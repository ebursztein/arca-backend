"""
Unit tests for entity merge conflict detection.

Tests the entity extraction and merging logic with real LLM calls
to ensure that entities with conflicting contexts (work vs. personal)
are not incorrectly merged.
"""

import pytest
import os
from datetime import datetime
from google import genai

from models import Entity, EntityStatus, AttributeKV
from entity_extraction import (
    extract_entities_from_message,
    merge_entities_with_existing,
    execute_merge_actions
)


@pytest.fixture
def gemini_client():
    """Get Gemini client from environment."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)


@pytest.fixture
def sample_existing_entities():
    """Sample entities that already exist in the database."""
    now = datetime.now()
    return [
        Entity(
            entity_id="ent_001",
            name="John",
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            aliases=["boyfriend", "partner"],
            attributes=[
                AttributeKV(key="relationship_to_user", value="partner"),
                AttributeKV(key="relationship_status", value="dating")
            ],
            related_entities=[],
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=5,
            context_snippets=[
                "Met at coffee shop last year",
                "Anniversary in June"
            ],
            importance_score=0.85,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        ),
        Entity(
            entity_id="ent_002",
            name="TechCorp",
            entity_type="company",
            status=EntityStatus.ACTIVE,
            aliases=[],
            attributes=[AttributeKV(key="user_role", value="software engineer")],
            related_entities=[],
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=3,
            context_snippets=["Working at TechCorp for 2 years"],
            importance_score=0.70,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )
    ]


@pytest.mark.asyncio
async def test_conflict_work_john_vs_boyfriend_john(gemini_client, sample_existing_entities):
    """
    Test that a coworker named John is NOT merged with boyfriend John.

    This is the critical test case - two people with the same name but
    completely different contexts should result in a CREATE action, not UPDATE/MERGE.
    """
    # User mentions "John" in a work context
    user_message = "Why am I feeling so much tension with John at work today?"
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Step 1: Extract entities
    extracted, perf_extract = await extract_entities_from_message(
        user_message=user_message,
        current_date=current_date,
        gemini_client=gemini_client,
        user_id="test_user_001",
        posthog_api_key=os.environ.get("POSTHOG_API_KEY")  # Optional for tests
    )

    print(f"\n✓ Extracted {len(extracted.entities)} entities ({perf_extract['time_ms']}ms)")
    for ent in extracted.entities:
        attrs_dict = {attr.key: attr.value for attr in ent.attributes}
        print(f"  • {ent.name} ({ent.entity_type}) - {attrs_dict}")

    # Verify extraction found John with work context
    john_entities = [e for e in extracted.entities if e.name.lower() == "john"]
    assert len(john_entities) > 0, "Should extract 'John' from message"

    # Step 2: Merge with existing
    merged_actions, perf_merge = await merge_entities_with_existing(
        extracted_entities=extracted,
        existing_entities=sample_existing_entities,
        current_date=current_date,
        gemini_client=gemini_client,
        user_id="test_user_001",
        posthog_api_key=os.environ.get("POSTHOG_API_KEY")  # Optional for tests
    )

    print(f"\n✓ Generated {len(merged_actions.actions)} merge actions ({perf_merge['time_ms']}ms)")
    for action in merged_actions.actions:
        print(f"  • {action.action.upper()}: {action.entity_name} ({action.entity_type})")
        if action.merge_with_id:
            print(f"    Merge with: {action.merge_with_id}")

    # Step 3: Verify John actions
    john_actions = [a for a in merged_actions.actions if a.entity_name.lower() == "john"]

    # CRITICAL ASSERTION: John should be CREATE, not UPDATE/MERGE
    # Work John is different from boyfriend John
    for action in john_actions:
        assert action.action == "create", \
            f"Expected CREATE for work John (different from boyfriend John), got {action.action.upper()}"
        assert action.merge_with_id is None or action.merge_with_id != "ent_001", \
            "Work John should NOT be merged with boyfriend John (ent_001)"

    # Step 4: Execute actions and verify final state
    now = datetime.now()
    updated_entities = execute_merge_actions(merged_actions, sample_existing_entities, now)

    # Count Johns in final entity list
    johns = [e for e in updated_entities if e.name.lower() == "john"]
    print(f"\n✓ Final entity count: {len(updated_entities)} total, {len(johns)} named 'John'")

    for john in johns:
        attrs_dict = {attr.key: attr.value for attr in john.attributes}
        print(f"  • {john.name} ({john.entity_type}): {attrs_dict}")

    # Should have TWO separate Johns now
    assert len(johns) == 2, \
        f"Expected 2 separate Johns (boyfriend + coworker), got {len(johns)}"

    # Verify boyfriend John still has personal attributes
    boyfriend_john = next((j for j in johns if j.entity_id == "ent_001"), None)
    assert boyfriend_john is not None, "Boyfriend John should still exist"

    bf_attrs = {attr.key: attr.value for attr in boyfriend_john.attributes}
    assert "relationship_to_user" in bf_attrs, "Boyfriend John should keep personal attributes"
    assert bf_attrs["relationship_to_user"] == "partner"

    # Verify work John has work attributes
    work_johns = [j for j in johns if j.entity_id != "ent_001"]
    assert len(work_johns) == 1, "Should have exactly one work John"

    work_john = work_johns[0]
    work_attrs = {attr.key: attr.value for attr in work_john.attributes}

    # Work John should NOT have personal relationship attributes
    assert "relationship_to_user" not in work_attrs or work_attrs["relationship_to_user"] != "partner", \
        "Work John should NOT have boyfriend/partner attributes"


@pytest.mark.asyncio
async def test_same_john_update(gemini_client, sample_existing_entities):
    """
    Test that mentioning boyfriend John in a personal context correctly UPDATES.

    This tests that the system CAN merge/update when appropriate.
    """
    # User mentions "John" in a personal/relationship context
    user_message = "John and I had a really nice date last night"
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Step 1: Extract entities
    extracted, _ = await extract_entities_from_message(
        user_message=user_message,
        current_date=current_date,
        gemini_client=gemini_client,
        user_id="test_user_001",
        posthog_api_key=os.environ.get("POSTHOG_API_KEY")
    )

    # Step 2: Merge with existing
    merged_actions, _ = await merge_entities_with_existing(
        extracted_entities=extracted,
        existing_entities=sample_existing_entities,
        current_date=current_date,
        gemini_client=gemini_client,
        user_id="test_user_001",
        posthog_api_key=os.environ.get("POSTHOG_API_KEY")
    )

    # Step 3: Verify John action
    john_actions = [a for a in merged_actions.actions if a.entity_name.lower() == "john"]

    # This time it SHOULD be UPDATE or MERGE (same John)
    if len(john_actions) > 0:
        action = john_actions[0]
        assert action.action in ["update", "merge"], \
            f"Expected UPDATE/MERGE for boyfriend John (same person), got {action.action.upper()}"

        # If merge, should merge with ent_001
        if action.action == "merge":
            assert action.merge_with_id == "ent_001", \
                "Should merge with existing boyfriend John (ent_001)"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])

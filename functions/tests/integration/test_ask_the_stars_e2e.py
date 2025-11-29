"""
End-to-end test for Ask the Stars feature.

Tests the complete flow:
1. Extract entities from user message
2. Merge with existing entities
3. Execute merge actions
4. Build conversation context
5. Generate response (mocked LLM)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from models import (
    Entity,
    EntityStatus,
    Message,
    MessageRole,
    Conversation,
    UserEntities,
    ExtractedEntities,
    ExtractedEntity,
    MergedEntities,
    EntityMergeAction,
    AttributeKV,
    DailyHoroscope,
    UserProfile,
    MemoryCollection,
    create_empty_memory
)
from entity_extraction import (
    execute_merge_actions,
    get_top_entities_by_importance
)


class TestAskTheStarsEndToEnd:
    """End-to-end integration tests for Ask the Stars."""

    def test_full_entity_extraction_flow(self):
        """Test complete entity extraction and merging flow."""
        now = datetime.now()

        # Initial state: No entities
        existing_entities = []

        # Simulate LLM extraction output
        extracted = ExtractedEntities(
            entities=[
                ExtractedEntity(
                    name="John",
                    entity_type="relationship",
                    context="Feeling tension with John today",
                    confidence=1.0,
                    attributes=[AttributeKV(key="relationship_to_user", value="partner")],
                    related_to=None
                ),
                ExtractedEntity(
                    name="TechCorp",
                    entity_type="company",
                    context="Work at TechCorp",
                    confidence=0.9,
                    attributes=[],
                    related_to=None
                )
            ]
        )

        # Simulate LLM merge output
        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="create",
                    entity_name="John",
                    entity_type="relationship",
                    context_update="Feeling tension with John today",
                    attribute_updates=[AttributeKV(key="relationship_to_user", value="partner")]
                ),
                EntityMergeAction(
                    action="create",
                    entity_name="TechCorp",
                    entity_type="company",
                    context_update="Work at TechCorp"
                )
            ]
        )

        # Execute merge
        updated_entities = execute_merge_actions(merged, existing_entities, now)

        # Verify results
        assert len(updated_entities) == 2
        john = [e for e in updated_entities if e.name == "John"][0]
        # attributes is now a list of AttributeKV
        attr_dict = {a.key: a.value for a in john.attributes}
        assert attr_dict["relationship_to_user"] == "partner"
        assert "Feeling tension with John today" in john.context_snippets

        print("Full entity extraction flow works")

    def test_entity_merge_on_second_mention(self):
        """Test that second mention merges with existing entity."""
        now = datetime.now()

        # Existing entity from first conversation
        existing_entities = [
            Entity(
                entity_id="ent_001",
                name="John",
                entity_type="relationship",
                status=EntityStatus.ACTIVE,
                aliases=[],
                attributes=[AttributeKV(key="relationship_to_user", value="partner")],
                related_entities=[],
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                context_snippets=["Feeling tension with John"],
                importance_score=0.8,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        # Second mention: User calls him "boyfriend"
        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="merge",
                    entity_name="boyfriend",
                    entity_type="relationship",
                    merge_with_id="ent_001",
                    new_alias="boyfriend",
                    context_update="Planning date with boyfriend"
                )
            ]
        )

        updated_entities = execute_merge_actions(merged, existing_entities, now)

        # Verify merge
        assert len(updated_entities) == 1
        john = updated_entities[0]
        assert "boyfriend" in john.aliases
        assert john.mention_count == 2
        assert "Planning date with boyfriend" in john.context_snippets

        print("Entity merge on second mention works")

    def test_entity_attribute_enrichment(self):
        """Test that entity attributes get enriched over time."""
        now = datetime.now()

        # Initial: mom with no attributes
        existing_entities = [
            Entity(
                entity_id="ent_mom",
                name="mom",
                entity_type="person",
                attributes=[],
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        # User mentions mom's birthday
        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="update",
                    entity_name="mom",
                    entity_type="person",
                    merge_with_id="ent_mom",
                    context_update="Getting birthday present for mom",
                    attribute_updates=[
                        AttributeKV(key="birthday_season", value="January"),
                        AttributeKV(key="relationship_to_user", value="mother")
                    ]
                )
            ]
        )

        updated_entities = execute_merge_actions(merged, existing_entities, now)

        # Verify enrichment
        mom = updated_entities[0]
        attr_dict = {a.key: a.value for a in mom.attributes}
        assert attr_dict["birthday_season"] == "January"
        assert attr_dict["relationship_to_user"] == "mother"

        print("Entity attribute enrichment works")

    def test_entity_relationship_linking(self):
        """Test linking entities together."""
        now = datetime.now()

        # Existing: company
        existing_entities = [
            Entity(
                entity_id="ent_company",
                name="TechCorp",
                entity_type="company",
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        # User mentions "Bob my boss at TechCorp"
        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="create",
                    entity_name="Bob",
                    entity_type="person",
                    context_update="Meeting with Bob my boss",
                    attribute_updates=[
                        AttributeKV(key="role", value="boss"),
                        AttributeKV(key="works_at", value="TechCorp")
                    ],
                    link_to_entity_id="ent_company"
                )
            ]
        )

        updated_entities = execute_merge_actions(merged, existing_entities, now)

        # Verify link
        bob = [e for e in updated_entities if e.name == "Bob"][0]
        assert "ent_company" in bob.related_entities
        attr_dict = {a.key: a.value for a in bob.attributes}
        assert attr_dict["works_at"] == "TechCorp"

        print("Entity relationship linking works")

    def test_top_entities_selection(self):
        """Test selecting top 15 entities by importance."""
        now = datetime.now()

        # Create 20 entities with varying importance
        entities = []
        for i in range(20):
            days_ago = i  # Older entities have lower scores
            entity_date = (now - timedelta(days=days_ago)).isoformat()

            entity = Entity(
                entity_id=f"ent_{i}",
                name=f"Entity {i}",
                entity_type="person",
                first_seen=entity_date,
                last_seen=entity_date,
                mention_count=20 - i,  # Recent entities mentioned more
                importance_score=0.0,  # Will be calculated
                created_at=entity_date,
                updated_at=entity_date
            )
            entities.append(entity)

        # Get top 15
        top_15 = get_top_entities_by_importance(entities, limit=15, current_time=now)

        # Verify selection
        assert len(top_15) == 15
        # First entity should be most recent (highest score)
        assert top_15[0].name == "Entity 0"

        print("Top entities selection works")

    def test_conversation_message_storage(self):
        """Test storing messages in conversation."""
        now = datetime.now().isoformat()

        user_msg = Message(
            message_id="msg_001",
            role=MessageRole.USER,
            content="Why am I feeling anxious about John today?",
            timestamp=now
        )

        assistant_msg = Message(
            message_id="msg_002",
            role=MessageRole.ASSISTANT,
            content="Mars is square your Venus today, which can create tension in relationships...",
            timestamp=now
        )

        conversation = Conversation(
            conversation_id="conv_001",
            user_id="user_123",
            horoscope_date="2025-01-20",
            messages=[user_msg, assistant_msg],
            created_at=now,
            updated_at=now
        )

        # Verify storage
        assert len(conversation.messages) == 2
        assert conversation.messages[0].role == MessageRole.USER
        assert conversation.messages[1].role == MessageRole.ASSISTANT
        assert "John" in conversation.messages[0].content
        assert "Mars" in conversation.messages[1].content

        print("Conversation message storage works")

    def test_context_snippet_fifo(self):
        """Test that context snippets maintain FIFO with max 10."""
        now = datetime.now()

        # Entity with 10 context snippets
        entity = Entity(
            entity_id="ent_001",
            name="John",
            entity_type="relationship",
            context_snippets=[f"Context {i}" for i in range(10)],
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=10,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        # Add 11th mention
        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="update",
                    entity_name="John",
                    entity_type="relationship",
                    merge_with_id="ent_001",
                    context_update="Context 10"
                )
            ]
        )

        updated = execute_merge_actions(merged, [entity], now)

        # Verify FIFO
        assert len(updated[0].context_snippets) == 10
        assert "Context 0" not in updated[0].context_snippets  # Oldest removed
        assert "Context 10" in updated[0].context_snippets  # Latest added

        print("Context snippet FIFO works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

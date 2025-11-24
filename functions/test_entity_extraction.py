"""
Unit tests for entity extraction and merging.

Tests:
- Entity extraction from messages
- Entity deduplication and merging
- Attribute extraction
- Relationship linking
- Importance score calculation
"""

import pytest
from datetime import datetime, timedelta
from models import (
    Entity,
    EntityStatus,
    ExtractedEntity,
    ExtractedEntities,
    EntityMergeAction,
    MergedEntities,
    calculate_entity_importance_score
)
from entity_extraction import (
    execute_merge_actions,
    get_top_entities_by_importance
)


class TestImportanceScoreCalculation:
    """Test importance score formula."""

    def test_recent_mention_high_score(self):
        """Entity mentioned today should have high score."""
        now = datetime.now()
        entity = Entity(
            entity_id="ent_001",
            name="John",
            entity_type="relationship",
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        score = calculate_entity_importance_score(entity, now)
        assert score > 0.6  # High recency weight

    def test_old_mention_low_score(self):
        """Entity mentioned 60 days ago should have low score."""
        now = datetime.now()
        old_date = now - timedelta(days=60)

        entity = Entity(
            entity_id="ent_001",
            name="Old Friend",
            entity_type="person",
            first_seen=old_date.isoformat(),
            last_seen=old_date.isoformat(),
            mention_count=1,
            created_at=old_date.isoformat(),
            updated_at=old_date.isoformat()
        )

        score = calculate_entity_importance_score(entity, now)
        assert score < 0.2  # Low recency, low frequency

    def test_high_frequency_boosts_score(self):
        """High mention count should boost score."""
        now = datetime.now()
        old_date = now - timedelta(days=20)

        entity = Entity(
            entity_id="ent_001",
            name="Boss",
            entity_type="person",
            first_seen=old_date.isoformat(),
            last_seen=old_date.isoformat(),
            mention_count=15,  # High frequency
            created_at=old_date.isoformat(),
            updated_at=old_date.isoformat()
        )

        score = calculate_entity_importance_score(entity, now)
        assert score > 0.5  # Frequency compensates for recency


class TestEntityMergeExecution:
    """Test execute_merge_actions function."""

    def test_create_new_entity(self):
        """Should create new entity."""
        actions = MergedEntities(actions=[
            EntityMergeAction(
                action="create",
                entity_name="Sarah",
                entity_type="person",
                context_update="Met Sarah at coffee shop",
                attribute_updates={"role": "friend"}
            )
        ])

        result = execute_merge_actions(actions, [], datetime.now())

        assert len(result) == 1
        assert result[0].name == "Sarah"
        assert result[0].entity_type == "person"
        assert result[0].attributes["role"] == "friend"
        assert "Met Sarah at coffee shop" in result[0].context_snippets

    def test_merge_with_existing(self):
        """Should merge new alias with existing entity."""
        now = datetime.now()
        existing = Entity(
            entity_id="ent_001",
            name="boyfriend",
            entity_type="relationship",
            aliases=[],
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        actions = MergedEntities(actions=[
            EntityMergeAction(
                action="merge",
                entity_name="John",
                entity_type="relationship",
                merge_with_id="ent_001",
                new_alias="John",
                context_update="Mentioned John by name"
            )
        ])

        result = execute_merge_actions(actions, [existing], now)

        assert len(result) == 1
        assert "John" in result[0].aliases
        assert result[0].mention_count == 2
        assert "Mentioned John by name" in result[0].context_snippets

    def test_update_entity_attributes(self):
        """Should update entity with new attributes."""
        now = datetime.now()
        existing = Entity(
            entity_id="ent_001",
            name="mom",
            entity_type="person",
            attributes={},
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        actions = MergedEntities(actions=[
            EntityMergeAction(
                action="update",
                entity_name="mom",
                entity_type="person",
                merge_with_id="ent_001",
                attribute_updates={"birthday_season": "January"}
            )
        ])

        result = execute_merge_actions(actions, [existing], now)

        assert result[0].attributes["birthday_season"] == "January"
        assert result[0].mention_count == 2

    def test_link_entities(self):
        """Should create relationship between entities."""
        now = datetime.now()
        company = Entity(
            entity_id="ent_company",
            name="TechCorp",
            entity_type="company",
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        actions = MergedEntities(actions=[
            EntityMergeAction(
                action="create",
                entity_name="Bob",
                entity_type="person",
                context_update="My boss Bob",
                attribute_updates={"role": "boss", "works_at": "TechCorp"},
                link_to_entity_id="ent_company"
            )
        ])

        result = execute_merge_actions(actions, [company], now)

        bob = [e for e in result if e.name == "Bob"][0]
        assert "ent_company" in bob.related_entities
        assert bob.attributes["works_at"] == "TechCorp"


class TestTopEntitiesSelection:
    """Test filtering top entities by importance."""

    def test_returns_top_n_entities(self):
        """Should return top N entities by importance."""
        now = datetime.now()
        entities = [
            Entity(
                entity_id=f"ent_{i}",
                name=f"Entity {i}",
                entity_type="person",
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=i + 1,  # Must be >= 1
                importance_score=float(i) / 20,  # Must be <= 1.0
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
            for i in range(20)
        ]

        top_5 = get_top_entities_by_importance(entities, limit=5, current_time=now)

        assert len(top_5) == 5
        # Should be sorted by importance (descending)
        for i in range(len(top_5) - 1):
            assert top_5[i].importance_score >= top_5[i+1].importance_score

    def test_filters_archived_entities(self):
        """Should only return active entities."""
        now = datetime.now()
        entities = [
            Entity(
                entity_id="ent_active",
                name="Active",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=5,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            ),
            Entity(
                entity_id="ent_archived",
                name="Archived",
                entity_type="person",
                status=EntityStatus.ARCHIVED,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=10,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        result = get_top_entities_by_importance(entities, limit=10, current_time=now)

        assert len(result) == 1
        assert result[0].entity_id == "ent_active"


class TestContextSnippetManagement:
    """Test FIFO context snippet management."""

    def test_limits_context_snippets_to_10(self):
        """Should keep only last 10 context snippets."""
        now = datetime.now()
        existing = Entity(
            entity_id="ent_001",
            name="John",
            entity_type="person",
            context_snippets=[f"Context {i}" for i in range(10)],
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=10,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        actions = MergedEntities(actions=[
            EntityMergeAction(
                action="update",
                entity_name="John",
                entity_type="person",
                merge_with_id="ent_001",
                context_update="New context 11"
            )
        ])

        result = execute_merge_actions(actions, [existing], now)

        assert len(result[0].context_snippets) == 10
        assert "Context 0" not in result[0].context_snippets  # Oldest removed
        assert "New context 11" in result[0].context_snippets  # Latest added


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

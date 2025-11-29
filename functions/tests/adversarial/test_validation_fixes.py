"""
Tests verifying that validation bugs have been FIXED.

These tests confirm that invalid data is now properly rejected.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestValidationFixesVerified:
    """Verify that all validation bugs have been fixed."""

    def test_connection_rejects_invalid_date(self):
        """FIXED: Connection now rejects semantically invalid dates."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        # "2000-13-45" should now be rejected
        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="Test",
                birth_date="2000-13-45",  # Invalid date - NOW REJECTED
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_connection_rejects_future_birth_date(self):
        """FIXED: Connection now rejects future birth dates."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="Test",
                birth_date="2099-01-01",  # Future date - NOW REJECTED
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_connection_rejects_lat_without_lon(self):
        """FIXED: Connection now requires both lat and lon together."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="Test",
                birth_date="1990-01-15",
                birth_lat=40.0,
                birth_lon=None,  # Only lat set - NOW REJECTED
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_entity_merge_action_rejects_invalid_action(self):
        """FIXED: EntityMergeAction now validates action type."""
        from models import EntityMergeAction

        with pytest.raises(ValidationError):
            EntityMergeAction(
                action="destroy",  # Invalid action - NOW REJECTED
                entity_name="Test",
                entity_type="person"
            )

    def test_actionable_advice_rejects_empty_strings(self):
        """FIXED: ActionableAdvice now requires non-empty strings."""
        from models import ActionableAdvice

        with pytest.raises(ValidationError):
            ActionableAdvice(
                do="",  # Empty - NOW REJECTED
                dont="",
                reflect_on=""
            )

    def test_meter_group_state_validates_quality(self):
        """FIXED: MeterGroupState now validates quality values."""
        from models import MeterGroupState

        with pytest.raises(ValidationError):
            MeterGroupState(
                label="Good",
                quality="super_awesome"  # Invalid - NOW REJECTED
            )

    def test_trend_metric_validates_direction(self):
        """FIXED: TrendMetric now validates direction values."""
        from models import TrendMetric

        with pytest.raises(ValidationError):
            TrendMetric(
                previous=50.0,
                delta=5.0,
                direction="backwards",  # Invalid - NOW REJECTED
                change_rate="moderate"
            )

    def test_trend_metric_validates_change_rate(self):
        """FIXED: TrendMetric now validates change_rate values."""
        from models import TrendMetric

        with pytest.raises(ValidationError):
            TrendMetric(
                previous=50.0,
                delta=5.0,
                direction="improving",
                change_rate="super_fast"  # Invalid - NOW REJECTED
            )

    def test_user_profile_validates_email(self):
        """FIXED: UserProfile now validates email format."""
        from models import UserProfile

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_001",
                name="Test",
                email="not-an-email",  # Invalid email - NOW REJECTED
                birth_date="1990-01-01",
                sun_sign="capricorn",
                natal_chart={},
                exact_chart=False,
                created_at=now,
                last_active=now
            )

    def test_user_profile_validates_sun_sign(self):
        """FIXED: UserProfile now validates sun sign."""
        from models import UserProfile

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_001",
                name="Test",
                email="test@test.com",
                birth_date="1990-01-01",
                sun_sign="not-a-sign",  # Invalid - NOW REJECTED
                natal_chart={},
                exact_chart=False,
                created_at=now,
                last_active=now
            )

    def test_user_profile_validates_birth_date_format(self):
        """FIXED: UserProfile now validates birth_date format."""
        from models import UserProfile

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_001",
                name="Test",
                email="test@test.com",
                birth_date="January 1, 1990",  # Invalid format - NOW REJECTED
                sun_sign="capricorn",
                natal_chart={},
                exact_chart=False,
                created_at=now,
                last_active=now
            )

    def test_message_rejects_whitespace_only(self):
        """FIXED: Message now rejects whitespace-only content."""
        from models import Message, MessageRole

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Message(
                message_id="msg_001",
                role=MessageRole.USER,
                content="   \n\t   ",  # Whitespace only - NOW REJECTED
                timestamp=now
            )

    def test_conversation_validates_horoscope_date_format(self):
        """FIXED: Conversation now validates horoscope_date format."""
        from models import Conversation

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Conversation(
                conversation_id="conv_001",
                user_id="user_001",
                horoscope_date="2025/01/20",  # Wrong format - NOW REJECTED
                messages=[],
                created_at=now,
                updated_at=now
            )

    def test_relationship_weather_requires_overview(self):
        """FIXED: RelationshipWeather now requires non-empty overview."""
        from models import RelationshipWeather

        with pytest.raises(ValidationError):
            RelationshipWeather(
                overview="",  # Empty - NOW REJECTED
                connection_vibes=[]
            )

    def test_connection_vibe_requires_content(self):
        """FIXED: ConnectionVibe now requires non-empty vibe and key_transit."""
        from models import ConnectionVibe, RelationshipType

        with pytest.raises(ValidationError):
            ConnectionVibe(
                connection_id="conn_001",
                name="Test",
                relationship_type=RelationshipType.FRIEND,
                vibe="",  # Empty - NOW REJECTED
                vibe_score=50,
                key_transit=""
            )

    def test_entity_id_validates_format(self):
        """FIXED: Entity now validates entity_id format."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Entity(
                entity_id="!!!invalid!!!",  # Invalid format - NOW REJECTED
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now,
                last_seen=now,
                mention_count=1,
                created_at=now,
                updated_at=now
            )

    def test_connection_id_validates_format(self):
        """FIXED: Connection now validates connection_id format."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Connection(
                connection_id="<script>alert('xss')</script>",  # XSS - NOW REJECTED
                name="Test",
                birth_date="1990-01-01",
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_share_link_validates_user_id(self):
        """FIXED: ShareLink now validates user_id format."""
        from connections import ShareLink

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            ShareLink(
                user_id="'; DROP TABLE users; --",  # SQL injection - NOW REJECTED
                created_at=now
            )

    def test_synastry_aspect_requires_non_empty_id(self):
        """FIXED: SynastryAspect now requires non-empty id."""
        from compatibility import SynastryAspect

        with pytest.raises(ValidationError):
            SynastryAspect(
                id="",  # Empty - NOW REJECTED
                user_planet="sun",
                their_planet="moon",
                aspect_type="conjunction",
                orb=0.5,
                is_harmonious=True
            )

    def test_entity_name_has_max_length(self):
        """FIXED: Entity name now has max length."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="A" * 10000,  # Too long - NOW REJECTED
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now,
                last_seen=now,
                mention_count=1,
                created_at=now,
                updated_at=now
            )

    def test_connection_name_has_max_length(self):
        """FIXED: Connection name now has max length."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="B" * 100000,  # Too long - NOW REJECTED
                birth_date="1990-01-01",
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_extracted_entity_context_accepts_long_strings(self):
        """ExtractedEntity context has no max_length - Gemini structured output can't handle nested array limits."""
        from models import ExtractedEntity

        # No max_length constraint - Gemini's structured output schema generation
        # fails with complex nested schemas that have array length limits
        entity = ExtractedEntity(
            name="Test",
            entity_type="person",
            context="C" * 10000,  # Long context is accepted
            confidence=0.9
        )
        assert len(entity.context) == 10000

    def test_entity_aliases_has_max_items(self):
        """FIXED: Entity aliases now has max items limit."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                aliases=[f"alias_{i}" for i in range(10000)],  # Too many - NOW REJECTED
                first_seen=now,
                last_seen=now,
                mention_count=1,
                created_at=now,
                updated_at=now
            )

    def test_entity_related_entities_has_max_items(self):
        """FIXED: Entity related_entities now has max items limit."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                related_entities=[f"ent_{i:06d}" for i in range(10000)],  # Too many - NOW REJECTED
                first_seen=now,
                last_seen=now,
                mention_count=1,
                created_at=now,
                updated_at=now
            )

    def test_entity_self_reference_rejected(self):
        """FIXED: Entity cannot reference itself in related_entities."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                related_entities=["ent_001"],  # Self-reference - NOW REJECTED
                first_seen=now,
                last_seen=now,
                mention_count=1,
                created_at=now,
                updated_at=now
            )

    def test_execute_merge_actions_no_longer_mutates_input(self):
        """FIXED: execute_merge_actions no longer mutates input entities."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus, ActionType
        import copy

        now = datetime.now()
        original_entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=5,
            context_snippets=["Original context"],
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        original_copy = copy.deepcopy(original_entity)

        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action=ActionType.MERGE,
                    entity_name="Test",
                    entity_type="person",
                    merge_with_id="ent_001",
                    context_update="New context"
                )
            ]
        )

        result = execute_merge_actions(merged, [original_entity], now)

        # FIXED: Input entity should NOT be mutated
        assert original_entity.mention_count == original_copy.mention_count, \
            "Input entity should not be mutated anymore"
        assert original_entity.context_snippets == original_copy.context_snippets, \
            "Input entity context should not be mutated"


class TestValidInputsStillWork:
    """Ensure valid inputs still work after fixes."""

    def test_valid_user_profile(self):
        """Valid UserProfile still works."""
        from models import UserProfile

        now = datetime.now().isoformat()

        profile = UserProfile(
            user_id="user_001",
            name="Test User",
            email="test@example.com",
            birth_date="1990-06-15",
            sun_sign="gemini",
            natal_chart={},
            exact_chart=False,
            created_at=now,
            last_active=now
        )
        assert profile.email == "test@example.com"
        assert profile.sun_sign == "gemini"

    def test_valid_connection(self):
        """Valid Connection still works."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        conn = Connection(
            connection_id="conn_001",
            name="John",
            birth_date="1990-06-15",
            relationship_type=RelationshipType.FRIEND,
            created_at=now,
            updated_at=now
        )
        assert conn.name == "John"

    def test_valid_entity(self):
        """Valid Entity still works."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        entity = Entity(
            entity_id="ent_001",
            name="Test Entity",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now,
            last_seen=now,
            mention_count=1,
            created_at=now,
            updated_at=now
        )
        assert entity.name == "Test Entity"

    def test_valid_entity_merge_action(self):
        """Valid EntityMergeAction still works."""
        from models import EntityMergeAction, ActionType

        action = EntityMergeAction(
            action=ActionType.CREATE,
            entity_name="Test",
            entity_type="person"
        )
        assert action.action == ActionType.CREATE

    def test_valid_trend_metric(self):
        """Valid TrendMetric still works."""
        from models import TrendMetric, DirectionType, ChangeRateType

        trend = TrendMetric(
            previous=50.0,
            delta=5.0,
            direction=DirectionType.IMPROVING,
            change_rate=ChangeRateType.MODERATE
        )
        assert trend.direction == DirectionType.IMPROVING


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

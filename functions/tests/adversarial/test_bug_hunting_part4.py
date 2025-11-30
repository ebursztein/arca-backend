"""
Bug-hunting adversarial tests for Arca Backend - Part 4.

Final push to find bugs 13-20.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError


# =============================================================================
# BUG HUNT 13-15: UserProfile Validation
# =============================================================================

class TestUserProfileValidationBugs:
    """Test UserProfile validation."""

    def test_user_profile_with_invalid_email(self):
        """Test UserProfile rejects invalid email format."""
        from models import UserProfile

        now = datetime.now().isoformat()

        # Validation should reject invalid emails
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_001",
                name="Test",
                email="not-an-email",  # Invalid email format - should be rejected
                birth_date="1990-01-01",
                sun_sign="capricorn",
                natal_chart={},
                exact_chart=False,
                created_at=now,
                last_active=now
            )

    def test_user_profile_with_invalid_sun_sign(self):
        """Test UserProfile rejects invalid sun_sign."""
        from models import UserProfile

        now = datetime.now().isoformat()

        # Validation should reject invalid sun signs
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_001",
                name="Test",
                email="test@test.com",
                birth_date="1990-01-01",
                sun_sign="not-a-sign",  # Invalid - should be rejected
                natal_chart={},
                exact_chart=False,
                created_at=now,
                last_active=now
            )

    def test_user_profile_with_invalid_birth_date_format(self):
        """Test UserProfile rejects invalid birth_date format."""
        from models import UserProfile

        now = datetime.now().isoformat()

        # Validation should reject invalid date format
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_001",
                name="Test",
                email="test@test.com",
                birth_date="January 1, 1990",  # Invalid format - should be rejected
                sun_sign="capricorn",
                natal_chart={},
                exact_chart=False,
                created_at=now,
                last_active=now
            )


# =============================================================================
# BUG HUNT 16-18: Message and Conversation Bugs
# =============================================================================

class TestMessageConversationBugs:
    """Test Message and Conversation model validation."""

    def test_message_with_whitespace_only_content(self):
        """Test Message rejects whitespace-only content."""
        from models import Message, MessageRole

        now = datetime.now().isoformat()

        # Validation should reject whitespace-only content
        with pytest.raises(ValidationError):
            Message(
                message_id="msg_001",
                role=MessageRole.USER,
                content="   \n\t   ",  # Only whitespace - should be rejected
                timestamp=now
            )

    def test_conversation_horoscope_date_format(self):
        """Test Conversation rejects invalid horoscope_date format."""
        from models import Conversation

        now = datetime.now().isoformat()

        # Validation should reject invalid date format
        with pytest.raises(ValidationError):
            Conversation(
                conversation_id="conv_001",
                user_id="user_001",
                horoscope_date="2025/01/20",  # Slash format - should be rejected
                messages=[],
                created_at=now,
                updated_at=now
            )

    def test_message_id_format_accepts_simple_ids(self):
        """Test Message accepts simple string IDs (not strictly UUIDs)."""
        from models import Message, MessageRole

        now = datetime.now().isoformat()

        # message_id accepts any string (not strictly UUIDs)
        message = Message(
            message_id="1",
            role=MessageRole.USER,
            content="Test",
            timestamp=now
        )
        assert message.message_id == "1"


# =============================================================================
# BUG HUNT 19-20: RelationshipWeather and ConnectionVibe
# =============================================================================

class TestRelationshipWeatherBugs:
    """Test RelationshipWeather and ConnectionVibe validation."""

    def test_relationship_weather_overview_empty(self):
        """Test RelationshipWeather rejects empty overview."""
        from models import RelationshipWeather

        # Validation should reject empty overview
        with pytest.raises(ValidationError):
            RelationshipWeather(
                overview="",  # Empty - should be rejected
                connection_vibes=[]
            )

    def test_connection_vibe_with_empty_vibe(self):
        """Test ConnectionVibe rejects empty vibe string."""
        from models import ConnectionVibe, RelationshipType

        # Validation should reject empty vibe
        with pytest.raises(ValidationError):
            ConnectionVibe(
                connection_id="conn_001",
                name="Test",
                relationship_type=RelationshipType.FRIEND,
                vibe="",  # Empty - should be rejected
                vibe_score=50,
                key_transit=""
            )


# =============================================================================
# Entity ID Format
# =============================================================================

class TestEntityIdFormatBugs:
    """Test entity ID format handling."""

    def test_entity_id_format_validated(self):
        """Test Entity rejects invalid ID format."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # Validation should reject invalid ID format
        with pytest.raises(ValidationError):
            Entity(
                entity_id="!!!invalid!!!",  # Invalid format - should be rejected
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now,
                last_seen=now,
                mention_count=1,
                created_at=now,
                updated_at=now
            )

    def test_connection_id_format_validated(self):
        """Test Connection rejects script tags in ID."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        # Validation should reject XSS attempts
        with pytest.raises(ValidationError):
            Connection(
                connection_id="<script>alert('xss')</script>",  # XSS attempt - should be rejected
                name="Test",
                birth_date="1990-01-01",
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_share_link_user_id_format(self):
        """Test ShareLink rejects SQL injection attempts."""
        from connections import ShareLink

        now = datetime.now().isoformat()

        # Validation should reject SQL injection attempts
        with pytest.raises(ValidationError):
            ShareLink(
                user_id="'; DROP TABLE users; --",  # SQL injection - should be rejected
                created_at=now
            )


# =============================================================================
# Aspect and Synastry ID
# =============================================================================

class TestAspectIdBugs:
    """Test aspect ID handling."""

    def test_synastry_aspect_id_format(self):
        """Test SynastryAspect rejects empty ID."""
        from compatibility import SynastryAspect

        # Validation should reject empty ID
        with pytest.raises(ValidationError):
            SynastryAspect(
                id="",  # Empty ID - should be rejected
                user_planet="sun",
                their_planet="moon",
                aspect_type="conjunction",
                orb=0.5,
                is_harmonious=True
            )


# =============================================================================
# BUG HUNT: Field Length and Size Limits
# =============================================================================

class TestFieldLengthBugs:
    """Test field length validation."""

    def test_entity_name_very_long(self):
        """Test Entity rejects extremely long name."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # Validation should reject names over 500 characters
        very_long_name = "A" * 10000

        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name=very_long_name,
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now,
                last_seen=now,
                mention_count=1,
                created_at=now,
                updated_at=now
            )

    def test_connection_name_very_long(self):
        """Test Connection rejects extremely long name."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        # Validation should reject names over max length
        very_long_name = "B" * 100000

        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name=very_long_name,
                birth_date="1990-01-01",
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_extracted_entity_context_very_long(self):
        """Test ExtractedEntity accepts any length context (no validation)."""
        from models import ExtractedEntity

        # ExtractedEntity has no max_length on context (extracted from LLM)
        very_long_context = "C" * 10000

        entity = ExtractedEntity(
            name="Test",
            entity_type="person",
            context=very_long_context,
            confidence=0.9
        )
        assert len(entity.context) == 10000

    def test_entity_aliases_array_very_large(self):
        """Test Entity rejects very large aliases array."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # Validation should reject arrays over max_length
        many_aliases = [f"alias_{i}" for i in range(10000)]

        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                aliases=many_aliases,
                first_seen=now,
                last_seen=now,
                mention_count=1,
                created_at=now,
                updated_at=now
            )

    def test_related_entities_array_very_large(self):
        """Test Entity rejects very large related_entities array."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # Validation should reject arrays over max_length
        many_related = [f"ent_{i:06d}" for i in range(10000)]

        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                related_entities=many_related,
                first_seen=now,
                last_seen=now,
                mention_count=1,
                created_at=now,
                updated_at=now
            )


# =============================================================================
# BUG HUNT: Validation on Combined Fields
# =============================================================================

class TestCombinedFieldValidationBugs:
    """Test validation of related fields."""

    def test_entity_first_seen_after_last_seen(self):
        """Test Entity where first_seen is after last_seen."""
        from models import Entity, EntityStatus

        # BUG HUNT: No validation that first_seen <= last_seen
        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen="2025-12-31T23:59:59",  # After last_seen!
            last_seen="2025-01-01T00:00:00",  # Before first_seen!
            mention_count=1,
            created_at="2025-01-01",
            updated_at="2025-01-01"
        )
        # Bug: Should validate first_seen <= last_seen

    def test_entity_created_after_updated(self):
        """Test Entity where created_at is after updated_at."""
        from models import Entity, EntityStatus

        # BUG HUNT: No validation that created_at <= updated_at
        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen="2025-01-01",
            last_seen="2025-01-01",
            mention_count=1,
            created_at="2025-12-31",  # After updated!
            updated_at="2025-01-01"  # Before created!
        )
        # Bug: Should validate created_at <= updated_at


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

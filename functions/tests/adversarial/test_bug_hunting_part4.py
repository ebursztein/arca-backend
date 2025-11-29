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
    """Find bugs in UserProfile validation."""

    def test_user_profile_with_invalid_email(self):
        """Test UserProfile with invalid email format."""
        from models import UserProfile

        now = datetime.now().isoformat()

        # BUG HUNT: email is just str, no email validation
        profile = UserProfile(
            user_id="user_001",
            name="Test",
            email="not-an-email",  # Invalid email format!
            birth_date="1990-01-01",
            sun_sign="capricorn",
            natal_chart={},
            exact_chart=False,
            created_at=now,
            last_active=now
        )
        assert profile.email == "not-an-email"  # Bug: Should validate email

    def test_user_profile_with_invalid_sun_sign(self):
        """Test UserProfile with invalid sun_sign."""
        from models import UserProfile

        now = datetime.now().isoformat()

        # BUG HUNT: sun_sign is just str, no validation
        profile = UserProfile(
            user_id="user_001",
            name="Test",
            email="test@test.com",
            birth_date="1990-01-01",
            sun_sign="not-a-sign",  # Invalid!
            natal_chart={},
            exact_chart=False,
            created_at=now,
            last_active=now
        )
        assert profile.sun_sign == "not-a-sign"  # Bug: Should validate

    def test_user_profile_with_invalid_birth_date_format(self):
        """Test UserProfile with invalid birth_date format."""
        from models import UserProfile

        now = datetime.now().isoformat()

        # BUG HUNT: birth_date is just str, no format validation
        profile = UserProfile(
            user_id="user_001",
            name="Test",
            email="test@test.com",
            birth_date="January 1, 1990",  # Invalid format!
            sun_sign="capricorn",
            natal_chart={},
            exact_chart=False,
            created_at=now,
            last_active=now
        )
        assert profile.birth_date == "January 1, 1990"  # Bug: Should validate


# =============================================================================
# BUG HUNT 16-18: Message and Conversation Bugs
# =============================================================================

class TestMessageConversationBugs:
    """Find bugs in Message and Conversation models."""

    def test_message_with_whitespace_only_content(self):
        """Test Message with whitespace-only content."""
        from models import Message, MessageRole

        now = datetime.now().isoformat()

        # BUG HUNT: whitespace-only content
        message = Message(
            message_id="msg_001",
            role=MessageRole.USER,
            content="   \n\t   ",  # Only whitespace!
            timestamp=now
        )
        assert message.content.strip() == ""  # Bug: Should reject whitespace-only

    def test_conversation_horoscope_date_format(self):
        """Test Conversation with various horoscope_date formats."""
        from models import Conversation

        now = datetime.now().isoformat()

        # BUG HUNT: horoscope_date format not validated
        conv = Conversation(
            conversation_id="conv_001",
            user_id="user_001",
            horoscope_date="2025/01/20",  # Slash format instead of dash!
            messages=[],
            created_at=now,
            updated_at=now
        )
        assert conv.horoscope_date == "2025/01/20"  # Bug: Should validate format

    def test_message_id_format_not_validated(self):
        """Test Message with non-UUID message_id."""
        from models import Message, MessageRole

        now = datetime.now().isoformat()

        # BUG HUNT: message_id should be UUID but accepts any string
        message = Message(
            message_id="1",  # Not a UUID!
            role=MessageRole.USER,
            content="Test",
            timestamp=now
        )
        assert message.message_id == "1"  # Bug: Should validate UUID format


# =============================================================================
# BUG HUNT 19-20: RelationshipWeather and ConnectionVibe
# =============================================================================

class TestRelationshipWeatherBugs:
    """Find bugs in RelationshipWeather and ConnectionVibe."""

    def test_relationship_weather_overview_empty(self):
        """Test RelationshipWeather with empty overview."""
        from models import RelationshipWeather

        # BUG HUNT: overview has no min_length validation
        weather = RelationshipWeather(
            overview="",  # Empty!
            connection_vibes=[]
        )
        assert weather.overview == ""  # Bug: Should require content

    def test_connection_vibe_with_empty_vibe(self):
        """Test ConnectionVibe with empty vibe string."""
        from models import ConnectionVibe, RelationshipType

        # BUG HUNT: vibe has no min_length validation
        vibe = ConnectionVibe(
            connection_id="conn_001",
            name="Test",
            relationship_type=RelationshipType.FRIEND,
            vibe="",  # Empty!
            vibe_score=50,
            key_transit=""  # Also empty!
        )
        assert vibe.vibe == ""  # Bug: Should require content


# =============================================================================
# BUG HUNT: Entity ID Format
# =============================================================================

class TestEntityIdFormatBugs:
    """Test entity ID format handling."""

    def test_entity_id_format_not_validated(self):
        """Test Entity with non-standard ID format."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # BUG HUNT: entity_id should follow format but accepts any string
        entity = Entity(
            entity_id="!!!invalid!!!",  # Not valid ID format
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now,
            last_seen=now,
            mention_count=1,
            created_at=now,
            updated_at=now
        )
        assert entity.entity_id == "!!!invalid!!!"  # Bug: Should validate

    def test_connection_id_format_not_validated(self):
        """Test Connection with non-standard ID format."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        # BUG HUNT: connection_id should follow format
        conn = Connection(
            connection_id="<script>alert('xss')</script>",  # XSS attempt as ID!
            name="Test",
            birth_date="1990-01-01",
            relationship_type=RelationshipType.FRIEND,
            created_at=now,
            updated_at=now
        )
        # Bug: Should validate ID format to prevent injection

    def test_share_link_user_id_format(self):
        """Test ShareLink with arbitrary user_id."""
        from connections import ShareLink

        now = datetime.now().isoformat()

        # BUG HUNT: user_id not validated
        link = ShareLink(
            user_id="'; DROP TABLE users; --",  # SQL injection attempt!
            created_at=now
        )
        # Bug: Should validate user_id format


# =============================================================================
# BUG HUNT: Aspect and Synastry ID Uniqueness
# =============================================================================

class TestAspectIdBugs:
    """Test aspect ID handling."""

    def test_synastry_aspect_id_format(self):
        """Test SynastryAspect with various ID formats."""
        from compatibility import SynastryAspect

        # BUG HUNT: id has no validation
        aspect = SynastryAspect(
            id="",  # Empty ID!
            user_planet="sun",
            their_planet="moon",
            aspect_type="conjunction",
            orb=0.5,
            is_harmonious=True
        )
        assert aspect.id == ""  # Bug: Should require non-empty ID


# =============================================================================
# BUG HUNT: Field Length and Size Limits
# =============================================================================

class TestFieldLengthBugs:
    """Test field length validation."""

    def test_entity_name_very_long(self):
        """Test Entity with extremely long name."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # BUG HUNT: name has no max_length
        very_long_name = "A" * 10000  # 10KB name!

        entity = Entity(
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
        assert len(entity.name) == 10000  # Bug: Should have max length

    def test_connection_name_very_long(self):
        """Test Connection with extremely long name."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        # BUG HUNT: name has min_length=1 but no max_length
        very_long_name = "B" * 100000  # 100KB name!

        conn = Connection(
            connection_id="conn_001",
            name=very_long_name,
            birth_date="1990-01-01",
            relationship_type=RelationshipType.FRIEND,
            created_at=now,
            updated_at=now
        )
        assert len(conn.name) == 100000  # Bug: Should have max length

    def test_extracted_entity_context_very_long(self):
        """Test ExtractedEntity with extremely long context."""
        from models import ExtractedEntity

        # BUG HUNT: context has no max_length
        very_long_context = "C" * 1000000  # 1MB context!

        entity = ExtractedEntity(
            name="Test",
            entity_type="person",
            context=very_long_context,
            confidence=0.9
        )
        assert len(entity.context) == 1000000  # Bug: Should have max length

    def test_entity_aliases_array_very_large(self):
        """Test Entity with very large aliases array."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # BUG HUNT: aliases has no max items
        many_aliases = [f"alias_{i}" for i in range(10000)]  # 10K aliases!

        entity = Entity(
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
        assert len(entity.aliases) == 10000  # Bug: Should limit array size

    def test_related_entities_array_very_large(self):
        """Test Entity with very large related_entities array."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # BUG HUNT: related_entities has no max items
        many_related = [f"ent_{i:06d}" for i in range(10000)]  # 10K relations!

        entity = Entity(
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
        assert len(entity.related_entities) == 10000  # Bug: Should limit


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

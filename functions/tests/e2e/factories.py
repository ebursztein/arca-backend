"""
Test data factories for E2E tests.

Provides factory classes for creating test objects:
- UserProfileFactory: Create user profiles with computed charts
- ConnectionFactory: Create connections with sun signs
- BirthDataFactory: Generate birth data for all 12 signs
- EntityFactory: Create test entities
- MessageFactory: Create conversation messages
"""
import uuid
from datetime import datetime, timezone
from typing import Optional


class BirthDataFactory:
    """Factory for generating birth data combinations."""

    # Birth dates for all 12 signs (middle of each sign's range)
    ALL_SIGNS = {
        "aries": "1990-04-10",
        "taurus": "1990-05-05",
        "gemini": "1990-06-15",
        "cancer": "1990-07-10",
        "leo": "1990-08-15",
        "virgo": "1990-09-10",
        "libra": "1990-10-10",
        "scorpio": "1990-11-10",
        "sagittarius": "1990-12-10",
        "capricorn": "1990-01-10",
        "aquarius": "1990-02-10",
        "pisces": "1990-03-10",
    }

    # Common cities with timezone/coordinates
    LOCATIONS = {
        "new_york": {
            "birth_timezone": "America/New_York",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
        },
        "los_angeles": {
            "birth_timezone": "America/Los_Angeles",
            "birth_lat": 34.0522,
            "birth_lon": -118.2437,
        },
        "london": {
            "birth_timezone": "Europe/London",
            "birth_lat": 51.5074,
            "birth_lon": -0.1278,
        },
        "paris": {
            "birth_timezone": "Europe/Paris",
            "birth_lat": 48.8566,
            "birth_lon": 2.3522,
        },
        "tokyo": {
            "birth_timezone": "Asia/Tokyo",
            "birth_lat": 35.6762,
            "birth_lon": 139.6503,
        },
    }

    @classmethod
    def for_sign(cls, sign: str) -> dict:
        """Get minimal birth data for a specific sun sign."""
        birth_date = cls.ALL_SIGNS.get(sign.lower())
        if not birth_date:
            raise ValueError(f"Unknown sign: {sign}")
        return {"birth_date": birth_date}

    @classmethod
    def for_sign_full(
        cls,
        sign: str,
        location: str = "new_york",
        birth_time: str = "12:00",
    ) -> dict:
        """Get full birth data for a specific sun sign."""
        birth_date = cls.ALL_SIGNS.get(sign.lower())
        if not birth_date:
            raise ValueError(f"Unknown sign: {sign}")

        loc_data = cls.LOCATIONS.get(location, cls.LOCATIONS["new_york"])

        return {
            "birth_date": birth_date,
            "birth_time": birth_time,
            **loc_data,
        }

    @staticmethod
    def create_minimal(birth_date: str = "1990-06-15") -> dict:
        """Create minimal birth data (V1 mode)."""
        return {"birth_date": birth_date}

    @staticmethod
    def create_full(
        birth_date: str = "1990-06-15",
        birth_time: str = "14:30",
        timezone: str = "America/New_York",
        lat: float = 40.7128,
        lon: float = -74.0060,
    ) -> dict:
        """Create complete birth data (V2 mode)."""
        return {
            "birth_date": birth_date,
            "birth_time": birth_time,
            "birth_timezone": timezone,
            "birth_lat": lat,
            "birth_lon": lon,
        }


class UserProfileFactory:
    """Factory for creating test UserProfile data."""

    @staticmethod
    def create(
        user_id: str = None,
        name: str = "Test User",
        email: str = None,
        birth_date: str = "1990-06-15",
        birth_time: Optional[str] = None,
        birth_timezone: Optional[str] = None,
        birth_lat: Optional[float] = None,
        birth_lon: Optional[float] = None,
        compute_chart: bool = True,
        **overrides,
    ) -> dict:
        """
        Create user profile data dict for testing.

        Args:
            user_id: Firebase user ID (auto-generated if not provided)
            name: User's name
            email: User's email (auto-generated if not provided)
            birth_date: Birth date YYYY-MM-DD
            birth_time: Birth time HH:MM (optional for V2)
            birth_timezone: IANA timezone (optional for V2)
            birth_lat: Birth latitude (optional for V2)
            birth_lon: Birth longitude (optional for V2)
            compute_chart: Whether to compute the natal chart
            **overrides: Additional fields to override

        Returns:
            dict: User profile data ready for testing
        """
        from astro import compute_birth_chart, get_sun_sign

        user_id = user_id or f"test_user_{uuid.uuid4().hex[:12]}"
        email = email or f"{user_id}@test.com"
        now = datetime.now(timezone.utc).isoformat()

        # Compute chart if requested
        chart_dict = None
        exact = False
        if compute_chart:
            chart_dict, exact = compute_birth_chart(
                birth_date=birth_date,
                birth_time=birth_time,
                birth_timezone=birth_timezone,
                birth_lat=birth_lat,
                birth_lon=birth_lon,
            )

        sun_sign = get_sun_sign(birth_date).value

        data = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "is_premium": False,
            "premium_expiry": None,
            "is_trial_active": False,
            "trial_end_date": None,
            "birth_date": birth_date,
            "birth_time": birth_time,
            "birth_timezone": birth_timezone,
            "birth_lat": birth_lat,
            "birth_lon": birth_lon,
            "sun_sign": sun_sign,
            "natal_chart": chart_dict,
            "exact_chart": exact,
            "photo_path": None,
            "created_at": now,
            "last_active": now,
        }
        data.update(overrides)
        return data

    @classmethod
    def create_v1(cls, user_id: str = None, birth_date: str = "1990-06-15") -> dict:
        """Create a V1 user profile (birth_date only)."""
        return cls.create(user_id=user_id, birth_date=birth_date)

    @classmethod
    def create_v2(
        cls,
        user_id: str = None,
        birth_date: str = "1990-06-15",
        location: str = "new_york",
    ) -> dict:
        """Create a V2 user profile with full birth data."""
        loc_data = BirthDataFactory.LOCATIONS.get(location, BirthDataFactory.LOCATIONS["new_york"])
        birth_data = BirthDataFactory.create_full(
            birth_date=birth_date,
            timezone=loc_data["birth_timezone"],
            lat=loc_data["birth_lat"],
            lon=loc_data["birth_lon"],
        )
        return cls.create(user_id=user_id, **birth_data)


class ConnectionFactory:
    """Factory for creating test Connection data."""

    @staticmethod
    def create(
        connection_id: str = None,
        name: str = "Test Connection",
        birth_date: str = "1992-03-22",
        relationship_category: str = "love",
        relationship_label: str = "crush",
        birth_time: Optional[str] = "12:00",
        birth_lat: Optional[float] = 0.0,
        birth_lon: Optional[float] = 0.0,
        birth_timezone: Optional[str] = "UTC",
        compute_chart: bool = False,
        **overrides,
    ) -> dict:
        """
        Create connection data dict for testing.

        Args:
            connection_id: Unique connection ID (auto-generated if not provided)
            name: Connection's name
            birth_date: Birth date YYYY-MM-DD
            relationship_category: love/friend/family/coworker/other
            relationship_label: crush/partner/best_friend/boss/etc
            birth_time: Birth time HH:MM (default: "12:00" - iOS default)
            birth_lat: Latitude (default: 0.0 - iOS default)
            birth_lon: Longitude (default: 0.0 - iOS default)
            birth_timezone: IANA timezone (default: "UTC")
            compute_chart: Whether to compute natal chart
            **overrides: Additional fields to override

        Returns:
            dict: Connection data ready for testing
        """
        from astro import get_sun_sign

        connection_id = connection_id or f"conn_{uuid.uuid4().hex[:12]}"
        sun_sign = get_sun_sign(birth_date).value
        now = datetime.now(timezone.utc).isoformat()

        chart_dict = None
        exact = False
        if compute_chart:
            from astro import compute_birth_chart

            chart_dict, exact = compute_birth_chart(
                birth_date=birth_date,
                birth_time=birth_time,
                birth_timezone=birth_timezone,
                birth_lat=birth_lat,
                birth_lon=birth_lon,
            )

        data = {
            "connection_id": connection_id,
            "name": name,
            "birth_date": birth_date,
            "birth_time": birth_time,
            "birth_lat": birth_lat,
            "birth_lon": birth_lon,
            "birth_timezone": birth_timezone,
            "relationship_category": relationship_category,
            "relationship_label": relationship_label,
            "sun_sign": sun_sign,
            "natal_chart": chart_dict,
            "exact_chart": exact,
            "source_user_id": None,
            "photo_path": None,
            "created_at": now,
            "updated_at": now,
            "synastry_points": None,
            "arca_notes": [],
            "vibes": [],
        }
        data.update(overrides)
        return data

    @classmethod
    def create_romantic(cls, name: str = "Partner", **kwargs) -> dict:
        """Create a romantic connection."""
        return cls.create(name=name, relationship_category="love", relationship_label="partner", **kwargs)

    @classmethod
    def create_friend(cls, name: str = "Friend", **kwargs) -> dict:
        """Create a friend connection."""
        return cls.create(name=name, relationship_category="friend", relationship_label="friend", **kwargs)

    @classmethod
    def create_family(cls, name: str = "Family Member", **kwargs) -> dict:
        """Create a family connection."""
        return cls.create(name=name, relationship_category="family", relationship_label="extended", **kwargs)

    @classmethod
    def create_coworker(cls, name: str = "Coworker", **kwargs) -> dict:
        """Create a coworker connection."""
        return cls.create(name=name, relationship_category="coworker", relationship_label="colleague", **kwargs)


class EntityFactory:
    """Factory for creating test entities."""

    @staticmethod
    def create(
        entity_id: str = None,
        name: str = "Test Entity",
        entity_type: str = "relationship",
        status: str = "active",
        **overrides,
    ) -> dict:
        """
        Create entity data dict for testing.

        Args:
            entity_id: Unique entity ID (auto-generated if not provided)
            name: Entity name
            entity_type: Type (relationship, career_goal, challenge, etc.)
            status: active/archived/resolved
            **overrides: Additional fields to override

        Returns:
            dict: Entity data ready for testing
        """
        entity_id = entity_id or f"ent_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        data = {
            "entity_id": entity_id,
            "name": name,
            "entity_type": entity_type,
            "status": status,
            "aliases": [],
            "category": None,
            "relationship_label": None,
            "notes": None,
            "attributes": [],
            "related_entities": [],
            "first_seen": now,
            "last_seen": now,
            "mention_count": 1,
            "context_snippets": [],
            "importance_score": 0.5,
            "connection_id": None,
            "created_at": now,
            "updated_at": now,
        }
        data.update(overrides)
        return data

    @classmethod
    def create_person(cls, name: str, category: str = "friend", **kwargs) -> dict:
        """Create a person entity."""
        return cls.create(
            name=name,
            entity_type="relationship",
            category=category,
            **kwargs,
        )

    @classmethod
    def create_career_goal(cls, name: str = "Career Goal", **kwargs) -> dict:
        """Create a career goal entity."""
        return cls.create(name=name, entity_type="career_goal", **kwargs)

    @classmethod
    def create_challenge(cls, name: str = "Challenge", **kwargs) -> dict:
        """Create a challenge entity."""
        return cls.create(name=name, entity_type="challenge", **kwargs)


class MessageFactory:
    """Factory for creating test messages and conversations."""

    @staticmethod
    def create_user_message(content: str, message_id: str = None) -> dict:
        """Create a user message."""
        return {
            "message_id": message_id or f"msg_{uuid.uuid4().hex[:12]}",
            "role": "user",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def create_assistant_message(content: str, message_id: str = None) -> dict:
        """Create an assistant message."""
        return {
            "message_id": message_id or f"msg_{uuid.uuid4().hex[:12]}",
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def create_conversation(
        user_id: str,
        horoscope_date: str,
        messages: list = None,
        conversation_id: str = None,
    ) -> dict:
        """Create a conversation dict."""
        now = datetime.now(timezone.utc).isoformat()
        return {
            "conversation_id": conversation_id or f"conv_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "horoscope_date": horoscope_date,
            "messages": messages or [],
            "created_at": now,
            "updated_at": now,
        }

    @classmethod
    def create_conversation_with_messages(
        cls,
        user_id: str,
        horoscope_date: str,
        exchanges: list[tuple[str, str]],
    ) -> dict:
        """
        Create a conversation with multiple exchanges.

        Args:
            user_id: Firebase user ID
            horoscope_date: ISO date
            exchanges: List of (user_message, assistant_response) tuples

        Returns:
            dict: Conversation with messages
        """
        messages = []
        for user_content, assistant_content in exchanges:
            messages.append(cls.create_user_message(user_content))
            messages.append(cls.create_assistant_message(assistant_content))

        return cls.create_conversation(
            user_id=user_id,
            horoscope_date=horoscope_date,
            messages=messages,
        )

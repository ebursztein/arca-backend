"""
Comprehensive tests for models.py - data validation and structure
"""
import pytest
from datetime import datetime
from models import (
    UserProfile,
    MemoryCollection,
    DailyHoroscope,
    ActionableAdvice,
    create_empty_memory,
    MeterForIOS,
    MeterGroupForIOS,
    AstrometersForIOS,
    AstrologicalFoundation,
    MeterAspect,
    AttributeKV
)
from astro import compute_birth_chart, get_sun_sign
from astrometers.meters import MeterReading, QualityLabel
from astrometers.hierarchy import MeterGroupV2


class TestUserProfile:
    """Test UserProfile model validation."""

    def test_user_profile_creation_minimal(self):
        """Test creating user profile with minimal required fields."""
        natal_chart, is_exact = compute_birth_chart("1990-06-15")

        profile = UserProfile(
            user_id="test_123",
            name="Test User",
            email="test@example.com",
            birth_date="1990-06-15",
            sun_sign="gemini",
            natal_chart=natal_chart,
            exact_chart=is_exact,
            created_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat()
        )

        assert profile.user_id == "test_123"
        assert profile.sun_sign == "gemini"
        assert profile.exact_chart == False  # No birth time = approximate
        assert profile.birth_time is None
        assert profile.birth_timezone is None
        print("✓ UserProfile minimal creation works")

    def test_user_profile_creation_full(self):
        """Test creating user profile with all fields."""
        natal_chart, is_exact = compute_birth_chart(
            "1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        profile = UserProfile(
            user_id="test_456",
            name="Full User",
            email="full@example.com",
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060,
            sun_sign="gemini",
            natal_chart=natal_chart,
            exact_chart=is_exact,
            created_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat()
        )

        assert profile.exact_chart == True  # Full info = exact
        assert profile.birth_time == "14:30"
        assert profile.birth_timezone == "America/New_York"
        print("✓ UserProfile full creation works")


class TestMemoryCollection:
    """Test MemoryCollection model."""

    def test_create_empty_memory(self):
        """Test creating empty memory collection."""
        memory = create_empty_memory("user_789")

        assert memory.user_id == "user_789"
        assert len(memory.categories) == 5  # Pre-initialized with 5 meter groups
        assert memory.updated_at  # Has timestamp
        # Verify all categories have zero engagement
        for category, engagement in memory.categories.items():
            assert engagement.count == 0
            assert engagement.last_mentioned is None
        print("✓ Empty memory creation works")

    def test_memory_format_for_llm_empty(self):
        """Test LLM formatting with empty memory."""
        memory = create_empty_memory("user_xyz")
        llm_text = memory.format_for_llm()

        assert "First time user" in llm_text
        assert "no history yet" in llm_text
        print("✓ Empty memory LLM formatting works")


class TestDailyHoroscope:
    """Test DailyHoroscope model validation."""

    def test_daily_horoscope_minimal_structure(self):
        """Test creating daily horoscope with minimal required fields."""
        from moon import MoonTransitDetail, VoidOfCourseStatus, NextLunarEvent
        from astro import ZodiacSign, House, LunarPhase

        # Create minimal moon detail
        moon_detail = MoonTransitDetail(
            moon_sign=ZodiacSign.TAURUS,
            moon_house=House.FIRST,
            moon_degree=45.5,
            moon_degree_in_sign=15.5,
            lunar_phase=LunarPhase(
                phase_name="waxing_gibbous",
                phase_emoji="🌔",
                angle=270.0,
                illumination_percent=83,
                energy="Refinement",
                ritual_suggestion="Polish details"
            ),
            moon_aspects=[],
            void_of_course=VoidOfCourseStatus.NOT_VOID,
            void_start_time=None,
            void_end_time=None,
            dispositor=None,
            next_sign_change=NextLunarEvent(
                event_type="sign_change",
                event_description="Moon enters Gemini",
                datetime_utc="2025-11-07T15:23:00",
                hours_away=36.5,
                significance="Shift to mental, communicative energy"
            ),
            next_major_aspect=None,
            next_phase_milestone=None,
            emotional_tone="Grounded",
            timing_guidance="Good for routine tasks"
        )

        # Create minimal MeterReading objects for overall intensity/harmony
        # Using MIND as placeholder group since OVERALL doesn't exist
        overall_intensity = MeterReading(
            meter_name="overall_intensity",
            date=datetime(2025, 11, 6),
            group=MeterGroupV2.MIND,
            unified_score=45.0,
            intensity=45.0,
            harmony=50.0,
            unified_quality=QualityLabel.MIXED,
            state_label="Moderate",
            interpretation="Overall intensity is moderate",
            advice=["Take it easy"],
            top_aspects=[],
            raw_scores={"dti": 45.0, "hqs": 50.0}
        )
        overall_harmony = MeterReading(
            meter_name="overall_harmony",
            date=datetime(2025, 11, 6),
            group=MeterGroupV2.MIND,
            unified_score=55.0,
            intensity=50.0,
            harmony=55.0,
            unified_quality=QualityLabel.MIXED,
            state_label="Balanced",
            interpretation="Overall harmony is balanced",
            advice=["Stay centered"],
            top_aspects=[],
            raw_scores={"dti": 50.0, "hqs": 55.0}
        )

        # Create minimal astrometers
        astrometers = AstrometersForIOS(
            date="2025-11-06T00:00:00",
            overall_unified_score=50.0,
            overall_intensity=overall_intensity,
            overall_harmony=overall_harmony,
            overall_quality="mixed",
            overall_state="Moderate energy",
            groups=[],
            top_active_meters=["vitality", "drive"],
            top_challenging_meters=["inner_stability", "focus"],
            top_flowing_meters=["communication", "love"]
        )

        horoscope = DailyHoroscope(
            date="2025-11-06",
            sun_sign="gemini",
            technical_analysis="Sample technical analysis",
            daily_theme_headline="Test headline",
            daily_overview="Test overview",
            actionable_advice=ActionableAdvice(
                do="Do this",
                dont="Don't do that",
                reflect_on="Reflect on this"
            ),
            astrometers=astrometers,
            moon_detail=moon_detail,
            look_ahead_preview="Test preview",
            energy_rhythm="Test rhythm",
            relationship_weather="Test weather",
            collective_energy="Test collective"
        )

        assert horoscope.date == "2025-11-06"
        assert horoscope.sun_sign == "gemini"
        assert horoscope.technical_analysis
        assert horoscope.moon_detail.interpretation == ""  # Default
        print("✓ DailyHoroscope minimal structure works")


class TestMeterModels:
    """Test meter-related models."""

    def test_astrological_foundation(self):
        """Test AstrologicalFoundation model."""
        foundation = AstrologicalFoundation(
            natal_planets_tracked=["sun", "mercury", "moon"],
            transit_planets_tracked=["mercury", "jupiter", "saturn"],
            key_houses={"9": "Higher mind, philosophy"},
            primary_planets={"mercury": "Rules thinking and communication"},
            secondary_planets={"sun": "Conscious awareness", "moon": "Emotional intelligence"}
        )

        assert len(foundation.natal_planets_tracked) == 3
        assert "mercury" in foundation.primary_planets
        assert "9" in foundation.key_houses
        print("✓ AstrologicalFoundation works")

    def test_meter_aspect(self):
        """Test MeterAspect model."""
        aspect = MeterAspect(
            label="Transit Neptune square Natal Mercury",
            natal_planet="mercury",
            transit_planet="neptune",
            aspect_type="square",
            orb=4.74,
            orb_percentage=59.25,
            phase="exact",
            days_to_exact=None,
            contribution=133.5,
            quality_factor=-1.0,
            natal_planet_house=10,
            natal_planet_sign="cancer",
            houses_involved=[10],
            natal_aspect_echo=None
        )

        assert aspect.transit_planet == "neptune"
        assert aspect.aspect_type == "square"
        assert aspect.quality_factor == -1.0
        assert aspect.orb == 4.74
        print("✓ MeterAspect works")

    def test_meter_for_ios_structure(self):
        """Test MeterForIOS model structure."""
        foundation = AstrologicalFoundation(
            natal_planets_tracked=["sun", "mercury"],
            transit_planets_tracked=["mercury"],
            key_houses={"9": "Higher mind"},
            primary_planets={"mercury": "Thinking"},
            secondary_planets=None
        )

        aspect = MeterAspect(
            label="Transit Mercury trine Natal Sun",
            natal_planet="sun",
            transit_planet="mercury",
            aspect_type="trine",
            orb=2.1,
            orb_percentage=26.25,
            phase="applying",
            days_to_exact=0.5,
            contribution=45.5,
            quality_factor=1.0,
            natal_planet_house=1,
            natal_planet_sign="gemini",
            houses_involved=[1],
            natal_aspect_echo=None
        )

        meter = MeterForIOS(
            meter_name="mental_clarity",
            display_name="Mental Clarity",
            group="mind",
            unified_score=75.5,
            intensity=68.0,
            harmony=83.0,
            unified_quality="harmonious",
            state_label="Sharp thinking",
            interpretation="Your mind is sharp today",
            trend_delta=5.2,
            trend_direction="improving",
            trend_change_rate="slow",
            overview="Mental Clarity represents cognitive sharpness",
            detailed="This meter tracks Mercury transits",
            astrological_foundation=foundation,
            top_aspects=[aspect]
        )

        assert meter.meter_name == "mental_clarity"
        assert meter.unified_score == 75.5
        assert len(meter.top_aspects) == 1
        assert meter.top_aspects[0].transit_planet == "mercury"
        print("✓ MeterForIOS structure works")

    def test_meter_group_for_ios(self):
        """Test MeterGroupForIOS model."""
        foundation = AstrologicalFoundation(
            natal_planets_tracked=["mercury"],
            transit_planets_tracked=["mercury"],
            key_houses={},
            primary_planets={"mercury": "Thinking"},
            secondary_planets=None
        )

        meter1 = MeterForIOS(
            meter_name="mental_clarity",
            display_name="Mental Clarity",
            group="mind",
            unified_score=75.0,
            intensity=70.0,
            harmony=80.0,
            unified_quality="harmonious",
            state_label="Sharp",
            interpretation="Sharp mind",
            overview="Cognitive sharpness",
            detailed="Mercury transits",
            astrological_foundation=foundation,
            top_aspects=[]
        )

        meter2 = MeterForIOS(
            meter_name="focus",
            display_name="Focus",
            group="mind",
            unified_score=65.0,
            intensity=60.0,
            harmony=70.0,
            unified_quality="harmonious",
            state_label="Steady",
            interpretation="Steady focus",
            overview="Concentration capacity",
            detailed="Saturn/Mars transits",
            astrological_foundation=foundation,
            top_aspects=[]
        )

        group = MeterGroupForIOS(
            group_name="mind",
            display_name="Mind",
            unified_score=70.0,
            intensity=65.0,
            harmony=75.0,
            state_label="Clear thinking",
            quality="harmonious",
            interpretation="Your mind is working well today",
            meters=[meter1, meter2],
            overview="Mental and cognitive functions",
            detailed="Combines mental clarity, focus, and communication"
        )

        assert group.group_name == "mind"
        assert len(group.meters) == 2
        assert group.unified_score == 70.0
        assert group.meters[0].meter_name == "mental_clarity"
        print("✓ MeterGroupForIOS structure works")


class TestActionableAdvice:
    """Test ActionableAdvice model."""

    def test_actionable_advice_structure(self):
        """Test ActionableAdvice has all required fields."""
        advice = ActionableAdvice(
            do="Write down three priorities before noon",
            dont="Don't make major decisions without sleeping on it",
            reflect_on="What would change if you asked for what you needed?"
        )

        assert advice.do
        assert advice.dont
        assert advice.reflect_on
        assert len(advice.do) > 10
        assert len(advice.dont) > 10
        assert len(advice.reflect_on) > 10
        print("✓ ActionableAdvice structure works")


class TestModelSerialization:
    """Test model serialization to/from JSON."""

    def test_user_profile_serialization(self):
        """Test UserProfile can be serialized and deserialized."""
        natal_chart, is_exact = compute_birth_chart("1990-06-15")

        profile = UserProfile(
            user_id="test_serial",
            name="Serial Test",
            email="serial@test.com",
            birth_date="1990-06-15",
            sun_sign="gemini",
            natal_chart=natal_chart,
            exact_chart=is_exact,
            created_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat()
        )

        # Serialize to dict
        profile_dict = profile.model_dump()
        assert isinstance(profile_dict, dict)
        assert profile_dict["user_id"] == "test_serial"

        # Deserialize back
        profile_restored = UserProfile(**profile_dict)
        assert profile_restored.user_id == profile.user_id
        assert profile_restored.sun_sign == profile.sun_sign
        print("✓ UserProfile serialization works")

    def test_memory_collection_serialization(self):
        """Test MemoryCollection can be serialized."""
        memory = create_empty_memory("test_memory")

        # Serialize to JSON string
        json_str = memory.model_dump_json()
        assert isinstance(json_str, str)
        assert "test_memory" in json_str

        # Deserialize back
        import json
        memory_dict = json.loads(json_str)
        memory_restored = MemoryCollection(**memory_dict)
        assert memory_restored.user_id == memory.user_id
        print("✓ MemoryCollection serialization works")


# =============================================================================
# Ask the Stars - Entity & Conversation Tests
# =============================================================================

from models import (
    Entity,
    EntityStatus,
    Message,
    MessageRole,
    Conversation,
    UserEntities,
    UserHoroscopes
)


class TestAskTheStarsModels:
    """Test Ask the Stars data models."""

    def test_entity_creation(self):
        """Test Entity model with attributes and relationships."""
        now = datetime.now().isoformat()
        entity = Entity(
            entity_id="ent_001",
            name="John",
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            aliases=["boyfriend", "partner"],
            attributes=[
                AttributeKV(key="role", value="partner"),
                AttributeKV(key="relationship_status", value="dating")
            ],
            related_entities=["ent_company"],
            first_seen=now,
            last_seen=now,
            mention_count=5,
            context_snippets=["Met at coffee shop", "Anniversary in June"],
            importance_score=0.85,
            created_at=now,
            updated_at=now
        )

        assert entity.name == "John"
        assert entity.attributes[0].key == "role"
        assert entity.attributes[0].value == "partner"
        assert "boyfriend" in entity.aliases
        assert "ent_company" in entity.related_entities
        print("✓ Entity with attributes and relationships works")

    def test_message_and_conversation(self):
        """Test Message and Conversation models."""
        now = datetime.now().isoformat()

        user_msg = Message(
            message_id="msg_001",
            role=MessageRole.USER,
            content="Why am I feeling anxious today?",
            timestamp=now
        )

        assistant_msg = Message(
            message_id="msg_002",
            role=MessageRole.ASSISTANT,
            content="Mars is square your Sun today...",
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

        assert len(conversation.messages) == 2
        assert conversation.messages[0].role == MessageRole.USER
        assert conversation.horoscope_date == "2025-01-20"
        print("✓ Message and Conversation models work")

    def test_user_entities_collection(self):
        """Test UserEntities single-document model."""
        now = datetime.now().isoformat()
        entities = [
            Entity(
                entity_id=f"ent_{i}",
                name=f"Entity {i}",
                entity_type="person",
                first_seen=now,
                last_seen=now,
                created_at=now,
                updated_at=now
            )
            for i in range(10)
        ]

        user_entities = UserEntities(
            user_id="user_123",
            entities=entities,
            updated_at=now
        )

        assert len(user_entities.entities) == 10
        assert user_entities.user_id == "user_123"
        print("✓ UserEntities single-document collection works")

    def test_user_horoscopes_collection(self):
        """Test UserHoroscopes single-document model."""
        now = datetime.now().isoformat()
        horoscopes = {
            "2025-01-20": {"date": "2025-01-20", "sun_sign": "taurus"},
            "2025-01-21": {"date": "2025-01-21", "sun_sign": "taurus"}
        }

        user_horoscopes = UserHoroscopes(
            user_id="user_123",
            horoscopes=horoscopes,
            updated_at=now
        )

        assert len(user_horoscopes.horoscopes) == 2
        assert "2025-01-20" in user_horoscopes.horoscopes
        print("✓ UserHoroscopes single-document collection works")

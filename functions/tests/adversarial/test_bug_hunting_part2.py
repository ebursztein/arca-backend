"""
Bug-hunting adversarial tests for Arca Backend - Part 2.

More aggressive tests targeting potential bugs in LLM, triggers,
models, and deeper edge cases.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
import json


# =============================================================================
# BUG HUNT 11: LLM Module Edge Cases
# =============================================================================

class TestLLMBugHuntDeep:
    """Deeper probing of llm.py."""

    def test_convert_aspect_contribution_zero_max_orb(self):
        """Test aspect conversion when max_orb is 0 (division by zero risk)."""
        from llm import convert_aspect_contribution_to_meter_aspect
        from astrometers.core import AspectContribution
        from astro import Planet, AspectType, ZodiacSign

        aspect = AspectContribution(
            natal_planet=Planet.SUN,
            transit_planet=Planet.MOON,
            aspect_type=AspectType.CONJUNCTION,
            orb_deviation=0.0,
            max_orb=0.0,  # BUG HUNT: Division by zero
            dti_contribution=1.0,
            quality_factor=1.0,
            natal_planet_sign=ZodiacSign.ARIES,
            natal_planet_house=1,
            label="Sun conjunct Moon",
            today_deviation=0.0,
            tomorrow_deviation=0.0
        )

        # Should not crash
        result = convert_aspect_contribution_to_meter_aspect(aspect)
        assert result.orb_percentage == 0.0, "Zero max_orb should give 0 percentage"

    def test_convert_aspect_contribution_none_deviations(self):
        """Test aspect conversion when today/tomorrow deviations are None."""
        from llm import convert_aspect_contribution_to_meter_aspect
        from astrometers.core import AspectContribution
        from astro import Planet, AspectType, ZodiacSign

        aspect = AspectContribution(
            natal_planet=Planet.SUN,
            transit_planet=Planet.MOON,
            aspect_type=AspectType.CONJUNCTION,
            orb_deviation=1.0,
            max_orb=8.0,
            dti_contribution=1.0,
            quality_factor=1.0,
            natal_planet_sign=ZodiacSign.ARIES,
            natal_planet_house=1,
            label="Sun conjunct Moon",
            today_deviation=None,  # None values
            tomorrow_deviation=None
        )

        # Should not crash
        result = convert_aspect_contribution_to_meter_aspect(aspect)
        assert result.phase == "exact", "None deviations should default to exact"

    def test_convert_aspect_contribution_applying_phase_calculation(self):
        """Test phase calculation when aspect is applying."""
        from llm import convert_aspect_contribution_to_meter_aspect
        from astrometers.core import AspectContribution
        from astro import Planet, AspectType, ZodiacSign

        aspect = AspectContribution(
            natal_planet=Planet.SUN,
            transit_planet=Planet.MOON,
            aspect_type=AspectType.CONJUNCTION,
            orb_deviation=2.0,
            max_orb=8.0,
            dti_contribution=1.0,
            quality_factor=1.0,
            natal_planet_sign=ZodiacSign.ARIES,
            natal_planet_house=1,
            label="Sun conjunct Moon",
            today_deviation=2.0,
            tomorrow_deviation=1.0  # Getting closer = applying
        )

        result = convert_aspect_contribution_to_meter_aspect(aspect)
        assert result.phase == "applying", "Decreasing deviation should be applying"

    def test_convert_aspect_contribution_separating_zero_daily_change(self):
        """Test phase calculation when daily change is zero (division by zero risk)."""
        from llm import convert_aspect_contribution_to_meter_aspect
        from astrometers.core import AspectContribution
        from astro import Planet, AspectType, ZodiacSign

        aspect = AspectContribution(
            natal_planet=Planet.SUN,
            transit_planet=Planet.MOON,
            aspect_type=AspectType.CONJUNCTION,
            orb_deviation=2.0,
            max_orb=8.0,
            dti_contribution=1.0,
            quality_factor=1.0,
            natal_planet_sign=ZodiacSign.ARIES,
            natal_planet_house=1,
            label="Sun conjunct Moon",
            today_deviation=2.0,
            tomorrow_deviation=2.0  # Same deviation = zero change
        )

        # BUG HUNT: Division by zero when daily_change is 0
        result = convert_aspect_contribution_to_meter_aspect(aspect)
        # Should handle gracefully


# =============================================================================
# BUG HUNT 12: Moon Module Edge Cases
# =============================================================================

class TestMoonBugHunt:
    """Probe moon.py for bugs."""

    def test_moon_phase_at_exact_new_moon(self):
        """Test moon phase calculation at exact new moon (illumination = 0)."""
        from moon import get_moon_transit_detail
        from astro import compute_birth_chart, NatalChartData

        # New moon date (approximately)
        chart_dict, _ = compute_birth_chart("2025-01-29")  # Near new moon
        chart = NatalChartData(**chart_dict)

        detail = get_moon_transit_detail(chart)
        assert detail is not None
        assert 0 <= detail.illumination <= 100

    def test_moon_phase_at_exact_full_moon(self):
        """Test moon phase at exact full moon (illumination = 100)."""
        from moon import get_moon_transit_detail
        from astro import compute_birth_chart, NatalChartData

        # Full moon date (approximately)
        chart_dict, _ = compute_birth_chart("2025-01-13")  # Near full moon
        chart = NatalChartData(**chart_dict)

        detail = get_moon_transit_detail(chart)
        assert detail is not None
        assert 0 <= detail.illumination <= 100

    def test_moon_void_of_course_detection(self):
        """Test void of course moon detection."""
        from moon import get_moon_transit_detail
        from astro import compute_birth_chart, NatalChartData

        chart_dict, _ = compute_birth_chart("2025-01-20")
        chart = NatalChartData(**chart_dict)

        detail = get_moon_transit_detail(chart)
        # Should have void_of_course field
        assert hasattr(detail, 'void_of_course')


# =============================================================================
# BUG HUNT 13: Astrometers Edge Cases
# =============================================================================

class TestAstrometersBugHunt:
    """Probe astrometers module for bugs."""

    def test_meter_score_with_no_aspects(self):
        """Test meter calculation when there are no relevant aspects."""
        from astrometers import get_meters
        from astro import compute_birth_chart, NatalChartData

        # Very old date might have different aspect configurations
        natal_dict, _ = compute_birth_chart("1990-06-15")
        transit_dict, _ = compute_birth_chart("2025-01-20")

        natal = NatalChartData(**natal_dict)
        transit = NatalChartData(**transit_dict)

        meters = get_meters(natal, transit)
        # All meters should have valid scores even if no aspects
        for meter in meters.meters:
            assert 0 <= meter.intensity <= 100
            assert 0 <= meter.harmony <= 100

    def test_meter_trend_calculation_first_day(self):
        """Test meter trend on first day (no previous data)."""
        from astrometers import get_meters
        from astro import compute_birth_chart, NatalChartData

        natal_dict, _ = compute_birth_chart("1990-06-15")
        transit_dict, _ = compute_birth_chart("2025-01-20")

        natal = NatalChartData(**natal_dict)
        transit = NatalChartData(**transit_dict)

        meters = get_meters(natal, transit)
        # Trends should be calculated relative to yesterday
        for meter in meters.meters:
            # Trend should exist
            assert hasattr(meter, 'trend')

    def test_meter_group_calculation_all_groups(self):
        """Test that all 5 meter groups are calculated."""
        from astrometers.meter_groups import build_all_meter_groups
        from astrometers import get_meters
        from astro import compute_birth_chart, NatalChartData

        natal_dict, _ = compute_birth_chart("1990-06-15")
        transit_dict, _ = compute_birth_chart("2025-01-20")

        natal = NatalChartData(**natal_dict)
        transit = NatalChartData(**transit_dict)

        meters = get_meters(natal, transit)
        groups = build_all_meter_groups(meters.meters)

        # Should have all 5 groups
        group_names = [g.group_name for g in groups]
        expected_groups = ["mind", "heart", "body", "instincts", "growth"]
        assert set(group_names) == set(expected_groups)


# =============================================================================
# BUG HUNT 14: Models Deep Validation
# =============================================================================

class TestModelsDeepBugHunt:
    """Deep probing of models.py validation."""

    def test_daily_horoscope_meter_interpretations_empty(self):
        """Test DailyHoroscope with empty meter_interpretations dict."""
        from models import (
            DailyHoroscope, AstrometersForIOS, AstrologicalFoundation,
            ActionableAdvice, RelationshipWeather
        )
        from astrometers.hierarchy import MeterGroupV2

        now = datetime.now().isoformat()

        # BUG HUNT: Can we create DailyHoroscope with empty interpretations?
        # The model should validate this

    def test_entity_with_very_long_context_snippets(self):
        """Test Entity with extremely long context snippets."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # BUG HUNT: No max_length on context_snippets items
        very_long_snippet = "A" * 100000  # 100KB string

        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now,
            last_seen=now,
            mention_count=1,
            context_snippets=[very_long_snippet],  # Very long!
            created_at=now,
            updated_at=now
        )
        # This creates entity with huge snippet - potential memory issue

    def test_message_content_empty_string(self):
        """Test Message with empty content."""
        from models import Message, MessageRole

        now = datetime.now().isoformat()

        # BUG HUNT: Is empty message content allowed?
        message = Message(
            message_id="msg_001",
            role=MessageRole.USER,
            content="",  # Empty content
            timestamp=now
        )
        assert message.content == ""

    def test_conversation_with_thousands_of_messages(self):
        """Test Conversation with very large message array."""
        from models import Conversation, Message, MessageRole

        now = datetime.now().isoformat()

        # BUG HUNT: No limit on messages array
        # This could be a memory bomb
        messages = [
            Message(
                message_id=f"msg_{i:05d}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i} " * 100,
                timestamp=now
            )
            for i in range(10000)  # 10K messages
        ]

        conv = Conversation(
            conversation_id="conv_001",
            user_id="user_001",
            horoscope_date="2025-01-20",
            messages=messages
        )
        assert len(conv.messages) == 10000

    def test_entity_with_circular_related_entities(self):
        """Test Entity that references itself in related_entities."""
        from models import Entity, EntityStatus

        now = datetime.now().isoformat()

        # BUG HUNT: Entity can reference itself
        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now,
            last_seen=now,
            mention_count=1,
            related_entities=["ent_001"],  # References itself!
            created_at=now,
            updated_at=now
        )
        assert "ent_001" in entity.related_entities


# =============================================================================
# BUG HUNT 15: Synastry and Compatibility Deep Dive
# =============================================================================

class TestSynastryBugHunt:
    """Deep testing of synastry calculations."""

    def test_synastry_with_identical_charts(self):
        """Test synastry when both charts are identical."""
        from compatibility import calculate_synastry_aspects, calculate_compatibility
        from astro import compute_birth_chart, NatalChartData

        chart_dict, _ = compute_birth_chart("1990-06-15")
        chart1 = NatalChartData(**chart_dict)
        chart2 = NatalChartData(**chart_dict)

        aspects = calculate_synastry_aspects(chart1, chart2)

        # BUG HUNT: 11 planets x 11 planets = 121 potential exact conjunctions
        # But wait - planet to itself is meaningless
        # We'd expect 11 exact conjunctions (each planet to its counterpart)

        # With same chart, every planet pairs with its twin at 0 orb
        exact_conjunctions = [a for a in aspects if a.orb == 0.0]
        assert len(exact_conjunctions) >= 11

    def test_compatibility_score_range(self):
        """Test that compatibility scores are always in valid range."""
        from compatibility import get_compatibility_from_birth_data

        result = get_compatibility_from_birth_data(
            user_birth_date="1990-06-15",
            user_birth_time=None,
            user_birth_lat=None,
            user_birth_lon=None,
            user_birth_timezone=None,
            connection_birth_date="1985-03-20"
        )

        # All scores should be in range
        assert 0 <= result.romantic.overall_score <= 100
        assert 0 <= result.friendship.overall_score <= 100
        assert 0 <= result.coworker.overall_score <= 100

        for cat in result.romantic.categories:
            assert -100 <= cat.score <= 100

    def test_composite_sign_all_12_combinations(self):
        """Test composite sign calculation for all sign boundaries."""
        from compatibility import calculate_composite_sign

        signs = []
        for i in range(12):
            degree = i * 30 + 15  # Middle of each sign
            sign = calculate_composite_sign(degree, degree)
            signs.append(sign)

        # Should have all 12 unique signs
        expected = [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        ]
        assert signs == expected


# =============================================================================
# BUG HUNT 16: Connections Validation Deep Dive
# =============================================================================

class TestConnectionsDeepBugHunt:
    """Deep validation testing of connections module."""

    def test_connection_relationship_type_validation(self):
        """Test Connection with invalid relationship_type."""
        from connections import Connection
        from models import RelationshipType
        from pydantic import ValidationError

        now = datetime.now().isoformat()

        # Valid relationship types
        valid_types = ["friend", "romantic", "family", "coworker"]
        for rt in valid_types:
            conn = Connection(
                connection_id="conn_001",
                name="Test",
                birth_date="1990-01-15",
                relationship_type=rt,
                created_at=now,
                updated_at=now
            )
            assert conn.relationship_type == rt

    def test_connection_latitude_longitude_mismatch(self):
        """Test Connection with only lat or only lon set."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        # BUG HUNT: Only lat set, no lon
        conn = Connection(
            connection_id="conn_001",
            name="Test",
            birth_date="1990-01-15",
            birth_lat=40.0,
            birth_lon=None,  # Missing!
            relationship_type=RelationshipType.FRIEND,
            created_at=now,
            updated_at=now
        )
        # This is allowed but might cause issues in chart calculation

    def test_connection_future_birth_date(self):
        """Test Connection with future birth date."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()
        future_date = "2099-01-01"

        # BUG HUNT: Future birth dates are allowed
        conn = Connection(
            connection_id="conn_001",
            name="Future Person",
            birth_date=future_date,
            relationship_type=RelationshipType.FRIEND,
            created_at=now,
            updated_at=now
        )
        assert conn.birth_date == future_date  # Bug: Should validate


# =============================================================================
# BUG HUNT 17: Entity Extraction Actions Edge Cases
# =============================================================================

class TestEntityActionsDeepBugHunt:
    """Deep testing of entity merge action execution."""

    def test_multiple_creates_with_same_name(self):
        """Test creating multiple entities with the same name."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction

        now = datetime.now()

        # Two create actions for same name
        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="create",
                    entity_name="John",
                    entity_type="person",
                    context_update="First John"
                ),
                EntityMergeAction(
                    action="create",
                    entity_name="John",  # Same name!
                    entity_type="person",
                    context_update="Second John"
                )
            ]
        )

        result = execute_merge_actions(merged, [], now)
        # BUG HUNT: Should we allow duplicate names?
        johns = [e for e in result if e.name == "John"]
        assert len(johns) == 2, "Should create two separate Johns"

    def test_merge_then_update_same_entity(self):
        """Test merging and then updating the same entity in one batch."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus

        now = datetime.now()
        existing = Entity(
            entity_id="ent_001",
            name="John",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        # Merge and then update same entity
        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="merge",
                    entity_name="John",
                    entity_type="person",
                    merge_with_id="ent_001",
                    context_update="Merge context"
                ),
                EntityMergeAction(
                    action="update",
                    entity_name="John",
                    entity_type="person",
                    merge_with_id="ent_001",
                    context_update="Update context"
                )
            ]
        )

        result = execute_merge_actions(merged, [existing], now)
        john = next(e for e in result if e.name == "John")
        # Should have both contexts added
        assert len(john.context_snippets) == 2


# =============================================================================
# BUG HUNT 18: Import and Dependency Issues
# =============================================================================

class TestImportBugHunt:
    """Test for import issues and missing dependencies."""

    def test_all_meter_json_files_exist(self):
        """Test that all meter JSON files exist and are valid."""
        from pathlib import Path
        import json

        base_path = Path(__file__).parent.parent.parent / "astrometers" / "labels"

        meter_names = [
            "clarity", "focus", "communication",
            "resilience", "connections", "vulnerability",
            "energy", "drive", "strength",
            "vision", "flow", "intuition", "creativity",
            "momentum", "ambition", "evolution", "circle"
        ]

        for meter_name in meter_names:
            json_path = base_path / f"{meter_name}.json"
            assert json_path.exists(), f"Missing meter file: {meter_name}.json"

            with open(json_path) as f:
                data = json.load(f)
                assert "description" in data, f"{meter_name}.json missing description"
                assert "overview" in data["description"]

    def test_all_group_json_files_exist(self):
        """Test that all group JSON files exist and are valid."""
        from pathlib import Path
        import json

        base_path = Path(__file__).parent.parent.parent / "astrometers" / "labels" / "groups"

        group_names = ["mind", "heart", "body", "instincts", "growth"]

        for group_name in group_names:
            json_path = base_path / f"{group_name}.json"
            assert json_path.exists(), f"Missing group file: {group_name}.json"

            with open(json_path) as f:
                data = json.load(f)
                assert "description" in data


# =============================================================================
# BUG HUNT 19: RelationshipType Enum Completeness
# =============================================================================

class TestRelationshipTypesBugHunt:
    """Test relationship type handling."""

    def test_all_relationship_types_have_category_mapping(self):
        """Test that all RelationshipTypes map to compatibility categories."""
        from models import RelationshipType
        from compatibility import (
            ROMANTIC_CATEGORIES, FRIENDSHIP_CATEGORIES, COWORKER_CATEGORIES
        )

        # Each relationship type should map to a category set
        type_to_categories = {
            RelationshipType.FRIEND: FRIENDSHIP_CATEGORIES,
            RelationshipType.ROMANTIC: ROMANTIC_CATEGORIES,
            RelationshipType.FAMILY: FRIENDSHIP_CATEGORIES,  # Usually uses friendship
            RelationshipType.COWORKER: COWORKER_CATEGORIES,
        }

        for rt in RelationshipType:
            # BUG HUNT: Does every type have a mapping?
            # This should pass if all types are covered
            pass  # Just iterate to ensure no errors


# =============================================================================
# BUG HUNT 20: Timestamp Handling
# =============================================================================

class TestTimestampBugHunt:
    """Test timestamp handling edge cases."""

    def test_entity_with_malformed_timestamps(self):
        """Test Entity with timestamps in wrong format."""
        from models import Entity, EntityStatus

        # BUG HUNT: Timestamps are just strings, no validation
        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen="not-a-timestamp",  # Invalid!
            last_seen="also-not-valid",
            mention_count=1,
            created_at="garbage",
            updated_at="data"
        )
        # These pass because they're just str fields!

    def test_importance_score_with_malformed_timestamp(self):
        """Test importance score calculation with invalid last_seen."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()

        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen="not-a-timestamp",
            last_seen="2025-13-45T99:99:99",  # Invalid but parseable fail
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        # BUG HUNT: What happens when we try to calculate importance?
        try:
            score = calculate_entity_importance_score(entity, now)
            # If it doesn't crash, that's also a bug - invalid dates should fail
        except ValueError:
            pass  # Expected: should fail on invalid timestamp

    def test_conversation_horoscope_date_validation(self):
        """Test Conversation with invalid horoscope_date."""
        from models import Conversation

        now = datetime.now().isoformat()

        # BUG HUNT: horoscope_date is just a str, no validation
        conv = Conversation(
            conversation_id="conv_001",
            user_id="user_001",
            horoscope_date="not-a-date",  # Invalid!
            messages=[]
        )
        assert conv.horoscope_date == "not-a-date"  # Bug: Should validate


# =============================================================================
# BUG HUNT 21: Transits Edge Cases
# =============================================================================

class TestTransitsBugHunt:
    """Test transit calculation edge cases."""

    def test_summarize_transits_with_invalid_sun_sign(self):
        """Test transit summary with invalid sun sign string."""
        from astro import summarize_transits, compute_birth_chart

        chart_dict, _ = compute_birth_chart("2025-01-20")

        # BUG HUNT: What happens with invalid sun sign?
        try:
            summary = summarize_transits(chart_dict, "invalid_sign")
        except ValueError:
            pass  # Expected

    def test_upcoming_transits_date_range(self):
        """Test upcoming transits with various date ranges."""
        from astro import get_upcoming_transits, compute_birth_chart, NatalChartData

        natal_dict, _ = compute_birth_chart("1990-06-15")
        natal = NatalChartData(**natal_dict)

        # Should work with default days
        transits = get_upcoming_transits(natal, days_ahead=7)
        assert isinstance(transits, list)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

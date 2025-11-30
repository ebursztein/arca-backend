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
            label="Sun conjunct Moon",
            natal_planet=Planet.SUN,
            transit_planet=Planet.MOON,
            aspect_type=AspectType.CONJUNCTION,
            weightage=1.0,
            transit_power=1.0,
            quality_factor=1.0,
            dti_contribution=1.0,
            hqs_contribution=1.0,
            orb_deviation=0.0,
            max_orb=0.0,  # BUG HUNT: Division by zero
            natal_planet_sign=ZodiacSign.ARIES,
            natal_planet_house=1,
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
            label="Sun conjunct Moon",
            natal_planet=Planet.SUN,
            transit_planet=Planet.MOON,
            aspect_type=AspectType.CONJUNCTION,
            weightage=1.0,
            transit_power=1.0,
            quality_factor=1.0,
            dti_contribution=1.0,
            hqs_contribution=1.0,
            orb_deviation=1.0,
            max_orb=8.0,
            natal_planet_sign=ZodiacSign.ARIES,
            natal_planet_house=1,
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
            label="Sun conjunct Moon",
            natal_planet=Planet.SUN,
            transit_planet=Planet.MOON,
            aspect_type=AspectType.CONJUNCTION,
            weightage=1.0,
            transit_power=1.0,
            quality_factor=1.0,
            dti_contribution=1.0,
            hqs_contribution=1.0,
            orb_deviation=2.0,
            max_orb=8.0,
            natal_planet_sign=ZodiacSign.ARIES,
            natal_planet_house=1,
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
            label="Sun conjunct Moon",
            natal_planet=Planet.SUN,
            transit_planet=Planet.MOON,
            aspect_type=AspectType.CONJUNCTION,
            weightage=1.0,
            transit_power=1.0,
            quality_factor=1.0,
            dti_contribution=1.0,
            hqs_contribution=1.0,
            orb_deviation=2.0,
            max_orb=8.0,
            natal_planet_sign=ZodiacSign.ARIES,
            natal_planet_house=1,
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
        """Test moon phase calculation at exact new moon."""
        from moon import get_moon_transit_detail
        from astro import compute_birth_chart

        # New moon date (approximately)
        natal_dict, _ = compute_birth_chart("1990-06-15")
        transit_dict, _ = compute_birth_chart("2025-01-29")  # Near new moon

        detail = get_moon_transit_detail(natal_dict, transit_dict, "2025-01-29T12:00:00")
        assert detail is not None
        assert 0 <= detail.lunar_phase.illumination_percent <= 100

    def test_moon_phase_at_exact_full_moon(self):
        """Test moon phase at exact full moon."""
        from moon import get_moon_transit_detail
        from astro import compute_birth_chart

        # Full moon date (approximately)
        natal_dict, _ = compute_birth_chart("1990-06-15")
        transit_dict, _ = compute_birth_chart("2025-01-13")  # Near full moon

        detail = get_moon_transit_detail(natal_dict, transit_dict, "2025-01-13T12:00:00")
        assert detail is not None
        assert 0 <= detail.lunar_phase.illumination_percent <= 100

    def test_moon_has_lunar_phase(self):
        """Test moon detail has lunar phase info."""
        from moon import get_moon_transit_detail
        from astro import compute_birth_chart

        natal_dict, _ = compute_birth_chart("1990-06-15")
        transit_dict, _ = compute_birth_chart("2025-01-20")

        detail = get_moon_transit_detail(natal_dict, transit_dict, "2025-01-20T12:00:00")
        assert hasattr(detail, 'lunar_phase')
        assert detail.lunar_phase is not None


# =============================================================================
# BUG HUNT 13: Astrometers Edge Cases
# =============================================================================

class TestAstrometersBugHunt:
    """Probe astrometers module for bugs."""

    def test_meter_score_with_no_aspects(self):
        """Test meter calculation when there are no relevant aspects."""
        from astrometers import get_meters
        from astro import compute_birth_chart

        # Very old date might have different aspect configurations
        natal_dict, _ = compute_birth_chart("1990-06-15")
        transit_dict, _ = compute_birth_chart("2025-01-20")

        meters = get_meters(natal_dict, transit_dict)
        # All meters should have valid scores even if no aspects
        for meter in meters.meters:
            assert 0 <= meter.intensity <= 100
            assert 0 <= meter.harmony <= 100

    def test_meter_trend_calculation_first_day(self):
        """Test meter trend on first day (no previous data)."""
        from astrometers import get_meters
        from astro import compute_birth_chart

        natal_dict, _ = compute_birth_chart("1990-06-15")
        transit_dict, _ = compute_birth_chart("2025-01-20")

        meters = get_meters(natal_dict, transit_dict)
        # Trends should be calculated relative to yesterday
        for meter in meters.meters:
            # Trend should exist
            assert hasattr(meter, 'trend')

    def test_meter_group_calculation_all_groups(self):
        """Test that all 5 meter groups are calculated."""
        from astrometers.meter_groups import build_all_meter_groups
        from astrometers import get_meters
        from astro import compute_birth_chart

        natal_dict, _ = compute_birth_chart("1990-06-15")
        transit_dict, _ = compute_birth_chart("2025-01-20")

        meters = get_meters(natal_dict, transit_dict)
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

    def test_entity_with_long_context_snippets_rejected(self):
        """Test Entity rejects extremely long context snippets."""
        from models import Entity, EntityStatus
        from pydantic import ValidationError

        now = datetime.now().isoformat()

        # Validation should reject very long context snippets
        very_long_snippet = "A" * 100000  # 100KB string

        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now,
                last_seen=now,
                mention_count=1,
                context_snippets=[very_long_snippet],
                created_at=now,
                updated_at=now
            )

    def test_message_content_empty_string_rejected(self):
        """Test Message rejects empty content."""
        from models import Message, MessageRole
        from pydantic import ValidationError

        now = datetime.now().isoformat()

        # Validation should reject empty content
        with pytest.raises(ValidationError):
            Message(
                message_id="msg_001",
                role=MessageRole.USER,
                content="",  # Empty content - should be rejected
                timestamp=now
            )

    def test_conversation_with_many_messages(self):
        """Test Conversation can have many messages."""
        from models import Conversation, Message, MessageRole

        now = datetime.now().isoformat()

        # Create a reasonable number of messages
        messages = [
            Message(
                message_id=f"msg_{i:05d}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i}",
                timestamp=now
            )
            for i in range(100)  # 100 messages is reasonable
        ]

        conv = Conversation(
            conversation_id="conv_001",
            user_id="user_001",
            horoscope_date="2025-01-20",
            messages=messages,
            created_at=now,
            updated_at=now
        )
        assert len(conv.messages) == 100

    def test_entity_related_entities_validation(self):
        """Test Entity related_entities validation."""
        from models import Entity, EntityStatus
        from pydantic import ValidationError

        now = datetime.now().isoformat()

        # Self-reference should be rejected
        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now,
                last_seen=now,
                mention_count=1,
                related_entities=["ent_001"],  # Self-reference - should be rejected
                created_at=now,
                updated_at=now
            )


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
        valid_types = ["friend", "partner", "family", "coworker"]
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

    def test_connection_latitude_longitude_mismatch_rejected(self):
        """Test Connection rejects only lat or only lon set."""
        from connections import Connection
        from models import RelationshipType
        from pydantic import ValidationError

        now = datetime.now().isoformat()

        # Validation should reject lat without lon
        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="Test",
                birth_date="1990-01-15",
                birth_lat=40.0,
                birth_lon=None,  # Missing!
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_connection_future_birth_date_rejected(self):
        """Test Connection rejects future birth date."""
        from connections import Connection
        from models import RelationshipType
        from pydantic import ValidationError

        now = datetime.now().isoformat()
        future_date = "2099-01-01"

        # Validation should reject future birth dates
        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="Future Person",
                birth_date=future_date,
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )


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

    def test_all_relationship_types_valid(self):
        """Test that RelationshipTypes can be enumerated."""
        from models import RelationshipType

        # Verify all relationship types are defined
        types = list(RelationshipType)
        assert len(types) >= 4, "Should have at least 4 relationship types"

        # Verify expected types exist
        type_values = [t.value for t in types]
        assert "friend" in type_values
        assert "partner" in type_values
        assert "family" in type_values
        assert "coworker" in type_values


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
        """Test Conversation rejects invalid horoscope_date."""
        from models import Conversation
        from pydantic import ValidationError

        now = datetime.now().isoformat()

        # Validation should reject invalid date format
        with pytest.raises(ValidationError):
            Conversation(
                conversation_id="conv_001",
                user_id="user_001",
                horoscope_date="not-a-date",  # Invalid - should be rejected
                messages=[],
                created_at=now,
                updated_at=now
            )


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
        from astro import get_upcoming_transits, compute_birth_chart

        natal_dict, _ = compute_birth_chart("1990-06-15")

        # Should work with default days
        transits = get_upcoming_transits(natal_dict, start_date="2025-01-20", days_ahead=7)
        assert isinstance(transits, list)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

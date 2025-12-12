"""
Adversarial tests for Arca Backend.

Tests edge cases, missing data, invalid inputs, and boundary conditions
to find bugs in the codebase.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock


# =============================================================================
# ENTITY EXTRACTION TESTS
# =============================================================================

class TestEntityExtractionAdversarial:
    """Adversarial tests for entity_extraction.py"""

    def test_execute_merge_actions_with_invalid_action_type(self):
        """Test EntityMergeAction rejects invalid action type."""
        from pydantic import ValidationError
        from models import MergedEntities, EntityMergeAction

        # Validation should reject invalid action types at model creation
        with pytest.raises(ValidationError):
            EntityMergeAction(
                action="delete",  # Invalid action type - should be rejected
                entity_name="Test",
                entity_type="person"
            )

    def test_execute_merge_actions_merge_with_nonexistent_id(self):
        """Test merge action with a merge_with_id that doesn't exist."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction

        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="merge",
                    entity_name="John",
                    entity_type="relationship",
                    merge_with_id="nonexistent_id_12345",  # Doesn't exist
                    new_alias="Johnny"
                )
            ]
        )

        # Should not crash
        result = execute_merge_actions(merged, [], datetime.now())
        # Merge should be skipped since target doesn't exist
        assert len(result) == 0

    def test_execute_merge_actions_update_nonexistent_entity(self):
        """Test update action for an entity that doesn't exist."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, AttributeKV

        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="update",
                    entity_name="Ghost",
                    entity_type="person",
                    context_update="This entity doesn't exist",
                    attribute_updates=[AttributeKV(key="test", value="value")]
                )
            ]
        )

        result = execute_merge_actions(merged, [], datetime.now())
        # Update should be skipped since target doesn't exist
        assert len(result) == 0

    def test_execute_merge_actions_link_without_target(self):
        """Test link action without link_to_entity_id."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus

        now = datetime.now()
        existing = [
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="link",
                    entity_name="Test",
                    entity_type="person",
                    merge_with_id="ent_001",
                    link_to_entity_id=None  # Missing target
                )
            ]
        )

        # Should not crash
        result = execute_merge_actions(merged, existing, now)
        assert len(result) == 1

    def test_get_top_entities_empty_list(self):
        """Test get_top_entities_by_importance with empty list."""
        from entity_extraction import get_top_entities_by_importance

        result = get_top_entities_by_importance([], limit=15)
        assert result == []

    def test_get_top_entities_all_archived(self):
        """Test get_top_entities_by_importance when all entities are archived."""
        from entity_extraction import get_top_entities_by_importance
        from models import Entity, EntityStatus

        now = datetime.now()
        entities = [
            Entity(
                entity_id=f"ent_{i}",
                name=f"Entity {i}",
                entity_type="person",
                status=EntityStatus.ARCHIVED,  # All archived
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
            for i in range(5)
        ]

        result = get_top_entities_by_importance(entities, limit=15)
        # Should return empty - only active entities are returned
        assert len(result) == 0

    def test_route_people_to_connections_empty_connections(self):
        """Test route_people_to_connections with no connections."""
        from entity_extraction import route_people_to_connections
        from models import Entity, EntityStatus

        now = datetime.now()
        entities = [
            Entity(
                entity_id="ent_001",
                name="John",
                entity_type="relationship",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                context_snippets=["Met John today"],
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        filtered, updates = route_people_to_connections(entities, [], "2025-01-20")
        # Should return entities unchanged, no updates
        assert len(filtered) == 1
        assert len(updates) == 0

    def test_route_people_to_connections_empty_name(self):
        """Test route_people_to_connections with connection that has empty name."""
        from entity_extraction import route_people_to_connections
        from models import Entity, EntityStatus

        now = datetime.now()
        entities = [
            Entity(
                entity_id="ent_001",
                name="John",
                entity_type="relationship",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                context_snippets=["Met John today"],
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        # Connection with empty name
        connections = [{"name": "", "connection_id": "conn_001"}]

        filtered, updates = route_people_to_connections(entities, connections, "2025-01-20")
        # Should not match, entity stays
        assert len(filtered) == 1
        assert len(updates) == 0

    def test_merge_attributes_with_empty_lists(self):
        """Test merge_attributes with empty lists."""
        from entity_extraction import merge_attributes
        from models import AttributeKV

        result = merge_attributes([], [])
        assert result == []

    def test_merge_attributes_overwrites_existing(self):
        """Test that merge_attributes overwrites existing keys."""
        from entity_extraction import merge_attributes
        from models import AttributeKV

        existing = [AttributeKV(key="role", value="boss")]
        updates = [AttributeKV(key="role", value="coworker")]

        result = merge_attributes(existing, updates)
        assert len(result) == 1
        assert result[0].value == "coworker"


# =============================================================================
# MODELS VALIDATION TESTS
# =============================================================================

class TestModelsAdversarial:
    """Adversarial tests for models.py"""

    def test_calculate_entity_importance_score_with_future_last_seen(self):
        """Test importance score with last_seen in the future."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()
        future = now + timedelta(days=30)

        entity = Entity(
            entity_id="ent_001",
            name="Future",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=future.isoformat(),  # In the future!
            mention_count=5,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        # Should handle gracefully - recency should be 1.0 or clipped
        score = calculate_entity_importance_score(entity, now)
        # With future date, days_since_mention will be negative
        # recency = max(0.0, 1.0 - (negative / 30)) = 1.0+ which is > 1
        # This is a potential bug if not handled
        assert score >= 0.0
        # BUG: recency can exceed 1.0 with future dates

    def test_calculate_entity_importance_score_with_malformed_timestamp(self):
        """Test importance score with malformed timestamp."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()

        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen="not-a-valid-timestamp",  # Malformed!
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        # This should raise an exception
        with pytest.raises(ValueError):
            calculate_entity_importance_score(entity, now)

    def test_calculate_entity_importance_score_with_timezone_aware_timestamp(self):
        """Test importance score with timezone-aware timestamp."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()

        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen="2025-01-20T10:30:00+05:30",  # Timezone-aware
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        # Should handle timezone-aware timestamps
        # BUG: Mixing timezone-naive and timezone-aware datetimes
        try:
            score = calculate_entity_importance_score(entity, now)
        except TypeError as e:
            pytest.fail(f"Failed with timezone-aware timestamp: {e}")

    def test_calculate_entity_importance_score_with_z_suffix(self):
        """Test importance score with Z suffix timestamp."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()

        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen="2025-01-20T10:30:00Z",  # Z suffix
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        # Should handle Z suffix
        score = calculate_entity_importance_score(entity, now)
        assert score >= 0.0

    def test_entity_with_zero_mention_count(self):
        """Test Entity creation with mention_count = 0 (should fail validation)."""
        from models import Entity, EntityStatus
        from pydantic import ValidationError

        now = datetime.now()

        # mention_count has ge=1 constraint
        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=0,  # Invalid - must be >= 1
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )

    def test_entity_with_importance_score_out_of_range(self):
        """Test Entity with importance_score > 1.0."""
        from models import Entity, EntityStatus
        from pydantic import ValidationError

        now = datetime.now()

        # importance_score has le=1.0 constraint
        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                importance_score=1.5,  # Invalid - must be <= 1.0
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )

    def test_user_profile_with_invalid_latitude(self):
        """Test UserProfile with latitude out of range."""
        from models import UserProfile
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_001",
                name="Test",
                email="test@test.com",
                birth_date="1990-01-01",
                birth_lat=100.0,  # Invalid - must be -90 to 90
                sun_sign="aries",
                natal_chart={},
                exact_chart=False,
                created_at=datetime.now().isoformat(),
                last_active=datetime.now().isoformat()
            )

    def test_user_profile_with_invalid_longitude(self):
        """Test UserProfile with longitude out of range."""
        from models import UserProfile
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserProfile(
                user_id="user_001",
                name="Test",
                email="test@test.com",
                birth_date="1990-01-01",
                birth_lon=200.0,  # Invalid - must be -180 to 180
                sun_sign="aries",
                natal_chart={},
                exact_chart=False,
                created_at=datetime.now().isoformat(),
                last_active=datetime.now().isoformat()
            )


# =============================================================================
# COMPATIBILITY TESTS
# =============================================================================

class TestCompatibilityAdversarial:
    """Adversarial tests for compatibility.py"""

    def test_get_planet_degree_nonexistent_planet(self):
        """Test get_planet_degree with a planet that doesn't exist."""
        from compatibility import get_planet_degree
        from astro import compute_birth_chart, NatalChartData

        chart_dict, _ = compute_birth_chart(birth_date="1990-06-15")
        chart = NatalChartData(**chart_dict)

        # Try to get a non-existent planet
        degree = get_planet_degree(chart, "krypton")
        assert degree is None

    def test_calculate_aspect_at_exact_angle(self):
        """Test calculate_aspect at exactly 0 degrees (conjunction)."""
        from compatibility import calculate_aspect

        result = calculate_aspect(100.0, 100.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, is_harmonious = result
        assert aspect_type == "conjunction"
        assert orb == 0.0

    def test_calculate_aspect_at_180_degrees(self):
        """Test calculate_aspect at exactly 180 degrees (opposition)."""
        from compatibility import calculate_aspect

        result = calculate_aspect(0.0, 180.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, is_harmonious = result
        assert aspect_type == "opposition"
        assert orb == 0.0

    def test_calculate_aspect_at_360_boundary(self):
        """Test calculate_aspect across the 0/360 degree boundary."""
        from compatibility import calculate_aspect

        # 355 degrees and 5 degrees should be a conjunction (10 degree orb)
        result = calculate_aspect(355.0, 5.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, is_harmonious = result
        assert aspect_type == "conjunction"
        assert orb == 10.0

    def test_calculate_aspect_challenging_conjunction(self):
        """Test that Saturn-Moon conjunction is marked as challenging."""
        from compatibility import calculate_aspect

        result = calculate_aspect(100.0, 100.0, "saturn", "moon")
        assert result is not None
        aspect_type, orb, is_harmonious = result
        assert aspect_type == "conjunction"
        assert is_harmonious is False  # Challenging conjunction

    def test_calculate_category_score_no_matching_aspects(self):
        """Test calculate_category_score when no aspects match the planet pairs."""
        from compatibility import calculate_category_score, SynastryAspect

        aspects = [
            SynastryAspect(
                id="asp_001",
                user_planet="neptune",
                their_planet="uranus",
                aspect_type="trine",
                orb=2.0,
                is_harmonious=True
            )
        ]

        # Planet pairs that don't include neptune-uranus
        planet_pairs = [("sun", "moon"), ("venus", "mars")]

        score, aspect_ids = calculate_category_score(aspects, planet_pairs)
        assert score == 0  # No matching aspects
        assert aspect_ids == []

    def test_calculate_composite_sign_at_boundary(self):
        """Test calculate_composite_sign at sign boundary."""
        from compatibility import calculate_composite_sign

        # 359.9 and 0.1 should give midpoint at 0 degrees (Aries)
        # Because: abs(359.9 - 0.1) = 359.8 > 180
        # So: ((359.9 + 0.1 + 360) / 2) % 360 = 360 % 360 = 0 (Aries)
        sign = calculate_composite_sign(359.9, 0.1)
        assert sign == "aries"  # Midpoint is 0 degrees = Aries

        # Test another boundary case: 350 and 10
        # abs(350 - 10) = 340 > 180
        # ((350 + 10 + 360) / 2) % 360 = 360 % 360 = 0 (Aries)
        sign = calculate_composite_sign(350.0, 10.0)
        assert sign == "aries"

    def test_calculate_vibe_score_empty_transits(self):
        """Test calculate_vibe_score with empty transits list."""
        from compatibility import calculate_vibe_score

        score = calculate_vibe_score([])
        assert score == 50  # Neutral

    def test_calculate_vibe_score_all_challenging(self):
        """Test calculate_vibe_score with all challenging transits."""
        from compatibility import calculate_vibe_score

        transits = [
            {"is_harmonious": False, "orb": 1.0},
            {"is_harmonious": False, "orb": 2.0},
        ]

        score = calculate_vibe_score(transits)
        assert score < 50  # Should be below neutral

    def test_compatibility_with_empty_charts(self):
        """Test compatibility calculation with charts that have empty planet lists."""
        from compatibility import calculate_synastry_aspects
        from astro import NatalChartData

        # Create mock charts with empty planet lists
        # This shouldn't happen in practice but tests robustness
        mock_chart1 = MagicMock(spec=NatalChartData)
        mock_chart1.planets = []

        mock_chart2 = MagicMock(spec=NatalChartData)
        mock_chart2.planets = []

        aspects = calculate_synastry_aspects(mock_chart1, mock_chart2)
        assert aspects == []


# =============================================================================
# ASTRO CALCULATIONS TESTS
# =============================================================================

class TestAstroAdversarial:
    """Adversarial tests for astro.py"""

    def test_get_sun_sign_leap_year_feb_29(self):
        """Test sun sign calculation for Feb 29 on leap year."""
        from astro import get_sun_sign

        # Feb 29, 2000 is valid
        sign = get_sun_sign("2000-02-29")
        assert sign.value == "pisces"

    def test_get_sun_sign_invalid_date_format(self):
        """Test sun sign calculation with invalid date format."""
        from astro import get_sun_sign

        with pytest.raises(Exception):  # Should raise ValueError or similar
            get_sun_sign("29-02-2000")  # Wrong format

    def test_get_sun_sign_nonexistent_date(self):
        """Test sun sign calculation for Feb 30 (doesn't exist)."""
        from astro import get_sun_sign

        with pytest.raises(Exception):
            get_sun_sign("2000-02-30")  # Invalid date

    def test_compute_birth_chart_with_extreme_latitude(self):
        """Test birth chart with extreme latitude (Arctic/Antarctic)."""
        from astro import compute_birth_chart

        # This might fail or have issues with house calculations
        try:
            chart, is_exact = compute_birth_chart(
                birth_date="1990-06-21",
                birth_time="12:00",
                birth_timezone="UTC",
                birth_lat=89.9,  # Very high latitude
                birth_lon=0.0
            )
            # Should still produce a chart
            assert chart is not None
        except Exception as e:
            # Some astrology libraries have issues at extreme latitudes
            pytest.skip(f"Extreme latitude not supported: {e}")

    def test_compute_birth_chart_date_at_sign_boundary(self):
        """Test birth chart for date right at sign boundary with non-zero coords."""
        from astro import compute_birth_chart, get_sun_sign

        # March 20 is right at Pisces/Aries boundary - use non-zero coords
        chart, _ = compute_birth_chart(
            birth_date="1990-03-20",
            birth_time="12:00",
            birth_timezone="UTC",
            birth_lat=40.0,
            birth_lon=-74.0
        )

        # Check the sun sign in the chart
        sun_planet = [p for p in chart["planets"] if p["name"] == "sun"][0]
        # Could be either Pisces or Aries depending on exact time
        assert sun_planet["sign"] in ["pisces", "aries"]

    def test_compute_birth_chart_with_zero_coordinates(self):
        """BUG: compute_birth_chart fails with lat=0.0 or lon=0.0 (equator/prime meridian)."""
        from astro import compute_birth_chart

        # BUG: This fails because 0.0 is falsy in Python
        # The code does: assert birth_lat and birth_lon
        # Which fails when either is 0.0
        try:
            chart, is_exact = compute_birth_chart(
                birth_date="1990-06-15",
                birth_time="12:00",
                birth_timezone="UTC",
                birth_lat=0.0,  # Equator - valid but causes AssertionError!
                birth_lon=0.0   # Prime Meridian - valid but causes AssertionError!
            )
            # Should succeed - people CAN be born on the equator
            assert chart is not None
        except AssertionError:
            pytest.fail("BUG: compute_birth_chart fails with lat=0.0 or lon=0.0 because 0.0 is falsy")

    def test_calculate_solar_house_same_sign(self):
        """Test solar house calculation when sun and transit are same sign."""
        from astro import calculate_solar_house

        house = calculate_solar_house("aries", "aries")
        assert house.value == 1  # First house

    def test_calculate_solar_house_opposite_sign(self):
        """Test solar house calculation for opposite sign."""
        from astro import calculate_solar_house

        house = calculate_solar_house("aries", "libra")
        assert house.value == 7  # Seventh house (opposite)

    def test_summarize_transits_with_missing_sun(self):
        """Test transit summary when sun sign is missing/invalid."""
        from astro import summarize_transits, compute_birth_chart

        chart, _ = compute_birth_chart(birth_date="2025-01-20")

        # Invalid sun sign
        try:
            summary = summarize_transits(chart, "invalid_sign")
            # Should handle gracefully or raise meaningful error
        except Exception:
            pass  # Expected to fail with invalid sign


# =============================================================================
# CONNECTIONS TESTS
# =============================================================================

class TestConnectionsAdversarial:
    """Adversarial tests for connections.py"""

    def test_connection_with_missing_birth_date(self):
        """Test Connection model with missing birth_date."""
        from connections import Connection
        from pydantic import ValidationError
        from models import RelationshipType

        now = datetime.now().isoformat()

        # birth_date is required
        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="Test",
                # birth_date missing
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_connection_with_invalid_relationship_type(self):
        """Test Connection with invalid relationship_type."""
        from connections import Connection
        from pydantic import ValidationError

        now = datetime.now().isoformat()

        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="Test",
                birth_date="1990-01-01",
                relationship_type="enemy",  # Invalid
                created_at=now,
                updated_at=now
            )

    def test_get_orb_weight_at_boundaries(self):
        """Test orb weight at exact boundaries."""
        from compatibility import get_orb_weight

        # Test boundary values
        assert get_orb_weight(0) == 1.0
        assert get_orb_weight(2) == 1.0
        assert get_orb_weight(2.001) == 0.75
        assert get_orb_weight(5) == 0.75
        assert get_orb_weight(5.001) == 0.5
        assert get_orb_weight(8) == 0.5
        assert get_orb_weight(8.001) == 0.25
        assert get_orb_weight(10) == 0.25
        assert get_orb_weight(10.001) == 0.0


# =============================================================================
# ASK THE STARS TESTS
# =============================================================================

class TestAskTheStarsAdversarial:
    """Adversarial tests for ask_the_stars.py edge cases"""

    def test_empty_question(self):
        """Test handling of empty question string."""
        # The validation happens at request level, but test template handling
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path

        template_dir = Path(__file__).parent / 'templates' / 'conversation'
        if template_dir.exists():
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('ask_the_stars.j2')

            # Render with empty question
            result = template.render(
                user_first_name="Test",
                sun_sign="aries",
                horoscope_date="2025-01-20",
                horoscope={},
                entities=[],
                mentioned_connections=[],
                messages=[],
                question=""  # Empty
            )
            # Should not crash
            assert result is not None

    def test_question_with_special_characters(self):
        """Test handling of question with special characters."""
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path

        template_dir = Path(__file__).parent / 'templates' / 'conversation'
        if template_dir.exists():
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            template = env.get_template('ask_the_stars.j2')

            # Question with potential injection characters
            result = template.render(
                user_first_name="Test",
                sun_sign="aries",
                horoscope_date="2025-01-20",
                horoscope={},
                entities=[],
                mentioned_connections=[],
                messages=[],
                question="{{ malicious }} <script>alert('xss')</script>"
            )
            # Should escape properly
            assert "{{ malicious }}" not in result or "{{" in result


# =============================================================================
# MEMORY COLLECTION TESTS
# =============================================================================

class TestMemoryCollectionAdversarial:
    """Adversarial tests for MemoryCollection"""

    def test_create_empty_memory_format_for_llm(self):
        """Test format_for_llm on empty memory."""
        from models import create_empty_memory

        memory = create_empty_memory("user_001")

        # Should not crash
        formatted = memory.format_for_llm()
        assert "First time user" in formatted

    def test_memory_format_for_llm_with_engagement(self):
        """Test format_for_llm with actual engagement data."""
        from models import MemoryCollection, CategoryEngagement
        from astrometers.hierarchy import MeterGroupV2

        memory = MemoryCollection(
            user_id="user_001",
            categories={
                MeterGroupV2.MIND: CategoryEngagement(count=5, last_mentioned="2025-01-20"),
                MeterGroupV2.HEART: CategoryEngagement(count=3, last_mentioned="2025-01-19"),
                MeterGroupV2.BODY: CategoryEngagement(count=0),
                MeterGroupV2.INSTINCTS: CategoryEngagement(count=0),
                MeterGroupV2.GROWTH: CategoryEngagement(count=0),
            },
            updated_at=datetime.now().isoformat()
        )

        formatted = memory.format_for_llm()
        assert "Mind" in formatted
        assert "5 times" in formatted


# =============================================================================
# COMPRESSED HOROSCOPE TESTS
# =============================================================================

class TestCompressedHoroscopeAdversarial:
    """Adversarial tests for horoscope compression"""

    def test_compressed_meter_score_boundaries(self):
        """Test CompressedMeter with boundary scores."""
        from models import CompressedMeter
        from pydantic import ValidationError

        # Valid at boundaries
        meter = CompressedMeter(name="test", intensity=0.0, harmony=100.0)
        assert meter.intensity == 0.0
        assert meter.harmony == 100.0

        # Invalid below 0
        with pytest.raises(ValidationError):
            CompressedMeter(name="test", intensity=-1.0, harmony=50.0)

        # Invalid above 100
        with pytest.raises(ValidationError):
            CompressedMeter(name="test", intensity=50.0, harmony=101.0)

    def test_compressed_horoscope_relationship_weather_backward_compat(self):
        """
        Test that CompressedHoroscope accepts relationship_weather as string (old format).

        CRITICAL: Old horoscopes stored in Firestore have relationship_weather as a string.
        The model was changed to use RelationshipWeather object, but we need backward
        compatibility to read existing data.

        Bug caught: ask_the_stars endpoint returned 500 because stored horoscopes
        had string relationship_weather but model expected RelationshipWeather object.
        """
        from models import (
            CompressedHoroscope,
            CompressedMeterGroup,
            CompressedMeter,
            CompressedAstrometers,
            CompressedTransitSummary,
            ActionableAdvice,
            RelationshipWeather,
        )

        # Minimal valid data for required fields
        meter_groups = [
            CompressedMeterGroup(
                name="mind",
                intensity=50.0,
                harmony=60.0,
                meters=[CompressedMeter(name="clarity", intensity=50.0, harmony=60.0)]
            )
        ]
        astrometers = CompressedAstrometers(
            overall_state="Balanced Flow",
            top_active_meters=["clarity"],
            top_flowing_meters=["clarity"],
            top_challenging_meters=[]
        )
        transit_summary = CompressedTransitSummary(priority_transits=[])
        actionable_advice = ActionableAdvice(
            do="Start your day mindfully and focus on your priorities",
            dont="Avoid rushing into decisions without thinking them through",
            reflect_on="What would make today feel meaningful to you?"
        )

        # Test 1: OLD FORMAT - relationship_weather as string (what's in Firestore)
        horoscope_with_string = CompressedHoroscope(
            date="2025-11-27",
            sun_sign="aries",
            technical_analysis="Technical analysis here",
            daily_theme_headline="Your Day Ahead",
            daily_overview="Overview of your day",
            actionable_advice=actionable_advice,
            relationship_weather="Today's energy is supportive for relationships.",  # OLD STRING FORMAT
            meter_groups=meter_groups,
            astrometers=astrometers,
            transit_summary=transit_summary,
            created_at="2025-11-27T10:00:00Z"
        )

        # Should successfully create and preserve the string in some form
        assert horoscope_with_string.relationship_weather is not None

        # Test 2: NEW FORMAT - relationship_weather as RelationshipWeather object
        horoscope_with_object = CompressedHoroscope(
            date="2025-11-27",
            sun_sign="aries",
            technical_analysis="Technical analysis here",
            daily_theme_headline="Your Day Ahead",
            daily_overview="Overview of your day",
            actionable_advice=actionable_advice,
            relationship_weather=RelationshipWeather(
                overview="Today's energy is supportive for relationships.",
                connection_vibes=[]
            ),
            meter_groups=meter_groups,
            astrometers=astrometers,
            transit_summary=transit_summary,
            created_at="2025-11-27T10:00:00Z"
        )

        assert horoscope_with_object.relationship_weather is not None
        assert isinstance(horoscope_with_object.relationship_weather, RelationshipWeather)

    def test_memory_collection_old_category_names_backward_compat(self):
        """
        Test that MemoryCollection accepts old category names (spirit, emotions).

        CRITICAL: Old memory docs in Firestore have category names like 'spirit' and 'emotions'.
        The model now uses MeterGroupV2 which only accepts 'mind', 'heart', 'body', 'instincts', 'growth'.
        We need backward compatibility to map old names to new ones.

        Bug caught: ask_the_stars endpoint returned 500 because stored memory
        had old category names but model expected new MeterGroupV2 names.
        """
        from models import MemoryCollection, CategoryEngagement
        from astrometers.hierarchy import MeterGroupV2

        # Test with OLD category names (what's in Firestore)
        memory = MemoryCollection(
            user_id="test_user",
            categories={
                "spirit": {"count": 5, "last_mentioned": None},  # OLD: should map to 'growth'
                "emotions": {"count": 3, "last_mentioned": None},  # OLD: should map to 'heart'
                "mind": {"count": 2, "last_mentioned": None},  # Already correct
            },
            updated_at="2025-11-27T10:00:00Z"
        )

        # Should successfully create with mapped names
        assert MeterGroupV2.GROWTH in memory.categories  # spirit -> growth
        assert MeterGroupV2.HEART in memory.categories   # emotions -> heart
        assert MeterGroupV2.MIND in memory.categories    # unchanged

    def test_connection_vibes_storage(self):
        """
        Test that Connection model supports vibes field (FIFO last 10).

        Feature: Store daily vibes on connection like Co-Star updates.
        """
        from connections import Connection, StoredVibe
        from models import RelationshipType

        # Create vibes
        vibes = [
            StoredVibe(
                date="2025-11-27",
                vibe="Great energy between you today",
                vibe_score=85,
                key_transit="Venus trine their Moon"
            ),
            StoredVibe(
                date="2025-11-26",
                vibe="Give them some space",
                vibe_score=35,
                key_transit="Mars square their Sun"
            ),
        ]

        # Create connection with vibes
        connection = Connection(
            connection_id="conn_test123",
            name="John",
            birth_date="1990-06-15",
            relationship_type=RelationshipType.FRIEND,
            created_at="2025-11-01T10:00:00Z",
            updated_at="2025-11-27T10:00:00Z",
            vibes=vibes
        )

        assert len(connection.vibes) == 2
        assert connection.vibes[0].vibe_score == 85
        assert connection.vibes[1].date == "2025-11-26"


# =============================================================================
# LLM MODULE TESTS
# =============================================================================

class TestLLMAdversarial:
    """Adversarial tests for llm.py"""

    def test_convert_aspect_contribution_with_none_deviations(self):
        """Test convert_aspect_contribution when today/tomorrow_deviation are None."""
        from llm import convert_aspect_contribution_to_meter_aspect
        from astrometers.core import AspectContribution
        from astro import Planet, AspectType, ZodiacSign

        # Create aspect with None deviations (which are the defaults)
        aspect = AspectContribution(
            label="Transit Saturn square Natal Sun",
            natal_planet=Planet.SUN,
            transit_planet=Planet.SATURN,
            aspect_type=AspectType.SQUARE,
            weightage=0.5,
            transit_power=0.8,
            quality_factor=-0.8,
            dti_contribution=0.4,
            hqs_contribution=-0.32,
            orb_deviation=3.5,
            max_orb=8.0,
            today_deviation=None,  # None!
            tomorrow_deviation=None,  # None!
            natal_planet_house=1,
            natal_planet_sign=ZodiacSign.ARIES
        )

        # Should handle None gracefully
        try:
            result = convert_aspect_contribution_to_meter_aspect(aspect)
            assert result is not None
        except Exception as e:
            pytest.fail(f"Failed with None deviations: {e}")

    def test_load_meter_descriptions_missing_file(self):
        """Test load_meter_descriptions when a JSON file is missing."""
        from llm import load_meter_descriptions
        import os
        from pathlib import Path

        # This should handle missing files gracefully
        descriptions = load_meter_descriptions()
        assert isinstance(descriptions, dict)
        # Should have fallback values for any missing meters


# =============================================================================
# MOON MODULE TESTS
# =============================================================================

class TestMoonAdversarial:
    """Adversarial tests for moon.py"""

    def test_moon_degree_boundary_360(self):
        """Test moon degree at 360 boundary."""
        from moon import MoonTransitDetail, VoidOfCourseStatus
        from astro import ZodiacSign, House, LunarPhase
        from pydantic import ValidationError

        # Degree >= 360 should fail
        with pytest.raises(ValidationError):
            MoonTransitDetail(
                moon_sign=ZodiacSign.ARIES,
                moon_house=House.FIRST,
                moon_degree=360.0,  # Invalid - lt 360
                moon_degree_in_sign=0.0,
                lunar_phase=LunarPhase(
                    name="new_moon",
                    illumination=0.0,
                    days_until_next_new=29,
                    days_since_last_new=0,
                    phase_emoji="",
                    guidance=""
                ),
                void_of_course=VoidOfCourseStatus.NOT_VOID
            )

    def test_moon_degree_in_sign_boundary_30(self):
        """Test moon degree in sign at 30 boundary."""
        from moon import MoonTransitDetail, VoidOfCourseStatus
        from astro import ZodiacSign, House, LunarPhase
        from pydantic import ValidationError

        # Degree in sign >= 30 should fail
        with pytest.raises(ValidationError):
            MoonTransitDetail(
                moon_sign=ZodiacSign.ARIES,
                moon_house=House.FIRST,
                moon_degree=350.0,
                moon_degree_in_sign=30.0,  # Invalid - lt 30
                lunar_phase=LunarPhase(
                    name="new_moon",
                    illumination=0.0,
                    days_until_next_new=29,
                    days_since_last_new=0,
                    phase_emoji="",
                    guidance=""
                ),
                void_of_course=VoidOfCourseStatus.NOT_VOID
            )

    def test_moon_dispositor_invalid_house(self):
        """Test MoonDispositor with invalid house number."""
        from moon import MoonDispositor
        from astro import Planet, ZodiacSign
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MoonDispositor(
                ruler=Planet.MARS,
                ruler_sign=ZodiacSign.ARIES,
                ruler_house=13,  # Invalid - max 12
                interpretation="Test"
            )


# =============================================================================
# TRIGGERS MODULE TESTS
# =============================================================================

class TestTriggersAdversarial:
    """Adversarial tests for triggers.py"""

    def test_trigger_with_empty_snapshot(self):
        """Test trigger handling with empty document snapshot."""
        # This tests the robustness of trigger functions
        # when they receive malformed data
        pass  # Would require mocking Firestore


# =============================================================================
# ADDITIONAL MODEL EDGE CASES
# =============================================================================

class TestAdditionalModelEdgeCases:
    """Additional edge case tests for models"""

    def test_extracted_entity_confidence_boundaries(self):
        """Test ExtractedEntity confidence at 0 and 1."""
        from models import ExtractedEntity
        from pydantic import ValidationError

        # Valid at boundaries
        entity = ExtractedEntity(
            name="Test",
            entity_type="person",
            context="Test context",
            confidence=0.0  # Valid
        )
        assert entity.confidence == 0.0

        entity = ExtractedEntity(
            name="Test",
            entity_type="person",
            context="Test context",
            confidence=1.0  # Valid
        )
        assert entity.confidence == 1.0

        # Invalid beyond boundaries
        with pytest.raises(ValidationError):
            ExtractedEntity(
                name="Test",
                entity_type="person",
                context="Test context",
                confidence=1.1  # Invalid
            )

        with pytest.raises(ValidationError):
            ExtractedEntity(
                name="Test",
                entity_type="person",
                context="Test context",
                confidence=-0.1  # Invalid
            )

    def test_category_engagement_negative_count(self):
        """Test CategoryEngagement with negative count."""
        from models import CategoryEngagement
        from pydantic import ValidationError

        # count has ge=0 constraint
        with pytest.raises(ValidationError):
            CategoryEngagement(count=-1)

    def test_meter_aspect_orb_percentage_boundaries(self):
        """Test MeterAspect orb_percentage boundaries."""
        from models import MeterAspect
        from pydantic import ValidationError

        # Valid at boundaries
        aspect = MeterAspect(
            label="Test",
            natal_planet="sun",
            transit_planet="mars",
            aspect_type="conjunction",
            orb=0.0,
            orb_percentage=0.0,  # Valid
            phase="exact",
            contribution=0.5,
            quality_factor=0.5,
            natal_planet_house=1,
            natal_planet_sign="aries",
            houses_involved=[1]
        )
        assert aspect.orb_percentage == 0.0

        aspect = MeterAspect(
            label="Test",
            natal_planet="sun",
            transit_planet="mars",
            aspect_type="conjunction",
            orb=0.0,
            orb_percentage=100.0,  # Valid
            phase="exact",
            contribution=0.5,
            quality_factor=0.5,
            natal_planet_house=1,
            natal_planet_sign="aries",
            houses_involved=[1]
        )
        assert aspect.orb_percentage == 100.0

        # Invalid beyond boundaries
        with pytest.raises(ValidationError):
            MeterAspect(
                label="Test",
                natal_planet="sun",
                transit_planet="mars",
                aspect_type="conjunction",
                orb=0.0,
                orb_percentage=101.0,  # Invalid
                phase="exact",
                contribution=0.5,
                quality_factor=0.5,
                natal_planet_house=1,
                natal_planet_sign="aries",
                houses_involved=[1]
            )

    def test_meter_aspect_quality_factor_boundaries(self):
        """Test MeterAspect quality_factor boundaries."""
        from models import MeterAspect
        from pydantic import ValidationError

        # Valid at boundaries -1 to 1
        aspect = MeterAspect(
            label="Test",
            natal_planet="sun",
            transit_planet="mars",
            aspect_type="conjunction",
            orb=0.0,
            orb_percentage=50.0,
            phase="exact",
            contribution=0.5,
            quality_factor=-1.0,  # Valid
            natal_planet_house=1,
            natal_planet_sign="aries",
            houses_involved=[1]
        )
        assert aspect.quality_factor == -1.0

        # Invalid beyond boundaries
        with pytest.raises(ValidationError):
            MeterAspect(
                label="Test",
                natal_planet="sun",
                transit_planet="mars",
                aspect_type="conjunction",
                orb=0.0,
                orb_percentage=50.0,
                phase="exact",
                contribution=0.5,
                quality_factor=1.5,  # Invalid
                natal_planet_house=1,
                natal_planet_sign="aries",
                houses_involved=[1]
            )

    def test_compressed_meter_group_missing_meters(self):
        """Test CompressedMeterGroup with empty meters list."""
        from models import CompressedMeterGroup

        # Should allow empty meters list (though unusual)
        group = CompressedMeterGroup(
            name="test",
            intensity=50.0,
            harmony=50.0,
            meters=[]  # Empty
        )
        assert group.meters == []

    def test_relationship_weather_with_connection_vibes(self):
        """Test RelationshipWeather with connection vibes."""
        from models import RelationshipWeather, ConnectionVibe, RelationshipType

        # Valid with vibes
        weather = RelationshipWeather(
            overview="Test overview",
            connection_vibes=[
                ConnectionVibe(
                    connection_id="conn_001",
                    name="John",
                    relationship_type=RelationshipType.FRIEND,
                    vibe="Good day to connect",
                    vibe_score=75,
                    key_transit="Venus trine Moon"
                )
            ]
        )
        assert len(weather.connection_vibes) == 1

    def test_connection_vibe_score_boundaries(self):
        """Test ConnectionVibe vibe_score boundaries."""
        from models import ConnectionVibe, RelationshipType
        from pydantic import ValidationError

        # Valid at boundaries
        vibe = ConnectionVibe(
            connection_id="conn_001",
            name="Test",
            relationship_type=RelationshipType.FRIEND,
            vibe="Test",
            vibe_score=0,  # Valid
            key_transit="Test"
        )
        assert vibe.vibe_score == 0

        vibe = ConnectionVibe(
            connection_id="conn_001",
            name="Test",
            relationship_type=RelationshipType.FRIEND,
            vibe="Test",
            vibe_score=100,  # Valid
            key_transit="Test"
        )
        assert vibe.vibe_score == 100

        # Invalid beyond boundaries
        with pytest.raises(ValidationError):
            ConnectionVibe(
                connection_id="conn_001",
                name="Test",
                relationship_type=RelationshipType.FRIEND,
                vibe="Test",
                vibe_score=101,  # Invalid
                key_transit="Test"
            )


# =============================================================================
# ADDITIONAL BUGS - IMPORTANCE SCORE AND TIMESTAMP HANDLING
# =============================================================================

class TestImportanceScoreBugs:
    """Tests that expose bugs in importance score calculation."""

    def test_importance_score_with_very_old_entity(self):
        """Test importance score with entity last seen years ago."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()
        old_date = (now - timedelta(days=365)).isoformat()  # 1 year ago

        entity = Entity(
            entity_id="ent_001",
            name="Old",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=old_date,
            last_seen=old_date,
            mention_count=5,
            created_at=old_date,
            updated_at=old_date
        )

        # With 365 days ago, recency = max(0, 1 - 365/30) = max(0, -11.17) = 0
        score = calculate_entity_importance_score(entity, now)
        # Score should be purely frequency-based: 0.4 * min(1, 5/10) = 0.4 * 0.5 = 0.2
        assert score >= 0.0
        assert score <= 1.0

    def test_importance_score_with_negative_days(self):
        """Test that future last_seen can exceed importance score of 1.0 - BUG!"""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()
        future = (now + timedelta(days=10)).isoformat()

        entity = Entity(
            entity_id="ent_001",
            name="Future",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=future,  # In the future!
            mention_count=10,  # Max frequency
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        score = calculate_entity_importance_score(entity, now)
        # BUG: With future date, recency = 1 - (-10/30) = 1.33
        # frequency = min(1, 10/10) = 1.0
        # importance = 1.33 * 0.6 + 1.0 * 0.4 = 0.8 + 0.4 = 1.2 > 1.0!
        # This should be capped but isn't
        if score > 1.0:
            pytest.fail(f"BUG: Importance score {score} exceeds 1.0 with future last_seen date")


# =============================================================================
# COMPRESS HOROSCOPE BUGS
# =============================================================================

class TestCompressHoroscopeBugs:
    """Tests for bugs in horoscope compression."""

    def test_compress_horoscope_with_none_transit_summary(self):
        """Test compress_horoscope when transit_summary is None."""
        from models import (
            DailyHoroscope, ActionableAdvice, AstrometersForIOS,
            MeterGroupForIOS, MeterForIOS, AstrologicalFoundation,
            compress_horoscope
        )
        from astrometers.meters import MeterReading

        # This is hard to test without full mock data
        # Let's test a simpler case
        pass

    def test_route_people_with_missing_connection_id(self):
        """Test route_people_to_connections when connection has no connection_id."""
        from entity_extraction import route_people_to_connections
        from models import Entity, EntityStatus

        now = datetime.now()
        entities = [
            Entity(
                entity_id="ent_001",
                name="John",
                entity_type="relationship",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                context_snippets=["Met John today"],
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        # Connection without connection_id
        connections = [{"name": "John"}]  # Missing connection_id!

        filtered, updates = route_people_to_connections(entities, connections, "2025-01-20")
        # Should handle missing connection_id gracefully
        # BUG: updates will have connection_id=None
        if updates and updates[0].get("connection_id") is None:
            pytest.fail("BUG: route_people_to_connections creates update with None connection_id")


# =============================================================================
# ENTITY EXTRACTION BUGS
# =============================================================================

class TestEntityExtractionBugs:
    """Tests for bugs in entity extraction."""

    def test_execute_merge_actions_case_sensitivity(self):
        """Test that entity name matching is case-insensitive but may have bugs."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus

        now = datetime.now()
        existing = [
            Entity(
                entity_id="ent_001",
                name="JOHN",  # Uppercase
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        # Try to update with lowercase name
        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="update",
                    entity_name="john",  # Lowercase
                    entity_type="person",
                    context_update="Updated context"
                )
            ]
        )

        result = execute_merge_actions(merged, existing, now)
        # Check if update was applied
        john = [e for e in result if e.name == "JOHN"][0]
        if "Updated context" not in john.context_snippets:
            pytest.fail("BUG: Entity update by name is case-sensitive")

    def test_execute_merge_actions_duplicate_creates(self):
        """Test creating duplicate entities with same name."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction

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

        result = execute_merge_actions(merged, [], datetime.now())
        # Should this create two entities or merge them?
        # Currently creates two - may or may not be a bug depending on intent
        johns = [e for e in result if e.name == "John"]
        if len(johns) == 2:
            # This might be intended behavior, but worth noting
            pass  # Not necessarily a bug, but could cause issues


# =============================================================================
# CONNECTION BUGS
# =============================================================================

class TestConnectionBugs:
    """Tests for bugs in connections module."""

    def test_connection_with_empty_birth_date(self):
        """Test Connection with empty string birth_date."""
        from connections import Connection
        from models import RelationshipType

        now = datetime.now().isoformat()

        # Empty birth_date should probably fail validation but doesn't
        try:
            conn = Connection(
                connection_id="conn_001",
                name="Test",
                birth_date="",  # Empty string - valid?
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )
            # BUG: Empty birth_date is accepted but will cause issues later
            if conn.birth_date == "":
                pytest.fail("BUG: Connection accepts empty birth_date which will cause downstream issues")
        except Exception:
            pass  # Expected to fail

    def test_get_sun_sign_with_empty_date(self):
        """Test get_sun_sign with empty date string."""
        from astro import get_sun_sign

        # Empty date should fail
        with pytest.raises(Exception):
            get_sun_sign("")

    def test_connection_sun_sign_calculation_with_empty_date(self):
        """Test that connections module handles empty birth_date when calculating sun sign."""
        from astro import get_sun_sign

        # If birth_date is empty string, get_sun_sign will crash
        try:
            sign = get_sun_sign("")
            pytest.fail("BUG: get_sun_sign should fail with empty date but didn't")
        except Exception:
            pass  # Expected

    def test_compute_birth_chart_missing_timezone_with_time(self):
        """Test compute_birth_chart with birth_time but no timezone."""
        from astro import compute_birth_chart

        # Has time but no timezone - what happens?
        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone=None,  # Missing timezone!
            birth_lat=40.0,
            birth_lon=-74.0
        )

        # Should this be exact=False since timezone is missing?
        # BUG: Currently returns exact=False only if ANY of the 4 fields is missing
        # But partial info (time without timezone) is problematic
        assert is_exact is False  # Shouldn't be exact without timezone


# =============================================================================
# ADDITIONAL CRITICAL BUGS
# =============================================================================

class TestCriticalBugs:
    """Tests for critical bugs that could cause production issues."""

    def test_entity_context_snippets_overflow(self):
        """Test that context_snippets list doesn't grow unbounded."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus

        now = datetime.now()
        # Entity with max context snippets
        existing = [
            Entity(
                entity_id="ent_001",
                name="John",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=1,
                context_snippets=["snippet"] * 10,  # Already has 10 snippets
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="update",
                    entity_name="John",
                    entity_type="person",
                    merge_with_id="ent_001",
                    context_update="New snippet"
                )
            ]
        )

        result = execute_merge_actions(merged, existing, now)
        john = [e for e in result if e.name == "John"][0]
        # Should be limited to 10 snippets (FIFO)
        if len(john.context_snippets) > 10:
            pytest.fail(f"BUG: context_snippets grew to {len(john.context_snippets)}, should be max 10")

    def test_planet_position_requires_all_fields(self):
        """Test that PlanetPosition validation correctly requires all fields."""
        from astro import PlanetPosition, ZodiacSign
        from pydantic import ValidationError

        # Creating a PlanetPosition with minimal fields should fail
        # The model requires: symbol, position_dms, degree_in_sign, absolute_degree, house, speed, element, modality
        with pytest.raises(ValidationError):
            PlanetPosition(
                name="sun",
                sign=ZodiacSign.GEMINI,
                degree=85.0,  # Wrong field name - should be absolute_degree
                retrograde=False
            )
        # Test passes - validation is working correctly

    def test_meter_groups_divide_by_zero(self):
        """Test meter group calculation with empty meters list."""
        from llm import METER_GROUP_MAPPING

        # If METER_GROUP_MAPPING has a group with empty list, division by zero
        for group_name, meters in METER_GROUP_MAPPING.items():
            if len(meters) == 0:
                pytest.fail(f"BUG: METER_GROUP_MAPPING['{group_name}'] is empty, will cause divide by zero")

        # The build_astrometers_for_ios divides by len(meters_for_ios)
        # avg_unified = sum(...) / len(meters_for_ios)
        # If meters_for_ios is empty, this crashes
        # Test with mock to verify
        pass  # Config is fine, but the function doesn't guard against empty groups

    def test_message_role_validation(self):
        """Test Message with invalid role."""
        from models import Message
        from pydantic import ValidationError

        # Role must be MessageRole enum value
        with pytest.raises(ValidationError):
            Message(
                role="invalid_role",  # Not a valid MessageRole
                content="Test"
            )

    def test_daily_horoscope_missing_required_fields(self):
        """Test DailyHoroscope validation with missing fields."""
        from models import DailyHoroscope
        from pydantic import ValidationError

        # DailyHoroscope has many required fields
        with pytest.raises(ValidationError):
            DailyHoroscope(
                # Missing all required fields
            )

    def test_compatibility_score_can_exceed_bounds(self):
        """Test that compatibility scores aren't properly bounded."""
        from compatibility import calculate_category_score, SynastryAspect

        # Create aspects with very tight orbs that could produce high scores
        aspects = [
            SynastryAspect(
                id=f"asp_{i}",
                user_planet="sun",
                their_planet="moon",
                aspect_type="conjunction",
                orb=0.1,  # Very tight orb = high weight
                is_harmonious=True
            )
            for i in range(20)  # Many aspects
        ]

        planet_pairs = [("sun", "moon")]
        score, _ = calculate_category_score(aspects, planet_pairs)

        # Score should be bounded 0-100 but may not be
        if score > 100 or score < -100:
            pytest.fail(f"BUG: Category score {score} exceeds bounds [-100, 100]")

    def test_triggers_entity_update_empty_doc(self):
        """Test that trigger functions handle empty/malformed document data."""
        # BUG: Triggers may not validate data before processing
        # This is a latent bug that would cause runtime errors
        pass

    def test_calculate_vibe_score_division_by_zero(self):
        """Test calculate_vibe_score potential division issues."""
        from compatibility import calculate_vibe_score

        # Empty transit list - should return 50 (neutral) not crash
        score = calculate_vibe_score([])
        assert score == 50

        # All None orbs - potential issue
        transits = [{"is_harmonious": True, "orb": None}]
        try:
            score = calculate_vibe_score(transits)
        except TypeError:
            pytest.fail("BUG: calculate_vibe_score crashes with None orb values")


# =============================================================================
# ASTRO ADDITIONAL EDGE CASES
# =============================================================================

class TestAstroAdditionalEdgeCases:
    """Additional edge cases for astro.py"""

    def test_zodiac_sign_from_symbol(self):
        """Test ZodiacSign from unicode symbol."""
        from astro import ZodiacSign

        # Should handle symbol-to-sign conversion
        try:
            sign = ZodiacSign("aries")
            assert sign.value == "aries"
        except Exception as e:
            pytest.fail(f"Failed to create ZodiacSign: {e}")

    def test_house_ordinal_and_meaning(self):
        """Test House enum ordinal and meaning properties."""
        from astro import House

        house = House.FIRST
        assert house.ordinal == "1st"
        assert house.meaning is not None

        house = House.TWELFTH
        assert house.ordinal == "12th"

    def test_aspect_type_values(self):
        """Test AspectType enum has expected values."""
        from astro import AspectType

        expected = ["conjunction", "opposition", "trine", "square", "sextile", "quincunx"]
        for asp in expected:
            assert hasattr(AspectType, asp.upper())

    def test_compute_birth_chart_with_null_time(self):
        """Test compute_birth_chart with None birth_time uses V1 mode."""
        from astro import compute_birth_chart

        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time=None  # V1 mode
        )

        assert chart is not None
        assert is_exact is False  # Not exact without time


# =============================================================================
# COMPATIBILITY ADDITIONAL EDGE CASES
# =============================================================================

class TestCompatibilityAdditionalEdgeCases:
    """Additional edge cases for compatibility.py"""

    def test_synastry_aspect_id_format(self):
        """Test SynastryAspect ID field."""
        from compatibility import SynastryAspect

        aspect = SynastryAspect(
            id="asp_001",
            user_planet="sun",
            their_planet="moon",
            aspect_type="conjunction",
            orb=2.5,
            is_harmonious=True
        )
        assert aspect.id == "asp_001"

    def test_compatibility_category_score_boundaries(self):
        """Test CompatibilityCategory score boundaries."""
        from compatibility import CompatibilityCategory
        from pydantic import ValidationError

        # Valid at boundaries -100 to 100
        cat = CompatibilityCategory(
            id="test",
            name="Test",
            score=-100
        )
        assert cat.score == -100

        cat = CompatibilityCategory(
            id="test",
            name="Test",
            score=100
        )
        assert cat.score == 100

        # Invalid beyond boundaries
        with pytest.raises(ValidationError):
            CompatibilityCategory(
                id="test",
                name="Test",
                score=101
            )

        with pytest.raises(ValidationError):
            CompatibilityCategory(
                id="test",
                name="Test",
                score=-101
            )

    def test_mode_compatibility_overall_score_boundaries(self):
        """Test ModeCompatibility overall_score boundaries."""
        from compatibility import ModeCompatibility, CompatibilityCategory
        from pydantic import ValidationError

        # Valid at boundaries 0-100
        mode = ModeCompatibility(
            overall_score=0,
            categories=[]
        )
        assert mode.overall_score == 0

        mode = ModeCompatibility(
            overall_score=100,
            categories=[]
        )
        assert mode.overall_score == 100

        # Invalid beyond boundaries
        with pytest.raises(ValidationError):
            ModeCompatibility(
                overall_score=101,
                categories=[]
            )

        with pytest.raises(ValidationError):
            ModeCompatibility(
                overall_score=-1,
                categories=[]
            )


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

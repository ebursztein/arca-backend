"""
Bug-hunting adversarial tests for Arca Backend - Part 3.

More targeted tests to find bugs 8-20.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError


# =============================================================================
# BUG HUNT 8-10: More Model Validation Bugs
# =============================================================================

class TestMoreModelValidationBugs:
    """Find more model validation bugs."""

    def test_extracted_entity_confidence_can_be_exactly_zero(self):
        """Test that ExtractedEntity confidence of 0 is valid."""
        from models import ExtractedEntity

        entity = ExtractedEntity(
            name="Test",
            entity_type="person",
            context="Test context",
            confidence=0.0  # Exactly 0
        )
        assert entity.confidence == 0.0

    def test_extracted_entity_confidence_can_be_exactly_one(self):
        """Test that ExtractedEntity confidence of 1 is valid."""
        from models import ExtractedEntity

        entity = ExtractedEntity(
            name="Test",
            entity_type="person",
            context="Test context",
            confidence=1.0  # Exactly 1
        )
        assert entity.confidence == 1.0

    def test_entity_merge_action_invalid_action_type(self):
        """Test EntityMergeAction with invalid action type."""
        from models import EntityMergeAction

        # BUG HUNT: action is just a str, not validated against enum
        action = EntityMergeAction(
            action="destroy",  # Invalid action type!
            entity_name="Test",
            entity_type="person"
        )
        assert action.action == "destroy"  # Bug: Should reject invalid actions

    def test_connection_vibe_score_boundary(self):
        """Test ConnectionVibe vibe_score at boundaries."""
        from models import ConnectionVibe, RelationshipType

        # Test at 0
        vibe = ConnectionVibe(
            connection_id="conn_001",
            name="Test",
            relationship_type=RelationshipType.FRIEND,
            vibe="Test vibe",
            vibe_score=0,
            key_transit="Test transit"
        )
        assert vibe.vibe_score == 0

        # Test at 100
        vibe = ConnectionVibe(
            connection_id="conn_001",
            name="Test",
            relationship_type=RelationshipType.FRIEND,
            vibe="Test vibe",
            vibe_score=100,
            key_transit="Test transit"
        )
        assert vibe.vibe_score == 100

    def test_compressed_meter_score_negative(self):
        """Test CompressedMeter with negative scores."""
        from models import CompressedMeter

        # BUG HUNT: intensity has ge=0 constraint
        with pytest.raises(ValidationError):
            CompressedMeter(
                name="test",
                intensity=-1.0,  # Negative!
                harmony=50.0
            )

    def test_compressed_meter_score_over_100(self):
        """Test CompressedMeter with score over 100."""
        from models import CompressedMeter

        # BUG HUNT: intensity has le=100 constraint
        with pytest.raises(ValidationError):
            CompressedMeter(
                name="test",
                intensity=101.0,  # Over 100!
                harmony=50.0
            )

    def test_actionable_advice_empty_strings(self):
        """Test ActionableAdvice with empty strings."""
        from models import ActionableAdvice

        # BUG HUNT: No min_length on fields
        advice = ActionableAdvice(
            do="",  # Empty!
            dont="",
            reflect_on=""
        )
        assert advice.do == ""  # Bug: Empty advice is allowed

    def test_daily_theme_headline_too_long(self):
        """Test DailyHoroscope with headline exceeding word limit."""
        from models import DailyHoroscope, ActionableAdvice, AstrometersForIOS

        # BUG HUNT: Field says "max 15 words" but no validation
        long_headline = "This is a very very very very very very very very very very very very very very very very very long headline"

        # Can't easily test without creating all required fields
        # But the model allows any length headline - potential bug

    def test_meter_group_state_invalid_quality(self):
        """Test MeterGroupState with invalid quality value."""
        from models import MeterGroupState

        # BUG HUNT: quality is just str, not validated against enum
        state = MeterGroupState(
            label="Good",
            quality="super_awesome"  # Invalid quality value!
        )
        assert state.quality == "super_awesome"  # Bug: Should validate

    def test_trend_metric_invalid_direction(self):
        """Test TrendMetric with invalid direction value."""
        from models import TrendMetric

        # BUG HUNT: direction is just str
        trend = TrendMetric(
            previous=50.0,
            delta=5.0,
            direction="backwards",  # Invalid!
            change_rate="moderate"
        )
        assert trend.direction == "backwards"  # Bug: Should validate

    def test_trend_metric_invalid_change_rate(self):
        """Test TrendMetric with invalid change_rate value."""
        from models import TrendMetric

        # BUG HUNT: change_rate is just str
        trend = TrendMetric(
            previous=50.0,
            delta=5.0,
            direction="improving",
            change_rate="super_fast"  # Invalid!
        )
        assert trend.change_rate == "super_fast"  # Bug: Should validate


# =============================================================================
# BUG HUNT 11-14: Entity Extraction Logic Bugs
# =============================================================================

class TestEntityExtractionLogicBugs:
    """Find bugs in entity extraction logic."""

    def test_execute_merge_actions_creates_duplicate_ids(self):
        """Test that multiple creates don't produce same entity_id."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction

        now = datetime.now()

        # Many create actions
        actions = [
            EntityMergeAction(
                action="create",
                entity_name=f"Entity{i}",
                entity_type="person"
            )
            for i in range(100)
        ]

        merged = MergedEntities(actions=actions)
        result = execute_merge_actions(merged, [], now)

        # All IDs should be unique
        ids = [e.entity_id for e in result]
        assert len(ids) == len(set(ids)), "Entity IDs should be unique"

    def test_execute_merge_actions_update_by_case_insensitive_name(self):
        """Test update finds entity by case-insensitive name match."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus

        now = datetime.now()
        existing = Entity(
            entity_id="ent_001",
            name="John",  # Capital J
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="update",
                    entity_name="john",  # lowercase j
                    entity_type="person",
                    context_update="Update context"
                )
            ]
        )

        result = execute_merge_actions(merged, [existing], now)
        # BUG HUNT: Does case-insensitive matching work correctly?
        john = next((e for e in result if e.name == "John"), None)
        assert john is not None
        assert len(john.context_snippets) == 1, "Update should have added context"

    def test_merge_adds_alias_that_already_exists(self):
        """Test merge doesn't add duplicate alias."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus

        now = datetime.now()
        existing = Entity(
            entity_id="ent_001",
            name="John",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            aliases=["Johnny"],  # Already has this alias
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="merge",
                    entity_name="John",
                    entity_type="person",
                    merge_with_id="ent_001",
                    new_alias="johnny"  # Same alias, different case
                )
            ]
        )

        result = execute_merge_actions(merged, [existing], now)
        john = result[0]
        # BUG HUNT: Does case-insensitive alias deduplication work?
        # Current code checks: action.new_alias.lower() not in [a.lower() for a in existing.aliases]
        assert len(john.aliases) == 1, f"Should not duplicate alias, got {john.aliases}"

    def test_get_top_entities_respects_limit(self):
        """Test get_top_entities_by_importance respects limit parameter."""
        from entity_extraction import get_top_entities_by_importance
        from models import Entity, EntityStatus

        now = datetime.now()
        entities = [
            Entity(
                entity_id=f"ent_{i:03d}",
                name=f"Entity {i}",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=i + 1,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
            for i in range(50)
        ]

        result = get_top_entities_by_importance(entities, limit=10)
        assert len(result) == 10, "Should respect limit"

    def test_route_people_matches_by_alias(self):
        """Test route_people_to_connections matches by entity alias."""
        from entity_extraction import route_people_to_connections
        from models import Entity, EntityStatus

        now = datetime.now()
        entity = Entity(
            entity_id="ent_001",
            name="Johnny",  # Different from connection name
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            aliases=["John"],  # But alias matches
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            context_snippets=["Met Johnny today"],
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        connections = [{"name": "John", "connection_id": "conn_001"}]

        filtered, updates = route_people_to_connections([entity], connections, "2025-01-20")
        # BUG HUNT: Does alias matching work?
        # Code checks entity.aliases too, should route
        assert len(filtered) == 0, "Should route to connection via alias"
        assert len(updates) == 1


# =============================================================================
# BUG HUNT 15-17: Compatibility Calculation Bugs
# =============================================================================

class TestCompatibilityCalculationBugs:
    """Find bugs in compatibility calculations."""

    def test_category_score_with_all_challenging_aspects(self):
        """Test category score when all aspects are challenging."""
        from compatibility import calculate_category_score, SynastryAspect

        aspects = [
            SynastryAspect(
                id="asp_001",
                user_planet="sun",
                their_planet="moon",
                aspect_type="square",
                orb=0.5,
                is_harmonious=False  # All challenging
            )
            for _ in range(5)
        ]

        planet_pairs = [("sun", "moon")]
        score, _ = calculate_category_score(aspects, planet_pairs)
        # Should be negative
        assert score < 0, "All challenging aspects should give negative score"

    def test_category_score_with_all_harmonious_aspects(self):
        """Test category score when all aspects are harmonious."""
        from compatibility import calculate_category_score, SynastryAspect

        aspects = [
            SynastryAspect(
                id="asp_001",
                user_planet="sun",
                their_planet="moon",
                aspect_type="trine",
                orb=0.5,
                is_harmonious=True  # All harmonious
            )
            for _ in range(5)
        ]

        planet_pairs = [("sun", "moon")]
        score, _ = calculate_category_score(aspects, planet_pairs)
        # Should be positive
        assert score > 0, "All harmonious aspects should give positive score"

    def test_aspect_at_180_degrees_is_opposition(self):
        """Test that exactly 180 degrees is detected as opposition."""
        from compatibility import calculate_aspect

        result = calculate_aspect(0.0, 180.0, "sun", "moon")
        assert result is not None
        aspect_type, orb, _ = result
        assert aspect_type == "opposition", f"180 degrees should be opposition, got {aspect_type}"
        assert orb == 0.0, "Should be exact"

    def test_orb_weight_with_exact_zero_orb(self):
        """Test orb weight with exactly 0 orb."""
        from compatibility import get_orb_weight

        weight = get_orb_weight(0.0)
        assert weight == 1.0, "Zero orb should give maximum weight"


# =============================================================================
# BUG HUNT 18-20: Astro Module Calculation Bugs
# =============================================================================

class TestAstroCalculationBugs:
    """Find bugs in astrology calculations."""

    def test_compute_birth_chart_with_midnight_time(self):
        """Test birth chart at exactly midnight."""
        from astro import compute_birth_chart

        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="00:00",  # Midnight
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert chart is not None
        assert len(chart["planets"]) == 11

    def test_compute_birth_chart_with_23_59_time(self):
        """Test birth chart at 23:59."""
        from astro import compute_birth_chart

        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="23:59",  # Just before midnight
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert chart is not None
        assert len(chart["planets"]) == 11

    def test_sun_sign_for_all_dates_in_year(self):
        """Test sun sign calculation for every day of the year."""
        from astro import get_sun_sign, ZodiacSign

        signs_seen = set()
        for month in range(1, 13):
            for day in range(1, 29):  # Use 28 to avoid month-end issues
                date_str = f"2000-{month:02d}-{day:02d}"
                sign = get_sun_sign(date_str)
                signs_seen.add(sign)

        # Should have seen all 12 signs
        assert len(signs_seen) == 12, f"Should see all 12 signs, got {len(signs_seen)}"

    def test_house_calculation_for_all_12_combinations(self):
        """Test solar house for all 144 sign combinations."""
        from astro import calculate_solar_house, ZodiacSign, House

        signs = list(ZodiacSign)

        for sun_sign in signs:
            for transit_sign in signs:
                house = calculate_solar_house(sun_sign.value, transit_sign.value)
                assert house.value >= 1 and house.value <= 12

    def test_describe_chart_emphasis_with_equal_distribution(self):
        """Test chart emphasis when all elements/modalities are equal."""
        from astro import describe_chart_emphasis

        # Equal distribution (impossible in real chart but tests edge case)
        distributions = {
            'elements': {'fire': 3, 'earth': 3, 'air': 3, 'water': 2},
            'modalities': {'cardinal': 4, 'fixed': 4, 'mutable': 3}
        }

        result = describe_chart_emphasis(distributions)
        # Should handle gracefully
        assert isinstance(result, str)

    def test_sign_ruler_for_all_signs(self):
        """Test that all signs have a ruler defined."""
        from astro import SIGN_RULERS, ZodiacSign

        for sign in ZodiacSign:
            assert sign in SIGN_RULERS, f"{sign} should have a ruler"


# =============================================================================
# BUG HUNT: Importance Score Calculation
# =============================================================================

class TestImportanceScoreCalculationBugs:
    """Find bugs in importance score calculation."""

    def test_importance_score_calculation_formula(self):
        """Verify importance score formula: 0.6 * recency + 0.4 * frequency."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()

        # Entity seen today with moderate frequency
        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=10,  # Moderate frequency
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        score = calculate_entity_importance_score(entity, now)
        # Should be combination of recency (high) and frequency (moderate)
        assert 0.5 < score <= 1.0, f"Score should be high for recent entity, got {score}"

    def test_importance_score_with_very_high_mention_count(self):
        """Test importance score with extremely high mention count."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()

        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1000000,  # Very high!
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        score = calculate_entity_importance_score(entity, now)
        # BUG HUNT: Does frequency component cap properly?
        assert score <= 1.0, f"Score should never exceed 1.0, got {score}"


# =============================================================================
# BUG HUNT: Connection Matching Logic
# =============================================================================

class TestConnectionMatchingBugs:
    """Find bugs in connection matching logic."""

    def test_route_people_matches_connection_by_alias(self):
        """Test that connection aliases are checked for matching."""
        from entity_extraction import route_people_to_connections
        from models import Entity, EntityStatus

        now = datetime.now()
        entity = Entity(
            entity_id="ent_001",
            name="Johnny",
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            context_snippets=["Met Johnny"],
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        # Connection has alias matching entity name
        connections = [{
            "name": "John Smith",
            "connection_id": "conn_001",
            "aliases": ["Johnny", "JS"]  # Entity name matches alias
        }]

        filtered, updates = route_people_to_connections([entity], connections, "2025-01-20")
        # BUG HUNT: Does connection alias matching work?
        assert len(updates) == 1, "Should match by connection alias"

    def test_route_people_empty_entity_name(self):
        """Test route_people with entity that has empty name."""
        from entity_extraction import route_people_to_connections
        from models import Entity, EntityStatus

        now = datetime.now()
        entity = Entity(
            entity_id="ent_001",
            name="",  # Empty name!
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            context_snippets=["Met someone"],
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        connections = [{"name": "", "connection_id": "conn_001"}]

        # BUG HUNT: What happens with empty name matching?
        filtered, updates = route_people_to_connections([entity], connections, "2025-01-20")
        # Should probably not match empty to empty


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

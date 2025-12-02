"""
Bug-hunting adversarial tests for Arca Backend.

Tests designed to find bugs by probing edge cases, boundary conditions,
and unexpected input combinations.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal


# =============================================================================
# BUG HUNT 1: Compatibility Module Edge Cases
# =============================================================================

class TestCompatibilityBugHunt:
    """Probe compatibility.py for bugs."""

    def test_calculate_aspect_at_exactly_0_degrees(self):
        """Test aspect calculation when both planets are at exactly 0 degrees."""
        from compatibility import calculate_aspect

        # Both planets at 0 degrees - should be exact conjunction
        result = calculate_aspect(0.0, 0.0, "sun", "moon")
        assert result is not None, "Should detect conjunction at 0 degrees"
        aspect_type, orb, is_harmonious = result
        assert aspect_type == "conjunction"
        assert orb == 0.0

    def test_calculate_aspect_at_exactly_360_degrees(self):
        """Test aspect when one planet is at 360 degrees (should wrap to 0)."""
        from compatibility import calculate_aspect

        # 360 is effectively 0 - should be conjunction with 0
        result = calculate_aspect(360.0, 0.0, "sun", "moon")
        # BUG HUNT: Does the code handle 360 degree input?
        assert result is not None, "Should handle 360 degrees"

    def test_calculate_aspect_negative_degree(self):
        """Test aspect calculation with negative degree input."""
        from compatibility import calculate_aspect

        # BUG HUNT: What happens with negative degrees?
        result = calculate_aspect(-10.0, 350.0, "sun", "moon")
        # -10 is effectively 350, so this should be conjunction with 350
        # Expected: either handle gracefully or we find a bug

    def test_get_orb_weight_exactly_at_boundaries(self):
        """Test orb weight at exact boundary values."""
        from compatibility import get_orb_weight

        # Test exact boundary values
        assert get_orb_weight(2.0) == 1.0, "Orb of exactly 2 should give weight 1.0"
        assert get_orb_weight(5.0) == 0.75, "Orb of exactly 5 should give weight 0.75"
        assert get_orb_weight(8.0) == 0.5, "Orb of exactly 8 should give weight 0.5"
        assert get_orb_weight(10.0) == 0.25, "Orb of exactly 10 should give weight 0.25"

    def test_get_orb_weight_above_10(self):
        """Test orb weight for orbs > 10."""
        from compatibility import get_orb_weight

        assert get_orb_weight(10.01) == 0.0, "Orb > 10 should give weight 0.0"
        assert get_orb_weight(100.0) == 0.0

    def test_calculate_composite_sign_wraparound(self):
        """Test composite sign calculation with wraparound (e.g., 350 and 10)."""
        from compatibility import calculate_composite_sign

        # 350 and 10 should give midpoint at 0 (Aries), not 180 (Libra)
        sign = calculate_composite_sign(350.0, 10.0)
        # The midpoint should be at 0/360, which is Aries
        assert sign == "aries", f"Wraparound midpoint should be aries, got {sign}"

    def test_calculate_composite_sign_at_sign_boundary(self):
        """Test composite sign at exact sign boundary (30, 60, etc.)."""
        from compatibility import calculate_composite_sign

        # Exactly at 30 degrees - boundary between Aries and Taurus
        sign = calculate_composite_sign(30.0, 30.0)
        # BUG HUNT: Does it give Taurus (30/30=1) or Aries?
        # 30/30 = 1, signs[1] = "taurus"
        assert sign == "taurus", f"30 degrees should be taurus, got {sign}"

    def test_calculate_vibe_score_with_negative_orb(self):
        """Test vibe score when transit has negative orb (invalid)."""
        from compatibility import calculate_vibe_score

        # BUG HUNT: What happens with negative orb?
        transits = [{"orb": -1.0, "is_harmonious": True}]
        score = calculate_vibe_score(transits)
        # Should handle gracefully, not crash

    def test_calculate_vibe_score_with_very_large_orb(self):
        """Test vibe score with extremely large orb values."""
        from compatibility import calculate_vibe_score

        transits = [{"orb": 1000.0, "is_harmonious": True}]
        score = calculate_vibe_score(transits)
        # BUG HUNT: max(0, 1 - (1000/3.0)) = max(0, -332.33) = 0
        # So total_weight would be 0, which triggers divide by zero check
        assert score == 50, "Large orb should result in neutral score"

    def test_synastry_aspect_with_same_planet(self):
        """Test synastry when comparing a planet to itself."""
        from compatibility import calculate_synastry_aspects
        from astro import compute_birth_chart, NatalChartData

        # Create two identical charts
        chart_dict, _ = compute_birth_chart("1990-06-15")
        chart1 = NatalChartData(**chart_dict)
        chart2 = NatalChartData(**chart_dict)

        aspects = calculate_synastry_aspects(chart1, chart2)
        # BUG HUNT: Should have many exact conjunctions (orb 0)
        exact_conjunctions = [a for a in aspects if a.orb == 0.0]
        assert len(exact_conjunctions) >= 11, "Same chart should have 11 exact conjunctions"


# =============================================================================
# BUG HUNT 2: Astro Module Edge Cases
# =============================================================================

class TestAstroBugHunt:
    """Probe astro.py for bugs."""

    def test_get_sun_sign_boundary_dates(self):
        """Test sun sign on exact boundary dates."""
        from astro import get_sun_sign, ZodiacSign

        # Aries/Taurus boundary: March 20-21
        # BUG HUNT: Off-by-one errors on boundaries
        # Note: These dates vary by year due to astronomical precision
        sign_mar20 = get_sun_sign("2000-03-20")
        sign_mar21 = get_sun_sign("2000-03-21")
        # At least one should be Pisces/Aries boundary area
        assert sign_mar20 in [ZodiacSign.PISCES, ZodiacSign.ARIES]

    def test_calculate_solar_house_with_same_sign(self):
        """Test solar house when sun and transit are same sign."""
        from astro import calculate_solar_house, House

        house = calculate_solar_house("aries", "aries")
        assert house == House.FIRST, "Same sign should be 1st house"

    def test_calculate_solar_house_wraparound(self):
        """Test solar house calculation wrapping around zodiac."""
        from astro import calculate_solar_house, House

        # Pisces sun, Aries transit: should be 2nd house
        house = calculate_solar_house("pisces", "aries")
        assert house == House.SECOND, f"Pisces+Aries should be 2nd house, got {house}"

    def test_compute_birth_chart_leap_year_feb_29(self):
        """Test birth chart on leap year Feb 29."""
        from astro import compute_birth_chart

        # Should not crash
        chart, is_exact = compute_birth_chart("2000-02-29")
        assert chart is not None
        assert len(chart["planets"]) == 12

    def test_compute_birth_chart_year_1900(self):
        """Test birth chart for very old date (ephemeris boundary)."""
        from astro import compute_birth_chart

        # 1900 is at the edge of many ephemeris files
        chart, is_exact = compute_birth_chart("1900-01-01")
        assert chart is not None
        assert len(chart["planets"]) == 12

    def test_compute_birth_chart_year_2100(self):
        """Test birth chart for far future date."""
        from astro import compute_birth_chart

        # BUG HUNT: Do ephemeris files support 2100?
        chart, is_exact = compute_birth_chart("2100-01-01")
        assert chart is not None

    def test_planet_absolute_degree_range(self):
        """Test that all planet degrees are in valid range 0-360."""
        from astro import compute_birth_chart

        chart, _ = compute_birth_chart("1990-06-15")
        for planet in chart["planets"]:
            degree = planet["absolute_degree"]
            assert 0 <= degree < 360, f"Planet {planet['name']} has invalid degree {degree}"

    def test_planet_degree_in_sign_range(self):
        """Test that degree_in_sign is always 0-30."""
        from astro import compute_birth_chart

        chart, _ = compute_birth_chart("1990-06-15")
        for planet in chart["planets"]:
            deg = planet["degree_in_sign"]
            assert 0 <= deg < 30, f"Planet {planet['name']} has invalid degree_in_sign {deg}"

    def test_house_cusp_degrees_ordered(self):
        """Test that house cusps are in proper order."""
        from astro import compute_birth_chart

        chart, _ = compute_birth_chart(
            "1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        # BUG HUNT: House cusps should generally increase
        # (though they wrap around 360)


# =============================================================================
# BUG HUNT 3: Entity Extraction Edge Cases
# =============================================================================

class TestEntityExtractionBugHunt:
    """Probe entity_extraction.py for bugs."""

    def test_merge_attributes_with_none_values(self):
        """Test merge_attributes when values contain None."""
        from entity_extraction import merge_attributes
        from models import AttributeKV

        existing = [AttributeKV(key="name", value="John")]
        # BUG HUNT: What if value is None?
        # Note: Pydantic should reject None for str field
        # This test verifies the validation works
        with pytest.raises(Exception):
            updates = [AttributeKV(key="name", value=None)]

    def test_merge_attributes_duplicate_keys(self):
        """Test merge_attributes with duplicate keys in updates."""
        from entity_extraction import merge_attributes
        from models import AttributeKV

        existing = [AttributeKV(key="status", value="single")]
        updates = [
            AttributeKV(key="status", value="dating"),
            AttributeKV(key="status", value="married"),  # Duplicate key
        ]

        result = merge_attributes(existing, updates)
        # BUG HUNT: Which value wins? Last one should win
        result_dict = {attr.key: attr.value for attr in result}
        assert result_dict["status"] == "married", "Last duplicate should win"

    def test_execute_merge_actions_context_fifo_overflow(self):
        """Test that context_snippets FIFO correctly limits to 10."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus

        now = datetime.now()
        # Create entity with 10 existing snippets
        existing = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=10,
            context_snippets=[f"Context {i}" for i in range(10)],
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        # Add new context via merge action
        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="merge",
                    entity_name="Test",
                    entity_type="person",
                    merge_with_id="ent_001",
                    context_update="New context 11"
                )
            ]
        )

        result = execute_merge_actions(merged, [existing], now)
        assert len(result) == 1
        entity = result[0]
        assert len(entity.context_snippets) == 10, "Should cap at 10 snippets"
        assert entity.context_snippets[-1] == "New context 11", "Newest should be last"
        assert entity.context_snippets[0] == "Context 1", "Oldest should be dropped (FIFO)"

    def test_importance_score_recalculation_on_merge(self):
        """Test that importance score is recalculated on merge."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus

        now = datetime.now()
        old_time = now - timedelta(days=30)

        existing = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=old_time.isoformat(),
            last_seen=old_time.isoformat(),
            mention_count=1,
            importance_score=0.1,  # Old low score
            created_at=old_time.isoformat(),
            updated_at=old_time.isoformat()
        )

        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="merge",
                    entity_name="Test",
                    entity_type="person",
                    merge_with_id="ent_001",
                    context_update="Recent mention"
                )
            ]
        )

        result = execute_merge_actions(merged, [existing], now)
        entity = result[0]
        # BUG HUNT: Score should be recalculated and higher due to recent mention
        assert entity.importance_score > 0.1, "Score should increase after recent mention"


# =============================================================================
# BUG HUNT 4: Models Validation Edge Cases
# =============================================================================

class TestModelsBugHunt:
    """Probe models.py for validation bugs."""

    def test_entity_mention_count_minimum(self):
        """Test Entity with mention_count below minimum."""
        from models import Entity, EntityStatus
        from pydantic import ValidationError

        now = datetime.now().isoformat()

        # BUG HUNT: mention_count has ge=1 constraint
        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now,
                last_seen=now,
                mention_count=0,  # Below minimum!
                created_at=now,
                updated_at=now
            )

    def test_entity_importance_score_above_max(self):
        """Test Entity with importance_score above 1.0."""
        from models import Entity, EntityStatus
        from pydantic import ValidationError

        now = datetime.now().isoformat()

        # BUG HUNT: importance_score has le=1.0 constraint
        with pytest.raises(ValidationError):
            Entity(
                entity_id="ent_001",
                name="Test",
                entity_type="person",
                status=EntityStatus.ACTIVE,
                first_seen=now,
                last_seen=now,
                mention_count=1,
                importance_score=1.5,  # Above maximum!
                created_at=now,
                updated_at=now
            )

    def test_user_profile_latitude_exactly_at_poles(self):
        """Test UserProfile with latitude at exactly +/- 90."""
        from models import UserProfile

        now = datetime.now().isoformat()

        # Should work at North Pole
        profile = UserProfile(
            user_id="user_001",
            name="Santa",
            email="santa@northpole.com",
            birth_date="1990-12-25",
            birth_lat=90.0,  # Exactly at North Pole
            birth_lon=0.0,
            sun_sign="capricorn",
            natal_chart={},
            exact_chart=False,
            created_at=now,
            last_active=now
        )
        assert profile.birth_lat == 90.0

    def test_user_profile_longitude_at_dateline(self):
        """Test UserProfile with longitude at +/- 180."""
        from models import UserProfile

        now = datetime.now().isoformat()

        # Should work at International Date Line
        profile = UserProfile(
            user_id="user_001",
            name="Test",
            email="test@test.com",
            birth_date="1990-01-01",
            birth_lat=0.0,
            birth_lon=180.0,  # Exactly at date line
            sun_sign="capricorn",
            natal_chart={},
            exact_chart=False,
            created_at=now,
            last_active=now
        )
        assert profile.birth_lon == 180.0

    def test_category_engagement_negative_count(self):
        """Test CategoryEngagement with negative count."""
        from models import CategoryEngagement
        from pydantic import ValidationError

        # BUG HUNT: count has ge=0 constraint
        with pytest.raises(ValidationError):
            CategoryEngagement(count=-1)

    def test_compatibility_category_score_boundaries(self):
        """Test CompatibilityCategory score at boundaries."""
        from compatibility import CompatibilityCategory

        # Test at -100
        cat = CompatibilityCategory(
            id="test",
            name="Test",
            score=-100
        )
        assert cat.score == -100

        # Test at +100
        cat = CompatibilityCategory(
            id="test",
            name="Test",
            score=100
        )
        assert cat.score == 100


# =============================================================================
# BUG HUNT 5: Connections Module Edge Cases
# =============================================================================

class TestConnectionsBugHunt:
    """Probe connections.py for bugs."""

    def test_connection_birth_date_regex_validation(self):
        """Test Connection birth_date regex pattern."""
        from connections import Connection
        from pydantic import ValidationError
        from models import RelationshipType

        now = datetime.now().isoformat()

        # BUG HUNT: birth_date has pattern r"^\d{4}-\d{2}-\d{2}$"
        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="Test",
                birth_date="1990-1-15",  # Invalid: single digit month
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_connection_birth_date_invalid_date(self):
        """Test Connection rejects syntactically valid but semantically invalid date."""
        from connections import Connection
        from pydantic import ValidationError
        from models import RelationshipType

        now = datetime.now().isoformat()

        # Validation should reject invalid dates like "2000-13-45"
        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="Test",
                birth_date="2000-13-45",  # Invalid date - should be rejected
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_connection_empty_name(self):
        """Test Connection with empty name."""
        from connections import Connection
        from pydantic import ValidationError
        from models import RelationshipType

        now = datetime.now().isoformat()

        # BUG HUNT: name has min_length=1 constraint
        with pytest.raises(ValidationError):
            Connection(
                connection_id="conn_001",
                name="",  # Empty name!
                birth_date="1990-01-15",
                relationship_type=RelationshipType.FRIEND,
                created_at=now,
                updated_at=now
            )

    def test_share_secret_length(self):
        """Test that share secret has consistent length."""
        from connections import generate_share_secret

        secrets = [generate_share_secret() for _ in range(100)]
        # BUG HUNT: token_urlsafe(9) should give 12 chars
        for secret in secrets:
            assert len(secret) == 12, f"Share secret should be 12 chars, got {len(secret)}"


# =============================================================================
# BUG HUNT 6: Calculate Importance Score Edge Cases
# =============================================================================

class TestImportanceScoreBugHunt:
    """Probe calculate_entity_importance_score for bugs."""

    def test_importance_score_entity_seen_today(self):
        """Test importance score for entity just seen."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()
        entity = Entity(
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

        score = calculate_entity_importance_score(entity, now)
        # Recently seen entity should have high recency score
        assert score >= 0.5, "Entity seen today should have high score"

    def test_importance_score_entity_not_seen_in_year(self):
        """Test importance score for entity not seen in a year."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()
        old_time = now - timedelta(days=365)

        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=old_time.isoformat(),
            last_seen=old_time.isoformat(),
            mention_count=1,
            created_at=old_time.isoformat(),
            updated_at=old_time.isoformat()
        )

        score = calculate_entity_importance_score(entity, now)
        # Very old entity should have low score
        assert score < 0.3, f"Entity not seen in year should have low score, got {score}"

    def test_importance_score_high_frequency_entity(self):
        """Test importance score for frequently mentioned entity."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()
        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=100,  # Very high frequency
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        score = calculate_entity_importance_score(entity, now)
        # Frequently mentioned entity should have high score
        assert score >= 0.8, f"Highly mentioned entity should have high score, got {score}"

    def test_importance_score_caps_at_1(self):
        """Test that importance score never exceeds 1.0."""
        from models import Entity, EntityStatus, calculate_entity_importance_score

        now = datetime.now()
        entity = Entity(
            entity_id="ent_001",
            name="Test",
            entity_type="person",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=10000,  # Extremely high
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        score = calculate_entity_importance_score(entity, now)
        assert score <= 1.0, f"Score should cap at 1.0, got {score}"


# =============================================================================
# BUG HUNT 7: LLM Module Edge Cases
# =============================================================================

class TestLLMBugHunt:
    """Probe llm.py for bugs."""

    def test_compress_horoscope_with_empty_meters(self):
        """Test compress_horoscope when meters list is empty."""
        # BUG HUNT: What happens when no meters are provided?

    def test_format_transit_summary_with_no_transits(self):
        """Test format_transit_summary with empty transit list."""
        # BUG HUNT: Does it handle empty data gracefully?


# =============================================================================
# BUG HUNT 8: Numeric Precision Issues
# =============================================================================

class TestNumericPrecisionBugHunt:
    """Test for floating point precision issues."""

    def test_aspect_orb_floating_point_comparison(self):
        """Test aspect calculation with floating point precision issues."""
        from compatibility import calculate_aspect

        # 89.99999999 should still be detected as square (90)
        result = calculate_aspect(89.99999999, 0.0, "sun", "moon")
        assert result is not None, "Should detect square aspect"
        aspect_type, orb, _ = result
        assert aspect_type == "square", f"Expected square, got {aspect_type}"

    def test_degree_normalization_floating_point(self):
        """Test degree calculations with floating point numbers."""
        from compatibility import calculate_composite_sign

        # Very close to 360 should behave like 0
        sign1 = calculate_composite_sign(359.9999999, 0.0000001)
        # This should be essentially 360/2 = 180 = Libra
        # But with wraparound handling it might be different

    def test_orb_weight_floating_point_boundary(self):
        """Test orb weight at floating point boundary."""
        from compatibility import get_orb_weight

        # Just barely under 2.0
        weight = get_orb_weight(1.9999999999)
        assert weight == 1.0, "Orb just under 2 should give weight 1.0"

        # Just barely over 2.0
        weight = get_orb_weight(2.0000000001)
        # BUG HUNT: Does this give 1.0 or 0.75?
        # With exact comparison (orb <= 2), this should give 0.75


# =============================================================================
# BUG HUNT 9: State and Mutation Issues
# =============================================================================

class TestStateMutationBugHunt:
    """Test for unintended state mutations."""

    def test_execute_merge_actions_doesnt_mutate_input(self):
        """Test that execute_merge_actions doesn't mutate input entities."""
        from entity_extraction import execute_merge_actions
        from models import MergedEntities, EntityMergeAction, Entity, EntityStatus
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

        # Deep copy to compare after
        original_copy = copy.deepcopy(original_entity)

        merged = MergedEntities(
            actions=[
                EntityMergeAction(
                    action="merge",
                    entity_name="Test",
                    entity_type="person",
                    merge_with_id="ent_001",
                    context_update="New context"
                )
            ]
        )

        result = execute_merge_actions(merged, [original_entity], now)

        # BUG HUNT: Did the original entity get mutated?
        # Pydantic models are mutable by default!
        # This test may reveal mutation bugs
        assert original_entity.mention_count == original_copy.mention_count, \
            "Input entity should not be mutated"

    def test_merge_attributes_doesnt_mutate_input(self):
        """Test that merge_attributes doesn't mutate input lists."""
        from entity_extraction import merge_attributes
        from models import AttributeKV
        import copy

        existing = [AttributeKV(key="name", value="John")]
        updates = [AttributeKV(key="status", value="active")]

        existing_copy = copy.deepcopy(existing)
        updates_copy = copy.deepcopy(updates)

        result = merge_attributes(existing, updates)

        # Check inputs weren't mutated
        assert len(existing) == len(existing_copy), "existing list should not be mutated"
        assert len(updates) == len(updates_copy), "updates list should not be mutated"


# =============================================================================
# BUG HUNT 10: Empty and None Handling
# =============================================================================

class TestEmptyNoneHandlingBugHunt:
    """Test handling of empty collections and None values."""

    def test_calculate_category_score_empty_planet_pairs(self):
        """Test category score with empty planet pairs list."""
        from compatibility import calculate_category_score

        score, aspect_ids = calculate_category_score([], [])
        assert score == 0, "Empty inputs should give score 0"
        assert aspect_ids == [], "Empty inputs should give empty aspect_ids"

    def test_memory_collection_format_for_llm_empty(self):
        """Test MemoryCollection.format_for_llm with no engagement."""
        from models import MemoryCollection, CategoryEngagement
        from astrometers.hierarchy import MeterGroupV2

        now = datetime.now().isoformat()

        # All categories with 0 count
        categories = {group: CategoryEngagement(count=0) for group in MeterGroupV2}

        memory = MemoryCollection(
            user_id="user_001",
            categories=categories,
            updated_at=now
        )

        formatted = memory.format_for_llm()
        assert "First time user" in formatted, "Should indicate first time user"

    def test_route_people_empty_context_snippets(self):
        """Test route_people_to_connections with entity having empty context."""
        from entity_extraction import route_people_to_connections
        from models import Entity, EntityStatus

        now = datetime.now()
        entity = Entity(
            entity_id="ent_001",
            name="John",
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=1,
            context_snippets=[],  # Empty!
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

        connections = [{"name": "John", "connection_id": "conn_001"}]

        filtered, updates = route_people_to_connections([entity], connections, "2025-01-20")
        # BUG HUNT: With empty context, should we still route?
        # Latest context would be empty string


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

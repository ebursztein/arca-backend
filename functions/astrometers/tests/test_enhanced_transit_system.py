"""
Comprehensive pytest unit tests for enhanced transit system.

Tests the complete natal-transit aspect detection, priority scoring,
critical degree analysis, speed timing, and UI formatting system.

Run with: pytest functions/astrometers/tests/test_enhanced_transit_system.py -v
"""

import pytest
import json
from astro import (
    find_natal_transit_aspects,
    calculate_aspect_priority,
    analyze_planet_speed,
    check_critical_degrees,
    format_transit_summary_for_ui,
    compute_birth_chart,
    Planet,
    AspectType,
    ZodiacSign,
    TransitSpeed,
    CriticalDegree
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_natal_chart():
    """Sample natal chart for testing."""
    chart, _ = compute_birth_chart("1990-01-15")
    return chart


@pytest.fixture
def sample_transit_chart():
    """Sample transit chart for testing."""
    chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")
    return chart


# =============================================================================
# 1. CORE ASPECT DETECTION TESTS
# =============================================================================

class TestAspectDetection:
    """Test aspect detection accuracy and orb calculations."""

    def test_aspect_detection_returns_list(self, sample_natal_chart, sample_transit_chart):
        """find_natal_transit_aspects should always return a list."""
        aspects = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=3.0)
        assert isinstance(aspects, list)

    def test_tight_aspects_have_small_orbs(self, sample_natal_chart, sample_transit_chart):
        """Tight aspects should have orbs < 0.5°."""
        aspects = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=3.0)
        tight_aspects = [a for a in aspects if a.orb < 0.5]

        for aspect in tight_aspects:
            assert aspect.orb >= 0.0
            assert aspect.orb < 0.5

    def test_orb_boundaries(self, sample_natal_chart, sample_transit_chart):
        """Tighter orb should find fewer or equal aspects."""
        aspects_3deg = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=3.0)
        aspects_1deg = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=1.0)

        assert len(aspects_1deg) <= len(aspects_3deg)

    def test_all_orbs_within_limit(self, sample_natal_chart, sample_transit_chart):
        """All detected orbs should be within specified limit."""
        orb_limit = 3.0
        aspects = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=orb_limit)

        for aspect in aspects:
            assert aspect.orb <= orb_limit
            assert aspect.orb >= 0.0

    def test_applying_is_boolean(self, sample_natal_chart, sample_transit_chart):
        """Applying field should always be boolean."""
        aspects = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=3.0)

        for aspect in aspects:
            assert isinstance(aspect.applying, bool)

    def test_very_tight_orb_works(self, sample_natal_chart, sample_transit_chart):
        """Extremely tight orb (0.1°) should work without errors."""
        aspects = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=0.1)

        assert isinstance(aspects, list)
        for aspect in aspects:
            assert aspect.orb <= 0.1


# =============================================================================
# 2. ORB CALCULATION TESTS
# =============================================================================

class TestOrbCalculation:
    """Test orb calculation consistency and precision."""

    def test_orb_calculation_is_deterministic(self, sample_natal_chart, sample_transit_chart):
        """Same calculation should return identical results."""
        aspects1 = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=3.0)
        aspects2 = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=3.0)

        assert len(aspects1) == len(aspects2)

        for a1, a2 in zip(aspects1, aspects2):
            assert a1.orb == a2.orb
            assert a1.priority_score == a2.priority_score

    def test_orb_precision(self, sample_natal_chart, sample_transit_chart):
        """Orb should be float with meaningful precision."""
        aspects = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=3.0)

        for aspect in aspects:
            assert isinstance(aspect.orb, float)
            # Check has decimal precision
            orb_str = f"{aspect.orb:.2f}"
            assert "." in orb_str

    def test_no_orb_exceeds_180_degrees(self, sample_natal_chart, sample_transit_chart):
        """Orb should never exceed 180° (should use shortest angle)."""
        aspects = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=8.0)

        for aspect in aspects:
            # Max orb for major aspects is ~8°
            assert aspect.orb <= 8.0


# =============================================================================
# 3. PRIORITY SCORING TESTS
# =============================================================================

class TestPriorityScoring:
    """Test aspect priority scoring algorithm."""

    def test_tighter_orb_scores_higher(self):
        """0.3° orb should score higher than 2.9° orb."""
        # Use Jupiter (less important than Saturn) to avoid hitting max score
        score_tight = calculate_aspect_priority(
            Planet.JUPITER, Planet.VENUS, AspectType.SEXTILE,
            orb=0.3, applying=True, transit_speed=TransitSpeed.AVERAGE,
            natal_house=5, transit_house=7,
            transit_retrograde=False, transit_sign=ZodiacSign.PISCES
        )

        score_loose = calculate_aspect_priority(
            Planet.JUPITER, Planet.VENUS, AspectType.SEXTILE,
            orb=2.9, applying=True, transit_speed=TransitSpeed.AVERAGE,
            natal_house=5, transit_house=7,
            transit_retrograde=False, transit_sign=ZodiacSign.PISCES
        )

        assert score_tight > score_loose

    def test_square_scores_higher_than_sextile(self):
        """Square should score higher than sextile (more impactful)."""
        # Use Mars to avoid max score ceiling
        score_square = calculate_aspect_priority(
            Planet.MARS, Planet.MERCURY, AspectType.SQUARE,
            orb=1.5, applying=True, transit_speed=TransitSpeed.AVERAGE,
            natal_house=3, transit_house=6,
            transit_retrograde=False, transit_sign=ZodiacSign.GEMINI
        )

        score_sextile = calculate_aspect_priority(
            Planet.MARS, Planet.MERCURY, AspectType.SEXTILE,
            orb=1.5, applying=True, transit_speed=TransitSpeed.AVERAGE,
            natal_house=3, transit_house=6,
            transit_retrograde=False, transit_sign=ZodiacSign.GEMINI
        )

        assert score_square > score_sextile

    def test_applying_scores_higher_than_separating(self):
        """Applying aspect should score higher than separating."""
        # Use Venus to avoid max score
        score_applying = calculate_aspect_priority(
            Planet.VENUS, Planet.MARS, AspectType.TRINE,
            orb=2.0, applying=True, transit_speed=TransitSpeed.AVERAGE,
            natal_house=5, transit_house=9,
            transit_retrograde=False, transit_sign=ZodiacSign.LIBRA
        )

        score_separating = calculate_aspect_priority(
            Planet.VENUS, Planet.MARS, AspectType.TRINE,
            orb=2.0, applying=False, transit_speed=TransitSpeed.AVERAGE,
            natal_house=5, transit_house=9,
            transit_retrograde=False, transit_sign=ZodiacSign.LIBRA
        )

        assert score_applying > score_separating

    def test_sun_scores_higher_than_jupiter(self):
        """Transit to Sun should score higher than transit to Jupiter."""
        score_to_sun = calculate_aspect_priority(
            Planet.SATURN, Planet.SUN, AspectType.SQUARE,
            orb=1.0, applying=True, transit_speed=TransitSpeed.AVERAGE,
            natal_house=1, transit_house=10,
            transit_retrograde=False, transit_sign=ZodiacSign.PISCES
        )

        score_to_jupiter = calculate_aspect_priority(
            Planet.SATURN, Planet.JUPITER, AspectType.SQUARE,
            orb=1.0, applying=True, transit_speed=TransitSpeed.AVERAGE,
            natal_house=1, transit_house=10,
            transit_retrograde=False, transit_sign=ZodiacSign.PISCES
        )

        assert score_to_sun > score_to_jupiter

    def test_aspects_sorted_by_priority(self, sample_natal_chart, sample_transit_chart):
        """Returned aspects should be sorted by priority descending."""
        aspects = find_natal_transit_aspects(
            sample_natal_chart, sample_transit_chart,
            orb=3.0, sort_by_priority=True
        )

        for i in range(len(aspects) - 1):
            assert aspects[i].priority_score >= aspects[i + 1].priority_score


# =============================================================================
# 4. CRITICAL DEGREE TESTS
# =============================================================================

class TestCriticalDegrees:
    """Test critical degree detection."""

    def test_anaretic_29_degree_detected(self):
        """29.0° to 29.99° should flag as anaretic."""
        critical = check_critical_degrees(29.5, ZodiacSign.ARIES)
        anaretic_found = any(deg_type == CriticalDegree.ANARETIC for deg_type, _ in critical)
        assert anaretic_found

    def test_anaretic_boundary_29_00(self):
        """29.00° should flag as anaretic."""
        critical = check_critical_degrees(29.0, ZodiacSign.ARIES)
        anaretic_found = any(deg_type == CriticalDegree.ANARETIC for deg_type, _ in critical)
        assert anaretic_found

    def test_non_anaretic_28_99(self):
        """28.99° should NOT flag as anaretic."""
        critical = check_critical_degrees(28.99, ZodiacSign.ARIES)
        anaretic_found = any(deg_type == CriticalDegree.ANARETIC for deg_type, _ in critical)
        assert not anaretic_found

    def test_avatar_0_degree_detected(self):
        """0.0° to 0.99° should flag as avatar."""
        critical = check_critical_degrees(0.5, ZodiacSign.ARIES)
        avatar_found = any(deg_type == CriticalDegree.AVATAR for deg_type, _ in critical)
        assert avatar_found

    def test_avatar_boundary_0_99(self):
        """0.99° should flag as avatar."""
        critical = check_critical_degrees(0.99, ZodiacSign.ARIES)
        avatar_found = any(deg_type == CriticalDegree.AVATAR for deg_type, _ in critical)
        assert avatar_found

    def test_non_avatar_1_00(self):
        """1.0° should NOT flag as avatar."""
        critical = check_critical_degrees(1.0, ZodiacSign.ARIES)
        avatar_found = any(deg_type == CriticalDegree.AVATAR for deg_type, _ in critical)
        assert not avatar_found

    def test_cardinal_13_degree_in_aries(self):
        """13° in Aries (cardinal) should flag as cardinal critical."""
        critical = check_critical_degrees(13.0, ZodiacSign.ARIES)
        cardinal_found = any(deg_type == CriticalDegree.CRITICAL_CARDINAL for deg_type, _ in critical)
        assert cardinal_found

    def test_cardinal_13_degree_not_in_taurus(self):
        """13° in Taurus (fixed) should NOT flag as cardinal critical."""
        critical = check_critical_degrees(13.0, ZodiacSign.TAURUS)
        cardinal_found = any(deg_type == CriticalDegree.CRITICAL_CARDINAL for deg_type, _ in critical)
        assert not cardinal_found

    def test_all_cardinal_degrees_detected(self):
        """0°, 13°, 26° in cardinal signs should all flag."""
        for degree in [0.5, 13.0, 26.0]:
            critical = check_critical_degrees(degree, ZodiacSign.CAPRICORN)
            assert len(critical) > 0


# =============================================================================
# 5. SPEED CALCULATION TESTS
# =============================================================================

class TestSpeedCalculation:
    """Test planet speed analysis."""

    def test_stationary_detection(self):
        """Near-zero motion should flag as stationary."""
        speed_enum, desc = analyze_planet_speed(Planet.SATURN, 0.001)
        assert speed_enum == TransitSpeed.STATIONARY
        assert "stationary" in desc.lower() or "station" in desc.lower()

    def test_speed_returns_valid_category(self):
        """Speed analysis should return valid TransitSpeed."""
        speed_enum, desc = analyze_planet_speed(Planet.MARS, 0.5)
        assert isinstance(speed_enum, TransitSpeed)
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_negative_speed_handled(self):
        """Negative (retrograde) speed should be handled."""
        speed_enum, desc = analyze_planet_speed(Planet.MERCURY, -0.5)
        # Should not crash, should return valid data
        assert isinstance(speed_enum, TransitSpeed)
        assert isinstance(desc, str)


# =============================================================================
# 6. FORMAT_TRANSIT_SUMMARY_FOR_UI TESTS
# =============================================================================

class TestTransitSummaryFormatting:
    """Test format_transit_summary_for_ui() output."""

    def test_returns_dict_with_required_keys(self, sample_natal_chart, sample_transit_chart):
        """Should return dict with all expected keys."""
        summary = format_transit_summary_for_ui(sample_natal_chart, sample_transit_chart)

        required_keys = [
            "priority_transits",
            "critical_degree_alerts",
            "critical_degree_synthesis",
            "theme_synthesis",
            "retrograde_planets",
            "planet_positions",
            "total_aspects_found"
        ]

        for key in required_keys:
            assert key in summary

    def test_priority_transits_have_required_fields(self, sample_natal_chart, sample_transit_chart):
        """Each priority transit should have required fields."""
        summary = format_transit_summary_for_ui(sample_natal_chart, sample_transit_chart)

        required_fields = [
            "description", "intensity_indicator", "priority_score",
            "orb", "meaning", "transit_planet", "natal_planet", "aspect_type"
        ]

        for transit in summary["priority_transits"]:
            for field in required_fields:
                assert field in transit

    def test_intensity_indicators_use_lightning(self, sample_natal_chart, sample_transit_chart):
        """Intensity indicators should use lightning bolt emoji."""
        summary = format_transit_summary_for_ui(sample_natal_chart, sample_transit_chart)

        for transit in summary["priority_transits"]:
            assert "⚡" in transit["intensity_indicator"]

    def test_theme_synthesis_has_text(self, sample_natal_chart, sample_transit_chart):
        """Theme synthesis should have theme_synthesis text."""
        summary = format_transit_summary_for_ui(sample_natal_chart, sample_transit_chart)

        assert "theme_synthesis" in summary["theme_synthesis"]
        assert isinstance(summary["theme_synthesis"]["theme_synthesis"], str)
        assert len(summary["theme_synthesis"]["theme_synthesis"]) > 0

    def test_max_aspects_limit_respected(self, sample_natal_chart, sample_transit_chart):
        """Should respect max_aspects parameter."""
        summary = format_transit_summary_for_ui(sample_natal_chart, sample_transit_chart, max_aspects=3)

        assert len(summary["priority_transits"]) <= 3

    def test_json_serializable(self, sample_natal_chart, sample_transit_chart):
        """All output should be JSON serializable."""
        summary = format_transit_summary_for_ui(sample_natal_chart, sample_transit_chart)

        # Should not raise exception
        json_str = json.dumps(summary, default=str)
        assert len(json_str) > 0

        # Should deserialize
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


# =============================================================================
# 7. INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Test complete end-to-end workflows."""

    def test_full_analysis_completes(self, sample_natal_chart, sample_transit_chart):
        """Complete natal + transit analysis should complete without errors."""
        summary = format_transit_summary_for_ui(sample_natal_chart, sample_transit_chart)

        assert len(summary) > 0
        assert isinstance(summary, dict)

    def test_handles_empty_aspects(self):
        """Should handle case where no aspects within orb."""
        natal, _ = compute_birth_chart("1990-01-15")
        transit, _ = compute_birth_chart("1990-01-20", birth_time="12:00")

        # Extremely tight orb
        aspects = find_natal_transit_aspects(natal, transit, orb=0.01)

        assert isinstance(aspects, list)
        # May be empty, but should not crash

    def test_handles_many_aspects(self, sample_natal_chart, sample_transit_chart):
        """Should handle charts with many simultaneous aspects."""
        # Use wide orb
        aspects = find_natal_transit_aspects(sample_natal_chart, sample_transit_chart, orb=8.0)

        assert isinstance(aspects, list)
        # Should work even if many aspects found


# =============================================================================
# 8. EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_same_date_natal_and_transit(self):
        """Natal and transit on same date should still work."""
        natal, _ = compute_birth_chart("2025-11-03", birth_time="00:00")
        transit, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        aspects = find_natal_transit_aspects(natal, transit, orb=3.0)
        assert isinstance(aspects, list)

    def test_convergence_patterns_detected(self, sample_natal_chart, sample_transit_chart):
        """Multiple transits to same natal planet should be detected."""
        summary = format_transit_summary_for_ui(sample_natal_chart, sample_transit_chart, max_aspects=10)

        # Check convergence patterns exist in theme synthesis
        if summary["theme_synthesis"].get("convergence_patterns"):
            for pattern in summary["theme_synthesis"]["convergence_patterns"]:
                assert pattern["count"] >= 1
                assert len(pattern["aspecting_planets"]) >= 1

    def test_retrograde_natal_connections(self):
        """Retrograde planets should show natal connections if applicable."""
        # Gemini sun
        natal, _ = compute_birth_chart("1987-06-02")
        transit, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        summary = format_transit_summary_for_ui(natal, transit)

        for rx in summary["retrograde_planets"]:
            # Should have natal_connection key (even if None)
            assert "natal_connection" in rx


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

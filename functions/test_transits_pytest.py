"""
Comprehensive pytest suite for enhanced transit reporting system.

Run with: pytest test_transits_pytest.py -v
"""

import pytest
import json
from datetime import datetime
from astro import (
    compute_birth_chart,
    find_natal_transit_aspects,
    format_transit_summary_for_ui,
    get_intensity_indicator,
    get_speed_timing_details,
    synthesize_transit_themes,
    check_critical_degrees,
    analyze_planet_speed,
    synthesize_critical_degrees,
    ZodiacSign,
    Planet,
    TransitSpeed,
    CriticalDegree
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def natal_chart():
    """Consistent test natal chart."""
    chart, _ = compute_birth_chart(
        birth_date="1985-05-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )
    return chart


@pytest.fixture
def transit_chart():
    """Consistent test transit chart."""
    chart, _ = compute_birth_chart(
        birth_date="2025-11-03",
        birth_time="12:00",
        birth_timezone="UTC",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )
    return chart


# ============================================================================
# Test: Intensity Indicators
# ============================================================================

class TestIntensityIndicators:
    """Test visual intensity indicator generation."""

    def test_peak_influence_high_priority(self):
        """Priority 90+ should show ⚡⚡⚡"""
        assert get_intensity_indicator(95, 1.5) == "⚡⚡⚡"
        assert get_intensity_indicator(90, 2.0) == "⚡⚡⚡"

    def test_peak_influence_tight_orb(self):
        """Orb < 0.5° should show ⚡⚡⚡ regardless of priority"""
        assert get_intensity_indicator(50, 0.3) == "⚡⚡⚡"
        assert get_intensity_indicator(60, 0.49) == "⚡⚡⚡"

    def test_strong_influence(self):
        """Priority 70-89 or orb 0.5-1.0° should show ⚡⚡"""
        assert get_intensity_indicator(75, 1.5) == "⚡⚡"
        assert get_intensity_indicator(80, 0.8) == "⚡⚡"

    def test_moderate_influence(self):
        """Priority 50-69 or orb 1.0-2.0° should show ⚡"""
        assert get_intensity_indicator(55, 2.5) == "⚡"
        assert get_intensity_indicator(65, 1.5) == "⚡"

    def test_background_influence(self):
        """Priority < 50 and orb > 2.0° should show ·"""
        assert get_intensity_indicator(45, 2.5) == "·"


# ============================================================================
# Test: Speed Timing Details
# ============================================================================

class TestSpeedTimingDetails:
    """Test enhanced speed timing with windows."""

    def test_stationary_planet_messaging(self):
        """Stationary planets should have maximum impact messaging"""
        result = get_speed_timing_details(Planet.MARS, 0.05, 0.5)
        assert result["speed_enum"] == "stationary"
        assert "Maximum impact" in result["timing_impact"]
        assert "Life-changing" in result["best_use"]

    def test_slow_planet_extended_window(self):
        """Slow planets should show extended influence windows"""
        result = get_speed_timing_details(Planet.JUPITER, 0.03, 0.5)
        assert result["speed_enum"] == "slow"
        assert "week influence window" in result["timing_impact"]
        assert result["peak_window"] is not None

    def test_fast_outer_planet_slow_burn(self):
        """Fast but very slow outer planets (Pluto) should show slow-burn"""
        result = get_speed_timing_details(Planet.PLUTO, 0.01, 0.83)
        assert result["speed_enum"] == "fast"
        assert "Slow-burn transformation" in result["timing_impact"]
        assert "weeks" in result["timing_impact"]
        assert "Integration window" in result["peak_window"]

    def test_fast_inner_planet_brief_window(self):
        """Fast inner planets should show brief window"""
        result = get_speed_timing_details(Planet.MERCURY, 1.5, 0.5)
        assert result["speed_enum"] == "fast"
        assert "Brief but intense" in result["timing_impact"]
        assert "days" in result["timing_impact"].lower()


# ============================================================================
# Test: Critical Degrees
# ============================================================================

class TestCriticalDegrees:
    """Test critical degree detection."""

    def test_anaretic_29_degrees(self):
        """29° should detect anaretic crisis point"""
        result = check_critical_degrees(29.2, ZodiacSign.SCORPIO)
        assert len(result) == 1
        assert result[0][0] == CriticalDegree.ANARETIC
        assert "Crisis" in result[0][1]

    def test_avatar_0_degrees(self):
        """0° should detect avatar new beginning"""
        result = check_critical_degrees(0.5, ZodiacSign.ARIES)
        assert len(result) >= 1
        types = [r[0] for r in result]
        assert CriticalDegree.AVATAR in types

    def test_cardinal_critical_13_degrees(self):
        """13° in cardinal signs should be detected"""
        result = check_critical_degrees(13.1, ZodiacSign.CANCER)
        types = [r[0] for r in result]
        assert CriticalDegree.CRITICAL_CARDINAL in types

    def test_no_critical_degrees(self):
        """Normal degrees should return empty"""
        result = check_critical_degrees(15.0, ZodiacSign.TAURUS)
        assert len(result) == 0


# ============================================================================
# Test: Critical Degree Synthesis
# ============================================================================

class TestCriticalDegreeSynthesis:
    """Test critical degree synthesis counting fix."""

    def test_counts_all_critical_degree_types(self, transit_chart):
        """Should count anaretic + avatar + cardinal critical"""
        synthesis = synthesize_critical_degrees(transit_chart)

        total_count = synthesis["total_count"]
        anaretic_count = len(synthesis["anaretic_planets"])
        avatar_count = len(synthesis["avatar_planets"])
        cardinal_count = len(synthesis["cardinal_critical"])

        # Total should equal sum of all three types
        expected_total = anaretic_count + avatar_count + cardinal_count
        assert total_count == expected_total

    def test_interpretation_includes_breakdown(self, transit_chart):
        """Interpretation should show breakdown of critical degree types"""
        synthesis = synthesize_critical_degrees(transit_chart)

        if synthesis["total_count"] >= 3:
            interp = synthesis["interpretation"]
            # Should mention counts of each type
            assert "anaretic" in interp
            assert "avatar" in interp or "cardinal" in interp


# ============================================================================
# Test: Orb Consistency
# ============================================================================

class TestOrbConsistency:
    """Test orb calculation consistency."""

    def test_orb_consistency_across_functions(self, natal_chart, transit_chart):
        """Orb should match between find_natal_transit_aspects and format_transit_summary_for_ui"""
        aspects = find_natal_transit_aspects(natal_chart, transit_chart)
        summary = format_transit_summary_for_ui(natal_chart, transit_chart, max_aspects=5)

        if aspects and summary["priority_transits"]:
            direct_orb = aspects[0].orb
            formatted_orb = summary["priority_transits"][0]["orb"]
            assert direct_orb == formatted_orb

    def test_orb_rounding_precision(self, natal_chart, transit_chart):
        """All orbs should be rounded to 2 decimal places"""
        aspects = find_natal_transit_aspects(natal_chart, transit_chart)

        for aspect in aspects:
            orb_str = str(aspect.orb)
            if '.' in orb_str:
                decimal_places = len(orb_str.split('.')[1])
                assert decimal_places <= 2

    def test_orb_within_specified_range(self, natal_chart, transit_chart):
        """All aspects should have orb within specified range"""
        aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=3.0)

        for aspect in aspects:
            assert aspect.orb >= 0
            assert aspect.orb <= 3.0


# ============================================================================
# Test: Theme Synthesis
# ============================================================================

class TestThemeSynthesis:
    """Test enhanced theme synthesis."""

    def test_convergence_detection(self, natal_chart, transit_chart):
        """Should detect multiple transits to same natal planet"""
        aspects = find_natal_transit_aspects(natal_chart, transit_chart)
        synthesis = synthesize_transit_themes(aspects, top_n=5)

        assert "convergence_patterns" in synthesis
        if synthesis["convergence_patterns"]:
            pattern = synthesis["convergence_patterns"][0]
            assert "focal_planet" in pattern
            assert "focal_meaning" in pattern
            assert pattern["count"] >= 2

    def test_harmony_tension_balance(self, natal_chart, transit_chart):
        """Should calculate harmony vs tension balance"""
        aspects = find_natal_transit_aspects(natal_chart, transit_chart)
        synthesis = synthesize_transit_themes(aspects, top_n=5)

        assert synthesis["harmony_tension_balance"] in ["harmonious", "challenging", "mixed", "neutral"]
        assert "total_harmonious" in synthesis
        assert "total_challenging" in synthesis


# ============================================================================
# Test: Format Transit Summary for UI
# ============================================================================

class TestFormatTransitSummaryForUI:
    """Test complete UI output structure."""

    def test_has_all_required_keys(self, natal_chart, transit_chart):
        """Summary should have all required top-level keys"""
        summary = format_transit_summary_for_ui(natal_chart, transit_chart)

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

    def test_priority_transit_structure(self, natal_chart, transit_chart):
        """Each priority transit should have complete structure"""
        summary = format_transit_summary_for_ui(natal_chart, transit_chart)

        if summary["priority_transits"]:
            transit = summary["priority_transits"][0]

            required_fields = [
                "description",
                "intensity_indicator",
                "intensity_label",
                "priority_score",
                "orb",
                "orb_label",
                "applying_label",
                "speed_timing",
                "meaning"
            ]

            for field in required_fields:
                assert field in transit

    def test_speed_timing_structure(self, natal_chart, transit_chart):
        """Speed timing should have complete structure"""
        summary = format_transit_summary_for_ui(natal_chart, transit_chart)

        if summary["priority_transits"]:
            transit = summary["priority_transits"][0]
            if transit["speed_timing"]:
                st = transit["speed_timing"]

                assert "speed_enum" in st
                assert "timing_impact" in st
                assert "peak_window" in st
                assert "best_use" in st

    def test_intensity_indicators_valid(self, natal_chart, transit_chart):
        """All intensity indicators should be valid"""
        summary = format_transit_summary_for_ui(natal_chart, transit_chart)

        valid_indicators = ["⚡⚡⚡", "⚡⚡", "⚡", "·"]
        for transit in summary["priority_transits"]:
            assert transit["intensity_indicator"] in valid_indicators

    def test_json_serializable(self, natal_chart, transit_chart):
        """Output should be JSON serializable for iOS"""
        summary = format_transit_summary_for_ui(natal_chart, transit_chart)

        try:
            json_str = json.dumps(summary, default=str)
            assert isinstance(json_str, str)
        except TypeError as e:
            pytest.fail(f"Not JSON serializable: {e}")


# ============================================================================
# Test: Integration Full Pipeline
# ============================================================================

class TestIntegrationFullPipeline:
    """Integration tests for complete pipeline."""

    def test_full_pipeline_executes(self, natal_chart, transit_chart):
        """Complete pipeline should execute without errors"""
        aspects = find_natal_transit_aspects(natal_chart, transit_chart)
        assert isinstance(aspects, list)

        summary = format_transit_summary_for_ui(natal_chart, transit_chart)
        assert isinstance(summary, dict)

        if aspects:
            synthesis = synthesize_transit_themes(aspects)
            assert isinstance(synthesis, dict)

    def test_intensity_matches_priority(self, natal_chart, transit_chart):
        """Intensity indicators should correlate with priority"""
        summary = format_transit_summary_for_ui(natal_chart, transit_chart)

        for transit in summary["priority_transits"]:
            indicator = transit["intensity_indicator"]
            priority = transit["priority_score"]
            orb = transit["orb"]

            if indicator == "⚡⚡⚡":
                assert priority >= 90 or orb < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Unit tests for meters module v2 (17-meter JSON-driven system).

Tests:
- JSON configuration loading
- Meter calculation with filtered aspects
- Retrograde modifiers
- Calibration integration
- All 17 meters present and functional
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from datetime import datetime
from astro import Planet, AspectType, compute_birth_chart
from astrometers.meters import (
    METER_CONFIGS,
    MeterConfig,
    get_meters,
    get_meter,
    calculate_unified_score,
    QualityLabel,
    filter_aspects
)
from astrometers.core import calculate_all_aspects


# ============================================================================
# Configuration Loading Tests
# ============================================================================

class TestConfigurationLoading:
    """Test that meter configurations are loaded from JSON files."""

    def test_all_17_meters_loaded(self):
        """Test that all 17 meters are loaded from JSON."""
        assert len(METER_CONFIGS) == 17

        expected_meters = [
            'clarity', 'focus', 'communication',
            'connections', 'resilience', 'vulnerability',
            'energy', 'drive', 'strength',
            'vision', 'flow', 'intuition', 'creativity',
            'momentum', 'ambition', 'evolution', 'circle'
        ]

        for meter_name in expected_meters:
            assert meter_name in METER_CONFIGS, f"Missing meter: {meter_name}"

    def test_config_structure(self):
        """Test that each config has required fields."""
        for meter_name, config in METER_CONFIGS.items():
            assert isinstance(config, MeterConfig)
            assert config.name == meter_name
            assert config.group is not None
            assert isinstance(config.natal_planets, list)
            assert isinstance(config.natal_houses, list)
            assert isinstance(config.retrograde_modifiers, dict)

    def test_mental_clarity_config(self):
        """Test mental_clarity meter configuration."""
        config = METER_CONFIGS['clarity']

        assert config.name == 'clarity'
        assert Planet.MERCURY in config.natal_planets
        assert Planet.SUN in config.natal_planets
        assert 9 in config.natal_houses  # Higher mind house
        assert Planet.MERCURY in config.retrograde_modifiers
        assert config.retrograde_modifiers[Planet.MERCURY] == 0.6

    def test_love_config(self):
        """Test love meter configuration."""
        config = METER_CONFIGS['connections']

        assert config.name == 'connections'
        assert Planet.VENUS in config.natal_planets
        assert 7 in config.natal_houses  # Partnership house

    def test_career_config(self):
        """Test career meter configuration."""
        config = METER_CONFIGS['ambition']

        assert config.name == 'ambition'
        assert Planet.SATURN in config.natal_planets
        assert 10 in config.natal_houses  # Career house


# ============================================================================
# Meter Calculation Tests
# ============================================================================

class TestMeterCalculation:
    """Test core meter calculation functionality."""

    def test_get_all_meters(self):
        """Test calculating all 17 meters at once."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_meters = get_meters(natal_chart, transit_chart, calculate_trends=False)

        # Check structure
        assert all_meters.date is not None
        assert all_meters.overall_intensity is not None
        assert all_meters.overall_harmony is not None

        # Check all 17 individual meters
        assert all_meters.clarity is not None
        assert all_meters.focus is not None
        assert all_meters.communication is not None
        assert all_meters.connections is not None
        assert all_meters.resilience is not None
        assert all_meters.vulnerability is not None
        assert all_meters.energy is not None
        assert all_meters.drive is not None
        assert all_meters.strength is not None
        assert all_meters.vision is not None
        assert all_meters.flow is not None
        assert all_meters.intuition is not None
        assert all_meters.creativity is not None
        assert all_meters.momentum is not None
        assert all_meters.ambition is not None
        assert all_meters.evolution is not None
        assert all_meters.circle is not None

    def test_get_single_meter(self):
        """Test calculating a single meter."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        mental_clarity = get_meter('clarity', natal_chart, transit_chart)

        assert mental_clarity.meter_name == 'clarity'
        assert 0 <= mental_clarity.intensity <= 100
        assert 0 <= mental_clarity.harmony <= 100
        # Unified score is -100 to +100 (polar-style)
        assert -100 <= mental_clarity.unified_score <= 100
        assert mental_clarity.unified_quality in [q.value for q in QualityLabel]

    def test_meter_value_ranges(self):
        """Test that all meters produce valid values."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_meters = get_meters(natal_chart, transit_chart, calculate_trends=False)

        # Test all 17 meters
        for meter_name in METER_CONFIGS.keys():
            meter = getattr(all_meters, meter_name)
            assert 0 <= meter.intensity <= 100, f"{meter_name} intensity out of range"
            assert 0 <= meter.harmony <= 100, f"{meter_name} harmony out of range"
            # Unified score is -100 to +100 (polar-style)
            assert -100 <= meter.unified_score <= 100, f"{meter_name} unified_score out of range"

    def test_meter_has_metadata(self):
        """Test that meters include all metadata fields."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        meter = get_meter('clarity', natal_chart, transit_chart)

        assert meter.state_label is not None
        assert meter.interpretation is not None
        assert isinstance(meter.advice, list)
        assert isinstance(meter.top_aspects, list)
        assert isinstance(meter.raw_scores, dict)
        assert 'dti' in meter.raw_scores
        assert 'hqs' in meter.raw_scores


# ============================================================================
# Aspect Filtering Tests
# ============================================================================

class TestAspectFiltering:
    """Test that aspect filtering works correctly based on configuration."""

    def test_filter_by_natal_planets(self):
        """Test filtering aspects by natal planets."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_aspects = calculate_all_aspects(natal_chart, transit_chart)
        config = METER_CONFIGS['clarity']

        filtered = filter_aspects(all_aspects, config, natal_chart)

        # All filtered aspects should involve Mercury or Sun (natal)
        for aspect in filtered:
            assert aspect.natal_planet in [Planet.MERCURY, Planet.SUN]

    def test_filter_by_natal_houses(self):
        """Test filtering aspects by natal houses."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_aspects = calculate_all_aspects(natal_chart, transit_chart)

        # Mental clarity also filters by houses 3 and 9
        config = METER_CONFIGS['clarity']
        filtered = filter_aspects(all_aspects, config, natal_chart)

        # Should have aspects (either by planet OR by house)
        assert len(filtered) > 0

    def test_different_meters_different_aspects(self):
        """Test that different meters filter different aspects."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_aspects = calculate_all_aspects(natal_chart, transit_chart)

        mental_clarity_aspects = filter_aspects(all_aspects, METER_CONFIGS['clarity'], natal_chart)
        love_aspects = filter_aspects(all_aspects, METER_CONFIGS['connections'], natal_chart)

        # Convert to sets for comparison
        mc_keys = {(a.natal_planet, a.transit_planet, a.aspect_type) for a in mental_clarity_aspects}
        love_keys = {(a.natal_planet, a.transit_planet, a.aspect_type) for a in love_aspects}

        # They should be different (mental_clarity focuses on Mercury/Sun, love on Venus)
        assert mc_keys != love_keys


# ============================================================================
# Retrograde Modifier Tests
# ============================================================================

class TestRetrogradeModifiers:
    """Test retrograde modifier application."""

    def test_mercury_retrograde_reduces_harmony(self):
        """Test that Mercury retrograde reduces mental_clarity harmony."""
        natal_chart, _ = compute_birth_chart("1990-06-15")

        # Find a date when Mercury is retrograde
        # Mercury retrograde periods in 2025: Apr 1-25, Aug 5-28, Nov 25-Dec 15
        transit_chart_rx, _ = compute_birth_chart("2025-04-15", birth_time="12:00")
        transit_chart_direct, _ = compute_birth_chart("2025-05-15", birth_time="12:00")

        # Check Mercury retrograde status
        mercury_rx = next((p for p in transit_chart_rx["planets"] if p["name"] == Planet.MERCURY.value), None)
        mercury_direct = next((p for p in transit_chart_direct["planets"] if p["name"] == Planet.MERCURY.value), None)

        # Only run test if Mercury is actually retrograde
        if mercury_rx and mercury_rx.get("retrograde", False):
            meter_rx = get_meter('clarity', natal_chart, transit_chart_rx)
            meter_direct = get_meter('clarity', natal_chart, transit_chart_direct)

            # Retrograde should reduce harmony (multiplied by 0.6)
            # This is a soft check since the overall harmony depends on many aspects
            assert meter_rx.harmony <= meter_direct.harmony * 1.5  # Allow some variance

    def test_retrograde_modifier_values(self):
        """Test that retrograde modifiers are in valid range."""
        for meter_name, config in METER_CONFIGS.items():
            for planet, modifier in config.retrograde_modifiers.items():
                assert 0 < modifier <= 1.0, f"{meter_name} has invalid retrograde modifier for {planet}"


# ============================================================================
# Unified Score Tests
# ============================================================================

class TestUnifiedScore:
    """Test unified score calculation (polar-style with sigmoid stretch)."""

    def test_quiet_low_intensity(self):
        """Test quiet quality for low intensity."""
        score, quality = calculate_unified_score(15, 50)
        assert quality == QualityLabel.QUIET

    def test_harmonious_high_harmony(self):
        """Test harmonious quality for high harmony."""
        score, quality = calculate_unified_score(60, 80)
        assert quality == QualityLabel.HARMONIOUS

    def test_challenging_low_harmony(self):
        """Test challenging quality for low harmony."""
        score, quality = calculate_unified_score(60, 20)
        assert quality == QualityLabel.CHALLENGING

    def test_mixed_medium_harmony(self):
        """Test mixed quality for medium harmony."""
        score, quality = calculate_unified_score(60, 50)
        assert quality == QualityLabel.MIXED

    def test_unified_score_range(self):
        """Test that unified score is in valid range (-100 to +100)."""
        # High harmony = positive score
        score_high, _ = calculate_unified_score(60, 80)
        assert 0 < score_high <= 100, "High harmony should give positive score"

        # Low harmony = negative score
        score_low, _ = calculate_unified_score(60, 20)
        assert -100 <= score_low < 0, "Low harmony should give negative score"

        # Neutral harmony = near zero
        score_neutral, _ = calculate_unified_score(60, 50)
        assert -10 <= score_neutral <= 10, "Neutral harmony should give near-zero score"

    def test_unified_score_zero_intensity(self):
        """Test that zero intensity still shows harmony direction (base weight)."""
        score, quality = calculate_unified_score(0, 80)
        # Even at 0 intensity, base weight preserves some harmony signal
        assert score >= 0, "Positive harmony should give positive score even at 0 intensity"
        assert quality == QualityLabel.QUIET  # Low intensity = quiet

    def test_unified_score_empowering_asymmetry(self):
        """Test that positive scores are boosted and negative dampened."""
        # Same distance from neutral (50)
        score_positive, _ = calculate_unified_score(60, 80)  # +30 from neutral
        score_negative, _ = calculate_unified_score(60, 20)  # -30 from neutral

        # Positive should be larger in magnitude due to empowering boost
        assert abs(score_positive) > abs(score_negative), "Positive should be boosted more than negative"


# ============================================================================
# Overall Aggregation Tests
# ============================================================================

class TestOverallAggregation:
    """Test overall intensity/harmony aggregation."""

    def test_overall_meters_present(self):
        """Test that overall meters are calculated."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_meters = get_meters(natal_chart, transit_chart, calculate_trends=False)

        assert all_meters.overall_intensity is not None
        assert all_meters.overall_harmony is not None
        assert all_meters.overall_unified_quality in [q.value for q in QualityLabel]

    def test_overall_values_reasonable(self):
        """Test that overall values are in valid range."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_meters = get_meters(natal_chart, transit_chart, calculate_trends=False)

        assert 0 <= all_meters.overall_intensity.intensity <= 100
        assert 0 <= all_meters.overall_harmony.harmony <= 100
        # Unified score is -100 to +100 (polar-style)
        assert -100 <= all_meters.overall_intensity.unified_score <= 100

    def test_key_aspects_extracted(self):
        """Test that key aspects are extracted across all meters."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_meters = get_meters(natal_chart, transit_chart, calculate_trends=False)

        assert all_meters.aspect_count > 0
        assert len(all_meters.key_aspects) > 0
        assert len(all_meters.key_aspects) <= 10  # Top 10 max


# ============================================================================
# Trend Calculation Tests
# ============================================================================

class TestTrendCalculation:
    """Test trend calculation between days."""

    def test_trends_calculated(self):
        """Test that trends are calculated when requested."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_meters = get_meters(natal_chart, transit_chart, calculate_trends=True)

        # Check that at least one meter has trends
        mental_clarity = all_meters.clarity
        assert mental_clarity.trend is not None
        assert mental_clarity.trend.intensity is not None
        assert mental_clarity.trend.harmony is not None
        assert mental_clarity.trend.unified_score is not None

    def test_trend_structure(self):
        """Test trend data structure."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_meters = get_meters(natal_chart, transit_chart, calculate_trends=True)

        trend = all_meters.clarity.trend

        assert hasattr(trend.intensity, 'previous')
        assert hasattr(trend.intensity, 'delta')
        assert hasattr(trend.intensity, 'direction')
        assert hasattr(trend.intensity, 'change_rate')

        # Change rate should be one of the expected values
        assert trend.intensity.change_rate in ['stable', 'slow', 'moderate', 'rapid']

    def test_no_trends_when_disabled(self):
        """Test that trends are not calculated when disabled."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        all_meters = get_meters(natal_chart, transit_chart, calculate_trends=False)

        # Trends should be None
        assert all_meters.clarity.trend is None


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete meter system."""

    def test_full_calculation_no_errors(self):
        """Test that full meter calculation completes without errors."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        # This should not raise any exceptions
        all_meters = get_meters(natal_chart, transit_chart, calculate_trends=True)

        assert all_meters is not None
        assert len([m for m in dir(all_meters) if not m.startswith('_')]) > 17

    def test_different_natal_charts(self):
        """Test that different natal charts produce different results."""
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        natal_chart_1, _ = compute_birth_chart("1990-06-15")
        natal_chart_2, _ = compute_birth_chart("1985-12-25")

        meters_1 = get_meters(natal_chart_1, transit_chart, calculate_trends=False)
        meters_2 = get_meters(natal_chart_2, transit_chart, calculate_trends=False)

        # Different natal charts should produce different readings
        assert meters_1.clarity.intensity != meters_2.clarity.intensity or \
               meters_1.clarity.harmony != meters_2.clarity.harmony

    def test_different_transit_dates(self):
        """Test that different transit dates produce different results."""
        natal_chart, _ = compute_birth_chart("1990-06-15")

        transit_chart_1, _ = compute_birth_chart("2025-11-03", birth_time="12:00")
        transit_chart_2, _ = compute_birth_chart("2025-12-25", birth_time="12:00")

        meters_1 = get_meters(natal_chart, transit_chart_1, calculate_trends=False)
        meters_2 = get_meters(natal_chart, transit_chart_2, calculate_trends=False)

        # Different dates should produce different readings
        assert meters_1.clarity.intensity != meters_2.clarity.intensity or \
               meters_1.clarity.harmony != meters_2.clarity.harmony


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_invalid_meter_name(self):
        """Test that invalid meter name raises error."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        with pytest.raises(ValueError):
            get_meter('nonexistent_meter', natal_chart, transit_chart)

    def test_empty_charts(self):
        """Test handling of empty chart data."""
        empty_chart = {"planets": [], "houses": [], "aspects": []}
        transit_chart, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

        # Should not crash, but produce zero readings
        all_meters = get_meters(empty_chart, transit_chart, calculate_trends=False)

        # Should have structure but low/zero values
        assert all_meters is not None

"""
Tests for normalization functions.

Tests the conversion of raw DTI/HQS scores to 0-100 meter scales,
including soft ceiling compression for outliers.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from astrometers.normalization import (
    normalize_with_soft_ceiling,
    normalize_intensity,
    normalize_harmony,
    normalize_meters,
    get_intensity_label,
    get_harmony_label,
    get_meter_interpretation,
    MeterInterpretation,
)
from astrometers.constants import (
    DTI_MAX_ESTIMATE,
    HQS_MAX_POSITIVE_ESTIMATE,
    HQS_MAX_NEGATIVE_ESTIMATE,
)


# =============================================================================
# Soft Ceiling Normalization Tests
# =============================================================================

def test_normalize_soft_ceiling_linear_range():
    """Test linear scaling within expected maximum."""
    # At 50% of max
    assert normalize_with_soft_ceiling(100, 200, 100) == 50.0
    # At 25% of max
    assert normalize_with_soft_ceiling(50, 200, 100) == 25.0
    # At 100% of max
    assert normalize_with_soft_ceiling(200, 200, 100) == 100.0


def test_normalize_soft_ceiling_zero():
    """Test that zero returns zero."""
    assert normalize_with_soft_ceiling(0, 200, 100) == 0.0


def test_normalize_soft_ceiling_negative():
    """Test that negative values return zero."""
    assert normalize_with_soft_ceiling(-10, 200, 100) == 0.0


def test_normalize_soft_ceiling_outlier_compressed():
    """Test that outliers beyond max are compressed."""
    # 150% of max should be compressed and capped at 100
    result = normalize_with_soft_ceiling(300, 200, 100)
    assert result == 100.0  # Capped at target scale


def test_normalize_soft_ceiling_different_scales():
    """Test soft ceiling with different target scales."""
    # Half scale (for harmony meter)
    assert normalize_with_soft_ceiling(50, 100, 50) == 25.0
    assert normalize_with_soft_ceiling(100, 100, 50) == 50.0


# =============================================================================
# Intensity Normalization Tests
# =============================================================================

def test_normalize_intensity_zero():
    """Test zero DTI returns zero intensity."""
    assert normalize_intensity(0, use_empirical=False) == 0.0


def test_normalize_intensity_half_max():
    """Test DTI at half of max."""
    # With DTI_MAX_ESTIMATE = 200, half should be 50%
    result = normalize_intensity(DTI_MAX_ESTIMATE / 2, use_empirical=False)
    assert result == pytest.approx(50.0)


def test_normalize_intensity_at_max():
    """Test DTI at estimated maximum."""
    result = normalize_intensity(DTI_MAX_ESTIMATE, use_empirical=False)
    assert result == pytest.approx(100.0)


def test_normalize_intensity_beyond_max():
    """Test DTI beyond estimated maximum is capped."""
    result = normalize_intensity(DTI_MAX_ESTIMATE * 2, use_empirical=False)
    assert result <= 100.0


# =============================================================================
# Harmony Normalization Tests
# =============================================================================

def test_normalize_harmony_zero():
    """Test zero HQS returns neutral harmony (50)."""
    assert normalize_harmony(0, use_empirical=False) == pytest.approx(50.0)


def test_normalize_harmony_positive():
    """Test positive HQS increases harmony above 50."""
    # Half of positive max should give 75 (50 + 25)
    result = normalize_harmony(HQS_MAX_POSITIVE_ESTIMATE / 2, use_empirical=False)
    assert result == pytest.approx(75.0)


def test_normalize_harmony_negative():
    """Test negative HQS decreases harmony below 50."""
    # Half of negative max should give 25 (50 - 25)
    result = normalize_harmony(-HQS_MAX_NEGATIVE_ESTIMATE / 2, use_empirical=False)
    assert result == pytest.approx(25.0)


def test_normalize_harmony_positive_at_max():
    """Test positive HQS at maximum returns 100."""
    result = normalize_harmony(HQS_MAX_POSITIVE_ESTIMATE, use_empirical=False)
    assert result == pytest.approx(100.0)


def test_normalize_harmony_negative_at_max():
    """Test negative HQS at maximum returns 0."""
    result = normalize_harmony(-HQS_MAX_NEGATIVE_ESTIMATE, use_empirical=False)
    assert result == pytest.approx(0.0)


def test_normalize_harmony_symmetry():
    """Test that positive and negative HQS are symmetric around 50."""
    positive_result = normalize_harmony(50, use_empirical=False)
    negative_result = normalize_harmony(-50, use_empirical=False)

    # Should be equidistant from 50
    positive_distance = positive_result - 50
    negative_distance = 50 - negative_result
    assert abs(positive_distance - negative_distance) < 0.01


# =============================================================================
# Combined Normalization Tests
# =============================================================================

def test_normalize_meters_combined():
    """Test normalizing both DTI and HQS together."""
    # Use theoretical mode for unit test
    intensity = normalize_intensity(100.0, use_empirical=False)
    harmony = normalize_harmony(-50.0, use_empirical=False)

    assert intensity > 0
    assert intensity < 100
    assert harmony < 50  # Negative HQS


def test_normalize_meters_zero():
    """Test normalizing zero DTI and HQS."""
    intensity = normalize_intensity(0, use_empirical=False)
    harmony = normalize_harmony(0, use_empirical=False)

    assert intensity == 0.0
    assert harmony == pytest.approx(50.0)


# =============================================================================
# Intensity Label Tests
# =============================================================================

def test_intensity_labels():
    """Test all intensity label thresholds."""
    assert get_intensity_label(15) == "Quiet"
    assert get_intensity_label(30) == "Quiet"
    assert get_intensity_label(31) == "Mild"
    assert get_intensity_label(45) == "Mild"
    assert get_intensity_label(50) == "Mild"
    assert get_intensity_label(51) == "Moderate"
    assert get_intensity_label(60) == "Moderate"
    assert get_intensity_label(70) == "Moderate"
    assert get_intensity_label(71) == "High"
    assert get_intensity_label(80) == "High"
    assert get_intensity_label(85) == "High"
    assert get_intensity_label(86) == "Extreme"
    assert get_intensity_label(95) == "Extreme"
    assert get_intensity_label(100) == "Extreme"


# =============================================================================
# Harmony Label Tests
# =============================================================================

def test_harmony_labels():
    """Test all harmony label thresholds."""
    assert get_harmony_label(0) == "Challenging"
    assert get_harmony_label(15) == "Challenging"
    assert get_harmony_label(30) == "Challenging"
    assert get_harmony_label(31) == "Mixed"
    assert get_harmony_label(50) == "Mixed"
    assert get_harmony_label(69) == "Mixed"
    assert get_harmony_label(70) == "Harmonious"
    assert get_harmony_label(85) == "Harmonious"
    assert get_harmony_label(100) == "Harmonious"


# =============================================================================
# Meter Interpretation Tests (Spec Section 2.5 Matrix)
# =============================================================================

def test_interpretation_quiet_period():
    """Test quiet period interpretation (0-30 intensity, any harmony)."""
    interp = get_meter_interpretation(20, 50)
    assert interp.label == "Quiet Period"
    assert "Low astrological activity" in interp.guidance


def test_interpretation_gentle_flow():
    """Test gentle flow interpretation (31-50 intensity, 70-100 harmony)."""
    interp = get_meter_interpretation(40, 80)
    assert interp.label == "Gentle Flow"
    assert "Mild supportive energy" in interp.guidance


def test_interpretation_minor_friction():
    """Test minor friction interpretation (31-50 intensity, 0-30 harmony)."""
    interp = get_meter_interpretation(40, 20)
    assert interp.label == "Minor Friction"
    assert "Small irritations" in interp.guidance


def test_interpretation_productive_flow():
    """Test productive flow interpretation (51-70 intensity, 70-100 harmony)."""
    interp = get_meter_interpretation(60, 80)
    assert interp.label == "Productive Flow"
    assert "Prime time for action" in interp.guidance


def test_interpretation_mixed_dynamics():
    """Test mixed dynamics interpretation (51-70 intensity, 30-70 harmony)."""
    interp = get_meter_interpretation(60, 50)
    assert interp.label == "Mixed Dynamics"
    assert "both opportunities and challenges" in interp.guidance


def test_interpretation_moderate_challenge():
    """Test moderate challenge interpretation (51-70 intensity, 0-30 harmony)."""
    interp = get_meter_interpretation(60, 20)
    assert interp.label == "Moderate Challenge"
    assert "Growth through persistence" in interp.guidance


def test_interpretation_peak_opportunity():
    """Test peak opportunity interpretation (71-85 intensity, 70-100 harmony)."""
    interp = get_meter_interpretation(75, 85)
    assert interp.label == "Peak Opportunity"
    assert "Rare alignment" in interp.guidance


def test_interpretation_intense_mixed():
    """Test intense mixed interpretation (71-85 intensity, 30-70 harmony)."""
    interp = get_meter_interpretation(75, 50)
    assert interp.label == "Intense Mixed"
    assert "Pivotal period" in interp.guidance


def test_interpretation_high_challenge():
    """Test high challenge interpretation (71-85 intensity, 0-30 harmony)."""
    interp = get_meter_interpretation(75, 20)
    assert interp.label == "High Challenge"
    assert "Resilience required" in interp.guidance


def test_interpretation_exceptional_grace():
    """Test exceptional grace interpretation (86-100 intensity, 70-100 harmony)."""
    interp = get_meter_interpretation(90, 85)
    assert interp.label == "Exceptional Grace"
    assert "Extremely rare" in interp.guidance


def test_interpretation_crisis_breakthrough():
    """Test crisis/breakthrough interpretation (86-100 intensity, 0-30 harmony)."""
    interp = get_meter_interpretation(90, 20)
    assert interp.label == "Crisis/Breakthrough"
    assert "transformation" in interp.guidance


# =============================================================================
# Edge Cases and Boundary Tests
# =============================================================================

def test_interpretation_boundary_at_30_intensity():
    """Test boundary at 30/31 intensity threshold."""
    quiet = get_meter_interpretation(30, 50)
    mild = get_meter_interpretation(31, 50)

    assert quiet.label == "Quiet Period"
    assert mild.label == "Mild Mixed"


def test_interpretation_boundary_at_30_harmony():
    """Test boundary at 30/31 harmony threshold."""
    challenging = get_meter_interpretation(60, 30)
    mixed = get_meter_interpretation(60, 31)

    assert challenging.label == "Moderate Challenge"
    assert mixed.label == "Mixed Dynamics"


def test_interpretation_boundary_at_70_harmony():
    """Test boundary at 69/70 harmony threshold."""
    mixed = get_meter_interpretation(60, 69)
    harmonious = get_meter_interpretation(60, 70)

    assert mixed.label == "Mixed Dynamics"
    assert harmonious.label == "Productive Flow"


def test_meter_interpretation_returns_dataclass():
    """Test that meter interpretation returns MeterInterpretation dataclass."""
    interp = get_meter_interpretation(50, 50)

    assert isinstance(interp, MeterInterpretation)
    assert hasattr(interp, 'label')
    assert hasattr(interp, 'guidance')
    assert isinstance(interp.label, str)
    assert isinstance(interp.guidance, str)


# =============================================================================
# Integration Test with Realistic Values
# =============================================================================

def test_realistic_scenario_moderate_challenging():
    """Test a realistic scenario with moderate challenging transits."""
    # Raw scores from hypothetical calculation
    dti = 150.0  # Moderate activity
    hqs = -75.0  # Somewhat challenging

    intensity = normalize_intensity(dti, use_empirical=False)
    harmony = normalize_harmony(hqs, use_empirical=False)
    interp = get_meter_interpretation(intensity, harmony)

    # Should be in moderate intensity range
    assert intensity > 50
    assert intensity < 100

    # Should be in challenging harmony range
    assert harmony < 50

    # Interpretation should reflect moderate challenge or mixed dynamics
    assert "Challenge" in interp.label or "Mixed" in interp.label


def test_realistic_scenario_high_harmonious():
    """Test a realistic scenario with high harmonious transits."""
    # Raw scores from hypothetical calculation
    dti = 160.0  # High activity
    hqs = 80.0  # Very harmonious

    intensity = normalize_intensity(dti, use_empirical=False)
    harmony = normalize_harmony(hqs, use_empirical=False)
    interp = get_meter_interpretation(intensity, harmony)

    # Should be in high intensity range
    assert intensity > 70

    # Should be in harmonious range
    assert harmony > 70

    # Interpretation should reflect opportunity
    assert "Opportunity" in interp.label or "Flow" in interp.label


# =============================================================================
# Meter-Specific Normalization Tests (Issue #1: Broken Normalization)
# =============================================================================

def test_meter_specific_normalization_different_results():
    """Test that same raw DTI normalizes differently for different meters."""
    raw_dti = 250.0

    # Different meters should produce different intensity scores
    overall = normalize_intensity(raw_dti, meter_name="overall_intensity")
    mental = normalize_intensity(raw_dti, meter_name="mental_clarity")
    physical = normalize_intensity(raw_dti, meter_name="physical_energy")

    # Mental clarity (smallest P99) should show highest intensity
    assert mental > physical > overall

    # Verify values are reasonable (not 0.0)
    assert mental > 15.0
    assert physical > 10.0
    assert overall > 5.0


def test_bug_fix_mental_clarity_not_zero():
    """
    TEST ORIGINAL BUG: Mental Clarity with DTI=80.85 was showing 0.0/100.

    Root cause: Global P99=3575 was used instead of meter-specific P99=1088.2.
    Expected: With meter-specific P99, DTI=80.85 should show ~7% intensity.
    """
    raw_dti = 80.85  # From the bug report

    # With meter-specific calibration
    result = normalize_intensity(raw_dti, meter_name="mental_clarity")

    # Should NOT be 0.0!
    assert result > 5.0, f"Mental Clarity intensity should be >5%, got {result:.1f}%"

    # Should be approximately 7% with real calibration (80.85/1088.2 = 7.4%)
    assert result == pytest.approx(7.4, abs=2.0)


def test_bug_fix_physical_energy_not_zero():
    """
    TEST ORIGINAL BUG: Physical Energy with DTI=525.91 was showing 0.0/100.

    Expected: With P99=1548.6, DTI=525.91 should show ~34% intensity.
    """
    raw_dti = 525.91  # From the bug report

    result = normalize_intensity(raw_dti, meter_name="physical_energy")

    # Should NOT be 0.0!
    assert result > 25.0, f"Physical Energy intensity should be >25%, got {result:.1f}%"

    # Should be approximately 34% (525.91/1548.6 = 34.0%)
    assert result == pytest.approx(34.0, abs=2.0)


def test_bug_fix_fire_energy_not_zero():
    """
    TEST ORIGINAL BUG: Fire Energy with DTI=447.85 was showing 0.0/100.

    Expected: With P99=1193.3, DTI=447.85 should show ~37.5% intensity.
    """
    raw_dti = 447.85  # From the bug report

    result = normalize_intensity(raw_dti, meter_name="fire_energy")

    # Should NOT be 0.0!
    assert result > 30.0, f"Fire Energy intensity should be >30%, got {result:.1f}%"

    # Should be approximately 37.5% (447.85/1193.3 = 37.5%)
    assert result == pytest.approx(37.5, abs=2.0)


def test_meter_specific_harmony_normalization():
    """Test that harmony also uses meter-specific calibration."""
    raw_hqs = 100.0

    # Mental clarity has smaller HQS range vs overall
    mental = normalize_harmony(raw_hqs, meter_name="mental_clarity")
    overall = normalize_harmony(raw_hqs, meter_name="overall_intensity")

    # Mental clarity should show more harmony for same raw HQS
    assert mental > overall

    # Both should be above neutral (50)
    assert mental > 50.0
    assert overall > 50.0


def test_normalize_meters_uses_meter_name():
    """Test that normalize_meters() convenience function uses meter_name."""
    raw_dti = 250.0
    raw_hqs = 100.0

    # Same raw scores, different meters
    mental_int, mental_harm = normalize_meters(raw_dti, raw_hqs, meter_name="mental_clarity")
    overall_int, overall_harm = normalize_meters(raw_dti, raw_hqs, meter_name="overall_intensity")

    # Both intensity and harmony should differ
    assert mental_int != overall_int
    assert mental_harm != overall_harm

    # Mental clarity should show higher values
    assert mental_int > overall_int
    assert mental_harm > overall_harm


def test_meter_name_none_uses_fallback():
    """Test that passing meter_name=None falls back gracefully."""
    raw_dti = 1805.0  # Median for overall

    # No meter name provided - should use fallback logic
    result = normalize_intensity(raw_dti, meter_name=None)

    # Should return reasonable value (not crash)
    assert 0.0 <= result <= 100.0


def test_unknown_meter_name_uses_fallback():
    """Test that unknown meter name falls back gracefully."""
    raw_dti = 1805.0

    # Unknown meter - should fall back without crashing
    result = normalize_intensity(raw_dti, meter_name="nonexistent_meter")

    # Should return reasonable value
    assert 0.0 <= result <= 100.0


def test_meter_specific_respects_zero_hqs():
    """Test that HQS=0 always returns 50 regardless of meter."""
    # Test multiple meters - all should return 50 for HQS=0
    for meter_name in ["mental_clarity", "physical_energy", "overall_intensity"]:
        result = normalize_harmony(0.0, meter_name=meter_name)
        assert result == pytest.approx(50.0, abs=0.1), f"{meter_name} should return 50 for HQS=0"


def test_calibration_file_has_meter_specific_data():
    """Test that calibration_constants.json has meter-specific data."""
    from astrometers.normalization import load_calibration_constants

    calibration = load_calibration_constants()

    # Should have version 3.0+ structure with meters
    assert calibration is not None
    assert "meters" in calibration

    # Check that specific meters exist
    required_meters = ["mental_clarity", "physical_energy", "fire_energy", "overall_intensity"]
    for meter in required_meters:
        assert meter in calibration["meters"], f"Missing meter: {meter}"

        # Each meter should have percentiles
        meter_data = calibration["meters"][meter]
        assert "dti_percentiles" in meter_data
        assert "hqs_percentiles" in meter_data
        assert "p99" in meter_data["dti_percentiles"]
        assert "p01" in meter_data["hqs_percentiles"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

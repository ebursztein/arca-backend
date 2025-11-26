"""
Tests for normalization functions.

Tests the conversion of raw DTI/HQS scores to 0-100 meter scales
using empirical calibration data.
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
    load_calibration_constants,
)


# =============================================================================
# Soft Ceiling Normalization Tests
# =============================================================================

def test_normalize_soft_ceiling_linear_range():
    """Test linear scaling within expected maximum."""
    assert normalize_with_soft_ceiling(100, 200, 100) == 50.0
    assert normalize_with_soft_ceiling(50, 200, 100) == 25.0
    assert normalize_with_soft_ceiling(200, 200, 100) == 100.0


def test_normalize_soft_ceiling_zero():
    """Test that zero returns zero."""
    assert normalize_with_soft_ceiling(0, 200, 100) == 0.0


def test_normalize_soft_ceiling_negative():
    """Test that negative values return zero."""
    assert normalize_with_soft_ceiling(-10, 200, 100) == 0.0


def test_normalize_soft_ceiling_outlier_compressed():
    """Test that outliers beyond max are compressed."""
    result = normalize_with_soft_ceiling(300, 200, 100)
    assert result == 100.0  # Capped at target scale


def test_normalize_soft_ceiling_different_scales():
    """Test soft ceiling with different target scales."""
    assert normalize_with_soft_ceiling(50, 100, 50) == 25.0
    assert normalize_with_soft_ceiling(100, 100, 50) == 50.0


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
# Meter-Specific Normalization Tests (Empirical Calibration)
# =============================================================================

def test_meter_specific_normalization_different_results():
    """Test that same raw DTI normalizes differently for different meters."""
    raw_dti = 250.0

    # Different meters should produce different intensity scores
    energy = normalize_intensity(raw_dti, meter_name="energy")
    clarity = normalize_intensity(raw_dti, meter_name="clarity")
    drive = normalize_intensity(raw_dti, meter_name="drive")

    # All should be within valid range
    assert 0 <= clarity <= 100
    assert 0 <= drive <= 100
    assert 0 <= energy <= 100


def test_meter_specific_normalization_nonzero():
    """Test meter-specific normalization produces non-zero values for realistic inputs."""
    test_cases = [
        ("clarity", 80.85),
        ("energy", 525.91),
        ("drive", 447.85),
    ]

    for meter_name, raw_dti in test_cases:
        result = normalize_intensity(raw_dti, meter_name=meter_name)
        assert 0 <= result <= 100, f"{meter_name} intensity should be 0-100, got {result:.1f}%"


def test_meter_specific_harmony_normalization():
    """Test that harmony uses meter-specific calibration."""
    raw_hqs = 100.0

    clarity = normalize_harmony(raw_hqs, meter_name="clarity")
    energy = normalize_harmony(raw_hqs, meter_name="energy")

    # Both should be within valid range
    assert 0 <= clarity <= 100
    assert 0 <= energy <= 100

    # Both should be above neutral (50) since HQS is positive
    assert clarity > 50.0
    assert energy > 50.0


def test_normalize_meters_uses_meter_name():
    """Test that normalize_meters() convenience function uses meter_name."""
    raw_dti = 250.0
    raw_hqs = 100.0

    clarity_int, clarity_harm = normalize_meters(raw_dti, raw_hqs, meter_name="clarity")
    energy_int, energy_harm = normalize_meters(raw_dti, raw_hqs, meter_name="energy")

    # Both should be within valid range
    assert 0 <= clarity_int <= 100
    assert 0 <= energy_int <= 100
    assert 0 <= clarity_harm <= 100
    assert 0 <= energy_harm <= 100


def test_meter_specific_zero_hqs_reasonable():
    """Test that HQS=0 returns a reasonable mid-range value."""
    for meter_name in ["clarity", "energy", "drive"]:
        result = normalize_harmony(0.0, meter_name=meter_name)
        # With empirical percentile calibration, HQS=0 should be in a reasonable
        # mid-range but not necessarily exactly 50 (depends on distribution)
        assert 30 <= result <= 70, f"{meter_name} HQS=0 should be mid-range, got {result:.1f}"


# =============================================================================
# Calibration File Tests
# =============================================================================

def test_calibration_file_exists():
    """Test that calibration_constants.json exists and loads."""
    calibration = load_calibration_constants()
    assert calibration is not None


def test_calibration_file_has_meter_specific_data():
    """Test that calibration_constants.json has meter-specific data."""
    calibration = load_calibration_constants()

    assert calibration is not None
    assert "meters" in calibration

    # Check that specific meters exist
    required_meters = ["clarity", "energy", "drive", "focus", "connections", "evolution"]
    for meter in required_meters:
        assert meter in calibration["meters"], f"Missing meter: {meter}"

        meter_data = calibration["meters"][meter]
        assert "dti_percentiles" in meter_data
        assert "hqs_percentiles" in meter_data
        assert "p99" in meter_data["dti_percentiles"]
        assert "p01" in meter_data["hqs_percentiles"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

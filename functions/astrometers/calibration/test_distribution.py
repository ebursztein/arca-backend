"""
Unit tests for empirical distribution validation.

Tests that normalized scores have expected statistical properties:
- Median around 50 (for intensity)
- Standard deviation reasonable (not too compressed or spread)
- P99 actually maps to ~100
- Distribution is well-calibrated

Usage:
    cd /Users/elie/git/arca/arca-backend
    uv run pytest functions/astrometers/calibration/test_distribution.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from astrometers.normalization import (
    normalize_intensity,
    normalize_harmony,
    load_calibration_constants
)


@pytest.fixture(scope="module")
def historical_scores():
    """Load historical scores for testing."""
    scores_path = os.path.join(
        os.path.dirname(__file__),
        "historical_scores.parquet"
    )
    return pd.read_parquet(scores_path)


@pytest.fixture(scope="module")
def calibration_constants():
    """Load calibration constants."""
    return load_calibration_constants()


class TestCalibrationConstants:
    """Test that calibration constants are loaded correctly."""

    def test_calibration_loaded(self, calibration_constants):
        """Calibration file should load successfully."""
        assert calibration_constants is not None
        assert "dti_percentiles" in calibration_constants
        assert "hqs_percentiles" in calibration_constants

    def test_dti_percentiles_exist(self, calibration_constants):
        """All DTI percentiles should exist."""
        dti = calibration_constants["dti_percentiles"]
        required = ["p01", "p05", "p10", "p25", "p50", "p75", "p90", "p95", "p99"]
        for p in required:
            assert p in dti
            assert dti[p] > 0

    def test_dti_percentiles_ordered(self, calibration_constants):
        """DTI percentiles should be in ascending order."""
        dti = calibration_constants["dti_percentiles"]
        assert dti["p01"] < dti["p05"] < dti["p10"] < dti["p25"]
        assert dti["p25"] < dti["p50"] < dti["p75"] < dti["p90"]
        assert dti["p90"] < dti["p95"] < dti["p99"]

    def test_hqs_percentiles_exist(self, calibration_constants):
        """All HQS percentiles should exist."""
        hqs = calibration_constants["hqs_percentiles"]
        required = ["p01", "p05", "p10", "p25", "p50", "p75", "p90", "p95", "p99"]
        for p in required:
            assert p in hqs

    def test_hqs_percentiles_ordered(self, calibration_constants):
        """HQS percentiles should be in ascending order."""
        hqs = calibration_constants["hqs_percentiles"]
        assert hqs["p01"] < hqs["p05"] < hqs["p10"] < hqs["p25"]
        assert hqs["p25"] < hqs["p50"] < hqs["p75"] < hqs["p90"]
        assert hqs["p90"] < hqs["p95"] < hqs["p99"]


class TestDTINormalization:
    """Test DTI normalization properties."""

    def test_normalize_intensity_zero(self):
        """Zero DTI should normalize to 0."""
        assert normalize_intensity(0.0) == 0.0

    def test_normalize_intensity_p50(self, calibration_constants):
        """P50 DTI should normalize to ~50."""
        p50 = calibration_constants["dti_percentiles"]["p50"]
        normalized = normalize_intensity(p50)
        assert 48.0 <= normalized <= 52.0, f"P50 normalized to {normalized}, expected ~50"

    def test_normalize_intensity_p99(self, calibration_constants):
        """P99 DTI should normalize to 100."""
        p99 = calibration_constants["dti_percentiles"]["p99"]
        normalized = normalize_intensity(p99)
        assert 99.0 <= normalized <= 100.0, f"P99 normalized to {normalized}, expected 100"

    def test_normalize_intensity_p90(self, calibration_constants):
        """P90 DTI should normalize to ~90 (percentile-based)."""
        p90 = calibration_constants["dti_percentiles"]["p90"]
        normalized = normalize_intensity(p90)
        assert 87.0 <= normalized <= 93.0, f"P90 normalized to {normalized}, expected ~90"

    def test_normalize_intensity_distribution(self, historical_scores):
        """Normalized intensity should have percentile-based distribution."""
        # Normalize all DTI values
        normalized = historical_scores['dti'].apply(normalize_intensity)

        # With percentile-based normalization, each percentile should map to itself
        # Check median is around 50
        median = normalized.median()
        assert 48.0 <= median <= 52.0, f"Median normalized intensity: {median}, expected ~50"

        # Check that P99 is around 99
        p99 = np.percentile(normalized, 99)
        assert 97.0 <= p99 <= 100.0, f"P99 normalized intensity: {p99}, expected ~99"

        # Check that P90 is around 90
        p90 = np.percentile(normalized, 90)
        assert 87.0 <= p90 <= 93.0, f"P90 normalized intensity: {p90}, expected ~90"

        # Check that P10 is around 10
        p10 = np.percentile(normalized, 10)
        assert 7.0 <= p10 <= 13.0, f"P10 normalized intensity: {p10}, expected ~10"

    def test_normalize_intensity_reasonable_stddev(self, historical_scores):
        """Normalized intensity should have uniform-like spread (percentile-based)."""
        normalized = historical_scores['dti'].apply(normalize_intensity)
        stddev = normalized.std()

        # Percentile-based normalization produces near-uniform distribution
        # Expected stddev for uniform [0,100]: ~28.9 (100/sqrt(12))
        assert 25.0 <= stddev <= 32.0, f"Std dev: {stddev}, expected 25-32 (uniform-like)"

    def test_normalize_intensity_no_values_above_100(self, historical_scores):
        """No normalized values should exceed 100."""
        normalized = historical_scores['dti'].apply(normalize_intensity)
        assert normalized.max() <= 100.0, f"Max normalized: {normalized.max()}, should be ≤100"

    def test_normalize_intensity_rare_extreme(self, historical_scores):
        """'Extreme' label (≥86) should be rare (~1-5%)."""
        normalized = historical_scores['dti'].apply(normalize_intensity)
        extreme_count = (normalized >= 86).sum()
        extreme_pct = extreme_count / len(normalized) * 100

        assert extreme_pct <= 5.0, f"Extreme: {extreme_pct:.1f}%, should be ≤5%"


class TestHQSNormalization:
    """Test HQS normalization properties."""

    def test_normalize_harmony_zero(self):
        """Zero HQS should normalize to 50 (neutral)."""
        assert normalize_harmony(0.0) == 50.0

    def test_normalize_harmony_p50(self, calibration_constants):
        """P50 HQS should normalize close to median harmony."""
        p50 = calibration_constants["hqs_percentiles"]["p50"]
        normalized = normalize_harmony(p50)

        # P50 is slightly negative (-200), so should be slightly below 50
        assert 40.0 <= normalized <= 50.0, f"P50 normalized to {normalized}"

    def test_normalize_harmony_p99_positive(self, calibration_constants):
        """P99 positive HQS should normalize to 100."""
        p99 = calibration_constants["hqs_percentiles"]["p99"]
        normalized = normalize_harmony(p99)
        assert 99.0 <= normalized <= 100.0, f"P99+ normalized to {normalized}, expected 100"

    def test_normalize_harmony_p01_negative(self, calibration_constants):
        """P01 negative HQS should normalize to 0."""
        p01 = calibration_constants["hqs_percentiles"]["p01"]
        normalized = normalize_harmony(p01)
        assert 0.0 <= normalized <= 1.0, f"P01 normalized to {normalized}, expected 0"

    def test_normalize_harmony_distribution(self, historical_scores):
        """Normalized harmony should have expected distribution."""
        # Normalize all HQS values
        normalized = historical_scores['hqs'].apply(normalize_harmony)

        # Check median is close to expected
        median = normalized.median()
        # Since real median is negative (-200), expect normalized median below 50
        assert 40.0 <= median <= 50.0, f"Median normalized harmony: {median}"

        # Check that P99 is around 100
        p99 = np.percentile(normalized, 99)
        assert 98.0 <= p99 <= 100.0, f"P99 normalized harmony: {p99}, expected ~100"

        # Check that P01 is around 0
        p01 = np.percentile(normalized, 1)
        assert 0.0 <= p01 <= 2.0, f"P01 normalized harmony: {p01}, expected ~0"

    def test_normalize_harmony_asymmetry(self):
        """HQS normalization reflects real-world asymmetry."""
        pos_500 = normalize_harmony(500.0)
        neg_500 = normalize_harmony(-500.0)

        # Real data shows more negative range (P01=-1438 vs P99=+748)
        # So equal magnitudes will NOT be symmetric
        pos_distance = pos_500 - 50
        neg_distance = 50 - neg_500

        # Positive should compress less than negative due to smaller range
        assert pos_distance > neg_distance, \
            f"Expected asymmetry: +500→{pos_500}, -500→{neg_500}"

    def test_normalize_harmony_challenging_percentage(self, historical_scores):
        """Challenging harmony (<30) should match expected percentage."""
        normalized = historical_scores['hqs'].apply(normalize_harmony)
        challenging = (normalized < 30).sum()
        challenging_pct = challenging / len(normalized) * 100

        # Based on empirical data, expect significant challenging periods
        assert 10.0 <= challenging_pct <= 40.0, \
            f"Challenging: {challenging_pct:.1f}%, expected 10-40%"

    def test_normalize_harmony_harmonious_percentage(self, historical_scores):
        """Harmonious harmony (>70) should match expected percentage."""
        normalized = historical_scores['hqs'].apply(normalize_harmony)
        harmonious = (normalized > 70).sum()
        harmonious_pct = harmonious / len(normalized) * 100

        # Based on empirical data, expect fewer harmonious periods
        assert 5.0 <= harmonious_pct <= 25.0, \
            f"Harmonious: {harmonious_pct:.1f}%, expected 5-25%"


class TestNormalizationAccuracy:
    """Test overall normalization accuracy."""

    def test_intensity_percentile_accuracy(self, historical_scores, calibration_constants):
        """Normalized intensity percentiles should match score values (percentile-based normalization)."""
        normalized = historical_scores['dti'].apply(normalize_intensity)

        # With percentile-based normalization, score X should equal percentile X
        # e.g., normalized score of 85 means P85 (top 15% of days)
        test_cases = [
            (10, 10, 3),  # P10 normalized to ~10
            (25, 25, 3),  # P25 normalized to ~25
            (50, 50, 3),  # P50 (median) normalized to ~50
            (75, 75, 3),  # P75 normalized to ~75
            (85, 85, 3),  # P85 normalized to ~85 (top 15%)
            (90, 90, 3),  # P90 normalized to ~90
            (95, 95, 3),  # P95 normalized to ~95
            (99, 99, 2),  # P99 normalized to ~99 (top 1%)
        ]

        for percentile, expected_norm, tolerance in test_cases:
            actual_norm = np.percentile(normalized, percentile)

            assert expected_norm - tolerance <= actual_norm <= expected_norm + tolerance, \
                f"P{percentile} normalized to {actual_norm:.1f}, expected ~{expected_norm}±{tolerance}"

    def test_harmony_center_at_50(self, historical_scores):
        """Harmony distribution should be centered around neutral (50)."""
        normalized = historical_scores['hqs'].apply(normalize_harmony)

        # Mean should be reasonably close to 50 (within 10 points)
        mean = normalized.mean()
        assert 40.0 <= mean <= 60.0, f"Mean harmony: {mean:.1f}, expected 40-60"

    def test_no_nan_values(self, historical_scores):
        """Normalization should never produce NaN values."""
        dti_normalized = historical_scores['dti'].apply(normalize_intensity)
        hqs_normalized = historical_scores['hqs'].apply(normalize_harmony)

        assert not dti_normalized.isna().any(), "DTI normalization produced NaN"
        assert not hqs_normalized.isna().any(), "HQS normalization produced NaN"

    def test_fallback_to_theoretical(self):
        """When calibration unavailable, should fall back to theoretical."""
        # Test with empirical disabled
        intensity = normalize_intensity(100.0, use_empirical=False)
        harmony = normalize_harmony(50.0, use_empirical=False)

        # Should still return valid values
        assert 0.0 <= intensity <= 100.0
        assert 0.0 <= harmony <= 100.0


class TestRealWorldScenarios:
    """Test real-world score scenarios."""

    def test_quiet_day_scores(self):
        """Quiet day (low DTI) should normalize to low intensity."""
        # Use P10 value as example of quiet day
        quiet_dti = 1185.63  # From calibration P10
        normalized = normalize_intensity(quiet_dti)

        assert normalized < 40.0, f"Quiet day DTI normalized to {normalized}, expected <40"

    def test_extreme_day_scores(self):
        """Extreme day (P99+ DTI) should normalize to 90-100."""
        # Use value above P99
        extreme_dti = 4000.0  # Above P99 (3575.73)
        normalized = normalize_intensity(extreme_dti)

        assert normalized >= 90.0, f"Extreme day DTI normalized to {normalized}, expected ≥90"

    def test_typical_day_scores(self):
        """Typical day (median DTI) should normalize to 40-60."""
        median_dti = 1805.47  # From calibration P50
        normalized = normalize_intensity(median_dti)

        assert 40.0 <= normalized <= 60.0, \
            f"Typical day DTI normalized to {normalized}, expected 40-60"

    def test_harmonious_day(self):
        """Harmonious day (positive HQS) should be above 50."""
        harmonious_hqs = 500.0  # Positive HQS
        normalized = normalize_harmony(harmonious_hqs)

        assert normalized > 50.0, f"Harmonious HQS normalized to {normalized}, expected >50"

    def test_challenging_day(self):
        """Challenging day (negative HQS) should be below 50."""
        challenging_hqs = -500.0  # Negative HQS
        normalized = normalize_harmony(challenging_hqs)

        assert normalized < 50.0, f"Challenging HQS normalized to {normalized}, expected <50"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

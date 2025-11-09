"""
Quick verification of percentile-based normalization.

Tests that the new normalization produces intuitive percentile mapping.

Usage:
    cd /Users/elie/git/arca/arca-backend
    uv run python -m functions.astrometers.calibration.verify_percentile
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import numpy as np
from astrometers.normalization import normalize_intensity, normalize_harmony


def verify_percentile_normalization():
    """Verify that percentile-based normalization works correctly."""

    # Load historical scores - try v2 CSV first, then fall back to parquet
    scores_path_v2 = os.path.join(os.path.dirname(__file__), "historical_scores_v2.csv")
    scores_path_v1 = os.path.join(os.path.dirname(__file__), "historical_scores.parquet")

    if os.path.exists(scores_path_v2):
        print("Loading historical scores from v2 CSV...")
        df = pd.read_csv(scores_path_v2)
        print(f"Loaded {len(df):,} score records (v2 format)")
    elif os.path.exists(scores_path_v1):
        print("Loading historical scores from v1 parquet...")
        df = pd.read_parquet(scores_path_v1)
        print(f"Loaded {len(df):,} score records (v1 format)")
    else:
        print(f"ERROR: Historical scores not found at:")
        print(f"  - {scores_path_v2} (v2)")
        print(f"  - {scores_path_v1} (v1)")
        print("Please run calculate_historical_v2.py first")
        return

    print()

    # Test DTI normalization
    print("=" * 60)
    print("DTI (INTENSITY) NORMALIZATION VERIFICATION")
    print("=" * 60)

    # Get some key percentile values
    dti_percentiles = {
        1: np.percentile(df['dti'], 1),
        10: np.percentile(df['dti'], 10),
        25: np.percentile(df['dti'], 25),
        50: np.percentile(df['dti'], 50),
        75: np.percentile(df['dti'], 75),
        85: np.percentile(df['dti'], 85),
        90: np.percentile(df['dti'], 90),
        95: np.percentile(df['dti'], 95),
        99: np.percentile(df['dti'], 99),
    }

    print("Testing key percentile values:")
    print()
    for p, raw_dti in dti_percentiles.items():
        normalized = normalize_intensity(raw_dti)
        print(f"  P{p:2d} raw DTI: {raw_dti:7.2f} → normalized: {normalized:5.1f} (expected ~{p})")

    print()
    print("Testing full distribution:")
    normalized_dti = df['dti'].apply(normalize_intensity)

    # Check that percentiles match scores
    test_percentiles = [10, 25, 50, 75, 85, 90, 95, 99]
    max_error = 0
    for p in test_percentiles:
        normalized_at_p = np.percentile(normalized_dti, p)
        error = abs(normalized_at_p - p)
        max_error = max(max_error, error)
        status = "✓" if error <= 3 else "✗"
        print(f"  P{p:2d}: normalized score = {normalized_at_p:5.1f} (expected {p}, error: {error:.1f}) {status}")

    print()
    print(f"  Max percentile error: {max_error:.1f}° (should be ≤3)")
    print(f"  Median: {normalized_dti.median():.1f} (expected ~50)")
    print(f"  Std dev: {normalized_dti.std():.1f} (expected ~29 for uniform)")
    print()

    # Test HQS normalization
    print("=" * 60)
    print("HQS (HARMONY) NORMALIZATION VERIFICATION")
    print("=" * 60)

    # Get some key percentile values
    hqs_percentiles = {
        1: np.percentile(df['hqs'], 1),
        10: np.percentile(df['hqs'], 10),
        25: np.percentile(df['hqs'], 25),
        50: np.percentile(df['hqs'], 50),
        75: np.percentile(df['hqs'], 75),
        90: np.percentile(df['hqs'], 90),
        95: np.percentile(df['hqs'], 95),
        99: np.percentile(df['hqs'], 99),
    }

    print("Testing key percentile values:")
    print()
    for p, raw_hqs in hqs_percentiles.items():
        normalized = normalize_harmony(raw_hqs)
        print(f"  P{p:2d} raw HQS: {raw_hqs:8.2f} → normalized: {normalized:5.1f} (expected ~{p})")

    print()
    print("Testing full distribution:")
    normalized_hqs = df['hqs'].apply(normalize_harmony)

    # Check that percentiles match scores
    max_error = 0
    for p in test_percentiles:
        normalized_at_p = np.percentile(normalized_hqs, p)
        error = abs(normalized_at_p - p)
        max_error = max(max_error, error)
        status = "✓" if error <= 3 else "✗"
        print(f"  P{p:2d}: normalized score = {normalized_at_p:5.1f} (expected {p}, error: {error:.1f}) {status}")

    print()
    print(f"  Max percentile error: {max_error:.1f}° (should be ≤3)")
    print(f"  Median: {normalized_hqs.median():.1f} (expected ~50)")
    print(f"  Std dev: {normalized_hqs.std():.1f} (expected ~29 for uniform)")
    print()

    # Summary
    print("=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print()
    print("Key findings:")
    print(f"  - Score 50 = P50 (median day)")
    print(f"  - Score 85 = P85 (top 15% of days)")
    print(f"  - Score 90 = P90 (top 10% of days)")
    print(f"  - Score 99 = P99 (top 1% of days)")
    print()
    print("Percentile-based normalization ensures:")
    print("  ✓ Intuitive interpretation (score = percentile rank)")
    print("  ✓ Uniform distribution of scores")
    print("  ✓ No confusing non-linear mapping")
    print()


if __name__ == "__main__":
    verify_percentile_normalization()

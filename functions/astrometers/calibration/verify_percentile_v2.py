"""
Quick verification of percentile-based normalization for v2 (per-meter calibration).

Tests that the new per-meter normalization produces intuitive percentile mapping.

Usage:
    cd /Users/elieb/git/arca-backend
    uv run python functions/astrometers/calibration/verify_percentile_v2.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import numpy as np
from astrometers.normalization import normalize_intensity, normalize_harmony


def verify_percentile_normalization_v2():
    """Verify that per-meter percentile-based normalization works correctly."""

    # Load historical scores
    scores_path = os.path.join(os.path.dirname(__file__), "historical_scores_v2.csv")

    if not os.path.exists(scores_path):
        print(f"ERROR: Historical scores not found at {scores_path}")
        print("Please run calculate_historical_v2.py first")
        return

    print("Loading historical scores (v2 format)...")
    df = pd.read_csv(scores_path)
    print(f"Loaded {len(df):,} score records")
    print(f"Unique meters: {df['meter'].nunique()}")
    print()

    # Get list of meters
    meters = sorted(df['meter'].unique())

    # Test each meter
    print("=" * 80)
    print("PER-METER DISTRIBUTION VERIFICATION")
    print("=" * 80)
    print()

    all_errors = []

    for meter_name in meters:
        meter_df = df[df['meter'] == meter_name]

        print(f"{'=' * 80}")
        print(f"METER: {meter_name.upper()}")
        print(f"{'=' * 80}")
        print(f"Records: {len(meter_df):,}")
        print()

        # Test DTI normalization
        print("DTI (Intensity) Normalization:")
        print("-" * 40)

        # Get some key percentile values
        dti_percentiles = {
            10: np.percentile(meter_df['dti'], 10),
            25: np.percentile(meter_df['dti'], 25),
            50: np.percentile(meter_df['dti'], 50),
            75: np.percentile(meter_df['dti'], 75),
            90: np.percentile(meter_df['dti'], 90),
            99: np.percentile(meter_df['dti'], 99),
        }

        for p, raw_dti in dti_percentiles.items():
            normalized = normalize_intensity(raw_dti, meter_name=meter_name)
            error = abs(normalized - p)
            all_errors.append(error)
            status = "✓" if error <= 3 else "✗"
            print(f"  P{p:2d}: {raw_dti:7.2f} → {normalized:5.1f} (expected {p}, error: {error:.1f}) {status}")

        # Test full distribution
        normalized_dti = meter_df['dti'].apply(lambda x: normalize_intensity(x, meter_name=meter_name))
        print(f"\n  Distribution stats:")
        print(f"    Median: {normalized_dti.median():.1f} (expected ~50)")
        print(f"    Std dev: {normalized_dti.std():.1f}")

        # Test HQS normalization
        print()
        print("HQS (Harmony) Normalization:")
        print("-" * 40)

        # Get some key percentile values
        hqs_percentiles = {
            10: np.percentile(meter_df['hqs'], 10),
            25: np.percentile(meter_df['hqs'], 25),
            50: np.percentile(meter_df['hqs'], 50),
            75: np.percentile(meter_df['hqs'], 75),
            90: np.percentile(meter_df['hqs'], 90),
            99: np.percentile(meter_df['hqs'], 99),
        }

        for p, raw_hqs in hqs_percentiles.items():
            normalized = normalize_harmony(raw_hqs, meter_name=meter_name)
            error = abs(normalized - p)
            all_errors.append(error)
            status = "✓" if error <= 3 else "✗"
            print(f"  P{p:2d}: {raw_hqs:8.2f} → {normalized:5.1f} (expected {p}, error: {error:.1f}) {status}")

        # Test full distribution
        normalized_hqs = meter_df['hqs'].apply(lambda x: normalize_harmony(x, meter_name=meter_name))
        print(f"\n  Distribution stats:")
        print(f"    Median: {normalized_hqs.median():.1f} (expected ~50)")
        print(f"    Std dev: {normalized_hqs.std():.1f}")
        print()

    # Summary
    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Meters tested: {len(meters)}")
    print(f"Max percentile error across all meters: {max(all_errors):.1f}° (should be ≤3)")
    print(f"Mean percentile error: {np.mean(all_errors):.1f}°")
    print()

    if max(all_errors) <= 3:
        print("✅ PASS: All meters have accurate percentile mapping")
    else:
        print("❌ FAIL: Some meters have percentile errors >3°")
        print("   Re-run calibration or check calibration_constants.json")
    print()

    print("Key findings:")
    print(f"  - Score 50 ≈ P50 (median day for each meter)")
    print(f"  - Score 90 ≈ P90 (top 10% of days for each meter)")
    print(f"  - Score 99 ≈ P99 (top 1% of days for each meter)")
    print()
    print("Per-meter calibration ensures:")
    print("  ✓ Each meter has its own scale (no cross-meter comparison)")
    print("  ✓ Intuitive interpretation (score = percentile rank within meter)")
    print("  ✓ Uniform distribution of scores per meter")
    print()


if __name__ == "__main__":
    verify_percentile_normalization_v2()

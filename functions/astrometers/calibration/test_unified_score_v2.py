"""
Test unified_score V2 formula with real calibration data.

This script simulates the new polar-style unified_score formula (-100 to +100)
using real natal charts and transits to validate the distribution.

Usage:
    cd /Users/elieb/git/arca-backend
    uv run python functions/astrometers/calibration/test_unified_score_v2.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import random
from datetime import datetime, timedelta

from astro import compute_birth_chart
from astrometers.meters import get_meters, calculate_unified_score
from astrometers.constants import (
    UNIFIED_SCORE_BASE_WEIGHT,
    UNIFIED_SCORE_INTENSITY_WEIGHT,
    UNIFIED_SCORE_POSITIVE_BOOST,
    UNIFIED_SCORE_NEGATIVE_DAMPEN,
)


# =============================================================================
# Use the ACTUAL implementation from meters.py
# =============================================================================

def calculate_unified_score_v2(intensity: float, harmony: float) -> float:
    """Wrapper around actual implementation."""
    score, _ = calculate_unified_score(intensity, harmony)
    return score


# =============================================================================
# MAIN SIMULATION
# =============================================================================

def main():
    # Load real natal charts
    charts_file = os.path.join(os.path.dirname(__file__), 'natal_charts.json')
    with open(charts_file) as f:
        charts = json.load(f)

    print(f"Loaded {len(charts)} natal charts")
    print()
    print("=" * 70)
    print("UNIFIED SCORE V2 SIMULATION")
    print(f"BASE_WEIGHT={UNIFIED_SCORE_BASE_WEIGHT}, INTENSITY_WEIGHT={UNIFIED_SCORE_INTENSITY_WEIGHT}")
    print(f"POSITIVE_BOOST={UNIFIED_SCORE_POSITIVE_BOOST}, NEGATIVE_DAMPEN={UNIFIED_SCORE_NEGATIVE_DAMPEN}")
    print("=" * 70)

    # Sample charts and dates - use proper sample sizes!
    random.seed(42)
    num_charts = min(200, len(charts))
    num_days_per_chart = 30
    sample_charts = random.sample(charts, num_charts)
    base_date = datetime(2024, 1, 1)

    meter_names = [
        'clarity', 'focus', 'communication', 'connections', 'resilience',
        'vulnerability', 'energy', 'drive', 'strength', 'vision', 'flow',
        'intuition', 'creativity', 'momentum', 'ambition', 'evolution', 'circle'
    ]

    all_intensity = []
    all_harmony = []
    all_unified_v2 = []
    all_unified_old = []

    print(f"\nSampling {num_charts} charts x {num_days_per_chart} days x {len(meter_names)} meters...")

    errors = 0
    for i, chart_data in enumerate(sample_charts):
        natal_chart = chart_data['natal_chart']
        for j in range(num_days_per_chart):
            day_offset = random.randint(0, 365)
            date = base_date + timedelta(days=day_offset)
            date_str = date.strftime('%Y-%m-%d')

            try:
                # Get transit chart
                transit_chart, _ = compute_birth_chart(date_str, '12:00')

                # Calculate meters
                meters = get_meters(
                    natal_chart=natal_chart,
                    transit_chart=transit_chart,
                    apply_harmonic_boost=True
                )

                for meter_name in meter_names:
                    meter = getattr(meters, meter_name)
                    all_intensity.append(meter.intensity)
                    all_harmony.append(meter.harmony)
                    all_unified_old.append(meter.unified_score)
                    all_unified_v2.append(calculate_unified_score_v2(meter.intensity, meter.harmony))

            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  Error {i}.{j}: {e}")

    n = len(all_unified_v2)
    print(f"\nCollected {n} data points ({errors} errors)")

    if n == 0:
        print("No data collected!")
        return

    # Distribution analysis
    print()
    print("=" * 70)
    print("DISTRIBUTION ANALYSIS")
    print("=" * 70)

    print(f"\nIntensity distribution:")
    print(f"  Min: {min(all_intensity):.1f}, Max: {max(all_intensity):.1f}")
    print(f"  Avg: {sum(all_intensity)/n:.1f}")

    print(f"\nHarmony distribution:")
    print(f"  Min: {min(all_harmony):.1f}, Max: {max(all_harmony):.1f}")
    print(f"  Avg: {sum(all_harmony)/n:.1f}")
    harm_above_50 = sum(1 for h in all_harmony if h > 50)
    print(f"  Above 50 (positive): {harm_above_50} ({100*harm_above_50/n:.1f}%)")

    # Old unified score (0-100)
    print(f"\nOld Unified Score (0-100):")
    old_sorted = sorted(all_unified_old)
    print(f"  Min: {min(old_sorted):.1f}, Max: {max(old_sorted):.1f}")
    print(f"  P10: {old_sorted[int(n*0.10)]:.1f}, P50: {old_sorted[int(n*0.50)]:.1f}, P90: {old_sorted[int(n*0.90)]:.1f}")
    print(f"  Avg: {sum(old_sorted)/n:.1f}")

    # New unified score V2 (-100 to +100)
    print(f"\nNew Unified Score V2 (-100 to +100):")
    scores = sorted(all_unified_v2)
    print(f"  Min: {min(scores):.1f}, Max: {max(scores):.1f}")
    print(f"  P10: {scores[int(n*0.10)]:.1f}, P25: {scores[int(n*0.25)]:.1f}, P50: {scores[int(n*0.50)]:.1f}, P75: {scores[int(n*0.75)]:.1f}, P90: {scores[int(n*0.90)]:.1f}")

    positive = sum(1 for s in scores if s > 0)
    negative = sum(1 for s in scores if s < 0)
    neutral = sum(1 for s in scores if s == 0)
    avg_score = sum(scores) / n

    print(f"\n  Positive (>0): {positive} ({100*positive/n:.1f}%)")
    print(f"  Negative (<0): {negative} ({100*negative/n:.1f}%)")
    print(f"  Neutral (=0): {neutral}")
    print(f"  Average: {avg_score:+.1f}")

    # Bucket distribution
    buckets = {
        '-100 to -60': 0,
        '-60 to -30': 0,
        '-30 to 0': 0,
        '0 to +30': 0,
        '+30 to +60': 0,
        '+60 to +100': 0
    }
    for s in scores:
        if s <= -60: buckets['-100 to -60'] += 1
        elif s <= -30: buckets['-60 to -30'] += 1
        elif s <= 0: buckets['-30 to 0'] += 1
        elif s <= 30: buckets['0 to +30'] += 1
        elif s <= 60: buckets['+30 to +60'] += 1
        else: buckets['+60 to +100'] += 1

    print("\nBucket distribution:")
    for bucket, count in buckets.items():
        pct = 100 * count / n
        bar = '#' * int(pct / 2)
        print(f"  {bucket:>13}: {count:>5} ({pct:>5.1f}%) {bar}")

    # Empowering assessment
    print()
    print("=" * 70)
    print("EMPOWERING ASSESSMENT")
    print("=" * 70)

    if avg_score > 0:
        print(f"  [OK] Average is positive: {avg_score:+.1f}")
    else:
        print(f"  [FAIL] Average is negative: {avg_score:+.1f} - need more boost!")

    if positive > negative:
        print(f"  [OK] More positive than negative: {positive} vs {negative}")
    else:
        print(f"  [FAIL] More negative than positive: {negative} vs {positive} - need more boost!")

    severe_negative = sum(1 for s in scores if s < -60)
    severe_positive = sum(1 for s in scores if s > 60)
    if severe_negative < n * 0.05:
        print(f"  [OK] Severe negative (<-60) is rare: {severe_negative} ({100*severe_negative/n:.1f}%)")
    else:
        print(f"  [WARN] Too many severe negatives: {severe_negative} ({100*severe_negative/n:.1f}%)")

    # Percentile analysis for threshold computation
    print()
    print("=" * 70)
    print("PERCENTILE ANALYSIS (for word bank thresholds)")
    print("=" * 70)

    int_sorted = sorted(all_intensity)
    harm_sorted = sorted(all_harmony)

    print(f"\nIntensity percentiles:")
    for p in [10, 20, 25, 33, 50, 67, 75, 80, 90]:
        val = int_sorted[int(n * p / 100)]
        print(f"  P{p}: {val:.1f}")

    print(f"\nHarmony percentiles:")
    for p in [10, 20, 25, 33, 50, 67, 75, 80, 90]:
        val = harm_sorted[int(n * p / 100)]
        print(f"  P{p}: {val:.1f}")

    print(f"\nUnified Score percentiles:")
    for p in [10, 20, 25, 33, 50, 67, 75, 80, 90]:
        val = scores[int(n * p / 100)]
        print(f"  P{p}: {val:.1f}")

    # Quadrant distribution (using P33/P67 as boundaries)
    int_low = int_sorted[int(n * 0.33)]
    int_high = int_sorted[int(n * 0.67)]
    harm_low = harm_sorted[int(n * 0.33)]
    harm_high = harm_sorted[int(n * 0.67)]

    print(f"\nSuggested thresholds (P33/P67):")
    print(f"  Intensity: low < {int_low:.0f}, high > {int_high:.0f}")
    print(f"  Harmony: low < {harm_low:.0f}, high > {harm_high:.0f}")

    # Count quadrant occurrences
    q_hi_hi = sum(1 for i, h in zip(all_intensity, all_harmony) if i > int_high and h > harm_high)
    q_hi_lo = sum(1 for i, h in zip(all_intensity, all_harmony) if i > int_high and h < harm_low)
    q_lo_hi = sum(1 for i, h in zip(all_intensity, all_harmony) if i < int_low and h > harm_high)
    q_lo_lo = sum(1 for i, h in zip(all_intensity, all_harmony) if i < int_low and h < harm_low)
    q_mid = n - q_hi_hi - q_hi_lo - q_lo_hi - q_lo_lo

    print(f"\nQuadrant distribution (with P33/P67 thresholds):")
    print(f"  High Int + High Harm: {q_hi_hi} ({100*q_hi_hi/n:.1f}%)")
    print(f"  High Int + Low Harm:  {q_hi_lo} ({100*q_hi_lo/n:.1f}%)")
    print(f"  Low Int + High Harm:  {q_lo_hi} ({100*q_lo_hi/n:.1f}%)")
    print(f"  Low Int + Low Harm:   {q_lo_lo} ({100*q_lo_lo/n:.1f}%)")
    print(f"  Moderate (middle):    {q_mid} ({100*q_mid/n:.1f}%)")


if __name__ == "__main__":
    main()

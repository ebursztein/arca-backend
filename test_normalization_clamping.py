"""
Normalization Clamping Analysis

Tests how much data is being clamped to 0 or 100 boundaries
with the current p15-p85 normalization window.
"""

import sys
sys.path.insert(0, '/Users/elieb/git/arca-backend/functions')

import random
import numpy as np
from datetime import datetime
from astro import compute_birth_chart
from astrometers.meters import calculate_meter, METER_CONFIGS
from astrometers.core import calculate_all_aspects


def generate_random_birth_data():
    year = random.randint(1950, 2010)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    locations = [
        (40.7128, -74.0060, "America/New_York"),
        (34.0522, -118.2437, "America/Los_Angeles"),
        (51.5074, -0.1278, "Europe/London"),
        (48.8566, 2.3522, "Europe/Paris"),
        (35.6762, 139.6503, "Asia/Tokyo"),
    ]

    lat, lon, tz = random.choice(locations)

    return {
        "birth_date": f"{year}-{month:02d}-{day:02d}",
        "birth_time": f"{hour:02d}:{minute:02d}",
        "birth_timezone": tz,
        "birth_lat": lat,
        "birth_lon": lon
    }


def main():
    num_samples = 5000
    print(f"Collecting {num_samples} harmony scores to analyze clamping...\n")

    harmony_scores = []

    attempts = 0
    while len(harmony_scores) < num_samples:
        attempts += 1
        birth_data = generate_random_birth_data()

        try:
            natal_chart, _ = compute_birth_chart(**birth_data)
            transit_chart, _ = compute_birth_chart("2025-01-15", "12:00")
            date = datetime(2025, 1, 15)

            meter_name = random.choice(list(METER_CONFIGS.keys()))
            config = METER_CONFIGS[meter_name]

            all_aspects = calculate_all_aspects(natal_chart, transit_chart)

            reading = calculate_meter(
                meter_name, config, all_aspects,
                natal_chart, transit_chart, date,
                apply_harmonic_boost=True
            )

            harmony_scores.append(reading.harmony)

        except:
            continue

    harmony = np.array(harmony_scores)

    print(f"n = {len(harmony)}\n")

    # Count exact boundaries
    at_zero = np.sum(harmony == 0.0)
    at_hundred = np.sum(harmony == 100.0)
    total_clamped = at_zero + at_hundred

    print("=" * 60)
    print("CLAMPING ANALYSIS - p15-p85 Normalization Window")
    print("=" * 60)
    print()
    print(f"Values at floor (0.0):     {at_zero:4d} ({at_zero/len(harmony)*100:5.1f}%)")
    print(f"Values at ceiling (100.0): {at_hundred:4d} ({at_hundred/len(harmony)*100:5.1f}%)")
    print(f"TOTAL CLAMPED:             {total_clamped:4d} ({total_clamped/len(harmony)*100:5.1f}%)")
    print()

    # Show distribution
    print("=" * 60)
    print("DISTRIBUTION (10-point buckets)")
    print("=" * 60)
    print()
    print("Range      | Count |   %   | Histogram")
    print("-" * 60)

    bins = [(i, i+10) for i in range(0, 100, 10)]
    for low, high in bins:
        count = np.sum((harmony >= low) & (harmony < high))
        pct = count / len(harmony) * 100
        bar = '█' * int(pct / 2)
        print(f"{low:3d} - {high:3d}  | {count:5d} | {pct:5.1f}% | {bar}")

    # Percentile table
    print()
    print("=" * 60)
    print("PERCENTILE DISTRIBUTION")
    print("=" * 60)
    print()
    print("Percentile | Value")
    print("-" * 30)

    percentiles = [0, 5, 10, 15, 20, 25, 50, 75, 80, 85, 90, 95, 100]
    for p in percentiles:
        val = np.percentile(harmony, p)
        marker = " <-- FLOOR" if val == 0.0 else (" <-- CEILING" if val == 100.0 else "")
        print(f"P{p:3d}        | {val:6.2f}{marker}")

    print()
    print("=" * 60)
    print("INTERPRETATION")
    print("=" * 60)
    print()
    print("p15-p85 normalization means:")
    print("- Raw scores below p15 → clamped to 0")
    print("- Raw scores above p85 → clamped to 100")
    print("- Expected clamping: ~30% (15% each side)")
    print()
    if total_clamped / len(harmony) > 0.35:
        print("⚠️  EXCESSIVE CLAMPING - Consider wider window (p10-p90)")
    elif total_clamped / len(harmony) < 0.25:
        print("✓  Clamping within expected range")
    else:
        print("~  Clamping at expected level (~30%)")


if __name__ == "__main__":
    main()

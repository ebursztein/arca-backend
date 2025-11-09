"""
Harmonic boost multiplier testing.

Tests benefic/malefic multipliers independently and together.
Current production settings: 2.0x / 0.5x (benefic/malefic)
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
    """Generate random but realistic birth data."""
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
    charts = 500
    print(f"\n{'='*100}")
    print(f"HARMONIC BOOST MULTIPLIER TESTING")
    print(f"{'='*100}\n")
    print(f"Collecting {charts} chart-meter calculations...")
    print("Testing benefic/malefic multipliers independently and together\n")

    # Collect test cases once
    test_cases = []
    attempts = 0
    max_attempts = 2000

    while len(test_cases) < charts and attempts < max_attempts:
        attempts += 1
        birth_data = generate_random_birth_data()

        try:
            natal_chart, _ = compute_birth_chart(**birth_data)
            transit_chart, _ = compute_birth_chart("2025-01-15", "12:00")
            date = datetime(2025, 1, 15)

            # Pick a random meter
            meter_name = random.choice(list(METER_CONFIGS.keys()))
            config = METER_CONFIGS[meter_name]

            # Calculate all aspects once
            all_aspects = calculate_all_aspects(natal_chart, transit_chart)

            test_cases.append({
                "meter_name": meter_name,
                "config": config,
                "all_aspects": all_aspects,
                "natal_chart": natal_chart,
                "transit_chart": transit_chart,
                "date": date
            })

        except Exception as e:
            continue

    print(f"Collected {len(test_cases)} test cases\n")

    # Test configurations
    print("=" * 100)
    print("SCENARIO 1: BENEFIC MULTIPLIER ONLY (malefic = 1.0)")
    print("=" * 100)
    print()
    benefic_configs = [
        (1.0, 1.0, "1.0x / 1.0x"),
        (1.5, 1.0, "1.5x / 1.0x"),
        (2.0, 1.0, "2.0x / 1.0x [current]"),
        (2.5, 1.0, "2.5x / 1.0x"),
    ]
    test_scenario(test_cases, benefic_configs)

    print("\n" + "=" * 100)
    print("SCENARIO 2: MALEFIC MULTIPLIER ONLY (benefic = 1.0)")
    print("=" * 100)
    print()
    malefic_configs = [
        (1.0, 1.0, "1.0x / 1.0x"),
        (1.0, 0.7, "1.0x / 0.7x"),
        (1.0, 0.5, "1.0x / 0.5x [current]"),
        (1.0, 0.3, "1.0x / 0.3x"),
    ]
    test_scenario(test_cases, malefic_configs)

    print("\n" + "=" * 100)
    print("SCENARIO 3: BOTH MULTIPLIERS TOGETHER")
    print("=" * 100)
    print()
    combined_configs = [
        (1.0, 1.0, "1.0x / 1.0x"),
        (1.5, 0.7, "1.5x / 0.7x"),
        (2.0, 0.5, "2.0x / 0.5x [current]"),
        (2.5, 0.3, "2.5x / 0.3x"),
    ]
    test_scenario(test_cases, combined_configs)


def test_scenario(test_cases, configs):
    """Test a scenario with multiple configurations."""
    results = {}

    for benefic_mult, malefic_mult, label in configs:
        harmony_scores = []

        for test_case in test_cases:
            reading = calculate_meter(
                meter_name=test_case["meter_name"],
                config=test_case["config"],
                all_aspects=test_case["all_aspects"],
                natal_chart=test_case["natal_chart"],
                transit_chart=test_case["transit_chart"],
                date=test_case["date"],
                apply_harmonic_boost=(benefic_mult != 1.0 or malefic_mult != 1.0),
                benefic_multiplier=benefic_mult,
                malefic_multiplier=malefic_mult
            )
            harmony_scores.append(reading.harmony)

        results[label] = np.array(harmony_scores)

    # Get baseline for comparison
    baseline_label = list(results.keys())[0]
    baseline = results[baseline_label]

    # Print summary table
    print(f"{'Configuration':<30} | Challenging | Mixed  | Harmonious | Mean Δ")
    print("-" * 80)

    for label, scores in results.items():
        challenging = np.sum(scores < 30) / len(scores) * 100
        mixed = np.sum((scores >= 30) & (scores < 70)) / len(scores) * 100
        harmonious = np.sum(scores >= 70) / len(scores) * 100
        mean_diff = scores.mean() - baseline.mean()

        print(f"{label:<30} | {challenging:6.1f}%    | {mixed:5.1f}% | {harmonious:6.1f}%   | {mean_diff:+6.2f}")

    print()

    # Detailed percentile comparison
    print(f"PERCENTILE DISTRIBUTION (n={len(baseline)})")
    print(f"{'Percentile':<12}", end="")
    for label in results.keys():
        print(f" {label:<15}", end="")
    print()
    print("-" * (12 + 16 * len(results)))

    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    for p in percentiles:
        print(f"P{p:<10}  ", end="")
        for label in results.keys():
            val = np.percentile(results[label], p)
            print(f" {val:>12.2f}   ", end="")
        print()

    print()
    print("=" * 100)
    print("✓ Test complete!")
    print("=" * 100)
    print()


if __name__ == "__main__":
    main()

"""
Raw data comparison - no bullshit.
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
    print("Collecting 500 samples...")

    harmony_no_boost = []
    harmony_with_boost = []

    attempts = 0
    while len(harmony_no_boost) < 500 and attempts < 2000:
        attempts += 1
        birth_data = generate_random_birth_data()

        try:
            natal_chart, _ = compute_birth_chart(**birth_data)
            transit_chart, _ = compute_birth_chart("2025-01-15", "12:00")
            date = datetime(2025, 1, 15)

            meter_name = random.choice(list(METER_CONFIGS.keys()))
            config = METER_CONFIGS[meter_name]

            all_aspects = calculate_all_aspects(natal_chart, transit_chart)

            reading_no = calculate_meter(
                meter_name, config, all_aspects,
                natal_chart, transit_chart, date,
                apply_harmonic_boost=False
            )

            reading_yes = calculate_meter(
                meter_name, config, all_aspects,
                natal_chart, transit_chart, date,
                apply_harmonic_boost=True
            )

            harmony_no_boost.append(reading_no.harmony)
            harmony_with_boost.append(reading_yes.harmony)

        except:
            continue

    harmony_no = np.array(harmony_no_boost)
    harmony_yes = np.array(harmony_with_boost)

    print(f"\nn = {len(harmony_no)}\n")

    # Full percentile table
    percentiles = list(range(0, 101, 5))

    print("Percentile | NO_BOOST | WITH_BOOST | DIFF")
    print("-" * 50)

    for p in percentiles:
        no_val = np.percentile(harmony_no, p)
        yes_val = np.percentile(harmony_yes, p)
        diff = yes_val - no_val
        print(f"P{p:3d}       | {no_val:8.2f} | {yes_val:10.2f} | {diff:+7.2f}")

    # Count exact values at boundaries
    print("\n")
    print("BOUNDARY COUNTS:")
    print(f"NO_BOOST  at 0.0:   {np.sum(harmony_no == 0.0)}")
    print(f"NO_BOOST  at 100.0: {np.sum(harmony_no == 100.0)}")
    print(f"WITH_BOOST at 0.0:   {np.sum(harmony_yes == 0.0)}")
    print(f"WITH_BOOST at 100.0: {np.sum(harmony_yes == 100.0)}")


if __name__ == "__main__":
    main()

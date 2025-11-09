"""
Test day-to-day variation with V2 Optimistic Model + IQR normalization.

Compares harmony distribution WITH and WITHOUT harmonic boost.
Records detailed computation data to verify boost is working.
"""

import sys
sys.path.insert(0, '/Users/elieb/git/arca-backend/functions')

from datetime import datetime, timedelta
import random

from astro import compute_birth_chart
from astrometers.meters import get_meters, calculate_meter, filter_aspects, METER_CONFIGS
from astrometers.core import calculate_all_aspects, calculate_astrometers
from astrometers.quality import harmonic_boost


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
        (55.7558, 37.6173, "Europe/Moscow"),
        (-33.8688, 151.2093, "Australia/Sydney"),
        (19.4326, -99.1332, "America/Mexico_City"),
        (28.6139, 77.2090, "Asia/Kolkata"),
        (-23.5505, -46.6333, "America/Sao_Paulo"),
    ]

    lat, lon, tz = random.choice(locations)

    return {
        "birth_date": f"{year}-{month:02d}-{day:02d}",
        "birth_time": f"{hour:02d}:{minute:02d}",
        "birth_timezone": tz,
        "birth_lat": lat,
        "birth_lon": lon
    }


def run_test_scenario(num_charts, num_days, apply_boost=True):
    """Run test with or without harmonic boost."""
    all_deltas = {meter: [] for meter in [
        "mental_clarity", "focus", "communication",
        "love", "inner_stability", "sensitivity",
        "vitality", "drive", "wellness",
        "purpose", "connection", "intuition", "creativity",
        "opportunities", "career", "growth", "social_life"
    ]}

    harmony_values = []

    for i in range(num_charts):
        birth_data = generate_random_birth_data()

        try:
            natal_chart, _ = compute_birth_chart(**birth_data)

            start_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
            daily_scores = []

            for day in range(num_days):
                date = start_date + timedelta(days=day)
                transit_chart, _ = compute_birth_chart(
                    birth_date=date.strftime("%Y-%m-%d"),
                    birth_time="12:00",
                    birth_timezone="UTC"
                )

                meters = get_meters(
                    natal_chart,
                    transit_chart,
                    date.date(),
                    calculate_trends=False,
                    apply_harmonic_boost=apply_boost
                )
                daily_scores.append(meters)

            # Calculate deltas
            for meter_name in all_deltas.keys():
                scores = [getattr(m, meter_name).unified_score for m in daily_scores]
                deltas = [abs(scores[i] - scores[i-1]) for i in range(1, len(scores))]
                all_deltas[meter_name].extend(deltas)

                # Collect harmony values
                harmony_values.extend([getattr(m, meter_name).harmony for m in daily_scores])

            if (i + 1) % 10 == 0:
                print(f"Processed {i+1}/{num_charts} charts...")

        except Exception as e:
            print(f"Error on chart {i+1}: {e}")
            continue

    return all_deltas, harmony_values


def main():
    num_charts = 100
    num_days = 7

    print(f"\n{'='*100}")
    print(f"HARMONIC BOOST A/B TEST - Harmony Distribution Comparison")
    print(f"{'='*100}")
    print(f"\nTesting {num_charts} charts × {num_days} days = {num_charts * num_days} chart-days")
    print(f"Running TWO scenarios: WITHOUT boost vs WITH boost\n")

    # ========================================
    # SCENARIO 1: WITHOUT HARMONIC BOOST
    # ========================================
    print(f"\n{'='*100}")
    print(f"SCENARIO 1: Flat Baseline (NO harmonic boost)")
    print(f"{'='*100}\n")

    all_deltas_no_boost, harmony_values_no_boost = run_test_scenario(num_charts, num_days, apply_boost=False)

    # ========================================
    # SCENARIO 2: WITH HARMONIC BOOST
    # ========================================
    print(f"\n{'='*100}")
    print(f"SCENARIO 2: Harmonic Boost Applied (benefic 1.1x, malefic 0.85x)")
    print(f"{'='*100}\n")

    all_deltas_with_boost, harmony_values_with_boost = run_test_scenario(num_charts, num_days, apply_boost=True)

    print(f"\n{'='*100}")
    print(f"HARMONY DISTRIBUTION COMPARISON")
    print(f"{'='*100}\n")

    # Calculate harmony distributions for both scenarios
    pct_challenging_no = sum(1 for h in harmony_values_no_boost if h < 30) / len(harmony_values_no_boost) * 100
    pct_mixed_no = sum(1 for h in harmony_values_no_boost if 30 <= h < 70) / len(harmony_values_no_boost) * 100
    pct_harmonious_no = sum(1 for h in harmony_values_no_boost if h >= 70) / len(harmony_values_no_boost) * 100

    pct_challenging_yes = sum(1 for h in harmony_values_with_boost if h < 30) / len(harmony_values_with_boost) * 100
    pct_mixed_yes = sum(1 for h in harmony_values_with_boost if 30 <= h < 70) / len(harmony_values_with_boost) * 100
    pct_harmonious_yes = sum(1 for h in harmony_values_with_boost if h >= 70) / len(harmony_values_with_boost) * 100

    print(f"{'Category':<20} {'NO Boost':<15} {'WITH Boost':<15} {'Change':<15}")
    print("-" * 70)
    print(f"{'Challenging (< 30)':<20} {pct_challenging_no:>7.1f}%       {pct_challenging_yes:>7.1f}%       {pct_challenging_yes - pct_challenging_no:>+7.1f}%")
    print(f"{'Mixed (30-70)':<20} {pct_mixed_no:>7.1f}%       {pct_mixed_yes:>7.1f}%       {pct_mixed_yes - pct_mixed_no:>+7.1f}%")
    print(f"{'Harmonious (≥ 70)':<20} {pct_harmonious_no:>7.1f}%       {pct_harmonious_yes:>7.1f}%       {pct_harmonious_yes - pct_harmonious_no:>+7.1f}%")

    print("\n" + "=" * 100)
    print("ANALYSIS")
    print("=" * 100 + "\n")

    print(f"Goal: < 40% challenging days\n")
    print(f"WITHOUT boost: {pct_challenging_no:.1f}% challenging")
    print(f"WITH boost:    {pct_challenging_yes:.1f}% challenging")
    print(f"Change:        {pct_challenging_yes - pct_challenging_no:+.1f}%\n")

    if pct_challenging_yes < pct_challenging_no:
        print(f"✓ Harmonic boost REDUCED challenging days by {abs(pct_challenging_yes - pct_challenging_no):.1f}%")
    elif pct_challenging_yes > pct_challenging_no:
        print(f"✗ Harmonic boost INCREASED challenging days by {abs(pct_challenging_yes - pct_challenging_no):.1f}%")
    else:
        print(f"→ Harmonic boost had NO EFFECT on harmony distribution")

    if pct_challenging_yes < 40 and pct_challenging_no >= 40:
        print(f"✓ Harmonic boost brought us UNDER the 40% goal!")
    elif pct_challenging_yes < 40:
        print(f"✓ Both scenarios meet the <40% goal")
    else:
        print(f"✗ Still above 40% challenging - needs further adjustment")

    print("\n" + "=" * 100)
    print("✓ A/B Test complete!")
    print("=" * 100)


if __name__ == "__main__":
    main()

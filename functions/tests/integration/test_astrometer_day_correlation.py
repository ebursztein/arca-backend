"""
Astrometer Day-to-Day Correlation Analysis

Measures how much meter scores change between consecutive days.
High day-to-day correlation = meters are too stable (boring)
Low day-to-day correlation = meters change meaningfully daily

For each chart, calculates meters on day N and day N+1, then correlates.
"""

import random
import math
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from astro import compute_birth_chart
from astrometers.meters import get_meters


CITIES = [
    ("New York", 40.7128, -74.0060, "America/New_York"),
    ("Los Angeles", 34.0522, -118.2437, "America/Los_Angeles"),
    ("Chicago", 41.8781, -87.6298, "America/Chicago"),
    ("London", 51.5074, -0.1278, "Europe/London"),
    ("Paris", 48.8566, 2.3522, "Europe/Paris"),
    ("Tokyo", 35.6762, 139.6503, "Asia/Tokyo"),
    ("Sydney", -33.8688, 151.2093, "Australia/Sydney"),
    ("Berlin", 52.5200, 13.4050, "Europe/Berlin"),
    ("Mumbai", 19.0760, 72.8777, "Asia/Kolkata"),
    ("Sao Paulo", -23.5505, -46.6333, "America/Sao_Paulo"),
]

METER_NAMES = [
    'clarity', 'focus', 'communication',
    'connections', 'resilience', 'vulnerability',
    'energy', 'drive', 'strength',
    'vision', 'flow', 'intuition', 'creativity',
    'momentum', 'ambition', 'evolution', 'circle'
]

# Group definitions for aggregate analysis
GROUPS = {
    'mind': ['clarity', 'focus', 'communication'],
    'heart': ['connections', 'resilience', 'vulnerability'],
    'body': ['energy', 'drive', 'strength'],
    'instincts': ['vision', 'flow', 'intuition', 'creativity'],
    'growth': ['momentum', 'ambition', 'evolution', 'circle'],
}


def generate_random_birth_data() -> dict:
    """Generate random birth data."""
    start_date = datetime(1960, 1, 1)
    end_date = datetime(2005, 12, 31)
    days_range = (end_date - start_date).days
    random_date = start_date + timedelta(days=random.randint(0, days_range))

    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    city_name, lat, lon, tz = random.choice(CITIES)

    return {
        "birth_date": random_date.strftime("%Y-%m-%d"),
        "birth_time": f"{hour:02d}:{minute:02d}",
        "birth_lat": lat,
        "birth_lon": lon,
        "birth_timezone": tz,
    }


def pearson_correlation(x: list[float], y: list[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    n = len(x)
    if n != len(y) or n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)

    if var_x == 0 or var_y == 0:
        return 0.0

    return numerator / math.sqrt(var_x * var_y)


def run_day_correlation_analysis(
    n_charts: int = 500,
    n_day_pairs: int = 20,
    seed: int = 42,
) -> dict:
    """
    Analyze day-to-day correlation for each meter.

    For each chart, picks random consecutive day pairs and measures
    how correlated day1 scores are with day2 scores.

    Args:
        n_charts: Number of random birth charts
        n_day_pairs: Number of consecutive day pairs per chart
        seed: Random seed
    """
    random.seed(seed)

    print(f"\n{'='*80}")
    print(f"DAY-TO-DAY CORRELATION ANALYSIS")
    print(f"{'='*80}")
    print(f"Parameters:")
    print(f"  Charts: {n_charts}")
    print(f"  Day pairs per chart: {n_day_pairs}")
    print(f"  Total day pairs: {n_charts * n_day_pairs}")
    print(f"{'='*80}\n")

    # Generate charts
    print("Generating birth charts...")
    charts = []
    for _ in range(n_charts):
        birth_data = generate_random_birth_data()
        try:
            natal_chart, _ = compute_birth_chart(
                birth_date=birth_data["birth_date"],
                birth_time=birth_data["birth_time"],
                birth_timezone=birth_data["birth_timezone"],
                birth_lat=birth_data["birth_lat"],
                birth_lon=birth_data["birth_lon"]
            )
            charts.append(natal_chart)
        except Exception as e:
            pass

    print(f"  Generated {len(charts)} valid charts")

    # Collect day1 vs day2 scores per meter
    day1_scores: dict[str, list[float]] = defaultdict(list)
    day2_scores: dict[str, list[float]] = defaultdict(list)
    deltas: dict[str, list[float]] = defaultdict(list)

    total_pairs = 0
    errors = 0

    print(f"\nCalculating day pairs...")
    for i, natal_chart in enumerate(charts):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{len(charts)} charts...")

        # Pick random start dates for this chart
        for _ in range(n_day_pairs):
            # Random date between 2020-2025
            start = datetime(2020, 1, 1)
            days_offset = random.randint(0, 365 * 5)
            day1 = start + timedelta(days=days_offset)
            day2 = day1 + timedelta(days=1)

            try:
                # Calculate day 1
                transit1, _ = compute_birth_chart(day1.strftime("%Y-%m-%d"), "12:00")
                meters1 = get_meters(natal_chart, transit1, day1, calculate_trends=False)

                # Calculate day 2
                transit2, _ = compute_birth_chart(day2.strftime("%Y-%m-%d"), "12:00")
                meters2 = get_meters(natal_chart, transit2, day2, calculate_trends=False)

                # Collect scores for individual meters
                for meter_name in METER_NAMES:
                    score1 = getattr(meters1, meter_name).unified_score
                    score2 = getattr(meters2, meter_name).unified_score
                    day1_scores[meter_name].append(score1)
                    day2_scores[meter_name].append(score2)
                    deltas[meter_name].append(abs(score2 - score1))

                # Collect scores for groups (average of meters in group)
                for group_name, group_meters in GROUPS.items():
                    group_score1 = sum(getattr(meters1, m).unified_score for m in group_meters) / len(group_meters)
                    group_score2 = sum(getattr(meters2, m).unified_score for m in group_meters) / len(group_meters)
                    day1_scores[f"GROUP_{group_name}"].append(group_score1)
                    day2_scores[f"GROUP_{group_name}"].append(group_score2)
                    deltas[f"GROUP_{group_name}"].append(abs(group_score2 - group_score1))

                # Overall average across all meters
                overall1 = sum(getattr(meters1, m).unified_score for m in METER_NAMES) / len(METER_NAMES)
                overall2 = sum(getattr(meters2, m).unified_score for m in METER_NAMES) / len(METER_NAMES)
                day1_scores["GROUP_overall"].append(overall1)
                day2_scores["GROUP_overall"].append(overall2)
                deltas["GROUP_overall"].append(abs(overall2 - overall1))

                total_pairs += 1

            except Exception as e:
                errors += 1

    print(f"\nComputed {total_pairs} day pairs ({errors} errors)")

    # Calculate day-to-day correlations per meter
    print(f"\n{'='*80}")
    print("DAY-TO-DAY CORRELATION BY METER")
    print(f"{'='*80}")
    print("(Want: moderate correlation 0.3-0.7 = meaningful daily change)")
    print()

    correlations = {}
    avg_deltas = {}

    print(f"  {'Meter':<15} {'Day Corr':>10} {'Avg |Delta|':>12} {'Median |D|':>12} {'Stability'}")
    print(f"  {'-'*65}")

    for meter_name in METER_NAMES:
        corr = pearson_correlation(day1_scores[meter_name], day2_scores[meter_name])
        correlations[meter_name] = corr

        avg_delta = statistics.mean(deltas[meter_name])
        median_delta = statistics.median(deltas[meter_name])
        avg_deltas[meter_name] = avg_delta

        # Interpret stability
        if corr > 0.85:
            stability = "TOO STABLE"
        elif corr > 0.7:
            stability = "Stable"
        elif corr > 0.5:
            stability = "Moderate"
        elif corr > 0.3:
            stability = "Dynamic"
        else:
            stability = "VOLATILE"

        print(f"  {meter_name:<15} {corr:>10.3f} {avg_delta:>12.1f} {median_delta:>12.1f} {stability}")

    # GROUP-LEVEL CORRELATIONS
    print(f"\n{'='*80}")
    print("DAY-TO-DAY CORRELATION BY GROUP (Important for UX)")
    print(f"{'='*80}")
    print("(Groups are what users see - these should have healthy dynamics)")
    print()

    group_correlations = {}
    group_avg_deltas = {}

    print(f"  {'Group':<15} {'Day Corr':>10} {'Avg |Delta|':>12} {'Median |D|':>12} {'Stability'}")
    print(f"  {'-'*65}")

    group_names = list(GROUPS.keys()) + ['overall']
    for group_name in group_names:
        key = f"GROUP_{group_name}"
        corr = pearson_correlation(day1_scores[key], day2_scores[key])
        group_correlations[group_name] = corr

        avg_delta = statistics.mean(deltas[key])
        median_delta = statistics.median(deltas[key])
        group_avg_deltas[group_name] = avg_delta

        # Interpret stability
        if corr > 0.85:
            stability = "TOO STABLE"
        elif corr > 0.7:
            stability = "Stable"
        elif corr > 0.5:
            stability = "Moderate"
        elif corr > 0.3:
            stability = "Dynamic"
        else:
            stability = "VOLATILE"

        display_name = group_name.upper() if group_name == 'overall' else group_name.title()
        print(f"  {display_name:<15} {corr:>10.3f} {avg_delta:>12.1f} {median_delta:>12.1f} {stability}")

    # Summary statistics (individual meters)
    avg_day_corr = statistics.mean(correlations.values())
    min_corr = min(correlations.values())
    max_corr = max(correlations.values())
    avg_all_deltas = statistics.mean(avg_deltas.values())

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    # Group-level summary stats
    avg_group_corr = statistics.mean(group_correlations.values())
    avg_group_deltas = statistics.mean(group_avg_deltas.values())
    overall_corr = group_correlations.get('overall', 0)
    overall_delta = group_avg_deltas.get('overall', 0)

    print(f"""
+--------------------------------+------------+------------+--------+
| INDIVIDUAL METERS              | Value      | Target     | Status |
+--------------------------------+------------+------------+--------+
| Avg Day-to-Day Correlation     | {avg_day_corr:>10.3f} | 0.4-0.7    | {'PASS' if 0.4 <= avg_day_corr <= 0.7 else 'WARN':>6} |
| Min Day Correlation            | {min_corr:>10.3f} | >0.2       | {'PASS' if min_corr > 0.2 else 'WARN':>6} |
| Max Day Correlation            | {max_corr:>10.3f} | <0.85      | {'PASS' if max_corr < 0.85 else 'WARN':>6} |
| Avg Daily |Delta|              | {avg_all_deltas:>10.1f} | 5-15       | {'PASS' if 5 <= avg_all_deltas <= 15 else 'WARN':>6} |
+--------------------------------+------------+------------+--------+
| GROUP METERS (UX-critical)     | Value      | Target     | Status |
+--------------------------------+------------+------------+--------+
| Avg Group Day Correlation      | {avg_group_corr:>10.3f} | 0.4-0.7    | {'PASS' if 0.4 <= avg_group_corr <= 0.7 else 'WARN':>6} |
| Avg Group Daily |Delta|        | {avg_group_deltas:>10.1f} | 3-10       | {'PASS' if 3 <= avg_group_deltas <= 10 else 'WARN':>6} |
| Overall Day Correlation        | {overall_corr:>10.3f} | 0.5-0.8    | {'PASS' if 0.5 <= overall_corr <= 0.8 else 'WARN':>6} |
| Overall Daily |Delta|          | {overall_delta:>10.1f} | 2-8        | {'PASS' if 2 <= overall_delta <= 8 else 'WARN':>6} |
+--------------------------------+------------+------------+--------+
""")

    # Identify problematic meters
    too_stable = [m for m, c in correlations.items() if c > 0.85]
    too_volatile = [m for m, c in correlations.items() if c < 0.3]

    if too_stable:
        print(f"  TOO STABLE (corr > 0.85): {', '.join(too_stable)}")
        print(f"    - These meters don't change enough day-to-day")
        print(f"    - Consider adding faster-moving transit planets")

    if too_volatile:
        print(f"\n  TOO VOLATILE (corr < 0.3): {', '.join(too_volatile)}")
        print(f"    - These meters change too much day-to-day")
        print(f"    - Consider adding slower-moving transit planets")

    if not too_stable and not too_volatile:
        print(f"  All meters have healthy day-to-day dynamics")

    # Interpretation guide
    print(f"\n{'='*80}")
    print("INTERPRETATION GUIDE")
    print(f"{'='*80}")
    print("""
  Day-to-day correlation measures how "sticky" meter scores are:

  - corr > 0.85: TOO STABLE - meter barely changes, feels static to user
  - corr 0.7-0.85: Stable - slow evolution, good for outer planet meters
  - corr 0.5-0.7: Moderate - balanced change, ideal for most meters
  - corr 0.3-0.5: Dynamic - noticeable daily shifts, good for lunar meters
  - corr < 0.3: VOLATILE - erratic, may feel random to user

  Avg |Delta| shows typical daily score change (on 0-100 scale):
  - <5: Very small changes, may feel meaningless
  - 5-10: Noticeable but not dramatic
  - 10-15: Significant daily variation
  - >15: Large swings, may feel unstable
""")

    return {
        "correlations": correlations,
        "avg_deltas": avg_deltas,
        "avg_day_corr": avg_day_corr,
        "total_pairs": total_pairs,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Day-to-Day Correlation Analysis")
    parser.add_argument("-n", "--charts", type=int, default=500, help="Number of charts")
    parser.add_argument("-d", "--days", type=int, default=20, help="Day pairs per chart")
    parser.add_argument("-s", "--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    results = run_day_correlation_analysis(
        n_charts=args.charts,
        n_day_pairs=args.days,
        seed=args.seed,
    )

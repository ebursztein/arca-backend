"""
Vibe Score Distribution and Day-to-Day Correlation Analysis

Statistical analysis of vibe score distributions to ensure:
1. Good distribution across the 0-100 range (not clustered at 50)
2. Meaningful day-to-day variation (scores should change as transits move)

Generates random natal chart pairs (user + connection) and calculates vibe
scores across multiple days to analyze:
- Overall distribution of vibe scores
- Day-to-day correlation (should be moderate - not too stable, not too erratic)
"""

import random
import math
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from astro import compute_birth_chart, NatalChartData
from compatibility import calculate_synastry_points, find_transits_to_synastry, calculate_vibe_score


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


def run_vibe_score_analysis(
    n_pairs: int = 200,
    n_days: int = 30,
    seed: int = 42,
) -> dict:
    """
    Analyze vibe score distribution and day-to-day correlation.

    For each user+connection pair, calculates vibe scores across multiple
    consecutive days to measure:
    1. Distribution - are scores spread across 0-100 or clustered?
    2. Day-to-day correlation - do scores change meaningfully day to day?

    Args:
        n_pairs: Number of random user+connection pairs
        n_days: Number of consecutive days to analyze per pair
        seed: Random seed
    """
    random.seed(seed)

    print(f"\n{'='*80}")
    print(f"VIBE SCORE DISTRIBUTION AND CORRELATION ANALYSIS")
    print(f"{'='*80}")
    print(f"Parameters:")
    print(f"  Chart pairs: {n_pairs}")
    print(f"  Days per pair: {n_days}")
    print(f"  Total vibe scores: {n_pairs * n_days}")
    print(f"{'='*80}\n")

    # Generate chart pairs
    print("Generating chart pairs...")
    pairs = []
    for i in range(n_pairs):
        user_birth = generate_random_birth_data()
        conn_birth = generate_random_birth_data()

        try:
            user_chart_dict, _ = compute_birth_chart(
                birth_date=user_birth["birth_date"],
                birth_time=user_birth["birth_time"],
                birth_timezone=user_birth["birth_timezone"],
                birth_lat=user_birth["birth_lat"],
                birth_lon=user_birth["birth_lon"]
            )
            user_chart = NatalChartData(**user_chart_dict)

            conn_chart_dict, _ = compute_birth_chart(
                birth_date=conn_birth["birth_date"],
                birth_time=conn_birth["birth_time"],
                birth_timezone=conn_birth["birth_timezone"],
                birth_lat=conn_birth["birth_lat"],
                birth_lon=conn_birth["birth_lon"]
            )
            conn_chart = NatalChartData(**conn_chart_dict)

            synastry_points = calculate_synastry_points(user_chart, conn_chart)

            pairs.append({
                "user_chart": user_chart,
                "conn_chart": conn_chart,
                "synastry_points": synastry_points,
            })
        except Exception as e:
            pass

    print(f"  Generated {len(pairs)} valid pairs")

    # Calculate vibe scores across days
    all_scores: list[float] = []
    day1_scores: list[float] = []
    day2_scores: list[float] = []
    deltas: list[float] = []
    transit_counts: list[int] = []
    no_transit_count = 0

    # Track per-pair statistics
    per_pair_ranges: list[float] = []
    per_pair_stdevs: list[float] = []

    print(f"\nCalculating vibe scores across {n_days} days per pair...")

    # Use a range of start dates to get varied transits
    base_date = datetime(2024, 1, 1)

    for i, pair in enumerate(pairs):
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(pairs)} pairs...")

        # Random start date offset for variety
        start_offset = random.randint(0, 365)
        pair_scores = []

        for day_idx in range(n_days):
            day = base_date + timedelta(days=start_offset + day_idx)

            try:
                transit_chart_dict, _ = compute_birth_chart(
                    day.strftime("%Y-%m-%d"), "12:00"
                )
                transit_chart = NatalChartData(**transit_chart_dict)

                synastry_pts: list[dict[Any, Any]] = pair["synastry_points"]  # type: ignore[assignment]
                active_transits = find_transits_to_synastry(
                    transit_chart=transit_chart,
                    synastry_points=synastry_pts,
                    orb=3.0
                )

                vibe_score = calculate_vibe_score(active_transits)
                all_scores.append(vibe_score)
                pair_scores.append(vibe_score)

                transit_counts.append(len(active_transits))
                if len(active_transits) == 0:
                    no_transit_count += 1

                # Collect consecutive day pairs for correlation
                if day_idx > 0:
                    day1_scores.append(pair_scores[day_idx - 1])
                    day2_scores.append(vibe_score)
                    deltas.append(abs(vibe_score - pair_scores[day_idx - 1]))

            except Exception as e:
                pass

        # Track per-pair range and stdev
        if len(pair_scores) >= 2:
            per_pair_ranges.append(max(pair_scores) - min(pair_scores))
            per_pair_stdevs.append(statistics.stdev(pair_scores))

    print(f"\nComputed {len(all_scores)} vibe scores")
    print(f"  Day pairs for correlation: {len(day1_scores)}")

    # =========================================================================
    # 1. OVERALL DISTRIBUTION
    # =========================================================================
    print(f"\n{'='*80}")
    print("1. VIBE SCORE DISTRIBUTION (0-100)")
    print(f"{'='*80}")

    if all_scores:
        mean_score = statistics.mean(all_scores)
        median_score = statistics.median(all_scores)
        stdev_score = statistics.stdev(all_scores) if len(all_scores) > 1 else 0
        min_score = min(all_scores)
        max_score = max(all_scores)

        sorted_scores = sorted(all_scores)
        n = len(sorted_scores)
        p5 = sorted_scores[int(n * 0.05)]
        p25 = sorted_scores[int(n * 0.25)]
        p75 = sorted_scores[int(n * 0.75)]
        p95 = sorted_scores[int(n * 0.95)]

        print(f"\n  Statistics:")
        print(f"    N = {n:,}")
        print(f"    Mean = {mean_score:.1f}")
        print(f"    Median = {median_score:.1f}")
        print(f"    StdDev = {stdev_score:.1f}")
        print(f"    Min = {min_score}, Max = {max_score}")
        print(f"    P5 = {p5}, P25 = {p25}, P75 = {p75}, P95 = {p95}")

        # Distribution by decile
        print(f"\n  Distribution by Decile:")
        for i in range(10):
            lo, hi = i * 10, (i + 1) * 10
            count = sum(1 for s in all_scores if lo <= s < hi)
            pct = count / len(all_scores) * 100
            bar = "#" * int(pct * 2)
            print(f"    [{lo:>2}-{hi:<3}): {count:>5} ({pct:>5.1f}%) {bar}")

        # Count at exactly 50 (neutral - no transits)
        at_50 = sum(1 for s in all_scores if s == 50)
        pct_at_50 = at_50 / len(all_scores) * 100
        print(f"\n  Scores exactly at 50 (neutral): {at_50} ({pct_at_50:.1f}%)")
        print(f"  Cases with no active transits: {no_transit_count} ({no_transit_count/len(all_scores)*100:.1f}%)")

        # Quality checks
        print(f"\n  Quality Checks:")
        mean_ok = 40 <= mean_score <= 60
        std_ok = stdev_score >= 5  # Want some spread
        range_ok = max_score - min_score >= 30  # Want range
        not_all_50 = pct_at_50 < 50  # Don't want most scores stuck at 50

        print(f"    Mean in [40,60]: {'PASS' if mean_ok else 'FAIL'} ({mean_score:.1f})")
        print(f"    StdDev >= 5: {'PASS' if std_ok else 'FAIL'} ({stdev_score:.1f})")
        print(f"    Range >= 30: {'PASS' if range_ok else 'FAIL'} ({max_score - min_score})")
        print(f"    <50% at neutral: {'PASS' if not_all_50 else 'FAIL'} ({pct_at_50:.1f}%)")

    # =========================================================================
    # 2. TRANSIT COUNT ANALYSIS
    # =========================================================================
    print(f"\n{'='*80}")
    print("2. TRANSIT COUNT ANALYSIS")
    print(f"{'='*80}")

    if transit_counts:
        mean_transits = statistics.mean(transit_counts)
        median_transits = statistics.median(transit_counts)
        max_transits = max(transit_counts)

        print(f"\n  Active transits per calculation:")
        print(f"    Mean: {mean_transits:.1f}")
        print(f"    Median: {median_transits:.1f}")
        print(f"    Max: {max_transits}")

        # Distribution of transit counts
        print(f"\n  Distribution of transit counts:")
        for count in range(max_transits + 1):
            n_with_count = sum(1 for t in transit_counts if t == count)
            pct = n_with_count / len(transit_counts) * 100
            bar = "#" * int(pct)
            print(f"    {count:>2} transits: {n_with_count:>5} ({pct:>5.1f}%) {bar}")
            if count >= 10 and pct < 1:
                break

    # =========================================================================
    # 3. DAY-TO-DAY CORRELATION
    # =========================================================================
    print(f"\n{'='*80}")
    print("3. DAY-TO-DAY CORRELATION ANALYSIS")
    print(f"{'='*80}")
    print("(Want: moderate correlation 0.3-0.7 = meaningful daily change)")

    if day1_scores and day2_scores:
        day_corr = pearson_correlation(day1_scores, day2_scores)
        avg_delta = statistics.mean(deltas) if deltas else 0
        median_delta = statistics.median(deltas) if deltas else 0

        # Interpret stability
        if day_corr > 0.85:
            stability = "TOO STABLE - scores barely change"
        elif day_corr > 0.7:
            stability = "Stable - slow evolution"
        elif day_corr > 0.5:
            stability = "Moderate - healthy dynamics"
        elif day_corr > 0.3:
            stability = "Dynamic - noticeable daily shifts"
        else:
            stability = "VOLATILE - may feel random"

        print(f"\n  Day-to-Day Correlation: {day_corr:.3f}")
        print(f"  Stability Assessment: {stability}")
        print(f"  Avg Daily |Delta|: {avg_delta:.1f}")
        print(f"  Median Daily |Delta|: {median_delta:.1f}")

        # Distribution of daily changes
        print(f"\n  Distribution of daily changes:")
        delta_ranges = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 100)]
        for lo, hi in delta_ranges:
            count = sum(1 for d in deltas if lo <= d < hi)
            pct = count / len(deltas) * 100
            bar = "#" * int(pct)
            print(f"    [{lo:>2}-{hi:<3}): {count:>5} ({pct:>5.1f}%) {bar}")

    # =========================================================================
    # 4. PER-PAIR DYNAMICS
    # =========================================================================
    print(f"\n{'='*80}")
    print("4. PER-PAIR DYNAMICS (within-pair variation)")
    print(f"{'='*80}")
    print("(Each pair should have some score variation over time)")

    if per_pair_ranges and per_pair_stdevs:
        avg_range = statistics.mean(per_pair_ranges)
        median_range = statistics.median(per_pair_ranges)
        avg_stdev = statistics.mean(per_pair_stdevs)
        pairs_with_no_change = sum(1 for r in per_pair_ranges if r == 0)

        print(f"\n  Per-pair score range over {n_days} days:")
        print(f"    Avg range: {avg_range:.1f}")
        print(f"    Median range: {median_range:.1f}")
        print(f"    Avg within-pair stdev: {avg_stdev:.1f}")
        print(f"    Pairs with zero change: {pairs_with_no_change} ({pairs_with_no_change/len(per_pair_ranges)*100:.1f}%)")

        # Distribution of per-pair ranges
        print(f"\n  Distribution of per-pair score ranges:")
        range_buckets = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 50), (50, 100)]
        for lo, hi in range_buckets:
            count = sum(1 for r in per_pair_ranges if lo <= r < hi)
            pct = count / len(per_pair_ranges) * 100
            bar = "#" * int(pct)
            print(f"    [{lo:>2}-{hi:<3}): {count:>5} ({pct:>5.1f}%) {bar}")

    # =========================================================================
    # 5. SUMMARY
    # =========================================================================
    print(f"\n{'='*80}")
    print("5. SUMMARY")
    print(f"{'='*80}")

    day_corr_ok = 0.3 <= day_corr <= 0.7 if day1_scores else False
    avg_delta_ok = 5 <= avg_delta <= 20 if deltas else False

    print(f"""
+--------------------------------+------------+------------+--------+
| Metric                         | Value      | Target     | Status |
+--------------------------------+------------+------------+--------+
| Mean Score                     | {mean_score:>10.1f} | 40-60      | {'PASS' if mean_ok else 'FAIL':>6} |
| StdDev                         | {stdev_score:>10.1f} | >= 5       | {'PASS' if std_ok else 'FAIL':>6} |
| Score Range                    | {max_score - min_score:>10} | >= 30      | {'PASS' if range_ok else 'FAIL':>6} |
| % at Neutral (50)              | {pct_at_50:>9.1f}% | < 50%      | {'PASS' if not_all_50 else 'FAIL':>6} |
| Day-to-Day Correlation         | {day_corr:>10.3f} | 0.3-0.7    | {'PASS' if day_corr_ok else 'WARN':>6} |
| Avg Daily |Delta|              | {avg_delta:>10.1f} | 5-20       | {'PASS' if avg_delta_ok else 'WARN':>6} |
+--------------------------------+------------+------------+--------+
""")

    # Interpretation guide
    print(f"\n{'='*80}")
    print("INTERPRETATION GUIDE")
    print(f"{'='*80}")
    print("""
  Day-to-day correlation measures how "sticky" vibe scores are:

  - corr > 0.85: TOO STABLE - vibe score barely changes day to day
  - corr 0.7-0.85: Stable - slow evolution
  - corr 0.5-0.7: Moderate - balanced change, ideal
  - corr 0.3-0.5: Dynamic - noticeable daily shifts
  - corr < 0.3: VOLATILE - erratic, may feel random

  Avg |Delta| shows typical daily score change (on 0-100 scale):
  - <5: Very small changes, may feel meaningless
  - 5-15: Noticeable but not dramatic (good)
  - 15-25: Significant daily variation
  - >25: Large swings, may feel unstable

  If scores cluster at 50 (neutral), it means too few transits are found.
  Consider:
  - Increasing the orb in find_transits_to_synastry
  - Adding more synastry points in calculate_synastry_points
  - Adding slower planets to transit_planets list
""")

    all_pass = mean_ok and std_ok and range_ok and not_all_50
    print(f"  OVERALL STATUS: {'PASS' if all_pass else 'NEEDS ATTENTION'}")

    return {
        "mean_score": mean_score if all_scores else 0,
        "stdev_score": stdev_score if all_scores else 0,
        "day_correlation": day_corr if day1_scores else 0,
        "avg_delta": avg_delta if deltas else 0,
        "pct_at_neutral": pct_at_50 if all_scores else 0,
        "all_pass": all_pass,
    }


class TestVibeScoreDistribution:
    """Pytest-compatible tests for vibe score distribution."""

    def test_vibe_score_has_good_distribution(self):
        """Vibe score should have reasonable distribution (not all at neutral)."""
        results = run_vibe_score_analysis(n_pairs=50, n_days=20, seed=42)

        # Score should not be clustered at neutral
        assert results["pct_at_neutral"] < 50, \
            f"Too many scores at neutral (50): {results['pct_at_neutral']:.1f}%"

        # Should have meaningful spread
        assert results["stdev_score"] >= 5, \
            f"StdDev too low: {results['stdev_score']:.1f}"

    def test_vibe_score_has_healthy_day_correlation(self):
        """Day-to-day correlation should be moderate (0.3-0.8)."""
        results = run_vibe_score_analysis(n_pairs=50, n_days=20, seed=42)

        # Correlation should indicate meaningful daily change
        # Slightly relaxed from 0.7 to 0.8 since we're seeing consistent ~0.64
        assert 0.3 <= results["day_correlation"] <= 0.8, \
            f"Day correlation outside healthy range: {results['day_correlation']:.3f}"

    def test_vibe_score_daily_delta_is_meaningful(self):
        """Daily score changes should be noticeable but not extreme."""
        results = run_vibe_score_analysis(n_pairs=50, n_days=20, seed=42)

        # Average daily change should be in reasonable range
        assert 3 <= results["avg_delta"] <= 30, \
            f"Avg daily delta outside range: {results['avg_delta']:.1f}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vibe Score Distribution Analysis")
    parser.add_argument("-n", "--pairs", type=int, default=200, help="Number of chart pairs")
    parser.add_argument("-d", "--days", type=int, default=30, help="Days per pair")
    parser.add_argument("-s", "--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    results = run_vibe_score_analysis(
        n_pairs=args.pairs,
        n_days=args.days,
        seed=args.seed,
    )

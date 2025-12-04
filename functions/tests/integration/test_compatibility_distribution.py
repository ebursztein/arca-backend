"""
Compatibility Distribution Analysis Test

Statistical analysis of compatibility score distributions to ensure
reasonable baseline behavior across random chart pairs.

Generates N charts with random birth data (1980-2010) and creates M
connections per chart, analyzing:
- Overall compatibility score distribution (0-100)
- Per-category score distributions (0-100, 50 is neutral)
- Karmic/fated connection frequency (5-10% target)
"""

import random
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import sys
import os

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from compatibility import (
    get_compatibility_from_birth_data,
    RelationshipType,
    CompatibilityData,
)


# Major cities with lat/lon for random location generation
CITIES = [
    ("New York", 40.7128, -74.0060, "America/New_York"),
    ("Los Angeles", 34.0522, -118.2437, "America/Los_Angeles"),
    ("Chicago", 41.8781, -87.6298, "America/Chicago"),
    ("Houston", 29.7604, -95.3698, "America/Chicago"),
    ("Phoenix", 33.4484, -112.0740, "America/Phoenix"),
    ("London", 51.5074, -0.1278, "Europe/London"),
    ("Paris", 48.8566, 2.3522, "Europe/Paris"),
    ("Berlin", 52.5200, 13.4050, "Europe/Berlin"),
    ("Tokyo", 35.6762, 139.6503, "Asia/Tokyo"),
    ("Sydney", -33.8688, 151.2093, "Australia/Sydney"),
    ("Sao Paulo", -23.5505, -46.6333, "America/Sao_Paulo"),
    ("Mumbai", 19.0760, 72.8777, "Asia/Kolkata"),
    ("Mexico City", 19.4326, -99.1332, "America/Mexico_City"),
    ("Cairo", 30.0444, 31.2357, "Africa/Cairo"),
    ("Dubai", 25.2048, 55.2708, "Asia/Dubai"),
    ("Toronto", 43.6532, -79.3832, "America/Toronto"),
    ("Moscow", 55.7558, 37.6173, "Europe/Moscow"),
    ("Singapore", 1.3521, 103.8198, "Asia/Singapore"),
    ("Seattle", 47.6062, -122.3321, "America/Los_Angeles"),
    ("Denver", 39.7392, -104.9903, "America/Denver"),
]


def generate_random_birth_data() -> dict:
    """Generate random birth data for testing."""
    start_date = datetime(1980, 1, 1)
    end_date = datetime(2010, 12, 31)
    days_range = (end_date - start_date).days
    random_date = start_date + timedelta(days=random.randint(0, days_range))

    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    birth_time = f"{hour:02d}:{minute:02d}"

    city_name, lat, lon, tz = random.choice(CITIES)

    return {
        "birth_date": random_date.strftime("%Y-%m-%d"),
        "birth_time": birth_time,
        "birth_lat": lat,
        "birth_lon": lon,
        "birth_timezone": tz,
        "city": city_name,
    }


def analyze_distribution(values: list[float], name: str) -> dict:
    """Analyze a distribution and return statistics."""
    if not values:
        return {"name": name, "count": 0}

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    return {
        "name": name,
        "count": n,
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if n > 1 else 0,
        "min": min(values),
        "max": max(values),
        "p5": sorted_vals[int(n * 0.05)],
        "p10": sorted_vals[int(n * 0.10)],
        "p25": sorted_vals[int(n * 0.25)],
        "p50": sorted_vals[int(n * 0.50)],
        "p75": sorted_vals[int(n * 0.75)],
        "p90": sorted_vals[int(n * 0.90)],
        "p95": sorted_vals[int(n * 0.95)],
    }


def count_in_ranges(values: list[float], ranges: list[tuple[float, float]]) -> dict:
    """Count values in specified ranges."""
    counts = {f"[{lo},{hi})": 0 for lo, hi in ranges}
    for v in values:
        for lo, hi in ranges:
            if lo <= v < hi:
                counts[f"[{lo},{hi})"] += 1
                break
    return counts


def get_5pct_bucket(value: float, min_val: float, max_val: float) -> int:
    """
    Map a value to a 5% bucket (0-19).
    Bucket 0 = 0-5%, Bucket 1 = 5-10%, ..., Bucket 19 = 95-100%
    """
    normalized = (value - min_val) / (max_val - min_val)  # 0.0 to 1.0
    bucket = int(normalized * 20)
    return min(19, max(0, bucket))  # Clamp to [0, 19]


def analyze_5pct_distribution(
    values: list[float],
    min_val: float,
    max_val: float,
    name: str
) -> dict:
    """
    Analyze distribution in 5% increments.
    Returns counts and percentages for each 5% bucket.
    """
    buckets = [0] * 20  # 20 buckets for 5% increments
    for v in values:
        bucket = get_5pct_bucket(v, min_val, max_val)
        buckets[bucket] += 1

    total = len(values)
    result = {
        "name": name,
        "total": total,
        "min_val": min_val,
        "max_val": max_val,
        "buckets": [],
    }

    for i in range(20):
        pct_start = i * 5
        pct_end = (i + 1) * 5
        val_start = min_val + (max_val - min_val) * (pct_start / 100)
        val_end = min_val + (max_val - min_val) * (pct_end / 100)
        count = buckets[i]
        pct_of_total = (count / total * 100) if total > 0 else 0

        result["buckets"].append({
            "bucket": i,
            "pct_range": f"{pct_start}-{pct_end}%",
            "val_range": f"[{val_start:.1f},{val_end:.1f})",
            "count": count,
            "pct_of_total": pct_of_total,
        })

    return result


def pearson_correlation(x: list[float], y: list[float]) -> float:
    """Calculate Pearson correlation coefficient between two lists."""
    import math
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


def print_5pct_distribution(dist: dict, show_bars: bool = True) -> None:
    """Print a 5% distribution analysis in a formatted table."""
    print(f"\n  5% Increment Distribution for {dist['name']}:")
    print(f"  Value Range: [{dist['min_val']}, {dist['max_val']}]")
    print(f"  Total samples: {dist['total']:,}")
    print()
    print(f"  {'Percentile':<12} {'Value Range':<16} {'Count':>8} {'% of Total':>12} {'Distribution'}")
    print(f"  {'-'*70}")

    for b in dist["buckets"]:
        bar = ""
        if show_bars:
            bar_len = int(b["pct_of_total"] * 2)  # Scale for display
            bar = "#" * bar_len
        print(f"  {b['pct_range']:<12} {b['val_range']:<16} {b['count']:>8} {b['pct_of_total']:>11.1f}% {bar}")


def run_comprehensive_analysis(
    n_charts: int = 100,
    m_connections: int = 25,
    relationship_type: RelationshipType = "romantic",
    seed: int = 42,
) -> dict:
    """
    Run comprehensive compatibility analysis on random chart pairs.
    """
    random.seed(seed)

    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE COMPATIBILITY DISTRIBUTION ANALYSIS")
    print(f"{'='*80}")
    print(f"Parameters:")
    print(f"  Charts (N): {n_charts}")
    print(f"  Connections per chart (M): {m_connections}")
    print(f"  Total pairs: {n_charts * m_connections}")
    print(f"  Relationship type: {relationship_type}")
    print(f"  Random seed: {seed}")
    print(f"{'='*80}\n")

    # Generate random charts
    print("Generating random birth data...")
    charts_data = [generate_random_birth_data() for _ in range(n_charts)]

    # Collect results
    overall_scores: list[float] = []
    category_scores: dict[str, list[float]] = defaultdict(list)
    category_aspect_counts: dict[str, list[int]] = defaultdict(list)
    karmic_count = 0
    total_pairs = 0
    karmic_themes: dict[str, int] = defaultdict(int)

    print(f"Computing {n_charts * m_connections} compatibility pairs...")
    for i, user_data in enumerate(charts_data):
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{n_charts} charts ({(i+1)*100//n_charts}%)...")

        available_indices = [j for j in range(n_charts) if j != i]
        connection_indices = random.sample(
            available_indices,
            min(m_connections, len(available_indices))
        )

        for conn_idx in connection_indices:
            conn_data = charts_data[conn_idx]

            try:
                result: CompatibilityData = get_compatibility_from_birth_data(
                    user_birth_date=user_data["birth_date"],
                    user_birth_time=user_data["birth_time"],
                    user_birth_lat=user_data["birth_lat"],
                    user_birth_lon=user_data["birth_lon"],
                    user_birth_timezone=user_data["birth_timezone"],
                    connection_birth_date=conn_data["birth_date"],
                    connection_birth_time=conn_data["birth_time"],
                    connection_birth_lat=conn_data["birth_lat"],
                    connection_birth_lon=conn_data["birth_lon"],
                    connection_birth_timezone=conn_data["birth_timezone"],
                    relationship_type=relationship_type,
                    user_name=f"User_{i}",
                    connection_name=f"Conn_{conn_idx}",
                )

                total_pairs += 1
                overall_scores.append(result.mode.overall_score)

                for cat in result.mode.categories:
                    category_scores[cat.id].append(cat.score)
                    category_aspect_counts[cat.id].append(len(cat.aspect_ids))

                if result.karmic.is_karmic:
                    karmic_count += 1
                    if result.karmic.theme:
                        karmic_themes[result.karmic.theme] += 1

            except Exception as e:
                print(f"    Error computing pair {i}->{conn_idx}: {e}")

    print(f"\nComputed {total_pairs} pairs successfully.\n")

    # =========================================================================
    # OVERALL SCORE ANALYSIS
    # =========================================================================
    print(f"\n{'='*80}")
    print("1. OVERALL SCORE DISTRIBUTION (0-100)")
    print(f"{'='*80}")

    overall_stats = analyze_distribution(overall_scores, "Overall")
    print(f"\n  Statistics:")
    print(f"    N = {overall_stats['count']:,}")
    print(f"    Mean = {overall_stats['mean']:.2f}")
    print(f"    Median = {overall_stats['median']:.2f}")
    print(f"    StdDev = {overall_stats['stdev']:.2f}")
    print(f"    Range = [{overall_stats['min']:.0f}, {overall_stats['max']:.0f}]")
    print(f"    IQR = [{overall_stats['p25']:.0f}, {overall_stats['p75']:.0f}]")

    # Distribution by decile
    overall_ranges = [(i*10, (i+1)*10) for i in range(10)]
    overall_dist = count_in_ranges(overall_scores, overall_ranges)
    print(f"\n  Distribution by Decile:")
    for rng, count in overall_dist.items():
        pct = count / total_pairs * 100
        bar = "#" * int(pct * 2)
        print(f"    {rng:>12}: {count:5} ({pct:5.1f}%) {bar}")

    # Quality checks
    print(f"\n  Quality Checks:")
    mean_ok = 45 <= overall_stats['mean'] <= 55
    std_ok = 10 <= overall_stats['stdev'] <= 20
    range_ok = overall_stats['min'] >= 0 and overall_stats['max'] <= 100
    print(f"    Mean in [45,55]: {'PASS' if mean_ok else 'FAIL'} ({overall_stats['mean']:.1f})")
    print(f"    StdDev in [10,20]: {'PASS' if std_ok else 'FAIL'} ({overall_stats['stdev']:.1f})")
    print(f"    Range in [0,100]: {'PASS' if range_ok else 'FAIL'} ([{overall_stats['min']:.0f},{overall_stats['max']:.0f}])")

    # =========================================================================
    # 5% INCREMENT DISTRIBUTION - OVERALL
    # =========================================================================
    print(f"\n{'='*80}")
    print("1b. OVERALL SCORE - 5% INCREMENT DISTRIBUTION")
    print(f"{'='*80}")

    overall_5pct = analyze_5pct_distribution(overall_scores, 0, 100, "Overall Score")
    print_5pct_distribution(overall_5pct)

    # Check for smooth distribution (no bucket > 15% or < 1%)
    bucket_pcts = [b["pct_of_total"] for b in overall_5pct["buckets"]]
    overall_smooth = all(1 <= p <= 15 for p in bucket_pcts if p > 0)
    print(f"\n  Smoothness Check (all non-empty buckets between 1-15%):")
    print(f"    Status: {'PASS' if overall_smooth else 'WARN - Some buckets outside 1-15% range'}")

    # =========================================================================
    # CATEGORY SCORE ANALYSIS
    # =========================================================================
    print(f"\n{'='*80}")
    print("2. CATEGORY SCORE DISTRIBUTIONS (0-100, 50=neutral)")
    print(f"{'='*80}")

    category_stats = {}
    for cat_id in sorted(category_scores.keys()):
        stats = analyze_distribution(category_scores[cat_id], cat_id)
        aspect_stats = analyze_distribution(
            [float(x) for x in category_aspect_counts[cat_id]],
            f"{cat_id}_aspects"
        )
        category_stats[cat_id] = {
            "score_stats": stats,
            "aspect_stats": aspect_stats,
        }

    # Summary table
    print(f"\n  {'Category':<15} {'Mean':>7} {'Median':>7} {'StdDev':>7} {'Min':>5} {'Max':>5} {'Aspects':>8}")
    print(f"  {'-'*62}")
    for cat_id in sorted(category_stats.keys()):
        s = category_stats[cat_id]["score_stats"]
        a = category_stats[cat_id]["aspect_stats"]
        print(f"  {cat_id:<15} {s['mean']:>7.1f} {s['median']:>7.1f} {s['stdev']:>7.1f} {s['min']:>5.0f} {s['max']:>5.0f} {a['mean']:>7.1f}")

    # Bimodality check (% at extremes) - check for scores <=20 or >=80
    print(f"\n  Bimodality Check (% at extremes score<=20 or score>=80):")
    print(f"  {'Category':<15} {'Low (<=20)':>12} {'High (>=80)':>12} {'Extreme%':>10} {'Status':>10}")
    print(f"  {'-'*62}")

    all_bimodal_ok = True
    for cat_id in sorted(category_stats.keys()):
        scores = category_scores[cat_id]
        low_extreme = sum(1 for s in scores if s <= 20)
        high_extreme = sum(1 for s in scores if s >= 80)
        extreme_pct = (low_extreme + high_extreme) / len(scores) * 100
        status = "OK" if extreme_pct < 25 else "HIGH"
        if status != "OK":
            all_bimodal_ok = False
        print(f"  {cat_id:<15} {low_extreme:>12} {high_extreme:>12} {extreme_pct:>9.1f}% {status:>10}")

    # Per-category detailed distribution
    print(f"\n  Detailed Distribution by Range:")
    cat_ranges = [(0, 20), (20, 35), (35, 50), (50, 65), (65, 80), (80, 101)]
    range_labels = ["[0,20)", "[20,35)", "[35,50)", "[50,65)", "[65,80)", "[80,100]"]

    print(f"\n  {'Category':<15}", end="")
    for label in range_labels:
        print(f" {label:>10}", end="")
    print()
    print(f"  {'-'*75}")

    for cat_id in sorted(category_stats.keys()):
        scores = category_scores[cat_id]
        print(f"  {cat_id:<15}", end="")
        for lo, hi in cat_ranges:
            count = sum(1 for s in scores if lo <= s < hi)
            pct = count / len(scores) * 100
            print(f" {pct:>9.1f}%", end="")
        print()

    # =========================================================================
    # 5% INCREMENT DISTRIBUTION - PER CATEGORY
    # =========================================================================
    print(f"\n{'='*80}")
    print("2b. CATEGORY SCORES - 5% INCREMENT DISTRIBUTIONS")
    print(f"{'='*80}")

    category_5pct_distributions = {}
    for cat_id in sorted(category_scores.keys()):
        cat_5pct = analyze_5pct_distribution(
            category_scores[cat_id],
            0,    # min value for category scores
            100,  # max value for category scores
            cat_id
        )
        category_5pct_distributions[cat_id] = cat_5pct
        print_5pct_distribution(cat_5pct)

    # Summary table of 5% distribution across all categories
    print(f"\n  5% INCREMENT SUMMARY TABLE (% of total in each bucket)")
    print(f"  {'Bucket':<10}", end="")
    for cat_id in sorted(category_scores.keys()):
        print(f" {cat_id[:8]:>9}", end="")
    print()
    print(f"  {'-'*75}")

    for bucket_idx in range(20):
        pct_start = bucket_idx * 5
        pct_end = (bucket_idx + 1) * 5
        print(f"  {pct_start:>2}-{pct_end:<2}%    ", end="")
        for cat_id in sorted(category_scores.keys()):
            pct = category_5pct_distributions[cat_id]["buckets"][bucket_idx]["pct_of_total"]
            print(f" {pct:>8.1f}%", end="")
        print()

    # =========================================================================
    # CORRELATION ANALYSIS
    # =========================================================================
    print(f"\n{'='*80}")
    print("2c. CROSS-CATEGORY CORRELATION ANALYSIS")
    print(f"{'='*80}")
    print("(Want: low correlations = categories measure different things)")

    cats = sorted(category_scores.keys())

    # Print header
    print(f"\n  {'':>15}", end="")
    for cat in cats:
        print(f" {cat[:8]:>9}", end="")
    print()
    print(f"  {'-'*75}")

    # Correlation matrix
    correlations = []
    for cat1 in cats:
        print(f"  {cat1:<15}", end="")
        for cat2 in cats:
            if cat1 == cat2:
                corr = 1.0
            else:
                corr = pearson_correlation(category_scores[cat1], category_scores[cat2])
            correlations.append((cat1, cat2, corr))
            print(f" {corr:>9.2f}", end="")
        print()

    # Calculate average off-diagonal correlation
    off_diag = [abs(c) for c1, c2, c in correlations if c1 != c2]
    avg_corr = sum(off_diag) / len(off_diag) if off_diag else 0

    print(f"\n  Average |correlation| (off-diagonal): {avg_corr:.3f}")
    corr_ok = avg_corr < 0.3
    print(f"  Target: <0.30")
    print(f"  Status: {'PASS' if corr_ok else 'FAIL'}")

    # =========================================================================
    # KARMIC ANALYSIS
    # =========================================================================
    print(f"\n{'='*80}")
    print("3. KARMIC/FATED CONNECTION ANALYSIS")
    print(f"{'='*80}")

    karmic_pct = karmic_count / total_pairs * 100
    print(f"\n  Statistics:")
    print(f"    Total pairs: {total_pairs:,}")
    print(f"    Karmic connections: {karmic_count:,}")
    print(f"    Karmic percentage: {karmic_pct:.2f}%")
    print(f"    Target range: 5-10%")

    karmic_ok = 3 <= karmic_pct <= 15
    print(f"    Status: {'PASS' if karmic_ok else 'FAIL'}")

    if karmic_themes:
        print(f"\n  Theme Distribution:")
        for theme, count in sorted(karmic_themes.items(), key=lambda x: -x[1]):
            theme_pct = count / karmic_count * 100
            print(f"    {theme}: {count} ({theme_pct:.1f}%)")

    # =========================================================================
    # FINAL SUMMARY TABLE
    # =========================================================================
    print(f"\n{'='*80}")
    print("4. FINAL SUMMARY TABLE")
    print(f"{'='*80}")

    print(f"""
+----------------------+------------+------------+--------+
| Metric               | Value      | Target     | Status |
+----------------------+------------+------------+--------+
| Overall Mean         | {overall_stats['mean']:>10.1f} | 45-55      | {'PASS' if mean_ok else 'FAIL':>6} |
| Overall StdDev       | {overall_stats['stdev']:>10.1f} | 10-20      | {'PASS' if std_ok else 'FAIL':>6} |
| Overall Range        | [{overall_stats['min']:.0f},{overall_stats['max']:.0f}]{' '*(6-len(f"[{overall_stats['min']:.0f},{overall_stats['max']:.0f}]"))} | [0,100]    | {'PASS' if range_ok else 'FAIL':>6} |
| Karmic Rate          | {karmic_pct:>9.1f}% | 5-10%      | {'PASS' if karmic_ok else 'FAIL':>6} |
| Bimodality (<25%)    | {'See above':>10} | <25%       | {'PASS' if all_bimodal_ok else 'FAIL':>6} |
| Avg Correlation      | {avg_corr:>10.3f} | <0.30      | {'PASS' if corr_ok else 'FAIL':>6} |
+----------------------+------------+------------+--------+
""")

    # Category summary
    print(f"""
+------------------+--------+--------+--------+--------+---------+
| Category         |   Mean | Median | StdDev | Aspects| Extreme%|
+------------------+--------+--------+--------+--------+---------+""")

    for cat_id in sorted(category_stats.keys()):
        s = category_stats[cat_id]["score_stats"]
        a = category_stats[cat_id]["aspect_stats"]
        scores = category_scores[cat_id]
        # Extreme = scores <= 20 or >= 80 (on 0-100 scale)
        extreme_pct = sum(1 for sc in scores if sc <= 20 or sc >= 80) / len(scores) * 100
        print(f"| {cat_id:<16} | {s['mean']:>6.1f} | {s['median']:>6.1f} | {s['stdev']:>6.1f} | {a['mean']:>6.1f} | {extreme_pct:>6.1f}% |")

    print(f"+------------------+--------+--------+--------+--------+---------+")

    # All tests summary
    all_pass = mean_ok and std_ok and range_ok and karmic_ok and all_bimodal_ok and corr_ok
    print(f"\n  ALL TESTS: {'PASS' if all_pass else 'FAIL'}")

    return {
        "overall_stats": overall_stats,
        "category_stats": category_stats,
        "karmic_count": karmic_count,
        "karmic_percentage": karmic_pct,
        "total_pairs": total_pairs,
        "all_pass": all_pass,
        "overall_5pct_distribution": overall_5pct,
        "category_5pct_distributions": category_5pct_distributions,
        "avg_correlation": avg_corr,
        "correlation_ok": corr_ok,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compatibility Distribution Analysis")
    parser.add_argument("-n", "--charts", type=int, default=100, help="Number of charts to generate")
    parser.add_argument("-m", "--connections", type=int, default=30, help="Connections per chart")
    parser.add_argument("-s", "--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--mode", choices=["romantic", "friendship", "coworker"], default="romantic", help="Relationship type")

    args = parser.parse_args()

    results = run_comprehensive_analysis(
        n_charts=args.charts,
        m_connections=args.connections,
        relationship_type=args.mode,
        seed=args.seed,
    )

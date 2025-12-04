"""
Astrometer Distribution Analysis Test

Statistical analysis of astrometer score distributions to ensure
reasonable baseline behavior and low cross-meter correlation.

Generates N charts with random birth data and calculates all 17 meters
over M random transit dates per chart, analyzing:
- Per-meter score distributions (unified scores 0-100)
- Cross-meter correlation matrix
- Group-level aggregations
"""

import random
import math
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import sys
import os

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from astro import compute_birth_chart
from astrometers.meters import get_meters
from astrometers.hierarchy import Meter, MeterGroupV2, METER_TO_GROUP_V2


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

# All 17 meter names in order
METER_NAMES = [
    'clarity', 'focus', 'communication',
    'connections', 'resilience', 'vulnerability',
    'energy', 'drive', 'strength',
    'vision', 'flow', 'intuition', 'creativity',
    'momentum', 'ambition', 'evolution', 'circle'
]


def generate_random_birth_data() -> dict:
    """Generate random birth data for testing."""
    start_date = datetime(1960, 1, 1)
    end_date = datetime(2005, 12, 31)
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


def generate_random_transit_date() -> datetime:
    """Generate a random transit date (2020-2025)."""
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 11, 30)
    days_range = (end_date - start_date).days
    random_date = start_date + timedelta(days=random.randint(0, days_range))
    return random_date


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


def get_5pct_bucket(value: float, min_val: float, max_val: float) -> int:
    """
    Map a value to a 5% bucket (0-19).
    Bucket 0 = 0-5%, Bucket 1 = 5-10%, ..., Bucket 19 = 95-100%
    """
    if max_val == min_val:
        return 10  # middle bucket
    normalized = (value - min_val) / (max_val - min_val)
    bucket = int(normalized * 20)
    return min(19, max(0, bucket))


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
    buckets = [0] * 20
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
            bar_len = int(b["pct_of_total"] * 2)
            bar = "#" * bar_len
        print(f"  {b['pct_range']:<12} {b['val_range']:<16} {b['count']:>8} {b['pct_of_total']:>11.1f}% {bar}")


def run_comprehensive_analysis(
    n_charts: int = 100,
    m_dates: int = 30,
    seed: int = 42,
) -> dict:
    """
    Run comprehensive astrometer analysis on random chart/date pairs.
    """
    random.seed(seed)

    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE ASTROMETER DISTRIBUTION ANALYSIS")
    print(f"{'='*80}")
    print(f"Parameters:")
    print(f"  Charts (N): {n_charts}")
    print(f"  Transit dates per chart (M): {m_dates}")
    print(f"  Total samples: {n_charts * m_dates}")
    print(f"  Random seed: {seed}")
    print(f"{'='*80}\n")

    # Generate random charts
    print("Generating random birth data...")
    charts_data = []
    for i in range(n_charts):
        birth_data = generate_random_birth_data()
        try:
            natal_chart, _ = compute_birth_chart(
                birth_date=birth_data["birth_date"],
                birth_time=birth_data["birth_time"],
                birth_timezone=birth_data["birth_timezone"],
                birth_lat=birth_data["birth_lat"],
                birth_lon=birth_data["birth_lon"]
            )
            charts_data.append({
                "birth_data": birth_data,
                "natal_chart": natal_chart,
            })
        except Exception as e:
            print(f"  Error generating chart {i}: {e}")

    print(f"  Generated {len(charts_data)} valid charts")

    # Collect meter scores
    meter_scores: dict[str, list[float]] = defaultdict(list)
    total_samples = 0
    errors = 0

    print(f"\nCalculating {len(charts_data) * m_dates} meter readings...")
    for i, chart_data in enumerate(charts_data):
        if (i + 1) % 25 == 0:
            print(f"  Progress: {i+1}/{len(charts_data)} charts ({(i+1)*100//len(charts_data)}%)...")

        natal_chart = chart_data["natal_chart"]

        # Generate M random transit dates for this chart
        for _ in range(m_dates):
            transit_date = generate_random_transit_date()
            date_str = transit_date.strftime("%Y-%m-%d")

            try:
                transit_chart, _ = compute_birth_chart(date_str, "12:00")
                all_meters = get_meters(
                    natal_chart,
                    transit_chart,
                    transit_date,
                    calculate_trends=False
                )

                # Collect unified scores for all 17 meters
                for meter_name in METER_NAMES:
                    reading = getattr(all_meters, meter_name)
                    meter_scores[meter_name].append(reading.unified_score)

                total_samples += 1

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"    Error: {e}")

    print(f"\nComputed {total_samples} samples successfully ({errors} errors).\n")

    # =========================================================================
    # PER-METER DISTRIBUTION ANALYSIS
    # =========================================================================
    print(f"\n{'='*80}")
    print("1. PER-METER SCORE DISTRIBUTIONS (Unified Score 0-100)")
    print(f"{'='*80}")

    meter_stats = {}
    for meter_name in METER_NAMES:
        stats = analyze_distribution(meter_scores[meter_name], meter_name)
        meter_stats[meter_name] = stats

    # Summary table
    print(f"\n  {'Meter':<15} {'Mean':>7} {'Median':>7} {'StdDev':>7} {'Min':>5} {'Max':>5} {'P10':>6} {'P90':>6}")
    print(f"  {'-'*70}")
    for meter_name in METER_NAMES:
        s = meter_stats[meter_name]
        print(f"  {meter_name:<15} {s['mean']:>7.1f} {s['median']:>7.1f} {s['stdev']:>7.1f} {s['min']:>5.0f} {s['max']:>5.0f} {s['p10']:>6.1f} {s['p90']:>6.1f}")

    # Quality checks per meter
    # NOTE: unified_score range is 20-100 (new sigmoid+harmony formula)
    # Good distribution: mean around 45-55, stddev 5-15
    print(f"\n  Quality Checks (Mean in [45,55], StdDev in [5,15]):")
    print(f"  {'Meter':<15} {'Mean':>7} {'StdDev':>7} {'Mean OK':>10} {'StdDev OK':>10}")
    print(f"  {'-'*55}")

    all_mean_ok = True
    all_std_ok = True
    for meter_name in METER_NAMES:
        s = meter_stats[meter_name]
        mean_ok = 45 <= s['mean'] <= 55
        std_ok = 5 <= s['stdev'] <= 15
        if not mean_ok:
            all_mean_ok = False
        if not std_ok:
            all_std_ok = False
        print(f"  {meter_name:<15} {s['mean']:>7.1f} {s['stdev']:>7.1f} {'PASS' if mean_ok else 'FAIL':>10} {'PASS' if std_ok else 'FAIL':>10}")

    # =========================================================================
    # CROSS-METER CORRELATION ANALYSIS
    # =========================================================================
    print(f"\n{'='*80}")
    print("2. CROSS-METER CORRELATION ANALYSIS")
    print(f"{'='*80}")
    print("(Want: low correlations = meters measure different things)")

    # Print header (truncated meter names)
    print(f"\n  {'':>12}", end="")
    for meter in METER_NAMES:
        print(f" {meter[:6]:>7}", end="")
    print()
    print(f"  {'-'*135}")

    # Correlation matrix
    correlations = []
    for meter1 in METER_NAMES:
        print(f"  {meter1:<12}", end="")
        for meter2 in METER_NAMES:
            if meter1 == meter2:
                corr = 1.0
            else:
                corr = pearson_correlation(meter_scores[meter1], meter_scores[meter2])
            correlations.append((meter1, meter2, corr))
            # Color-code: high correlation in "brackets"
            if meter1 != meter2 and abs(corr) >= 0.5:
                print(f" [{corr:>5.2f}]", end="")
            else:
                print(f"  {corr:>5.2f} ", end="")
        print()

    # Calculate average off-diagonal correlation
    off_diag = [abs(c) for m1, m2, c in correlations if m1 != m2]
    avg_corr = sum(off_diag) / len(off_diag) if off_diag else 0

    # Find high correlations
    high_corr_pairs = [(m1, m2, c) for m1, m2, c in correlations if m1 < m2 and abs(c) >= 0.5]
    high_corr_pairs.sort(key=lambda x: -abs(x[2]))

    print(f"\n  Average |correlation| (off-diagonal): {avg_corr:.3f}")
    corr_ok = avg_corr < 0.30
    print(f"  Target: <0.30")
    print(f"  Status: {'PASS' if corr_ok else 'FAIL'}")

    if high_corr_pairs:
        print(f"\n  High Correlation Pairs (|r| >= 0.50):")
        for m1, m2, c in high_corr_pairs[:10]:
            group1 = METER_TO_GROUP_V2.get(Meter(m1), "?").value
            group2 = METER_TO_GROUP_V2.get(Meter(m2), "?").value
            same_group = "(same group)" if group1 == group2 else ""
            print(f"    {m1:15} <-> {m2:15}: {c:>6.3f}  [{group1}/{group2}] {same_group}")

    # =========================================================================
    # WITHIN-GROUP VS BETWEEN-GROUP CORRELATION
    # =========================================================================
    print(f"\n{'='*80}")
    print("3. WITHIN-GROUP VS BETWEEN-GROUP CORRELATION")
    print(f"{'='*80}")

    within_group_corrs = []
    between_group_corrs = []

    for m1, m2, c in correlations:
        if m1 >= m2:
            continue
        group1 = METER_TO_GROUP_V2.get(Meter(m1))
        group2 = METER_TO_GROUP_V2.get(Meter(m2))
        if group1 == group2:
            within_group_corrs.append(abs(c))
        else:
            between_group_corrs.append(abs(c))

    avg_within = sum(within_group_corrs) / len(within_group_corrs) if within_group_corrs else 0
    avg_between = sum(between_group_corrs) / len(between_group_corrs) if between_group_corrs else 0

    print(f"\n  Within-group average |correlation|:  {avg_within:.3f} (n={len(within_group_corrs)} pairs)")
    print(f"  Between-group average |correlation|: {avg_between:.3f} (n={len(between_group_corrs)} pairs)")
    print(f"\n  Interpretation:")
    if avg_within > avg_between + 0.05:
        print(f"    Meters within same group are more correlated (expected)")
    elif avg_within < avg_between:
        print(f"    Meters within same group are LESS correlated than between groups (unexpected)")
    else:
        print(f"    No significant difference between within/between group correlations")

    # =========================================================================
    # GROUP-LEVEL ANALYSIS
    # =========================================================================
    print(f"\n{'='*80}")
    print("4. GROUP-LEVEL ANALYSIS")
    print(f"{'='*80}")

    groups = [MeterGroupV2.MIND, MeterGroupV2.HEART, MeterGroupV2.BODY,
              MeterGroupV2.INSTINCTS, MeterGroupV2.GROWTH]

    group_correlations = {}
    for group in groups:
        group_meters = [m.value for m in Meter if METER_TO_GROUP_V2.get(m) == group]
        group_corrs = []
        for m1 in group_meters:
            for m2 in group_meters:
                if m1 < m2:
                    corr = pearson_correlation(meter_scores[m1], meter_scores[m2])
                    group_corrs.append((m1, m2, corr))
        group_correlations[group.value] = group_corrs

    print(f"\n  Per-Group Correlation Summary:")
    print(f"  {'Group':<12} {'Avg |r|':>10} {'Max |r|':>10} {'Meter Pairs'}")
    print(f"  {'-'*60}")

    for group in groups:
        corrs = group_correlations[group.value]
        if corrs:
            avg_r = sum(abs(c) for _, _, c in corrs) / len(corrs)
            max_pair = max(corrs, key=lambda x: abs(x[2]))
            max_r = abs(max_pair[2])
            print(f"  {group.value:<12} {avg_r:>10.3f} {max_r:>10.3f}   {max_pair[0]} <-> {max_pair[1]}")
        else:
            print(f"  {group.value:<12} {'N/A':>10} {'N/A':>10}")

    # =========================================================================
    # 5% INCREMENT DISTRIBUTIONS (SAMPLE)
    # =========================================================================
    print(f"\n{'='*80}")
    print("5. 5% INCREMENT DISTRIBUTIONS (showing 3 sample meters)")
    print(f"{'='*80}")

    sample_meters = ['clarity', 'energy', 'momentum']
    for meter_name in sample_meters:
        meter_5pct = analyze_5pct_distribution(
            meter_scores[meter_name],
            0, 100,  # unified_score range is 0-100
            meter_name
        )
        print_5pct_distribution(meter_5pct)

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print(f"\n{'='*80}")
    print("6. FINAL SUMMARY")
    print(f"{'='*80}")

    print(f"""
+--------------------------------+------------+------------+--------+
| Metric                         | Value      | Target     | Status |
+--------------------------------+------------+------------+--------+
| Avg Cross-Meter |Correlation|  | {avg_corr:>10.3f} | <0.30      | {'PASS' if corr_ok else 'FAIL':>6} |
| High Correlation Pairs (>=0.5) | {len(high_corr_pairs):>10} | 0          | {'PASS' if len(high_corr_pairs) == 0 else 'WARN':>6} |
| Within-Group Avg |r|           | {avg_within:>10.3f} | -          | INFO   |
| Between-Group Avg |r|          | {avg_between:>10.3f} | -          | INFO   |
| All Means in [45,55]           | {'Yes' if all_mean_ok else 'No':>10} | Yes        | {'PASS' if all_mean_ok else 'FAIL':>6} |
| All StdDevs in [5,15]          | {'Yes' if all_std_ok else 'No':>10} | Yes        | {'PASS' if all_std_ok else 'FAIL':>6} |
+--------------------------------+------------+------------+--------+
""")

    all_pass = corr_ok and all_mean_ok and all_std_ok
    print(f"  OVERALL: {'PASS' if all_pass else 'NEEDS ATTENTION'}")

    if high_corr_pairs:
        print(f"\n  ACTION ITEMS:")
        print(f"  - Review {len(high_corr_pairs)} meter pairs with high correlation (>=0.5)")
        print(f"  - Consider adjusting aspect filters to differentiate these meters")

    return {
        "meter_stats": meter_stats,
        "avg_correlation": avg_corr,
        "correlation_ok": corr_ok,
        "high_corr_pairs": high_corr_pairs,
        "within_group_avg": avg_within,
        "between_group_avg": avg_between,
        "all_pass": all_pass,
        "total_samples": total_samples,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Astrometer Distribution Analysis")
    parser.add_argument("-n", "--charts", type=int, default=1000, help="Number of charts to generate")
    parser.add_argument("-m", "--dates", type=int, default=10, help="Transit dates per chart")
    parser.add_argument("-s", "--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    results = run_comprehensive_analysis(
        n_charts=args.charts,
        m_dates=args.dates,
        seed=args.seed,
    )

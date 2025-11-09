"""
Proper analysis of day-to-day meter variation across diverse birth charts.

Tests N random birth charts across multiple consecutive days to get
statistically meaningful data on meter variation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import List, Dict
import json
import random

from astro import compute_birth_chart
from astrometers.meters import get_meters


def generate_random_birth_data():
    """Generate random but realistic birth data."""
    # Random date between 1950-2010
    year = random.randint(1950, 2010)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Safe for all months

    # Random time
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    # Random location (major cities worldwide)
    locations = [
        (40.7128, -74.0060, "America/New_York"),      # NYC
        (34.0522, -118.2437, "America/Los_Angeles"),  # LA
        (51.5074, -0.1278, "Europe/London"),          # London
        (48.8566, 2.3522, "Europe/Paris"),            # Paris
        (35.6762, 139.6503, "Asia/Tokyo"),            # Tokyo
        (55.7558, 37.6173, "Europe/Moscow"),          # Moscow
        (-33.8688, 151.2093, "Australia/Sydney"),     # Sydney
        (19.4326, -99.1332, "America/Mexico_City"),   # Mexico City
        (28.6139, 77.2090, "Asia/Kolkata"),           # Delhi
        (-23.5505, -46.6333, "America/Sao_Paulo"),    # Sao Paulo
    ]

    lat, lon, tz = random.choice(locations)

    return {
        "birth_date": f"{year}-{month:02d}-{day:02d}",
        "birth_time": f"{hour:02d}:{minute:02d}",
        "birth_timezone": tz,
        "birth_lat": lat,
        "birth_lon": lon
    }


def analyze_chart_variation(birth_data: dict, num_days: int = 7) -> Dict:
    """
    Calculate meter variation for one chart over N days.

    Returns dict with variation stats.
    """
    # Get natal chart
    natal_chart, is_exact = compute_birth_chart(
        birth_date=birth_data["birth_date"],
        birth_time=birth_data["birth_time"],
        birth_timezone=birth_data["birth_timezone"],
        birth_lat=birth_data["birth_lat"],
        birth_lon=birth_data["birth_lon"]
    )

    # Generate meters for consecutive days (use current date)
    start_date = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

    daily_meters = []
    for i in range(num_days):
        date = start_date + timedelta(days=i)

        # Get transit chart
        transit_chart, _ = compute_birth_chart(
            birth_date=date.strftime("%Y-%m-%d"),
            birth_time="12:00",
            birth_timezone="UTC"
        )

        # Calculate meters
        meters = get_meters(
            natal_chart=natal_chart,
            transit_chart=transit_chart,
            date=date.date(),
            calculate_trends=False  # Don't need trends, saves time
        )

        daily_meters.append(meters)

    # Calculate day-to-day deltas for all 17 meters
    meter_names = [
        "mental_clarity", "focus", "communication",
        "love", "inner_stability", "sensitivity",
        "vitality", "drive", "wellness",
        "purpose", "connection", "intuition", "creativity",
        "opportunities", "career", "growth", "social_life"
    ]

    chart_stats = {}

    for meter_name in meter_names:
        unified_scores = [getattr(m, meter_name).unified_score for m in daily_meters]

        # Calculate day-to-day deltas
        deltas = [abs(unified_scores[i] - unified_scores[i-1]) for i in range(1, len(unified_scores))]

        if deltas:
            chart_stats[meter_name] = {
                "avg_delta": sum(deltas) / len(deltas),
                "max_delta": max(deltas),
                "range": max(unified_scores) - min(unified_scores),
                "days_stable": sum(1 for d in deltas if d < 5),
                "days_slow": sum(1 for d in deltas if 5 <= d < 10),
                "days_moderate": sum(1 for d in deltas if 10 <= d < 20),
                "days_rapid": sum(1 for d in deltas if d >= 20),
            }

    return chart_stats


def main():
    """Run comprehensive variation analysis."""
    num_charts = 2000  # Test 200 random charts
    num_days = 7      # 7 consecutive days each

    print(f"\n{'='*100}")
    print(f"COMPREHENSIVE METER VARIATION ANALYSIS")
    print(f"{'='*100}")
    print(f"\nTesting {num_charts} random birth charts × {num_days} days = {num_charts * num_days} chart-days")
    print(f"Locations: NYC, LA, London, Paris, Tokyo, Moscow, Sydney, Mexico City, Delhi, Sao Paulo")
    print(f"Birth years: 1950-2010")
    print(f"\nThis will take ~5-10 minutes...\n")

    # Collect stats from all charts
    all_charts_stats = []

    for i in range(num_charts):
        birth_data = generate_random_birth_data()

        try:
            chart_stats = analyze_chart_variation(birth_data, num_days)
            all_charts_stats.append(chart_stats)

            if (i + 1) % 20 == 0:
                print(f"Processed {i+1}/{num_charts} charts...")
        except Exception as e:
            print(f"Error processing chart {i+1}: {e}")
            continue

    print(f"\n{'='*100}")
    print(f"AGGREGATED RESULTS (across {len(all_charts_stats)} charts)")
    print(f"{'='*100}\n")

    # Aggregate stats across all charts
    meter_names = [
        "mental_clarity", "focus", "communication",
        "love", "inner_stability", "sensitivity",
        "vitality", "drive", "wellness",
        "purpose", "connection", "intuition", "creativity",
        "opportunities", "career", "growth", "social_life"
    ]

    aggregated = {}

    for meter_name in meter_names:
        avg_deltas = [chart[meter_name]["avg_delta"] for chart in all_charts_stats]
        max_deltas = [chart[meter_name]["max_delta"] for chart in all_charts_stats]
        ranges = [chart[meter_name]["range"] for chart in all_charts_stats]

        total_transitions = sum(
            chart[meter_name]["days_stable"] +
            chart[meter_name]["days_slow"] +
            chart[meter_name]["days_moderate"] +
            chart[meter_name]["days_rapid"]
            for chart in all_charts_stats
        )

        days_stable = sum(chart[meter_name]["days_stable"] for chart in all_charts_stats)
        days_slow = sum(chart[meter_name]["days_slow"] for chart in all_charts_stats)
        days_moderate = sum(chart[meter_name]["days_moderate"] for chart in all_charts_stats)
        days_rapid = sum(chart[meter_name]["days_rapid"] for chart in all_charts_stats)

        aggregated[meter_name] = {
            "avg_delta_mean": sum(avg_deltas) / len(avg_deltas),
            "avg_delta_median": sorted(avg_deltas)[len(avg_deltas)//2],
            "max_delta_mean": sum(max_deltas) / len(max_deltas),
            "range_mean": sum(ranges) / len(ranges),
            "pct_stable": days_stable / total_transitions * 100,
            "pct_slow": days_slow / total_transitions * 100,
            "pct_moderate": days_moderate / total_transitions * 100,
            "pct_rapid": days_rapid / total_transitions * 100,
        }

    # Print summary table
    print(f"{'Meter':<20} {'Avg Δ':<10} {'Median Δ':<12} {'Max Δ':<10} {'Range':<10} {'%Stable':<10} {'%Slow':<8} {'%Mod':<8} {'%Rapid':<8}")
    print("-" * 100)

    for meter_name in meter_names:
        s = aggregated[meter_name]
        print(f"{meter_name:<20} "
              f"{s['avg_delta_mean']:>6.1f}    "
              f"{s['avg_delta_median']:>6.1f}      "
              f"{s['max_delta_mean']:>6.1f}    "
              f"{s['range_mean']:>6.1f}    "
              f"{s['pct_stable']:>6.1f}%   "
              f"{s['pct_slow']:>5.1f}%  "
              f"{s['pct_moderate']:>5.1f}%  "
              f"{s['pct_rapid']:>5.1f}%")

    # Overall statistics
    print("\n" + "=" * 100)
    print("OVERALL STATISTICS (averaged across all 17 meters)")
    print("=" * 100 + "\n")

    avg_avg_delta = sum(s["avg_delta_mean"] for s in aggregated.values()) / len(aggregated)
    avg_max_delta = sum(s["max_delta_mean"] for s in aggregated.values()) / len(aggregated)
    avg_range = sum(s["range_mean"] for s in aggregated.values()) / len(aggregated)

    overall_pct_stable = sum(s["pct_stable"] for s in aggregated.values()) / len(aggregated)
    overall_pct_slow = sum(s["pct_slow"] for s in aggregated.values()) / len(aggregated)
    overall_pct_moderate = sum(s["pct_moderate"] for s in aggregated.values()) / len(aggregated)
    overall_pct_rapid = sum(s["pct_rapid"] for s in aggregated.values()) / len(aggregated)

    print(f"Average daily change: {avg_avg_delta:.1f} points")
    print(f"Average max change (over {num_days} days): {avg_max_delta:.1f} points")
    print(f"Average range (over {num_days} days): {avg_range:.1f} points")
    print(f"\nTrend Distribution:")
    print(f"  Stable (Δ < 5):         {overall_pct_stable:.1f}%")
    print(f"  Slow (5 ≤ Δ < 10):      {overall_pct_slow:.1f}%")
    print(f"  Moderate (10 ≤ Δ < 20): {overall_pct_moderate:.1f}%")
    print(f"  Rapid (Δ ≥ 20):         {overall_pct_rapid:.1f}%")

    # Identify problem meters
    print("\n" + "=" * 100)
    print("PROBLEM METERS (Consistently Low Variation)")
    print("=" * 100 + "\n")

    threshold = avg_avg_delta * 0.7  # Less than 70% of average
    problem_meters = [(name, s) for name, s in aggregated.items() if s["avg_delta_mean"] < threshold]

    if problem_meters:
        print(f"Meters with avg daily change < {threshold:.1f} (70% of overall average):\n")
        for name, s in sorted(problem_meters, key=lambda x: x[1]["avg_delta_mean"]):
            print(f"  {name:<20} Avg Δ: {s['avg_delta_mean']:.1f}, Stable: {s['pct_stable']:.1f}%, Range: {s['range_mean']:.1f}")
    else:
        print("No problem meters found!")

    # Save results
    with open("meter_variation_comprehensive.json", "w") as f:
        json.dump(aggregated, f, indent=2)

    print("\n" + "=" * 100)
    print("Results saved to meter_variation_comprehensive.json")
    print("=" * 100)

    return aggregated


if __name__ == "__main__":
    results = main()

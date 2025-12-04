"""
Prototype: Compare order of operations

Option A: raw → sigmoid → +variation → soft_clamp
Option B: raw → +variation → sigmoid (no clamp needed)

Run with: uv run python functions/tests/integration/prototype_smooth_scores.py
"""

import math
import random
from collections import defaultdict
import statistics
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from compatibility import get_compatibility_from_birth_data
from datetime import datetime, timedelta


CATEGORY_CONFIG = {
    "attraction": {
        "planets": ["venus", "mars"],
        "steepness": 0.028,
        "max_var": 12,
    },
    "communication": {
        "planets": ["mercury"],
        "steepness": 0.030,
        "max_var": 8,
    },
    "emotional": {
        "planets": ["moon"],
        "steepness": 0.025,
        "max_var": 10,
    },
    "longTerm": {
        "planets": ["saturn"],
        "steepness": 0.022,
        "max_var": 15,
    },
    "growth": {
        "planets": ["jupiter", "north node"],
        "steepness": 0.030,
        "max_var": 8,
    },
    "values": {
        "planets": ["sun", "venus"],
        "steepness": 0.028,
        "max_var": 10,
    },
}


def sigmoid_compress(score: float, steepness: float = 0.025, max_output: float = 85) -> float:
    """Compress score using sigmoid - maps any input to (-max_output, +max_output)."""
    normalized = 2 / (1 + math.exp(-steepness * score)) - 1
    return normalized * max_output


def get_planet_degrees(chart: dict, planet_names: list[str]) -> list[float]:
    degrees = []
    planets = chart.get("planets", [])
    for p in planets:
        name = p.get("name", "").lower()
        if name in [pn.lower() for pn in planet_names]:
            degrees.append(p.get("absolute_degree", 0))
    return degrees if degrees else [0]


def chart_variation_for_category(user_chart: dict, conn_chart: dict, category: str, config: dict) -> float:
    planet_names = config["planets"]
    max_var = config["max_var"]

    user_degrees = get_planet_degrees(user_chart, planet_names)
    conn_degrees = get_planet_degrees(conn_chart, planet_names)

    user_frac = sum(d % 30 for d in user_degrees) / 30
    conn_frac = sum(d % 30 for d in conn_degrees) / 30

    seed = hash(category) % 1000 / 1000
    combined = (user_frac + conn_frac + seed) % 2

    return (combined - 1) * max_var


def smooth_option_a(raw_score: float, user_chart: dict, conn_chart: dict, category: str) -> float:
    """Option A: sigmoid first, then variation, then soft clamp."""
    config = CATEGORY_CONFIG.get(category, {"planets": ["sun"], "steepness": 0.025, "max_var": 10})

    base = sigmoid_compress(raw_score, steepness=config["steepness"])
    var = chart_variation_for_category(user_chart, conn_chart, category, config)
    return max(-85, min(85, base + var))


def smooth_option_b(raw_score: float, user_chart: dict, conn_chart: dict, category: str) -> float:
    """Option B: variation first, then sigmoid (no clamp needed)."""
    config = CATEGORY_CONFIG.get(category, {"planets": ["sun"], "steepness": 0.025, "max_var": 10})

    var = chart_variation_for_category(user_chart, conn_chart, category, config)
    adjusted = raw_score + var
    return sigmoid_compress(adjusted, steepness=config["steepness"])


# =============================================================================
# Data Generation
# =============================================================================

CITIES = [
    ("New York", 40.7128, -74.0060, "America/New_York"),
    ("Los Angeles", 34.0522, -118.2437, "America/Los_Angeles"),
    ("Chicago", 41.8781, -87.6298, "America/Chicago"),
    ("London", 51.5074, -0.1278, "Europe/London"),
    ("Tokyo", 35.6762, 139.6503, "Asia/Tokyo"),
    ("Sydney", -33.8688, 151.2093, "Australia/Sydney"),
]


def generate_random_birth_data():
    start_date = datetime(1980, 1, 1)
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


def compute_all_variants(n_pairs: int = 500, seed: int = 42):
    random.seed(seed)
    print(f"Generating {n_pairs} pairs...")

    before = defaultdict(list)
    option_a = defaultdict(list)
    option_b = defaultdict(list)

    for i in range(n_pairs):
        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{n_pairs}")

        user = generate_random_birth_data()
        conn = generate_random_birth_data()

        try:
            result = get_compatibility_from_birth_data(
                user_birth_date=user["birth_date"],
                user_birth_time=user["birth_time"],
                user_birth_lat=user["birth_lat"],
                user_birth_lon=user["birth_lon"],
                user_birth_timezone=user["birth_timezone"],
                connection_birth_date=conn["birth_date"],
                connection_birth_time=conn["birth_time"],
                connection_birth_lat=conn["birth_lat"],
                connection_birth_lon=conn["birth_lon"],
                connection_birth_timezone=conn["birth_timezone"],
                relationship_type="romantic",
                user_name="User",
                connection_name="Conn",
            )

            from astro import compute_birth_chart
            user_chart, _ = compute_birth_chart(
                user["birth_date"], user["birth_time"],
                user["birth_timezone"], user["birth_lat"], user["birth_lon"]
            )
            conn_chart, _ = compute_birth_chart(
                conn["birth_date"], conn["birth_time"],
                conn["birth_timezone"], conn["birth_lat"], conn["birth_lon"]
            )

            for cat in result.mode.categories:
                raw = cat.score
                before[cat.id].append(raw)
                option_a[cat.id].append(smooth_option_a(raw, user_chart, conn_chart, cat.id))
                option_b[cat.id].append(smooth_option_b(raw, user_chart, conn_chart, cat.id))

        except Exception:
            pass

    return before, option_a, option_b


def stats(scores: list[float]) -> tuple[float, float, float]:
    mean = statistics.mean(scores)
    std = statistics.stdev(scores)
    ext = sum(1 for s in scores if abs(s) >= 70) / len(scores) * 100
    return mean, std, ext


def bucket_analysis(scores: list[float]) -> tuple[float, float]:
    """Return (max_bucket_pct, spike_at_extremes)."""
    buckets = [0] * 20
    for s in scores:
        bucket = int((s + 85) / 170 * 20)
        bucket = min(19, max(0, bucket))
        buckets[bucket] += 1

    pcts = [b / len(scores) * 100 for b in buckets]
    max_pct = max(pcts)
    extreme_spike = pcts[0] + pcts[19]  # Bottom + top bucket
    return max_pct, extreme_spike


def main():
    before, option_a, option_b = compute_all_variants(n_pairs=1000, seed=42)

    print("\n" + "="*100)
    print("COMPARISON: BEFORE vs OPTION A (sigmoid→var) vs OPTION B (var→sigmoid)")
    print("="*100)

    print(f"\n  {'Category':<12} | {'BEFORE':^24} | {'OPTION A':^24} | {'OPTION B':^24}")
    print(f"  {'':12} | {'Mean':>7} {'Std':>6} {'Ext%':>6} | {'Mean':>7} {'Std':>6} {'Ext%':>6} | {'Mean':>7} {'Std':>6} {'Ext%':>6}")
    print(f"  {'-'*95}")

    for cat in sorted(before.keys()):
        b_m, b_s, b_e = stats(before[cat])
        a_m, a_s, a_e = stats(option_a[cat])
        bb_m, bb_s, bb_e = stats(option_b[cat])

        print(f"  {cat:<12} | {b_m:>7.1f} {b_s:>6.1f} {b_e:>5.1f}% | {a_m:>7.1f} {a_s:>6.1f} {a_e:>5.1f}% | {bb_m:>7.1f} {bb_s:>6.1f} {bb_e:>5.1f}%")

    print("\n" + "="*100)
    print("BUCKET ANALYSIS (lower is better)")
    print("="*100)

    print(f"\n  {'Category':<12} | {'BEFORE':^18} | {'OPTION A':^18} | {'OPTION B':^18}")
    print(f"  {'':12} | {'Max%':>8} {'Extr':>8} | {'Max%':>8} {'Extr':>8} | {'Max%':>8} {'Extr':>8}")
    print(f"  {'-'*75}")

    for cat in sorted(before.keys()):
        b_max, b_ext = bucket_analysis(before[cat])
        a_max, a_ext = bucket_analysis(option_a[cat])
        bb_max, bb_ext = bucket_analysis(option_b[cat])

        print(f"  {cat:<12} | {b_max:>7.1f}% {b_ext:>7.1f}% | {a_max:>7.1f}% {a_ext:>7.1f}% | {bb_max:>7.1f}% {bb_ext:>7.1f}%")

    # Summary
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print("\n  Option A: raw → sigmoid → +variation → soft_clamp")
    print("  Option B: raw → +variation → sigmoid (no clamp)")
    print("\n  Key differences:")
    print("  - Option A: variation shifts the sigmoid output (can hit clamp)")
    print("  - Option B: variation shifts the input to sigmoid (naturally bounded)")


if __name__ == "__main__":
    main()

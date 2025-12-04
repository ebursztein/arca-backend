"""
Planet Velocity Analysis

Measures actual daily movement speed of each planet from chart data.
Used to understand which planets drive daily vs long-term meter changes.

Usage:
    uv run python functions/tests/integration/test_planet_velocities.py
"""

import random
from datetime import datetime, timedelta
import statistics
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from astro import compute_birth_chart


PLANETS = [
    'moon', 'sun', 'mercury', 'venus', 'mars',
    'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'north_node'
]


def run_velocity_analysis(n_samples: int = 500, seed: int = 42) -> dict:
    """
    Sample planet speeds across random dates.

    Args:
        n_samples: Number of random dates to sample
        seed: Random seed for reproducibility

    Returns:
        Dict with velocity stats per planet
    """
    random.seed(seed)

    planet_speeds = {p: [] for p in PLANETS}

    print(f"\n{'='*70}")
    print("PLANET VELOCITY ANALYSIS")
    print(f"{'='*70}")
    print(f"Sampling {n_samples} random dates (2020-2025)...")

    for i in range(n_samples):
        date = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 365 * 5))

        try:
            chart, _ = compute_birth_chart(date.strftime('%Y-%m-%d'), '12:00')

            for p in chart['planets']:
                name = p['name'].lower()
                if name in planet_speeds:
                    planet_speeds[name].append(abs(p['speed']))
        except Exception as e:
            pass

        if (i + 1) % 100 == 0:
            print(f"  Progress: {i+1}/{n_samples}")

    # Calculate statistics
    results = {}

    print(f"\n{'='*70}")
    print("PLANET DAILY VELOCITY (degrees/day)")
    print(f"{'='*70}")
    print(f"{'Planet':<12} {'Mean':>8} {'Median':>8} {'Min':>8} {'Max':>8} {'Days/8deg':>10}")
    print("-" * 70)

    for planet in PLANETS:
        speeds = planet_speeds[planet]
        if speeds:
            mean = statistics.mean(speeds)
            median = statistics.median(speeds)
            min_s = min(speeds)
            max_s = max(speeds)
            days_for_8deg = 8.0 / mean if mean > 0 else float('inf')

            results[planet] = {
                'mean': mean,
                'median': median,
                'min': min_s,
                'max': max_s,
                'days_per_8deg': days_for_8deg,
            }

            print(f"{planet:<12} {mean:>8.3f} {median:>8.3f} {min_s:>8.3f} {max_s:>8.3f} {days_for_8deg:>10.1f}")

    # Show current weights vs speed
    print(f"\n{'='*70}")
    print("CURRENT TRANSIT WEIGHTS vs ACTUAL SPEED")
    print(f"{'='*70}")

    current_weights = {
        'moon': 0.8,
        'sun': 1.0,
        'mercury': 1.0,
        'venus': 1.0,
        'mars': 1.0,
        'jupiter': 1.2,
        'saturn': 1.2,
        'uranus': 1.5,
        'neptune': 1.5,
        'pluto': 1.5,
        'north_node': 1.5,
    }

    print(f"{'Planet':<12} {'Speed':>10} {'Days/8deg':>12} {'Weight':>10} {'Issue'}")
    print("-" * 70)

    for planet in PLANETS:
        if planet in results:
            speed = results[planet]['mean']
            days = results[planet]['days_per_8deg']
            weight = current_weights.get(planet, 1.0)

            # Flag issues
            issue = ""
            if days < 10 and weight < 1.0:
                issue = "FAST but low weight"
            elif days > 100 and weight > 1.0:
                issue = "SLOW but high weight"

            print(f"{planet:<12} {speed:>10.3f} {days:>12.1f} {weight:>10.1f} {issue}")

    # Recommendations
    print(f"\n{'='*70}")
    print("ANALYSIS")
    print(f"{'='*70}")
    print("""
Speed Categories:
  - FAST (< 1 day/8deg):  Moon
  - MEDIUM (1-15 days):   Sun, Mercury, Venus, Mars
  - SLOW (15-150 days):   Jupiter, Saturn
  - GLACIAL (> 150 days): Uranus, Neptune, Pluto

Current Problem:
  - Moon is FASTEST (0.6 days/8deg) but has LOWEST weight (0.8)
  - Outer planets are SLOWEST (240-440 days/8deg) but have HIGHEST weight (1.5)
  - This makes meters dominated by slow-moving planets = too stable day-to-day

Suggested Weight Adjustment (to increase daily variation):
  - Moon: 0.8 -> 1.5 (emphasize fastest mover)
  - Outer planets: 1.5 -> 0.8 (de-emphasize glacial movers)
""")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Planet Velocity Analysis")
    parser.add_argument("-n", "--samples", type=int, default=500, help="Number of dates to sample")
    parser.add_argument("-s", "--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    results = run_velocity_analysis(n_samples=args.samples, seed=args.seed)

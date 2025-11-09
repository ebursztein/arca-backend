"""
Debug: Check what aspects are actually being found.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from astro import compute_birth_chart, find_natal_transit_aspects
from functions.astrometers.meters_v1 import convert_to_transit_aspects


def test_debug_all_aspects():
    """See what aspects are actually being found."""

    # Same test data
    natal_chart, _ = compute_birth_chart(
        birth_date="1990-06-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )

    transit_chart, _ = compute_birth_chart(birth_date="2025-10-26")

    # Find all natal-transit aspects
    natal_transit_aspects = find_natal_transit_aspects(
        natal_chart,
        transit_chart,
        orb=8.0
    )

    print(f"\n{'='*80}")
    print(f"TOTAL ASPECTS FOUND: {len(natal_transit_aspects)}")
    print(f"{'='*80}\n")

    # Count by natal planet
    natal_planet_counts = {}
    for aspect in natal_transit_aspects:
        planet = aspect.natal_planet.value
        natal_planet_counts[planet] = natal_planet_counts.get(planet, 0) + 1

    print("Aspects per natal planet:")
    for planet, count in sorted(natal_planet_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {planet:15s}: {count} aspects")

    # Convert to TransitAspect format
    all_aspects = convert_to_transit_aspects(
        natal_chart,
        transit_chart,
        natal_transit_aspects
    )

    print(f"\nAfter conversion: {len(all_aspects)} TransitAspect objects")

    # Show all aspects
    print(f"\n{'='*80}")
    print("ALL ASPECTS:")
    print(f"{'='*80}\n")

    for aspect in all_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal: {aspect.natal_planet.value:10s} (house {aspect.natal_house})")
        print(f"    Transit: {aspect.transit_planet.value}")
        print(f"    Aspect: {aspect.aspect_type.value}")
        print()


if __name__ == "__main__":
    test_debug_all_aspects()

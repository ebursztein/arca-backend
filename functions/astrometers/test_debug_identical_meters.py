"""
Debug test to understand why challenge_intensity and karmic_lessons have identical aspect sets.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from astro import compute_birth_chart
from astrometers.meters import get_meters


def test_debug_challenge_vs_karmic():
    """Debug why these two meters have identical aspect sets."""

    # Same test data as validation tests
    natal_chart, _ = compute_birth_chart(
        birth_date="1990-06-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )

    transit_chart, _ = compute_birth_chart(birth_date="2025-10-26")
    date = datetime(2025, 10, 26, 12, 0)

    # Get all meters
    meters = get_meters(natal_chart, transit_chart, date)

    print("\n" + "="*80)
    print("CHALLENGE INTENSITY ASPECTS")
    print("="*80)
    print(f"Total aspects: {len(meters.challenge_intensity.top_aspects)}")
    for aspect in meters.challenge_intensity.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal planet: {aspect.natal_planet.value}")
        print(f"    Transit planet: {aspect.transit_planet.value}")
        print(f"    Aspect type: {aspect.aspect_type.value}")
        print(f"    DTI: {aspect.dti_contribution:.1f}")
        print()

    print("\n" + "="*80)
    print("KARMIC LESSONS ASPECTS")
    print("="*80)
    print(f"Total aspects: {len(meters.karmic_lessons.top_aspects)}")
    for aspect in meters.karmic_lessons.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal planet: {aspect.natal_planet.value}")
        print(f"    Transit planet: {aspect.transit_planet.value}")
        print(f"    Aspect type: {aspect.aspect_type.value}")
        print(f"    DTI: {aspect.dti_contribution:.1f}")
        print()

    # Create sets for comparison
    challenge_set = set(
        (a.natal_planet, a.transit_planet, a.aspect_type)
        for a in meters.challenge_intensity.top_aspects
    )
    karmic_set = set(
        (a.natal_planet, a.transit_planet, a.aspect_type)
        for a in meters.karmic_lessons.top_aspects
    )

    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    print(f"Challenge intensity planets: Saturn, Uranus, Neptune, Pluto")
    print(f"Karmic lessons planets: Saturn, North Node")
    print()
    print(f"Challenge set size: {len(challenge_set)}")
    print(f"Karmic set size: {len(karmic_set)}")
    print(f"Are they equal? {challenge_set == karmic_set}")

    if challenge_set == karmic_set:
        print("\n❌ BUG CONFIRMED: These meters have identical aspect sets!")
        print("\nThis means:")
        print("  1. Either the filtering logic is broken")
        print("  2. Or in this specific chart there are no Uranus/Neptune/Pluto/North Node aspects")
        print("     and both meters only see Saturn aspects")


if __name__ == "__main__":
    test_debug_challenge_vs_karmic()

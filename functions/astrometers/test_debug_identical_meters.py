"""
Debug test to understand why focus and communication might have identical aspect sets.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from astro import compute_birth_chart
from astrometers.meters import get_meters


def test_debug_focus_vs_communication():
    """Debug why these two meters might have identical aspect sets."""

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
    print("FOCUS ASPECTS")
    print("="*80)
    print(f"Total aspects: {len(meters.focus.top_aspects)}")
    for aspect in meters.focus.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal planet: {aspect.natal_planet.value}")
        print(f"    Transit planet: {aspect.transit_planet.value}")
        print(f"    Aspect type: {aspect.aspect_type.value}")
        print(f"    DTI: {aspect.dti_contribution:.1f}")
        print()

    print("\n" + "="*80)
    print("COMMUNICATION ASPECTS")
    print("="*80)
    print(f"Total aspects: {len(meters.communication.top_aspects)}")
    for aspect in meters.communication.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal planet: {aspect.natal_planet.value}")
        print(f"    Transit planet: {aspect.transit_planet.value}")
        print(f"    Aspect type: {aspect.aspect_type.value}")
        print(f"    DTI: {aspect.dti_contribution:.1f}")
        print()

    # Create sets for comparison
    focus_set = set(
        (a.natal_planet, a.transit_planet, a.aspect_type)
        for a in meters.focus.top_aspects
    )
    comm_set = set(
        (a.natal_planet, a.transit_planet, a.aspect_type)
        for a in meters.communication.top_aspects
    )

    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    print(f"Focus set size: {len(focus_set)}")
    print(f"Communication set size: {len(comm_set)}")
    print(f"Are they equal? {focus_set == comm_set}")

    if focus_set == comm_set:
        print("\nℹ️  INFO: These meters have identical aspect sets.")
        print("   This is expected if they share the same configuration (e.g. Mercury/3rd House).")
    else:
        print("\n✅ These meters have different aspect sets.")


if __name__ == "__main__":
    test_debug_focus_vs_communication()

"""
Analyze the complete meter taxonomy by running meters with real data.

This script:
1. Generates a test natal and transit chart
2. Calls get_meters() to calculate all 23 meters
3. Inspects each meter's actual aspects to see what it filters
4. Displays in a table to identify overlaps

This reads the ACTUAL runtime behavior - no source parsing needed.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from tabulate import tabulate
from astro import compute_birth_chart
from astrometers.meters import get_meters


def analyze_meter_taxonomy():
    """Analyze all meters by running them with real data."""

    # Generate test charts
    print("Generating test charts...")
    natal_chart, _ = compute_birth_chart(
        birth_date="1990-06-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )

    transit_chart, _ = compute_birth_chart(birth_date="2025-10-26")
    date = datetime(2025, 10, 26, 12, 0)

    # Calculate all meters
    print("Calculating all meters...")
    meters = get_meters(natal_chart, transit_chart, date)

    # Get all meter readings
    all_readings = [
        meters.overall_intensity,
        meters.overall_harmony,
        meters.fire_energy,
        meters.earth_energy,
        meters.air_energy,
        meters.water_energy,
        meters.mental_clarity,
        meters.decision_quality,
        meters.communication_flow,
        meters.emotional_intensity,
        meters.relationship_harmony,
        meters.emotional_resilience,
        meters.physical_energy,
        meters.conflict_risk,
        meters.motivation_drive,
        meters.career_ambition,
        meters.opportunity_window,
        meters.challenge_intensity,
        meters.transformation_pressure,
        meters.intuition_spirituality,
        meters.innovation_breakthrough,
        meters.karmic_lessons,
        meters.social_collective,
    ]

    print(f"\n{'='*180}")
    print(f"ASTROMETERS TAXONOMY - ACTUAL RUNTIME BEHAVIOR")
    print(f"{'='*180}\n")

    # Build table
    table_data = []

    for reading in all_readings:
        # Extract unique natal planets
        natal_planets = sorted(set(a.natal_planet.value for a in reading.top_aspects))

        # Extract unique transit planets
        transit_planets = sorted(set(a.transit_planet.value for a in reading.top_aspects))

        # Extract unique aspect types
        aspect_types = sorted(set(a.aspect_type.value for a in reading.top_aspects))

        # Check if only hard aspects (square, opposition)
        aspect_filter = "All"
        if aspect_types and all(at in ['square', 'opposition'] for at in aspect_types):
            aspect_filter = "Hard only"
        elif aspect_types and all(at in ['trine', 'sextile'] for at in aspect_types):
            aspect_filter = "Soft only"

        table_data.append([
            reading.meter_name,
            reading.group.value,
            ', '.join(natal_planets) if natal_planets else '-',
            ', '.join(transit_planets) if transit_planets else '-',
            aspect_filter,
            len(reading.top_aspects),
            f"{reading.intensity:.1f}",
            f"{reading.harmony:.1f}"
        ])

    headers = ["Meter", "Group", "Natal Planets", "Transit Planets", "Aspect Filter", "# Aspects", "Intensity", "Harmony"]
    print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[None, 12, 25, 25, 20, 12, None, None, None]))

    # Overlap analysis
    print(f"\n{'='*180}")
    print("OVERLAP ANALYSIS - Pairwise Comparison")
    print(f"{'='*180}\n")

    # Build aspect sets for comparison
    aspect_sets = {}
    for reading in all_readings:
        aspect_set = set(
            (a.natal_planet, a.transit_planet, a.aspect_type)
            for a in reading.top_aspects
        )
        aspect_sets[reading.meter_name] = aspect_set

    # Find identical pairs
    identical_pairs = []
    high_overlap_pairs = []

    for i, reading1 in enumerate(all_readings):
        for reading2 in all_readings[i+1:]:
            set1 = aspect_sets[reading1.meter_name]
            set2 = aspect_sets[reading2.meter_name]

            # Skip if either is empty
            if not set1 or not set2:
                continue

            overlap = set1 & set2
            overlap_pct = len(overlap) / max(len(set1), len(set2)) * 100

            if set1 == set2:
                identical_pairs.append((reading1.meter_name, reading2.meter_name, len(set1)))
            elif overlap_pct >= 80:
                high_overlap_pairs.append((reading1.meter_name, reading2.meter_name, overlap_pct, len(overlap)))

    # Show identical pairs
    if identical_pairs:
        print("❌ IDENTICAL ASPECT SETS:\n")
        for meter1, meter2, count in identical_pairs:
            print(f"  {meter1:30s} == {meter2:30s} ({count} aspects)")
        print()
    else:
        print("✅ No meters have identical aspect sets\n")

    # Show high overlap
    if high_overlap_pairs:
        print("⚠️  HIGH OVERLAP (≥80%):\n")
        overlap_table = []
        for meter1, meter2, pct, count in sorted(high_overlap_pairs, key=lambda x: x[2], reverse=True):
            overlap_table.append([meter1, meter2, f"{pct:.0f}%", count])
        print(tabulate(overlap_table, headers=["Meter 1", "Meter 2", "Overlap %", "# Shared"], tablefmt="grid"))
        print()

    # Summary statistics
    print(f"{'='*180}")
    print("SUMMARY STATISTICS")
    print(f"{'='*180}\n")

    print(f"Total meters: {len(all_readings)}")
    print(f"Identical pairs: {len(identical_pairs)}")
    print(f"High overlap pairs (≥80%): {len(high_overlap_pairs)}")

    # Group distribution
    groups = {}
    for reading in all_readings:
        groups[reading.group.value] = groups.get(reading.group.value, 0) + 1

    print(f"\nMeters by group:")
    for group, count in sorted(groups.items()):
        print(f"  {group:15s}: {count} meters")

    # Aspect count distribution
    aspect_counts = [len(r.top_aspects) for r in all_readings]
    print(f"\nAspect count distribution:")
    print(f"  Min: {min(aspect_counts)}")
    print(f"  Max: {max(aspect_counts)}")
    print(f"  Mean: {sum(aspect_counts)/len(aspect_counts):.1f}")

    # Empty meters
    empty_meters = [r.meter_name for r in all_readings if len(r.top_aspects) == 0]
    if empty_meters:
        print(f"\n⚠️  Meters with NO aspects: {', '.join(empty_meters)}")


if __name__ == "__main__":
    analyze_meter_taxonomy()

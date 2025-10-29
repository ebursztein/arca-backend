"""
Verify if meters with "identical" top aspects actually processed different aspect sets.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from astro import compute_birth_chart
from astrometers.meters import get_meters


def test_verify_identical():
    """Check if supposedly identical meters have same raw scores."""

    natal_chart, _ = compute_birth_chart(
        birth_date="1990-06-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )

    transit_chart, _ = compute_birth_chart(birth_date="2025-10-26")
    date = datetime(2025, 10, 26, 12, 0)

    meters = get_meters(natal_chart, transit_chart, date)

    print(f"\n{'='*80}")
    print("SUPPOSEDLY IDENTICAL METERS - RAW SCORES")
    print(f"{'='*80}\n")

    # Check overall_intensity vs overall_harmony vs emotional_resilience
    print("Group 1: overall_intensity / overall_harmony / emotional_resilience")
    print(f"  overall_intensity:")
    print(f"    Raw DTI: {meters.overall_intensity.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.overall_intensity.raw_scores['hqs']:.2f}")
    print(f"    Top aspects natal planets: {set(a.natal_planet.value for a in meters.overall_intensity.top_aspects)}")

    print(f"\n  overall_harmony:")
    print(f"    Raw DTI: {meters.overall_harmony.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.overall_harmony.raw_scores['hqs']:.2f}")
    print(f"    Top aspects natal planets: {set(a.natal_planet.value for a in meters.overall_harmony.top_aspects)}")

    print(f"\n  emotional_resilience:")
    print(f"    Raw DTI: {meters.emotional_resilience.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.emotional_resilience.raw_scores['hqs']:.2f}")
    print(f"    Top aspects natal planets: {set(a.natal_planet.value for a in meters.emotional_resilience.top_aspects)}")

    # Check challenge_intensity vs karmic_lessons
    print(f"\n{'='*80}")
    print("Group 2: challenge_intensity / karmic_lessons")
    print(f"  challenge_intensity:")
    print(f"    Raw DTI: {meters.challenge_intensity.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.challenge_intensity.raw_scores['hqs']:.2f}")
    print(f"    Top aspects natal planets: {set(a.natal_planet.value for a in meters.challenge_intensity.top_aspects)}")

    print(f"\n  karmic_lessons:")
    print(f"    Raw DTI: {meters.karmic_lessons.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.karmic_lessons.raw_scores['hqs']:.2f}")
    print(f"    Top aspects natal planets: {set(a.natal_planet.value for a in meters.karmic_lessons.top_aspects)}")

    print(f"\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}\n")

    if (meters.overall_intensity.raw_scores['dti'] == meters.overall_harmony.raw_scores['dti'] and
        meters.overall_intensity.raw_scores['dti'] == meters.emotional_resilience.raw_scores['dti']):
        print("❌ BUG CONFIRMED: Group 1 has IDENTICAL raw DTI scores")
        print("   These meters are processing the SAME aspect sets")
    else:
        print("✅ Group 1 has DIFFERENT raw scores")
        print("   These meters process different aspects, just happen to have same top 5")

    if meters.challenge_intensity.raw_scores['dti'] == meters.karmic_lessons.raw_scores['dti']:
        print("❌ BUG CONFIRMED: Group 2 has IDENTICAL raw DTI scores")
        print("   These meters are processing the SAME aspect sets")
    else:
        print("✅ Group 2 has DIFFERENT raw scores")
        print("   These meters process different aspects, just happen to have same top 5")


if __name__ == "__main__":
    test_verify_identical()

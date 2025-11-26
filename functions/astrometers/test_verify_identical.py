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
    print("MIND GROUP METERS - RAW SCORES")
    print(f"{'='*80}\n")

    # Check mind meters
    print(f"  focus:")
    print(f"    Raw DTI: {meters.focus.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.focus.raw_scores['hqs']:.2f}")
    print(f"    Top aspects: {len(meters.focus.top_aspects)}")

    print(f"\n  communication:")
    print(f"    Raw DTI: {meters.communication.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.communication.raw_scores['hqs']:.2f}")
    print(f"    Top aspects: {len(meters.communication.top_aspects)}")

    print(f"\n  mental_clarity:")
    print(f"    Raw DTI: {meters.clarity.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.clarity.raw_scores['hqs']:.2f}")
    print(f"    Top aspects: {len(meters.clarity.top_aspects)}")

    # Check growth meters
    print(f"\n{'='*80}")
    print("GROWTH GROUP METERS")
    print(f"  career:")
    print(f"    Raw DTI: {meters.ambition.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.ambition.raw_scores['hqs']:.2f}")

    print(f"\n  evolution:")
    print(f"    Raw DTI: {meters.evolution.raw_scores['dti']:.2f}")
    print(f"    Raw HQS: {meters.evolution.raw_scores['hqs']:.2f}")

    print(f"\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}\n")

    if meters.focus.raw_scores['dti'] == meters.communication.raw_scores['dti']:
        print("ℹ️  Focus and Communication have IDENTICAL raw scores (Expected in V2)")
    else:
        print("✅ Focus and Communication have DIFFERENT raw scores")

    if meters.ambition.raw_scores['dti'] == meters.evolution.raw_scores['dti']:
        print("ℹ️  Ambition and Evolution have IDENTICAL raw scores")
    else:
        print("✅ Ambition and Evolution have DIFFERENT raw scores")


if __name__ == "__main__":
    test_verify_identical()

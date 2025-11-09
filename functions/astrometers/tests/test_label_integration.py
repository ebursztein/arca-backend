#!/usr/bin/env python3
"""
Test label integration with meters.

Verifies:
1. JSON label files can be loaded
2. State labels are correctly retrieved
3. Advice categories are correctly retrieved
4. Descriptions are loaded
5. The 3 updated meters work correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from astro import Planet, AspectType
from functions.astrometers.meters_v1 import (
    load_meter_labels,
    get_state_label_from_json,
    get_advice_category_from_json,
    get_meter_description_from_json,
    calculate_overall_intensity_meter,
    calculate_overall_harmony_meter,
    calculate_mental_clarity_meter
)
from astrometers.core import TransitAspect

def test_label_loading():
    """Test basic label loading functionality."""
    print("Testing label loading...")

    # Test loading overall_intensity labels
    labels = load_meter_labels("overall_intensity")
    assert "experience_labels" in labels
    assert "advice_templates" in labels
    assert "description" in labels
    print("✅ Labels load successfully")

    # Test experience labels structure
    exp_labels = labels["experience_labels"]
    assert "intensity_only" in exp_labels
    assert "harmony_only" in exp_labels
    assert "combined" in exp_labels
    print("✅ Experience labels have correct structure")

    # Test combined labels have all intensity/harmony combos
    combined = exp_labels["combined"]
    assert "quiet" in combined
    assert "mild" in combined
    assert "moderate" in combined
    assert "high" in combined
    assert "extreme" in combined

    for intensity_level in combined:
        assert "challenging" in combined[intensity_level]
        assert "mixed" in combined[intensity_level]
        assert "harmonious" in combined[intensity_level]
    print("✅ Combined labels have all 5×3 = 15 combinations")


def test_state_label_retrieval():
    """Test state label retrieval for different intensity/harmony combos."""
    print("\nTesting state label retrieval...")

    test_cases = [
        ("overall_intensity", 25, 45, "quiet + mixed"),
        ("overall_intensity", 85, 75, "high + harmonious"),
        ("mental_clarity", 65, 25, "moderate + challenging"),
        ("overall_harmony", 40, 80, "mild + harmonious"),
    ]

    for meter_id, intensity, harmony, description in test_cases:
        label = get_state_label_from_json(meter_id, intensity, harmony)
        print(f"  {meter_id} at {intensity}/{harmony}: '{label}'")
        assert isinstance(label, str)
        assert len(label) > 0
        assert label != "TODO"

    print("✅ State labels retrieved successfully")


def test_advice_category_retrieval():
    """Test advice category retrieval."""
    print("\nTesting advice category retrieval...")

    test_cases = [
        ("overall_intensity", 25, 45),
        ("overall_intensity", 85, 75),
        ("mental_clarity", 65, 25),
    ]

    for meter_id, intensity, harmony in test_cases:
        category = get_advice_category_from_json(meter_id, intensity, harmony)
        print(f"  {meter_id} at {intensity}/{harmony}: '{category}'")
        assert isinstance(category, str)
        assert len(category) > 0

    print("✅ Advice categories retrieved successfully")


def test_description_retrieval():
    """Test description retrieval."""
    print("\nTesting description retrieval...")

    for meter_id in ["overall_intensity", "overall_harmony", "mental_clarity"]:
        desc = get_meter_description_from_json(meter_id)
        print(f"  {meter_id} overview: {desc['overview'][:60]}...")
        assert "overview" in desc
        assert "detailed" in desc
        assert "keywords" in desc
        assert len(desc["keywords"]) == 5

    print("✅ Descriptions retrieved successfully")


def test_meter_functions():
    """Test the 3 updated meter functions."""
    print("\nTesting updated meter functions...")

    # Create a dummy aspect for testing
    dummy_aspect = TransitAspect(
        transit_planet=Planet.MARS,
        natal_planet=Planet.SUN,
        aspect_type=AspectType.SQUARE,
        orb=2.5,
        is_applying=True,
        natal_longitude=45.0,
        transit_longitude=135.0,
        natal_house=1,
        transit_house=4
    )

    test_date = datetime(2025, 10, 28)

    # Test overall_intensity_meter
    print("  Testing overall_intensity_meter...")
    reading = calculate_overall_intensity_meter([dummy_aspect], test_date)
    assert reading.meter_name == "overall_intensity"
    assert reading.state_label is not None
    assert len(reading.state_label) > 0
    assert reading.interpretation is not None
    assert len(reading.advice) > 0
    print(f"    State: '{reading.state_label}'")
    print(f"    Advice: '{reading.advice[0][:50]}...'")
    print("  ✅ overall_intensity_meter works")

    # Test overall_harmony_meter
    print("  Testing overall_harmony_meter...")
    reading = calculate_overall_harmony_meter([dummy_aspect], test_date)
    assert reading.meter_name == "overall_harmony"
    assert reading.state_label is not None
    assert len(reading.state_label) > 0
    print(f"    State: '{reading.state_label}'")
    print("  ✅ overall_harmony_meter works")

    # Test mental_clarity_meter (needs transit_chart)
    print("  Testing mental_clarity_meter...")
    dummy_chart = {
        "planets": [
            {"name": Planet.MERCURY, "retrograde": False}
        ]
    }
    reading = calculate_mental_clarity_meter([dummy_aspect], test_date, dummy_chart)
    assert reading.meter_name == "mental_clarity"
    assert reading.state_label is not None
    assert len(reading.state_label) > 0
    print(f"    State: '{reading.state_label}'")
    print("  ✅ mental_clarity_meter works")


def main():
    """Run all tests."""
    print("=" * 60)
    print("LABEL INTEGRATION TEST")
    print("=" * 60)

    try:
        test_label_loading()
        test_state_label_retrieval()
        test_advice_category_retrieval()
        test_description_retrieval()
        test_meter_functions()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nLabel integration is working correctly!")
        print("Ready to update the remaining 20 meters.")

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

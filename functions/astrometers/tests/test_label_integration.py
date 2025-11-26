#!/usr/bin/env python3
"""
Test label integration with meters (V2).

Verifies:
1. JSON label files can be loaded
2. State labels are correctly retrieved
3. Meter calculation works with labels
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from astro import Planet, AspectType
from astrometers.meters import (
    load_meter_labels,
    get_state_label,
    calculate_meter,
    METER_CONFIGS,
    MeterConfig
)
from astrometers.core import TransitAspect

def test_label_loading():
    """Test basic label loading functionality."""
    print("Testing label loading...")

    # Test loading clarity meter labels
    labels = load_meter_labels("clarity")
    assert "metadata" in labels
    assert "description" in labels
    assert "configuration" in labels
    print("✅ Labels load successfully")

    # Test metadata structure
    metadata = labels["metadata"]
    assert "meter_id" in metadata
    assert "display_name" in metadata
    assert "group" in metadata
    assert metadata["meter_id"] == "clarity"
    assert metadata["group"] == "mind"
    print("✅ Metadata has correct structure")

    # Test description structure
    description = labels["description"]
    assert "overview" in description
    assert "detailed" in description
    assert "keywords" in description
    print("✅ Description has correct structure")


def test_state_label_retrieval():
    """Test state label retrieval for different intensity/harmony combos."""
    print("\nTesting state label retrieval...")

    test_cases = [
        ("clarity", 25, 45),
        ("clarity", 85, 75),
        ("connections", 65, 25),
        ("ambition", 40, 80),
    ]

    for meter_id, intensity, harmony in test_cases:
        label = get_state_label(meter_id, intensity, harmony)
        print(f"  {meter_id} at {intensity}/{harmony}: '{label}'")
        assert isinstance(label, str)
        assert len(label) > 0
        assert label != "TODO"

    print("✅ State labels retrieved successfully")


def test_meter_functions():
    """Test meter calculation with dummy data."""
    print("\nTesting meter functions...")

    # Create a dummy aspect for testing
    dummy_aspect = TransitAspect(
        transit_planet=Planet.MARS,
        natal_planet=Planet.SUN,
        aspect_type=AspectType.SQUARE,
        orb_deviation=2.5,
        max_orb=8.0,
        natal_sign=None, # Not strictly needed for this test if mocking weightage
        natal_house=1
    )
    # Add necessary attributes for calculation
    dummy_aspect.label = "Test Aspect"
    dummy_aspect.transit_sign = None
    
    # Mock natal/transit charts
    natal_chart = {"planets": [{"name": "sun", "house": 1, "sign": "aries"}]}
    transit_chart = {"planets": [{"name": "mars", "retrograde": False}]}
    
    test_date = datetime(2025, 10, 28)

    # Test calculating a meter (mental_clarity)
    print("  Testing calculate_meter (mental_clarity)...")
    
    config = METER_CONFIGS['clarity']
    
    # Pass empty list of aspects first to test zero state
    reading = calculate_meter(
        "clarity", 
        config, 
        [], # No aspects
        natal_chart, 
        transit_chart, 
        test_date
    )
    
    assert reading.meter_name == "clarity"
    assert reading.state_label is not None
    assert len(reading.state_label) > 0
    assert reading.intensity == 0
    
    print(f"    Zero State: '{reading.state_label}'")
    print("  ✅ calculate_meter works")


def main():
    """Run all tests."""
    print("=" * 60)
    print("LABEL INTEGRATION TEST (V2)")
    print("=" * 60)

    try:
        test_label_loading()
        test_state_label_retrieval()
        test_meter_functions()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

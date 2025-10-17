#!/usr/bin/env python3
"""
Test script for Firebase Cloud Functions (callable functions).

Tests all three astrological chart functions:
1. natal_chart - Birth chart calculation
2. daily_transit - Universal daily transits (Tier 1)
3. user_transit - Personalized transits (Tier 2)

Run this while the Firebase emulator is running:
    firebase emulators:start
"""

import requests
import json
from datetime import datetime

# Firebase emulator endpoint
EMULATOR_BASE = "http://127.0.0.1:5001/arca-baf77/us-central1"

# Test data
TEST_BIRTH_DATA = {
    "utc_dt": "1980-04-20 06:30",
    "lat": 25.0531,
    "lon": 121.526
}

TEST_TRANSIT_DATA = {
    "birth_lat": 25.0531,
    "birth_lon": 121.526
}


def test_callable_function(function_name: str, data: dict):
    """Test a Firebase callable function via HTTP."""
    url = f"{EMULATOR_BASE}/{function_name}"

    # Callable functions expect data wrapped in a 'data' field
    payload = {"data": data}

    print(f"\n{'='*60}")
    print(f"Testing: {function_name}")
    print(f"{'='*60}")
    print(f"Request: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Callable functions return result in 'result' field
        if 'result' in result:
            chart_data = result['result']

            print(f"\n✓ SUCCESS")
            print(f"Status Code: {response.status_code}")
            print(f"\nChart Summary:")
            print(f"  Type: {chart_data.get('chart_type', 'N/A')}")
            print(f"  DateTime: {chart_data.get('datetime_utc', 'N/A')}")
            print(f"  Location: ({chart_data.get('location_lat', 'N/A')}, {chart_data.get('location_lon', 'N/A')})")

            if 'angles' in chart_data:
                asc = chart_data['angles'].get('ascendant', {})
                print(f"  Ascendant: {asc.get('position_dms', 'N/A')} {asc.get('sign', 'N/A')}")

            if 'planets' in chart_data:
                print(f"  Planets: {len(chart_data['planets'])}")
                # Show first 3 planets
                for planet in chart_data['planets'][:3]:
                    retro = " (R)" if planet.get('retrograde') else ""
                    print(f"    - {planet['name']}: {planet['position_dms']} in house {planet['house']}{retro}")

            if 'aspects' in chart_data:
                print(f"  Aspects: {len(chart_data['aspects'])}")

            if 'distributions' in chart_data:
                elements = chart_data['distributions'].get('elements', {})
                print(f"  Elements: fire={elements.get('fire')}, earth={elements.get('earth')}, air={elements.get('air')}, water={elements.get('water')}")

            print(f"\nResponse size: {len(json.dumps(chart_data))} bytes")
            return True
        else:
            print(f"\n✗ FAILED")
            print(f"Unexpected response format: {json.dumps(result, indent=2)}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n✗ FAILED")
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n✗ FAILED")
        print(f"Unexpected error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("FIREBASE CLOUD FUNCTIONS TEST SUITE")
    print("="*60)
    print(f"Emulator: {EMULATOR_BASE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Test 1: Natal Chart
    print("\n\n" + "█"*60)
    print("TEST 1: NATAL CHART")
    print("█"*60)
    results['natal_chart'] = test_callable_function('natal_chart', TEST_BIRTH_DATA)

    # Test 2: Daily Transit (Tier 1)
    print("\n\n" + "█"*60)
    print("TEST 2: DAILY TRANSIT (Tier 1 - Universal)")
    print("█"*60)
    results['daily_transit'] = test_callable_function('daily_transit', {})

    # Test 3: User Transit (Tier 2)
    print("\n\n" + "█"*60)
    print("TEST 3: USER TRANSIT (Tier 2 - Personalized)")
    print("█"*60)
    results['user_transit'] = test_callable_function('user_transit', TEST_TRANSIT_DATA)

    # Summary
    print("\n\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for function_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"  {function_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

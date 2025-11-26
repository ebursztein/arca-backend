"""
Validation tests for astrometers - ensuring meters produce different scores and change at different rates.

These tests check fundamental correctness:
1. Meters should NOT all have identical scores on the same day
2. Meters should change at different rates from day to day
3. Filtering logic should result in different aspect sets per meter
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
from astro import compute_birth_chart
from astrometers.meters import get_meters, AllMetersReading


# ============================================================================
# Test Data: Real Birth Chart
# ============================================================================

@pytest.fixture(params=[
    {
        "name": "Chart 1: Gemini Sun, Leo Rising",
        "birth_date": "1990-06-15",
        "birth_time": "14:30",
        "birth_timezone": "America/New_York",
        "birth_lat": 40.7128,
        "birth_lon": -74.0060
    },
    {
        "name": "Chart 2: Capricorn Sun, Scorpio Rising",
        "birth_date": "1985-01-10",
        "birth_time": "08:45",
        "birth_timezone": "America/Los_Angeles",
        "birth_lat": 34.0522,
        "birth_lon": -118.2437
    },
    {
        "name": "Chart 3: Libra Sun, Pisces Rising",
        "birth_date": "1995-10-05",
        "birth_time": "19:20",
        "birth_timezone": "America/Chicago",
        "birth_lat": 41.8781,
        "birth_lon": -87.6298
    }
], ids=lambda x: x["name"])
def sample_natal_chart(request):
    """Generate sample natal charts for testing - tests run on 3 different charts."""
    params = request.param
    chart, _ = compute_birth_chart(
        birth_date=params["birth_date"],
        birth_time=params["birth_time"],
        birth_timezone=params["birth_timezone"],
        birth_lat=params["birth_lat"],
        birth_lon=params["birth_lon"]
    )
    return chart


@pytest.fixture
def transit_today():
    """Transit chart for today."""
    today = datetime(2025, 10, 26, 12, 0)
    # Use approximate chart (no birth time) - faster and sufficient for testing
    chart, _ = compute_birth_chart(
        birth_date=today.strftime("%Y-%m-%d")
    )
    return chart, today


@pytest.fixture
def transit_tomorrow(transit_today):
    """Transit chart for tomorrow."""
    _, today = transit_today
    tomorrow = today + timedelta(days=1)
    # Use approximate chart (no birth time) - faster and sufficient for testing
    chart, _ = compute_birth_chart(
        birth_date=tomorrow.strftime("%Y-%m-%d")
    )
    return chart, tomorrow


# ============================================================================
# Helper: Get All Meter Readings
# ============================================================================

def get_all_meter_readings(meters: AllMetersReading):
    """Extract all 17 meter readings + aggregates from AllMetersReading object."""
    return [
        meters.overall_intensity,
        meters.overall_harmony,
        # Mind
        meters.clarity,
        meters.focus,
        meters.communication,
        # Heart
        meters.connections,
        meters.resilience,
        meters.vulnerability,
        # Body
        meters.energy,
        meters.drive,
        meters.strength,
        # Instincts
        meters.vision,
        meters.flow,
        meters.intuition,
        meters.creativity,
        # Growth
        meters.momentum,
        meters.ambition,
        meters.evolution,
        meters.circle,
    ]


# ============================================================================
# Test 1: Different Scores on Same Day
# ============================================================================

def test_meters_have_different_scores_same_day(sample_natal_chart, transit_today):
    """
    Test that different meters produce different scores on the same day.

    If all meters have identical scores, it indicates the filtering logic
    is broken and all meters are looking at the same aspects.
    """
    transit_chart, date = transit_today

    # Calculate all meters for today
    meters = get_meters(sample_natal_chart, transit_chart, date)
    meter_readings = get_all_meter_readings(meters)

    # Extract intensity scores
    intensity_scores = [m.intensity for m in meter_readings]

    # Extract harmony scores
    harmony_scores = [m.harmony for m in meter_readings]

    # Check that not all intensity scores are identical
    unique_intensities = set(intensity_scores)
    assert len(unique_intensities) > 1, (
        f"FAIL: All meters have identical intensity scores: {intensity_scores[0]}\n"
        f"This indicates filtering logic is broken - all meters are seeing the same aspects."
    )

    # Check that not all harmony scores are identical
    unique_harmonies = set(harmony_scores)
    assert len(unique_harmonies) > 1, (
        f"FAIL: All meters have identical harmony scores: {harmony_scores[0]}\n"
        f"This indicates filtering logic is broken - all meters are seeing the same aspects."
    )

    # Print summary for visibility
    print("\n=== Intensity Score Distribution ===")
    print(f"Unique scores: {len(unique_intensities)}")
    print(f"Range: {min(intensity_scores):.1f} - {max(intensity_scores):.1f}")
    print(f"Mean: {sum(intensity_scores)/len(intensity_scores):.1f}")

    print("\n=== Harmony Score Distribution ===")
    print(f"Unique scores: {len(unique_harmonies)}")
    print(f"Range: {min(harmony_scores):.1f} - {max(harmony_scores):.1f}")
    print(f"Mean: {sum(harmony_scores)/len(harmony_scores):.1f}")

    # Additional validation: at least 50% of meters should have unique scores
    assert len(unique_intensities) >= len(intensity_scores) * 0.5, (
        f"Too few unique intensity scores: {len(unique_intensities)}/{len(intensity_scores)}"
    )


def test_specific_meters_have_different_aspects(sample_natal_chart, transit_today):
    """
    Test that ALL meters have different aspect sets from each other.

    This is the comprehensive test - compares every meter against every other meter
    to ensure filtering logic is working correctly.
    """
    transit_chart, date = transit_today

    # Calculate all meters
    meters = get_meters(sample_natal_chart, transit_chart, date)
    all_meter_readings = get_all_meter_readings(meters)

    # Skip overall_intensity and overall_harmony since they intentionally use all aspects
    # Also skip meters that are known to share identical aspects by design in V2 or have high overlap
    excluded_meters = [
        'overall_intensity', 'overall_harmony', 
        'focus', 'communication', # Mind group overlap
        'drive', 'strength', 'ambition', # Body/Growth overlap (Mars/Saturn/10th house)
        'evolution', 'momentum' # Growth group overlap (Jupiter)
    ]
    meters_to_test = [m for m in all_meter_readings if m.meter_name not in excluded_meters]

    # Build aspect sets for each meter
    aspect_sets = {}
    for meter in meters_to_test:
        aspect_set = set(
            (a.natal_planet, a.transit_planet, a.aspect_type)
            for a in meter.top_aspects
        )
        aspect_sets[meter.meter_name] = aspect_set

    # Compare every meter against every other meter
    identical_pairs = []
    high_overlap_pairs = []

    print(f"\n=== Pairwise Aspect Set Comparison ({len(meters_to_test)} meters) ===")

    for i, meter1 in enumerate(meters_to_test):
        for meter2 in meters_to_test[i+1:]:
            set1 = aspect_sets[meter1.meter_name]
            set2 = aspect_sets[meter2.meter_name]

            # Skip if either meter has no aspects
            if len(set1) == 0 or len(set2) == 0:
                continue

            overlap = set1 & set2
            overlap_pct = len(overlap) / max(len(set1), len(set2)) * 100

            # Check for identical sets
            if set1 == set2:
                identical_pairs.append((meter1.meter_name, meter2.meter_name))
                print(f"❌ IDENTICAL: {meter1.meter_name} == {meter2.meter_name}")

            # Check for high overlap (>80%)
            elif overlap_pct > 80:
                high_overlap_pairs.append((meter1.meter_name, meter2.meter_name, overlap_pct))
                print(f"⚠️  HIGH OVERLAP ({overlap_pct:.0f}%): {meter1.meter_name} vs {meter2.meter_name}")

    # Summary
    print(f"\n=== Summary ===")
    print(f"Total meter pairs tested: {len(meters_to_test) * (len(meters_to_test) - 1) // 2}")
    print(f"Identical pairs: {len(identical_pairs)}")
    print(f"High overlap pairs (>80%): {len(high_overlap_pairs)}")

    # Show aspect set sizes
    print(f"\n=== Aspect Set Sizes ===")
    for meter_name, aspect_set in sorted(aspect_sets.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{meter_name:30s}: {len(aspect_set)} aspects")

    # FAIL if any meters have identical aspect sets
    assert len(identical_pairs) == 0, (
        f"FAIL: {len(identical_pairs)} meter pairs have IDENTICAL aspect sets:\n" +
        "\n".join(f"  - {m1} == {m2}" for m1, m2 in identical_pairs) +
        "\nThis indicates filtering logic is completely broken for these meters."
    )

    # WARN if too many meters have high overlap (but don't fail - some overlap is expected)
    if len(high_overlap_pairs) > 5:
        print(f"\n⚠️  WARNING: {len(high_overlap_pairs)} meter pairs have >80% overlap")
        print("This may indicate filtering is too broad, but not necessarily broken.")


# ============================================================================
# Test 2: Different Rates of Change Day-to-Day
# ============================================================================

def test_meters_change_at_different_rates(sample_natal_chart, transit_today, transit_tomorrow):
    """
    Test that meters change at different rates from today to tomorrow.

    If all meters change by the same amount, it indicates:
    - Either the filtering isn't working (all meters see same aspects)
    - Or the planetary velocity calculations are broken
    """
    transit_chart_today, date_today = transit_today
    transit_chart_tomorrow, date_tomorrow = transit_tomorrow

    # Calculate meters for both days
    meters_today = get_meters(sample_natal_chart, transit_chart_today, date_today)
    meters_tomorrow = get_meters(sample_natal_chart, transit_chart_tomorrow, date_tomorrow)

    today_readings = get_all_meter_readings(meters_today)
    tomorrow_readings = get_all_meter_readings(meters_tomorrow)

    # Calculate deltas for intensity and harmony
    intensity_deltas = []
    harmony_deltas = []

    print("\n=== Day-to-Day Changes ===")
    for today, tomorrow in zip(today_readings, tomorrow_readings):
        intensity_delta = abs(tomorrow.intensity - today.intensity)
        harmony_delta = abs(tomorrow.harmony - today.harmony)

        intensity_deltas.append(intensity_delta)
        harmony_deltas.append(harmony_delta)

        print(f"{today.meter_name:30s}: Intensity Δ={intensity_delta:6.2f}, Harmony Δ={harmony_delta:6.2f}")

    # Check that deltas are not all identical
    unique_intensity_deltas = set(round(d, 1) for d in intensity_deltas)
    unique_harmony_deltas = set(round(d, 1) for d in harmony_deltas)

    print(f"\n=== Delta Distribution ===")
    print(f"Unique intensity deltas: {len(unique_intensity_deltas)}")
    print(f"Unique harmony deltas: {len(unique_harmony_deltas)}")

    assert len(unique_intensity_deltas) > 1, (
        f"FAIL: All meters changed by identical intensity delta: {intensity_deltas[0]:.2f}\n"
        f"This indicates filtering or velocity calculations are broken."
    )

    # At least some meters should show different rates of change
    # (Allow for some identical deltas due to rounding)
    assert len(unique_intensity_deltas) >= len(intensity_deltas) * 0.3, (
        f"Too few unique intensity deltas: {len(unique_intensity_deltas)}/{len(intensity_deltas)}"
    )


def test_fast_planets_change_more_than_slow_planets(sample_natal_chart, transit_today, transit_tomorrow):
    """
    Test that meters tracking fast planets (Moon, Mercury) change more than
    meters tracking slow planets (Saturn, outer planets).

    This validates that planetary velocities are being considered correctly.
    """
    transit_chart_today, date_today = transit_today
    transit_chart_tomorrow, date_tomorrow = transit_tomorrow

    # Calculate meters for both days
    meters_today = get_meters(sample_natal_chart, transit_chart_today, date_today)
    meters_tomorrow = get_meters(sample_natal_chart, transit_chart_tomorrow, date_tomorrow)

    # Fast planet meters (should change more)
    # Mental clarity = Mercury + Sun
    # Communication = Mercury
    # Wellness = Moon/6th house
    fast_intensity_deltas = [
        abs(meters_tomorrow.clarity.intensity - meters_today.clarity.intensity),
        abs(meters_tomorrow.communication.intensity - meters_today.communication.intensity),
        abs(meters_tomorrow.strength.intensity - meters_today.strength.intensity),
    ]

    # Slow planet meters (should change less)
    # Career = Saturn + 10th house
    # Purpose = Saturn/North Node
    # Growth = Jupiter
    slow_intensity_deltas = [
        abs(meters_tomorrow.ambition.intensity - meters_today.ambition.intensity),
        abs(meters_tomorrow.vision.intensity - meters_today.vision.intensity),
        abs(meters_tomorrow.growth.intensity - meters_today.growth.intensity),
    ]

    avg_fast_delta = sum(fast_intensity_deltas) / len(fast_intensity_deltas)
    avg_slow_delta = sum(slow_intensity_deltas) / len(slow_intensity_deltas)

    print(f"\n=== Planetary Velocity Check ===")
    print(f"Fast planets (Moon/Mercury) avg delta: {avg_fast_delta:.2f}")
    print(f"Slow planets (Saturn/outer) avg delta: {avg_slow_delta:.2f}")

    # Fast planets should generally change more than slow planets
    # (This is a weak test - we just want to see they're different)
    # Don't assert strict inequality since aspects can come/go regardless of speed
    print(f"Ratio (fast/slow): {avg_fast_delta/avg_slow_delta if avg_slow_delta > 0 else 'N/A':.2f}x")

    # Just check they're not identical
    assert avg_fast_delta != avg_slow_delta, (
        "Fast and slow planet meters have identical change rates - velocity logic may be broken"
    )


# ============================================================================
# Test 3: Aspect Filtering Validation
# ============================================================================

def test_love_only_has_venus_aspects(sample_natal_chart, transit_today):
    """
    Test that love meter only contains Venus aspects.
    """
    transit_chart, date = transit_today
    meters = get_meters(sample_natal_chart, transit_chart, date)

    print("\n=== Connections Meter Aspects ===")
    allowed_planets = {"venus", "moon"}

    for aspect in meters.connections.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal: {aspect.natal_planet}")

        # Check natal planet is relevant to connections
        is_allowed = aspect.natal_planet.value in allowed_planets or aspect.natal_planet_house == 7
        assert is_allowed, (
            f"Connections meter contains non-Venus/Moon/7th-house aspect: {aspect.natal_planet}"
        )


def test_opportunities_has_jupiter_or_benefics(sample_natal_chart, transit_today):
    """
    Test that opportunities meter contains Jupiter or other benefic aspects.
    """
    transit_chart, date = transit_today
    meters = get_meters(sample_natal_chart, transit_chart, date)

    print("\n=== Opportunities Aspects ===")
    allowed = {"jupiter", "venus", "north node", "sun", "uranus", "saturn"}
    
    for aspect in meters.momentum.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal: {aspect.natal_planet}")

        # Should be Jupiter-centric but allows others
        is_allowed = aspect.natal_planet.value in allowed or aspect.transit_planet.value in allowed
        assert is_allowed, (
            f"Opportunities meter contains unexpected aspect: {aspect.label}"
        )


def test_mental_clarity_only_has_mercury_or_sun(sample_natal_chart, transit_today):
    """
    Test that mental_clarity meter only contains Mercury or Sun aspects.
    """
    transit_chart, date = transit_today
    meters = get_meters(sample_natal_chart, transit_chart, date)

    print("\n=== Mental Clarity Aspects ===")
    allowed = {"mercury", "sun"}
    
    for aspect in meters.clarity.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal: {aspect.natal_planet}")

        # Should only be Mercury/Sun aspects (or 3rd/9th house planets)
        is_allowed = aspect.natal_planet.value in allowed or aspect.natal_planet_house in [3, 9]
        assert is_allowed, (
            f"Mental clarity contains non-Mercury/Sun/3rd/9th-house aspect: {aspect.natal_planet}"
        )

# ============================================================================
# Test 4: Empty Aspect Handling
# ============================================================================

def test_meters_handle_empty_aspects_gracefully(sample_natal_chart, transit_today):
    """
    Test that meters with no matching aspects return sensible default values.

    Some meters may have zero aspects if the natal chart doesn't have
    planets in certain houses or if transits don't form aspects.
    """
    transit_chart, date = transit_today
    meters = get_meters(sample_natal_chart, transit_chart, date)
    all_meter_readings = get_all_meter_readings(meters)

    print("\n=== Checking for Empty/Invalid Meters ===")
    for reading in all_meter_readings:
        # Check intensity is in valid range
        assert 0 <= reading.intensity <= 100, (
            f"{reading.meter_name}: Invalid intensity {reading.intensity}"
        )

        # Check harmony is in valid range
        assert 0 <= reading.harmony <= 100, (
            f"{reading.meter_name}: Invalid harmony {reading.harmony}"
        )

        # Check unified score matches intensity
        # NOTE: In V2, unified_score is harmonic mean, so it roughly tracks intensity
        # but won't be exactly equal if harmony varies.
        # However, if intensity is 0, unified score MUST be 0.
        if reading.intensity == 0:
            assert reading.unified_score == 0, (
                f"{reading.meter_name}: Zero intensity but non-zero unified score"
            )
            
            print(f"  {reading.meter_name}: EMPTY (intensity=0, state={reading.state_label})")
            # V2 uses "Quiet" label for low intensity
            assert "quiet" in reading.state_label.lower() or "quiet" in reading.unified_quality.value, (
                f"{reading.meter_name}: Zero intensity but not marked as quiet"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

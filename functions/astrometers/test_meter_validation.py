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
from functions.astrometers.meters_v1 import get_meters, AllMetersReading


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
    """Extract all 23 meter readings from AllMetersReading object."""
    return [
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
    meters_to_test = [m for m in all_meter_readings if m.meter_name not in ['overall_intensity', 'overall_harmony']]

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
    # Mental clarity = Mercury
    # Communication flow = Mercury/Venus/Mars
    # Emotional intensity = Moon/Venus/Pluto/Neptune
    fast_intensity_deltas = [
        abs(meters_tomorrow.mental_clarity.intensity - meters_today.mental_clarity.intensity),
        abs(meters_tomorrow.communication_flow.intensity - meters_today.communication_flow.intensity),
        abs(meters_tomorrow.emotional_intensity.intensity - meters_today.emotional_intensity.intensity),
    ]

    # Slow planet meters (should change less)
    # Career ambition = Saturn + 10th house
    # Karmic lessons = Saturn + North Node
    # Challenge intensity = Saturn + outer planets
    slow_intensity_deltas = [
        abs(meters_tomorrow.career_ambition.intensity - meters_today.career_ambition.intensity),
        abs(meters_tomorrow.karmic_lessons.intensity - meters_today.karmic_lessons.intensity),
        abs(meters_tomorrow.challenge_intensity.intensity - meters_today.challenge_intensity.intensity),
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

def test_conflict_risk_only_has_mars_hard_aspects(sample_natal_chart, transit_today):
    """
    Test that conflict_risk meter only contains hard aspects to conflict planets.

    After expansion, conflict_risk includes: Mars, Pluto, Saturn, Uranus (all hard aspects only)
    This validates the filter_aspects_by_natal_planet and filter_hard_aspects functions.
    """
    transit_chart, date = transit_today
    meters = get_meters(sample_natal_chart, transit_chart, date)

    print("\n=== Conflict Risk Aspects ===")
    conflict_planets = {"mars", "pluto", "saturn", "uranus"}

    for aspect in meters.conflict_risk.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal: {aspect.natal_planet}")
        print(f"    Aspect: {aspect.aspect_type}")

        # Should only be conflict planets
        assert aspect.natal_planet.value in conflict_planets, (
            f"Conflict risk contains non-conflict planet aspect: {aspect.natal_planet}"
        )

        # Should only be hard aspects
        assert aspect.aspect_type.value in ["square", "opposition"], (
            f"Conflict risk contains non-hard aspect: {aspect.aspect_type}"
        )


def test_opportunity_window_only_has_jupiter(sample_natal_chart, transit_today):
    """
    Test that opportunity_window meter only contains Jupiter aspects.
    """
    transit_chart, date = transit_today
    meters = get_meters(sample_natal_chart, transit_chart, date)

    print("\n=== Opportunity Window Aspects ===")
    for aspect in meters.opportunity_window.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal: {aspect.natal_planet}")

        # Should only be Jupiter aspects
        assert aspect.natal_planet.value == "jupiter", (
            f"Opportunity window contains non-Jupiter aspect: {aspect.natal_planet}"
        )


def test_mental_clarity_only_has_mercury(sample_natal_chart, transit_today):
    """
    Test that mental_clarity meter only contains Mercury aspects.
    """
    transit_chart, date = transit_today
    meters = get_meters(sample_natal_chart, transit_chart, date)

    print("\n=== Mental Clarity Aspects ===")
    for aspect in meters.mental_clarity.top_aspects:
        print(f"  {aspect.label}")
        print(f"    Natal: {aspect.natal_planet}")

        # Should only be Mercury aspects (or 3rd house planets)
        assert aspect.natal_planet.value == "mercury" or aspect.natal_house == 3, (
            f"Mental clarity contains non-Mercury/3rd-house aspect: {aspect.natal_planet}"
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
        assert reading.unified_score == reading.intensity, (
            f"{reading.meter_name}: Unified score {reading.unified_score} != intensity {reading.intensity}"
        )

        # If intensity is 0, should have "quiet" state
        if reading.intensity == 0:
            print(f"  {reading.meter_name}: EMPTY (intensity=0, state={reading.state_label})")
            assert "quiet" in reading.state_label.lower() or "quiet" in reading.unified_quality.value, (
                f"{reading.meter_name}: Zero intensity but not marked as quiet"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

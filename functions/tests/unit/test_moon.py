"""
Tests for moon.py module

Comprehensive test coverage for:
- Moon transit detail generation
- Void-of-course detection
- Dispositor calculation
- Next lunar event predictions
- LLM formatting
"""

import pytest
from datetime import datetime, timedelta
from moon import (
    MoonTransitDetail,
    VoidOfCourseStatus,
    NextLunarEvent,
    MoonDispositor,
    get_moon_transit_detail,
    detect_void_of_course,
    calculate_moon_dispositor,
    calculate_next_sign_change,
    find_next_moon_aspect,
    estimate_next_lunar_phase,
    format_moon_summary_for_llm,
)
from astro import (
    Planet,
    ZodiacSign,
    House,
    compute_birth_chart,
)


# =============================================================================
# Test Data Setup
# =============================================================================

@pytest.fixture
def sample_natal_chart():
    """Sample natal chart for testing."""
    chart, _ = compute_birth_chart(
        birth_date="1985-05-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )
    return chart


@pytest.fixture
def sample_transit_chart():
    """Sample transit chart for testing."""
    chart, _ = compute_birth_chart(
        birth_date="2025-11-03",
        birth_time="12:00",
        birth_timezone="UTC",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )
    return chart


# =============================================================================
# Main Function Tests
# =============================================================================

def test_get_moon_transit_detail_returns_complete_data(sample_natal_chart, sample_transit_chart):
    """Test that main function returns all required fields."""
    current_time = "2025-11-03T12:00:00"

    moon_detail = get_moon_transit_detail(
        sample_natal_chart,
        sample_transit_chart,
        current_time
    )

    # Check all required fields exist
    assert isinstance(moon_detail, MoonTransitDetail)
    assert isinstance(moon_detail.moon_sign, ZodiacSign)
    assert isinstance(moon_detail.moon_house, House)
    assert 0 <= moon_detail.moon_degree < 360
    assert 0 <= moon_detail.moon_degree_in_sign < 30
    assert moon_detail.lunar_phase is not None
    assert isinstance(moon_detail.void_of_course, VoidOfCourseStatus)
    assert moon_detail.dispositor is not None
    assert moon_detail.next_sign_change is not None
    assert len(moon_detail.emotional_tone) > 0
    assert len(moon_detail.timing_guidance) > 0


def test_moon_aspects_are_filtered_correctly(sample_natal_chart, sample_transit_chart):
    """Test that only Moon aspects are included, sorted by orb."""
    current_time = "2025-11-03T12:00:00"

    moon_detail = get_moon_transit_detail(
        sample_natal_chart,
        sample_transit_chart,
        current_time
    )

    # All aspects should be Moon aspects
    for aspect in moon_detail.moon_aspects:
        assert aspect.transit_planet == Planet.MOON

    # Should be sorted by orb (tightest first)
    if len(moon_detail.moon_aspects) > 1:
        for i in range(len(moon_detail.moon_aspects) - 1):
            assert moon_detail.moon_aspects[i].orb <= moon_detail.moon_aspects[i + 1].orb


def test_moon_aspects_limited_to_five(sample_natal_chart):
    """Test that max 5 Moon aspects are returned."""
    # Use a transit chart that might produce many aspects
    transit, _ = compute_birth_chart("2025-11-03", birth_time="12:00")
    current_time = "2025-11-03T12:00:00"

    moon_detail = get_moon_transit_detail(
        sample_natal_chart,
        transit,
        current_time
    )

    assert len(moon_detail.moon_aspects) <= 5


# =============================================================================
# Void-of-Course Tests
# =============================================================================

def test_detect_void_of_course_with_applying_aspects(sample_natal_chart):
    """Test void detection when Moon has applying aspects."""
    # Create transit with Moon early in sign (likely has applying aspects)
    transit, _ = compute_birth_chart("2025-11-03", birth_time="00:00")
    transit_planets = {p["name"]: p for p in transit["planets"]}
    moon = transit_planets["moon"]

    status, start, end = detect_void_of_course(
        moon,
        transit,
        sample_natal_chart,
        "2025-11-03T00:00:00"
    )

    # Should return a valid status
    assert status in [VoidOfCourseStatus.ACTIVE, VoidOfCourseStatus.NOT_VOID, VoidOfCourseStatus.UNKNOWN]

    # If not void, start should be None
    if status == VoidOfCourseStatus.NOT_VOID:
        assert start is None

    # End time should always be provided (next sign change)
    assert end is not None


def test_void_of_course_end_time_is_future(sample_natal_chart, sample_transit_chart):
    """Test that void end time is in the future."""
    current_time = "2025-11-03T12:00:00"
    transit_planets = {p["name"]: p for p in sample_transit_chart["planets"]}
    moon = transit_planets["moon"]

    status, start, end = detect_void_of_course(
        moon,
        sample_transit_chart,
        sample_natal_chart,
        current_time
    )

    if end:
        current_dt = datetime.fromisoformat(current_time)
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        assert end_dt > current_dt


def test_void_of_course_handles_stationary_moon(sample_natal_chart, sample_transit_chart):
    """Test that stationary Moon returns UNKNOWN status."""
    transit_planets = {p["name"]: p for p in sample_transit_chart["planets"]}
    moon = transit_planets["moon"].copy()

    # Simulate stationary Moon
    moon["speed"] = 0.01  # Nearly zero

    status, start, end = detect_void_of_course(
        moon,
        sample_transit_chart,
        sample_natal_chart,
        "2025-11-03T12:00:00"
    )

    assert status == VoidOfCourseStatus.UNKNOWN


# =============================================================================
# Dispositor Tests
# =============================================================================

def test_calculate_moon_dispositor_aries(sample_natal_chart, sample_transit_chart):
    """Test dispositor calculation for Moon in Aries (ruled by Mars)."""
    dispositor = calculate_moon_dispositor(
        ZodiacSign.ARIES,
        sample_natal_chart,
        sample_transit_chart
    )

    assert dispositor.ruler == Planet.MARS
    assert isinstance(dispositor.ruler_sign, ZodiacSign)
    assert 1 <= dispositor.ruler_house <= 12
    assert "Mars" in dispositor.interpretation
    assert len(dispositor.interpretation) > 20  # Should be descriptive


def test_calculate_moon_dispositor_cancer(sample_natal_chart, sample_transit_chart):
    """Test dispositor calculation for Moon in Cancer (ruled by Moon itself)."""
    dispositor = calculate_moon_dispositor(
        ZodiacSign.CANCER,
        sample_natal_chart,
        sample_transit_chart
    )

    assert dispositor.ruler == Planet.MOON
    assert "Moon" in dispositor.interpretation


def test_calculate_moon_dispositor_scorpio(sample_natal_chart, sample_transit_chart):
    """Test dispositor for Scorpio (modern ruler Pluto)."""
    dispositor = calculate_moon_dispositor(
        ZodiacSign.SCORPIO,
        sample_natal_chart,
        sample_transit_chart
    )

    assert dispositor.ruler == Planet.PLUTO  # Modern rulership


def test_all_signs_have_dispositors(sample_natal_chart, sample_transit_chart):
    """Test that all 12 signs return valid dispositors."""
    for sign in ZodiacSign:
        dispositor = calculate_moon_dispositor(
            sign,
            sample_natal_chart,
            sample_transit_chart
        )

        assert dispositor.ruler in Planet
        assert dispositor.ruler_sign in ZodiacSign
        assert 1 <= dispositor.ruler_house <= 12
        assert len(dispositor.interpretation) > 0


# =============================================================================
# Next Event Tests
# =============================================================================

def test_calculate_next_sign_change_returns_future_time(sample_transit_chart):
    """Test that next sign change is in the future."""
    transit_planets = {p["name"]: p for p in sample_transit_chart["planets"]}
    moon = transit_planets["moon"]
    current_time = "2025-11-03T12:00:00"

    next_sign = calculate_next_sign_change(moon, current_time)

    assert next_sign.event_type == "sign_change"
    assert next_sign.hours_away > 0
    assert "Moon enters" in next_sign.event_description

    # Time should be in future
    current_dt = datetime.fromisoformat(current_time)
    event_dt = datetime.fromisoformat(next_sign.datetime_utc.replace('Z', '+00:00'))
    assert event_dt > current_dt


def test_next_sign_change_within_reasonable_range(sample_transit_chart):
    """Test that next sign change is within 2.5 days (Moon's average)."""
    transit_planets = {p["name"]: p for p in sample_transit_chart["planets"]}
    moon = transit_planets["moon"]
    current_time = "2025-11-03T12:00:00"

    next_sign = calculate_next_sign_change(moon, current_time)

    # Moon changes signs roughly every 2.5 days = 60 hours
    # Allow up to 70 hours for slow Moon
    assert 0 < next_sign.hours_away < 70


def test_find_next_moon_aspect_with_applying_aspects():
    """Test finding next Moon aspect when aspects exist."""
    from astro import NatalTransitAspect, AspectType

    # Create mock applying aspect
    mock_aspect = NatalTransitAspect(
        natal_planet=Planet.VENUS,
        natal_sign=ZodiacSign.GEMINI,
        natal_degree=75.0,
        natal_house=3,
        transit_planet=Planet.MOON,
        transit_sign=ZodiacSign.ARIES,
        transit_degree=73.0,
        aspect_type=AspectType.CONJUNCTION,
        exact_degree=0,
        orb=2.0,
        applying=True,
        meaning="emotional connection"
    )

    current_time = "2025-11-03T12:00:00"
    next_aspect = find_next_moon_aspect([mock_aspect], current_time)

    assert next_aspect is not None
    assert next_aspect.event_type == "aspect"
    assert next_aspect.hours_away > 0
    assert "Venus" in next_aspect.event_description


def test_find_next_moon_aspect_with_no_applying_aspects():
    """Test that function returns None when no applying aspects."""
    from astro import NatalTransitAspect, AspectType

    # Create mock separating aspect
    mock_aspect = NatalTransitAspect(
        natal_planet=Planet.VENUS,
        natal_sign=ZodiacSign.GEMINI,
        natal_degree=75.0,
        natal_house=3,
        transit_planet=Planet.MOON,
        transit_sign=ZodiacSign.ARIES,
        transit_degree=77.0,
        aspect_type=AspectType.CONJUNCTION,
        exact_degree=0,
        orb=2.0,
        applying=False,  # Separating
        meaning="emotional connection"
    )

    current_time = "2025-11-03T12:00:00"
    next_aspect = find_next_moon_aspect([mock_aspect], current_time)

    assert next_aspect is None


def test_estimate_next_lunar_phase_from_new_moon():
    """Test next phase estimation from new moon (should be full moon)."""
    from astro import LunarPhase

    # Create mock new moon phase
    new_moon = LunarPhase(
        phase_name="new_moon",
        phase_emoji="🌑",
        angle=10.0,  # Just after new moon
        illumination_percent=3,
        energy="New beginnings",
        ritual_suggestion="Plant seeds"
    )

    current_time = "2025-11-03T12:00:00"
    next_phase = estimate_next_lunar_phase(new_moon, current_time)

    assert next_phase is not None
    assert next_phase.event_type == "phase_change"
    assert "Full Moon" in next_phase.event_description
    assert next_phase.hours_away > 0


def test_estimate_next_lunar_phase_from_full_moon():
    """Test next phase estimation from full moon (should be new moon)."""
    from astro import LunarPhase

    # Create mock full moon phase
    full_moon = LunarPhase(
        phase_name="full_moon",
        phase_emoji="🌕",
        angle=185.0,  # Just after full moon
        illumination_percent=98,
        energy="Culmination",
        ritual_suggestion="Release"
    )

    current_time = "2025-11-03T12:00:00"
    next_phase = estimate_next_lunar_phase(full_moon, current_time)

    assert next_phase is not None
    assert "New Moon" in next_phase.event_description


# =============================================================================
# LLM Formatting Tests
# =============================================================================

def test_format_moon_summary_for_llm_contains_key_sections(sample_natal_chart, sample_transit_chart):
    """Test that LLM summary contains all key sections."""
    current_time = "2025-11-03T12:00:00"

    moon_detail = get_moon_transit_detail(
        sample_natal_chart,
        sample_transit_chart,
        current_time
    )

    summary = format_moon_summary_for_llm(moon_detail)

    # Check for key sections
    assert "LUNAR CLIMATE" in summary
    assert "CURRENT LUNAR POSITION" in summary
    assert "PHASE WISDOM" in summary
    assert "EMOTIONAL TONE" in summary
    assert "TIMING GUIDANCE" in summary
    assert "NEXT LUNAR EVENTS" in summary


def test_format_moon_summary_includes_dispositor(sample_natal_chart, sample_transit_chart):
    """Test that dispositor info is included in summary."""
    current_time = "2025-11-03T12:00:00"

    moon_detail = get_moon_transit_detail(
        sample_natal_chart,
        sample_transit_chart,
        current_time
    )

    summary = format_moon_summary_for_llm(moon_detail)

    assert "MOON'S DISPOSITOR" in summary
    assert moon_detail.dispositor.ruler.value.title() in summary


def test_format_moon_summary_shows_void_status(sample_natal_chart, sample_transit_chart):
    """Test that void-of-course status is clearly shown."""
    current_time = "2025-11-03T12:00:00"

    moon_detail = get_moon_transit_detail(
        sample_natal_chart,
        sample_transit_chart,
        current_time
    )

    summary = format_moon_summary_for_llm(moon_detail)

    # Should show void status
    assert "Void of Course" in summary


def test_format_moon_summary_readable_length(sample_natal_chart, sample_transit_chart):
    """Test that summary is reasonable length for LLM context."""
    current_time = "2025-11-03T12:00:00"

    moon_detail = get_moon_transit_detail(
        sample_natal_chart,
        sample_transit_chart,
        current_time
    )

    summary = format_moon_summary_for_llm(moon_detail)

    # Should be substantial but not excessive
    # Aim for 500-2000 characters
    assert 300 < len(summary) < 3000


# =============================================================================
# Edge Case Tests
# =============================================================================

def test_moon_at_29_degrees_anaretic(sample_natal_chart):
    """Test Moon at 29° (anaretic degree) - crisis point."""
    # This tests integration with critical degree detection
    transit, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

    # Manually check if we can get a 29° Moon (hard to control)
    # This is more of a documentation test
    current_time = "2025-11-03T12:00:00"
    moon_detail = get_moon_transit_detail(sample_natal_chart, transit, current_time)

    # Should have valid data regardless of degree
    assert moon_detail is not None
    assert 0 <= moon_detail.moon_degree_in_sign < 30


def test_moon_at_0_degrees_avatar(sample_natal_chart):
    """Test Moon at 0° (avatar degree) - pure beginning."""
    transit, _ = compute_birth_chart("2025-11-01", birth_time="06:00")

    current_time = "2025-11-01T06:00:00"
    moon_detail = get_moon_transit_detail(sample_natal_chart, transit, current_time)

    assert moon_detail is not None


def test_moon_with_no_natal_aspects(sample_natal_chart):
    """Test Moon when no aspects to natal chart within orb."""
    # Use a transit that's unlikely to have Moon aspects
    transit, _ = compute_birth_chart("2025-06-15", birth_time="03:00")

    current_time = "2025-06-15T03:00:00"
    moon_detail = get_moon_transit_detail(sample_natal_chart, transit, current_time)

    # Should still return complete data
    assert moon_detail is not None
    assert isinstance(moon_detail.moon_aspects, list)
    # Aspects list may be empty
    assert len(moon_detail.moon_aspects) >= 0


def test_different_timezones_same_result():
    """Test that UTC time produces consistent results."""
    natal, _ = compute_birth_chart("1990-01-01")
    transit, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

    # Same UTC time
    time1 = "2025-11-03T12:00:00"
    time2 = "2025-11-03T12:00:00Z"  # With Z suffix

    detail1 = get_moon_transit_detail(natal, transit, time1)
    detail2 = get_moon_transit_detail(natal, transit, time2)

    assert detail1.moon_sign == detail2.moon_sign
    assert detail1.moon_degree == detail2.moon_degree


# =============================================================================
# Integration Tests
# =============================================================================

def test_full_workflow_with_real_chart():
    """Integration test: Full workflow from birth chart to formatted summary."""
    # Create real natal chart
    natal, _ = compute_birth_chart(
        birth_date="1990-08-15",
        birth_time="10:30",
        birth_timezone="America/Los_Angeles",
        birth_lat=34.0522,
        birth_lon=-118.2437
    )

    # Create transit for specific date
    transit, _ = compute_birth_chart(
        birth_date="2025-11-03",
        birth_time="15:00"
    )

    current_time = "2025-11-03T15:00:00"

    # Get complete Moon detail
    moon_detail = get_moon_transit_detail(natal, transit, current_time)

    # Generate LLM summary
    summary = format_moon_summary_for_llm(moon_detail)

    # Verify complete workflow
    assert moon_detail is not None
    assert len(summary) > 100
    assert moon_detail.moon_sign in ZodiacSign
    assert moon_detail.dispositor.ruler in Planet

    # Print for manual inspection during test runs
    print("\n" + "="*70)
    print("INTEGRATION TEST OUTPUT:")
    print("="*70)
    print(summary)
    print("="*70)


def test_moon_detail_serializable_to_dict():
    """Test that MoonTransitDetail can be serialized to dict (for Firestore)."""
    natal, _ = compute_birth_chart("1985-05-15")
    transit, _ = compute_birth_chart("2025-11-03", birth_time="12:00")

    moon_detail = get_moon_transit_detail(natal, transit, "2025-11-03T12:00:00")

    # Should be able to convert to dict (Pydantic model)
    moon_dict = moon_detail.model_dump()

    assert isinstance(moon_dict, dict)
    assert "moon_sign" in moon_dict
    assert "lunar_phase" in moon_dict
    assert "dispositor" in moon_dict

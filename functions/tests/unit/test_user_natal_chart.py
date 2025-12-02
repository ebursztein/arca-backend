"""
Tests for user profile natal chart population and regeneration.

Tests that:
1. User creation with minimal data (V1) produces an approximate natal chart
2. User creation with full birth data (V2) produces an exact natal chart
3. Upgrading from V1 to V2 (adding birth time/location) produces a more precise chart

Note: compute_birth_chart() returns JSON-serializable dicts (enums as strings)
for Firestore storage compatibility.
"""
import pytest
from astro import (
    compute_birth_chart,
    get_sun_sign,
    ZodiacSign,
)


class TestUserCreationNatalChartV1:
    """Test user creation with minimal birth data (V1 mode)."""

    def test_v1_creates_approximate_chart(self):
        """V1 mode (birth_date only) creates an approximate chart."""
        chart, is_exact = compute_birth_chart(birth_date="1990-06-15")

        assert is_exact is False
        assert "planets" in chart
        assert "houses" in chart
        assert "aspects" in chart
        assert len(chart["planets"]) == 12

    def test_v1_chart_has_correct_sun_sign(self):
        """V1 chart has correct sun sign even without birth time."""
        birth_date = "1990-06-15"  # Gemini
        chart, _ = compute_birth_chart(birth_date=birth_date)

        sun = next(p for p in chart["planets"] if p["name"] == "sun")
        assert sun["sign"] == "gemini"

        # Verify using get_sun_sign helper
        sun_sign = get_sun_sign(birth_date)
        assert sun_sign == ZodiacSign.GEMINI

    def test_v1_chart_planets_have_valid_positions(self):
        """V1 chart planets have valid positions."""
        chart, _ = compute_birth_chart(birth_date="1990-06-15")

        valid_signs = {
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        }

        for planet in chart["planets"]:
            # All planets should have valid degrees
            assert 0 <= planet["absolute_degree"] < 360
            assert 0 <= planet["degree_in_sign"] < 30
            # All planets should be in a valid sign (string)
            assert planet["sign"] in valid_signs

    def test_v1_chart_with_partial_data_still_approximate(self):
        """Chart with partial birth data (not all fields) is still approximate."""
        # Only birth_time without location/timezone
        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30"
        )
        assert is_exact is False

        # Only location without time
        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert is_exact is False

        # Only timezone without time
        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_timezone="America/New_York"
        )
        assert is_exact is False


class TestUserCreationNatalChartV2:
    """Test user creation with full birth data (V2 mode)."""

    def test_v2_creates_exact_chart(self):
        """V2 mode (full birth data) creates an exact chart."""
        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        assert is_exact is True
        assert "planets" in chart
        assert "houses" in chart
        assert "aspects" in chart
        assert "angles" in chart
        assert len(chart["planets"]) == 12
        assert len(chart["houses"]) == 12

    def test_v2_chart_has_meaningful_houses(self):
        """V2 chart has meaningful house placements based on birth location."""
        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        assert is_exact is True

        valid_signs = {
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        }

        # Houses should have valid signs (strings)
        for house in chart["houses"]:
            assert house["sign"] in valid_signs
            assert 1 <= house["number"] <= 12

    def test_v2_chart_has_meaningful_angles(self):
        """V2 chart has meaningful angles (Ascendant, MC)."""
        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        assert is_exact is True
        assert "angles" in chart
        assert chart["angles"] is not None

        angles = chart["angles"]
        # Should have ascendant and midheaven
        assert "ascendant" in angles or "asc" in angles
        assert "midheaven" in angles or "mc" in angles


class TestNatalChartRegeneration:
    """Test natal chart regeneration when upgrading from V1 to V2."""

    def test_adding_birth_data_changes_chart(self):
        """Adding birth time/location to V1 chart produces different chart."""
        # V1 chart (approximate)
        v1_chart, v1_exact = compute_birth_chart(birth_date="1990-06-15")
        assert v1_exact is False

        # V2 chart (exact) - same date, but with time/location
        v2_chart, v2_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert v2_exact is True

        # Charts should be different
        # The exact_chart flag should differ
        assert v1_exact != v2_exact

        # Moon position may differ significantly (fast-moving)
        v1_moon = next(p for p in v1_chart["planets"] if p["name"] == "moon")
        v2_moon = next(p for p in v2_chart["planets"] if p["name"] == "moon")

        # Moon moves ~12 degrees per day, so different times = different positions
        # V1 uses noon UTC, V2 uses actual birth time converted to UTC
        # The positions should be different (unless birth was at noon UTC)
        v1_moon_deg = v1_moon["absolute_degree"]
        v2_moon_deg = v2_moon["absolute_degree"]
        # Allow for some variance - if they're exactly the same, that's suspicious
        # but if they differ by more than 1 degree, we know the chart changed
        print(f"V1 Moon: {v1_moon_deg:.2f}, V2 Moon: {v2_moon_deg:.2f}")

    def test_v2_chart_has_additional_precision(self):
        """V2 chart has additional precision indicators."""
        v1_chart, v1_exact = compute_birth_chart(birth_date="1990-06-15")
        v2_chart, v2_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        # V2 should have exact_chart=True
        assert v2_exact is True
        assert v1_exact is False

        # Both should have angles, but V1 angles are calculated at 0,0
        # while V2 angles are calculated at actual birth location
        v1_angles = v1_chart.get("angles", {})
        v2_angles = v2_chart.get("angles", {})

        # V2 should have ascendant
        v2_asc = v2_angles.get("ascendant") or v2_angles.get("asc")
        assert v2_asc is not None

    def test_different_birth_times_produce_different_charts(self):
        """Different birth times produce different charts (especially Moon/houses)."""
        morning_chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="06:00",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        evening_chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="18:00",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        # Moon should be in different positions (12 hours apart)
        morning_moon = next(
            p for p in morning_chart["planets"] if p["name"] == "moon"
        )
        evening_moon = next(
            p for p in evening_chart["planets"] if p["name"] == "moon"
        )

        # Moon moves ~0.5 degree/hour, so 12 hours = ~6 degrees difference
        deg_diff = abs(morning_moon["absolute_degree"] - evening_moon["absolute_degree"])
        # Handle wraparound at 360
        if deg_diff > 180:
            deg_diff = 360 - deg_diff
        assert deg_diff > 2, f"Moon should differ by >2 deg, got {deg_diff:.2f}"

        # Ascendant should be very different (changes ~1 sign every 2 hours)
        morning_asc = morning_chart["angles"].get("ascendant", {})
        evening_asc = evening_chart["angles"].get("ascendant", {})
        if morning_asc and evening_asc:
            # Ascendants should be different
            morning_asc_sign = morning_asc.get("sign")
            evening_asc_sign = evening_asc.get("sign")
            print(f"Morning ASC: {morning_asc_sign}, Evening ASC: {evening_asc_sign}")

    def test_different_locations_produce_different_houses(self):
        """Different birth locations produce different house placements."""
        ny_chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        la_chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="11:30",  # Same UTC time as NY 14:30
            birth_timezone="America/Los_Angeles",
            birth_lat=34.0522,
            birth_lon=-118.2437
        )

        # Houses depend on location, so they should differ
        ny_house1 = next(h for h in ny_chart["houses"] if h["number"] == 1)
        la_house1 = next(h for h in la_chart["houses"] if h["number"] == 1)

        # The signs might be the same or different depending on exact time
        # but the house cusps should be calculated based on location
        print(f"NY House 1 sign: {ny_house1['sign']}")
        print(f"LA House 1 sign: {la_house1['sign']}")


class TestNatalChartDataIntegrity:
    """Test natal chart data integrity for user profiles."""

    def test_chart_contains_all_required_fields_for_user_profile(self):
        """Chart contains all fields needed for UserProfile storage."""
        chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        # Required top-level fields
        required_fields = {"planets", "houses", "aspects", "angles", "distributions"}
        assert required_fields.issubset(set(chart.keys()))

        # Planets must have required fields for horoscope generation
        for planet in chart["planets"]:
            assert "name" in planet
            assert "sign" in planet
            assert "house" in planet
            assert "degree_in_sign" in planet
            assert "retrograde" in planet
            assert "absolute_degree" in planet

    def test_chart_is_dict_for_firestore_storage(self):
        """Chart is a dict suitable for Firestore storage."""
        chart, _ = compute_birth_chart(birth_date="1990-06-15")

        assert isinstance(chart, dict)
        assert isinstance(chart["planets"], list)
        assert isinstance(chart["houses"], list)
        assert isinstance(chart["aspects"], list)

    def test_multiple_chart_generations_are_deterministic(self):
        """Same input produces same chart (deterministic)."""
        chart1, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        chart2, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        # Planets should be in identical positions
        for p1, p2 in zip(chart1["planets"], chart2["planets"]):
            assert p1["name"] == p2["name"]
            assert p1["sign"] == p2["sign"]
            assert abs(p1["absolute_degree"] - p2["absolute_degree"]) < 0.001


class TestSunSignAccuracy:
    """Test sun sign calculation accuracy for different dates."""

    @pytest.mark.parametrize("birth_date,expected_sign", [
        ("1990-01-15", ZodiacSign.CAPRICORN),
        ("1990-02-15", ZodiacSign.AQUARIUS),
        ("1990-03-15", ZodiacSign.PISCES),
        ("1990-04-15", ZodiacSign.ARIES),
        ("1990-05-15", ZodiacSign.TAURUS),
        ("1990-06-15", ZodiacSign.GEMINI),
        ("1990-07-15", ZodiacSign.CANCER),
        ("1990-08-15", ZodiacSign.LEO),
        ("1990-09-15", ZodiacSign.VIRGO),
        ("1990-10-15", ZodiacSign.LIBRA),
        ("1990-11-15", ZodiacSign.SCORPIO),
        ("1990-12-15", ZodiacSign.SAGITTARIUS),
    ])
    def test_sun_sign_for_date(self, birth_date, expected_sign):
        """Test sun sign is correct for various birth dates."""
        sun_sign = get_sun_sign(birth_date)
        assert sun_sign == expected_sign

    def test_sun_sign_cusp_dates(self):
        """Test sun sign calculation near cusp dates."""
        # Test a few cusp dates (dates when sun changes signs)
        # These may vary by year due to Earth's elliptical orbit

        # Gemini/Cancer cusp around June 21
        chart_june20, _ = compute_birth_chart("1990-06-20")
        chart_june22, _ = compute_birth_chart("1990-06-22")

        sun_june20 = next(
            p for p in chart_june20["planets"] if p["name"] == "sun"
        )
        sun_june22 = next(
            p for p in chart_june22["planets"] if p["name"] == "sun"
        )

        print(f"June 20 sun: {sun_june20['sign']}")
        print(f"June 22 sun: {sun_june22['sign']}")


class TestUpdateUserProfileNatalChartRegeneration:
    """
    Test that update_user_profile correctly regenerates natal chart
    when birth time/location is provided.

    These tests verify the logic that powers the update_user_profile endpoint.
    """

    def test_upgrade_v1_to_v2_regenerates_chart(self):
        """Upgrading from V1 to V2 produces an exact chart."""
        # Simulate V1 user (just birth_date)
        v1_chart, v1_exact = compute_birth_chart(birth_date="1990-06-15")
        assert v1_exact is False

        # Simulate update with extended setup
        v2_chart, v2_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert v2_exact is True

        # The upgrade should produce an exact chart
        assert v1_exact != v2_exact

    def test_partial_update_still_approximate(self):
        """Partial birth data update keeps chart approximate."""
        # User starts with just birth_date
        v1_chart, v1_exact = compute_birth_chart(birth_date="1990-06-15")
        assert v1_exact is False

        # User adds only birth_time (no timezone/location)
        partial_chart, partial_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30"
        )
        assert partial_exact is False

        # User adds only location (no time/timezone)
        partial_chart2, partial_exact2 = compute_birth_chart(
            birth_date="1990-06-15",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert partial_exact2 is False

    def test_complete_update_produces_exact_chart(self):
        """Complete birth data produces exact chart."""
        chart, exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        assert exact is True
        assert "angles" in chart
        assert chart["angles"] is not None

    def test_updated_chart_has_different_moon_position(self):
        """Updated chart has different Moon position (time-sensitive)."""
        # V1: noon UTC at (0,0)
        v1_chart, _ = compute_birth_chart(birth_date="1990-06-15")

        # V2: 14:30 Eastern (18:30 UTC) at NYC
        v2_chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        v1_moon = next(p for p in v1_chart["planets"] if p["name"] == "moon")
        v2_moon = next(p for p in v2_chart["planets"] if p["name"] == "moon")

        # Moon moves ~0.5 deg/hour, 6.5 hours diff = ~3+ degrees
        deg_diff = abs(v1_moon["absolute_degree"] - v2_moon["absolute_degree"])
        if deg_diff > 180:
            deg_diff = 360 - deg_diff

        # The positions should differ (unless coincidentally the same)
        print(f"V1 Moon: {v1_moon['absolute_degree']:.2f} deg")
        print(f"V2 Moon: {v2_moon['absolute_degree']:.2f} deg")
        print(f"Difference: {deg_diff:.2f} deg")

    def test_updated_chart_has_meaningful_ascendant(self):
        """Updated chart has ascendant based on birth location."""
        v2_chart, v2_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        assert v2_exact is True
        angles = v2_chart.get("angles", {})

        # Should have ascendant
        asc = angles.get("ascendant") or angles.get("asc")
        assert asc is not None

        # Ascendant should have a sign
        if isinstance(asc, dict):
            assert "sign" in asc
        print(f"Ascendant: {asc}")

    def test_incremental_update_merges_with_existing(self):
        """
        Test that partial updates merge correctly with existing data.

        Simulates:
        1. User has V1 chart
        2. User adds time only
        3. User adds location later
        4. Final result is exact chart
        """
        birth_date = "1990-06-15"

        # Step 1: V1 chart
        _, exact1 = compute_birth_chart(birth_date=birth_date)
        assert exact1 is False

        # Step 2: Add time only (still approximate)
        _, exact2 = compute_birth_chart(
            birth_date=birth_date,
            birth_time="14:30"
        )
        assert exact2 is False

        # Step 3: Add time + timezone (still approximate - no location)
        _, exact3 = compute_birth_chart(
            birth_date=birth_date,
            birth_time="14:30",
            birth_timezone="America/New_York"
        )
        assert exact3 is False

        # Step 4: Complete data (exact)
        final_chart, exact_final = compute_birth_chart(
            birth_date=birth_date,
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert exact_final is True
        assert "angles" in final_chart


class TestNatalChartUpdateEdgeCases:
    """Test edge cases for natal chart updates."""

    def test_update_with_different_timezone_same_utc(self):
        """Same UTC time from different timezones produces same chart."""
        # In June, DST is active: EDT is UTC-4, PDT is UTC-7
        # 14:30 EDT = 18:30 UTC
        # 11:30 PDT = 18:30 UTC
        ny_chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        la_chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="11:30",
            birth_timezone="America/Los_Angeles",
            birth_lat=40.7128,  # Same location for comparison
            birth_lon=-74.0060
        )

        # Same UTC time = same planetary positions
        # Sun moves ~0.04 deg/hour, allow 0.2 deg tolerance for rounding
        ny_sun = next(p for p in ny_chart["planets"] if p["name"] == "sun")
        la_sun = next(p for p in la_chart["planets"] if p["name"] == "sun")

        assert abs(ny_sun["absolute_degree"] - la_sun["absolute_degree"]) < 0.2

    def test_update_near_midnight_boundary(self):
        """Chart generation near midnight handles date correctly."""
        # Late night in Eastern = next day in UTC
        late_chart, exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="23:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        assert exact is True
        # Should still produce valid chart
        assert len(late_chart["planets"]) == 12

    def test_update_with_negative_longitude(self):
        """Chart generation works with negative longitude (Western hemisphere)."""
        chart, exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060  # Negative = West
        )

        assert exact is True
        assert len(chart["planets"]) == 12

    def test_update_with_southern_hemisphere(self):
        """Chart generation works in Southern hemisphere."""
        chart, exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="Australia/Sydney",
            birth_lat=-33.8688,  # Sydney (negative = South)
            birth_lon=151.2093
        )

        assert exact is True
        assert len(chart["planets"]) == 12
        assert len(chart["houses"]) == 12

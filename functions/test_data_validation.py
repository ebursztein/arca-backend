"""
Simple validation tests for sun signs and natal charts - verify actual data structure.
"""
import pytest
from astro import (
    get_sun_sign,
    get_sun_sign_profile,
    compute_birth_chart,
    ZodiacSign
)


class TestSunSignDataIntegrity:
    """Test that sun sign profile data is complete and valid."""

    def test_all_12_signs_have_profiles(self):
        """Verify all 12 zodiac signs have loadable profiles."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None
            assert profile.sign  # Has a sign value
        print("✓ All 12 sun sign profiles load successfully")

    def test_profile_has_core_fields(self):
        """Test that profile has all core required fields."""
        profile = get_sun_sign_profile(ZodiacSign.GEMINI)

        # Core identity
        assert profile.sign
        assert profile.element
        assert profile.modality
        assert profile.ruling_planet

        # Content
        assert profile.summary
        assert len(profile.summary) > 100

        # Traits
        assert profile.positive_traits
        assert len(profile.positive_traits) >= 3
        assert profile.shadow_traits
        assert len(profile.shadow_traits) >= 3

        # Domains
        assert profile.domain_profiles
        assert profile.domain_profiles.love_and_relationships
        assert profile.domain_profiles.path_and_profession

        print("✓ Profile has all core fields")

    def test_no_placeholder_text(self):
        """Verify profiles don't contain placeholder text."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            profile_json = profile.model_dump_json()

            assert "TBD" not in profile_json
            assert "TODO" not in profile_json
            assert "FIXME" not in profile_json
            assert "placeholder" not in profile_json.lower()

        print("✓ No placeholder text in any profile")


class TestNatalChartDataIntegrity:
    """Test that natal chart data is complete and valid."""

    def test_chart_has_all_components(self):
        """Verify chart has all required components."""
        chart, _ = compute_birth_chart("1990-06-15")

        assert "planets" in chart
        assert "houses" in chart
        assert "aspects" in chart
        assert "distributions" in chart

        print("✓ Chart has all components")

    def test_chart_has_11_celestial_bodies(self):
        """Verify chart contains all 11 planets."""
        chart, _ = compute_birth_chart("1990-06-15")

        # Planet names are enum objects, extract their values
        planet_names = {p["name"].value if hasattr(p["name"], 'value') else p["name"]
                       for p in chart["planets"]}

        # Should have 11 unique planet names
        assert len(planet_names) == 11

        # Check some key planets are present
        assert any('sun' in str(name).lower() for name in planet_names)
        assert any('moon' in str(name).lower() for name in planet_names)
        assert any('mercury' in str(name).lower() for name in planet_names)

        print(f"✓ Chart has all 11 celestial bodies")

    def test_chart_has_12_houses(self):
        """Verify chart contains all 12 houses."""
        chart, _ = compute_birth_chart("1990-06-15")

        house_numbers = {h["number"] for h in chart["houses"]}
        assert house_numbers == set(range(1, 13))

        print("✓ Chart has all 12 houses")

    def test_planets_have_valid_data(self):
        """Verify each planet has valid positional data."""
        chart, _ = compute_birth_chart("1990-06-15")

        for planet in chart["planets"]:
            # Has required keys
            assert "name" in planet
            assert "sign" in planet
            assert "house" in planet
            assert "degree_in_sign" in planet
            assert "absolute_degree" in planet
            assert "retrograde" in planet

            # Degrees in valid range
            assert 0 <= planet["degree_in_sign"] < 30
            assert 0 <= planet["absolute_degree"] < 360

            # House in valid range
            assert 1 <= planet["house"] <= 12

        print("✓ All planets have valid positional data")

    def test_aspects_have_valid_data(self):
        """Verify aspects have valid data."""
        chart, _ = compute_birth_chart("1990-06-15")

        assert len(chart["aspects"]) > 0, "Chart should have aspects"

        for aspect in chart["aspects"]:
            # Has required keys
            assert "body1" in aspect
            assert "body2" in aspect
            assert "aspect_type" in aspect
            assert "orb" in aspect
            assert "applying" in aspect

            # Orb in reasonable range
            assert 0 <= aspect["orb"] <= 10

        print(f"✓ {len(chart['aspects'])} aspects have valid data")

    def test_distributions_are_complete(self):
        """Verify distributions add up correctly."""
        chart, _ = compute_birth_chart("1990-06-15")

        dist = chart["distributions"]

        # Element distribution totals 11
        element_total = sum(dist["elements"].values())
        assert element_total == 11

        # Modality distribution totals 11
        modality_total = sum(dist["modalities"].values())
        assert modality_total == 11

        # Quadrant distribution totals 11
        quadrant_total = sum(dist["quadrants"].values())
        assert quadrant_total == 11

        print("✓ All distributions total 11 planets")

    def test_exact_vs_approximate_charts(self):
        """Verify exact vs approximate chart detection."""
        # Approximate (no birth time)
        chart1, is_exact1 = compute_birth_chart("1990-06-15")
        assert is_exact1 == False

        # Exact (full birth info)
        chart2, is_exact2 = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert is_exact2 == True

        print("✓ Exact vs approximate detection works")


class TestChartSerialization:
    """Test that charts can be serialized."""

    def test_chart_dict_is_valid(self):
        """Verify chart returns as valid dict."""
        chart, _ = compute_birth_chart("1990-06-15")

        assert isinstance(chart, dict)
        assert len(chart) > 0

        # Can access nested data
        assert len(chart["planets"]) > 0
        assert len(chart["houses"]) > 0

        print("✓ Chart is valid dict structure")

    def test_profile_serialization(self):
        """Verify profile can be serialized."""
        profile = get_sun_sign_profile(ZodiacSign.CAPRICORN)

        # Can convert to dict
        profile_dict = profile.model_dump()
        assert isinstance(profile_dict, dict)

        # Can convert to JSON
        profile_json = profile.model_dump_json()
        assert isinstance(profile_json, str)
        assert len(profile_json) > 1000

        print("✓ Profile serialization works")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_leap_year_date(self):
        """Test chart generation on leap year date."""
        chart, _ = compute_birth_chart("2024-02-29")
        assert len(chart["planets"]) == 11
        print("✓ Leap year date works")

    def test_very_old_date(self):
        """Test chart generation for very old date."""
        chart, _ = compute_birth_chart("1900-01-01")
        assert len(chart["planets"]) == 11
        print("✓ Very old date works")

    def test_future_date(self):
        """Test chart generation for future date."""
        chart, _ = compute_birth_chart("2050-12-31")
        assert len(chart["planets"]) == 11
        print("✓ Future date works")

    def test_different_coordinates(self):
        """Test charts with different coordinates."""
        # New York
        chart_ny, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        # Los Angeles
        chart_la, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/Los_Angeles",
            birth_lat=34.0522,
            birth_lon=-118.2437
        )

        # Both should work
        assert len(chart_ny["planets"]) == 11
        assert len(chart_la["planets"]) == 11

        print("✓ Different geographic locations work")

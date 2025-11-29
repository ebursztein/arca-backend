"""
Comprehensive tests for natal chart generation and validation.
"""
import pytest
from astro import (
    compute_birth_chart,
    get_astro_chart,
    ChartType,
    ZodiacSign,
    Planet,
    AspectType,
    Element,
    Modality,
    House,
    CelestialBody
)


class TestNatalChartGeneration:
    """Test natal chart computation."""

    def test_approximate_chart_structure(self):
        """Test approximate chart (no birth time) has all required components."""
        chart, is_exact = compute_birth_chart("1990-06-15")

        assert is_exact == False
        assert "planets" in chart
        assert "houses" in chart
        assert "aspects" in chart
        assert "distributions" in chart

        print(f"Approximate chart has all components")
        print(f"  Planets: {len(chart['planets'])}")
        print(f"  Houses: {len(chart['houses'])}")
        print(f"  Aspects: {len(chart['aspects'])}")

    def test_exact_chart_structure(self):
        """Test exact chart (with birth time) has all required components."""
        chart, is_exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        assert is_exact == True
        assert "planets" in chart
        assert "houses" in chart
        assert "aspects" in chart
        assert "angles" in chart
        assert "distributions" in chart

        print(f"Exact chart has all components")

    def test_chart_has_11_planets(self):
        """Test that chart contains all 11 celestial bodies."""
        chart, _ = compute_birth_chart("1987-06-02")

        # Planet names are now Planet enums
        planet_names = {p["name"] for p in chart["planets"]}
        expected_planets = {
            Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS, Planet.MARS,
            Planet.JUPITER, Planet.SATURN, Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO,
            Planet.NORTH_NODE
        }

        assert planet_names == expected_planets
        print(f"Chart has all 11 celestial bodies")

    def test_chart_has_12_houses(self):
        """Test that chart contains all 12 houses."""
        chart, _ = compute_birth_chart("1987-06-02")

        house_numbers = {h["number"] for h in chart["houses"]}
        expected_houses = set(range(1, 13))

        assert house_numbers == expected_houses
        print(f"Chart has all 12 houses")

    def test_planets_have_required_fields(self):
        """Test that each planet has all required fields."""
        chart, _ = compute_birth_chart("1987-06-02")

        required_fields = {
            "name", "sign", "house", "degree_in_sign", "retrograde",
            "element", "modality", "absolute_degree"
        }

        valid_planets = {
            "sun", "moon", "mercury", "venus", "mars", "jupiter",
            "saturn", "uranus", "neptune", "pluto", "north node"
        }
        valid_signs = {
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        }
        valid_elements = {"fire", "earth", "air", "water"}
        valid_modalities = {"cardinal", "fixed", "mutable"}

        for planet in chart["planets"]:
            planet_fields = set(planet.keys())
            missing = required_fields - planet_fields
            assert not missing, f"Missing fields: {missing}"
            # Validate types - now strings (JSON serialized for Firestore)
            assert isinstance(planet["name"], str)
            assert planet["name"] in valid_planets
            assert isinstance(planet["sign"], str)
            assert planet["sign"] in valid_signs
            assert isinstance(planet["house"], int)
            assert isinstance(planet["degree_in_sign"], (int, float))
            assert isinstance(planet["retrograde"], bool)
            assert isinstance(planet["element"], str)
            assert planet["element"] in valid_elements
            assert isinstance(planet["modality"], str)
            assert planet["modality"] in valid_modalities

        print(f"All planets have required fields with correct types")

    def test_houses_have_required_fields(self):
        """Test that each house has all required fields."""
        chart, _ = compute_birth_chart("1987-06-02")

        required_fields = {
            "number", "sign", "ruler", "classic_ruler"
        }
        valid_signs = {
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        }

        for house in chart["houses"]:
            house_fields = set(house.keys())
            assert required_fields.issubset(house_fields)
            # Validate types - now strings (JSON serialized)
            assert isinstance(house["number"], int)
            assert 1 <= house["number"] <= 12
            assert isinstance(house["sign"], str)
            assert house["sign"] in valid_signs

        print(f"All houses have required fields")

    def test_aspects_have_required_fields(self):
        """Test that each aspect has all required fields."""
        chart, _ = compute_birth_chart("1987-06-02")

        required_fields = {
            "body1", "body2", "aspect_type", "orb", "applying"
        }
        valid_aspect_types = {
            "conjunction", "opposition", "trine", "square", "sextile",
            "quincunx", "semisextile", "semisquare", "sesquiquadrate"
        }

        for aspect in chart["aspects"]:
            aspect_fields = set(aspect.keys())
            missing = required_fields - aspect_fields
            assert not missing, f"Missing fields: {missing}. Got: {aspect_fields}"
            # body1/body2 are now strings (JSON serialized)
            assert isinstance(aspect["body1"], str)
            assert isinstance(aspect["body2"], str)
            assert isinstance(aspect["aspect_type"], str)
            assert aspect["aspect_type"] in valid_aspect_types
            assert isinstance(aspect["orb"], float)
            assert isinstance(aspect["applying"], bool)
            # Validate orb is reasonable
            assert 0 <= aspect["orb"] <= 10

        print(f"All aspects have required fields")


class TestNatalChartDistributions:
    """Test chart distribution calculations."""

    def test_element_distribution(self):
        """Test element distribution is calculated correctly."""
        chart, _ = compute_birth_chart("1987-06-02")

        distributions = chart["distributions"]
        assert "elements" in distributions

        element_dist = distributions["elements"]
        # Keys are strings: fire, earth, air, water
        keys = set(element_dist.keys())
        expected_keys = {"fire", "earth", "air", "water"}

        assert keys == expected_keys

        # Total should equal number of planets (11)
        total = sum(element_dist.values())
        assert total == 11

        print(f"Element distribution: {element_dist}")

    def test_modality_distribution(self):
        """Test modality distribution is calculated correctly."""
        chart, _ = compute_birth_chart("1987-06-02")

        distributions = chart["distributions"]
        assert "modalities" in distributions

        modality_dist = distributions["modalities"]
        # Keys are strings: cardinal, fixed, mutable
        keys = set(modality_dist.keys())
        expected_keys = {"cardinal", "fixed", "mutable"}

        assert keys == expected_keys

        # Total should equal number of planets (11)
        total = sum(modality_dist.values())
        assert total == 11

        print(f"Modality distribution: {modality_dist}")

    def test_quadrant_distribution(self):
        """Test quadrant distribution is calculated correctly."""
        chart, _ = compute_birth_chart("1987-06-02")

        distributions = chart["distributions"]
        assert "quadrants" in distributions

        quadrant_dist = distributions["quadrants"]
        # Keys are: first, second, third, fourth
        expected_keys = {"first", "second", "third", "fourth"}
        assert set(quadrant_dist.keys()) == expected_keys

        # Total should equal number of planets (11)
        total = sum(quadrant_dist.values())
        assert total == 11

        print(f"Quadrant distribution: {quadrant_dist}")

    def test_hemisphere_distribution(self):
        """Test hemisphere distribution is calculated correctly."""
        chart, _ = compute_birth_chart("1987-06-02")

        distributions = chart["distributions"]
        assert "hemispheres" in distributions

        hemisphere_dist = distributions["hemispheres"]
        # Keys are: northern, southern, eastern, western
        expected_keys = {"northern", "southern", "eastern", "western"}
        assert set(hemisphere_dist.keys()) == expected_keys

        print(f"Hemisphere distribution: {hemisphere_dist}")


class TestChartAngles:
    """Test chart angle calculations."""

    def test_exact_chart_has_angles(self):
        """Test that exact chart includes angles."""
        chart, is_exact = compute_birth_chart(
            birth_date="1987-06-02",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        assert is_exact == True
        assert "angles" in chart
        assert chart["angles"] is not None

        angles = chart["angles"]
        # Angles might be nested or flat
        if hasattr(angles, 'ascendant'):
            assert angles.ascendant is not None
            assert angles.midheaven is not None
        else:
            assert "ascendant" in angles or "asc" in angles

        print(f"Exact chart has angles")

    def test_approximate_chart_still_has_angles(self):
        """Test that approximate chart still has angles (based on noon UTC at 0,0).

        Note: Even approximate charts have angles calculated based on the
        default time (noon UTC) and location (0,0). These angles are NOT
        meaningful for the user's actual birth chart but are included for
        consistency. The is_exact flag should be used to determine whether
        angles are reliable.
        """
        chart, is_exact = compute_birth_chart("1987-06-02")

        assert is_exact == False
        # Approximate charts still have angles (calculated at noon UTC, 0,0)
        # but the is_exact flag indicates they are not reliable
        assert "angles" in chart
        angles = chart["angles"]
        assert isinstance(angles, dict)
        assert "ascendant" in angles or "asc" in angles

        print(f"Approximate chart has angles (but is_exact={is_exact})")


class TestTransitCharts:
    """Test transit chart generation."""

    def test_transit_chart_generation(self):
        """Test generating transit chart for current date."""
        chart, _ = compute_birth_chart(
            birth_date="2025-11-06",
            birth_time="12:00"
        )

        # Should have all planets
        assert len(chart["planets"]) == 11

        # Transits use noon UTC at 0,0 coordinates
        print(f"Transit chart generated successfully")

    def test_transit_chart_different_dates(self):
        """Test transit charts for different dates are different."""
        chart1, _ = compute_birth_chart("2025-01-01", birth_time="12:00")
        chart2, _ = compute_birth_chart("2025-06-01", birth_time="12:00")

        # Planets should be in different positions
        sun1 = next(p for p in chart1["planets"] if p["name"] == "sun")
        sun2 = next(p for p in chart2["planets"] if p["name"] == "sun")

        assert sun1["sign"] != sun2["sign"]
        print(f"Transit charts vary by date")


class TestRetrogrades:
    """Test retrograde detection."""

    def test_retrograde_flag_exists(self):
        """Test that retrograde flag is present for all planets."""
        chart, _ = compute_birth_chart("1987-06-02")

        for planet in chart["planets"]:
            assert "retrograde" in planet
            assert isinstance(planet["retrograde"], bool)

        print(f"Retrograde flag present for all planets")

    def test_some_planets_can_be_retrograde(self):
        """Test that at least some planets can be retrograde."""
        # Test multiple dates to find retrogrades
        dates_to_test = [
            "2024-01-15",
            "2024-04-15",
            "2024-07-15",
            "2024-10-15"
        ]

        retrograde_found = False
        for date in dates_to_test:
            chart, _ = compute_birth_chart(date)
            for planet in chart["planets"]:
                if planet["retrograde"]:
                    retrograde_found = True
                    print(f"Found {planet['name']} retrograde on {date}")
                    break
            if retrograde_found:
                break

        assert retrograde_found, "No retrogrades found in test dates"


class TestPlanetDegrees:
    """Test planet degree calculations."""

    def test_absolute_degrees_in_range(self):
        """Test that absolute degrees are in valid range."""
        chart, _ = compute_birth_chart("1987-06-02")

        for planet in chart["planets"]:
            assert 0 <= planet["absolute_degree"] < 360
            print(f"{planet['name']}: {planet['absolute_degree']:.2f} deg")

    def test_degree_within_sign_in_range(self):
        """Test that degree within sign is in valid range."""
        chart, _ = compute_birth_chart("1987-06-02")

        for planet in chart["planets"]:
            degree = planet.get("degree_in_sign", planet.get("degree", 0))
            assert 0 <= degree < 30
            print(f"{planet['name']} at {degree:.2f} deg {planet['sign']}")


class TestAspectValidation:
    """Test aspect calculations."""

    def test_aspects_include_major_types(self):
        """Test that aspects include major types."""
        chart, _ = compute_birth_chart("1987-06-02")

        aspect_types = {a["aspect_type"] for a in chart["aspects"]}

        # Should have at least some of the major aspects (now strings)
        major_aspects = {
            "conjunction",
            "opposition",
            "trine",
            "square",
            "sextile"
        }

        # Should have at least 3 of the 5 major aspects
        found_major = aspect_types.intersection(major_aspects)
        assert len(found_major) >= 3

        print(f"Found aspect types: {list(found_major)}")

    def test_no_duplicate_aspects(self):
        """Test that there are no duplicate aspects."""
        chart, _ = compute_birth_chart("1987-06-02")

        aspect_pairs = set()
        for aspect in chart["aspects"]:
            # body1/body2 are now strings
            b1 = aspect["body1"]
            b2 = aspect["body2"]
            # Create normalized pair (order doesn't matter)
            pair = tuple(sorted([b1, b2]))
            aspect_type = aspect["aspect_type"]
            key = (pair, aspect_type)

            assert key not in aspect_pairs, f"Duplicate aspect: {key}"
            aspect_pairs.add(key)

        print(f"No duplicate aspects found ({len(aspect_pairs)} unique)")

    def test_aspects_between_valid_planets(self):
        """Test that aspects are between valid planets."""
        chart, _ = compute_birth_chart("1987-06-02")

        # Get all valid bodies (planets + angles) - now strings
        valid_planets = {p["name"] for p in chart["planets"]}
        # Add angles for exact charts (abbreviated names)
        valid_bodies = valid_planets | {
            "asc", "mc", "dsc", "ic",
            "ascendant", "midheaven", "descendant", "imum_coeli"
        }

        for aspect in chart["aspects"]:
            b1 = aspect["body1"]
            b2 = aspect["body2"]
            # Bodies are now strings
            assert b1 in valid_bodies, f"Invalid body1: {b1}"
            assert b2 in valid_bodies, f"Invalid body2: {b2}"

        print(f"All aspects between valid bodies")


class TestChartEdgeCases:
    """Test edge cases and error handling."""

    def test_partial_birth_info_is_approximate(self):
        """Test that partial birth info results in approximate chart."""
        # Only birth time, no timezone
        chart1, is_exact1 = compute_birth_chart(
            birth_date="1987-06-02",
            birth_time="14:30"
        )
        assert is_exact1 == False

        # Only timezone, no time
        chart2, is_exact2 = compute_birth_chart(
            birth_date="1987-06-02",
            birth_timezone="America/New_York"
        )
        assert is_exact2 == False

        # Only coordinates, no time
        chart3, is_exact3 = compute_birth_chart(
            birth_date="1987-06-02",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert is_exact3 == False

        print(f"Partial info correctly results in approximate charts")

    def test_different_timezones(self):
        """Test charts with different timezones."""
        # Same time, different timezones
        chart_ny, _ = compute_birth_chart(
            birth_date="1987-06-02",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        chart_la, _ = compute_birth_chart(
            birth_date="1987-06-02",
            birth_time="11:30",  # 3 hours earlier
            birth_timezone="America/Los_Angeles",
            birth_lat=34.0522,
            birth_lon=-118.2437
        )

        # Should result in similar but not identical charts
        # (same UTC time, different locations)
        print(f"Different timezone charts generated")

    def test_leap_year_date(self):
        """Test chart generation on leap year date."""
        chart, _ = compute_birth_chart("2024-02-29")

        assert len(chart["planets"]) == 11
        print(f"Leap year date works")

    def test_very_old_date(self):
        """Test chart generation for very old date."""
        chart, _ = compute_birth_chart("1900-01-01")

        assert len(chart["planets"]) == 11
        print(f"Very old date works")

    def test_future_date(self):
        """Test chart generation for future date."""
        chart, _ = compute_birth_chart("2050-12-31")

        assert len(chart["planets"]) == 11
        print(f"Future date works")


class TestGetAstroChartFunction:
    """Test the lower-level get_astro_chart function."""

    def test_natal_chart_type(self):
        """Test generating natal chart with ChartType enum."""
        chart_data = get_astro_chart(
            utc_dt="1987-06-02 18:30",  # natal library expects "YYYY-MM-DD HH:MM" format
            lat=40.7128,
            lon=-74.0060,
            chart_type=ChartType.NATAL
        )

        assert chart_data.chart_type == ChartType.NATAL
        assert len(chart_data.planets) == 11
        assert len(chart_data.houses) == 12

        print(f"get_astro_chart with NATAL type works")

    def test_transit_chart_type(self):
        """Test generating transit chart with ChartType enum."""
        chart_data = get_astro_chart(
            utc_dt="2025-11-06 12:00",  # natal library expects "YYYY-MM-DD HH:MM" format
            lat=0.0,
            lon=0.0,
            chart_type=ChartType.TRANSIT
        )

        assert chart_data.chart_type == ChartType.TRANSIT
        assert len(chart_data.planets) == 11

        print(f"get_astro_chart with TRANSIT type works")


class TestChartSerialization:
    """Test chart data serialization."""

    def test_chart_is_json_serializable(self):
        """Test that chart can be serialized to JSON."""
        import json

        chart, _ = compute_birth_chart("1987-06-02")

        # Convert enums to strings for JSON
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif hasattr(obj, 'value'):  # Enum
                return obj.value
            return obj

        chart_serializable = convert_enums(chart)
        json_str = json.dumps(chart_serializable)

        assert isinstance(json_str, str)
        assert len(json_str) > 1000

        print(f"Chart is JSON serializable ({len(json_str)} bytes)")

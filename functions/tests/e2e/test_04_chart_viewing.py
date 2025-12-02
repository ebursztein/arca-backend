"""
E2E Tests for Journey 4: Chart Viewing.

Tests the ACTUAL Cloud Functions via Firebase emulator:
- natal_chart: Generate natal chart with planets, houses, aspects
- daily_transit: Get daily transit chart
- user_transit: Get user-specific transit chart
- get_natal_chart_for_connection: Get chart for a connection

NO MOCKS. Real HTTP calls to emulator. Real astronomical calculations.
"""
import pytest

from .conftest import call_function


class TestNatalChartFunction:
    """E2E tests for natal_chart Cloud Function."""

    def test_returns_valid_structure(self):
        """Test natal chart has all required fields."""
        result = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        assert "planets" in result
        assert "houses" in result
        assert "aspects" in result
        assert "angles" in result
        assert "chart_type" in result

    def test_has_11_planets(self):
        """Test chart includes all 11 planets."""
        result = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        assert len(result["planets"]) == 12

        planet_names = {p["name"] for p in result["planets"]}
        expected = {"sun", "moon", "mercury", "venus", "mars",
                    "jupiter", "saturn", "uranus", "neptune", "pluto", "north node", "south node"}
        assert planet_names == expected

    def test_has_12_houses(self):
        """Test chart includes all 12 houses."""
        result = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        assert len(result["houses"]) == 12

        house_numbers = {h["number"] for h in result["houses"]}
        assert house_numbers == set(range(1, 13))

    def test_has_angles(self):
        """Test chart includes angles (ascendant, midheaven, etc.)."""
        result = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        assert "angles" in result
        assert "ascendant" in result["angles"]
        assert "midheaven" in result["angles"]
        assert "descendant" in result["angles"]
        assert "imum_coeli" in result["angles"]

    def test_planet_has_required_fields(self):
        """Test each planet has required position data."""
        result = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        for planet in result["planets"]:
            assert "name" in planet
            assert "sign" in planet
            assert "absolute_degree" in planet
            assert "degree_in_sign" in planet
            assert "house" in planet

    def test_aspect_has_required_fields(self):
        """Test each aspect has required data."""
        result = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        # Should have at least some aspects
        assert len(result["aspects"]) > 0

        for aspect in result["aspects"]:
            assert "body1" in aspect
            assert "body2" in aspect
            assert "aspect_type" in aspect
            assert "orb" in aspect

    def test_different_dates_different_positions(self):
        """Test different dates produce different planetary positions."""
        chart1 = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        chart2 = call_function("natal_chart", {
            "utc_dt": "1995-01-20 10:00",
            "lat": 40.7128,
            "lon": -74.0060
        })

        sun1 = next(p for p in chart1["planets"] if p["name"] == "sun")
        sun2 = next(p for p in chart2["planets"] if p["name"] == "sun")

        assert sun1["sign"] != sun2["sign"] or sun1["absolute_degree"] != sun2["absolute_degree"]

    def test_different_locations_different_houses(self):
        """Test different locations produce different house positions."""
        chart_ny = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        chart_la = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 34.0522,
            "lon": -118.2437
        })

        # Ascendants should differ
        asc_ny = chart_ny["angles"]["ascendant"]["absolute_degree"]
        asc_la = chart_la["angles"]["ascendant"]["absolute_degree"]

        assert abs(asc_ny - asc_la) > 0.1


class TestDailyTransitFunction:
    """E2E tests for daily_transit Cloud Function."""

    def test_returns_valid_structure(self):
        """Test daily transit has required fields."""
        result = call_function("daily_transit", {})

        assert "planets" in result
        assert "aspects" in result
        assert len(result["planets"]) == 11

    def test_specific_date(self):
        """Test requesting specific date."""
        result = call_function("daily_transit", {
            "utc_dt": "2025-06-21 00:00"  # Summer solstice
        })

        sun = next(p for p in result["planets"] if p["name"] == "sun")
        # Around summer solstice, Sun should be in late Gemini or early Cancer
        assert sun["sign"] in ["gemini", "cancer"]


class TestUserTransitFunction:
    """E2E tests for user_transit Cloud Function."""

    def test_returns_valid_structure(self):
        """Test user transit has required fields."""
        result = call_function("user_transit", {
            "birth_lat": 40.7128,
            "birth_lon": -74.0060
        })

        assert "planets" in result
        assert "houses" in result
        assert "aspects" in result
        assert len(result["planets"]) == 11

    def test_houses_relative_to_birth_location(self):
        """Test houses are computed relative to birth location."""
        result_ny = call_function("user_transit", {
            "birth_lat": 40.7128,
            "birth_lon": -74.0060
        })

        result_tokyo = call_function("user_transit", {
            "birth_lat": 35.6762,
            "birth_lon": 139.6503
        })

        # Houses should differ based on location
        house1_ny = result_ny["houses"][0]["absolute_degree"]
        house1_tokyo = result_tokyo["houses"][0]["absolute_degree"]

        assert abs(house1_ny - house1_tokyo) > 0.1


class TestGetNatalChartForConnection:
    """E2E tests for get_natal_chart_for_connection Cloud Function."""

    @pytest.mark.llm
    def test_returns_connection_chart(self, test_user_id, test_connection_id):
        """Test getting natal chart for a connection."""
        # First create user profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Create a connection
        call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "John",
                "birth_date": "1992-08-15",
                "relationship_category": "friend",
                "relationship_label": "friend",
            }
        })

        # Get connections to find connection_id
        connections = call_function("list_connections", {"user_id": test_user_id})

        if connections["connections"]:
            conn_id = connections["connections"][0]["connection_id"]

            # Get natal chart for connection
            result = call_function("get_natal_chart_for_connection", {
                "user_id": test_user_id,
                "connection_id": conn_id,
            })

            assert "chart" in result
            assert "planets" in result["chart"]
            assert len(result["chart"]["planets"]) == 11

    def test_missing_connection_raises_error(self, test_user_id):
        """Test getting chart for nonexistent connection raises error."""
        with pytest.raises(Exception):
            call_function("get_natal_chart_for_connection", {
                "user_id": test_user_id,
                "connection_id": "nonexistent_conn_xyz",
            })

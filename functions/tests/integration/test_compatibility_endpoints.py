"""
Tests for compatibility endpoint logic.

Tests the core logic used by Cloud Function endpoints without requiring
Firebase/Flask infrastructure.

Run with: pytest functions/test_compatibility_endpoints.py -v
"""

import pytest
import json
from datetime import datetime

from compatibility import (
    calculate_compatibility,
    calculate_synastry_aspects,
    CompatibilityResult,
)
from astro import compute_birth_chart, NatalChartData


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def user_natal_chart():
    """User's natal chart data (as stored in Firestore)."""
    chart_dict, _ = compute_birth_chart(
        birth_date="1990-06-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )
    return chart_dict


@pytest.fixture
def connection_birth_data():
    """Connection's birth data (as stored in Firestore)."""
    return {
        "birth_date": "1992-03-22",
        "birth_time": "09:15",
        "birth_timezone": "America/Los_Angeles",
        "birth_lat": 34.0522,
        "birth_lon": -118.2437,
    }


@pytest.fixture
def connection_birth_data_no_time():
    """Connection without birth time."""
    return {
        "birth_date": "1988-08-15",
        "birth_time": None,
        "birth_timezone": None,
        "birth_lat": None,
        "birth_lon": None,
    }


# =============================================================================
# Test get_synastry_chart Logic
# =============================================================================

class TestSynastryChartLogic:
    """Tests for synastry chart endpoint logic."""

    def test_can_build_user_chart_from_stored_data(self, user_natal_chart):
        """Should be able to reconstruct user chart from stored dict."""
        user_chart = NatalChartData(**user_natal_chart)
        assert user_chart.planets is not None
        assert len(user_chart.planets) > 0

    def test_can_build_connection_chart_from_birth_data(self, connection_birth_data):
        """Should be able to compute connection chart from birth data."""
        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)
        assert conn_chart.planets is not None
        assert len(conn_chart.planets) > 0

    def test_can_build_connection_chart_without_birth_time(self, connection_birth_data_no_time):
        """Should be able to compute chart without birth time."""
        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data_no_time["birth_date"],
            birth_time=connection_birth_data_no_time["birth_time"],
            birth_timezone=connection_birth_data_no_time["birth_timezone"],
            birth_lat=connection_birth_data_no_time["birth_lat"],
            birth_lon=connection_birth_data_no_time["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)
        assert conn_chart.planets is not None

    def test_synastry_response_structure(self, user_natal_chart, connection_birth_data):
        """Synastry endpoint response should have correct structure."""
        # Simulate endpoint logic
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        synastry_aspects = calculate_synastry_aspects(user_chart, conn_chart)

        # Build response like endpoint does
        response = {
            "user_chart": user_chart.model_dump(),
            "connection_chart": conn_chart.model_dump(),
            "synastry_aspects": [a.model_dump() for a in synastry_aspects]
        }

        # Verify structure
        assert "user_chart" in response
        assert "connection_chart" in response
        assert "synastry_aspects" in response

        # Verify user_chart has planets
        assert "planets" in response["user_chart"]
        assert len(response["user_chart"]["planets"]) > 0

        # Verify connection_chart has planets
        assert "planets" in response["connection_chart"]
        assert len(response["connection_chart"]["planets"]) > 0

        # Verify synastry_aspects
        assert isinstance(response["synastry_aspects"], list)
        if response["synastry_aspects"]:
            aspect = response["synastry_aspects"][0]
            assert "id" in aspect
            assert "user_planet" in aspect
            assert "their_planet" in aspect
            assert "aspect_type" in aspect
            assert "orb" in aspect
            assert "is_harmonious" in aspect

    def test_synastry_response_is_json_serializable(self, user_natal_chart, connection_birth_data):
        """Response should be JSON serializable."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        synastry_aspects = calculate_synastry_aspects(user_chart, conn_chart)

        response = {
            "user_chart": user_chart.model_dump(),
            "connection_chart": conn_chart.model_dump(),
            "synastry_aspects": [a.model_dump() for a in synastry_aspects]
        }

        # Should not raise
        json_str = json.dumps(response)
        assert json_str is not None

        # Should be parseable back
        parsed = json.loads(json_str)
        assert parsed["user_chart"] is not None


# =============================================================================
# Test get_compatibility Logic
# =============================================================================

class TestCompatibilityLogic:
    """Tests for compatibility endpoint logic."""

    def test_compatibility_response_structure(self, user_natal_chart, connection_birth_data):
        """Compatibility endpoint response should have correct structure."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        # Verify all modes present
        assert "romantic" in response
        assert "friendship" in response
        assert "coworker" in response

        # Verify each mode has required fields
        for mode in ["romantic", "friendship", "coworker"]:
            assert "overall_score" in response[mode]
            assert 0 <= response[mode]["overall_score"] <= 100
            assert "categories" in response[mode]
            assert isinstance(response[mode]["categories"], list)

        # Verify aspects
        assert "aspects" in response
        assert isinstance(response["aspects"], list)

        # Verify composite_summary
        assert "composite_summary" in response
        assert "composite_sun" in response["composite_summary"]
        assert "composite_moon" in response["composite_summary"]

        # Verify timestamp
        assert "calculated_at" in response
        datetime.fromisoformat(response["calculated_at"])

    def test_romantic_has_six_categories(self, user_natal_chart, connection_birth_data):
        """Romantic mode should have 6 categories."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        assert len(response["romantic"]["categories"]) == 6

        expected_ids = {"emotional", "communication", "attraction", "values", "longTerm", "growth"}
        actual_ids = {c["id"] for c in response["romantic"]["categories"]}
        assert actual_ids == expected_ids

    def test_friendship_has_five_categories(self, user_natal_chart, connection_birth_data):
        """Friendship mode should have 5 categories."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        assert len(response["friendship"]["categories"]) == 5

        expected_ids = {"emotional", "communication", "fun", "loyalty", "sharedInterests"}
        actual_ids = {c["id"] for c in response["friendship"]["categories"]}
        assert actual_ids == expected_ids

    def test_coworker_has_five_categories(self, user_natal_chart, connection_birth_data):
        """Coworker mode should have 5 categories."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        assert len(response["coworker"]["categories"]) == 5

        expected_ids = {"communication", "collaboration", "reliability", "ambition", "powerDynamics"}
        actual_ids = {c["id"] for c in response["coworker"]["categories"]}
        assert actual_ids == expected_ids

    def test_category_fields(self, user_natal_chart, connection_birth_data):
        """Each category should have required fields."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        for cat in response["romantic"]["categories"]:
            assert "id" in cat
            assert "name" in cat
            assert "score" in cat
            assert "aspect_ids" in cat
            assert -100 <= cat["score"] <= 100

    def test_aspect_fields(self, user_natal_chart, connection_birth_data):
        """Each aspect should have required fields."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        valid_types = {"conjunction", "sextile", "square", "trine", "quincunx", "opposition"}

        for aspect in response["aspects"][:10]:  # Check first 10
            assert "id" in aspect
            assert aspect["id"].startswith("asp_")
            assert "user_planet" in aspect
            assert "their_planet" in aspect
            assert "aspect_type" in aspect
            assert aspect["aspect_type"] in valid_types
            assert "orb" in aspect
            assert aspect["orb"] >= 0
            assert "is_harmonious" in aspect
            assert isinstance(aspect["is_harmonious"], bool)

    def test_compatibility_is_json_serializable(self, user_natal_chart, connection_birth_data):
        """Response should be JSON serializable."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        # Should not raise
        json_str = json.dumps(response)
        assert len(json_str) > 0

        # Should be parseable back
        parsed = json.loads(json_str)
        assert parsed["romantic"]["overall_score"] == response["romantic"]["overall_score"]


# =============================================================================
# Test Interpretation Merging Logic
# =============================================================================

class TestInterpretationMerging:
    """Tests for merging LLM interpretations into response."""

    def test_merge_category_summaries(self, user_natal_chart, connection_birth_data):
        """Category summaries should merge correctly."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        # Mock interpretation with category summaries
        interpretation = {
            "category_summaries": {
                "emotional": "Strong emotional bond",
                "communication": "Easy conversation flow",
                "attraction": "Natural chemistry",
            }
        }

        # Apply merge logic (from main.py)
        category_summaries = interpretation.get("category_summaries", {})
        for mode_key in ["romantic", "friendship", "coworker"]:
            if mode_key in response:
                for cat in response[mode_key].get("categories", []):
                    cat_id = cat.get("id")
                    if cat_id and cat_id in category_summaries:
                        cat["summary"] = category_summaries[cat_id]

        # Verify merging
        emotional_cat = next(
            (c for c in response["romantic"]["categories"] if c["id"] == "emotional"),
            None
        )
        assert emotional_cat is not None
        assert emotional_cat["summary"] == "Strong emotional bond"

        # Categories not in interpretation should remain None
        growth_cat = next(
            (c for c in response["romantic"]["categories"] if c["id"] == "growth"),
            None
        )
        assert growth_cat is not None
        assert growth_cat.get("summary") is None

    def test_merge_aspect_interpretations(self, user_natal_chart, connection_birth_data):
        """Aspect interpretations should merge correctly."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        # Get first aspect ID for testing
        first_aspect_id = response["aspects"][0]["id"] if response["aspects"] else "asp_001"

        # Mock interpretation with aspect interpretations
        interpretation = {
            "aspect_interpretations": [
                {"aspect_id": first_aspect_id, "interpretation": "This aspect creates magic"},
            ]
        }

        # Apply merge logic (from main.py)
        aspect_interps = {
            ai.get("aspect_id"): ai.get("interpretation")
            for ai in interpretation.get("aspect_interpretations", [])
            if ai.get("aspect_id")
        }
        for aspect in response.get("aspects", []):
            asp_id = aspect.get("id")
            if asp_id and asp_id in aspect_interps:
                aspect["interpretation"] = aspect_interps[asp_id]

        # Verify merging
        first_aspect = response["aspects"][0] if response["aspects"] else None
        if first_aspect and first_aspect["id"] == first_aspect_id:
            assert first_aspect["interpretation"] == "This aspect creates magic"

    def test_empty_interpretation_doesnt_break_merging(self, user_natal_chart, connection_birth_data):
        """Empty interpretation should not cause errors."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        # Empty interpretation
        interpretation = {
            "category_summaries": {},
            "aspect_interpretations": []
        }

        # Apply merge logic - should not raise
        category_summaries = interpretation.get("category_summaries", {})
        for mode_key in ["romantic", "friendship", "coworker"]:
            if mode_key in response:
                for cat in response[mode_key].get("categories", []):
                    cat_id = cat.get("id")
                    if cat_id and cat_id in category_summaries:
                        cat["summary"] = category_summaries[cat_id]

        aspect_interps = {
            ai.get("aspect_id"): ai.get("interpretation")
            for ai in interpretation.get("aspect_interpretations", [])
            if ai.get("aspect_id")
        }
        for aspect in response.get("aspects", []):
            asp_id = aspect.get("id")
            if asp_id and asp_id in aspect_interps:
                aspect["interpretation"] = aspect_interps[asp_id]

        # Response should still be valid
        assert "romantic" in response
        assert len(response["romantic"]["categories"]) == 6


# =============================================================================
# Test Different Birth Data Scenarios
# =============================================================================

class TestBirthDataScenarios:
    """Tests for different birth data combinations."""

    def test_both_have_full_birth_data(self, user_natal_chart, connection_birth_data):
        """Both users with full birth data should work."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        assert 0 <= result.romantic.overall_score <= 100

    def test_connection_without_birth_time(self, user_natal_chart, connection_birth_data_no_time):
        """Connection without birth time should still work."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data_no_time["birth_date"],
            birth_time=connection_birth_data_no_time["birth_time"],
            birth_timezone=connection_birth_data_no_time["birth_timezone"],
            birth_lat=connection_birth_data_no_time["birth_lat"],
            birth_lon=connection_birth_data_no_time["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        assert 0 <= result.romantic.overall_score <= 100

    def test_very_old_birth_date(self, user_natal_chart):
        """Should handle old birth dates."""
        user_chart = NatalChartData(**user_natal_chart)

        old_chart_dict, _ = compute_birth_chart(birth_date="1920-05-15")
        old_chart = NatalChartData(**old_chart_dict)

        result = calculate_compatibility(user_chart, old_chart)
        assert 0 <= result.romantic.overall_score <= 100

    def test_recent_birth_date(self, user_natal_chart):
        """Should handle recent birth dates."""
        user_chart = NatalChartData(**user_natal_chart)

        recent_chart_dict, _ = compute_birth_chart(birth_date="2005-12-25")
        recent_chart = NatalChartData(**recent_chart_dict)

        result = calculate_compatibility(user_chart, recent_chart)
        assert 0 <= result.romantic.overall_score <= 100

    def test_same_birth_date(self, user_natal_chart):
        """Should handle two people with same birth date."""
        user_chart = NatalChartData(**user_natal_chart)

        # Same birth date, different time
        same_day_dict, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="22:00",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        same_day_chart = NatalChartData(**same_day_dict)

        result = calculate_compatibility(user_chart, same_day_chart)
        assert 0 <= result.romantic.overall_score <= 100

    def test_opposite_hemisphere_birth_locations(self, user_natal_chart):
        """Should handle birth locations in opposite hemispheres."""
        user_chart = NatalChartData(**user_natal_chart)

        # Sydney, Australia
        sydney_dict, _ = compute_birth_chart(
            birth_date="1990-03-15",
            birth_time="14:00",
            birth_timezone="Australia/Sydney",
            birth_lat=-33.8688,
            birth_lon=151.2093
        )
        sydney_chart = NatalChartData(**sydney_dict)

        result = calculate_compatibility(user_chart, sydney_chart)
        assert 0 <= result.romantic.overall_score <= 100


# =============================================================================
# Test Response Size
# =============================================================================

class TestResponseSize:
    """Tests for response size and performance."""

    def test_synastry_aspects_count(self, user_natal_chart, connection_birth_data):
        """Should have reasonable number of synastry aspects."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        aspects = calculate_synastry_aspects(user_chart, conn_chart)

        # Should have some aspects
        assert len(aspects) > 0

        # Should not be excessive (11 planets x 11 planets = 121 max possible)
        assert len(aspects) <= 121

    def test_response_json_size_reasonable(self, user_natal_chart, connection_birth_data):
        """Response JSON size should be reasonable for mobile."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        json_str = json.dumps(response)

        # Should be under 100KB for mobile performance
        assert len(json_str) < 100_000, f"Response too large: {len(json_str)} bytes"

    def test_synastry_chart_response_size_reasonable(self, user_natal_chart, connection_birth_data):
        """Synastry chart response size should be reasonable."""
        user_chart = NatalChartData(**user_natal_chart)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=connection_birth_data["birth_date"],
            birth_time=connection_birth_data["birth_time"],
            birth_timezone=connection_birth_data["birth_timezone"],
            birth_lat=connection_birth_data["birth_lat"],
            birth_lon=connection_birth_data["birth_lon"]
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        synastry_aspects = calculate_synastry_aspects(user_chart, conn_chart)

        response = {
            "user_chart": user_chart.model_dump(),
            "connection_chart": conn_chart.model_dump(),
            "synastry_aspects": [a.model_dump() for a in synastry_aspects]
        }

        json_str = json.dumps(response)

        # Should be under 150KB (two full charts + aspects)
        assert len(json_str) < 150_000, f"Response too large: {len(json_str)} bytes"

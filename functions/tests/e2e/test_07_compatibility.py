"""
E2E Tests for Journey 7: Compatibility.

Tests the ACTUAL Cloud Functions via Firebase emulator:
- get_compatibility: Calculate compatibility between user and connection

NO MOCKS. Real HTTP calls to emulator. Real calculations.

OPTIMIZATION: Uses module-scoped fixtures to cache LLM responses.
One create_user_profile call, one create_connection call, one get_compatibility call,
then multiple assertions on the same response.
"""
import pytest
import uuid

from .conftest import call_function


# ============================================================================
# MODULE-SCOPED FIXTURES (LLM calls cached for entire module)
# ============================================================================

@pytest.fixture(scope="module")
def compatibility_user_id():
    """Fixed user ID for compatibility tests (module-scoped)."""
    return "test_user_b"  # Dev account from DEV_ACCOUNT_UIDS


@pytest.fixture(scope="module")
def compatibility_user_profile(compatibility_user_id):
    """Create user profile once for all compatibility tests."""
    call_function("create_user_profile", {
        "user_id": compatibility_user_id,
        "name": "Test User",
        "email": f"{compatibility_user_id}@test.com",
        "birth_date": "1990-06-15",
        "birth_time": "14:30",
        "birth_timezone": "America/New_York",
        "birth_lat": 40.7128,
        "birth_lon": -74.0060,
    })
    return compatibility_user_id


@pytest.fixture(scope="module")
def compatibility_connection_id(compatibility_user_profile):
    """Create connection once for all compatibility tests."""
    conn_result = call_function("create_connection", {
        "user_id": compatibility_user_profile,
        "connection": {
            "name": "Partner",
            "birth_date": "1988-12-01",
            "birth_time": "10:00",
            "birth_timezone": "America/Los_Angeles",
            "birth_lat": 34.0522,
            "birth_lon": -118.2437,
            "relationship_category": "love",
            "relationship_label": "partner",
        }
    })
    return conn_result["connection_id"]


@pytest.fixture(scope="module")
def compatibility_response(compatibility_user_profile, compatibility_connection_id):
    """Fetch compatibility once for all tests in this module."""
    return call_function("get_compatibility", {
        "user_id": compatibility_user_profile,
        "connection_id": compatibility_connection_id,
    })


# ============================================================================
# COMPATIBILITY TESTS (all use cached compatibility_response)
# ============================================================================

class TestGetCompatibility:
    """E2E tests for get_compatibility Cloud Function."""

    @pytest.mark.llm
    def test_returns_valid_structure(self, compatibility_response):
        """Test get_compatibility returns expected structure."""
        assert "romantic" in compatibility_response
        assert "friendship" in compatibility_response
        assert "coworker" in compatibility_response
        assert "aspects" in compatibility_response

    @pytest.mark.llm
    def test_has_three_modes(self, compatibility_response):
        """Test compatibility has romantic, friendship, coworker modes."""
        # Each mode should have overall_score and categories
        for mode_name in ["romantic", "friendship", "coworker"]:
            mode = compatibility_response[mode_name]
            assert "overall_score" in mode
            assert "categories" in mode
            assert len(mode["categories"]) > 0

    @pytest.mark.llm
    def test_overall_scores_in_range(self, compatibility_response):
        """Test overall scores are in 0-100 range."""
        assert 0 <= compatibility_response["romantic"]["overall_score"] <= 100
        assert 0 <= compatibility_response["friendship"]["overall_score"] <= 100
        assert 0 <= compatibility_response["coworker"]["overall_score"] <= 100

    @pytest.mark.llm
    def test_romantic_has_expected_categories(self, compatibility_response):
        """Test romantic mode has expected category IDs."""
        category_ids = {c["id"] for c in compatibility_response["romantic"]["categories"]}
        expected = {"emotional", "communication", "attraction", "values", "longTerm", "growth"}
        assert category_ids == expected

    @pytest.mark.llm
    def test_has_synastry_aspects(self, compatibility_response):
        """Test compatibility includes synastry aspects."""
        assert "aspects" in compatibility_response
        # Should have at least some aspects between two charts
        assert len(compatibility_response["aspects"]) > 0

    @pytest.mark.llm
    def test_has_composite_summary(self, compatibility_response):
        """Test compatibility includes composite chart summary."""
        assert "composite_summary" in compatibility_response
        assert "composite_sun" in compatibility_response["composite_summary"]
        assert "composite_moon" in compatibility_response["composite_summary"]

    def test_missing_connection_raises_error(self, test_user_id):
        """Test get_compatibility with missing connection raises error."""
        with pytest.raises(Exception):
            call_function("get_compatibility", {
                "user_id": test_user_id,
                "connection_id": "nonexistent_conn_xyz",
            })

    def test_missing_user_raises_error(self):
        """Test get_compatibility with missing user raises error."""
        with pytest.raises(Exception):
            call_function("get_compatibility", {
                "user_id": "nonexistent_user_xyz",
                "connection_id": "some_conn",
            })

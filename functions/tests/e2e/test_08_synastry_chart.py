"""
E2E Tests for Journey 8: Synastry Chart.

Tests the ACTUAL Cloud Functions via Firebase emulator:
- get_synastry_chart: Get synastry chart overlay between user and connection

NO MOCKS. Real HTTP calls to emulator. Real calculations.

OPTIMIZATION: Uses module-scoped fixtures to cache responses.
One create_user_profile call, one create_connection call, one get_synastry_chart call,
then multiple assertions on the same response.
"""
import pytest
import uuid

from .conftest import call_function


# ============================================================================
# MODULE-SCOPED FIXTURES (calls cached for entire module)
# ============================================================================

@pytest.fixture(scope="module")
def synastry_user_id():
    """Fixed user ID for synastry tests (module-scoped)."""
    return "test_user_c"  # Dev account from DEV_ACCOUNT_UIDS


@pytest.fixture(scope="module")
def synastry_user_profile(synastry_user_id):
    """Create user profile once for all synastry tests."""
    call_function("create_user_profile", {
        "user_id": synastry_user_id,
        "name": "Test User",
        "email": f"{synastry_user_id}@test.com",
        "birth_date": "1990-06-15",
        "birth_time": "14:30",
        "birth_timezone": "America/New_York",
        "birth_lat": 40.7128,
        "birth_lon": -74.0060,
    })
    return synastry_user_id


@pytest.fixture(scope="module")
def synastry_connection_id(synastry_user_profile):
    """Create connection once for all synastry tests."""
    conn_result = call_function("create_connection", {
        "user_id": synastry_user_profile,
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
def synastry_response(synastry_user_profile, synastry_connection_id):
    """Fetch synastry chart once for all tests in this module."""
    return call_function("get_synastry_chart", {
        "user_id": synastry_user_profile,
        "connection_id": synastry_connection_id,
    })


# ============================================================================
# SYNASTRY CHART TESTS (all use cached synastry_response)
# ============================================================================

class TestGetSynastryChart:
    """E2E tests for get_synastry_chart Cloud Function."""

    @pytest.mark.llm
    def test_returns_valid_structure(self, synastry_response):
        """Test get_synastry_chart returns expected structure."""
        assert "user_chart" in synastry_response
        assert "connection_chart" in synastry_response
        assert "synastry_aspects" in synastry_response

    @pytest.mark.llm
    def test_user_chart_has_planets(self, synastry_response):
        """Test user chart has all planets."""
        assert "planets" in synastry_response["user_chart"]
        assert len(synastry_response["user_chart"]["planets"]) == 12  # 10 planets + North Node + South Node

    @pytest.mark.llm
    def test_connection_chart_has_planets(self, synastry_response):
        """Test connection chart has all planets."""
        assert "planets" in synastry_response["connection_chart"]
        assert len(synastry_response["connection_chart"]["planets"]) == 12  # 10 planets + North Node + South Node

    @pytest.mark.llm
    def test_synastry_aspects_exist(self, synastry_response):
        """Test synastry aspects are calculated between charts."""
        # Should have some aspects between the two charts
        assert len(synastry_response["synastry_aspects"]) > 0

    @pytest.mark.llm
    def test_synastry_aspect_has_required_fields(self, synastry_response):
        """Test each synastry aspect has required fields."""
        for aspect in synastry_response["synastry_aspects"]:
            assert "body1" in aspect or "planet1" in aspect or "user_planet" in aspect
            assert "body2" in aspect or "planet2" in aspect or "their_planet" in aspect
            assert "aspect_type" in aspect
            assert "orb" in aspect

    def test_missing_connection_raises_error(self, test_user_id):
        """Test get_synastry_chart with missing connection raises error."""
        with pytest.raises(Exception):
            call_function("get_synastry_chart", {
                "user_id": test_user_id,
                "connection_id": "nonexistent_conn_xyz",
            })

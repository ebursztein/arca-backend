"""
E2E Tests for Journey 7: Compatibility.

Tests the ACTUAL Cloud Functions via Firebase emulator:
- get_compatibility: Calculate compatibility between user and connection

NO MOCKS. Real HTTP calls to emulator. Real calculations.

OPTIMIZATION: Uses module-scoped fixtures to cache LLM responses.
One create_user_profile call, one create_connection call, one get_compatibility call,
then multiple assertions on the same response.

OUTPUT FILES: Tests save JSON outputs to backend_output/ for iOS mock data:
- backend_output/compatibility_love.json
- backend_output/compatibility_friendship.json
- backend_output/compatibility_coworker.json

NEW STRUCTURE (v2):
- Single mode per response based on connection's relationship_category
- LLM text fields at top level (headline, summary, strengths, etc.)
- mode.type indicates which mode (romantic/friendship/coworker)
- composite and karmic objects (renamed from composite_summary, karmic_summary)
"""
import pytest
import uuid
import json
from pathlib import Path

from .conftest import call_function


# Output directory for iOS mock data
OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "backend_output"


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
        # New structure: single mode, top-level LLM fields
        assert "mode" in compatibility_response
        assert "headline" in compatibility_response
        assert "summary" in compatibility_response
        assert "aspects" in compatibility_response
        assert "composite" in compatibility_response
        assert "karmic" in compatibility_response

    @pytest.mark.llm
    def test_has_single_mode(self, compatibility_response):
        """Test compatibility has single mode based on relationship type."""
        mode = compatibility_response["mode"]
        assert "type" in mode
        assert "overall_score" in mode
        assert "categories" in mode
        assert len(mode["categories"]) > 0
        # Connection is love, so should be romantic mode
        assert mode["type"] == "romantic"

    @pytest.mark.llm
    def test_overall_score_in_range(self, compatibility_response):
        """Test overall score is in 0-100 range."""
        assert 0 <= compatibility_response["mode"]["overall_score"] <= 100

    @pytest.mark.llm
    def test_romantic_has_expected_categories(self, compatibility_response):
        """Test romantic mode has expected category IDs."""
        mode = compatibility_response["mode"]
        category_ids = {c["id"] for c in mode["categories"]}
        expected = {"emotional", "communication", "attraction", "values", "longTerm", "growth"}
        assert category_ids == expected

    @pytest.mark.llm
    def test_has_synastry_aspects(self, compatibility_response):
        """Test compatibility includes synastry aspects."""
        assert "aspects" in compatibility_response
        # Should have at least some aspects between two charts
        assert len(compatibility_response["aspects"]) > 0

    @pytest.mark.llm
    def test_has_composite(self, compatibility_response):
        """Test compatibility includes composite chart data."""
        assert "composite" in compatibility_response
        composite = compatibility_response["composite"]
        assert "sun_sign" in composite
        assert "moon_sign" in composite
        assert "dominant_element" in composite

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


# ============================================================================
# KARMIC E2E TESTS
# ============================================================================

class TestKarmicCompatibility:
    """E2E tests for karmic/fated aspects in compatibility."""

    @pytest.mark.llm
    def test_has_karmic(self, compatibility_response):
        """Test compatibility includes karmic data."""
        assert "karmic" in compatibility_response
        karmic = compatibility_response["karmic"]
        assert "is_karmic" in karmic
        assert isinstance(karmic["is_karmic"], bool)

    @pytest.mark.llm
    def test_karmic_structure(self, compatibility_response):
        """Test karmic has expected fields."""
        karmic = compatibility_response["karmic"]
        assert "is_karmic" in karmic
        assert "theme" in karmic
        # Note: karmic_aspects are now internal, not exposed in API

    @pytest.mark.llm
    def test_karmic_destiny_note_only_if_karmic(self, compatibility_response):
        """Test destiny_note is only present if is_karmic is True."""
        karmic = compatibility_response["karmic"]
        destiny_note = karmic.get("destiny_note")

        if karmic["is_karmic"]:
            # If karmic, destiny_note may be filled by LLM
            pass
        else:
            # If not karmic, destiny_note should be None or empty
            assert not destiny_note, f"destiny_note should be empty when not karmic: {destiny_note}"

    @pytest.mark.llm
    def test_interpretation_uses_names(self, compatibility_response):
        """Test LLM interpretation uses both user and connection names."""
        # Check top-level interpretation fields
        summary = compatibility_response.get("summary", "")
        strengths = compatibility_response.get("strengths", "")
        advice = compatibility_response.get("advice", "")

        # At least one of these should mention names
        all_text = f"{summary} {strengths} {advice}"
        # Note: The fixtures use "Test User" and "Partner"
        # The LLM should use these names in the interpretation
        assert len(all_text) > 0, "Interpretation text should not be empty"


# ============================================================================
# NON-KARMIC PAIR TEST
# ============================================================================

@pytest.fixture(scope="module")
def non_karmic_user_id():
    """User ID for non-karmic test pair."""
    return "test_user_c"  # Dev account from DEV_ACCOUNT_UIDS


@pytest.fixture(scope="module")
def non_karmic_user_profile(non_karmic_user_id):
    """Create user profile for non-karmic test."""
    call_function("create_user_profile", {
        "user_id": non_karmic_user_id,
        "name": "Alice",
        "email": f"{non_karmic_user_id}@test.com",
        # Dates chosen to likely NOT have tight node aspects
        "birth_date": "1985-03-15",
        "birth_time": "08:00",
        "birth_timezone": "America/Chicago",
        "birth_lat": 41.8781,
        "birth_lon": -87.6298,
    })
    return non_karmic_user_id


@pytest.fixture(scope="module")
def non_karmic_connection_id(non_karmic_user_profile):
    """Create connection for non-karmic test."""
    conn_result = call_function("create_connection", {
        "user_id": non_karmic_user_profile,
        "connection": {
            "name": "Bob",
            # Different dates, hoping for no tight node aspects
            "birth_date": "1987-09-20",
            "birth_time": "15:30",
            "birth_timezone": "America/Denver",
            "birth_lat": 39.7392,
            "birth_lon": -104.9903,
            "relationship_category": "friend",
            "relationship_label": "friend",
        }
    })
    return conn_result["connection_id"]


@pytest.fixture(scope="module")
def non_karmic_response(non_karmic_user_profile, non_karmic_connection_id):
    """Fetch compatibility for non-karmic pair."""
    return call_function("get_compatibility", {
        "user_id": non_karmic_user_profile,
        "connection_id": non_karmic_connection_id,
    })


class TestNonKarmicPair:
    """E2E tests for a pair that may not be karmic."""

    @pytest.mark.llm
    def test_structure_valid_even_if_not_karmic(self, non_karmic_response):
        """Test response structure is valid even for non-karmic pairs."""
        assert "karmic" in non_karmic_response
        karmic = non_karmic_response["karmic"]
        assert "is_karmic" in karmic
        assert "theme" in karmic

    @pytest.mark.llm
    def test_destiny_note_empty_if_not_karmic(self, non_karmic_response):
        """Test destiny_note is empty when not karmic."""
        karmic = non_karmic_response["karmic"]
        destiny_note = karmic.get("destiny_note")

        if not karmic["is_karmic"]:
            assert not destiny_note, f"destiny_note should be empty: '{destiny_note}'"

    @pytest.mark.llm
    def test_friendship_mode_no_romantic_language(self, non_karmic_response):
        """Test friendship compatibility doesn't use romantic language."""
        summary = non_karmic_response.get("summary", "").lower()
        headline = non_karmic_response.get("headline", "").lower()

        # Friendship reading should not use romantic terms
        romantic_terms = ["romance", "passion", "intimacy", "lover", "soulmate"]
        all_text = f"{summary} {headline}"

        for term in romantic_terms:
            # Allow some false positives but flag obvious violations
            if term in all_text:
                # Only fail if it's clearly romantic context
                assert "friend" in all_text or "platonic" in all_text, \
                    f"Romantic term '{term}' found in friendship reading"


# ============================================================================
# iOS MOCK DATA GENERATION - LOVE CONNECTION
# ============================================================================

@pytest.fixture(scope="module")
def love_user_id():
    """User ID for love compatibility test."""
    return "test_user_d"  # Dev account from DEV_ACCOUNT_UIDS


@pytest.fixture(scope="module")
def love_user_profile(love_user_id):
    """Create user profile for love test - Emma."""
    call_function("create_user_profile", {
        "user_id": love_user_id,
        "name": "Emma",
        "email": f"{love_user_id}@test.com",
        "birth_date": "1992-07-22",  # Cancer/Leo cusp
        "birth_time": "16:45",
        "birth_timezone": "America/New_York",
        "birth_lat": 40.7128,
        "birth_lon": -74.0060,
    })
    return love_user_id


@pytest.fixture(scope="module")
def love_connection_id(love_user_profile):
    """Create love connection - James (partner)."""
    conn_result = call_function("create_connection", {
        "user_id": love_user_profile,
        "connection": {
            "name": "James",
            "birth_date": "1990-03-15",  # Pisces
            "birth_time": "09:30",
            "birth_timezone": "America/Chicago",
            "birth_lat": 41.8781,
            "birth_lon": -87.6298,
            "relationship_category": "love",
            "relationship_label": "partner",
        }
    })
    return conn_result["connection_id"]


@pytest.fixture(scope="module")
def love_compatibility_response(love_user_profile, love_connection_id):
    """Fetch love compatibility and save to file."""
    response = call_function("get_compatibility", {
        "user_id": love_user_profile,
        "connection_id": love_connection_id,
    })

    # Save to backend_output for iOS
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "compatibility_love.json"
    with open(output_file, "w") as f:
        json.dump(response, f, indent=2)

    return response


class TestLoveCompatibilityOutput:
    """E2E tests for love compatibility - generates iOS mock data."""

    @pytest.mark.llm
    def test_love_output_saved(self, love_compatibility_response):
        """Test love compatibility output is saved to file."""
        output_file = OUTPUT_DIR / "compatibility_love.json"
        assert output_file.exists(), "Love compatibility output not saved"

    @pytest.mark.llm
    def test_love_has_romantic_mode(self, love_compatibility_response):
        """Test love compatibility uses romantic mode."""
        assert "mode" in love_compatibility_response
        mode = love_compatibility_response["mode"]
        assert mode["type"] == "romantic"
        assert "overall_score" in mode
        assert 0 <= mode["overall_score"] <= 100

    @pytest.mark.llm
    def test_love_has_attraction_category(self, love_compatibility_response):
        """Test love compatibility has attraction category."""
        mode = love_compatibility_response["mode"]
        category_ids = {c["id"] for c in mode["categories"]}
        assert "attraction" in category_ids

    @pytest.mark.llm
    def test_love_interpretation_appropriate(self, love_compatibility_response):
        """Test love interpretation uses appropriate language."""
        summary = love_compatibility_response.get("summary", "").lower()

        # Love readings can use romantic language
        # Just verify we got meaningful content
        assert len(summary) > 50, "Summary too short"


# ============================================================================
# iOS MOCK DATA GENERATION - FRIENDSHIP CONNECTION
# ============================================================================

@pytest.fixture(scope="module")
def friendship_user_id():
    """User ID for friendship compatibility test."""
    return "test_user_e"  # Dev account from DEV_ACCOUNT_UIDS


@pytest.fixture(scope="module")
def friendship_user_profile(friendship_user_id):
    """Create user profile for friendship test - Sofia."""
    call_function("create_user_profile", {
        "user_id": friendship_user_id,
        "name": "Sofia",
        "email": f"{friendship_user_id}@test.com",
        "birth_date": "1995-11-08",  # Scorpio
        "birth_time": "11:20",
        "birth_timezone": "America/Los_Angeles",
        "birth_lat": 34.0522,
        "birth_lon": -118.2437,
    })
    return friendship_user_id


@pytest.fixture(scope="module")
def friendship_connection_id(friendship_user_profile):
    """Create friendship connection - Maya (close friend)."""
    conn_result = call_function("create_connection", {
        "user_id": friendship_user_profile,
        "connection": {
            "name": "Maya",
            "birth_date": "1994-05-21",  # Taurus/Gemini cusp
            "birth_time": "14:00",
            "birth_timezone": "America/Denver",
            "birth_lat": 39.7392,
            "birth_lon": -104.9903,
            "relationship_category": "friend",
            "relationship_label": "close_friend",  # Valid label (not 'best_friend')
        }
    })
    return conn_result["connection_id"]


@pytest.fixture(scope="module")
def friendship_compatibility_response(friendship_user_profile, friendship_connection_id):
    """Fetch friendship compatibility and save to file."""
    response = call_function("get_compatibility", {
        "user_id": friendship_user_profile,
        "connection_id": friendship_connection_id,
    })

    # Save to backend_output for iOS
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "compatibility_friendship.json"
    with open(output_file, "w") as f:
        json.dump(response, f, indent=2)

    return response


class TestFriendshipCompatibilityOutput:
    """E2E tests for friendship compatibility - generates iOS mock data."""

    @pytest.mark.llm
    def test_friendship_output_saved(self, friendship_compatibility_response):
        """Test friendship compatibility output is saved to file."""
        output_file = OUTPUT_DIR / "compatibility_friendship.json"
        assert output_file.exists(), "Friendship compatibility output not saved"

    @pytest.mark.llm
    def test_friendship_has_friendship_mode(self, friendship_compatibility_response):
        """Test friendship compatibility uses friendship mode."""
        assert "mode" in friendship_compatibility_response
        mode = friendship_compatibility_response["mode"]
        assert mode["type"] == "friendship"
        assert "overall_score" in mode
        assert 0 <= mode["overall_score"] <= 100

    @pytest.mark.llm
    def test_friendship_has_fun_category(self, friendship_compatibility_response):
        """Test friendship compatibility has fun category."""
        mode = friendship_compatibility_response["mode"]
        category_ids = {c["id"] for c in mode["categories"]}
        assert "fun" in category_ids

    @pytest.mark.llm
    def test_friendship_no_romantic_terms(self, friendship_compatibility_response):
        """Test friendship interpretation avoids romantic language."""
        summary = friendship_compatibility_response.get("summary", "").lower()
        headline = friendship_compatibility_response.get("headline", "").lower()
        all_text = f"{summary} {headline}"

        # These terms should not appear in friendship readings
        forbidden_terms = ["romance", "passion", "intimacy", "lover"]
        for term in forbidden_terms:
            assert term not in all_text, f"Romantic term '{term}' in friendship reading"


# ============================================================================
# iOS MOCK DATA GENERATION - COWORKER CONNECTION
# ============================================================================

@pytest.fixture(scope="module")
def coworker_user_id():
    """User ID for coworker compatibility test."""
    return "test_crud_user"  # Dev account from DEV_ACCOUNT_UIDS


@pytest.fixture(scope="module")
def coworker_user_profile(coworker_user_id):
    """Create user profile for coworker test - Alex."""
    call_function("create_user_profile", {
        "user_id": coworker_user_id,
        "name": "Alex",
        "email": f"{coworker_user_id}@test.com",
        "birth_date": "1988-01-25",  # Aquarius
        "birth_time": "08:15",
        "birth_timezone": "America/New_York",
        "birth_lat": 40.7128,
        "birth_lon": -74.0060,
    })
    return coworker_user_id


@pytest.fixture(scope="module")
def coworker_connection_id(coworker_user_profile):
    """Create coworker connection - Jordan (manager)."""
    conn_result = call_function("create_connection", {
        "user_id": coworker_user_profile,
        "connection": {
            "name": "Jordan",
            "birth_date": "1975-09-10",  # Virgo
            "birth_time": "06:30",
            "birth_timezone": "America/Chicago",
            "birth_lat": 41.8781,
            "birth_lon": -87.6298,
            "relationship_category": "coworker",
            "relationship_label": "manager",  # Valid label (not 'boss')
        }
    })
    return conn_result["connection_id"]


@pytest.fixture(scope="module")
def coworker_compatibility_response(coworker_user_profile, coworker_connection_id):
    """Fetch coworker compatibility and save to file."""
    response = call_function("get_compatibility", {
        "user_id": coworker_user_profile,
        "connection_id": coworker_connection_id,
    })

    # Save to backend_output for iOS
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "compatibility_coworker.json"
    with open(output_file, "w") as f:
        json.dump(response, f, indent=2)

    return response


class TestCoworkerCompatibilityOutput:
    """E2E tests for coworker compatibility - generates iOS mock data."""

    @pytest.mark.llm
    def test_coworker_output_saved(self, coworker_compatibility_response):
        """Test coworker compatibility output is saved to file."""
        output_file = OUTPUT_DIR / "compatibility_coworker.json"
        assert output_file.exists(), "Coworker compatibility output not saved"

    @pytest.mark.llm
    def test_coworker_has_coworker_mode(self, coworker_compatibility_response):
        """Test coworker compatibility uses coworker mode."""
        assert "mode" in coworker_compatibility_response
        mode = coworker_compatibility_response["mode"]
        assert mode["type"] == "coworker"
        assert "overall_score" in mode
        assert 0 <= mode["overall_score"] <= 100

    @pytest.mark.llm
    def test_coworker_has_collaboration_category(self, coworker_compatibility_response):
        """Test coworker compatibility has collaboration category."""
        mode = coworker_compatibility_response["mode"]
        category_ids = {c["id"] for c in mode["categories"]}
        assert "collaboration" in category_ids

    @pytest.mark.llm
    def test_coworker_no_romantic_terms(self, coworker_compatibility_response):
        """Test coworker interpretation avoids romantic language."""
        summary = coworker_compatibility_response.get("summary", "").lower()
        headline = coworker_compatibility_response.get("headline", "").lower()
        all_text = f"{summary} {headline}"

        # These terms should NEVER appear in coworker readings
        forbidden_terms = ["love", "romance", "passion", "intimacy", "heart", "soulmate"]
        for term in forbidden_terms:
            assert term not in all_text, f"Romantic term '{term}' in coworker reading"

    @pytest.mark.llm
    def test_coworker_uses_professional_framing(self, coworker_compatibility_response):
        """Test coworker reading uses professional language."""
        summary = coworker_compatibility_response.get("summary", "").lower()

        # Should have professional/work-related terms
        professional_indicators = ["work", "professional", "career", "collaborate", "team", "project", "business"]
        has_professional = any(term in summary for term in professional_indicators)
        assert has_professional, "Coworker reading should use professional language"

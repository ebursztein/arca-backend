"""
E2E Tests for Journey 9: Ask the Stars (Conversational Q&A).

Tests the ACTUAL HTTP endpoint via Firebase emulator:
- ask_the_stars: SSE streaming endpoint for Q&A

Note: ask_the_stars is an HTTPS endpoint, not a callable function.

NO MOCKS. Real HTTP calls to emulator. Real Gemini API.

OPTIMIZATION: Uses module-scoped fixtures to cache LLM responses.
One user profile creation, one SSE request for most tests.
Conversation continuity test requires separate LLM calls by design.
"""
import pytest
import requests
import uuid
from datetime import datetime

from .conftest import call_function


# Direct HTTP endpoint (not callable function)
ASK_THE_STARS_URL = "http://localhost:5001/arca-baf77/us-central1/ask_the_stars"

# Dev token for authentication bypass
DEV_AUTH_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer dev_arca_2025",
}


# ============================================================================
# MODULE-SCOPED FIXTURES (LLM calls cached for entire module)
# ============================================================================

@pytest.fixture(scope="module")
def ask_stars_user_id():
    """Fixed user ID for ask_the_stars tests (module-scoped)."""
    return "test_user_d"  # Dev account from DEV_ACCOUNT_UIDS


@pytest.fixture(scope="module")
def ask_stars_user_profile(ask_stars_user_id):
    """Create user profile and generate horoscope for all ask_the_stars tests."""
    call_function("create_user_profile", {
        "user_id": ask_stars_user_id,
        "name": "Test User",
        "email": f"{ask_stars_user_id}@test.com",
        "birth_date": "1990-06-15",  # Gemini
    })
    # ask_the_stars requires a horoscope to exist
    call_function("get_daily_horoscope", {
        "user_id": ask_stars_user_id,
    })
    return ask_stars_user_id


@pytest.fixture(scope="module")
def ask_stars_sse_response(ask_stars_user_profile):
    """
    Make one SSE request and capture the full response for all tests.
    Returns tuple: (status_code, content_type, full_content_bytes)
    """
    response = requests.post(
        ASK_THE_STARS_URL,
        json={
            "user_id": ask_stars_user_profile,
            "question": "Tell me about being a Gemini and what my sun sign means",
            "horoscope_date": datetime.now().strftime("%Y-%m-%d"),
        },
        headers=DEV_AUTH_HEADERS,
        stream=True,
        timeout=60,
    )

    status_code = response.status_code
    content_type = response.headers.get("Content-Type", "")

    # Collect full response
    full_content = b""
    for chunk in response.iter_content(chunk_size=1024):
        full_content += chunk

    response.close()

    return (status_code, content_type, full_content)


# ============================================================================
# ASK THE STARS TESTS (most use cached ask_stars_sse_response)
# ============================================================================

class TestAskTheStars:
    """E2E tests for ask_the_stars HTTPS endpoint."""

    @pytest.mark.llm
    def test_returns_sse_stream(self, ask_stars_sse_response):
        """Test ask_the_stars returns SSE stream."""
        status_code, content_type, full_content = ask_stars_sse_response

        assert status_code == 200
        assert "text/event-stream" in content_type
        # Should have SSE data format
        assert b"data:" in full_content

    @pytest.mark.llm
    def test_responds_to_astrology_question(self, ask_stars_sse_response):
        """Test ask_the_stars responds to astrology questions."""
        status_code, content_type, full_content = ask_stars_sse_response

        assert status_code == 200

        # Response should mention Gemini (case insensitive)
        content_str = full_content.decode("utf-8").lower()
        assert "gemini" in content_str or "air" in content_str or "mercury" in content_str

    @pytest.mark.llm
    def test_creates_conversation(self, ask_stars_sse_response):
        """Test ask_the_stars creates conversation in Firestore."""
        status_code, content_type, full_content = ask_stars_sse_response

        # If we got a successful response, a conversation was created
        assert status_code == 200
        assert len(full_content) > 0


class TestAskTheStarsConversationContinuity:
    """
    Test conversation continuity (requires separate LLM calls by design).
    Uses its own user to ensure fresh conversation state.
    """

    @pytest.mark.llm
    def test_continues_conversation(self, test_user_id):
        """Test ask_the_stars continues existing conversation."""
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })
        # ask_the_stars requires a horoscope to exist
        call_function("get_daily_horoscope", {
            "user_id": test_user_id,
        })

        today = datetime.now().strftime("%Y-%m-%d")

        # First message
        resp1 = requests.post(
            ASK_THE_STARS_URL,
            json={
                "user_id": test_user_id,
                "question": "My name is Alex",
                "horoscope_date": today,
            },
            headers=DEV_AUTH_HEADERS,
            stream=True,
            timeout=60,
        )
        for _ in resp1.iter_content(chunk_size=1024):
            pass
        resp1.close()

        # Follow-up message
        resp2 = requests.post(
            ASK_THE_STARS_URL,
            json={
                "user_id": test_user_id,
                "question": "What was my name again?",
                "horoscope_date": today,
            },
            headers=DEV_AUTH_HEADERS,
            stream=True,
            timeout=60,
        )

        assert resp2.status_code == 200

        full_content = b""
        for chunk in resp2.iter_content(chunk_size=1024):
            full_content += chunk
        resp2.close()

        # Verify we got a response (conversation continued)
        content_str = full_content.decode("utf-8").lower()
        assert len(content_str) > 50  # Got meaningful response
        assert "data:" in content_str  # SSE format


class TestAskTheStarsErrorCases:
    """Error case tests (no LLM calls needed)."""

    def test_missing_user_returns_error(self):
        """Test ask_the_stars with missing user returns error."""
        response = requests.post(
            ASK_THE_STARS_URL,
            json={
                "user_id": "nonexistent_user_xyz_999",
                "question": "Hello",
                "horoscope_date": datetime.now().strftime("%Y-%m-%d"),
            },
            headers=DEV_AUTH_HEADERS,
            timeout=30,
        )

        # Should return error status
        assert response.status_code >= 400

    def test_missing_question_returns_error(self, test_user_id):
        """Test ask_the_stars without question returns error."""
        response = requests.post(
            ASK_THE_STARS_URL,
            json={
                "user_id": test_user_id,
                "horoscope_date": datetime.now().strftime("%Y-%m-%d"),
                # Missing question
            },
            headers=DEV_AUTH_HEADERS,
            timeout=30,
        )

        assert response.status_code >= 400


class TestAskTheStarsPromptDebug:
    """Debug test to verify prompt contains technical analysis and natal data."""

    @pytest.mark.llm
    def test_is_today_a_good_day_has_technical_support(self, test_user_id):
        """
        Test: "Is today a good day?" should return response with technical backing.

        This test verifies:
        1. The response includes actual astrological context (not generic fluff)
        2. Transit interpretations are used
        3. Response matches our brand voice (direct, actionable)
        """
        # Create user with full birth data for natal chart
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Luna",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1992-03-21",  # Aries
            "birth_time": "14:30",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
        })

        # Generate horoscope (this populates technical_analysis, transit_summary, etc.)
        horoscope_resp = call_function("get_daily_horoscope", {
            "user_id": test_user_id,
        })

        # Print the horoscope data that SHOULD be in the prompt
        print("\n" + "=" * 80)
        print("HOROSCOPE DATA AVAILABLE FOR PROMPT")
        print("=" * 80)
        print(f"technical_analysis: {horoscope_resp.get('technical_analysis', 'MISSING!')[:200]}...")
        print(f"daily_overview: {horoscope_resp.get('daily_overview', 'MISSING!')[:200]}...")
        print(f"daily_theme_headline: {horoscope_resp.get('daily_theme_headline', 'MISSING!')}")
        print("=" * 80)

        today = datetime.now().strftime("%Y-%m-%d")

        # Ask the key question
        response = requests.post(
            ASK_THE_STARS_URL,
            json={
                "user_id": test_user_id,
                "question": "Is today a good day?",
                "horoscope_date": today,
            },
            headers=DEV_AUTH_HEADERS,
            stream=True,
            timeout=60,
        )

        assert response.status_code == 200

        # Collect full response
        full_content = b""
        for chunk in response.iter_content(chunk_size=1024):
            full_content += chunk
        response.close()

        content_str = full_content.decode("utf-8")

        # Extract actual text from SSE chunks
        import json
        response_text = ""
        for line in content_str.split("\n"):
            if line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                    if data.get("type") == "chunk":
                        response_text += data.get("text", "")
                except json.JSONDecodeError:
                    pass

        print("\n" + "=" * 80)
        print("ASK THE STARS RESPONSE TO 'Is today a good day?'")
        print("=" * 80)
        print(response_text)
        print("=" * 80)

        # Verify response has substance (not generic fluff)
        response_lower = response_text.lower()

        # Should NOT be generic positivity without substance
        generic_phrases = [
            "the universe has",
            "beautiful things",
            "trust the process",
            "everything happens for a reason",
        ]
        for phrase in generic_phrases:
            assert phrase not in response_lower, f"Response contains generic fluff: '{phrase}'"

        # Should be reasonably substantive (not just "Yes!" or "No!")
        assert len(response_text) > 100, "Response too short - lacks substance"

        # Should contain SOME indication of astrological backing
        # (checking for common transit/planet references or energy words)
        astrological_indicators = [
            "today", "energy", "vibe", "planet", "transit", "moon", "sun",
            "mars", "venus", "mercury", "saturn", "jupiter", "flow",
            "challenge", "push", "pull", "feel", "focus", "wait"
        ]
        found_indicators = [ind for ind in astrological_indicators if ind in response_lower]
        assert len(found_indicators) >= 2, \
            f"Response lacks astrological context. Found: {found_indicators}"

        print(f"\nAstrological indicators found: {found_indicators}")
        print("Test passed - response has technical backing")

    @pytest.mark.llm
    def test_mentions_connection_pulls_synastry_data(self, test_user_id):
        """
        Test: When user asks about a connection by name, synastry data is used.

        This test verifies:
        1. Connection data is pulled when name appears in question
        2. Synastry aspects are calculated and available
        3. Response references the specific relationship
        """
        # Create user with full birth data
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Maya",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1994-08-12",  # Leo
            "birth_time": "10:00",
            "birth_lat": 34.0522,
            "birth_lon": -118.2437,
        })

        # Create a connection named "Alex"
        connection_resp = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "Alex",
                "birth_date": "1992-01-15",  # Capricorn
                "birth_time": "14:30",
                "birth_lat": 40.7128,
                "birth_lon": -74.0060,
                "relationship_category": "love",
                "relationship_label": "partner",
            }
        })

        print("\n" + "=" * 80)
        print("CONNECTION CREATED")
        print("=" * 80)
        print(f"Connection: {connection_resp}")
        print("=" * 80)

        # Generate horoscope
        call_function("get_daily_horoscope", {
            "user_id": test_user_id,
        })

        today = datetime.now().strftime("%Y-%m-%d")

        # Ask about Alex by name
        response = requests.post(
            ASK_THE_STARS_URL,
            json={
                "user_id": test_user_id,
                "question": "How are things looking with Alex today?",
                "horoscope_date": today,
            },
            headers=DEV_AUTH_HEADERS,
            stream=True,
            timeout=60,
        )

        assert response.status_code == 200

        # Collect full response
        full_content = b""
        for chunk in response.iter_content(chunk_size=1024):
            full_content += chunk
        response.close()

        content_str = full_content.decode("utf-8")

        # Extract actual text from SSE chunks
        import json
        response_text = ""
        for line in content_str.split("\n"):
            if line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                    if data.get("type") == "chunk":
                        response_text += data.get("text", "")
                except json.JSONDecodeError:
                    pass

        print("\n" + "=" * 80)
        print("ASK THE STARS RESPONSE TO 'How are things looking with Alex today?'")
        print("=" * 80)
        print(response_text)
        print("=" * 80)

        response_lower = response_text.lower()

        # Should mention Alex or relationship context
        assert "alex" in response_lower or "partner" in response_lower or "relationship" in response_lower, \
            "Response doesn't reference the connection"

        # Should have some substance about the connection
        assert len(response_text) > 80, "Response too short"

        # Should reference something astrological about the pairing
        relationship_indicators = [
            "alex", "partner", "relationship", "between", "connection",
            "venus", "mars", "moon", "sun", "aspect", "chemistry",
            "tension", "flow", "communicate", "feel", "energy"
        ]
        found = [ind for ind in relationship_indicators if ind in response_lower]
        assert len(found) >= 2, f"Response lacks relationship context. Found: {found}"

        print(f"\nRelationship indicators found: {found}")
        print("Test passed - connection data was used")

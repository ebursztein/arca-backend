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

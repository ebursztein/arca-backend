"""
Pytest configuration and shared fixtures for E2E tests.

Provides:
- Environment variable loading via dotenv
- API key fixtures (skip if not set)
- Firebase emulator fixtures
- Sample data fixtures for users, connections, charts
- Auto-marking for slow/llm/emulator tests
"""
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

import pytest
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add functions directory to path for imports
functions_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(functions_dir))


# ---------------------------------------------------------------------------
# Pytest Configuration
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: mark test as slow (>30s)")
    config.addinivalue_line("markers", "llm: mark test as requiring Gemini API")
    config.addinivalue_line("markers", "emulator: mark test as requiring Firebase emulator")


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on fixtures used."""
    for item in items:
        # Auto-mark tests that use gemini_api_key fixture
        if "gemini_api_key" in item.fixturenames:
            item.add_marker(pytest.mark.llm)
            item.add_marker(pytest.mark.slow)
        # Auto-mark tests that use firestore_emulator fixture
        if "firestore_emulator" in item.fixturenames:
            item.add_marker(pytest.mark.emulator)


# ---------------------------------------------------------------------------
# API Key Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def gemini_api_key():
    """Get Gemini API key from environment. Skip if not set."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        pytest.skip("GEMINI_API_KEY not set in environment")
    return key


@pytest.fixture(scope="session")
def posthog_api_key():
    """Get PostHog API key from environment (optional)."""
    return os.getenv("POSTHOG_API_KEY")


# ---------------------------------------------------------------------------
# Firebase Emulator Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def firestore_emulator():
    """
    Get Firestore client connected to emulator.
    Skip if emulator not running on localhost:8080.
    """
    from emulator_helpers import is_emulator_running, get_emulator_client

    if not is_emulator_running():
        pytest.skip("Firestore emulator not running on localhost:8080")

    return get_emulator_client()


@pytest.fixture
def clean_firestore(firestore_emulator, test_user_id):
    """
    Fixture that cleans up test data after each test.
    Yields the Firestore client, then cleans up.
    """
    from emulator_helpers import clear_test_data

    yield firestore_emulator

    # Cleanup after test
    clear_test_data(firestore_emulator, test_user_id)


# ---------------------------------------------------------------------------
# Test User Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_user_id():
    """Generate unique user ID per test for isolation."""
    return f"test_user_{uuid.uuid4().hex[:12]}"


@pytest.fixture
def test_connection_id():
    """Generate unique connection ID per test."""
    return f"conn_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Birth Data Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_birth_data_minimal():
    """Minimal birth data (V1 mode - birth_date only)."""
    return {
        "birth_date": "1990-06-15",
    }


@pytest.fixture
def sample_birth_data_full():
    """Full birth data (V2 mode - date + time + location)."""
    return {
        "birth_date": "1990-06-15",
        "birth_time": "14:30",
        "birth_timezone": "America/New_York",
        "birth_lat": 40.7128,
        "birth_lon": -74.0060,
    }


@pytest.fixture
def sample_connection_birth_data():
    """Birth data for a sample connection (different person)."""
    return {
        "birth_date": "1992-03-22",
        "birth_time": "10:15",
        "birth_timezone": "America/Los_Angeles",
        "birth_lat": 34.0522,
        "birth_lon": -118.2437,
    }


# ---------------------------------------------------------------------------
# Chart Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_natal_chart(sample_birth_data_full):
    """Pre-computed natal chart from full birth data."""
    from astro import compute_birth_chart

    chart_dict, _ = compute_birth_chart(
        birth_date=sample_birth_data_full["birth_date"],
        birth_time=sample_birth_data_full["birth_time"],
        birth_timezone=sample_birth_data_full["birth_timezone"],
        birth_lat=sample_birth_data_full["birth_lat"],
        birth_lon=sample_birth_data_full["birth_lon"],
    )
    return chart_dict


@pytest.fixture
def sample_transit_chart():
    """Pre-computed transit chart for today."""
    from astro import compute_birth_chart

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    chart_dict, _ = compute_birth_chart(birth_date=today, birth_time="12:00")
    return chart_dict


# ---------------------------------------------------------------------------
# User Profile Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user_profile(test_user_id, sample_natal_chart, sample_birth_data_full):
    """Create a valid UserProfile for testing."""
    from models import UserProfile

    now = datetime.now(timezone.utc).isoformat()

    return UserProfile(
        user_id=test_user_id,
        name="Test User",
        email=f"{test_user_id}@test.com",
        birth_date=sample_birth_data_full["birth_date"],
        birth_time=sample_birth_data_full["birth_time"],
        birth_timezone=sample_birth_data_full["birth_timezone"],
        birth_lat=sample_birth_data_full["birth_lat"],
        birth_lon=sample_birth_data_full["birth_lon"],
        sun_sign="gemini",
        natal_chart=sample_natal_chart,
        exact_chart=True,
        created_at=now,
        last_active=now,
    )


@pytest.fixture
def sample_user_profile_v1(test_user_id, sample_birth_data_minimal):
    """Create a V1 UserProfile (birth_date only, noon-estimated chart)."""
    from models import UserProfile
    from astro import compute_birth_chart, get_sun_sign

    chart_dict, exact = compute_birth_chart(
        birth_date=sample_birth_data_minimal["birth_date"],
    )
    sun_sign = get_sun_sign(sample_birth_data_minimal["birth_date"]).value
    now = datetime.now(timezone.utc).isoformat()

    return UserProfile(
        user_id=test_user_id,
        name="V1 Test User",
        email=f"{test_user_id}@test.com",
        birth_date=sample_birth_data_minimal["birth_date"],
        sun_sign=sun_sign,
        natal_chart=chart_dict,
        exact_chart=exact,
        created_at=now,
        last_active=now,
    )


# ---------------------------------------------------------------------------
# Memory Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_memory(test_user_id):
    """Empty memory collection for user."""
    from models import create_empty_memory

    return create_empty_memory(test_user_id)


# ---------------------------------------------------------------------------
# Connection Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_connections():
    """List of sample Connection data dicts for testing."""
    now = datetime.now(timezone.utc).isoformat()

    return [
        {
            "connection_id": "conn_john_001",
            "name": "John",
            "birth_date": "1992-08-15",
            "relationship_type": "partner",
            "sun_sign": "leo",
            "created_at": now,
            "updated_at": now,
            "arca_notes": [],
            "vibes": [],
        },
        {
            "connection_id": "conn_sarah_002",
            "name": "Sarah",
            "birth_date": "1995-06-05",
            "relationship_type": "friend",
            "sun_sign": "gemini",
            "created_at": now,
            "updated_at": now,
            "arca_notes": [],
            "vibes": [],
        },
        {
            "connection_id": "conn_mom_003",
            "name": "Mom",
            "birth_date": "1965-07-10",
            "relationship_type": "family",
            "sun_sign": "cancer",
            "created_at": now,
            "updated_at": now,
            "arca_notes": [],
            "vibes": [],
        },
    ]


@pytest.fixture
def sample_connection_full(test_connection_id, sample_connection_birth_data):
    """Single connection with full birth data."""
    from astro import compute_birth_chart, get_sun_sign

    chart_dict, exact = compute_birth_chart(
        birth_date=sample_connection_birth_data["birth_date"],
        birth_time=sample_connection_birth_data["birth_time"],
        birth_timezone=sample_connection_birth_data["birth_timezone"],
        birth_lat=sample_connection_birth_data["birth_lat"],
        birth_lon=sample_connection_birth_data["birth_lon"],
    )
    sun_sign = get_sun_sign(sample_connection_birth_data["birth_date"]).value
    now = datetime.now(timezone.utc).isoformat()

    return {
        "connection_id": test_connection_id,
        "name": "Test Connection",
        "birth_date": sample_connection_birth_data["birth_date"],
        "birth_time": sample_connection_birth_data["birth_time"],
        "birth_timezone": sample_connection_birth_data["birth_timezone"],
        "birth_lat": sample_connection_birth_data["birth_lat"],
        "birth_lon": sample_connection_birth_data["birth_lon"],
        "relationship_type": "friend",
        "sun_sign": sun_sign,
        "natal_chart": chart_dict,
        "exact_chart": exact,
        "created_at": now,
        "updated_at": now,
        "arca_notes": [],
        "vibes": [],
    }


# ---------------------------------------------------------------------------
# Firebase Emulator HTTP Client
# ---------------------------------------------------------------------------

import requests

EMULATOR_BASE_URL = "http://localhost:5001/arca-baf77/us-central1"


def call_function(function_name: str, data: dict) -> dict:
    """
    Call a Cloud Function via the Firebase emulator.

    Args:
        function_name: Name of the function (e.g., 'get_sun_sign_from_date')
        data: Request data to send

    Returns:
        The 'result' field from the response

    Raises:
        Exception if the function returns an error
    """
    url = f"{EMULATOR_BASE_URL}/{function_name}"
    print(f"\n[E2E] POST {url}")
    print(f"[E2E] Payload: {data}")

    response = requests.post(
        url,
        json={"data": data},
        headers={"Content-Type": "application/json"},
        timeout=120,
    )

    print(f"[E2E] Response: {response.status_code}")

    result = response.json()

    if "error" in result:
        error = result["error"]
        raise Exception(f"{error.get('status', 'ERROR')}: {error.get('message', 'Unknown error')}")

    return result.get("result", result)


# ---------------------------------------------------------------------------
# Date Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def today_date():
    """Today's date in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

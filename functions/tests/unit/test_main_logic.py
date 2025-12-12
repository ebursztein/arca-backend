"""
Unit tests for main.py logic using mocks.
Tests Cloud Functions entry points without actual Firebase/LLM calls.
"""

import sys
import pytest
from unittest.mock import MagicMock, patch

# =============================================================================
# Mock Firebase Dependencies BEFORE importing main
# =============================================================================

# Create mock modules
mock_firebase_functions = MagicMock()
mock_firebase_admin = MagicMock()
mock_firebase_secrets = MagicMock()

# Setup https_fn structure
mock_https_fn = MagicMock()
mock_https_fn.CallableRequest = MagicMock
# Create a proper HttpsError class that accepts keyword arguments
class MockHttpsError(Exception):
    def __init__(self, code=None, message=None, details=None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message or "")
mock_https_fn.HttpsError = MockHttpsError
mock_https_fn.FunctionsErrorCode = MagicMock()
# Make on_call decorator pass through the original function
mock_https_fn.on_call.return_value = lambda f: f
mock_firebase_functions.https_fn = mock_https_fn

# Setup firestore structure
mock_firestore = MagicMock()
mock_firestore_client = MagicMock()
mock_firestore.client.return_value = mock_firestore_client
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.initialize_app = MagicMock()

# Setup params and secrets
mock_params = MagicMock()
mock_firebase_functions.params = mock_params
mock_secret = MagicMock()
mock_secret.value = "test_key"
mock_firebase_secrets.GEMINI_API_KEY = mock_secret
mock_firebase_secrets.POSTHOG_API_KEY = mock_secret

# Apply patches to sys.modules
with patch.dict(sys.modules, {
    "firebase_functions": mock_firebase_functions,
    "firebase_admin": mock_firebase_admin,
    "firebase_secrets": mock_firebase_secrets
}):
    # Import main after mocking
    import main

# =============================================================================
# Tests
# =============================================================================

def test_natal_chart_success():
    """Test natal_chart function with valid data."""
    # Setup request
    req = MagicMock()
    req.data = {
        "utc_dt": "1990-06-15 14:30",
        "lat": 40.7128,
        "lon": -74.0060
    }
    
    # Call function
    result = main.natal_chart(req)
    
    # Verify result
    assert isinstance(result, dict)
    assert result["chart_type"] == "natal"
    assert result["location_lat"] == 40.7128
    assert len(result["planets"]) == 12


def test_natal_chart_missing_params():
    """Test natal_chart throws error on missing params."""
    req = MagicMock()
    req.data = {"utc_dt": "1990-06-15 14:30"} # Missing lat/lon

    with pytest.raises(MockHttpsError) as excinfo:
        main.natal_chart(req)

    # Check that HttpsError was raised with correct message
    assert "Missing required parameters" in excinfo.value.message


def test_daily_transit_default_date():
    """Test daily_transit uses today's date if not provided."""
    req = MagicMock()
    req.data = {}
    
    result = main.daily_transit(req)
    
    assert result["chart_type"] == "transit"
    assert result["location_lat"] == 0.0
    
    # Should have generated a timestamp for today (check format)
    assert "00:00" in result["datetime_utc"]


def test_daily_transit_specific_date():
    """Test daily_transit uses provided date."""
    req = MagicMock()
    req.data = {"utc_dt": "2025-01-01 00:00"}
    
    result = main.daily_transit(req)
    
    assert result["datetime_utc"] == "2025-01-01 00:00"


def test_user_transit_success():
    """Test user_transit with valid data."""
    req = MagicMock()
    req.data = {
        "birth_lat": 40.7128,
        "birth_lon": -74.0060
    }
    
    result = main.user_transit(req)
    
    assert result["chart_type"] == "transit"
    assert result["location_lat"] == 40.7128
    # Should contain houses since we provided location
    assert "houses" in result


def _setup_firestore_mock_for_profile(mock_db, user_exists=False, existing_data=None):
    """Helper to setup Firestore mock for create_user_profile tests."""
    mock_user_doc = MagicMock()
    mock_user_doc.exists = user_exists
    mock_user_doc.to_dict.return_value = existing_data or {}

    mock_memory_doc = MagicMock()
    mock_memory_doc.exists = False

    def collection_side_effect(name):
        mock_collection = MagicMock()
        mock_doc = MagicMock()

        if name == "users":
            mock_doc.get.return_value = mock_user_doc
        elif name == "memory":
            mock_doc.get.return_value = mock_memory_doc

        mock_collection.document.return_value = mock_doc
        return mock_collection

    mock_db.collection.side_effect = collection_side_effect
    return mock_db


@patch("llm.generate_natal_chart_summary")
def test_create_user_profile_v1(mock_gen_summary):
    """Test V1 profile creation (date only)."""
    mock_gen_summary.return_value = "You are a Gemini."

    # Setup Firestore mock for new user
    mock_db = MagicMock()
    _setup_firestore_mock_for_profile(mock_db, user_exists=False)
    mock_firestore.client.return_value = mock_db

    req = MagicMock()
    req.auth.uid = "user_123"  # Set up auth directly on request
    req.data = {
        "name": "Test",
        "email": "test@test.com",
        "birth_date": "1990-06-15"
    }

    result = main.create_user_profile(req)

    assert result["success"] is True
    assert result["mode"] == "v1"
    assert result["sun_sign"] == "gemini"
    assert result["exact_chart"] is False


@patch("llm.generate_natal_chart_summary")
def test_create_user_profile_v2(mock_gen_summary):
    """Test V2 profile creation (full birth info)."""
    mock_gen_summary.return_value = "You are a Gemini with Virgo Rising."

    # Setup Firestore mock for new user
    mock_db = MagicMock()
    _setup_firestore_mock_for_profile(mock_db, user_exists=False)
    mock_firestore.client.return_value = mock_db

    req = MagicMock()
    req.auth.uid = "user_123"  # Set up auth directly on request
    req.data = {
        "name": "Test",
        "email": "test@test.com",
        "birth_date": "1990-06-15",
        "birth_time": "14:30",
        "birth_timezone": "America/New_York",
        "birth_lat": 40.7128,
        "birth_lon": -74.0060
    }

    result = main.create_user_profile(req)

    assert result["success"] is True
    assert result["mode"] == "v2"
    assert result["exact_chart"] is True


@patch("llm.generate_natal_chart_summary")
def test_create_user_profile_preserves_protected_fields(mock_gen_summary):
    """Test that calling create_user_profile repeatedly preserves premium/trial/created_at."""
    mock_gen_summary.return_value = "You are a Gemini."

    # Simulate existing user with premium status and trial info
    existing_data = {
        "is_premium": True,
        "premium_expiry": "2025-12-31",
        "is_trial_active": True,
        "trial_end_date": "2025-01-15",
        "created_at": "2024-06-01T10:00:00",
    }

    mock_db = MagicMock()
    _setup_firestore_mock_for_profile(mock_db, user_exists=True, existing_data=existing_data)
    mock_firestore.client.return_value = mock_db

    # Track what gets written to Firestore
    captured_profile = {}

    def capture_set(data):
        captured_profile.update(data)

    mock_db.collection.side_effect = None  # Reset side_effect

    # Re-setup with capture
    mock_user_doc = MagicMock()
    mock_user_doc.exists = True
    mock_user_doc.to_dict.return_value = existing_data

    mock_memory_doc = MagicMock()
    mock_memory_doc.exists = True  # Memory already exists

    mock_user_ref = MagicMock()
    mock_user_ref.get.return_value = mock_user_doc
    mock_user_ref.set.side_effect = capture_set

    mock_memory_ref = MagicMock()
    mock_memory_ref.get.return_value = mock_memory_doc

    def collection_side_effect(name):
        mock_collection = MagicMock()
        if name == "users":
            mock_collection.document.return_value = mock_user_ref
        elif name == "memory":
            mock_collection.document.return_value = mock_memory_ref
        return mock_collection

    mock_db.collection.side_effect = collection_side_effect

    req = MagicMock()
    req.auth.uid = "user_123"
    req.data = {
        "name": "Updated Name",
        "email": "test@test.com",
        "birth_date": "1990-06-15"
    }

    result = main.create_user_profile(req)

    assert result["success"] is True

    # Verify protected fields were preserved
    assert captured_profile["is_premium"] is True
    assert captured_profile["premium_expiry"] == "2025-12-31"
    assert captured_profile["is_trial_active"] is True
    assert captured_profile["trial_end_date"] == "2025-01-15"
    assert captured_profile["created_at"] == "2024-06-01T10:00:00"

    # Verify updatable fields were updated
    assert captured_profile["name"] == "Updated Name"

    # Verify memory was NOT reset (already exists)
    mock_memory_ref.set.assert_not_called()

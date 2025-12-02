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


@patch("llm.generate_natal_chart_summary")
def test_create_user_profile_v1(mock_gen_summary):
    """Test V1 profile creation (date only)."""
    mock_gen_summary.return_value = "You are a Gemini."

    # Setup Firestore mock
    mock_db = MagicMock()
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

    # Verify Firestore write
    mock_db.collection.return_value.document.return_value.set.assert_called()


@patch("llm.generate_natal_chart_summary")
def test_create_user_profile_v2(mock_gen_summary):
    """Test V2 profile creation (full birth info)."""
    mock_gen_summary.return_value = "You are a Gemini with Virgo Rising."

    # Setup Firestore mock
    mock_db = MagicMock()
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

    # Verify Firestore write
    mock_db.collection.return_value.document.return_value.set.assert_called()

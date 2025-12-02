"""
E2E tests for authentication enforcement.

Verifies that all protected endpoints reject unauthenticated requests.
"""

import pytest
from .conftest import call_function


# All endpoints that require authentication (use get_authenticated_user_id)
PROTECTED_ENDPOINTS = [
    ("create_user_profile", {"name": "Test", "email": "test@test.com", "birth_date": "1990-01-01"}),
    ("get_user_profile", {}),
    ("update_user_profile", {"birth_time": "12:00"}),
    ("get_memory", {}),
    ("get_daily_horoscope", {}),
    ("get_astrometers", {}),
    ("get_share_link", {}),
    ("import_connection", {"share_secret": "fake"}),
    ("create_connection", {"name": "Test", "birth_date": "1990-01-01", "relationship_category": "friend", "relationship_label": "friend"}),
    ("update_connection", {"connection_id": "fake", "name": "Updated"}),
    ("delete_connection", {"connection_id": "fake"}),
    ("list_connections", {}),
    ("list_connection_requests", {}),
    ("update_share_mode", {"share_mode": "public"}),
    ("respond_to_request", {"request_id": "fake", "action": "approve"}),
    ("register_device_token", {"device_token": "fake", "platform": "ios"}),
    ("get_natal_chart_for_connection", {"connection_id": "fake"}),
    ("get_compatibility", {"connection_id": "fake"}),
    ("get_synastry_chart", {"connection_id": "fake"}),
]


class TestAuthenticationEnforcement:
    """Verify all protected endpoints reject unauthenticated requests."""

    @pytest.mark.parametrize("endpoint,payload", PROTECTED_ENDPOINTS)
    def test_unauthenticated_request_rejected(self, endpoint, payload):
        """Test that endpoint rejects requests without valid auth."""
        # Add a user_id that is NOT in DEV_ACCOUNT_UIDS
        payload_with_bad_auth = {**payload, "user_id": "unauthorized_user_xyz"}

        with pytest.raises(Exception) as exc_info:
            call_function(endpoint, payload_with_bad_auth)

        assert "UNAUTHENTICATED" in str(exc_info.value), (
            f"{endpoint} should reject unauthenticated requests"
        )

    @pytest.mark.parametrize("endpoint,payload", PROTECTED_ENDPOINTS)
    def test_missing_user_id_rejected(self, endpoint, payload):
        """Test that endpoint rejects requests with no user_id."""
        # Remove user_id entirely
        payload_no_auth = {k: v for k, v in payload.items() if k != "user_id"}

        with pytest.raises(Exception) as exc_info:
            call_function(endpoint, payload_no_auth)

        assert "UNAUTHENTICATED" in str(exc_info.value), (
            f"{endpoint} should reject requests without user_id"
        )


# Endpoints that should NOT require authentication
PUBLIC_ENDPOINTS = [
    ("natal_chart", {"utc_dt": "1990-06-15 12:00", "lat": 40.7128, "lon": -74.0060}),
    ("daily_transit", {}),
    ("user_transit", {"lat": 40.7128, "lon": -74.0060}),
    ("get_sun_sign_from_date", {"birth_date": "1990-06-15"}),
    ("get_public_profile", {"share_secret": "fake"}),
]


class TestPublicEndpoints:
    """Verify public endpoints work without authentication."""

    @pytest.mark.parametrize("endpoint,payload", PUBLIC_ENDPOINTS)
    def test_public_endpoint_accessible(self, endpoint, payload):
        """Test that public endpoints don't require auth."""
        # These should not raise UNAUTHENTICATED
        # They may raise other errors (NOT_FOUND, etc.) but not auth errors
        try:
            call_function(endpoint, payload)
        except Exception as e:
            # Should not be an auth error
            assert "UNAUTHENTICATED" not in str(e), (
                f"{endpoint} should not require authentication"
            )

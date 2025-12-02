"""
Unit tests for auth.py - authentication helper functions.

Tests:
- Dev account bypass
- Firebase Auth validation
- Missing auth handling
- Missing uid handling
"""

import pytest
from unittest.mock import MagicMock, patch
from firebase_functions import https_fn

from auth import get_authenticated_user_id, DEV_ACCOUNT_UIDS


class MockAuthInfo:
    """Mock Firebase Auth info."""
    def __init__(self, uid: str = None):
        self.uid = uid


class MockCallableRequest:
    """Mock Firebase CallableRequest."""
    def __init__(self, data: dict = None, auth: MockAuthInfo = None):
        self.data = data or {}
        self.auth = auth


class TestDevAccountBypass:
    """Test dev account bypass functionality."""

    def test_dev_account_bypass_allowed(self):
        """Dev accounts should bypass Firebase Auth."""
        req = MockCallableRequest(
            data={"user_id": "test_user_a"},
            auth=None  # No Firebase Auth
        )

        result = get_authenticated_user_id(req, allow_override=True)
        assert result == "test_user_a"

    def test_dev_account_bypass_all_accounts(self):
        """All configured dev accounts should work."""
        for dev_uid in DEV_ACCOUNT_UIDS:
            req = MockCallableRequest(
                data={"user_id": dev_uid},
                auth=None
            )
            result = get_authenticated_user_id(req, allow_override=True)
            assert result == dev_uid

    def test_dev_account_bypass_disabled(self):
        """Dev account bypass should not work when disabled."""
        req = MockCallableRequest(
            data={"user_id": "test_user_a"},
            auth=None
        )

        with pytest.raises(https_fn.HttpsError) as exc_info:
            get_authenticated_user_id(req, allow_override=False)

        assert exc_info.value.code == https_fn.FunctionsErrorCode.UNAUTHENTICATED

    def test_non_dev_account_rejected(self):
        """Non-dev user_ids should not bypass auth."""
        req = MockCallableRequest(
            data={"user_id": "random_user_123"},
            auth=None
        )

        with pytest.raises(https_fn.HttpsError) as exc_info:
            get_authenticated_user_id(req, allow_override=True)

        assert exc_info.value.code == https_fn.FunctionsErrorCode.UNAUTHENTICATED


class TestFirebaseAuth:
    """Test Firebase Auth validation."""

    def test_valid_firebase_auth(self):
        """Valid Firebase Auth should return uid."""
        req = MockCallableRequest(
            data={},
            auth=MockAuthInfo(uid="firebase_user_123")
        )

        result = get_authenticated_user_id(req)
        assert result == "firebase_user_123"

    def test_missing_auth_rejected(self):
        """Missing auth should raise UNAUTHENTICATED."""
        req = MockCallableRequest(
            data={},
            auth=None
        )

        with pytest.raises(https_fn.HttpsError) as exc_info:
            get_authenticated_user_id(req)

        assert exc_info.value.code == https_fn.FunctionsErrorCode.UNAUTHENTICATED
        assert "Authentication required" in str(exc_info.value.message)

    def test_missing_uid_rejected(self):
        """Auth present but uid missing should raise UNAUTHENTICATED."""
        req = MockCallableRequest(
            data={},
            auth=MockAuthInfo(uid=None)
        )

        with pytest.raises(https_fn.HttpsError) as exc_info:
            get_authenticated_user_id(req)

        assert exc_info.value.code == https_fn.FunctionsErrorCode.UNAUTHENTICATED
        assert "missing uid" in str(exc_info.value.message)

    def test_empty_uid_rejected(self):
        """Auth present but uid empty should raise UNAUTHENTICATED."""
        req = MockCallableRequest(
            data={},
            auth=MockAuthInfo(uid="")
        )

        with pytest.raises(https_fn.HttpsError) as exc_info:
            get_authenticated_user_id(req)

        assert exc_info.value.code == https_fn.FunctionsErrorCode.UNAUTHENTICATED


class TestPriorityOrder:
    """Test authentication priority order."""

    def test_dev_account_takes_priority(self):
        """Dev account should take priority over Firebase Auth."""
        req = MockCallableRequest(
            data={"user_id": "test_user_a"},
            auth=MockAuthInfo(uid="firebase_user_456")
        )

        result = get_authenticated_user_id(req, allow_override=True)
        # Dev account should win
        assert result == "test_user_a"

    def test_firebase_auth_when_no_dev_account(self):
        """Firebase Auth should be used when no dev account override."""
        req = MockCallableRequest(
            data={"user_id": "not_a_dev_account"},
            auth=MockAuthInfo(uid="firebase_user_789")
        )

        result = get_authenticated_user_id(req, allow_override=True)
        # Firebase Auth should be used since user_id is not a dev account
        assert result == "firebase_user_789"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

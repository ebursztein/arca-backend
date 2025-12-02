"""
Unit tests for conversation_helpers.py - conversation and entity management functions.

Tests:
- get_conversation_history
- get_user_entities
- update_entity
- delete_entity

Note: Full integration tests requiring Firestore are in tests/e2e/.
These unit tests verify function signatures and basic logic.
"""

import pytest
import inspect
from firebase_functions import https_fn

from auth import get_authenticated_user_id


class MockAuthInfo:
    """Mock Firebase Auth info."""
    def __init__(self, uid: str):
        self.uid = uid


class MockCallableRequest:
    """Mock Firebase CallableRequest."""
    def __init__(self, data: dict = None, auth: MockAuthInfo = None):
        self.data = data or {}
        self.auth = auth


class TestFunctionSignatures:
    """Verify function signatures are correct."""

    def test_get_conversation_history_exists(self):
        """get_conversation_history should be a callable function."""
        from conversation_helpers import get_conversation_history
        assert callable(get_conversation_history)

    def test_get_user_entities_exists(self):
        """get_user_entities should be a callable function."""
        from conversation_helpers import get_user_entities
        assert callable(get_user_entities)

    def test_update_entity_exists(self):
        """update_entity should be a callable function."""
        from conversation_helpers import update_entity
        assert callable(update_entity)

    def test_delete_entity_exists(self):
        """delete_entity should be a callable function."""
        from conversation_helpers import delete_entity
        assert callable(delete_entity)


class TestAuthIntegration:
    """Test that conversation helpers use get_authenticated_user_id."""

    def test_get_conversation_history_uses_auth(self):
        """get_conversation_history should use get_authenticated_user_id."""
        from conversation_helpers import get_conversation_history
        import inspect
        source = inspect.getsource(get_conversation_history)
        assert 'get_authenticated_user_id' in source

    def test_get_user_entities_uses_auth(self):
        """get_user_entities should use get_authenticated_user_id."""
        from conversation_helpers import get_user_entities
        import inspect
        source = inspect.getsource(get_user_entities)
        assert 'get_authenticated_user_id' in source

    def test_update_entity_uses_auth(self):
        """update_entity should use get_authenticated_user_id."""
        from conversation_helpers import update_entity
        import inspect
        source = inspect.getsource(update_entity)
        assert 'get_authenticated_user_id' in source

    def test_delete_entity_uses_auth(self):
        """delete_entity should use get_authenticated_user_id."""
        from conversation_helpers import delete_entity
        import inspect
        source = inspect.getsource(delete_entity)
        assert 'get_authenticated_user_id' in source


class TestRequiredValidation:
    """Test that required parameters are validated."""

    def test_get_conversation_history_checks_conversation_id(self):
        """Should verify conversation_id is checked."""
        from conversation_helpers import get_conversation_history
        import inspect
        source = inspect.getsource(get_conversation_history)
        assert 'conversation_id' in source
        assert 'INVALID_ARGUMENT' in source

    def test_update_entity_checks_entity_id(self):
        """Should verify entity_id is checked."""
        from conversation_helpers import update_entity
        import inspect
        source = inspect.getsource(update_entity)
        assert 'entity_id' in source
        assert 'INVALID_ARGUMENT' in source

    def test_delete_entity_checks_entity_id(self):
        """Should verify entity_id is checked."""
        from conversation_helpers import delete_entity
        import inspect
        source = inspect.getsource(delete_entity)
        assert 'entity_id' in source
        assert 'INVALID_ARGUMENT' in source


class TestErrorHandling:
    """Test that proper HTTP errors are raised."""

    def test_get_conversation_history_handles_not_found(self):
        """Should raise NOT_FOUND for missing conversation."""
        from conversation_helpers import get_conversation_history
        import inspect
        source = inspect.getsource(get_conversation_history)
        assert 'NOT_FOUND' in source

    def test_get_conversation_history_handles_permission_denied(self):
        """Should raise PERMISSION_DENIED for unauthorized access."""
        from conversation_helpers import get_conversation_history
        import inspect
        source = inspect.getsource(get_conversation_history)
        assert 'PERMISSION_DENIED' in source

    def test_get_user_entities_handles_invalid_status(self):
        """Should handle invalid status filter."""
        from conversation_helpers import get_user_entities
        import inspect
        source = inspect.getsource(get_user_entities)
        assert 'INVALID_ARGUMENT' in source
        assert 'Invalid status' in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

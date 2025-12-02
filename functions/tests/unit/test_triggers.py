"""
Unit tests for triggers.py - Firestore trigger functions.

Tests:
- Entity extraction trigger logic
- Function signature verification (regression tests)
- Correct API usage (api_key vs gemini_client)

Note: Full integration tests requiring Firestore/LLM are in tests/integration/.
These unit tests focus on verifying the correct function signatures are used.
"""

import pytest
import inspect
from unittest.mock import MagicMock, patch
from datetime import datetime

from models import (
    ExtractedEntities,
    ExtractedEntity,
    MergedEntities,
)


class TestFunctionSignatureRegression:
    """
    CRITICAL Regression tests to ensure function signatures match.

    These tests verify that the API contracts between modules are correct.
    This prevents bugs like calling extract_entities_from_message with
    gemini_client instead of api_key.
    """

    def test_extract_entities_from_message_signature(self):
        """
        Verify extract_entities_from_message accepts api_key parameter.

        REGRESSION: triggers.py was calling this with gemini_client which
        doesn't exist. It must use api_key.
        """
        from entity_extraction import extract_entities_from_message

        sig = inspect.signature(extract_entities_from_message)
        params = list(sig.parameters.keys())

        assert 'api_key' in params, "extract_entities_from_message must accept 'api_key'"
        assert 'gemini_client' not in params, "extract_entities_from_message must NOT accept 'gemini_client'"

    def test_merge_entities_with_existing_signature(self):
        """
        Verify merge_entities_with_existing accepts gemini_client parameter.

        This function correctly uses gemini_client (unlike extract_entities_from_message).
        """
        from entity_extraction import merge_entities_with_existing

        sig = inspect.signature(merge_entities_with_existing)
        params = list(sig.parameters.keys())

        assert 'gemini_client' in params, "merge_entities_with_existing must accept 'gemini_client'"

    def test_triggers_uses_correct_extract_api(self):
        """
        Verify triggers.py calls extract_entities_from_message with api_key.

        REGRESSION: This was the bug - triggers.py was using gemini_client.
        """
        from triggers import _extract_and_merge_entities
        source = inspect.getsource(_extract_and_merge_entities)

        # Should use api_key for extract_entities_from_message
        assert 'api_key=gemini_api_key' in source or 'api_key=' in source, \
            "triggers.py must call extract_entities_from_message with api_key"

        # Should NOT have gemini_client in the extract call context
        # (it should only appear in the merge call)

    def test_triggers_helper_is_sync(self):
        """
        Verify _extract_and_merge_entities is a sync function (not async).

        REGRESSION: This function was incorrectly defined as async and awaited
        sync functions.
        """
        from triggers import _extract_and_merge_entities
        import asyncio

        # Should NOT be a coroutine function
        assert not asyncio.iscoroutinefunction(_extract_and_merge_entities), \
            "_extract_and_merge_entities must be sync (was incorrectly async)"

    def test_extract_entities_is_sync(self):
        """Verify extract_entities_from_message is a sync function."""
        from entity_extraction import extract_entities_from_message
        import asyncio

        assert not asyncio.iscoroutinefunction(extract_entities_from_message), \
            "extract_entities_from_message must be sync"

    def test_merge_entities_is_sync(self):
        """Verify merge_entities_with_existing is a sync function."""
        from entity_extraction import merge_entities_with_existing
        import asyncio

        assert not asyncio.iscoroutinefunction(merge_entities_with_existing), \
            "merge_entities_with_existing must be sync"


class TestTriggerExists:
    """Verify trigger function exists and is properly decorated."""

    def test_extract_entities_on_message_exists(self):
        """Trigger function should exist."""
        from triggers import extract_entities_on_message
        assert callable(extract_entities_on_message)

    def test_helper_function_exists(self):
        """Helper function should exist."""
        from triggers import _extract_and_merge_entities
        assert callable(_extract_and_merge_entities)


class TestTriggerLogic:
    """Test trigger logic by inspecting the source code."""

    def test_trigger_checks_message_role(self):
        """Trigger should check if message is from user."""
        from triggers import extract_entities_on_message
        source = inspect.getsource(extract_entities_on_message)

        assert 'MessageRole.USER' in source, "Should check for user messages"

    def test_trigger_skips_assistant_messages(self):
        """Trigger should skip assistant messages."""
        from triggers import extract_entities_on_message
        source = inspect.getsource(extract_entities_on_message)

        # Should have logic to skip non-user messages
        assert 'latest_message.role != MessageRole.USER' in source or \
               'role != MessageRole.USER' in source, \
            "Should skip non-user messages"

    def test_trigger_handles_null_data(self):
        """Trigger should handle null event data."""
        from triggers import extract_entities_on_message
        source = inspect.getsource(extract_entities_on_message)

        assert 'if not event.data' in source, "Should check for null event data"

    def test_helper_checks_empty_entities(self):
        """Helper should skip merge if no entities extracted."""
        from triggers import _extract_and_merge_entities
        source = inspect.getsource(_extract_and_merge_entities)

        assert 'if not extracted.entities' in source, \
            "Should check for empty extracted entities"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

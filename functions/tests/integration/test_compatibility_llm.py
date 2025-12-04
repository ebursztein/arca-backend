"""
Integration tests for compatibility LLM interpretation.

Tests real LLM calls for generating compatibility interpretations.
Run with: uv run pytest functions/tests/integration/test_compatibility_llm.py -v
"""

import pytest
import os

from compatibility import (
    get_compatibility_from_birth_data,
    CompatibilityData,
    CompatibilityResult,
)
from llm import generate_compatibility_result


@pytest.fixture
def api_key():
    """Get API key from environment."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        pytest.skip("GEMINI_API_KEY not set")
    return key


@pytest.fixture
def compatibility_data() -> CompatibilityData:
    """Pre-calculated compatibility data for romantic relationship."""
    return get_compatibility_from_birth_data(
        user_birth_date="1990-06-15",
        user_birth_time="14:30",
        user_birth_lat=40.7128,
        user_birth_lon=-74.0060,
        user_birth_timezone="America/New_York",
        connection_birth_date="1992-03-22",
        connection_birth_time="09:15",
        connection_birth_lat=34.0522,
        connection_birth_lon=-118.2437,
        connection_birth_timezone="America/Los_Angeles",
        relationship_type="romantic",
        user_name="Sarah",
        connection_name="Mike",
    )


class TestLLMFunctionImport:
    """Tests that LLM functions can be imported."""

    def test_import_generate_compatibility_result(self):
        """Should be able to import the function."""
        from llm import generate_compatibility_result
        assert callable(generate_compatibility_result)


class TestCompatibilityInterpretation:
    """Tests for real LLM compatibility interpretation."""

    def test_generates_valid_result(self, api_key, compatibility_data):
        """Real LLM should generate valid CompatibilityResult."""
        result = generate_compatibility_result(
            compatibility_data=compatibility_data,
            relationship_category="love",
            relationship_label="partner",
            api_key=api_key
        )

        # Should return a CompatibilityResult
        assert isinstance(result, CompatibilityResult)

        # Check required fields are present
        assert result.headline is not None
        assert result.summary is not None
        assert result.strengths is not None
        assert result.growth_areas is not None
        assert result.advice is not None
        assert result.mode is not None

    def test_headline_is_meaningful(self, api_key, compatibility_data):
        """Headline should be a meaningful string."""
        result = generate_compatibility_result(
            compatibility_data=compatibility_data,
            relationship_category="love",
            relationship_label="partner",
            api_key=api_key
        )

        assert isinstance(result.headline, str)
        assert len(result.headline) > 5  # More than just a few chars

    def test_romantic_has_category_insights(self, api_key, compatibility_data):
        """Romantic type should have category insights."""
        result = generate_compatibility_result(
            compatibility_data=compatibility_data,
            relationship_category="love",
            relationship_label="partner",
            api_key=api_key
        )

        # Should have categories in mode
        assert len(result.mode.categories) > 0
        # Each category should have an insight
        for cat in result.mode.categories:
            assert cat.insight is not None

    def test_includes_aspects(self, api_key, compatibility_data):
        """Should include aspects."""
        result = generate_compatibility_result(
            compatibility_data=compatibility_data,
            relationship_category="love",
            relationship_label="partner",
            api_key=api_key
        )

        assert result.aspects is not None
        assert isinstance(result.aspects, list)


class TestFriendshipCompatibility:
    """Tests for friendship compatibility."""

    @pytest.fixture
    def friendship_data(self) -> CompatibilityData:
        """Compatibility data for friendship."""
        return get_compatibility_from_birth_data(
            user_birth_date="1990-06-15",
            user_birth_time="14:30",
            user_birth_lat=40.7128,
            user_birth_lon=-74.0060,
            user_birth_timezone="America/New_York",
            connection_birth_date="1992-03-22",
            connection_birth_time="09:15",
            connection_birth_lat=34.0522,
            connection_birth_lon=-118.2437,
            connection_birth_timezone="America/Los_Angeles",
            relationship_type="friendship",
            user_name="Sarah",
            connection_name="Mike",
        )

    def test_friend_generates_valid_result(self, api_key, friendship_data):
        """Friend type should generate valid result."""
        result = generate_compatibility_result(
            compatibility_data=friendship_data,
            relationship_category="friend",
            relationship_label="friend",
            api_key=api_key
        )

        assert isinstance(result, CompatibilityResult)
        assert result.headline is not None


class TestCoworkerCompatibility:
    """Tests for coworker compatibility."""

    @pytest.fixture
    def coworker_data(self) -> CompatibilityData:
        """Compatibility data for coworker relationship."""
        return get_compatibility_from_birth_data(
            user_birth_date="1990-06-15",
            user_birth_time="14:30",
            user_birth_lat=40.7128,
            user_birth_lon=-74.0060,
            user_birth_timezone="America/New_York",
            connection_birth_date="1992-03-22",
            connection_birth_time="09:15",
            connection_birth_lat=34.0522,
            connection_birth_lon=-118.2437,
            connection_birth_timezone="America/Los_Angeles",
            relationship_type="coworker",
            user_name="Sarah",
            connection_name="Mike",
        )

    def test_coworker_generates_valid_result(self, api_key, coworker_data):
        """Coworker type should generate valid result."""
        result = generate_compatibility_result(
            compatibility_data=coworker_data,
            relationship_category="coworker",
            relationship_label="colleague",
            api_key=api_key
        )

        assert isinstance(result, CompatibilityResult)
        assert result.headline is not None


class TestSpecialCharacters:
    """Tests for special characters in names."""

    def test_handles_hyphenated_names(self, api_key):
        """Should handle hyphenated names."""
        data = get_compatibility_from_birth_data(
            user_birth_date="1990-06-15",
            user_birth_time="14:30",
            user_birth_lat=40.7128,
            user_birth_lon=-74.0060,
            user_birth_timezone="America/New_York",
            connection_birth_date="1992-03-22",
            connection_birth_time="09:15",
            connection_birth_lat=34.0522,
            connection_birth_lon=-118.2437,
            connection_birth_timezone="America/Los_Angeles",
            relationship_type="romantic",
            user_name="Marie-Claire",
            connection_name="Jean-Pierre",
        )

        result = generate_compatibility_result(
            compatibility_data=data,
            relationship_category="love",
            relationship_label="partner",
            api_key=api_key
        )

        assert result.headline is not None

    def test_handles_apostrophe_names(self, api_key):
        """Should handle names with apostrophes."""
        data = get_compatibility_from_birth_data(
            user_birth_date="1990-06-15",
            user_birth_time="14:30",
            user_birth_lat=40.7128,
            user_birth_lon=-74.0060,
            user_birth_timezone="America/New_York",
            connection_birth_date="1992-03-22",
            connection_birth_time="09:15",
            connection_birth_lat=34.0522,
            connection_birth_lon=-118.2437,
            connection_birth_timezone="America/Los_Angeles",
            relationship_type="romantic",
            user_name="Sarah",
            connection_name="O'Brien",
        )

        result = generate_compatibility_result(
            compatibility_data=data,
            relationship_category="love",
            relationship_label="partner",
            api_key=api_key
        )

        assert result.headline is not None

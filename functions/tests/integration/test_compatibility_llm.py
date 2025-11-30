"""
Integration tests for compatibility LLM interpretation.

Tests real LLM calls for generating compatibility interpretations.
Run with: uv run pytest functions/tests/integration/test_compatibility_llm.py -v
"""

import pytest
import os

from compatibility import (
    calculate_compatibility,
    CompatibilityResult,
)
from astro import compute_birth_chart, NatalChartData


@pytest.fixture
def api_key():
    """Get API key from environment."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        pytest.skip("GEMINI_API_KEY not set")
    return key


@pytest.fixture
def user_chart():
    """User's natal chart."""
    chart_dict, _ = compute_birth_chart(
        birth_date="1990-06-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )
    return NatalChartData(**chart_dict)


@pytest.fixture
def connection_chart():
    """Connection's natal chart."""
    chart_dict, _ = compute_birth_chart(
        birth_date="1992-03-22",
        birth_time="09:15",
        birth_timezone="America/Los_Angeles",
        birth_lat=34.0522,
        birth_lon=-118.2437
    )
    return NatalChartData(**chart_dict)


@pytest.fixture
def compatibility_result(user_chart, connection_chart):
    """Pre-calculated compatibility result."""
    return calculate_compatibility(user_chart, connection_chart)


class TestLLMFunctionImport:
    """Tests that LLM functions can be imported."""

    def test_import_generate_compatibility_interpretation(self):
        """Should be able to import the function."""
        from llm import generate_compatibility_interpretation
        assert callable(generate_compatibility_interpretation)


class TestCompatibilityInterpretation:
    """Tests for real LLM compatibility interpretation."""

    def test_generates_valid_interpretation(self, api_key, compatibility_result):
        """Real LLM should generate valid interpretation structure."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Sarah",
            user_sun_sign="gemini",
            connection_name="Mike",
            connection_sun_sign="aries",
            relationship_type="partner",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        # Check required fields are present
        assert "headline" in result
        assert "summary" in result
        assert "strengths" in result
        assert "growth_areas" in result
        assert "advice" in result
        assert "category_summaries" in result
        assert "aspect_interpretations" in result
        assert "model_used" in result
        assert "generation_time_ms" in result

    def test_headline_is_meaningful(self, api_key, compatibility_result):
        """Headline should be a meaningful string."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Sarah",
            user_sun_sign="gemini",
            connection_name="Mike",
            connection_sun_sign="aries",
            relationship_type="partner",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        assert isinstance(result["headline"], str)
        assert len(result["headline"]) > 5  # More than just a few chars

    def test_romantic_has_category_summaries(self, api_key, compatibility_result):
        """Romantic type should have romantic category summaries."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Sarah",
            user_sun_sign="gemini",
            connection_name="Mike",
            connection_sun_sign="aries",
            relationship_type="partner",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        category_summaries = result["category_summaries"]
        assert isinstance(category_summaries, dict)
        # Should have romantic categories
        romantic_categories = ["emotional", "communication", "attraction", "values", "longTerm", "growth"]
        for cat in romantic_categories:
            assert cat in category_summaries, f"Missing category: {cat}"

    def test_friend_has_friendship_categories(self, api_key, compatibility_result):
        """Friend type should have friendship category summaries."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Sarah",
            user_sun_sign="gemini",
            connection_name="Mike",
            connection_sun_sign="aries",
            relationship_type="friend",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        category_summaries = result["category_summaries"]
        # Should have friendship categories
        friendship_categories = ["emotional", "communication", "fun", "loyalty", "sharedInterests"]
        for cat in friendship_categories:
            assert cat in category_summaries, f"Missing category: {cat}"

    def test_coworker_has_work_categories(self, api_key, compatibility_result):
        """Coworker type should have work category summaries."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Sarah",
            user_sun_sign="gemini",
            connection_name="Mike",
            connection_sun_sign="aries",
            relationship_type="coworker",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        category_summaries = result["category_summaries"]
        # Should have coworker categories
        coworker_categories = ["communication", "collaboration", "reliability", "ambition", "powerDynamics"]
        for cat in coworker_categories:
            assert cat in category_summaries, f"Missing category: {cat}"

    def test_includes_aspect_interpretations(self, api_key, compatibility_result):
        """Should include aspect interpretations."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Sarah",
            user_sun_sign="gemini",
            connection_name="Mike",
            connection_sun_sign="aries",
            relationship_type="partner",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        aspect_interpretations = result["aspect_interpretations"]
        assert isinstance(aspect_interpretations, list)
        # Should have interpretations if there are aspects
        if len(compatibility_result.aspects) > 0:
            assert len(aspect_interpretations) > 0

    def test_generation_time_tracked(self, api_key, compatibility_result):
        """Generation time should be tracked in ms."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Sarah",
            user_sun_sign="gemini",
            connection_name="Mike",
            connection_sun_sign="aries",
            relationship_type="partner",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        assert "generation_time_ms" in result
        assert isinstance(result["generation_time_ms"], int)
        assert result["generation_time_ms"] > 0

    def test_model_name_returned(self, api_key, compatibility_result):
        """Model name should be returned."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Sarah",
            user_sun_sign="gemini",
            connection_name="Mike",
            connection_sun_sign="aries",
            relationship_type="partner",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        assert "model_used" in result
        assert "gemini" in result["model_used"]


class TestSpecialCharacters:
    """Tests for special characters in names."""

    def test_handles_hyphenated_names(self, api_key, compatibility_result):
        """Should handle hyphenated names."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Marie-Claire",
            user_sun_sign="gemini",
            connection_name="Jean-Pierre",
            connection_sun_sign="aries",
            relationship_type="partner",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        assert "headline" in result

    def test_handles_apostrophe_names(self, api_key, compatibility_result):
        """Should handle names with apostrophes."""
        from llm import generate_compatibility_interpretation

        result = generate_compatibility_interpretation(
            user_name="Sarah",
            user_sun_sign="gemini",
            connection_name="O'Brien",
            connection_sun_sign="aries",
            relationship_type="partner",
            compatibility_result=compatibility_result,
            api_key=api_key
        )

        assert "headline" in result

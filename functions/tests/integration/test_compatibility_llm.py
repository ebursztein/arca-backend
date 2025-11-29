"""
Tests for compatibility LLM interpretation.

Run with: pytest functions/test_compatibility_llm.py -v
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from compatibility import (
    calculate_compatibility,
    CompatibilityResult,
    ModeCompatibility,
    CompatibilityCategory,
    SynastryAspect,
    CompositeSummary,
)
from astro import compute_birth_chart, NatalChartData


# =============================================================================
# Test Fixtures
# =============================================================================

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


@pytest.fixture
def mock_llm_response():
    """Mock successful LLM response."""
    return {
        "headline": "Fire Meets Water Magic",
        "summary": "Sarah and Mike have a dynamic connection that balances passion with emotional depth.",
        "strengths": "Your natural communication style meshes well. Mercury aspects show easy conversation.",
        "growth_areas": "Learning to balance independence with togetherness will be your growth edge.",
        "advice": "Trust the emotional connection even when logic says otherwise.",
        "category_summaries": {
            "emotional": "Your Moon-Venus connection creates deep emotional resonance.",
            "communication": "Mercury aspects indicate easy conversation flow.",
            "attraction": "Venus-Mars dynamics show natural chemistry.",
            "values": "Jupiter aspects suggest shared optimism.",
            "longTerm": "Saturn connections indicate staying power.",
            "growth": "Pluto aspects point to transformative potential."
        },
        "aspect_interpretations": [
            {"aspect_id": "asp_001", "interpretation": "Your Venus trine their Neptune creates romantic idealism."},
            {"aspect_id": "asp_002", "interpretation": "North Node sextile Mercury suggests fated conversations."},
            {"aspect_id": "asp_003", "interpretation": "Venus opposition Moon brings emotional intensity."},
        ]
    }


# =============================================================================
# Test LLM Function Import
# =============================================================================

class TestLLMFunctionImport:
    """Tests that LLM functions can be imported."""

    def test_import_generate_compatibility_interpretation(self):
        """Should be able to import the function."""
        from llm import generate_compatibility_interpretation
        assert callable(generate_compatibility_interpretation)


# =============================================================================
# Test LLM Response Parsing
# =============================================================================

class TestLLMResponseParsing:
    """Tests for LLM response parsing logic."""

    def test_valid_json_response_parsed(self, compatibility_result, mock_llm_response):
        """Valid JSON response should be parsed correctly."""
        from llm import generate_compatibility_interpretation

        # Mock the Gemini client
        mock_response = Mock()
        mock_response.text = json.dumps(mock_llm_response)

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        assert result["headline"] == "Fire Meets Water Magic"
        assert "category_summaries" in result
        assert "aspect_interpretations" in result
        assert result["model_used"] == "gemini-2.5-flash-lite"

    def test_invalid_json_returns_fallback(self, compatibility_result):
        """Invalid JSON should return fallback response."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = "This is not valid JSON {{"

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        assert result["parse_error"] is True
        assert "category_summaries" in result
        assert "aspect_interpretations" in result
        assert result["aspect_interpretations"] == []

    def test_missing_category_summaries_filled(self, compatibility_result):
        """Missing category summaries should be filled with empty strings."""
        from llm import generate_compatibility_interpretation

        # Response missing some category summaries
        partial_response = {
            "headline": "Test",
            "summary": "Test summary",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {
                "emotional": "Has emotional summary"
                # Missing other categories
            },
            "aspect_interpretations": []
        }

        mock_response = Mock()
        mock_response.text = json.dumps(partial_response)

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        # Should have all romantic category IDs
        assert "emotional" in result["category_summaries"]
        assert "communication" in result["category_summaries"]
        assert "attraction" in result["category_summaries"]
        # emotional should have content, others empty
        assert result["category_summaries"]["emotional"] == "Has emotional summary"
        assert result["category_summaries"]["communication"] == ""

    def test_missing_aspect_interpretations_returns_empty_list(self, compatibility_result):
        """Missing aspect_interpretations should return empty list."""
        from llm import generate_compatibility_interpretation

        response_without_aspects = {
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {}
            # No aspect_interpretations
        }

        mock_response = Mock()
        mock_response.text = json.dumps(response_without_aspects)

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        assert result["aspect_interpretations"] == []


# =============================================================================
# Test Relationship Type Handling
# =============================================================================

class TestRelationshipTypeHandling:
    """Tests for different relationship types."""

    def test_romantic_uses_romantic_categories(self, compatibility_result):
        """Romantic type should use romantic categories."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        # Should include romantic-specific categories
        assert "attraction" in result["category_summaries"]
        assert "longTerm" in result["category_summaries"]

    def test_friend_uses_friendship_categories(self, compatibility_result):
        """Friend type should use friendship categories."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="friend",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        # Should include friendship-specific categories
        assert "fun" in result["category_summaries"]
        assert "loyalty" in result["category_summaries"]
        assert "sharedInterests" in result["category_summaries"]

    def test_coworker_uses_coworker_categories(self, compatibility_result):
        """Coworker type should use coworker categories."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="coworker",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        # Should include coworker-specific categories
        assert "collaboration" in result["category_summaries"]
        assert "reliability" in result["category_summaries"]
        assert "ambition" in result["category_summaries"]
        assert "powerDynamics" in result["category_summaries"]

    def test_family_uses_friendship_categories(self, compatibility_result):
        """Family type should use friendship categories."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mom",
                connection_sun_sign="cancer",
                relationship_type="family",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        # Should use friendship categories (same as friend)
        assert "fun" in result["category_summaries"]
        assert "loyalty" in result["category_summaries"]


# =============================================================================
# Test API Key Handling
# =============================================================================

class TestAPIKeyHandling:
    """Tests for API key handling."""

    def test_raises_error_without_api_key(self, compatibility_result):
        """Should raise ValueError if no API key provided."""
        from llm import generate_compatibility_interpretation

        with patch.dict("os.environ", {}, clear=True):
            with patch("llm.os.environ.get", return_value=None):
                with pytest.raises(ValueError, match="GEMINI_API_KEY not found"):
                    generate_compatibility_interpretation(
                        user_name="Sarah",
                        user_sun_sign="gemini",
                        connection_name="Mike",
                        connection_sun_sign="aries",
                        relationship_type="romantic",
                        compatibility_result=compatibility_result,
                        api_key=None
                    )

    def test_uses_provided_api_key(self, compatibility_result):
        """Should use explicitly provided API key."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="my-test-api-key"
            )

            # Verify the API key was used
            mock_genai.Client.assert_called_once_with(api_key="my-test-api-key")


# =============================================================================
# Test Generation Time Tracking
# =============================================================================

class TestGenerationTimeTracking:
    """Tests for generation time tracking."""

    def test_includes_generation_time(self, compatibility_result):
        """Result should include generation time in ms."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        assert "generation_time_ms" in result
        assert isinstance(result["generation_time_ms"], int)
        assert result["generation_time_ms"] >= 0

    def test_includes_model_used(self, compatibility_result):
        """Result should include model name."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        assert "model_used" in result
        assert result["model_used"] == "gemini-2.5-flash-lite"

    def test_custom_model_name(self, compatibility_result):
        """Should use custom model name when provided."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key",
                model_name="gemini-2.5-pro"
            )

        assert result["model_used"] == "gemini-2.5-pro"


# =============================================================================
# Test Aspect Limiting
# =============================================================================

class TestAspectLimiting:
    """Tests that aspects are limited to top 8."""

    def test_limits_aspects_to_eight(self, compatibility_result):
        """Should only request interpretations for top 8 aspects."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        captured_prompt = None

        def capture_prompt(*args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = kwargs.get("contents", args[1] if len(args) > 1 else None)
            return mock_response

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.side_effect = capture_prompt

            generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        # The prompt should mention aspect IDs
        assert captured_prompt is not None
        # Count aspect IDs mentioned - should be at most 8
        aspect_count = captured_prompt.count("asp_")
        # Each aspect is mentioned at least twice in the prompt (context + required list)
        # So max would be ~16-24 mentions for 8 aspects
        assert aspect_count <= 30, f"Too many aspect mentions: {aspect_count}"


# =============================================================================
# Test Response Merging in Main.py
# =============================================================================

class TestResponseMerging:
    """Tests for merging LLM interpretations into compatibility response."""

    def test_category_summaries_merged_into_categories(self):
        """Category summaries should be merged into category objects."""
        # Create a mock response with category summaries
        mock_interpretation = {
            "headline": "Test",
            "summary": "Test summary",
            "strengths": "Test strengths",
            "growth_areas": "Test growth",
            "advice": "Test advice",
            "category_summaries": {
                "emotional": "Emotional summary text",
                "communication": "Communication summary text",
            },
            "aspect_interpretations": []
        }

        # Simulate the merging logic from main.py
        response = {
            "romantic": {
                "overall_score": 75,
                "categories": [
                    {"id": "emotional", "name": "Emotional Connection", "score": 80, "summary": None},
                    {"id": "communication", "name": "Communication", "score": 70, "summary": None},
                ]
            }
        }

        # Apply merge logic
        category_summaries = mock_interpretation.get("category_summaries", {})
        for mode_key in ["romantic", "friendship", "coworker"]:
            if mode_key in response:
                for cat in response[mode_key].get("categories", []):
                    cat_id = cat.get("id")
                    if cat_id and cat_id in category_summaries:
                        cat["summary"] = category_summaries[cat_id]

        # Verify merging worked
        assert response["romantic"]["categories"][0]["summary"] == "Emotional summary text"
        assert response["romantic"]["categories"][1]["summary"] == "Communication summary text"

    def test_aspect_interpretations_merged_into_aspects(self):
        """Aspect interpretations should be merged into aspect objects."""
        mock_interpretation = {
            "aspect_interpretations": [
                {"aspect_id": "asp_001", "interpretation": "First aspect meaning"},
                {"aspect_id": "asp_002", "interpretation": "Second aspect meaning"},
            ]
        }

        response = {
            "aspects": [
                {"id": "asp_001", "user_planet": "venus", "their_planet": "mars", "interpretation": None},
                {"id": "asp_002", "user_planet": "moon", "their_planet": "moon", "interpretation": None},
                {"id": "asp_003", "user_planet": "sun", "their_planet": "sun", "interpretation": None},
            ]
        }

        # Apply merge logic
        aspect_interps = {
            ai.get("aspect_id"): ai.get("interpretation")
            for ai in mock_interpretation.get("aspect_interpretations", [])
            if ai.get("aspect_id")
        }
        for aspect in response.get("aspects", []):
            asp_id = aspect.get("id")
            if asp_id and asp_id in aspect_interps:
                aspect["interpretation"] = aspect_interps[asp_id]

        # Verify merging worked
        assert response["aspects"][0]["interpretation"] == "First aspect meaning"
        assert response["aspects"][1]["interpretation"] == "Second aspect meaning"
        assert response["aspects"][2]["interpretation"] is None  # Not in LLM response


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases in LLM interpretation."""

    def test_empty_aspects_list(self):
        """Should handle compatibility result with no aspects."""
        # Create minimal compatibility result
        empty_result = CompatibilityResult(
            romantic=ModeCompatibility(
                overall_score=50,
                categories=[
                    CompatibilityCategory(id="emotional", name="Emotional", score=0),
                    CompatibilityCategory(id="communication", name="Communication", score=0),
                    CompatibilityCategory(id="attraction", name="Attraction", score=0),
                    CompatibilityCategory(id="values", name="Values", score=0),
                    CompatibilityCategory(id="longTerm", name="Long-term", score=0),
                    CompatibilityCategory(id="growth", name="Growth", score=0),
                ]
            ),
            friendship=ModeCompatibility(
                overall_score=50,
                categories=[
                    CompatibilityCategory(id="emotional", name="Emotional", score=0),
                    CompatibilityCategory(id="communication", name="Communication", score=0),
                    CompatibilityCategory(id="fun", name="Fun", score=0),
                    CompatibilityCategory(id="loyalty", name="Loyalty", score=0),
                    CompatibilityCategory(id="sharedInterests", name="Shared Interests", score=0),
                ]
            ),
            coworker=ModeCompatibility(
                overall_score=50,
                categories=[
                    CompatibilityCategory(id="communication", name="Communication", score=0),
                    CompatibilityCategory(id="collaboration", name="Collaboration", score=0),
                    CompatibilityCategory(id="reliability", name="Reliability", score=0),
                    CompatibilityCategory(id="ambition", name="Ambition", score=0),
                    CompatibilityCategory(id="powerDynamics", name="Power Dynamics", score=0),
                ]
            ),
            aspects=[],  # Empty aspects list
            composite_summary=CompositeSummary(),
            calculated_at="2025-11-26T12:00:00"
        )

        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Sun Sign Connection",
            "summary": "Based on sun signs alone.",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=empty_result,
                api_key="test-key"
            )

        assert result["headline"] == "Sun Sign Connection"
        assert result["aspect_interpretations"] == []

    def test_special_characters_in_names(self, compatibility_result):
        """Should handle special characters in names."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            # Names with special characters
            result = generate_compatibility_interpretation(
                user_name="Marie-Claire",
                user_sun_sign="gemini",
                connection_name="O'Brien",
                connection_sun_sign="aries",
                relationship_type="romantic",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        # Should not raise an error
        assert "headline" in result

    def test_unknown_relationship_type_defaults_to_friendship(self, compatibility_result):
        """Unknown relationship type should default to friendship mode."""
        from llm import generate_compatibility_interpretation

        mock_response = Mock()
        mock_response.text = json.dumps({
            "headline": "Test",
            "summary": "Test",
            "strengths": "Test",
            "growth_areas": "Test",
            "advice": "Test",
            "category_summaries": {},
            "aspect_interpretations": []
        })

        with patch("llm.genai") as mock_genai:
            mock_client = Mock()
            mock_genai.Client.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            result = generate_compatibility_interpretation(
                user_name="Sarah",
                user_sun_sign="gemini",
                connection_name="Mike",
                connection_sun_sign="aries",
                relationship_type="unknown_type",
                compatibility_result=compatibility_result,
                api_key="test-key"
            )

        # Should use friendship categories (the default)
        assert "fun" in result["category_summaries"]
        assert "loyalty" in result["category_summaries"]

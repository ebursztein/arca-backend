"""
Unit tests for llm.py logic without network calls.
Tests prompt construction, response parsing, and error handling.
"""

import pytest
import json
import os
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime
from google.genai import types

from llm import (
    generate_daily_horoscope,
    generate_natal_chart_summary,
    select_featured_relationship,
    select_featured_connection
)
from models import (
    UserProfile,
    MemoryCollection,
    DailyHoroscope,
    Entity,
    EntityCategory,
    RelationshipMention,
    ConnectionMention,
    ActionableAdvice,
)
from astro import (
    compute_birth_chart,
    get_sun_sign,
    get_sun_sign_profile,
    SunSignProfile,
    ZodiacSign,
    Element,
    Modality
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_genai_client():
    """Mock the Google GenAI Client."""
    with patch("llm.genai.Client") as MockClient:
        client_instance = MockClient.return_value
        yield client_instance


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile."""
    natal_chart, is_exact = compute_birth_chart("1990-06-15")
    return UserProfile(
        user_id="test_user_123",
        name="Test User",
        email="test@example.com",
        birth_date="1990-06-15",
        sun_sign="gemini",
        natal_chart=natal_chart,
        exact_chart=is_exact,
        created_at=datetime.now().isoformat(),
        last_active=datetime.now().isoformat()
    )


@pytest.fixture
def sample_sun_sign_profile():
    """Create a sample sun sign profile."""
    # We can use the real one since it just loads JSON
    return get_sun_sign_profile(ZodiacSign.GEMINI)


@pytest.fixture
def sample_memory():
    """Create a sample memory collection."""
    return MemoryCollection(
        user_id="test_user_123",
        categories={},
        relationship_mentions=[],
        connection_mentions=[],
        updated_at=datetime.now().isoformat()
    )


@pytest.fixture
def sample_transit_summary():
    """Create a sample transit summary dict."""
    return {
        "priority_transits": [
            {
                "description": "Transit Sun conjunct Natal Sun",
                "intensity_indicator": "⚡⚡⚡",
                "intensity_label": "High",
                "priority_score": 95,
                "orb": 0.5,
                "orb_label": "Exact",
                "applying_label": "Exact",
                "speed_timing": {},
                "meaning": "Solar Return"
            }
        ],
        "critical_degree_alerts": [],
        "critical_degree_synthesis": {},
        "theme_synthesis": {},
        "retrograde_planets": [],
        "planet_positions": {},
        "total_aspects_found": 1
    }


@pytest.fixture
def mock_llm_response_json():
    """Mock valid JSON response from LLM."""
    return {
        "technical_analysis": "Sun is conjunct Sun today.",
        "lunar_cycle_update": "Moon is waxing.",
        "daily_theme_headline": "Happy Birthday",
        "daily_overview": "It is your solar return.",
        "actionable_advice": {
            "do": "Celebrate yourself",
            "dont": "Hide away",
            "reflect_on": "Your year ahead"
        },
        "mind_interpretation": "Mind is clear.",
        "heart_interpretation": "Heart is full.",
        "body_interpretation": "Body is strong.",
        "instincts_interpretation": "Instincts are sharp.",
        "growth_interpretation": "Growth is happening.",
        "look_ahead_preview": "Tomorrow looks good.",
        "energy_rhythm": "High energy.",
        "relationship_weather": {
            "overview": "Relationships are harmonious.",
            "connection_vibe": None
        },
        "collective_energy": "Everyone is happy.",
        "follow_up_questions": ["What is your wish?"]
    }


# =============================================================================
# Tests for generate_daily_horoscope
# =============================================================================

def test_generate_daily_horoscope_success(
    mock_genai_client,
    sample_user_profile,
    sample_sun_sign_profile,
    sample_transit_summary,
    sample_memory,
    mock_llm_response_json
):
    """Test successful horoscope generation with mocked LLM."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_llm_response_json)
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.model_dump.return_value = {"total_tokens": 100, "prompt_tokens": 50, "candidates_tokens": 50}

    # Setup parsed response (Pydantic model style)
    mock_parsed = MagicMock()
    mock_parsed.technical_analysis = mock_llm_response_json["technical_analysis"]
    mock_parsed.lunar_cycle_update = mock_llm_response_json["lunar_cycle_update"]
    mock_parsed.daily_theme_headline = mock_llm_response_json["daily_theme_headline"]
    mock_parsed.daily_overview = mock_llm_response_json["daily_overview"]

    # Use real ActionableAdvice object
    mock_parsed.actionable_advice = ActionableAdvice(
        do=mock_llm_response_json["actionable_advice"]["do"],
        dont=mock_llm_response_json["actionable_advice"]["dont"],
        reflect_on=mock_llm_response_json["actionable_advice"]["reflect_on"]
    )

    mock_parsed.mind_interpretation = mock_llm_response_json["mind_interpretation"]
    mock_parsed.heart_interpretation = mock_llm_response_json["heart_interpretation"]
    mock_parsed.body_interpretation = mock_llm_response_json["body_interpretation"]
    mock_parsed.instincts_interpretation = mock_llm_response_json["instincts_interpretation"]
    mock_parsed.growth_interpretation = mock_llm_response_json["growth_interpretation"]
    mock_parsed.look_ahead_preview = mock_llm_response_json["look_ahead_preview"]
    mock_parsed.energy_rhythm = mock_llm_response_json["energy_rhythm"]

    # relationship_weather is now a nested object with overview + connection_vibe
    mock_relationship_weather = MagicMock()
    mock_relationship_weather.overview = mock_llm_response_json["relationship_weather"]["overview"]
    mock_relationship_weather.connection_vibe = mock_llm_response_json["relationship_weather"]["connection_vibe"]
    mock_parsed.relationship_weather = mock_relationship_weather

    mock_parsed.collective_energy = mock_llm_response_json["collective_energy"]
    mock_parsed.follow_up_questions = mock_llm_response_json["follow_up_questions"]

    # Add model_dump_json method to parsed object
    mock_parsed.model_dump_json.return_value = json.dumps(mock_llm_response_json)

    mock_response.parsed = mock_parsed

    mock_genai_client.models.generate_content.return_value = mock_response

    # Call function
    with patch("os.environ.get") as mock_env:
        mock_env.side_effect = lambda k, default=None: "dummy_key" if "API_KEY" in k else default

        horoscope = generate_daily_horoscope(
            date="2025-01-01",
            user_profile=sample_user_profile,
            sun_sign_profile=sample_sun_sign_profile,
            transit_summary=sample_transit_summary,
            memory=sample_memory,
            api_key="test_key",
            posthog_api_key="test_ph_key"
        )

    # Verify results
    assert isinstance(horoscope, DailyHoroscope)
    assert horoscope.daily_theme_headline == "Happy Birthday"
    assert horoscope.moon_detail.interpretation == "Moon is waxing."
    assert horoscope.astrometers.groups[0].interpretation == "Mind is clear."

    # Verify LLM was called with correct model
    mock_genai_client.models.generate_content.assert_called_once()
    call_args = mock_genai_client.models.generate_content.call_args
    assert call_args.kwargs["model"] == "gemini-2.5-flash-lite"

    # Verify prompt contains key info
    prompt_content = call_args.kwargs["contents"]
    assert "Gemini" in prompt_content # User's sign
    assert "Test User" in prompt_content # User's name


def test_generate_daily_horoscope_posthog_logging(
    mock_genai_client,
    sample_user_profile,
    sample_sun_sign_profile,
    sample_transit_summary,
    sample_memory,
    mock_llm_response_json
):
    """Test that PostHog capture is called."""
    # Setup mock response (same as above)
    mock_response = MagicMock()
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.model_dump.return_value = {"total_tokens": 100, "prompt_tokens": 50, "candidates_tokens": 50}

    mock_response.parsed = MagicMock()
    # Minimal population to avoid AttributeError
    mock_response.parsed.daily_theme_headline = "Test"
    mock_response.parsed.daily_overview = "Test"

    # Use real ActionableAdvice object
    mock_response.parsed.actionable_advice = ActionableAdvice(
        do="Test",
        dont="Test",
        reflect_on="Test"
    )

    mock_response.parsed.mind_interpretation = ""
    mock_response.parsed.heart_interpretation = ""
    mock_response.parsed.body_interpretation = ""
    mock_response.parsed.instincts_interpretation = ""
    mock_response.parsed.growth_interpretation = ""
    mock_response.parsed.look_ahead_preview = ""
    mock_response.parsed.energy_rhythm = ""

    # relationship_weather is now a nested object
    mock_relationship_weather = MagicMock()
    mock_relationship_weather.overview = "Test relationship weather"  # Must be non-empty
    mock_relationship_weather.connection_vibe = None
    mock_response.parsed.relationship_weather = mock_relationship_weather

    mock_response.parsed.collective_energy = "Test"
    mock_response.parsed.follow_up_questions = []
    mock_response.parsed.technical_analysis = ""
    mock_response.parsed.lunar_cycle_update = ""
    mock_response.parsed.model_dump_json.return_value = "{}"

    mock_genai_client.models.generate_content.return_value = mock_response

    with patch("llm.capture_llm_generation") as mock_capture:
        with patch("os.environ.get") as mock_env:
            mock_env.side_effect = lambda k, default=None: "dummy_key" if "API_KEY" in k else default

            generate_daily_horoscope(
                date="2025-01-01",
                user_profile=sample_user_profile,
                sun_sign_profile=sample_sun_sign_profile,
                transit_summary=sample_transit_summary,
                memory=sample_memory,
                api_key="test_key",
                posthog_api_key="test_ph_key"
            )

        mock_capture.assert_called_once()
        assert mock_capture.call_args.kwargs["distinct_id"] == "test_user_123"
        assert mock_capture.call_args.kwargs["generation_type"] == "daily_horoscope"


# =============================================================================
# Tests for Selection Logic
# =============================================================================

def test_select_featured_relationship_logic(sample_memory):
    """Test logic for selecting featured relationship."""
    date = "2025-01-01"

    # Create entities
    e1 = Entity(entity_id="1", name="Partner", entity_type="relationship", category=EntityCategory.PARTNER, importance_score=0.9, first_seen="", last_seen="", created_at="", updated_at="")
    e2 = Entity(entity_id="2", name="Mom", entity_type="relationship", category=EntityCategory.FAMILY, importance_score=0.8, first_seen="", last_seen="", created_at="", updated_at="")
    e3 = Entity(entity_id="3", name="Boss", entity_type="relationship", category=EntityCategory.COWORKER, importance_score=0.5, first_seen="", last_seen="", created_at="", updated_at="")
    
    entities = [e1, e2, e3]
    
    # 1. No history -> should pick highest importance (Partner)
    selected = select_featured_relationship(entities, sample_memory, date)
    assert selected.entity_id == "1"
    
    # 2. Partner recently featured -> should pick Mom
    sample_memory.relationship_mentions.append(
        RelationshipMention(entity_id="1", entity_name="Partner", category=EntityCategory.PARTNER, date="2024-12-31", context="")
    )
    selected = select_featured_relationship(entities, sample_memory, date)
    assert selected.entity_id == "2"
    
    # 3. Partner and Mom recently featured -> should pick Boss
    sample_memory.relationship_mentions.append(
        RelationshipMention(entity_id="2", entity_name="Mom", category=EntityCategory.FAMILY, date="2024-12-30", context="")
    )
    selected = select_featured_relationship(entities, sample_memory, date)
    assert selected.entity_id == "3"
    
    # 4. All recently featured -> should pick oldest mentioned (Mom from 12-30 vs Partner 12-31 vs Boss just now?)
    # Wait, let's add Boss to history too
    sample_memory.relationship_mentions.append(
        RelationshipMention(entity_id="3", entity_name="Boss", category=EntityCategory.COWORKER, date="2025-01-01", context="")
    )
    # Now logic: all in recent mentions. Sort by mention date.
    # Mom (12-30), Partner (12-31), Boss (01-01). Oldest is Mom.
    selected = select_featured_relationship(entities, sample_memory, date)
    assert selected.entity_id == "2"


class TestSelectFeaturedConnection:
    """Test suite for select_featured_connection with 7-day gap and randomness."""

    def test_no_connections_returns_none(self, sample_memory):
        """Empty connections list returns None."""
        selected = select_featured_connection([], sample_memory, "2025-01-15")
        assert selected is None

    def test_no_history_selects_randomly(self, sample_memory):
        """With no mention history, randomly selects from all connections."""
        connections = [
            {"connection_id": "c1", "name": "Friend A"},
            {"connection_id": "c2", "name": "Friend B"},
            {"connection_id": "c3", "name": "Friend C"},
        ]

        # Run multiple times to verify randomness (should not always pick same one)
        # Also accounts for 20% skip rate
        selected_ids = set()
        for _ in range(50):
            selected = select_featured_connection(connections, sample_memory, "2025-01-15")
            if selected:
                selected_ids.add(selected["connection_id"])

        # With 50 runs and 3 options, should see at least 2 different selections
        # (statistically almost certain unless broken)
        assert len(selected_ids) >= 2, "Should randomly select different connections"

    def test_7_day_gap_enforced(self, sample_memory):
        """Connection mentioned within 7 days is not eligible."""
        connections = [
            {"connection_id": "c1", "name": "Friend A"},
            {"connection_id": "c2", "name": "Friend B"},
        ]

        # Mention c1 3 days ago (within 7 days)
        sample_memory.connection_mentions.append(
            ConnectionMention(
                connection_id="c1",
                connection_name="Friend A",
                relationship_category="friend",
                relationship_label="friend",
                date="2025-01-12",  # 3 days before test date
                context=""
            )
        )

        # Run multiple times - should only ever pick c2 (when not skipped)
        for _ in range(20):
            selected = select_featured_connection(connections, sample_memory, "2025-01-15")
            if selected:
                assert selected["connection_id"] == "c2", "Should not select c1 (mentioned 3 days ago)"

    def test_connection_eligible_after_7_days(self, sample_memory):
        """Connection mentioned 8+ days ago is eligible again."""
        connections = [
            {"connection_id": "c1", "name": "Friend A"},
        ]

        # Mention c1 8 days ago (outside 7-day window)
        sample_memory.connection_mentions.append(
            ConnectionMention(
                connection_id="c1",
                connection_name="Friend A",
                relationship_category="friend",
                relationship_label="friend",
                date="2025-01-07",  # 8 days before test date
                context=""
            )
        )

        # Should be able to select c1 again (when not skipped)
        selected_count = 0
        for _ in range(20):
            selected = select_featured_connection(connections, sample_memory, "2025-01-15")
            if selected:
                selected_count += 1
                assert selected["connection_id"] == "c1"

        # Should have selected at least some times (accounting for 20% skip)
        assert selected_count > 0, "Should be able to select c1 after 8 days"

    def test_all_connections_within_7_days_returns_none(self, sample_memory):
        """When all connections were mentioned within 7 days, returns None."""
        connections = [
            {"connection_id": "c1", "name": "Friend A"},
            {"connection_id": "c2", "name": "Friend B"},
        ]

        # Both mentioned within 7 days
        sample_memory.connection_mentions.extend([
            ConnectionMention(
                connection_id="c1",
                connection_name="Friend A",
                relationship_category="friend",
                relationship_label="friend",
                date="2025-01-14",
                context=""
            ),
            ConnectionMention(
                connection_id="c2",
                connection_name="Friend B",
                relationship_category="friend",
                relationship_label="friend",
                date="2025-01-13",
                context=""
            ),
        ])

        # Should always return None (all ineligible)
        for _ in range(20):
            selected = select_featured_connection(connections, sample_memory, "2025-01-15")
            assert selected is None, "Should return None when all connections are within 7-day window"

    def test_20_percent_skip_rate(self, sample_memory):
        """Approximately 20% of calls should return None (skip feature)."""
        connections = [
            {"connection_id": "c1", "name": "Friend A"},
            {"connection_id": "c2", "name": "Friend B"},
            {"connection_id": "c3", "name": "Friend C"},
        ]

        # Run many times to verify skip rate
        skip_count = 0
        total_runs = 500

        for _ in range(total_runs):
            selected = select_featured_connection(connections, sample_memory, "2025-01-15")
            if selected is None:
                skip_count += 1

        # 20% skip rate means ~100 skips out of 500
        # Allow range of 10%-30% to account for randomness
        skip_rate = skip_count / total_runs
        assert 0.10 <= skip_rate <= 0.30, f"Skip rate {skip_rate:.1%} should be ~20%"

    def test_mixed_eligibility(self, sample_memory):
        """With some connections eligible and some not, only eligible ones are selected."""
        connections = [
            {"connection_id": "c1", "name": "Friend A"},  # Will be ineligible
            {"connection_id": "c2", "name": "Friend B"},  # Eligible
            {"connection_id": "c3", "name": "Friend C"},  # Will be ineligible
            {"connection_id": "c4", "name": "Friend D"},  # Eligible
        ]

        # Mark c1 and c3 as recently mentioned
        sample_memory.connection_mentions.extend([
            ConnectionMention(
                connection_id="c1",
                connection_name="Friend A",
                relationship_category="friend",
                relationship_label="friend",
                date="2025-01-14",
                context=""
            ),
            ConnectionMention(
                connection_id="c3",
                connection_name="Friend C",
                relationship_category="friend",
                relationship_label="friend",
                date="2025-01-10",
                context=""
            ),
        ])

        # Should only select c2 or c4
        selected_ids = set()
        for _ in range(50):
            selected = select_featured_connection(connections, sample_memory, "2025-01-15")
            if selected:
                selected_ids.add(selected["connection_id"])

        assert selected_ids <= {"c2", "c4"}, f"Should only select eligible connections, got {selected_ids}"
        assert len(selected_ids) == 2, "Should select both eligible connections over time"

    def test_invalid_date_in_mentions_handled(self, sample_memory):
        """Invalid date formats in mentions are gracefully skipped."""
        connections = [
            {"connection_id": "c1", "name": "Friend A"},
        ]

        # Add mention with invalid date
        sample_memory.connection_mentions.append(
            ConnectionMention(
                connection_id="c1",
                connection_name="Friend A",
                relationship_category="friend",
                relationship_label="friend",
                date="invalid-date",  # Invalid format
                context=""
            )
        )

        # Should not crash, and c1 should be selectable (invalid date is ignored)
        selected_count = 0
        for _ in range(20):
            selected = select_featured_connection(connections, sample_memory, "2025-01-15")
            if selected:
                selected_count += 1
                assert selected["connection_id"] == "c1"

        assert selected_count > 0, "Should handle invalid dates gracefully"

    def test_exactly_7_days_ago_is_eligible(self, sample_memory):
        """Connection mentioned exactly 7 days ago should be eligible (>7 days check)."""
        connections = [
            {"connection_id": "c1", "name": "Friend A"},
        ]

        # Mention exactly 7 days ago
        sample_memory.connection_mentions.append(
            ConnectionMention(
                connection_id="c1",
                connection_name="Friend A",
                relationship_category="friend",
                relationship_label="friend",
                date="2025-01-08",  # Exactly 7 days before 2025-01-15
                context=""
            )
        )

        # Should be eligible (the check is > one_week_ago, so exactly 7 days is eligible)
        selected_count = 0
        for _ in range(20):
            selected = select_featured_connection(connections, sample_memory, "2025-01-15")
            if selected:
                selected_count += 1

        assert selected_count > 0, "Exactly 7 days ago should be eligible"


# =============================================================================
# Tests for generate_natal_chart_summary
# =============================================================================

def test_generate_natal_chart_summary_success(
    mock_genai_client,
    sample_user_profile,
    sample_sun_sign_profile
):
    """Test natal chart summary generation."""
    mock_response = MagicMock()
    mock_response.text = "You are a Gemini Sun with..."
    mock_genai_client.models.generate_content.return_value = mock_response
    
    with patch("os.environ.get") as mock_env:
        mock_env.side_effect = lambda k, default=None: "dummy_key" if "API_KEY" in k else default

        summary = generate_natal_chart_summary(
            chart_dict=sample_user_profile.natal_chart,
            sun_sign_profile=sample_sun_sign_profile,
            user_name="Test User",
            api_key="test_key"
        )
    
    assert summary == "You are a Gemini Sun with..."
    
    # Verify prompt
    call_args = mock_genai_client.models.generate_content.call_args
    prompt = call_args.kwargs["contents"]
    assert "Test User" in prompt
    assert "Gemini" in prompt
    assert "Sun Sign: Gemini" in prompt

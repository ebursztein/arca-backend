"""
Tests for headline generation system.

Tests cover:
- Headline examples JSON structure
- Mode selection determinism
- Pattern classification
- Integration with meters
"""

import json
from pathlib import Path
import pytest


def load_headline_examples():
    """Load headline examples from JSON file."""
    labels_dir = Path(__file__).parent.parent / "labels"
    with open(labels_dir / "headline_examples.json") as f:
        return json.load(f)


class TestHeadlineExamplesStructure:
    """Test headline_examples.json has correct structure."""

    def test_has_three_modes(self):
        """Test all three voice modes exist."""
        examples = load_headline_examples()
        assert "modes" in examples
        assert set(examples["modes"].keys()) == {"provocative", "personalized", "imperative"}

    def test_each_mode_has_required_fields(self):
        """Test each mode has style, formula, rules, and examples."""
        examples = load_headline_examples()
        required_fields = {"style", "formula", "rules", "examples"}

        for mode_name, mode_data in examples["modes"].items():
            for field in required_fields:
                assert field in mode_data, f"{mode_name} missing {field}"

    def test_each_mode_has_five_patterns(self):
        """Test each mode has all five pattern examples."""
        examples = load_headline_examples()
        required_patterns = {"one_positive", "two_positive", "one_negative", "two_negative", "contrast"}

        for mode_name, mode_data in examples["modes"].items():
            assert set(mode_data["examples"].keys()) == required_patterns, \
                f"{mode_name} missing pattern examples"

    def test_rules_are_lists(self):
        """Test rules are non-empty lists."""
        examples = load_headline_examples()

        for mode_name, mode_data in examples["modes"].items():
            assert isinstance(mode_data["rules"], list), f"{mode_name} rules should be list"
            assert len(mode_data["rules"]) > 0, f"{mode_name} rules should not be empty"


class TestModeCharacteristics:
    """Test each mode follows its own rules."""

    def test_provocative_uses_name(self):
        """Test provocative examples use a name (Maya)."""
        examples = load_headline_examples()
        mode = examples["modes"]["provocative"]

        for pattern, example in mode["examples"].items():
            assert "Maya" in example, \
                f"provocative.{pattern} should use name: {example}"

    def test_provocative_no_emoji(self):
        """Test provocative examples have no emoji."""
        examples = load_headline_examples()
        mode = examples["modes"]["provocative"]
        # Common emoji ranges
        emoji_chars = set("".join(chr(i) for i in range(0x1F300, 0x1F9FF)))

        for pattern, example in mode["examples"].items():
            has_emoji = any(c in emoji_chars for c in example)
            assert not has_emoji, \
                f"provocative.{pattern} should not have emoji: {example}"

    def test_personalized_has_planet(self):
        """Test personalized examples reference a planet."""
        examples = load_headline_examples()
        mode = examples["modes"]["personalized"]
        planets = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Neptune", "Uranus", "Pluto", "Moon", "Sun"]

        for pattern, example in mode["examples"].items():
            has_planet = any(planet in example for planet in planets)
            assert has_planet, \
                f"personalized.{pattern} should reference a planet: {example}"

    def test_personalized_no_name(self):
        """Test personalized examples don't use name (that's provocative mode)."""
        examples = load_headline_examples()
        mode = examples["modes"]["personalized"]

        for pattern, example in mode["examples"].items():
            assert "Maya" not in example, \
                f"personalized.{pattern} should not use name: {example}"

    def test_personalized_uses_you_or_your(self):
        """Test personalized examples use you/your."""
        examples = load_headline_examples()
        mode = examples["modes"]["personalized"]

        for pattern, example in mode["examples"].items():
            has_you = "you" in example.lower() or "your" in example.lower()
            assert has_you, \
                f"personalized.{pattern} should use you/your: {example}"

    def test_imperative_starts_with_emoji(self):
        """Test imperative examples start with emoji."""
        examples = load_headline_examples()
        mode = examples["modes"]["imperative"]

        for pattern, example in mode["examples"].items():
            # Check first character is not ASCII letter
            first_char = example[0]
            assert not first_char.isascii() or not first_char.isalpha(), \
                f"imperative.{pattern} should start with emoji: {example}"

    def test_imperative_no_planet(self):
        """Test imperative examples don't mention planets (behavior-focused)."""
        examples = load_headline_examples()
        mode = examples["modes"]["imperative"]
        planets = ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Neptune", "Uranus", "Pluto"]

        for pattern, example in mode["examples"].items():
            has_planet = any(planet in example for planet in planets)
            assert not has_planet, \
                f"imperative.{pattern} should not mention planets: {example}"


class TestTemporality:
    """Test all examples include 'today' for temporality."""

    def test_all_examples_have_today(self):
        """Test every example includes 'today'."""
        examples = load_headline_examples()

        for mode_name, mode_data in examples["modes"].items():
            for pattern, example in mode_data["examples"].items():
                assert "today" in example.lower(), \
                    f"{mode_name}.{pattern} missing 'today': {example}"


class TestPathThrough:
    """Test negative examples include path through (not just doom)."""

    def test_negative_examples_have_guidance(self):
        """Test negative examples include actionable guidance."""
        examples = load_headline_examples()
        # Words that indicate guidance/path through
        guidance_words = [
            "double-check", "go easy", "take your time", "give yourself",
            "slow down", "rest", "trust", "save", "let", "margin"
        ]

        negative_patterns = ["one_negative", "two_negative"]

        for mode_name, mode_data in examples["modes"].items():
            for pattern in negative_patterns:
                example = mode_data["examples"][pattern].lower()
                has_guidance = any(word in example for word in guidance_words)
                assert has_guidance, \
                    f"{mode_name}.{pattern} should have path through: {example}"


class TestModeSelection:
    """Test deterministic mode selection."""

    def test_mode_selection_is_deterministic(self):
        """Test same user_id + date always gives same mode."""
        from astrometers.meters import _get_headline_mode

        user_id = "test_user_123"
        date = "2025-01-15"

        mode1 = _get_headline_mode(user_id, date)
        mode2 = _get_headline_mode(user_id, date)

        assert mode1 == mode2, "Same inputs should give same mode"

    def test_different_users_can_get_different_modes(self):
        """Test different users get variety (not all same mode)."""
        from astrometers.meters import _get_headline_mode

        date = "2025-01-15"
        modes = set()

        # Test 10 different users
        for i in range(10):
            mode = _get_headline_mode(f"user_{i}", date)
            modes.add(mode)

        # Should have at least 2 different modes across 10 users
        assert len(modes) >= 2, "Different users should get variety"

    def test_mode_changes_over_days(self):
        """Test same user gets variety over multiple days."""
        from astrometers.meters import _get_headline_mode

        user_id = "consistent_user"
        modes = set()

        # Test 10 different days
        for day in range(1, 11):
            mode = _get_headline_mode(user_id, f"2025-01-{day:02d}")
            modes.add(mode)

        # Should have at least 2 different modes across 10 days
        assert len(modes) >= 2, "Same user should get variety over days"

    def test_all_three_modes_reachable(self):
        """Test all three modes can be selected."""
        from astrometers.meters import _get_headline_mode

        modes = set()

        # Test many combinations
        for user_num in range(20):
            for day in range(1, 15):
                mode = _get_headline_mode(f"user_{user_num}", f"2025-01-{day:02d}")
                modes.add(mode)

        assert modes == {"provocative", "personalized", "imperative"}, \
            f"All modes should be reachable, got: {modes}"


class TestPatternClassification:
    """Test pattern classification from score bands."""

    def test_high_scores_give_positive_patterns(self):
        """Test high/mid_high scores map to positive patterns."""
        from astrometers.meters import get_score_band

        assert get_score_band(85) == "high"
        assert get_score_band(60) == "mid_high"

    def test_low_scores_give_negative_patterns(self):
        """Test mid_low/low scores map to negative patterns."""
        from astrometers.meters import get_score_band

        assert get_score_band(35) == "mid_low"
        assert get_score_band(15) == "low"

    def test_boundary_at_50(self):
        """Test 50 is the boundary between positive and negative."""
        from astrometers.meters import get_score_band

        assert get_score_band(50) == "mid_high"  # 50 is positive
        assert get_score_band(49) == "mid_low"   # 49 is negative

    def test_boundary_at_75(self):
        """Test 75 is boundary between mid_high and high."""
        from astrometers.meters import get_score_band

        assert get_score_band(75) == "high"
        assert get_score_band(74) == "mid_high"

    def test_boundary_at_25(self):
        """Test 25 is boundary between low and mid_low."""
        from astrometers.meters import get_score_band

        assert get_score_band(25) == "mid_low"
        assert get_score_band(24) == "low"

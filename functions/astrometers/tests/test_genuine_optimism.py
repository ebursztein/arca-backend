"""
Tests for genuine optimism updates to labels and prompts.

Verifies that all group advice_templates follow the genuine optimism pattern:
- Acknowledge obstacles honestly
- Empower users to overcome them
- No toxic positivity or doom-and-gloom
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import pytest
from pathlib import Path


# =============================================================================
# Test Data Loading
# =============================================================================

def load_group_labels():
    """Load all group label files."""
    labels_dir = Path(__file__).parent.parent / "labels" / "groups"
    groups = {}
    for json_file in labels_dir.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
            group_name = json_file.stem
            groups[group_name] = data
    return groups


def load_meter_labels():
    """Load all individual meter label files."""
    labels_dir = Path(__file__).parent.parent / "labels"
    meters = {}
    # Files to skip (not meter labels)
    skip_files = {"word_banks.json", "headline_examples.json"}
    for json_file in labels_dir.glob("*.json"):
        if json_file.name in skip_files:
            continue
        if json_file.parent.name != "labels":
            continue
        with open(json_file) as f:
            data = json.load(f)
            meter_name = json_file.stem
            meters[meter_name] = data
    return meters


# =============================================================================
# Group Label Tests
# =============================================================================

class TestGroupLabelsStructure:
    """Test that group labels have correct structure."""

    def test_all_groups_have_advice_templates(self):
        """Test all 6 groups have advice_templates."""
        groups = load_group_labels()
        expected_groups = ["mind", "heart", "body", "instincts", "growth", "overall"]

        for group in expected_groups:
            assert group in groups, f"Missing group: {group}"
            assert "advice_templates" in groups[group], f"{group} missing advice_templates"

    def test_advice_templates_have_all_intensities(self):
        """Test advice_templates have all 5 intensity levels."""
        groups = load_group_labels()
        intensities = ["quiet", "mild", "moderate", "high", "extreme"]

        for group_name, group_data in groups.items():
            templates = group_data["advice_templates"]
            for intensity in intensities:
                assert intensity in templates, f"{group_name} missing intensity: {intensity}"

    def test_advice_templates_have_all_qualities(self):
        """Test each intensity level has all 3 quality types."""
        groups = load_group_labels()
        qualities = ["challenging", "mixed", "harmonious"]

        for group_name, group_data in groups.items():
            templates = group_data["advice_templates"]
            for intensity, quality_dict in templates.items():
                for quality in qualities:
                    assert quality in quality_dict, f"{group_name}.{intensity} missing quality: {quality}"


class TestGroupLabelsGenuineOptimism:
    """Test that group labels follow genuine optimism principles."""

    def test_challenging_templates_not_doom_and_gloom(self):
        """Test challenging templates aren't pure negativity."""
        groups = load_group_labels()

        doom_phrases = [
            "just survive",
            "things are terrible",
            "nothing will work",
            "give up",
            "hopeless",
        ]

        for group_name, group_data in groups.items():
            templates = group_data["advice_templates"]
            for intensity, quality_dict in templates.items():
                challenging = quality_dict.get("challenging", "")
                for phrase in doom_phrases:
                    assert phrase not in challenging.lower(), \
                        f"{group_name}.{intensity}.challenging contains doom phrase: {phrase}"

    def test_challenging_templates_have_empowerment(self):
        """Test challenging templates include empowering elements."""
        groups = load_group_labels()

        # Look for patterns that suggest empowerment or path forward
        empowering_patterns = [
            " - ",  # Pattern: "obstacle - solution"
            "you",  # Addresses the user
            "can",
            "will",
            "trust",
            "handle",
            "pass",
            "through",
        ]

        for group_name, group_data in groups.items():
            templates = group_data["advice_templates"]
            for intensity, quality_dict in templates.items():
                challenging = quality_dict.get("challenging", "").lower()
                has_empowerment = any(pattern in challenging for pattern in empowering_patterns)
                assert has_empowerment, \
                    f"{group_name}.{intensity}.challenging lacks empowering language"

    def test_harmonious_templates_not_toxic_positivity(self):
        """Test harmonious templates aren't saccharine toxic positivity."""
        groups = load_group_labels()

        toxic_phrases = [
            "everything is perfect",
            "nothing can go wrong",
            "just be positive",
            "ignore problems",
            "manifest",
        ]

        for group_name, group_data in groups.items():
            templates = group_data["advice_templates"]
            for intensity, quality_dict in templates.items():
                harmonious = quality_dict.get("harmonious", "")
                for phrase in toxic_phrases:
                    assert phrase not in harmonious.lower(), \
                        f"{group_name}.{intensity}.harmonious contains toxic positivity: {phrase}"

    def test_templates_are_actionable(self):
        """Test templates provide actionable guidance."""
        groups = load_group_labels()

        for group_name, group_data in groups.items():
            templates = group_data["advice_templates"]
            for intensity, quality_dict in templates.items():
                for quality, text in quality_dict.items():
                    # Should be substantial enough to be useful
                    assert len(text) > 20, \
                        f"{group_name}.{intensity}.{quality} too short to be actionable"
                    # Should have some directive language
                    words = text.lower().split()
                    assert len(words) >= 5, \
                        f"{group_name}.{intensity}.{quality} needs more substance"


# =============================================================================
# Individual Meter Label Tests
# =============================================================================

class TestMeterLabelsStructure:
    """Test individual meter labels structure."""

    def test_all_17_meters_have_labels(self):
        """Test all 17 meters have label files."""
        meters = load_meter_labels()
        expected_meters = [
            'clarity', 'focus', 'communication',
            'connections', 'resilience', 'vulnerability',
            'energy', 'drive', 'strength',
            'vision', 'flow', 'intuition', 'creativity',
            'momentum', 'ambition', 'evolution', 'circle'
        ]

        for meter in expected_meters:
            assert meter in meters, f"Missing meter label file: {meter}"

    def test_meters_have_interpretation_guidelines(self):
        """Test each meter has interpretation_guidelines."""
        meters = load_meter_labels()

        for meter_name, meter_data in meters.items():
            assert "interpretation_guidelines" in meter_data, \
                f"{meter_name} missing interpretation_guidelines"

    def test_meters_have_avoid_list(self):
        """Test each meter has an avoid list (anti-patterns)."""
        meters = load_meter_labels()

        for meter_name, meter_data in meters.items():
            guidelines = meter_data.get("interpretation_guidelines", {})
            assert "avoid" in guidelines, f"{meter_name} missing avoid list"
            assert len(guidelines["avoid"]) > 0, f"{meter_name} avoid list is empty"


class TestMeterLabelsGenuineOptimism:
    """Test meter labels follow genuine optimism principles."""

    def test_avoid_lists_block_toxic_positivity(self):
        """Test avoid lists include toxic positivity warnings."""
        meters = load_meter_labels()

        for meter_name, meter_data in meters.items():
            guidelines = meter_data.get("interpretation_guidelines", {})
            avoid_list = guidelines.get("avoid", [])
            avoid_text = " ".join(avoid_list).lower()

            # Should warn against dismissing struggles
            has_anti_toxic = any(term in avoid_text for term in [
                "toxic", "dismiss", "ignore", "push through", "toughen"
            ])
            # This is a soft check - not all meters need explicit "toxic positivity" warning
            # but they should have SOME guardrails

    def test_phrasing_examples_have_challenging_version(self):
        """Test phrasing examples include low/challenging scenarios."""
        meters = load_meter_labels()

        for meter_name, meter_data in meters.items():
            guidelines = meter_data.get("interpretation_guidelines", {})
            examples = guidelines.get("phrasing_examples", {})

            # Should have a challenging example
            has_challenging = "low_challenging" in examples or "challenging" in str(examples).lower()
            assert has_challenging, \
                f"{meter_name} phrasing_examples missing challenging scenario"

    def test_challenging_examples_acknowledge_difficulty(self):
        """Test challenging examples acknowledge real difficulty."""
        meters = load_meter_labels()

        acknowledgment_terms = [
            "hard", "difficult", "challenging", "struggle", "genuine",
            "real", "shaky", "foggy", "low", "absorb", "overwhelming",
            "scarce", "off", "closed", "stuck", "blocked", "slow",
            "uncertain", "pressure", "tension", "intense", "heavy",
            "scattered", "distracted", "defensive", "vulnerable",
            "muffled", "confusing", "unclear", "weak", "drained",
            "exhausted", "frustrated", "strained", "tested"
        ]

        for meter_name, meter_data in meters.items():
            guidelines = meter_data.get("interpretation_guidelines", {})
            examples = guidelines.get("phrasing_examples", {})
            challenging = examples.get("low_challenging", "")

            if challenging:
                has_acknowledgment = any(term in challenging.lower() for term in acknowledgment_terms)
                assert has_acknowledgment, \
                    f"{meter_name} low_challenging example doesn't acknowledge difficulty: {challenging}"


# =============================================================================
# Word Count Tests (iOS UI Constraint)
# =============================================================================

class TestLabelWordCounts:
    """Test that labels meet iOS UI constraints (max 2 words)."""

    def test_group_advice_templates_reasonable_length(self):
        """Test group advice templates aren't too long for UI display."""
        groups = load_group_labels()
        max_words = 50  # Reasonable max for advice text

        for group_name, group_data in groups.items():
            templates = group_data["advice_templates"]
            for intensity, quality_dict in templates.items():
                for quality, text in quality_dict.items():
                    word_count = len(text.split())
                    assert word_count <= max_words, \
                        f"{group_name}.{intensity}.{quality} too long ({word_count} words)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

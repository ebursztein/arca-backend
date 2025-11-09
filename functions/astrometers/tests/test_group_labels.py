"""Test meter label JSON files (17-meter system)."""

import json
import os
from astrometers.hierarchy import Meter


def test_all_meter_labels_exist():
    """Test that all 17 meter label files exist."""
    labels_dir = os.path.join(os.path.dirname(__file__), "..", "labels")

    for meter in Meter:
        filepath = os.path.join(labels_dir, f"{meter.value}.json")
        assert os.path.exists(filepath), f"Label file missing for {meter.value}"


def test_meter_label_structure():
    """Test that all meter label files have the correct structure."""
    labels_dir = os.path.join(os.path.dirname(__file__), "..", "labels")

    required_keys = ["_schema_version", "_meter", "_last_updated", "metadata", "description", "experience_labels", "advice_templates"]
    metadata_keys = ["meter_id", "display_name", "group"]  # description is optional in metadata
    description_keys = ["overview", "detailed", "keywords"]

    for meter in Meter:
        filepath = os.path.join(labels_dir, f"{meter.value}.json")

        with open(filepath, "r") as f:
            data = json.load(f)

        # Check top-level keys
        for key in required_keys:
            assert key in data, f"{meter.value}: Missing key '{key}'"

        # Check metadata
        for key in metadata_keys:
            assert key in data["metadata"], f"{meter.value}: Missing metadata key '{key}'"

        # Check description
        for key in description_keys:
            assert key in data["description"], f"{meter.value}: Missing description key '{key}'"

        # Check experience_labels structure (combined only)
        assert "combined" in data["experience_labels"]

        # Check combined has 5x3 structure
        intensity_levels = ["quiet", "mild", "moderate", "high", "extreme"]
        harmony_levels = ["challenging", "mixed", "harmonious"]

        for intensity_level in intensity_levels:
            assert intensity_level in data["experience_labels"]["combined"], f"{meter.value}: Missing combined intensity level '{intensity_level}'"
            for harmony_level in harmony_levels:
                assert harmony_level in data["experience_labels"]["combined"][intensity_level], f"{meter.value}: Missing combined harmony level '{harmony_level}' in intensity '{intensity_level}'"

        # Check advice_templates exists (structure varies: some have "general", others have 5x3 matrix)
        assert "advice_templates" in data, f"{meter.value}: Missing 'advice_templates'"
        assert len(data["advice_templates"]) > 0, f"{meter.value}: Empty advice_templates"


def test_meter_metadata_accuracy():
    """Test that metadata in label files matches meter enum."""
    labels_dir = os.path.join(os.path.dirname(__file__), "..", "labels")

    for meter in Meter:
        filepath = os.path.join(labels_dir, f"{meter.value}.json")

        with open(filepath, "r") as f:
            data = json.load(f)

        # Check meter_id matches
        assert data["metadata"]["meter_id"] == meter.value, f"{meter.value}: meter_id mismatch"

        # Check group is valid
        valid_groups = ["mind", "emotions", "body", "spirit", "growth"]
        assert data["metadata"]["group"] in valid_groups, f"{meter.value}: Invalid group '{data['metadata']['group']}'"


def test_label_content_not_empty():
    """Test that all labels have non-empty content."""
    labels_dir = os.path.join(os.path.dirname(__file__), "..", "labels")

    for meter in Meter:
        filepath = os.path.join(labels_dir, f"{meter.value}.json")

        with open(filepath, "r") as f:
            data = json.load(f)

        # Check description fields are not empty
        assert len(data["description"]["overview"]) > 0, f"{meter.value}: Empty overview"
        assert len(data["description"]["detailed"]) > 0, f"{meter.value}: Empty detailed"
        assert len(data["description"]["keywords"]) >= 3, f"{meter.value}: Should have at least 3 keywords"

        # Check all experience labels are not empty
        for intensity_level in ["quiet", "mild", "moderate", "high", "extreme"]:
            for harmony_level in ["challenging", "mixed", "harmonious"]:
                label = data["experience_labels"]["combined"][intensity_level][harmony_level]
                assert len(label) > 0, f"{meter.value}: Empty label at {intensity_level}/{harmony_level}"
                assert len(label.split()) <= 4, f"{meter.value}: Label too long (>4 words) at {intensity_level}/{harmony_level}: '{label}'"


if __name__ == "__main__":
    print("Running meter label tests (17-meter system)...")
    print()

    test_all_meter_labels_exist()
    print("✅ All 17 meter label files exist")

    test_meter_label_structure()
    print("✅ All label files have correct structure")

    test_meter_metadata_accuracy()
    print("✅ Metadata matches meter enum")

    test_label_content_not_empty()
    print("✅ All labels have content")

    print()
    print("🎉 All meter label tests passed!")

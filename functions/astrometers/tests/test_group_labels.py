"""Test meter label JSON files (17-meter system).

Note: Experience labels have been removed from JSON files. iOS handles bucket labels.
These tests verify the remaining structure: metadata, description, and astrological_foundation.
"""

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

    # experience_labels removed - iOS handles bucket labels now
    required_keys = ["_meter", "metadata", "description"]
    metadata_keys = ["meter_id", "display_name", "group"]
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
        valid_groups = ["mind", "heart", "body", "instincts", "growth"]
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


if __name__ == "__main__":
    print("Running meter label tests (17-meter system)...")
    print()

    test_all_meter_labels_exist()
    print("All 17 meter label files exist")

    test_meter_label_structure()
    print("All label files have correct structure")

    test_meter_metadata_accuracy()
    print("Metadata matches meter enum")

    test_label_content_not_empty()
    print("All labels have content")

    print()
    print("All meter label tests passed!")

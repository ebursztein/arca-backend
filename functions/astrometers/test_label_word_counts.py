"""
Test script to validate all astrometer state labels are 2 words or less.
"""

import json
import os
from pathlib import Path

def count_words(text):
    """Count words in a text string."""
    return len(text.strip().split())

def test_labels_in_file(file_path):
    """Test all labels in a single JSON file."""
    errors = []

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Get experience labels
    if 'experience_labels' not in data:
        return errors

    experience_labels = data['experience_labels']['combined']

    # Check each intensity level
    for intensity in ['quiet', 'mild', 'moderate', 'high', 'extreme']:
        if intensity not in experience_labels:
            continue

        for quality in ['challenging', 'mixed', 'harmonious']:
            if quality not in experience_labels[intensity]:
                continue

            label = experience_labels[intensity][quality]
            word_count = count_words(label)

            if word_count > 2:
                errors.append({
                    'file': file_path.name,
                    'intensity': intensity,
                    'quality': quality,
                    'label': label,
                    'word_count': word_count
                })

    return errors

def main():
    """Run tests on all label files."""
    labels_dir = Path(__file__).parent / 'labels'

    # Test individual meter files
    meter_files = list(labels_dir.glob('*.json'))

    # Test group files
    group_files = list((labels_dir / 'groups').glob('*.json'))

    all_files = meter_files + group_files
    all_errors = []

    for file_path in sorted(all_files):
        errors = test_labels_in_file(file_path)
        all_errors.extend(errors)

    # Report results
    if all_errors:
        print(f"\n❌ Found {len(all_errors)} labels exceeding 2 words:\n")
        for error in all_errors:
            print(f"  {error['file']}")
            print(f"    {error['intensity']}/{error['quality']}: \"{error['label']}\" ({error['word_count']} words)")
        return 1
    else:
        print(f"\n✅ All {len(all_files)} files passed! All labels are 2 words or less.")
        return 0

if __name__ == '__main__':
    exit(main())

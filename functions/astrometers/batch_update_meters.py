#!/usr/bin/env python3
"""
Batch update all remaining meter functions to use JSON labels.

Updates 20 remaining meters by replacing hardcoded interpretation/advice/state_label
with apply_labels_to_reading().
"""

import re

# All 23 meters and their IDs
METER_UPDATES = [
    ("calculate_decision_quality_meter", "decision_quality"),
    ("calculate_communication_flow_meter", "communication_flow"),
    ("calculate_emotional_intensity_meter", "emotional_intensity"),
    ("calculate_relationship_harmony_meter", "relationship_harmony"),
    ("calculate_emotional_resilience_meter", "emotional_resilience"),
    ("calculate_physical_energy_meter", "physical_energy"),
    ("calculate_conflict_risk_meter", "conflict_risk"),
    ("calculate_motivation_drive_meter", "motivation_drive"),
    ("calculate_career_ambition_meter", "career_ambition"),
    ("calculate_opportunity_window_meter", "opportunity_window"),
    ("calculate_challenge_intensity_meter", "challenge_intensity"),
    ("calculate_transformation_pressure_meter", "transformation_pressure"),
    ("calculate_fire_energy_meter", "fire_energy"),
    ("calculate_earth_energy_meter", "earth_energy"),
    ("calculate_air_energy_meter", "air_energy"),
    ("calculate_water_energy_meter", "water_energy"),
    ("calculate_intuition_spirituality_meter", "intuition_spirituality"),
    ("calculate_innovation_breakthrough_meter", "innovation_breakthrough"),
    ("calculate_karmic_lessons_meter", "karmic_lessons"),
    ("calculate_social_collective_meter", "social_collective"),
]


def update_single_meter(content: str, func_name: str, meter_id: str) -> tuple[str, bool]:
    """
    Update a single meter function.

    Returns: (updated_content, was_updated)
    """
    # Find the function
    pattern = rf"(def {func_name}\([^)]*\)[^:]*:.*?)(    return reading)"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print(f"  ❌ Could not find function: {func_name}")
        return content, False

    func_body = match.group(0)

    # Check if already updated
    if "apply_labels_to_reading" in func_body:
        print(f"  ✓ Skipped (already updated): {func_name}")
        return content, False

    # Split into lines
    lines = func_body.split('\n')

    # Find the return statement
    return_idx = None
    for i, line in enumerate(lines):
        if "return reading" in line and not line.strip().startswith("#"):
            return_idx = i
            break

    if return_idx is None:
        print(f"  ❌ No return statement found: {func_name}")
        return content, False

    # Find where interpretation logic starts
    # Look backwards from return for interpretation/advice/state_label assignments
    interp_start = None
    for i in range(return_idx - 1, -1, -1):
        line = lines[i].strip()

        # These indicate interpretation logic
        if any(marker in line for marker in [
            "reading.interpretation =",
            "reading.advice =",
            "reading.state_label =",
            "if reading.intensity",
            "elif reading.intensity",
            "if intensity <",
            "elif intensity <",
            "if reading.harmony",
            "elif reading.harmony",
            "if harmony <",
            "elif harmony <",
        ]):
            interp_start = i
        # These indicate we've gone past interpretation logic
        elif any(marker in line for marker in [
            "reading = calculate_meter_score",
            "additional_context[",
            "# Apply",
            "# Count",
            "# Filter",
        ]) and interp_start is not None:
            # Found the start of interpretation block
            break

    if interp_start is None:
        print(f"  ⚠️  No interpretation logic found, adding apply_labels_to_reading before return")
        # Just add before return
        new_lines = (
            lines[:return_idx] +
            ['', '    # Apply labels from JSON', f'    apply_labels_to_reading(reading, "{meter_id}")', ''] +
            lines[return_idx:]
        )
    else:
        # Replace interpretation block
        # Keep everything before interpretation starts
        # Add apply_labels_to_reading
        # Keep everything after interpretation (but before return) if it's special (contributors, notes, etc.)

        # Check if there are special additions after interpretation
        special_additions = []
        for i in range(interp_start, return_idx):
            line = lines[i].strip()
            if any(marker in line for marker in [
                "reading.interpretation +=",
                "contrib_text",
                "breakdown",
                "retrograde",
                "# Add",
            ]) and "reading.interpretation =" not in line:
                # This is a special addition, keep it
                if i not in special_additions:
                    special_additions.append(i)

        # Build new function body
        kept_lines = lines[:interp_start]
        new_logic = [
            '',
            '    # Apply labels from JSON',
            f'    apply_labels_to_reading(reading, "{meter_id}")',
            ''
        ]

        # Add special additions
        if special_additions:
            for idx in special_additions:
                new_logic.append(lines[idx])
            new_logic.append('')

        new_lines = kept_lines + new_logic + lines[return_idx:]

    new_func = '\n'.join(new_lines)
    new_content = content.replace(func_body, new_func)

    return new_content, True


def main():
    """Update all meters in meters.py"""
    print("=" * 70)
    print("BATCH UPDATE: Replace interpretation logic with JSON labels")
    print("=" * 70)

    with open("meters.py", "r") as f:
        content = f.read()

    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for func_name, meter_id in METER_UPDATES:
        print(f"\nProcessing: {func_name}")
        new_content, was_updated = update_single_meter(content, func_name, meter_id)

        if was_updated:
            content = new_content
            updated_count += 1
            print(f"  ✅ Updated!")
        elif "apply_labels_to_reading" in new_content:
            skipped_count += 1
        else:
            failed_count += 1

    # Write back
    with open("meters.py", "w") as f:
        f.write(content)

    print("\n" + "=" * 70)
    print(f"✅ COMPLETE: Updated {updated_count} meters")
    print(f"✓  Skipped {skipped_count} meters (already updated)")
    if failed_count > 0:
        print(f"⚠️  Failed {failed_count} meters (may need manual review)")
    print(f"📊 Total: {updated_count + skipped_count + failed_count}/{len(METER_UPDATES)} meters processed")
    print("=" * 70)


if __name__ == "__main__":
    main()

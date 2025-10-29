#!/usr/bin/env python3
"""
Script to update all meter functions to use JSON labels.

Replaces hardcoded interpretation/advice/state_label logic with apply_labels_to_reading().
"""

import re

# Meter ID mapping
METER_IDS = {
    "calculate_overall_intensity_meter": "overall_intensity",
    "calculate_overall_harmony_meter": "overall_harmony",
    "calculate_mental_clarity_meter": "mental_clarity",
    "calculate_decision_quality_meter": "decision_quality",
    "calculate_communication_flow_meter": "communication_flow",
    "calculate_emotional_intensity_meter": "emotional_intensity",
    "calculate_relationship_harmony_meter": "relationship_harmony",
    "calculate_emotional_resilience_meter": "emotional_resilience",
    "calculate_physical_energy_meter": "physical_energy",
    "calculate_conflict_risk_meter": "conflict_risk",
    "calculate_motivation_drive_meter": "motivation_drive",
    "calculate_career_ambition_meter": "career_ambition",
    "calculate_opportunity_window_meter": "opportunity_window",
    "calculate_challenge_intensity_meter": "challenge_intensity",
    "calculate_transformation_pressure_meter": "transformation_pressure",
    "calculate_fire_energy_meter": "fire_energy",
    "calculate_earth_energy_meter": "earth_energy",
    "calculate_air_energy_meter": "air_energy",
    "calculate_water_energy_meter": "water_energy",
    "calculate_intuition_spirituality_meter": "intuition_spirituality",
    "calculate_innovation_breakthrough_meter": "innovation_breakthrough",
    "calculate_karmic_lessons_meter": "karmic_lessons",
    "calculate_social_collective_meter": "social_collective",
}

def update_meter_function(content: str, func_name: str, meter_id: str) -> str:
    """
    Update a single meter function to use apply_labels_to_reading().

    Finds the function, locates where reading.interpretation/advice/state_label are set,
    and replaces with apply_labels_to_reading().
    """
    # Pattern to find the function
    func_pattern = rf"(def {func_name}\([^)]*\)[^:]*:.*?)(    return reading)"

    match = re.search(func_pattern, content, re.DOTALL)
    if not match:
        print(f"❌ Could not find function: {func_name}")
        return content

    func_start, return_statement = match.groups()
    func_body = match.group(0)

    # Check if already updated
    if "apply_labels_to_reading" in func_body:
        print(f"✓ Already updated: {func_name}")
        return content

    # Find where the interpretation logic starts (usually after reading = calculate_meter_score or after modifiers)
    # We want to replace everything from the first "reading.interpretation =" or "if intensity <" until just before "return reading"

    # Strategy: Find the last line before "return reading" that doesn't involve interpretation/advice/state_label
    # Then insert apply_labels_to_reading() there

    lines = func_body.split('\n')

    # Find index of "return reading"
    return_idx = None
    for i, line in enumerate(lines):
        if "return reading" in line and not line.strip().startswith("#"):
            return_idx = i
            break

    if return_idx is None:
        print(f"❌ Could not find return statement in: {func_name}")
        return content

    # Find where interpretation logic starts
    # Look for lines with: reading.interpretation =, reading.advice =, reading.state_label =, if intensity, elif harmony
    interp_start_idx = None
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if any(x in line for x in ["reading.interpretation", "reading.advice", "reading.state_label", "if intensity", "elif intensity", "elif harmony", "if harmony"]):
            if interp_start_idx is None:
                interp_start_idx = i
        elif "reading =" in line or "calculate_meter_score" in line or "additional_context" in line:
            # Found the line before interpretation logic starts
            if interp_start_idx is not None:
                break

    if interp_start_idx is None:
        print(f"⚠️  No interpretation logic found in: {func_name}")
        # Just add apply_labels_to_reading before return
        new_lines = lines[:return_idx] + [f"    # Apply labels from JSON", f'    apply_labels_to_reading(reading, "{meter_id}")'] + [''] + lines[return_idx:]
        new_func = '\n'.join(new_lines)
        return content.replace(func_body, new_func)

    # Replace interpretation logic with apply_labels_to_reading
    indent = "    "  # Standard function body indent
    new_lines = (
        lines[:interp_start_idx] +
        ['', f'{indent}# Apply labels from JSON', f'{indent}apply_labels_to_reading(reading, "{meter_id}")',''] +
        lines[return_idx:]
    )

    new_func = '\n'.join(new_lines)
    return content.replace(func_body, new_func)


def main():
    """Update all meter functions in meters.py"""
    with open("meters.py", "r") as f:
        content = f.read()

    print("Updating meter functions to use JSON labels...\n")

    updated_count = 0
    skipped_count = 0

    for func_name, meter_id in METER_IDS.items():
        if "apply_labels_to_reading" in content:
            # Check if this specific function is already updated
            func_pattern = rf"def {func_name}\([^)]*\):.*?return reading"
            match = re.search(func_pattern, content, re.DOTALL)
            if match and "apply_labels_to_reading" in match.group(0):
                print(f"✓ Skipped (already updated): {func_name}")
                skipped_count += 1
                continue

        print(f"Updating: {func_name}...")
        old_content = content
        content = update_meter_function(content, func_name, meter_id)
        if content != old_content:
            updated_count += 1
            print(f"✅ Updated: {func_name}")
        else:
            print(f"⚠️  No changes: {func_name}")

    # Write back
    with open("meters.py", "w") as f:
        f.write(content)

    print(f"\n✅ Updated {updated_count} functions")
    print(f"✓ Skipped {skipped_count} functions (already updated)")
    print(f"Total: {len(METER_IDS)} meter functions")


if __name__ == "__main__":
    main()

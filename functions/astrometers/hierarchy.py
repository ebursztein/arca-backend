"""
Astro Meters Hierarchy - Single Source of Truth

Streamlined 17-meter system organized into 5 user-facing categories.

This module defines the complete organizational structure and serves as
the canonical reference for all category-related code.
"""

from enum import Enum
from typing import Dict, List


# =============================================================================
# LEVEL 0: Individual Meter Names (17 total)
# =============================================================================

class Meter(str, Enum):
    """Individual meter identifiers (17 total)"""
    # MIND (3)
    MENTAL_CLARITY = "mental_clarity"
    FOCUS = "focus"
    COMMUNICATION = "communication"

    # EMOTIONS (3)
    LOVE = "love"
    INNER_STABILITY = "inner_stability"
    SENSITIVITY = "sensitivity"

    # BODY (3)
    VITALITY = "vitality"
    DRIVE = "drive"
    WELLNESS = "wellness"

    # SPIRIT (4)
    PURPOSE = "purpose"
    CONNECTION = "connection"
    INTUITION = "intuition"
    CREATIVITY = "creativity"

    # GROWTH (4)
    OPPORTUNITIES = "opportunities"
    CAREER = "career"
    GROWTH = "growth"
    SOCIAL_LIFE = "social_life"


# =============================================================================
# LEVEL 1: User-Facing Categories (5 groups)
# =============================================================================

class MeterGroupV2(str, Enum):
    """5 user-facing life categories"""
    MIND = "mind"
    EMOTIONS = "emotions"
    BODY = "body"
    SPIRIT = "spirit"
    GROWTH = "growth"


# =============================================================================
# METER TO GROUP MAPPINGS
# =============================================================================

# Meter → MeterGroupV2 mapping
METER_TO_GROUP_V2: Dict[Meter, MeterGroupV2] = {
    # MIND (3 meters)
    Meter.MENTAL_CLARITY: MeterGroupV2.MIND,
    Meter.FOCUS: MeterGroupV2.MIND,
    Meter.COMMUNICATION: MeterGroupV2.MIND,

    # EMOTIONS (3 meters)
    Meter.LOVE: MeterGroupV2.EMOTIONS,
    Meter.INNER_STABILITY: MeterGroupV2.EMOTIONS,
    Meter.SENSITIVITY: MeterGroupV2.EMOTIONS,

    # BODY (3 meters)
    Meter.VITALITY: MeterGroupV2.BODY,
    Meter.DRIVE: MeterGroupV2.BODY,
    Meter.WELLNESS: MeterGroupV2.BODY,

    # SPIRIT (4 meters)
    Meter.PURPOSE: MeterGroupV2.SPIRIT,
    Meter.CONNECTION: MeterGroupV2.SPIRIT,
    Meter.INTUITION: MeterGroupV2.SPIRIT,
    Meter.CREATIVITY: MeterGroupV2.SPIRIT,

    # GROWTH (4 meters)
    Meter.OPPORTUNITIES: MeterGroupV2.GROWTH,
    Meter.CAREER: MeterGroupV2.GROWTH,
    Meter.GROWTH: MeterGroupV2.GROWTH,
    Meter.SOCIAL_LIFE: MeterGroupV2.GROWTH,
}

# MeterGroupV2 → List[Meter] reverse mapping
GROUP_V2_METERS: Dict[MeterGroupV2, List[Meter]] = {
    MeterGroupV2.MIND: [
        Meter.MENTAL_CLARITY,
        Meter.FOCUS,
        Meter.COMMUNICATION,
    ],
    MeterGroupV2.EMOTIONS: [
        Meter.LOVE,
        Meter.INNER_STABILITY,
        Meter.SENSITIVITY,
    ],
    MeterGroupV2.BODY: [
        Meter.VITALITY,
        Meter.DRIVE,
        Meter.WELLNESS,
    ],
    MeterGroupV2.SPIRIT: [
        Meter.PURPOSE,
        Meter.CONNECTION,
        Meter.INTUITION,
        Meter.CREATIVITY,
    ],
    MeterGroupV2.GROWTH: [
        Meter.OPPORTUNITIES,
        Meter.CAREER,
        Meter.GROWTH,
        Meter.SOCIAL_LIFE,
    ],
}

# Display names for each group
GROUP_V2_DISPLAY_NAMES: Dict[MeterGroupV2, str] = {
    MeterGroupV2.MIND: "Mind",
    MeterGroupV2.EMOTIONS: "Emotions",
    MeterGroupV2.BODY: "Body",
    MeterGroupV2.SPIRIT: "Spirit",
    MeterGroupV2.GROWTH: "Growth",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_group_v2(meter: Meter) -> MeterGroupV2:
    """Get the MeterGroupV2 for a given meter."""
    if meter not in METER_TO_GROUP_V2:
        raise ValueError(f"{meter} is not mapped to a MeterGroupV2")
    return METER_TO_GROUP_V2[meter]


def get_meters_in_group_v2(group: MeterGroupV2) -> List[Meter]:
    """Get all meters in a given MeterGroupV2."""
    return GROUP_V2_METERS[group]


def get_group_v2_display_name(group: MeterGroupV2) -> str:
    """Get the display name for a MeterGroupV2."""
    return GROUP_V2_DISPLAY_NAMES[group]


def validate_group_v2_complete() -> bool:
    """Validate that all 17 meters are mapped to MeterGroupV2."""
    all_meters = set(Meter)
    mapped_meters = set(METER_TO_GROUP_V2.keys())

    if all_meters != mapped_meters:
        missing = all_meters - mapped_meters
        extra = mapped_meters - all_meters
        if missing:
            print(f"MeterGroupV2: Missing meters: {missing}")
        if extra:
            print(f"MeterGroupV2: Extra meters: {extra}")
        return False

    # Validate counts
    if len(mapped_meters) != 17:
        print(f"MeterGroupV2: Expected 17 meters, got {len(mapped_meters)}")
        return False

    # Validate no duplicates in reverse mapping
    all_meters_in_groups = []
    for meters in GROUP_V2_METERS.values():
        all_meters_in_groups.extend(meters)

    if len(all_meters_in_groups) != len(set(all_meters_in_groups)):
        print(f"MeterGroupV2: Duplicate meters found in GROUP_V2_METERS")
        return False

    # Validate distribution
    expected_distribution = {
        MeterGroupV2.MIND: 3,
        MeterGroupV2.EMOTIONS: 3,
        MeterGroupV2.BODY: 3,
        MeterGroupV2.SPIRIT: 4,
        MeterGroupV2.GROWTH: 4,
    }

    for group, expected_count in expected_distribution.items():
        actual_count = len(GROUP_V2_METERS[group])
        if actual_count != expected_count:
            print(f"MeterGroupV2.{group.value}: Expected {expected_count} meters, got {actual_count}")
            return False

    return True


# Validate on import
assert validate_group_v2_complete(), "MeterGroupV2 mapping is incomplete or has duplicates"

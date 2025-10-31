"""
Astro Meters Hierarchy - Single Source of Truth

Three-tier taxonomy:
    SuperGroup (5) → MeterGroup (9) → Meters (23)

This module defines the complete organizational structure and serves as
the canonical reference for all category-related code.
"""

from enum import Enum
from typing import Dict, List, TypedDict


# =============================================================================
# LEVEL 0: Individual Meter Names (23 total)
# =============================================================================

class Meter(str, Enum):
    """Level 3: Individual meter identifiers (23 total) + 5 super-group aggregates"""
    # OVERVIEW
    OVERALL_INTENSITY = "overall_intensity"
    OVERALL_HARMONY = "overall_harmony"

    # MIND
    MENTAL_CLARITY = "mental_clarity"
    DECISION_QUALITY = "decision_quality"
    COMMUNICATION_FLOW = "communication_flow"

    # EMOTIONS
    EMOTIONAL_INTENSITY = "emotional_intensity"
    RELATIONSHIP_HARMONY = "relationship_harmony"
    EMOTIONAL_RESILIENCE = "emotional_resilience"

    # BODY
    PHYSICAL_ENERGY = "physical_energy"
    CONFLICT_RISK = "conflict_risk"
    MOTIVATION_DRIVE = "motivation_drive"

    # CAREER
    CAREER_AMBITION = "career_ambition"
    OPPORTUNITY_WINDOW = "opportunity_window"

    # EVOLUTION
    CHALLENGE_INTENSITY = "challenge_intensity"
    TRANSFORMATION_PRESSURE = "transformation_pressure"
    INNOVATION_BREAKTHROUGH = "innovation_breakthrough"

    # ELEMENTS
    FIRE_ENERGY = "fire_energy"
    EARTH_ENERGY = "earth_energy"
    AIR_ENERGY = "air_energy"
    WATER_ENERGY = "water_energy"

    # SPIRITUAL
    INTUITION_SPIRITUALITY = "intuition_spirituality"
    KARMIC_LESSONS = "karmic_lessons"

    # COLLECTIVE
    SOCIAL_COLLECTIVE = "social_collective"

    # SUPER-GROUP AGGREGATES (5 total)
    # These are calculated by aggregating all meters within their super-group
    OVERVIEW_SUPER_GROUP = "overview_super_group"
    INNER_WORLD_SUPER_GROUP = "inner_world_super_group"
    OUTER_WORLD_SUPER_GROUP = "outer_world_super_group"
    EVOLUTION_SUPER_GROUP = "evolution_super_group"
    DEEPER_DIMENSIONS_SUPER_GROUP = "deeper_dimensions_super_group"


# =============================================================================
# LEVEL 1: Super-Groups (5 domains)
# =============================================================================

class SuperGroup(str, Enum):
    """Level 1: Major life domains (5 total)"""
    OVERVIEW = "overview"
    INNER_WORLD = "inner_world"
    OUTER_WORLD = "outer_world"
    EVOLUTION = "evolution"
    DEEPER_DIMENSIONS = "deeper_dimensions"


# =============================================================================
# LEVEL 2: Groups (9 categories)
# =============================================================================

class MeterGroup(str, Enum):
    """Level 2: Thematic categories (9 total)"""
    # OVERVIEW super-group
    OVERVIEW = "overview"

    # INNER_WORLD super-group
    MIND = "mind"
    EMOTIONS = "emotions"

    # OUTER_WORLD super-group
    BODY = "body"
    CAREER = "career"

    # EVOLUTION super-group
    EVOLUTION = "evolution"

    # DEEPER_DIMENSIONS super-group
    ELEMENTS = "elements"
    SPIRITUAL = "spiritual"
    COLLECTIVE = "collective"


# =============================================================================
# TYPE-SAFE HIERARCHY STRUCTURE
# =============================================================================

class GroupDefinition(TypedDict):
    """Type definition for a single group"""
    group: MeterGroup
    meters: List[Meter]
    description: str


class SuperGroupDefinition(TypedDict):
    """Type definition for a super-group"""
    super_group: SuperGroup
    groups: List[GroupDefinition]
    description: str


# Complete hierarchy as nested structure
HIERARCHY: List[SuperGroupDefinition] = [
    # =========================================================================
    # OVERVIEW
    # =========================================================================
    {
        "super_group": SuperGroup.OVERVIEW,
        "description": "High-level dashboard summary",
        "groups": [
            {
                "group": MeterGroup.OVERVIEW,
                "description": "Overall astrological intensity and quality",
                "meters": [
                    Meter.OVERALL_INTENSITY,
                    Meter.OVERALL_HARMONY,
                ]
            }
        ]
    },

    # =========================================================================
    # INNER WORLD
    # =========================================================================
    {
        "super_group": SuperGroup.INNER_WORLD,
        "description": "Internal states—thoughts, feelings, and inner resources",
        "groups": [
            {
                "group": MeterGroup.MIND,
                "description": "Cognitive function, communication, decision-making",
                "meters": [
                    Meter.MENTAL_CLARITY,
                    Meter.DECISION_QUALITY,
                    Meter.COMMUNICATION_FLOW,
                ]
            },
            {
                "group": MeterGroup.EMOTIONS,
                "description": "Emotional life, relationships, and inner resilience",
                "meters": [
                    Meter.EMOTIONAL_INTENSITY,
                    Meter.RELATIONSHIP_HARMONY,
                    Meter.EMOTIONAL_RESILIENCE,
                ]
            }
        ]
    },

    # =========================================================================
    # OUTER WORLD
    # =========================================================================
    {
        "super_group": SuperGroup.OUTER_WORLD,
        "description": "Engagement with external reality—body, action, career, opportunities",
        "groups": [
            {
                "group": MeterGroup.BODY,
                "description": "Physical energy, action-taking, conflict management",
                "meters": [
                    Meter.PHYSICAL_ENERGY,
                    Meter.CONFLICT_RISK,
                    Meter.MOTIVATION_DRIVE,
                ]
            },
            {
                "group": MeterGroup.CAREER,
                "description": "Professional life, ambition, opportunities",
                "meters": [
                    Meter.CAREER_AMBITION,
                    Meter.OPPORTUNITY_WINDOW,
                ]
            }
        ]
    },

    # =========================================================================
    # EVOLUTION
    # =========================================================================
    {
        "super_group": SuperGroup.EVOLUTION,
        "description": "Growth through challenge, transformation, and breakthrough",
        "groups": [
            {
                "group": MeterGroup.EVOLUTION,
                "description": "Challenge, transformation, innovation",
                "meters": [
                    Meter.CHALLENGE_INTENSITY,
                    Meter.TRANSFORMATION_PRESSURE,
                    Meter.INNOVATION_BREAKTHROUGH,
                ]
            }
        ]
    },

    # =========================================================================
    # DEEPER DIMENSIONS
    # =========================================================================
    {
        "super_group": SuperGroup.DEEPER_DIMENSIONS,
        "description": "Foundational energies, spiritual awareness, and collective currents",
        "groups": [
            {
                "group": MeterGroup.ELEMENTS,
                "description": "Temperament balance, elemental energy distribution",
                "meters": [
                    Meter.FIRE_ENERGY,
                    Meter.EARTH_ENERGY,
                    Meter.AIR_ENERGY,
                    Meter.WATER_ENERGY,
                ]
            },
            {
                "group": MeterGroup.SPIRITUAL,
                "description": "Soul-level awareness, karmic themes, spiritual sensitivity",
                "meters": [
                    Meter.INTUITION_SPIRITUALITY,
                    Meter.KARMIC_LESSONS,
                ]
            },
            {
                "group": MeterGroup.COLLECTIVE,
                "description": "Connection to societal currents and collective consciousness",
                "meters": [
                    Meter.SOCIAL_COLLECTIVE,
                ]
            }
        ]
    }
]


# =============================================================================
# LOOKUP UTILITIES (Derived from HIERARCHY)
# =============================================================================

# Flat mapping: Meter → (MeterGroup, SuperGroup)
METER_TO_GROUP: Dict[Meter, tuple[MeterGroup, SuperGroup]] = {}

# Reverse mapping: MeterGroup → SuperGroup
GROUP_TO_SUPER: Dict[MeterGroup, SuperGroup] = {}

# Group membership: MeterGroup → List[Meter]
GROUP_METERS: Dict[MeterGroup, List[Meter]] = {}

# Super-group membership: SuperGroup → List[MeterGroup]
SUPER_GROUPS: Dict[SuperGroup, List[MeterGroup]] = {}

# Build lookups from HIERARCHY (single source of truth)
for super_def in HIERARCHY:
    super_group = super_def["super_group"]

    for group_def in super_def["groups"]:
        group = group_def["group"]
        meters = group_def["meters"]

        # Register group → super-group
        GROUP_TO_SUPER[group] = super_group

        # Register super-group → groups
        if super_group not in SUPER_GROUPS:
            SUPER_GROUPS[super_group] = []
        SUPER_GROUPS[super_group].append(group)

        # Register group → meters
        GROUP_METERS[group] = meters

        # Register meter → (group, super-group)
        for meter in meters:
            METER_TO_GROUP[meter] = (group, super_group)

# Super-group aggregate meters (5 total)
SUPER_GROUP_METERS = {
    Meter.OVERVIEW_SUPER_GROUP,
    Meter.INNER_WORLD_SUPER_GROUP,
    Meter.OUTER_WORLD_SUPER_GROUP,
    Meter.EVOLUTION_SUPER_GROUP,
    Meter.DEEPER_DIMENSIONS_SUPER_GROUP,
}

# Mapping: SuperGroup → aggregate Meter
SUPER_GROUP_TO_METER: Dict[SuperGroup, Meter] = {
    SuperGroup.OVERVIEW: Meter.OVERVIEW_SUPER_GROUP,
    SuperGroup.INNER_WORLD: Meter.INNER_WORLD_SUPER_GROUP,
    SuperGroup.OUTER_WORLD: Meter.OUTER_WORLD_SUPER_GROUP,
    SuperGroup.EVOLUTION: Meter.EVOLUTION_SUPER_GROUP,
    SuperGroup.DEEPER_DIMENSIONS: Meter.DEEPER_DIMENSIONS_SUPER_GROUP,
}

# Reverse mapping: Aggregate Meter → SuperGroup
METER_TO_SUPER_GROUP: Dict[Meter, SuperGroup] = {
    Meter.OVERVIEW_SUPER_GROUP: SuperGroup.OVERVIEW,
    Meter.INNER_WORLD_SUPER_GROUP: SuperGroup.INNER_WORLD,
    Meter.OUTER_WORLD_SUPER_GROUP: SuperGroup.OUTER_WORLD,
    Meter.EVOLUTION_SUPER_GROUP: SuperGroup.EVOLUTION,
    Meter.DEEPER_DIMENSIONS_SUPER_GROUP: SuperGroup.DEEPER_DIMENSIONS,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_super_group(meter: Meter) -> SuperGroup:
    """Get the super-group for a given meter"""
    _, super_group = METER_TO_GROUP[meter]
    return super_group


def get_group(meter: Meter) -> MeterGroup:
    """Get the group for a given meter"""
    group, _ = METER_TO_GROUP[meter]
    return group


def get_meters_in_group(group: MeterGroup) -> List[Meter]:
    """Get all meters in a given group"""
    return GROUP_METERS[group]


def get_groups_in_super(super_group: SuperGroup) -> List[MeterGroup]:
    """Get all groups in a given super-group"""
    return SUPER_GROUPS[super_group]


def get_meters_in_super_group(super_group: SuperGroup) -> List[Meter]:
    """Get all individual meters in a given super-group (excludes aggregate meter)"""
    meters = []
    for group in get_groups_in_super(super_group):
        meters.extend(get_meters_in_group(group))
    return meters


def is_super_group_meter(meter: Meter) -> bool:
    """Check if a meter is a super-group aggregate meter"""
    return meter in SUPER_GROUP_METERS


def get_super_group_for_aggregate(meter: Meter) -> SuperGroup:
    """Get the super-group for a super-group aggregate meter"""
    if meter not in METER_TO_SUPER_GROUP:
        raise ValueError(f"{meter} is not a super-group aggregate meter")
    return METER_TO_SUPER_GROUP[meter]


def validate_hierarchy_complete() -> bool:
    """Validate that all 23 individual meters are accounted for + 5 super-group aggregates"""
    all_meters = set(Meter)
    mapped_meters = set(METER_TO_GROUP.keys())

    # Super-group meters should NOT be in METER_TO_GROUP
    individual_meters = all_meters - SUPER_GROUP_METERS

    if individual_meters != mapped_meters:
        missing = individual_meters - mapped_meters
        extra = mapped_meters - individual_meters
        if missing:
            print(f"Missing meters: {missing}")
        if extra:
            print(f"Extra meters: {extra}")
        return False

    # Validate counts
    if len(mapped_meters) != 23:
        print(f"Expected 23 individual meters, got {len(mapped_meters)}")
        return False

    if len(SUPER_GROUP_METERS) != 5:
        print(f"Expected 5 super-group meters, got {len(SUPER_GROUP_METERS)}")
        return False

    if len(all_meters) != 28:
        print(f"Expected 28 total meters (23 individual + 5 super-group), got {len(all_meters)}")
        return False

    return True


# Validate on import
assert validate_hierarchy_complete(), "Hierarchy is incomplete or has duplicates"

"""
Relationship Categories and Labels Module.

Provides:
- RelationshipCategory enum (determines compatibility mode)
- RelationshipLabel enum (gives LLM nuance)
- Helper functions to load label guidance for LLM prompts
"""

import json
from enum import Enum
from pathlib import Path
from typing import Optional


# =============================================================================
# Enums
# =============================================================================

class RelationshipCategory(str, Enum):
    """
    Main category - determines which compatibility mode to use.

    love -> romantic compatibility
    friend -> friendship compatibility
    family -> friendship compatibility
    coworker -> coworker compatibility
    other -> friendship compatibility
    """
    LOVE = "love"
    FRIEND = "friend"
    FAMILY = "family"
    COWORKER = "coworker"
    OTHER = "other"


class RelationshipLabel(str, Enum):
    """
    Sub-category label - gives LLM nuance for personalized guidance.

    Each label belongs to a category and has specific LLM guidance.
    """
    # Love
    CRUSH = "crush"
    DATING = "dating"
    SITUATIONSHIP = "situationship"
    PARTNER = "partner"
    BOYFRIEND = "boyfriend"
    GIRLFRIEND = "girlfriend"
    SPOUSE = "spouse"
    EX = "ex"

    # Friend
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    NEW_FRIEND = "new_friend"

    # Family
    MOTHER = "mother"
    FATHER = "father"
    SISTER = "sister"
    BROTHER = "brother"
    DAUGHTER = "daughter"
    SON = "son"
    GRANDPARENT = "grandparent"
    EXTENDED = "extended"

    # Coworker
    MANAGER = "manager"
    COLLEAGUE = "colleague"
    MENTOR = "mentor"
    MENTEE = "mentee"
    CLIENT = "client"
    BUSINESS_PARTNER = "business_partner"

    # Other
    ACQUAINTANCE = "acquaintance"
    NEIGHBOR = "neighbor"
    EX_FRIEND = "ex_friend"
    COMPLICATED = "complicated"


# =============================================================================
# Category to Compatibility Mode Mapping
# =============================================================================

CATEGORY_TO_COMPATIBILITY_MODE = {
    RelationshipCategory.LOVE: "romantic",
    RelationshipCategory.FRIEND: "friendship",
    RelationshipCategory.FAMILY: "friendship",
    RelationshipCategory.COWORKER: "coworker",
    RelationshipCategory.OTHER: "friendship",
}


# =============================================================================
# Label to Category Mapping
# =============================================================================

LABEL_TO_CATEGORY = {
    # Love
    RelationshipLabel.CRUSH: RelationshipCategory.LOVE,
    RelationshipLabel.DATING: RelationshipCategory.LOVE,
    RelationshipLabel.SITUATIONSHIP: RelationshipCategory.LOVE,
    RelationshipLabel.PARTNER: RelationshipCategory.LOVE,
    RelationshipLabel.BOYFRIEND: RelationshipCategory.LOVE,
    RelationshipLabel.GIRLFRIEND: RelationshipCategory.LOVE,
    RelationshipLabel.SPOUSE: RelationshipCategory.LOVE,
    RelationshipLabel.EX: RelationshipCategory.LOVE,

    # Friend
    RelationshipLabel.FRIEND: RelationshipCategory.FRIEND,
    RelationshipLabel.CLOSE_FRIEND: RelationshipCategory.FRIEND,
    RelationshipLabel.NEW_FRIEND: RelationshipCategory.FRIEND,

    # Family
    RelationshipLabel.MOTHER: RelationshipCategory.FAMILY,
    RelationshipLabel.FATHER: RelationshipCategory.FAMILY,
    RelationshipLabel.SISTER: RelationshipCategory.FAMILY,
    RelationshipLabel.BROTHER: RelationshipCategory.FAMILY,
    RelationshipLabel.DAUGHTER: RelationshipCategory.FAMILY,
    RelationshipLabel.SON: RelationshipCategory.FAMILY,
    RelationshipLabel.GRANDPARENT: RelationshipCategory.FAMILY,
    RelationshipLabel.EXTENDED: RelationshipCategory.FAMILY,

    # Coworker
    RelationshipLabel.MANAGER: RelationshipCategory.COWORKER,
    RelationshipLabel.COLLEAGUE: RelationshipCategory.COWORKER,
    RelationshipLabel.MENTOR: RelationshipCategory.COWORKER,
    RelationshipLabel.MENTEE: RelationshipCategory.COWORKER,
    RelationshipLabel.CLIENT: RelationshipCategory.COWORKER,
    RelationshipLabel.BUSINESS_PARTNER: RelationshipCategory.COWORKER,

    # Other
    RelationshipLabel.ACQUAINTANCE: RelationshipCategory.OTHER,
    RelationshipLabel.NEIGHBOR: RelationshipCategory.OTHER,
    RelationshipLabel.EX_FRIEND: RelationshipCategory.OTHER,
    RelationshipLabel.COMPLICATED: RelationshipCategory.OTHER,
}


# =============================================================================
# JSON Labels Loader
# =============================================================================

_labels_cache: Optional[dict] = None


def _load_labels() -> dict:
    """Load labels.json (cached)."""
    global _labels_cache
    if _labels_cache is None:
        labels_path = Path(__file__).parent / "labels.json"
        with open(labels_path) as f:
            _labels_cache = json.load(f)
    return _labels_cache


def get_llm_guidance(category: RelationshipCategory, label: RelationshipLabel) -> str:
    """
    Get LLM guidance text for a specific relationship label.

    Args:
        category: The relationship category
        label: The relationship label

    Returns:
        LLM guidance string for prompts
    """
    labels_data = _load_labels()
    category_labels = labels_data.get("labels", {}).get(category.value, {})
    label_data = category_labels.get(label.value, {})
    return label_data.get("llm_guidance", "")


def get_label_display_name(category: RelationshipCategory, label: RelationshipLabel) -> str:
    """
    Get display name for a relationship label.

    Args:
        category: The relationship category
        label: The relationship label

    Returns:
        Human-readable display name
    """
    labels_data = _load_labels()
    category_labels = labels_data.get("labels", {}).get(category.value, {})
    label_data = category_labels.get(label.value, {})
    return label_data.get("display_name", label.value.replace("_", " ").title())


def get_compatibility_mode(category: RelationshipCategory) -> str:
    """
    Get the compatibility mode for a category.

    Args:
        category: The relationship category

    Returns:
        Compatibility mode: "romantic", "friendship", or "coworker"
    """
    return CATEGORY_TO_COMPATIBILITY_MODE.get(category, "friendship")


def get_category_for_label(label: RelationshipLabel) -> RelationshipCategory:
    """
    Get the category for a given label.

    Args:
        label: The relationship label

    Returns:
        The parent category
    """
    return LABEL_TO_CATEGORY.get(label, RelationshipCategory.OTHER)


def get_all_labels_for_category(category: RelationshipCategory) -> list[RelationshipLabel]:
    """
    Get all labels that belong to a category.

    Args:
        category: The relationship category

    Returns:
        List of labels in that category
    """
    return [label for label, cat in LABEL_TO_CATEGORY.items() if cat == category]


# =============================================================================
# Backward Compatibility - Map old relationship_type to new system
# =============================================================================

def migrate_relationship_type(old_type: str) -> tuple[RelationshipCategory, RelationshipLabel]:
    """
    Migrate old relationship_type to new category/label system.

    Args:
        old_type: Old relationship type (friend, partner, family, coworker)

    Returns:
        Tuple of (category, label)
    """
    mapping = {
        "friend": (RelationshipCategory.FRIEND, RelationshipLabel.FRIEND),
        "partner": (RelationshipCategory.LOVE, RelationshipLabel.PARTNER),
        "family": (RelationshipCategory.FAMILY, RelationshipLabel.EXTENDED),
        "coworker": (RelationshipCategory.COWORKER, RelationshipLabel.COLLEAGUE),
    }
    return mapping.get(old_type.lower(), (RelationshipCategory.OTHER, RelationshipLabel.COMPLICATED))

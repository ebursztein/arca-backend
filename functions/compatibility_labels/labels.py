"""
Compatibility Labels Module

Loads and looks up labels, guidance, and descriptions for compatibility categories.
Uses JSON configuration files for each category/mode combination.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, TypedDict, cast


# Type definitions
class BandDef(TypedDict):
    id: str
    min: int
    max: int


class BucketLabel(TypedDict):
    label: str
    guidance: str


class CategoryMetadata(TypedDict):
    category_id: str
    display_name: str
    description: str
    sentence_template: Optional[str]


class PlanetMeanings(TypedDict, total=False):
    Moon: str
    Venus: str
    Neptune: str
    Mercury: str
    Mars: str
    Jupiter: str
    Saturn: str
    Pluto: str
    Sun: str
    Uranus: str
    Chiron: str
    Juno: str


class AstrologicalBasis(TypedDict, total=False):
    primary_planets: list[str]
    what_it_measures: str
    planet_meanings: PlanetMeanings


class CategoryLabelConfig(TypedDict):
    _schema_version: str
    _category: str
    _mode: Optional[str]
    metadata: CategoryMetadata
    bands: list[BandDef]
    bucket_labels: dict[str, BucketLabel]
    astrological_basis: Optional[AstrologicalBasis]


# Band IDs in order
BAND_IDS = ["very_low", "low", "mid", "high", "very_high"]

# Mode name mapping (API uses different names than file structure)
MODE_FILE_MAP = {
    "romantic": "romantic",
    "friendship": "friendship",
    "coworker": "coworker",
}

# Category ID mapping (code uses camelCase, files use snake_case)
CATEGORY_FILE_MAP = {
    "longTerm": "long_term",
    "sharedInterests": "shared_interests",
    "powerDynamics": "power_dynamics",
}


def get_labels_dir() -> Path:
    """Get the labels directory path."""
    return Path(__file__).parent / "labels"


@lru_cache(maxsize=32)
def load_category_labels(mode: str, category_id: str) -> Optional[CategoryLabelConfig]:
    """
    Load JSON config for a category.

    Args:
        mode: Relationship mode (romantic, friendship, coworker)
        category_id: Category identifier (emotional, communication, etc.)

    Returns:
        CategoryLabelConfig dict or None if not found
    """
    labels_dir = get_labels_dir()

    # Map mode to file directory
    mode_dir = MODE_FILE_MAP.get(mode, mode)

    # Map category ID to file name (camelCase -> snake_case)
    file_category_id = CATEGORY_FILE_MAP.get(category_id, category_id)

    # Build file path with mode prefix (e.g., romantic_emotional.json)
    file_path = labels_dir / mode_dir / f"{mode_dir}_{file_category_id}.json"

    if not file_path.exists():
        # Try without mode prefix for backwards compatibility
        file_path = labels_dir / mode_dir / f"{file_category_id}.json"

    if not file_path.exists():
        return None

    with open(file_path, "r") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_overall_labels() -> Optional[CategoryLabelConfig]:
    """Load the overall compatibility labels."""
    labels_dir = get_labels_dir()
    file_path = labels_dir / "overall.json"

    if not file_path.exists():
        return None

    with open(file_path, "r") as f:
        return json.load(f)


def get_band_for_score(score: float, bands: Optional[list[BandDef]] = None) -> str:
    """
    Map score to band ID.

    Args:
        score: Score value (0-100)
        bands: Optional band definitions (uses default if not provided)

    Returns:
        Band ID (very_low, low, mid, high, very_high)
    """
    if bands:
        for band in bands:
            if band["min"] <= score < band["max"]:
                return band["id"]
        # Handle edge case of exactly 100
        if score >= 100:
            return "very_high"
        return "very_low"

    # Default bands
    if score >= 80:
        return "very_high"
    if score >= 60:
        return "high"
    if score >= 40:
        return "mid"
    if score >= 20:
        return "low"
    return "very_low"


def get_category_label(mode: str, category_id: str, score: float) -> str:
    """
    Get the display label for a category score.

    Args:
        mode: Relationship mode
        category_id: Category identifier
        score: Score value (0-100)

    Returns:
        Label string (e.g., "Warm", "Soul-Level", "Combustible")
    """
    config = load_category_labels(mode, category_id)
    if not config:
        return ""

    bands = config.get("bands", [])
    band_id = get_band_for_score(score, bands)

    bucket_labels: dict[str, Any] = config.get("bucket_labels", {})
    bucket = bucket_labels.get(band_id, {})
    return str(bucket.get("label", ""))


def get_category_guidance(mode: str, category_id: str, score: float) -> str:
    """
    Get the LLM guidance string for a score band.

    Args:
        mode: Relationship mode
        category_id: Category identifier
        score: Score value (0-100)

    Returns:
        Guidance string for LLM prompting
    """
    config = load_category_labels(mode, category_id)
    if not config:
        return ""

    bands = config.get("bands", [])
    band_id = get_band_for_score(score, bands)

    bucket_labels: dict[str, Any] = config.get("bucket_labels", {})
    bucket = bucket_labels.get(band_id, {})
    return str(bucket.get("guidance", ""))


def get_category_description(mode: str, category_id: str) -> str:
    """
    Get the category description from metadata.

    Args:
        mode: Relationship mode
        category_id: Category identifier

    Returns:
        Description string for iOS display
    """
    config = load_category_labels(mode, category_id)
    if not config:
        return ""

    metadata = config.get("metadata", {})
    return metadata.get("description", "")


def get_category_display_name(mode: str, category_id: str) -> str:
    """
    Get the category display name from metadata.

    Args:
        mode: Relationship mode
        category_id: Category identifier

    Returns:
        Display name string (e.g., "Emotional Connection")
    """
    config = load_category_labels(mode, category_id)
    if not config:
        return category_id.replace("_", " ").title()

    metadata = config.get("metadata", {})
    return metadata.get("display_name", category_id.replace("_", " ").title())


def get_planet_meaning(mode: str, category_id: str, planet: str) -> str:
    """
    Get planet meaning from astrological_basis.planet_meanings.

    Args:
        mode: Relationship mode
        category_id: Category identifier
        planet: Planet name (e.g., "Moon", "Venus")

    Returns:
        Meaning string or empty if not found
    """
    config = load_category_labels(mode, category_id)
    if not config:
        return ""

    astro_basis = config.get("astrological_basis") or {}
    if not astro_basis:
        return ""

    planet_meanings: dict[str, str] = cast(dict[str, Any], astro_basis).get("planet_meanings", {})
    # Try exact match first, then title case
    result = planet_meanings.get(planet, planet_meanings.get(planet.title(), ""))
    return str(result) if result else ""


def get_overall_label(score: float) -> str:
    """
    Get the overall compatibility label.

    Args:
        score: Overall score (0-100)

    Returns:
        Label string (e.g., "Solid", "Seamless", "Volatile")
    """
    config = load_overall_labels()
    if not config:
        return ""

    bands = config.get("bands", [])
    band_id = get_band_for_score(score, bands)

    bucket_labels: dict[str, Any] = config.get("bucket_labels", {})
    bucket = bucket_labels.get(band_id, {})
    return str(bucket.get("label", ""))


def get_overall_guidance(score: float) -> str:
    """
    Get the overall compatibility LLM guidance.

    Args:
        score: Overall score (0-100)

    Returns:
        Guidance string for LLM prompting
    """
    config = load_overall_labels()
    if not config:
        return ""

    bands = config.get("bands", [])
    band_id = get_band_for_score(score, bands)

    bucket_labels: dict[str, Any] = config.get("bucket_labels", {})
    bucket = bucket_labels.get(band_id, {})
    return str(bucket.get("guidance", ""))


def generate_driving_aspect_summary(
    user_planet: str,
    their_planet: str,
    aspect_type: str,
    is_harmonious: bool,
    mode: str,
    category_id: str,
) -> str:
    """
    Generate human-readable summary using planet_meanings from JSON.

    Args:
        user_planet: User's planet name
        their_planet: Connection's planet name
        aspect_type: Type of aspect (trine, square, etc.)
        is_harmonious: Whether the aspect is harmonious
        mode: Relationship mode
        category_id: Category identifier

    Returns:
        Human-readable summary string
    """
    # Get planet meanings from config
    user_meaning = get_planet_meaning(mode, category_id, user_planet)
    their_meaning = get_planet_meaning(mode, category_id, their_planet)

    # Fallback meanings if not in config
    default_meanings = {
        "sun": "core identity",
        "moon": "emotional needs",
        "mercury": "communication style",
        "venus": "love style",
        "mars": "drive and passion",
        "jupiter": "growth and expansion",
        "saturn": "commitment and structure",
        "uranus": "independence",
        "neptune": "dreams and intuition",
        "pluto": "transformation",
        "north node": "growth direction",
        "south node": "past patterns",
    }

    if not user_meaning:
        user_meaning = default_meanings.get(user_planet.lower(), user_planet)
    if not their_meaning:
        their_meaning = default_meanings.get(their_planet.lower(), their_planet)

    # Aspect verbs
    aspect_verbs = {
        "conjunction": ("merges with", "intensely connects to"),
        "trine": ("flows easily with", "harmonizes with"),
        "sextile": ("supports", "complements"),
        "square": ("challenges", "creates tension with"),
        "opposition": ("balances", "polarizes with"),
        "quincunx": ("adjusts to", "adapts to"),
    }

    verb_pair = aspect_verbs.get(aspect_type, ("connects to", "relates to"))
    verb = verb_pair[0] if is_harmonious else verb_pair[1]

    return f"Your {user_meaning} ({user_planet.title()}) {verb} their {their_meaning} ({their_planet.title()})"


# Headline guidance matrix (25-case)
# Maps (top_band, bottom_band) -> (pattern, conjunction, tone)
COMPAT_HEADLINE_MATRIX: dict[tuple[str, str], tuple[str, str, str]] = {
    # very_high (80-100) + X
    ("very_high", "very_high"): ("stellar_match", "and", "celebrate exceptional alignment"),
    ("very_high", "high"): ("strong_foundation", "and", "lead with strength, note solid support"),
    ("very_high", "mid"): ("bright_with_work", "but", "highlight the strength, acknowledge room to grow"),
    ("very_high", "low"): ("strong_contrast", "but", "celebrate the win, honestly name the gap"),
    ("very_high", "very_low"): ("stark_divide", "but", "anchor to the strength, be direct about the struggle"),

    # high (60-80) + X
    ("high", "very_high"): ("solid_with_spark", "and", "both positive, let the stronger shine"),
    ("high", "high"): ("reliable_bond", "and", "steady, dependable connection"),
    ("high", "mid"): ("mostly_positive", "but", "good foundation, one area needs attention"),
    ("high", "low"): ("partial_fit", "but", "acknowledge what works, name the weak spot"),
    ("high", "very_low"): ("uneven_match", "but", "hold onto the good, be real about the hard"),

    # mid (40-60) + X
    ("mid", "very_high"): ("hidden_gem", "but", "name the average, pivot to the bright spot"),
    ("mid", "high"): ("potential_exists", "but", "challenges present, foundation exists"),
    ("mid", "mid"): ("neutral_ground", "and", "neither great nor terrible, effort-dependent"),
    ("mid", "low"): ("uphill_road", "and", "honest about challenges, suggest patience"),
    ("mid", "very_low"): ("heavy_lift", "and", "validate the strain, focus on boundaries"),

    # low (20-40) + X
    ("low", "very_high"): ("lifeline_present", "but", "acknowledge the difficulty, find the lifeline"),
    ("low", "high"): ("some_hope", "but", "name the friction, point to what works"),
    ("low", "mid"): ("mostly_struggling", "and", "validate the effort, suggest realistic expectations"),
    ("low", "low"): ("rough_terrain", "and", "honest about friction, both need work"),
    ("low", "very_low"): ("very_hard", "and", "be direct about difficulty, focus on self-care"),

    # very_low (0-20) + X
    ("very_low", "very_high"): ("extreme_contrast", "but", "one bright light in the dark, name both"),
    ("very_low", "high"): ("glimmer_exists", "but", "mostly struggling, but something works"),
    ("very_low", "mid"): ("largely_draining", "and", "honest about the toll, suggest boundaries"),
    ("very_low", "low"): ("very_rough", "and", "validate how hard this is, protect yourself"),
    ("very_low", "very_low"): ("fundamental_mismatch", "and", "be honest about friction, prioritize self-protection"),
}


class HeadlineGuidance(TypedDict):
    pattern: str
    conjunction: str
    tone: str
    top_category: dict
    bottom_category: dict
    instruction: str


def generate_compat_headline_guidance(
    categories: list[dict],
    mode: str,
) -> HeadlineGuidance:
    """
    Generate headline guidance based on top and bottom categories.

    Args:
        categories: List of category dicts with 'id', 'score', 'name'
        mode: Relationship mode for label lookup

    Returns:
        HeadlineGuidance with pattern, conjunction, tone, and instruction
    """
    if not categories:
        return HeadlineGuidance(
            pattern="neutral_ground",
            conjunction="and",
            tone="balanced perspective",
            top_category={},
            bottom_category={},
            instruction="Write a balanced overview of this connection."
        )

    # Sort by score to find top and bottom
    sorted_cats = sorted(categories, key=lambda c: c.get("score", 50), reverse=True)
    top = sorted_cats[0]
    bottom = sorted_cats[-1]

    top_score = top.get("score", 50)
    bottom_score = bottom.get("score", 50)

    top_band = get_band_for_score(top_score)
    bottom_band = get_band_for_score(bottom_score)

    # Get matrix guidance
    matrix_key = (top_band, bottom_band)
    pattern, conjunction, tone = COMPAT_HEADLINE_MATRIX.get(
        matrix_key,
        ("neutral_ground", "and", "balanced perspective")
    )

    # Get labels for top and bottom
    top_label = get_category_label(mode, top.get("id", ""), top_score)
    bottom_label = get_category_label(mode, bottom.get("id", ""), bottom_score)

    top_guidance = get_category_guidance(mode, top.get("id", ""), top_score)
    bottom_guidance = get_category_guidance(mode, bottom.get("id", ""), bottom_score)

    # Build instruction
    instruction = (
        f"When writing about this connection, lead with {top.get('name', 'the strongest area')} "
        f"(label: \"{top_label}\") {conjunction} acknowledge {bottom.get('name', 'the weakest area')} "
        f"(label: \"{bottom_label}\"). Tone: {tone}."
    )

    return HeadlineGuidance(
        pattern=pattern,
        conjunction=conjunction,
        tone=tone,
        top_category={
            "id": top.get("id", ""),
            "name": top.get("name", ""),
            "score": top_score,
            "band": top_band,
            "label": top_label,
            "guidance": top_guidance,
        },
        bottom_category={
            "id": bottom.get("id", ""),
            "name": bottom.get("name", ""),
            "score": bottom_score,
            "band": bottom_band,
            "label": bottom_label,
            "guidance": bottom_guidance,
        },
        instruction=instruction,
    )


def get_all_category_labels_for_mode(mode: str, categories: list[dict]) -> list[dict]:
    """
    Get labels and descriptions for all categories in a mode.

    Args:
        mode: Relationship mode
        categories: List of category dicts with 'id' and 'score'

    Returns:
        List of enriched category dicts with label, description, guidance
    """
    enriched = []
    for cat in categories:
        cat_id = cat.get("id", "")
        score = cat.get("score", 50)

        enriched.append({
            "id": cat_id,
            "name": cat.get("name", get_category_display_name(mode, cat_id)),
            "score": score,
            "band": get_band_for_score(score),
            "label": get_category_label(mode, cat_id, score),
            "description": get_category_description(mode, cat_id),
            "guidance": get_category_guidance(mode, cat_id, score),
        })

    return enriched

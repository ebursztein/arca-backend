"""
Compatibility Module - Synastry Analysis

Calculates astrological compatibility between two natal charts.
Provides scores across multiple relationship modes (romantic, friendship, coworker).

Key Concepts:
- Synastry: Comparing aspects between two people's natal charts
- Composite: Midpoints between two charts (represents the relationship itself)
- Categories: Different life areas scored separately per relationship type
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

from astro import (
    compute_birth_chart,
    NatalChartData,
    ZodiacSign,
    AspectType,
    Planet,
)


# =============================================================================
# Constants - Aspect Configuration
# =============================================================================

# Aspect angles and their nature
ASPECT_CONFIG: dict[str, dict[str, int | str]] = {
    "conjunction": {"angle": 0, "orb": 10, "nature": "variable"},
    "sextile": {"angle": 60, "orb": 6, "nature": "harmonious"},
    "square": {"angle": 90, "orb": 8, "nature": "challenging"},
    "trine": {"angle": 120, "orb": 8, "nature": "harmonious"},
    "quincunx": {"angle": 150, "orb": 5, "nature": "challenging"},
    "opposition": {"angle": 180, "orb": 10, "nature": "challenging"},
}

# Conjunction nature depends on planets involved
CHALLENGING_CONJUNCTIONS = {
    ("saturn", "mars"), ("mars", "saturn"),
    ("saturn", "moon"), ("moon", "saturn"),
    ("pluto", "sun"), ("sun", "pluto"),
    ("pluto", "moon"), ("moon", "pluto"),
    ("saturn", "venus"), ("venus", "saturn"),
}

# Orb weight by tightness
def get_orb_weight(orb: float) -> float:
    """Get weight multiplier based on orb tightness."""
    if orb <= 2:
        return 1.0
    elif orb <= 5:
        return 0.75
    elif orb <= 8:
        return 0.5
    elif orb <= 10:
        return 0.25
    return 0.0


# Aspect type weights - how much each aspect type contributes to scoring
# Conjunction is strongest (binding), sextile/quincunx are weakest
ASPECT_TYPE_WEIGHTS: dict[str, float] = {
    "conjunction": 1.2,
    "trine": 1.0,
    "opposition": 0.9,
    "square": 0.8,
    "sextile": 0.7,
    "quincunx": 0.6,
}


# =============================================================================
# Element Compatibility (Phase 1b)
# =============================================================================

# Element compatibility matrix
# Fire + Air = harmonious (both active/yang)
# Earth + Water = harmonious (both receptive/yin)
# Same element = very harmonious
# Fire + Water = challenging (steam/conflict)
# Other combinations = neutral
ELEMENT_COMPATIBILITY: dict[tuple[str, str], float] = {
    # Same element - very compatible
    ("fire", "fire"): 0.3,
    ("earth", "earth"): 0.3,
    ("air", "air"): 0.3,
    ("water", "water"): 0.3,
    # Complementary pairs - compatible
    ("fire", "air"): 0.2,
    ("air", "fire"): 0.2,
    ("earth", "water"): 0.2,
    ("water", "earth"): 0.2,
    # Challenging pairs
    ("fire", "water"): -0.2,
    ("water", "fire"): -0.2,
    ("fire", "earth"): -0.1,
    ("earth", "fire"): -0.1,
    # Neutral pairs
    ("air", "water"): 0.0,
    ("water", "air"): 0.0,
    ("air", "earth"): 0.0,
    ("earth", "air"): 0.0,
}

# Which categories use element scoring and which planet pairs to check
# Format: category_id -> list of (user_planet, their_planet) to check elements
CATEGORY_ELEMENT_PAIRS: dict[str, list[tuple[str, str]]] = {
    "emotional": [("moon", "moon"), ("sun", "moon"), ("moon", "sun")],
    "attraction": [("venus", "mars"), ("mars", "venus")],
    "values": [("sun", "venus"), ("venus", "sun"), ("sun", "sun")],
}

# Maximum element bonus/penalty contribution
ELEMENT_MAX_CONTRIBUTION = 0.3


def get_element_score(
    chart1: "NatalChartData",
    chart2: "NatalChartData",
    planet_pairs: list[tuple[str, str]]
) -> float:
    """
    Calculate element compatibility score for given planet pairs.

    Returns average element compatibility across all pairs, clamped to [-0.3, +0.3].
    """
    if not planet_pairs:
        return 0.0

    scores = []
    for p1_name, p2_name in planet_pairs:
        # Find planets in charts
        p1 = next((p for p in chart1.planets if p.name.value == p1_name), None)
        p2 = next((p for p in chart2.planets if p.name.value == p2_name), None)

        if p1 and p2:
            e1 = p1.element.value
            e2 = p2.element.value
            compat = ELEMENT_COMPATIBILITY.get((e1, e2), 0.0)
            scores.append(compat)

    if not scores:
        return 0.0

    avg_score = sum(scores) / len(scores)
    return max(-ELEMENT_MAX_CONTRIBUTION, min(ELEMENT_MAX_CONTRIBUTION, avg_score))


# =============================================================================
# Score Smoothing Configuration (Phase 2)
# =============================================================================
# Each category uses different planets for chart-based variation,
# different sigmoid steepness, and different variation amplitude.
# This creates natural distribution without hard clamping.

import math

CATEGORY_SMOOTHING_CONFIG: dict[str, dict] = {
    "attraction": {
        "planets": ["venus", "mars"],  # Passion planets
        "steepness": 0.028,  # Moderate compression
        "max_var": 12,  # More variation - attraction is volatile
    },
    "communication": {
        "planets": ["mercury"],
        "steepness": 0.030,
        "max_var": 8,
    },
    "emotional": {
        "planets": ["moon"],
        "steepness": 0.025,  # Gentler - emotions are nuanced
        "max_var": 10,
    },
    "longTerm": {
        "planets": ["saturn"],
        "steepness": 0.022,  # Gentlest - long term is most stable
        "max_var": 15,  # More variation to smooth bimodal tendency
    },
    "growth": {
        "planets": ["jupiter", "north node"],
        "steepness": 0.030,
        "max_var": 8,
    },
    "values": {
        "planets": ["sun", "venus"],
        "steepness": 0.028,
        "max_var": 10,
    },
    # Friendship categories
    "fun": {
        "planets": ["venus", "jupiter"],
        "steepness": 0.028,
        "max_var": 10,
    },
    "loyalty": {
        "planets": ["saturn", "moon"],
        "steepness": 0.025,
        "max_var": 12,
    },
    "sharedInterests": {
        "planets": ["mercury", "jupiter"],
        "steepness": 0.028,
        "max_var": 8,
    },
    # Coworker categories
    "collaboration": {
        "planets": ["mercury", "mars"],
        "steepness": 0.028,
        "max_var": 10,
    },
    "reliability": {
        "planets": ["saturn"],
        "steepness": 0.025,
        "max_var": 12,
    },
    "ambition": {
        "planets": ["mars", "jupiter"],
        "steepness": 0.028,
        "max_var": 10,
    },
    "powerDynamics": {
        "planets": ["pluto", "saturn"],
        "steepness": 0.025,
        "max_var": 12,
    },
}


def _sigmoid_compress(score: float, steepness: float = 0.025) -> float:
    """
    Compress score using sigmoid function.
    Maps any input to (0, 100) range smoothly.
    No hard clamping needed.

    The sigmoid naturally avoids true 0 or 100 - extreme inputs
    asymptotically approach the bounds but never reach them.
    """
    # Sigmoid outputs 0-1, then scale to 0-100
    sigmoid_val = 1 / (1 + math.exp(-steepness * score))
    return sigmoid_val * 100


def _get_planet_degrees_from_chart(chart: "NatalChartData", planet_names: list[str]) -> list[float]:
    """Extract absolute degrees for specified planets from chart."""
    degrees = []
    for planet in chart.planets:
        name = planet.get("name", "").lower() if isinstance(planet, dict) else planet.name.lower()
        if name in [pn.lower() for pn in planet_names]:
            degree = planet.get("absolute_degree", 0) if isinstance(planet, dict) else planet.absolute_degree
            degrees.append(degree)
    return degrees if degrees else [0.0]


def _chart_variation_for_category(
    chart1: "NatalChartData",
    chart2: "NatalChartData",
    category_id: str,
) -> float:
    """
    Calculate deterministic variation based on category-specific planet positions.
    Uses fractional degrees to create smooth, consistent variation per pair.
    """
    config = CATEGORY_SMOOTHING_CONFIG.get(category_id, {
        "planets": ["sun"],
        "max_var": 10,
    })
    planet_names = config["planets"]
    max_var = config["max_var"]

    degrees1 = _get_planet_degrees_from_chart(chart1, planet_names)
    degrees2 = _get_planet_degrees_from_chart(chart2, planet_names)

    # Use degree within sign (0-30) for smooth distribution
    frac1 = sum(d % 30 for d in degrees1) / 30
    frac2 = sum(d % 30 for d in degrees2) / 30

    # Add category-specific seed for uniqueness between categories
    seed = hash(category_id) % 1000 / 1000
    combined = (frac1 + frac2 + seed) % 2  # 0-2 range

    # Map to [-max_var, +max_var]
    return (combined - 1) * max_var


def _smooth_category_score(
    raw_score: float,
    chart1: Optional["NatalChartData"],
    chart2: Optional["NatalChartData"],
    category_id: str,
) -> int:
    """
    Apply category-specific smoothing: variation first, then sigmoid.
    Order: raw_score + chart_variation -> sigmoid_compress

    Returns score in 0-100 range where:
    - 0-30: Challenging
    - 30-50: Below average
    - 50: Neutral
    - 50-70: Above average
    - 70-100: Flowing/harmonious
    """
    if chart1 is None or chart2 is None:
        # Fallback to simple sigmoid if charts not available
        config = CATEGORY_SMOOTHING_CONFIG.get(category_id, {"steepness": 0.025})
        return int(round(_sigmoid_compress(raw_score, steepness=config.get("steepness", 0.025))))

    config = CATEGORY_SMOOTHING_CONFIG.get(category_id, {
        "planets": ["sun"],
        "steepness": 0.025,
        "max_var": 10,
    })

    # Step 1: Add chart-based variation to raw score
    variation = _chart_variation_for_category(chart1, chart2, category_id)
    adjusted = raw_score + variation

    # Step 2: Apply sigmoid compression (naturally bounded to 0-100)
    smoothed = _sigmoid_compress(adjusted, steepness=config.get("steepness", 0.025))

    return int(round(smoothed))


# =============================================================================
# Category Definitions by Relationship Mode
# =============================================================================

# Each category maps to a list of planet pairs to check
# Format: (planet1, planet2) where we check aspects between chart1.planet1 and chart2.planet2

# Expanded planet pairs to ensure 5+ signals per category (reduces bimodal extremes)
ROMANTIC_CATEGORIES = {
    "emotional": [
        # Core: Moon connections
        ("moon", "moon"), ("moon", "venus"), ("venus", "moon"),
        ("moon", "neptune"), ("neptune", "moon"),
        # Sun-Moon cross aspects for emotional understanding
        ("sun", "moon"), ("moon", "sun"),
        # Venus-Neptune for romantic idealization
        ("venus", "neptune"), ("neptune", "venus"),
        # Added Phase 1b: More emotional signals
        ("moon", "saturn"), ("saturn", "moon"),  # Emotional security
        ("venus", "venus"),  # Affection style
        ("sun", "neptune"), ("neptune", "sun"),  # Idealization of identity
    ],
    "communication": [
        # Core: Mercury connections
        ("mercury", "mercury"), ("mercury", "moon"), ("moon", "mercury"),
        ("mercury", "venus"), ("venus", "mercury"),
        # Sun-Mercury for understanding each other's core
        ("sun", "mercury"), ("mercury", "sun"),
        # Mercury-Jupiter for expanding dialogue
        ("mercury", "jupiter"), ("jupiter", "mercury"),
        # Added Phase 1b: More communication signals
        ("mercury", "mars"), ("mars", "mercury"),  # Direct communication
        ("mercury", "saturn"), ("saturn", "mercury"),  # Serious dialogue
        ("mercury", "uranus"), ("uranus", "mercury"),  # Exciting ideas
    ],
    "attraction": [
        # Core: Venus-Mars chemistry
        ("venus", "mars"), ("mars", "venus"),
        ("mars", "mars"), ("venus", "venus"),
        # Sun connections for magnetic attraction
        ("sun", "venus"), ("venus", "sun"),
        ("sun", "mars"), ("mars", "sun"),
        # Pluto for intensity
        ("venus", "pluto"), ("pluto", "venus"),
        ("mars", "pluto"), ("pluto", "mars"),
    ],
    "values": [
        # Core: Venus-Jupiter (values and growth)
        ("venus", "venus"), ("jupiter", "jupiter"),
        ("sun", "jupiter"), ("jupiter", "sun"),
        ("venus", "jupiter"), ("jupiter", "venus"),
        # Sun-Sun for core value alignment
        ("sun", "sun"),
        # Moon-Jupiter for emotional values
        ("moon", "jupiter"), ("jupiter", "moon"),
        # Added Phase 1b: More value signals
        ("sun", "venus"), ("venus", "sun"),  # Core aesthetic values
        ("moon", "venus"), ("venus", "moon"),  # Emotional values
        ("saturn", "jupiter"), ("jupiter", "saturn"),  # Growth vs stability values
    ],
    "longTerm": [
        # Core: Saturn connections (commitment and structure)
        ("saturn", "sun"), ("sun", "saturn"),
        ("saturn", "moon"), ("moon", "saturn"),
        ("saturn", "venus"), ("venus", "saturn"),
        ("sun", "sun"),
        # Saturn-Saturn for shared approach to responsibility
        ("saturn", "saturn"),
        # Saturn-Jupiter for balancing growth and stability
        ("saturn", "jupiter"), ("jupiter", "saturn"),
    ],
    "growth": [
        # Core: Pluto connections (transformation)
        ("pluto", "sun"), ("sun", "pluto"),
        ("pluto", "moon"), ("moon", "pluto"),
        ("pluto", "venus"), ("venus", "pluto"),
        # North Node: future growth direction
        ("north node", "sun"), ("sun", "north node"),
        ("north node", "moon"), ("moon", "north node"),
        ("north node", "venus"), ("venus", "north node"),
        # South Node: past patterns to release/transform
        ("south node", "sun"), ("sun", "south node"),
        ("south node", "moon"), ("moon", "south node"),
        ("south node", "saturn"), ("saturn", "south node"),
        # Jupiter-Pluto for transformative growth
        ("jupiter", "pluto"), ("pluto", "jupiter"),
    ],
}

FRIENDSHIP_CATEGORIES = {
    "emotional": [
        # Core: Moon connections
        ("moon", "moon"), ("moon", "venus"), ("venus", "moon"),
        ("sun", "moon"), ("moon", "sun"),
        # Added: Venus-Venus for affection
        ("venus", "venus"),
        # Added: Neptune for intuitive understanding
        ("moon", "neptune"), ("neptune", "moon"),
    ],
    "communication": [
        # Core: Mercury connections
        ("mercury", "mercury"), ("mercury", "jupiter"), ("jupiter", "mercury"),
        ("mercury", "sun"), ("sun", "mercury"),
        # Added: Mercury-Moon for emotional communication
        ("mercury", "moon"), ("moon", "mercury"),
        # Added: Mercury-Uranus for exciting ideas
        ("mercury", "uranus"), ("uranus", "mercury"),
    ],
    "fun": [
        # Core: Jupiter and Sun (joy and vitality)
        ("jupiter", "jupiter"), ("sun", "sun"),
        ("mars", "jupiter"), ("jupiter", "mars"),
        ("venus", "jupiter"), ("jupiter", "venus"),
        # Added: Sun-Jupiter for shared enthusiasm
        ("sun", "jupiter"), ("jupiter", "sun"),
        # Added: Mars-Mars for active fun
        ("mars", "mars"),
        # Added: Uranus for spontaneity
        ("jupiter", "uranus"), ("uranus", "jupiter"),
    ],
    "loyalty": [
        # Core: Saturn connections
        ("saturn", "moon"), ("moon", "saturn"),
        ("saturn", "sun"), ("sun", "saturn"),
        # Added: Saturn-Saturn for mutual reliability
        ("saturn", "saturn"),
        # Added: Saturn-Venus for lasting affection
        ("saturn", "venus"), ("venus", "saturn"),
        # Added: Moon-Moon for emotional loyalty
        ("moon", "moon"),
    ],
    "sharedInterests": [
        # Core: Venus and Mercury connections
        ("venus", "venus"), ("mercury", "venus"), ("venus", "mercury"),
        ("moon", "venus"), ("venus", "moon"),
        # Added: Mercury-Mercury for intellectual interests
        ("mercury", "mercury"),
        # Added: Jupiter-Venus for cultural interests
        ("jupiter", "venus"), ("venus", "jupiter"),
    ],
}

COWORKER_CATEGORIES = {
    "communication": [
        # Core: Mercury connections
        ("mercury", "mercury"), ("mercury", "saturn"), ("saturn", "mercury"),
        ("mercury", "mars"), ("mars", "mercury"),
        # Added: Sun-Mercury for clear direction
        ("sun", "mercury"), ("mercury", "sun"),
        # Added: Mercury-Jupiter for big picture communication
        ("mercury", "jupiter"), ("jupiter", "mercury"),
    ],
    "collaboration": [
        # Core: Sun and Mars (leadership and action)
        ("sun", "sun"), ("mars", "mars"),
        ("sun", "mars"), ("mars", "sun"),
        # Added: Jupiter connections for growth-oriented teamwork
        ("sun", "jupiter"), ("jupiter", "sun"),
        ("mars", "jupiter"), ("jupiter", "mars"),
        # Added: Venus-Mars for complementary skills
        ("venus", "mars"), ("mars", "venus"),
    ],
    "reliability": [
        # Core: Saturn connections
        ("saturn", "sun"), ("sun", "saturn"),
        ("saturn", "moon"), ("moon", "saturn"),
        ("saturn", "saturn"),
        # Added: Saturn-Mercury for consistent communication
        ("saturn", "mercury"), ("mercury", "saturn"),
        # Added: Saturn-Mars for disciplined execution
        ("saturn", "mars"), ("mars", "saturn"),
    ],
    "ambition": [
        # Core: Mars-Saturn-Jupiter triangle
        ("mars", "saturn"), ("saturn", "mars"),
        ("jupiter", "saturn"), ("saturn", "jupiter"),
        ("mars", "jupiter"), ("jupiter", "mars"),
        # Added: Sun-Saturn for career focus
        ("sun", "saturn"), ("saturn", "sun"),
        # Added: Pluto for transformative ambition
        ("pluto", "jupiter"), ("jupiter", "pluto"),
    ],
    "powerDynamics": [
        # Core: Pluto connections
        ("pluto", "sun"), ("sun", "pluto"),
        ("pluto", "mars"), ("mars", "pluto"),
        # Added: Pluto-Saturn for structural power
        ("pluto", "saturn"), ("saturn", "pluto"),
        # Added: Sun-Sun for ego dynamics
        ("sun", "sun"),
        # Added: Mars-Mars for competition/cooperation
        ("mars", "mars"),
    ],
}

# Category display names
CATEGORY_NAMES = {
    # Romantic
    "emotional": "Emotional Connection",
    "communication": "Communication",
    "attraction": "Attraction",
    "values": "Shared Values",
    "longTerm": "Long-term Potential",
    "growth": "Growth Together",
    # Friendship
    "fun": "Fun & Adventure",
    "loyalty": "Loyalty & Support",
    "sharedInterests": "Shared Interests",
    # Coworker
    "collaboration": "Collaboration",
    "reliability": "Reliability",
    "ambition": "Ambition Alignment",
    "powerDynamics": "Power Dynamics",
}


# =============================================================================
# Pydantic Models
# =============================================================================

# Relationship type mapping from connection's relationship_category
RelationshipType = Literal["romantic", "friendship", "coworker"]

CATEGORY_TO_MODE: dict[str, RelationshipType] = {
    "love": "romantic",
    "friend": "friendship",
    "coworker": "coworker",
    "family": "friendship",  # Family uses friendship categories
    "other": "friendship",   # Default to friendship
}


class SynastryAspect(BaseModel):
    """A single aspect between two charts. Used for iOS chart rendering."""
    id: str = Field(min_length=1, max_length=32, description="Unique aspect ID (e.g., 'asp_001')")
    user_planet: str = Field(min_length=1, max_length=32, description="Planet from user's chart (e.g., 'venus')")
    their_planet: str = Field(min_length=1, max_length=32, description="Planet from connection's chart (e.g., 'mars')")
    aspect_type: str = Field(min_length=1, max_length=32, description="Aspect type: conjunction, trine, square, sextile, opposition, quincunx")
    orb: float = Field(ge=0, le=20, description="Orb in degrees (tighter = stronger)")
    is_harmonious: bool = Field(description="True if supportive (trine/sextile), False if challenging (square/opposition)")


class DrivingAspect(BaseModel):
    """A simplified aspect for iOS display with human-readable meanings.

    Used to show users WHY a category score is what it is.
    """
    aspect_id: str = Field(description="Reference to full aspect in aspects list (e.g., 'asp_001')")
    user_planet: str = Field(description="Your planet (e.g., 'Moon')")
    their_planet: str = Field(description="Their planet (e.g., 'Venus')")
    aspect_type: str = Field(description="trine, square, conjunction, etc.")
    is_harmonious: bool = Field(description="True if supportive, False if challenging")
    summary: str = Field(description="Human-readable summary (e.g., 'Your emotional needs flow easily with their love style')")


class CompatibilityCategory(BaseModel):
    """A single compatibility category with score and LLM insight.

    Categories vary by relationship type:
    - Romantic: emotional, communication, attraction, values, longTerm, growth
    - Friendship: emotional, communication, fun, loyalty, sharedInterests
    - Coworker: communication, collaboration, reliability, ambition, powerDynamics
    """
    id: str = Field(description="Category ID for iOS state management")
    name: str = Field(description="Display name (e.g., 'Emotional Connection')")
    score: int = Field(ge=0, le=100, description="Category score: 0 (challenging) to 100 (flowing), 50 is neutral")
    insight: Optional[str] = Field(None, description="LLM-generated 1-2 sentence insight for this category")
    aspect_ids: list[str] = Field(default_factory=list, description="Top 3-5 aspect IDs driving this score, ordered by tightest orb")

    # NEW fields from labels system
    label: str = Field(default="", description="Band label from JSON config (e.g., 'Warm', 'Soul-Level', 'Combustible')")
    description: str = Field(default="", description="What this category measures (for iOS display)")
    driving_aspects: list[DrivingAspect] = Field(default_factory=list, description="Top aspects with human-readable meanings explaining WHY the score is what it is")


class ModeCompatibility(BaseModel):
    """Compatibility scores for the requested relationship type."""
    type: RelationshipType = Field(description="The relationship type: romantic, friendship, or coworker")
    overall_score: int = Field(ge=0, le=100, description="Overall compatibility score (0-100)")
    overall_label: str = Field(default="", description="Overall band label (e.g., 'Solid', 'Seamless', 'Volatile')")
    vibe_phrase: Optional[str] = Field(None, description="Short energy label. Romantic: 'Slow Burn', 'Electric'. Friendship: 'Ride or Die'. Coworker: 'Power Partners'")
    categories: list[CompatibilityCategory] = Field(description="Category breakdowns with scores and insights")


class Composite(BaseModel):
    """The composite chart - represents the relationship itself as an entity.

    Calculated from midpoints between both charts.
    """
    sun_sign: str = Field(description="Composite Sun sign - the relationship's core purpose (e.g., 'taurus')")
    moon_sign: str = Field(description="Composite Moon sign - the relationship's emotional center (e.g., 'aquarius')")
    rising_sign: Optional[str] = Field(None, description="Composite Rising sign - how others perceive the relationship. Null if birth time unknown for either person.")
    dominant_element: str = Field(description="Dominant element (fire/earth/air/water). Use as fallback display when rising_sign is null.")
    purpose: Optional[str] = Field(None, description="LLM-generated 1-2 sentences on why this relationship exists")


class Karmic(BaseModel):
    """Karmic/fated connection analysis based on North/South Node aspects.

    Only ~20-25% of pairs will have is_karmic=True, making it feel
    special when it appears.
    """
    is_karmic: bool = Field(description="True if tight Node aspects exist (orb < 3 deg for Sun/Moon/Saturn)")
    theme: Optional[str] = Field(None, description="Primary karmic theme if applicable (e.g., 'Past-life connection through Saturn')")
    destiny_note: Optional[str] = Field(None, description="LLM-generated 1-2 sentences about the fated nature of this bond")


# Internal model for LLM prompting (not exposed in API response)
class KarmicAspectInternal(BaseModel):
    """Internal: A single karmic aspect for LLM context. Not in API response."""
    planet: str
    planet_owner: str
    node: str
    node_owner: str
    aspect_type: str
    orb: float
    interpretation_hint: str


class CompatibilityResult(BaseModel):
    """Complete compatibility analysis for a specific relationship type.

    The response combines:
    - Raw astrological data (aspects, composite) for iOS chart rendering
    - LLM-generated narrative (headline, summary, insights) for display

    Call get_compatibility with the connection_id. The relationship_type
    is determined from the connection's stored relationship_category.
    """
    # --- LLM-Generated Narrative (The "Hook") ---
    headline: str = Field(description="5-8 word viral-worthy summary (e.g., 'Deep Waters, Shared Vision')")
    summary: str = Field(description="2-3 sentence elevator pitch of the relationship")
    strengths: str = Field(description="2-3 sentences about natural flows (trines/sextiles)")
    growth_areas: str = Field(description="1-2 sentences about challenges/opportunities (squares/oppositions)")
    advice: str = Field(description="One concrete, actionable step they can take today")

    # --- Mode-Specific Scores (The "Metrics") ---
    mode: ModeCompatibility = Field(description="Scores and insights for the relationship type (romantic/friendship/coworker)")

    # --- Raw Astrological Data (For iOS Charts) ---
    aspects: list[SynastryAspect] = Field(description="All synastry aspects for chart rendering")
    composite: Composite = Field(description="Composite chart data - the 'Us' chart")
    karmic: Karmic = Field(description="Karmic/destiny analysis based on Node aspects")

    # --- Metadata ---
    calculated_at: str = Field(description="ISO timestamp of calculation")
    generation_time_ms: int = Field(default=0, description="LLM generation time in milliseconds")
    model_used: str = Field(default="", description="LLM model used for generation")


# =============================================================================
# Synastry Calculation Functions
# =============================================================================

def get_planet_degree(chart: NatalChartData, planet_name: str) -> Optional[float]:
    """Get absolute degree for a planet in a chart."""
    for planet in chart.planets:
        if planet.name.value == planet_name:
            return planet.absolute_degree
    return None


def calculate_aspect(
    degree1: float,
    degree2: float,
    planet1: str,
    planet2: str
) -> Optional[tuple[str, float, bool]]:
    """
    Calculate if there's an aspect between two degrees.

    Returns:
        Tuple of (aspect_type, orb, is_harmonious) or None if no aspect
    """
    # Calculate angular separation
    diff = abs(degree1 - degree2)
    if diff > 180:
        diff = 360 - diff

    # Check each aspect type
    for aspect_type, config in ASPECT_CONFIG.items():
        angle = int(config["angle"])
        max_orb = int(config["orb"])

        orb = abs(diff - angle)
        if orb <= max_orb:
            # Determine if harmonious
            nature = config["nature"]
            if nature == "variable":
                # Conjunction - depends on planets
                pair = (planet1, planet2)
                is_harmonious = pair not in CHALLENGING_CONJUNCTIONS
            else:
                is_harmonious = (nature == "harmonious")

            return (aspect_type, round(orb, 2), is_harmonious)

    return None


def calculate_synastry_aspects(
    chart1: NatalChartData,
    chart2: NatalChartData
) -> list[SynastryAspect]:
    """
    Calculate all synastry aspects between two charts.

    Args:
        chart1: User's natal chart
        chart2: Connection's natal chart

    Returns:
        List of all synastry aspects found
    """
    aspects = []
    aspect_counter = 0

    # Get all planet pairs
    for planet1 in chart1.planets:
        for planet2 in chart2.planets:
            p1_name = planet1.name.value
            p2_name = planet2.name.value

            result = calculate_aspect(
                planet1.absolute_degree,
                planet2.absolute_degree,
                p1_name,
                p2_name
            )

            if result:
                aspect_type, orb, is_harmonious = result
                aspect_counter += 1

                aspects.append(SynastryAspect(
                    id=f"asp_{aspect_counter:03d}",
                    user_planet=p1_name,
                    their_planet=p2_name,
                    aspect_type=aspect_type,
                    orb=orb,
                    is_harmonious=is_harmonious,
                ))

    # Sort by orb (tightest first)
    aspects.sort(key=lambda a: a.orb)

    return aspects


def calculate_category_score(
    aspects: list[SynastryAspect],
    planet_pairs: list[tuple[str, str]],
    category_id: str = "",
    chart1: Optional["NatalChartData"] = None,
    chart2: Optional["NatalChartData"] = None,
) -> tuple[int, list[str]]:
    """
    Calculate score for a category based on relevant aspects and element compatibility.

    Uses aspect-type weights to give more influence to stronger aspects
    (conjunction > trine > opposition > square > sextile > quincunx).

    Element compatibility (Phase 1b) adds a small bonus/penalty for categories
    that have element pairs defined (emotional, attraction, values).

    Score smoothing (Phase 2) applies chart-based variation + sigmoid compression
    to create natural distributions without hard clamping. Each category uses
    different planets for variation based on astrological relevance.

    Args:
        aspects: All synastry aspects
        planet_pairs: List of (planet1, planet2) tuples for this category
        category_id: Category identifier for element/smoothing lookup
        chart1: User's natal chart (for element scoring and smoothing)
        chart2: Connection's natal chart (for element scoring and smoothing)

    Returns:
        Tuple of (smoothed score in range ~[-85, +85], list of aspect_ids)
    """
    total_score = 0.0
    total_weight = 0.0
    aspect_ids = []

    for aspect in aspects:
        # Check if this aspect involves any of our planet pairs
        pair1 = (aspect.user_planet, aspect.their_planet)
        pair2 = (aspect.their_planet, aspect.user_planet)  # Check reverse too

        if pair1 in planet_pairs or pair2 in planet_pairs:
            # Get orb weight (tighter aspects count more)
            orb_weight = get_orb_weight(aspect.orb)

            # Get aspect type weight (conjunction strongest, quincunx weakest)
            aspect_type_weight = ASPECT_TYPE_WEIGHTS.get(aspect.aspect_type, 0.7)

            # Combined weight
            combined_weight = orb_weight * aspect_type_weight

            # Score based on harmony: +1 for harmonious, -1 for challenging
            base_harmony = 1.0 if aspect.is_harmonious else -1.0

            # Contribution = harmony direction * combined weight
            contribution = base_harmony * combined_weight

            total_score += contribution
            total_weight += combined_weight
            aspect_ids.append(aspect.id)

    # Add element compatibility bonus/penalty (Phase 1b)
    element_contribution = 0.0
    if chart1 and chart2 and category_id in CATEGORY_ELEMENT_PAIRS:
        element_pairs = CATEGORY_ELEMENT_PAIRS[category_id]
        element_score = get_element_score(chart1, chart2, element_pairs)
        # Element contributes as a soft signal with fixed weight
        element_contribution = element_score
        # Always add element weight to denominator for stability
        total_weight += ELEMENT_MAX_CONTRIBUTION

    # Normalize and apply smoothing (Phase 2)
    # Raw scores go into sigmoid which outputs 0-100 (50 = neutral)
    if total_weight > 0:
        # Add element contribution to the score
        total_score += element_contribution
        normalized = (total_score / total_weight) * 100
        # Apply chart-based variation + sigmoid smoothing (outputs 0-100)
        smoothed = _smooth_category_score(normalized, chart1, chart2, category_id)
        return (smoothed, aspect_ids)
    else:
        # No aspects found - use element score alone if available
        if element_contribution != 0:
            # Scale element-only score (will be small)
            element_only = element_contribution / ELEMENT_MAX_CONTRIBUTION * 30
            smoothed = _smooth_category_score(element_only, chart1, chart2, category_id)
            return (smoothed, aspect_ids)
        # No data at all - return neutral (50)
        return (50, aspect_ids)


def calculate_mode_compatibility(
    aspects: list[SynastryAspect],
    categories_config: dict[str, list[tuple[str, str]]],
    mode_type: RelationshipType,
    chart1: Optional["NatalChartData"] = None,
    chart2: Optional["NatalChartData"] = None,
) -> ModeCompatibility:
    """
    Calculate compatibility for a single mode (romantic/friendship/coworker).

    Args:
        aspects: All synastry aspects
        categories_config: Category definitions for this mode
        mode_type: The relationship type being calculated
        chart1: User's natal chart (for element scoring)
        chart2: Connection's natal chart (for element scoring)

    Returns:
        ModeCompatibility with scores per category
    """
    # Import labels module
    from compatibility_labels.labels import (
        get_category_label,
        get_category_description,
        get_overall_label,
        generate_driving_aspect_summary,
    )

    # Build aspect lookup for driving aspects
    aspect_lookup = {a.id: a for a in aspects}

    categories = []
    total_score = 0

    for cat_id, planet_pairs in categories_config.items():
        score, aspect_ids = calculate_category_score(
            aspects, planet_pairs, cat_id, chart1, chart2
        )

        # Get label and description from JSON config
        label = get_category_label(mode_type, cat_id, score)
        description = get_category_description(mode_type, cat_id)

        # Build driving aspects with summaries (top 3)
        driving_aspects = []
        for asp_id in aspect_ids[:3]:
            asp = aspect_lookup.get(asp_id)
            if asp:
                summary = generate_driving_aspect_summary(
                    user_planet=asp.user_planet,
                    their_planet=asp.their_planet,
                    aspect_type=asp.aspect_type,
                    is_harmonious=asp.is_harmonious,
                    mode=mode_type,
                    category_id=cat_id,
                )
                driving_aspects.append(DrivingAspect(
                    aspect_id=asp_id,
                    user_planet=asp.user_planet.title(),
                    their_planet=asp.their_planet.title(),
                    aspect_type=asp.aspect_type,
                    is_harmonious=asp.is_harmonious,
                    summary=summary,
                ))

        categories.append(CompatibilityCategory(
            id=cat_id,
            name=CATEGORY_NAMES.get(cat_id, cat_id.title()),
            score=score,
            insight=None,  # Will be filled by LLM
            aspect_ids=aspect_ids[:5],  # Top 3-5 aspects, already sorted by tightest orb
            label=label,
            description=description,
            driving_aspects=driving_aspects,
        ))

        total_score += score

    # Calculate overall score as average of category scores (all now 0-100)
    num_categories = len(categories)
    overall = int(round(total_score / num_categories)) if num_categories > 0 else 50
    overall = max(0, min(100, overall))  # Safety clamp (should not be needed with sigmoid)

    # Get overall label
    overall_label = get_overall_label(overall)

    return ModeCompatibility(
        type=mode_type,
        overall_score=overall,
        overall_label=overall_label,
        vibe_phrase=None,  # Will be filled by LLM
        categories=categories,
    )


def calculate_composite_sign(degree1: float, degree2: float) -> str:
    """Calculate composite midpoint and return the sign."""
    # Calculate midpoint
    if abs(degree1 - degree2) > 180:
        # Handle wrap-around
        midpoint = ((degree1 + degree2 + 360) / 2) % 360
    else:
        midpoint = (degree1 + degree2) / 2

    # Determine sign from degree
    signs = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]
    sign_index = int(midpoint / 30)
    return signs[sign_index]


SIGN_TO_ELEMENT: dict[str, str] = {
    "aries": "fire", "leo": "fire", "sagittarius": "fire",
    "taurus": "earth", "virgo": "earth", "capricorn": "earth",
    "gemini": "air", "libra": "air", "aquarius": "air",
    "cancer": "water", "scorpio": "water", "pisces": "water",
}


def calculate_dominant_element(
    chart1: NatalChartData,
    chart2: NatalChartData
) -> str:
    """
    Calculate dominant element from both charts combined.

    Counts element distribution across Sun, Moon, Mercury, Venus, Mars
    for both charts and returns the most common element.
    """
    element_counts: dict[str, int] = {"fire": 0, "earth": 0, "air": 0, "water": 0}
    personal_planets = ["sun", "moon", "mercury", "venus", "mars"]

    for chart in [chart1, chart2]:
        for planet in chart.planets:
            if planet.name.value in personal_planets:
                sign = planet.sign.value if hasattr(planet.sign, 'value') else planet.sign
                element = SIGN_TO_ELEMENT.get(sign, "earth")
                element_counts[element] += 1

    # Return most common element
    return max(element_counts, key=lambda k: element_counts[k])


def calculate_composite(
    chart1: NatalChartData,
    chart2: NatalChartData
) -> Composite:
    """
    Calculate composite chart data.

    The composite chart represents the relationship itself as an entity,
    calculated from midpoints between both charts.

    Args:
        chart1: User's natal chart
        chart2: Connection's natal chart

    Returns:
        Composite with midpoint signs and dominant element
    """
    # Get Sun, Moon, and Ascendant degrees
    sun1 = get_planet_degree(chart1, "sun")
    sun2 = get_planet_degree(chart2, "sun")
    moon1 = get_planet_degree(chart1, "moon")
    moon2 = get_planet_degree(chart2, "moon")

    # Get Ascendant from houses (1st house cusp)
    asc1 = chart1.houses[0].absolute_degree if chart1.houses else None
    asc2 = chart2.houses[0].absolute_degree if chart2.houses else None

    # Calculate composite signs
    sun_sign = calculate_composite_sign(sun1, sun2) if sun1 and sun2 else "unknown"
    moon_sign = calculate_composite_sign(moon1, moon2) if moon1 and moon2 else "unknown"
    rising_sign = calculate_composite_sign(asc1, asc2) if asc1 and asc2 else None

    # Calculate dominant element as fallback for missing rising
    dominant_element = calculate_dominant_element(chart1, chart2)

    return Composite(
        sun_sign=sun_sign,
        moon_sign=moon_sign,
        rising_sign=rising_sign,
        dominant_element=dominant_element,
        purpose=None,  # Will be filled by LLM
    )


# =============================================================================
# Karmic/Nodal Aspect Detection (Recalibrated for ~20-25% rate)
# =============================================================================

# Tiered planet system for karmic detection
# Tier 1 (Badge-level): These planets create the strongest karmic bonds
# Tier 2 (Undertone): These add flavor but don't alone trigger the badge
KARMIC_TIER1_PLANETS = {"sun", "moon", "saturn", "pluto"}  # Badge-level
KARMIC_TIER2_PLANETS = {"venus", "mars", "mercury"}  # Undertone only

# Orb thresholds - very tight orbs with threshold=1 for ~5-7% rate
KARMIC_TIER1_ORB = 1.0  # Sun, Moon, Saturn
KARMIC_PLUTO_ORB = 0.75  # Pluto (generational, needs tightest orb)
KARMIC_TIER2_ORB = 0.75  # Venus, Mars, Mercury

# Primary aspects count toward the karmic badge
KARMIC_PRIMARY_ASPECTS = {"conjunction", "opposition"}
# Secondary aspects add flavor but don't count toward badge threshold
# Only Saturn and Pluto squares count as secondary
KARMIC_SECONDARY_ASPECTS = {"square"}
KARMIC_SECONDARY_PLANETS = {"saturn", "pluto"}

# Badge threshold: need at least this many Tier 1 primary aspects
# Threshold=2 with both nodes gives ~5-10% rate
KARMIC_BADGE_THRESHOLD = 2

# Interpretation hints for North Node contacts (future growth)
KARMIC_NORTH_HINTS = {
    "sun": "This relationship pulls you toward your future identity and life purpose",
    "moon": "Destined emotional growth - this connection evolves your inner world",
    "saturn": "A binding pact to build something lasting together",
    "pluto": "Transformative destiny - this bond will change you both profoundly",
    "venus": "Fated to teach you new standards of love and value",
    "mars": "This bond activates your ambition - you push each other forward",
    "mercury": "Destined to expand your mind and communication",
}

# Interpretation hints for South Node contacts (past-life familiarity)
KARMIC_SOUTH_HINTS = {
    "sun": "Deep past-life recognition - you knew each other instantly",
    "moon": "Uncanny emotional safety - feels like you've always known each other",
    "saturn": "Heavy karmic bonds - a sense of unfinished business keeps you together",
    "pluto": "Old souls reuniting - intense familiarity with shadow and depth",
    "venus": "Past-life lovers - an instant, sweet, familiar affection",
    "mars": "Old passions rekindled - intense chemistry from day one",
    "mercury": "Telepathic rapport - you pick up a conversation started lifetimes ago",
}

KARMIC_SQUARE_HINTS = {
    "saturn": "Karmic tension: frustrating blocks that test your commitment",
    "pluto": "Karmic intensity: power struggles that demand transformation",
}


def _get_karmic_orb_threshold(planet_name: str) -> float:
    """Get the orb threshold for a planet based on its tier."""
    if planet_name == "pluto":
        return KARMIC_PLUTO_ORB
    elif planet_name in KARMIC_TIER1_PLANETS:
        return KARMIC_TIER1_ORB
    elif planet_name in KARMIC_TIER2_PLANETS:
        return KARMIC_TIER2_ORB
    return 0.0  # Exclude other planets


def _get_karmic_hint(planet_name: str, node_name: str, aspect_type: str) -> str:
    """Get the interpretation hint based on planet, node, and aspect type."""
    if aspect_type == "square":
        return KARMIC_SQUARE_HINTS.get(planet_name, "")
    if node_name == "south node":
        return KARMIC_SOUTH_HINTS.get(planet_name, "")
    return KARMIC_NORTH_HINTS.get(planet_name, "")


def calculate_karmic(
    chart1: NatalChartData,
    chart2: NatalChartData
) -> tuple[Karmic, list[KarmicAspectInternal]]:
    """
    Detect karmic/fated aspects between two charts.

    Recalibrated detection for ~5-10% badge rate:
    - Both North and South Nodes checked
    - Both directions: connection's planets -> user's nodes AND user's planets -> connection's nodes
    - Primary aspects (conjunction, opposition) count toward badge
    - Secondary aspects (Saturn/Pluto squares) add flavor only
    - Badge requires 2+ Tier-1 primary aspects (across all nodes/directions)
    - Tight orbs: 1deg for Tier 1, 0.75deg for Pluto/Tier 2

    Args:
        chart1: User's natal chart
        chart2: Connection's natal chart

    Returns:
        Tuple of (Karmic for API response, list of KarmicAspectInternal for LLM prompting)
    """
    primary_aspects: list[KarmicAspectInternal] = []
    secondary_aspects: list[KarmicAspectInternal] = []
    all_karmic_planets = list(KARMIC_TIER1_PLANETS | KARMIC_TIER2_PLANETS)

    # Get all node degrees (North and South for both charts)
    user_north_deg = get_planet_degree(chart1, "north node")
    user_south_deg = get_planet_degree(chart1, "south node")
    conn_north_deg = get_planet_degree(chart2, "north node")
    conn_south_deg = get_planet_degree(chart2, "south node")

    # Check if we have any node data
    has_any_nodes = any([user_north_deg, user_south_deg, conn_north_deg, conn_south_deg])
    if not has_any_nodes:
        return Karmic(is_karmic=False, theme=None, destiny_note=None), []

    def check_planet_to_node(
        planet_chart: NatalChartData,
        node_deg: float,
        node_name: str,
        planet_owner: str,
        node_owner: str
    ) -> None:
        """Check all planets from one chart against a node."""
        for planet_name in all_karmic_planets:
            planet_deg = get_planet_degree(planet_chart, planet_name)
            if planet_deg is None:
                continue

            orb_threshold = _get_karmic_orb_threshold(planet_name)
            aspect_result = calculate_aspect(planet_deg, node_deg, planet_name, node_name)

            if aspect_result:
                aspect_type, orb, _ = aspect_result

                # Check for primary aspects (conjunction, opposition)
                if aspect_type in KARMIC_PRIMARY_ASPECTS and orb <= orb_threshold:
                    primary_aspects.append(KarmicAspectInternal(
                        planet=planet_name,
                        planet_owner=planet_owner,
                        node=node_name,
                        node_owner=node_owner,
                        aspect_type=aspect_type,
                        orb=round(orb, 2),
                        interpretation_hint=_get_karmic_hint(planet_name, node_name, aspect_type)
                    ))

                # Check for secondary aspects (Saturn/Pluto squares only)
                elif (aspect_type in KARMIC_SECONDARY_ASPECTS and
                      planet_name in KARMIC_SECONDARY_PLANETS and
                      orb <= orb_threshold):
                    secondary_aspects.append(KarmicAspectInternal(
                        planet=planet_name,
                        planet_owner=planet_owner,
                        node=node_name,
                        node_owner=node_owner,
                        aspect_type=aspect_type,
                        orb=round(orb, 2),
                        interpretation_hint=_get_karmic_hint(planet_name, node_name, aspect_type)
                    ))

    # Check all four combinations (both directions, both nodes)
    # Connection's planets to User's nodes
    if user_north_deg is not None:
        check_planet_to_node(chart2, user_north_deg, "north node", "connection", "user")
    if user_south_deg is not None:
        check_planet_to_node(chart2, user_south_deg, "south node", "connection", "user")

    # User's planets to Connection's nodes
    if conn_north_deg is not None:
        check_planet_to_node(chart1, conn_north_deg, "north node", "user", "connection")
    if conn_south_deg is not None:
        check_planet_to_node(chart1, conn_south_deg, "south node", "user", "connection")

    # Sort by orb (tightest first)
    primary_aspects.sort(key=lambda a: a.orb)
    secondary_aspects.sort(key=lambda a: a.orb)

    # Count Tier 1 primary aspects for badge determination
    tier1_primary_count = sum(
        1 for a in primary_aspects
        if a.planet in KARMIC_TIER1_PLANETS
    )

    # Determine if this qualifies for the karmic badge
    # Badge requires 2+ Tier-1 primary aspects
    has_badge = tier1_primary_count >= KARMIC_BADGE_THRESHOLD

    # Combine all aspects for LLM context
    all_karmic_aspects = primary_aspects + secondary_aspects

    # Determine theme from tightest aspect
    theme = None
    if all_karmic_aspects:
        tightest = all_karmic_aspects[0]
        if tightest.aspect_type == "square":
            theme = f"Karmic tension through {tightest.planet}"
        elif tightest.node == "south node":
            theme = f"Past-life bond through {tightest.planet}"
        else:
            theme = f"Fated growth through {tightest.planet}"

    # is_karmic is True only if we have the badge (2+ Tier-1 primary aspects)
    karmic = Karmic(
        is_karmic=has_badge,
        theme=theme if has_badge else None,
        destiny_note=None  # Will be filled by LLM only if is_karmic
    )

    return karmic, all_karmic_aspects


# =============================================================================
# Main API Function
# =============================================================================

# Category configs by mode
MODE_CATEGORIES: dict[RelationshipType, dict[str, list[tuple[str, str]]]] = {
    "romantic": ROMANTIC_CATEGORIES,
    "friendship": FRIENDSHIP_CATEGORIES,
    "coworker": COWORKER_CATEGORIES,
}


class CompatibilityData:
    """
    Internal data structure for compatibility calculation.

    Contains all calculated data before LLM enrichment.
    The LLM layer uses this to generate narrative content.
    """
    def __init__(
        self,
        mode: ModeCompatibility,
        aspects: list[SynastryAspect],
        composite: Composite,
        karmic: Karmic,
        karmic_aspects_internal: list[KarmicAspectInternal],
        user_name: str,
        connection_name: str,
        user_sun_sign: str,
        connection_sun_sign: str,
        user_moon_sign: str = "unknown",
        connection_moon_sign: str = "unknown",
        user_rising_sign: str = "unknown",
        connection_rising_sign: str = "unknown",
    ):
        self.mode = mode
        self.aspects = aspects
        self.composite = composite
        self.karmic = karmic
        self.karmic_aspects_internal = karmic_aspects_internal
        self.user_name = user_name
        self.connection_name = connection_name
        self.user_sun_sign = user_sun_sign
        self.connection_sun_sign = connection_sun_sign
        self.user_moon_sign = user_moon_sign
        self.connection_moon_sign = connection_moon_sign
        self.user_rising_sign = user_rising_sign
        self.connection_rising_sign = connection_rising_sign


def calculate_compatibility(
    user_chart: NatalChartData,
    connection_chart: NatalChartData,
    relationship_type: RelationshipType,
    user_name: str = "You",
    connection_name: str = "They",
) -> CompatibilityData:
    """
    Calculate compatibility analysis for a specific relationship type.

    Returns CompatibilityData which contains all raw calculations.
    The caller (main.py) passes this to the LLM layer to generate
    the final CompatibilityResult with narrative content.

    Args:
        user_chart: User's natal chart (NatalChartData)
        connection_chart: Connection's natal chart (NatalChartData)
        relationship_type: "romantic", "friendship", or "coworker"
        user_name: User's name for personalization
        connection_name: Connection's name for personalization

    Returns:
        CompatibilityData with all calculations ready for LLM enrichment
    """
    # Calculate all synastry aspects (for iOS chart rendering)
    aspects = calculate_synastry_aspects(user_chart, connection_chart)

    # Calculate only the requested mode (with element compatibility from Phase 1b)
    categories_config = MODE_CATEGORIES[relationship_type]
    mode = calculate_mode_compatibility(
        aspects, categories_config, relationship_type, user_chart, connection_chart
    )

    # Calculate composite (the "Purpose")
    composite = calculate_composite(user_chart, connection_chart)

    # Calculate karmic aspects (the "Destiny")
    karmic, karmic_aspects_internal = calculate_karmic(user_chart, connection_chart)

    # Get sun, moon, and rising signs for LLM context
    user_sun_sign = next(
        (p.sign.value for p in user_chart.planets if p.name.value == "sun"),
        "unknown"
    )
    connection_sun_sign = next(
        (p.sign.value for p in connection_chart.planets if p.name.value == "sun"),
        "unknown"
    )
    user_moon_sign = next(
        (p.sign.value for p in user_chart.planets if p.name.value == "moon"),
        "unknown"
    )
    connection_moon_sign = next(
        (p.sign.value for p in connection_chart.planets if p.name.value == "moon"),
        "unknown"
    )
    # Rising sign from angles (may not be available if no birth time)
    user_rising_sign = (
        user_chart.angles.ascendant.sign.value
        if user_chart.angles and user_chart.angles.ascendant
        else "unknown"
    )
    connection_rising_sign = (
        connection_chart.angles.ascendant.sign.value
        if connection_chart.angles and connection_chart.angles.ascendant
        else "unknown"
    )

    return CompatibilityData(
        mode=mode,
        aspects=aspects,
        composite=composite,
        karmic=karmic,
        karmic_aspects_internal=karmic_aspects_internal,
        user_name=user_name,
        connection_name=connection_name,
        user_sun_sign=user_sun_sign,
        connection_sun_sign=connection_sun_sign,
        user_moon_sign=user_moon_sign,
        connection_moon_sign=connection_moon_sign,
        user_rising_sign=user_rising_sign,
        connection_rising_sign=connection_rising_sign,
    )


def get_compatibility_from_birth_data(
    user_birth_date: str,
    user_birth_time: Optional[str],
    user_birth_lat: Optional[float],
    user_birth_lon: Optional[float],
    user_birth_timezone: Optional[str],
    connection_birth_date: str,
    relationship_type: RelationshipType,
    connection_birth_time: Optional[str] = None,
    connection_birth_lat: Optional[float] = None,
    connection_birth_lon: Optional[float] = None,
    connection_birth_timezone: Optional[str] = None,
    user_name: str = "You",
    connection_name: str = "They",
) -> CompatibilityData:
    """
    Calculate compatibility from raw birth data.

    Convenience function that computes charts and runs compatibility.

    Args:
        user_birth_*: User's birth data
        connection_birth_*: Connection's birth data
        relationship_type: "romantic", "friendship", or "coworker"
        user_name: User's name for personalization
        connection_name: Connection's name for personalization

    Returns:
        CompatibilityData ready for LLM enrichment
    """
    # Compute user chart
    user_chart_dict, _ = compute_birth_chart(
        birth_date=user_birth_date,
        birth_time=user_birth_time,
        birth_timezone=user_birth_timezone,
        birth_lat=user_birth_lat,
        birth_lon=user_birth_lon
    )
    user_chart = NatalChartData(**user_chart_dict)

    # Compute connection chart
    conn_chart_dict, _ = compute_birth_chart(
        birth_date=connection_birth_date,
        birth_time=connection_birth_time,
        birth_timezone=connection_birth_timezone,
        birth_lat=connection_birth_lat,
        birth_lon=connection_birth_lon
    )
    connection_chart = NatalChartData(**conn_chart_dict)

    return calculate_compatibility(
        user_chart,
        connection_chart,
        relationship_type,
        user_name,
        connection_name,
    )


# =============================================================================
# Synastry Points for Daily Relationship Weather
# =============================================================================

def calculate_synastry_points(
    user_chart: NatalChartData,
    connection_chart: NatalChartData
) -> list[dict]:
    """
    Calculate key synastry midpoints for transit checking.

    Used by daily horoscope to find transits hitting relationship points.

    Args:
        user_chart: User's natal chart
        connection_chart: Connection's natal chart

    Returns:
        List of synastry point dicts with degree and type
    """
    points = []

    def add_midpoint(planet1: str, planet2: str, label: str, point_type: str):
        deg1 = get_planet_degree(user_chart, planet1)
        deg2 = get_planet_degree(connection_chart, planet2)

        if deg1 is not None and deg2 is not None:
            # Calculate midpoint
            if abs(deg1 - deg2) > 180:
                midpoint = ((deg1 + deg2 + 360) / 2) % 360
            else:
                midpoint = (deg1 + deg2) / 2

            points.append({
                "degree": round(midpoint, 2),
                "type": point_type,
                "label": label,
                "planets": [planet1, planet2]
            })

    # Key midpoints
    add_midpoint("moon", "moon", "emotional connection point", "moon_moon_midpoint")
    add_midpoint("sun", "sun", "core identity point", "sun_sun_midpoint")
    add_midpoint("venus", "venus", "affection point", "venus_venus_midpoint")
    add_midpoint("mercury", "mercury", "communication point", "mercury_mercury_midpoint")
    add_midpoint("venus", "mars", "attraction point", "venus_mars_midpoint")
    add_midpoint("mars", "venus", "passion point", "mars_venus_midpoint")

    return points


def find_transits_to_synastry(
    transit_chart: NatalChartData,
    synastry_points: list[dict],
    orb: float = 3.0
) -> list[dict]:
    """
    Find today's transits aspecting synastry points.

    Args:
        transit_chart: Current transit chart
        synastry_points: Synastry points from calculate_synastry_points()
        orb: Max orb to consider (default 3.0)

    Returns:
        List of active transit dicts
    """
    active_transits = []

    # Fast-moving planets to check (daily relevance)
    transit_planets = ["moon", "mercury", "venus", "mars", "sun"]

    # Aspects to check
    aspect_angles = {
        "conjunction": 0,
        "opposition": 180,
        "trine": 120,
        "square": 90,
        "sextile": 60
    }

    for planet in transit_chart.planets:
        if planet.name.value not in transit_planets:
            continue

        transit_degree = planet.absolute_degree

        for point in synastry_points:
            point_degree = point["degree"]

            for aspect_name, aspect_angle in aspect_angles.items():
                # Calculate angular difference
                diff = abs(transit_degree - point_degree)
                if diff > 180:
                    diff = 360 - diff

                aspect_diff = abs(diff - aspect_angle)

                if aspect_diff <= orb:
                    is_harmonious = aspect_name in ["trine", "sextile", "conjunction"]

                    active_transits.append({
                        "transit_planet": planet.name.value,
                        "aspect": aspect_name,
                        "synastry_point": point["type"],
                        "synastry_label": point["label"],
                        "orb": round(aspect_diff, 1),
                        "is_harmonious": is_harmonious,
                        "description": f"Transit {planet.name.value.title()} {aspect_name} your {point['label']}"
                    })

    # Sort by orb (tightest first)
    active_transits.sort(key=lambda x: x["orb"])

    return active_transits


def calculate_vibe_score(active_transits: list[dict]) -> int:
    """
    Calculate vibe score (0-100) from active transits.

    Args:
        active_transits: List of active transit dicts

    Returns:
        Vibe score 0-100 (50 = neutral)
    """
    if not active_transits:
        return 50  # Neutral if no transits

    total_score = 0.0
    total_weight = 0.0

    for transit in active_transits:
        # Get orb, defaulting to 3.0 (medium weight) if None or missing
        orb = transit.get("orb")
        if orb is None:
            orb = 3.0  # Default to medium orb if missing

        # Weight by orb (tighter = more impact)
        orb_weight = max(0, 1 - (orb / 3.0))

        # Aspect score
        aspect_score = 1 if transit.get("is_harmonious") else -1

        total_score += aspect_score * orb_weight
        total_weight += orb_weight

    if total_weight == 0:
        return 50

    # Normalize to 0-100
    normalized = (total_score / total_weight + 1) / 2
    return int(normalized * 100)

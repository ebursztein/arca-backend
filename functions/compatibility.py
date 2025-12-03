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


# =============================================================================
# Category Definitions by Relationship Mode
# =============================================================================

# Each category maps to a list of planet pairs to check
# Format: (planet1, planet2) where we check aspects between chart1.planet1 and chart2.planet2

ROMANTIC_CATEGORIES = {
    "emotional": [
        ("moon", "moon"), ("moon", "venus"), ("venus", "moon"),
        ("moon", "neptune"), ("neptune", "moon"),
    ],
    "communication": [
        ("mercury", "mercury"), ("mercury", "moon"), ("moon", "mercury"),
        ("mercury", "venus"), ("venus", "mercury"),
    ],
    "attraction": [
        ("venus", "mars"), ("mars", "venus"),
        ("mars", "mars"), ("venus", "venus"),
    ],
    "values": [
        ("venus", "venus"), ("jupiter", "jupiter"),
        ("sun", "jupiter"), ("jupiter", "sun"),
        ("venus", "jupiter"), ("jupiter", "venus"),
    ],
    "longTerm": [
        ("saturn", "sun"), ("sun", "saturn"),
        ("saturn", "moon"), ("moon", "saturn"),
        ("saturn", "venus"), ("venus", "saturn"),
        ("sun", "sun"),
    ],
    "growth": [
        ("pluto", "sun"), ("sun", "pluto"),
        ("pluto", "moon"), ("moon", "pluto"),
        ("pluto", "venus"), ("venus", "pluto"),
        ("north node", "sun"), ("sun", "north node"),
        ("north node", "moon"), ("moon", "north node"),
    ],
}

FRIENDSHIP_CATEGORIES = {
    "emotional": [
        ("moon", "moon"), ("moon", "venus"), ("venus", "moon"),
        ("sun", "moon"), ("moon", "sun"),
    ],
    "communication": [
        ("mercury", "mercury"), ("mercury", "jupiter"), ("jupiter", "mercury"),
        ("mercury", "sun"), ("sun", "mercury"),
    ],
    "fun": [
        ("jupiter", "jupiter"), ("sun", "sun"),
        ("mars", "jupiter"), ("jupiter", "mars"),
        ("venus", "jupiter"), ("jupiter", "venus"),
    ],
    "loyalty": [
        ("saturn", "moon"), ("moon", "saturn"),
        ("saturn", "sun"), ("sun", "saturn"),
    ],
    "sharedInterests": [
        ("venus", "venus"), ("mercury", "venus"), ("venus", "mercury"),
        ("moon", "venus"), ("venus", "moon"),
    ],
}

COWORKER_CATEGORIES = {
    "communication": [
        ("mercury", "mercury"), ("mercury", "saturn"), ("saturn", "mercury"),
        ("mercury", "mars"), ("mars", "mercury"),
    ],
    "collaboration": [
        ("sun", "sun"), ("mars", "mars"),
        ("sun", "mars"), ("mars", "sun"),
    ],
    "reliability": [
        ("saturn", "sun"), ("sun", "saturn"),
        ("saturn", "moon"), ("moon", "saturn"),
        ("saturn", "saturn"),
    ],
    "ambition": [
        ("mars", "saturn"), ("saturn", "mars"),
        ("jupiter", "saturn"), ("saturn", "jupiter"),
        ("mars", "jupiter"), ("jupiter", "mars"),
    ],
    "powerDynamics": [
        ("pluto", "sun"), ("sun", "pluto"),
        ("pluto", "mars"), ("mars", "pluto"),
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


class CompatibilityCategory(BaseModel):
    """A single compatibility category with score and LLM insight.

    Categories vary by relationship type:
    - Romantic: emotional, communication, attraction, values, longTerm, growth
    - Friendship: emotional, communication, fun, loyalty, sharedInterests
    - Coworker: communication, collaboration, reliability, ambition, powerDynamics
    """
    id: str = Field(description="Category ID for iOS state management")
    name: str = Field(description="Display name (e.g., 'Emotional Connection')")
    score: int = Field(ge=-100, le=100, description="Category score: -100 (challenging) to +100 (flowing)")
    insight: Optional[str] = Field(None, description="LLM-generated 1-2 sentence insight for this category")
    aspect_ids: list[str] = Field(default_factory=list, description="Top 3-5 aspect IDs driving this score, ordered by tightest orb")


class ModeCompatibility(BaseModel):
    """Compatibility scores for the requested relationship type."""
    type: RelationshipType = Field(description="The relationship type: romantic, friendship, or coworker")
    overall_score: int = Field(ge=0, le=100, description="Overall compatibility score (0-100)")
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
    planet_pairs: list[tuple[str, str]]
) -> tuple[int, list[str]]:
    """
    Calculate score for a category based on relevant aspects.

    Args:
        aspects: All synastry aspects
        planet_pairs: List of (planet1, planet2) tuples for this category

    Returns:
        Tuple of (score, list of aspect_ids)
    """
    total_score = 0.0
    total_weight = 0.0
    aspect_ids = []

    for aspect in aspects:
        # Check if this aspect involves any of our planet pairs
        pair1 = (aspect.user_planet, aspect.their_planet)
        pair2 = (aspect.their_planet, aspect.user_planet)  # Check reverse too

        if pair1 in planet_pairs or pair2 in planet_pairs:
            # Calculate weighted contribution
            weight = get_orb_weight(aspect.orb)

            # Score based on harmony
            if aspect.is_harmonious:
                score = 1.0
            else:
                score = -1.0

            total_score += score * weight
            total_weight += weight
            aspect_ids.append(aspect.id)

    # Normalize to -100 to +100
    if total_weight > 0:
        normalized = (total_score / total_weight) * 100
        return (int(round(normalized)), aspect_ids)
    else:
        # No aspects found for this category - neutral
        return (0, aspect_ids)


def calculate_mode_compatibility(
    aspects: list[SynastryAspect],
    categories_config: dict[str, list[tuple[str, str]]],
    mode_type: RelationshipType
) -> ModeCompatibility:
    """
    Calculate compatibility for a single mode (romantic/friendship/coworker).

    Args:
        aspects: All synastry aspects
        categories_config: Category definitions for this mode
        mode_type: The relationship type being calculated

    Returns:
        ModeCompatibility with scores per category
    """
    categories = []
    total_score = 0

    for cat_id, planet_pairs in categories_config.items():
        score, aspect_ids = calculate_category_score(aspects, planet_pairs)

        categories.append(CompatibilityCategory(
            id=cat_id,
            name=CATEGORY_NAMES.get(cat_id, cat_id.title()),
            score=score,
            insight=None,  # Will be filled by LLM
            aspect_ids=aspect_ids[:5],  # Top 3-5 aspects, already sorted by tightest orb
        ))

        total_score += score

    # Calculate overall score (normalize category sum to 0-100)
    num_categories = len(categories)
    max_possible = num_categories * 100
    min_possible = num_categories * -100

    # Map to 0-100 range
    overall = int(round(((total_score - min_possible) / (max_possible - min_possible)) * 100))
    overall = max(0, min(100, overall))  # Clamp

    return ModeCompatibility(
        type=mode_type,
        overall_score=overall,
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
# Karmic/Nodal Aspect Detection
# =============================================================================

# Only hard aspects count for karmic connections (conjunction, opposition, square)
# Sextiles and trines are too easy/common to feel "fated"
KARMIC_ASPECTS = {"conjunction", "opposition", "square"}

# Tiered orb thresholds by planet importance
# Tier 1 (Fated): Sun, Moon, Saturn - the heavy hitters
# Tier 2 (Personal): Venus, Mars, Mercury - personal but less binding
# Generational planets (Jupiter+) excluded - not personal enough for synastry
KARMIC_TIER1_PLANETS = {"sun", "moon", "saturn"}  # 3 degree orb
KARMIC_TIER2_PLANETS = {"venus", "mars", "mercury"}  # 2 degree orb
KARMIC_TIER1_ORB = 3.0
KARMIC_TIER2_ORB = 2.0

# Interpretation hints distinguished by node and aspect type
# North Node conjunction/opposition = future growth
# South Node conjunction/opposition = past life familiarity
# Square = tension/crisis demanding resolution

KARMIC_PLANET_HINTS_NORTH = {
    "sun": "This relationship pulls you toward your future identity and life purpose",
    "moon": "Destined emotional growth - this connection evolves your inner world",
    "saturn": "A binding pact to build a solid, long-term structure together",
    "venus": "Fated to teach you new, higher standards of love and value",
    "mars": "This bond activates your ambition - you push each other forward",
    "mercury": "Destined to expand your mind and teach you new languages of thought",
}

KARMIC_PLANET_HINTS_SOUTH = {
    "sun": "Deep past-life familiarity - you recognized each other instantly",
    "moon": "Uncanny emotional safety - feels like you've always known each other",
    "saturn": "Heavy karmic bonds - a sense of duty or 'unfinished business' keeps you together",
    "venus": "Past-life lovers reuniting - an instant, sweet, familiar affection",
    "mars": "Old passions rekindled - intense chemistry but prone to familiar conflicts",
    "mercury": "Telepathic rapport - you pick up a conversation started lifetimes ago",
}

KARMIC_PLANET_HINTS_SQUARE = {
    "sun": "A crisis of identity - you challenge each other's ego to force growth",
    "moon": "Emotional tension that demands you resolve past patterns now",
    "saturn": "Frustrating blocks or timing issues that test your commitment",
    "venus": "Clashing values that force a re-evaluation of what you truly want",
    "mars": "Friction and rivalry that demands you learn to act cooperatively",
    "mercury": "Misunderstandings that force you to learn radical new ways of listening",
}


def _get_karmic_orb_threshold(planet_name: str) -> float:
    """Get the orb threshold for a planet based on its tier."""
    if planet_name in KARMIC_TIER1_PLANETS:
        return KARMIC_TIER1_ORB
    elif planet_name in KARMIC_TIER2_PLANETS:
        return KARMIC_TIER2_ORB
    return 0.0  # Exclude generational planets


def _get_karmic_hint(planet_name: str, node_name: str, aspect_type: str) -> str:
    """Get the appropriate interpretation hint based on node and aspect type."""
    if aspect_type == "square":
        return KARMIC_PLANET_HINTS_SQUARE.get(planet_name, "")
    elif node_name == "north node":
        # Conjunction to North Node or Opposition (= conjunct South Node, but framed as North)
        return KARMIC_PLANET_HINTS_NORTH.get(planet_name, "")
    else:
        # South Node contact = past life familiarity
        return KARMIC_PLANET_HINTS_SOUTH.get(planet_name, "")


def calculate_karmic(
    chart1: NatalChartData,
    chart2: NatalChartData
) -> tuple[Karmic, list[KarmicAspectInternal]]:
    """
    Detect karmic/fated aspects between two charts.

    Uses astrologer-recommended criteria:
    - Only hard aspects (conjunction, opposition, square)
    - Tiered orbs: Tier 1 (Sun/Moon/Saturn) = 3 deg, Tier 2 (Venus/Mars/Mercury) = 2 deg
    - Generational planets excluded (not personal enough)

    This gives ~20-25% probability of a karmic match, making it feel
    "rare but attainable" rather than universal.

    Args:
        chart1: User's natal chart
        chart2: Connection's natal chart

    Returns:
        Tuple of (Karmic for API response, list of KarmicAspectInternal for LLM prompting)
    """
    karmic_aspects: list[KarmicAspectInternal] = []
    nodes = ["north node", "south node"]
    # Only personal planets - generational excluded
    karmic_planets = list(KARMIC_TIER1_PLANETS | KARMIC_TIER2_PLANETS)

    # Check user's planets to connection's nodes
    for planet_name in karmic_planets:
        planet_deg = get_planet_degree(chart1, planet_name)
        if planet_deg is None:
            continue

        orb_threshold = _get_karmic_orb_threshold(planet_name)

        for node_name in nodes:
            node_deg = get_planet_degree(chart2, node_name)
            if node_deg is None:
                continue

            aspect_result = calculate_aspect(planet_deg, node_deg, planet_name, node_name)
            if aspect_result:
                aspect_type, orb, _ = aspect_result
                # Only hard aspects with tight orbs
                if aspect_type in KARMIC_ASPECTS and orb <= orb_threshold:
                    karmic_aspects.append(KarmicAspectInternal(
                        planet=planet_name,
                        planet_owner="user",
                        node=node_name,
                        node_owner="connection",
                        aspect_type=aspect_type,
                        orb=round(orb, 2),
                        interpretation_hint=_get_karmic_hint(planet_name, node_name, aspect_type)
                    ))

    # Check connection's planets to user's nodes
    for planet_name in karmic_planets:
        planet_deg = get_planet_degree(chart2, planet_name)
        if planet_deg is None:
            continue

        orb_threshold = _get_karmic_orb_threshold(planet_name)

        for node_name in nodes:
            node_deg = get_planet_degree(chart1, node_name)
            if node_deg is None:
                continue

            aspect_result = calculate_aspect(planet_deg, node_deg, planet_name, node_name)
            if aspect_result:
                aspect_type, orb, _ = aspect_result
                # Only hard aspects with tight orbs
                if aspect_type in KARMIC_ASPECTS and orb <= orb_threshold:
                    karmic_aspects.append(KarmicAspectInternal(
                        planet=planet_name,
                        planet_owner="connection",
                        node=node_name,
                        node_owner="user",
                        aspect_type=aspect_type,
                        orb=round(orb, 2),
                        interpretation_hint=_get_karmic_hint(planet_name, node_name, aspect_type)
                    ))

    # Sort by orb (tightest first)
    karmic_aspects.sort(key=lambda a: a.orb)

    # Determine primary theme from tightest aspect
    theme = None
    if karmic_aspects:
        tightest = karmic_aspects[0]
        if tightest.aspect_type == "square":
            theme = f"Karmic tension through {tightest.planet}"
        elif tightest.node == "north node":
            theme = f"Future growth through {tightest.planet}"
        else:
            theme = f"Past-life connection through {tightest.planet}"

    karmic = Karmic(
        is_karmic=len(karmic_aspects) > 0,
        theme=theme,
        destiny_note=None  # Will be filled by LLM only if is_karmic
    )

    return karmic, karmic_aspects


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

    # Calculate only the requested mode
    categories_config = MODE_CATEGORIES[relationship_type]
    mode = calculate_mode_compatibility(aspects, categories_config, relationship_type)

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

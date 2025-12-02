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
ASPECT_CONFIG = {
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

class SynastryAspect(BaseModel):
    """A single aspect between two charts."""
    id: str = Field(min_length=1, max_length=32, description="Unique aspect ID")
    user_planet: str = Field(min_length=1, max_length=32, description="Planet from user's chart")
    their_planet: str = Field(min_length=1, max_length=32, description="Planet from connection's chart")
    aspect_type: str = Field(min_length=1, max_length=32, description="conjunction, trine, square, etc.")
    orb: float = Field(ge=0, le=20, description="Orb in degrees")
    is_harmonious: bool = Field(description="True if supportive aspect")
    interpretation: Optional[str] = Field(None, max_length=2000, description="LLM-generated meaning")


class CompatibilityCategory(BaseModel):
    """Score and details for a single compatibility category."""
    id: str = Field(description="Category ID: emotional, communication, etc.")
    name: str = Field(description="Display name")
    score: int = Field(ge=-100, le=100, description="Category score (-100 to +100)")
    summary: Optional[str] = Field(None, description="LLM-generated summary")
    aspect_ids: list[str] = Field(default_factory=list, description="Contributing aspect IDs")


class KarmicAspect(BaseModel):
    """A single karmic aspect (planet touching a Node)."""
    planet: str = Field(description="The planet touching the Node")
    planet_owner: str = Field(description="'user' or 'connection' - whose planet")
    node: str = Field(description="'north node' or 'south node'")
    node_owner: str = Field(description="'user' or 'connection' - whose node")
    aspect_type: str = Field(description="conjunction, opposition, trine, square, sextile")
    orb: float = Field(ge=0, le=10, description="Orb in degrees")
    interpretation_hint: str = Field(description="Brief hint for LLM interpretation")


class KarmicSummary(BaseModel):
    """Summary of karmic/fated connections between two charts."""
    is_karmic: bool = Field(description="True if any tight Node aspects exist")
    karmic_aspects: list[KarmicAspect] = Field(default_factory=list)
    primary_theme: Optional[str] = Field(None, description="Main karmic theme if applicable")
    destiny_note: Optional[str] = Field(None, description="LLM-generated destiny interpretation")


class CompositeSummary(BaseModel):
    """Composite chart summary (midpoints of both charts)."""
    composite_sun: Optional[str] = Field(None, description="Composite Sun sign")
    composite_moon: Optional[str] = Field(None, description="Composite Moon sign")
    composite_ascendant: Optional[str] = Field(None, description="Composite Ascendant sign")
    summary: Optional[str] = Field(None, description="LLM-generated composite summary")
    relationship_purpose: Optional[str] = Field(None, description="LLM-generated purpose statement")
    strengths: list[str] = Field(default_factory=list)
    challenges: list[str] = Field(default_factory=list)


class ModeCompatibility(BaseModel):
    """Compatibility result for a single mode (romantic/friendship/coworker)."""
    overall_score: int = Field(ge=0, le=100, description="Overall score (0-100)")
    relationship_verb: Optional[str] = Field(None, description="e.g., 'You spark each other'")
    categories: list[CompatibilityCategory]
    missing_data_prompts: list[str] = Field(default_factory=list)


class CompatibilityInterpretation(BaseModel):
    """LLM-generated interpretation for compatibility reading."""
    headline: str = Field(description="5-8 word headline capturing their dynamic")
    summary: str = Field(description="2-3 sentences overall summary")
    relationship_purpose: str = Field(default="", description="1-2 sentences about the relationship's purpose")
    strengths: str = Field(description="2-3 sentences about natural connection points")
    growth_areas: str = Field(description="1-2 sentences about growth opportunities")
    advice: str = Field(description="1 actionable sentence")
    destiny_note: str = Field(default="", description="1-2 sentences about karmic connection (only if karmic)")
    generation_time_ms: int = Field(default=0, description="LLM generation time in milliseconds")
    model_used: str = Field(default="", description="Model used for generation")


class CompatibilityResult(BaseModel):
    """Complete compatibility analysis across all three modes."""
    romantic: ModeCompatibility
    friendship: ModeCompatibility
    coworker: ModeCompatibility
    aspects: list[SynastryAspect] = Field(description="All synastry aspects found")
    composite_summary: Optional[CompositeSummary] = None
    karmic_summary: Optional[KarmicSummary] = None
    interpretation: Optional["CompatibilityInterpretation"] = Field(default=None, description="LLM-generated interpretation")
    calculated_at: str = Field(description="ISO timestamp")


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
        angle = config["angle"]
        max_orb = config["orb"]

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
                    interpretation=None  # Will be filled by LLM
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
    categories_config: dict[str, list[tuple[str, str]]]
) -> ModeCompatibility:
    """
    Calculate compatibility for a single mode (romantic/friendship/coworker).

    Args:
        aspects: All synastry aspects
        categories_config: Category definitions for this mode

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
            summary=None,  # Will be filled by LLM
            aspect_ids=aspect_ids
        ))

        total_score += score

    # Calculate overall score (normalize category sum to 0-100)
    # Formula: (sum + 600) / 12 maps -600..+600 to 0..100
    # But we have variable category counts, so adjust
    num_categories = len(categories)
    max_possible = num_categories * 100
    min_possible = num_categories * -100

    # Map to 0-100 range
    overall = int(round(((total_score - min_possible) / (max_possible - min_possible)) * 100))
    overall = max(0, min(100, overall))  # Clamp

    return ModeCompatibility(
        overall_score=overall,
        relationship_verb=None,  # Will be filled by LLM
        categories=categories,
        missing_data_prompts=[]
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


def calculate_composite_summary(
    chart1: NatalChartData,
    chart2: NatalChartData
) -> CompositeSummary:
    """
    Calculate composite chart summary.

    Args:
        chart1: User's natal chart
        chart2: Connection's natal chart

    Returns:
        CompositeSummary with midpoint signs
    """
    # Get Sun, Moon, and Ascendant degrees
    sun1 = get_planet_degree(chart1, "sun")
    sun2 = get_planet_degree(chart2, "sun")
    moon1 = get_planet_degree(chart1, "moon")
    moon2 = get_planet_degree(chart2, "moon")

    # Get Ascendant from houses (1st house cusp)
    asc1 = chart1.houses[0].absolute_degree if chart1.houses else None
    asc2 = chart2.houses[0].absolute_degree if chart2.houses else None

    composite_sun = None
    composite_moon = None
    composite_ascendant = None

    if sun1 is not None and sun2 is not None:
        composite_sun = calculate_composite_sign(sun1, sun2)

    if moon1 is not None and moon2 is not None:
        composite_moon = calculate_composite_sign(moon1, moon2)

    if asc1 is not None and asc2 is not None:
        composite_ascendant = calculate_composite_sign(asc1, asc2)

    return CompositeSummary(
        composite_sun=composite_sun,
        composite_moon=composite_moon,
        composite_ascendant=composite_ascendant,
        summary=None,  # Will be filled by LLM
        relationship_purpose=None,  # Will be filled by LLM
        strengths=[],
        challenges=[]
    )


# =============================================================================
# Karmic/Nodal Aspect Detection
# =============================================================================

# Karmic orb threshold - tight aspects indicate stronger karmic connection
KARMIC_ORB_THRESHOLD = 4.0

# Interpretation hints for karmic aspects by planet
KARMIC_PLANET_HINTS = {
    "sun": "Core identity and life purpose connection",
    "moon": "Deep emotional and soul-level familiarity",
    "mercury": "Destined communication and mental exchange",
    "venus": "Fated love, values, and relationship lessons",
    "mars": "Karmic passion, drive, and action patterns",
    "jupiter": "Shared growth and spiritual expansion destiny",
    "saturn": "Serious karmic debt or responsibility together",
    "uranus": "Destined awakening and liberation themes",
    "neptune": "Spiritual or creative soul connection",
    "pluto": "Intense transformational karma to work through",
}


def calculate_karmic_aspects(
    chart1: NatalChartData,
    chart2: NatalChartData
) -> KarmicSummary:
    """
    Detect karmic/fated aspects between two charts.

    Checks for planets touching North/South Nodes with tight orbs.
    These indicate past-life connections and destined encounters.

    Args:
        chart1: User's natal chart
        chart2: Connection's natal chart

    Returns:
        KarmicSummary with is_karmic flag and aspect details
    """
    karmic_aspects = []
    nodes = ["north node", "south node"]
    key_planets = ["sun", "moon", "venus", "mars", "saturn", "jupiter", "mercury"]

    # Check user's planets to connection's nodes
    for planet_name in key_planets:
        planet_deg = get_planet_degree(chart1, planet_name)
        if planet_deg is None:
            continue

        for node_name in nodes:
            node_deg = get_planet_degree(chart2, node_name)
            if node_deg is None:
                continue

            aspect_result = calculate_aspect(planet_deg, node_deg, planet_name, node_name)
            if aspect_result:
                aspect_type, orb, _ = aspect_result
                if orb <= KARMIC_ORB_THRESHOLD:
                    karmic_aspects.append(KarmicAspect(
                        planet=planet_name,
                        planet_owner="user",
                        node=node_name,
                        node_owner="connection",
                        aspect_type=aspect_type,
                        orb=round(orb, 2),
                        interpretation_hint=KARMIC_PLANET_HINTS.get(planet_name, "")
                    ))

    # Check connection's planets to user's nodes
    for planet_name in key_planets:
        planet_deg = get_planet_degree(chart2, planet_name)
        if planet_deg is None:
            continue

        for node_name in nodes:
            node_deg = get_planet_degree(chart1, node_name)
            if node_deg is None:
                continue

            aspect_result = calculate_aspect(planet_deg, node_deg, planet_name, node_name)
            if aspect_result:
                aspect_type, orb, _ = aspect_result
                if orb <= KARMIC_ORB_THRESHOLD:
                    karmic_aspects.append(KarmicAspect(
                        planet=planet_name,
                        planet_owner="connection",
                        node=node_name,
                        node_owner="user",
                        aspect_type=aspect_type,
                        orb=round(orb, 2),
                        interpretation_hint=KARMIC_PLANET_HINTS.get(planet_name, "")
                    ))

    # Sort by orb (tightest first)
    karmic_aspects.sort(key=lambda a: a.orb)

    # Determine primary theme from tightest aspect
    primary_theme = None
    if karmic_aspects:
        tightest = karmic_aspects[0]
        if tightest.node == "north node":
            primary_theme = f"Future growth through {tightest.planet}"
        else:
            primary_theme = f"Past-life connection through {tightest.planet}"

    return KarmicSummary(
        is_karmic=len(karmic_aspects) > 0,
        karmic_aspects=karmic_aspects,
        primary_theme=primary_theme,
        destiny_note=None  # Will be filled by LLM
    )


# =============================================================================
# Main API Function
# =============================================================================

def calculate_compatibility(
    user_chart: NatalChartData,
    connection_chart: NatalChartData
) -> CompatibilityResult:
    """
    Calculate full compatibility analysis between two charts.

    Includes:
    - Synastry aspects (planet-to-planet)
    - Mode scores (romantic/friendship/coworker)
    - Composite chart (the "Us" midpoint chart)
    - Karmic aspects (planets touching Nodes - the "Destiny" check)

    Args:
        user_chart: User's natal chart (NatalChartData)
        connection_chart: Connection's natal chart (NatalChartData)

    Returns:
        CompatibilityResult with all three modes, synastry aspects, and karmic data
    """
    # Calculate all synastry aspects
    aspects = calculate_synastry_aspects(user_chart, connection_chart)

    # Calculate each mode (the "Mechanics")
    romantic = calculate_mode_compatibility(aspects, ROMANTIC_CATEGORIES)
    friendship = calculate_mode_compatibility(aspects, FRIENDSHIP_CATEGORIES)
    coworker = calculate_mode_compatibility(aspects, COWORKER_CATEGORIES)

    # Calculate composite (the "Purpose")
    composite = calculate_composite_summary(user_chart, connection_chart)

    # Calculate karmic aspects (the "Destiny")
    karmic = calculate_karmic_aspects(user_chart, connection_chart)

    return CompatibilityResult(
        romantic=romantic,
        friendship=friendship,
        coworker=coworker,
        aspects=aspects,
        composite_summary=composite,
        karmic_summary=karmic,
        calculated_at=datetime.now().isoformat()
    )


def get_compatibility_from_birth_data(
    user_birth_date: str,
    user_birth_time: Optional[str],
    user_birth_lat: Optional[float],
    user_birth_lon: Optional[float],
    user_birth_timezone: Optional[str],
    connection_birth_date: str,
    connection_birth_time: Optional[str] = None,
    connection_birth_lat: Optional[float] = None,
    connection_birth_lon: Optional[float] = None,
    connection_birth_timezone: Optional[str] = None,
) -> CompatibilityResult:
    """
    Calculate compatibility from raw birth data.

    Convenience function that computes charts and runs compatibility.

    Args:
        user_birth_*: User's birth data
        connection_birth_*: Connection's birth data

    Returns:
        CompatibilityResult
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

    return calculate_compatibility(user_chart, connection_chart)


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

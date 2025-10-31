"""
Constants for astrometer calculations.

All values are taken from the Astrometers V2 specification.
"""

from typing import Dict, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astro import Planet, AspectType, ZodiacSign

# Import after path setup to avoid circular imports
from astrometers.hierarchy import Meter

# =============================================================================
# Planet Base Scores (Section 2.3.A - Weightage Factor)
# =============================================================================

PLANET_BASE_SCORES: Dict[Planet, float] = {
    # Luminaries
    Planet.SUN: 10.0,
    Planet.MOON: 10.0,

    # Personal planets
    Planet.MERCURY: 7.0,
    Planet.VENUS: 7.0,
    Planet.MARS: 7.0,

    # Social planets
    Planet.JUPITER: 5.0,
    Planet.SATURN: 5.0,

    # Outer planets
    Planet.URANUS: 3.0,
    Planet.NEPTUNE: 3.0,
    Planet.PLUTO: 3.0,

    # North Node - karmic/destiny point (similar to outer planets)
    Planet.NORTH_NODE: 3.0,
}

# =============================================================================
# House Multipliers (Section 2.3.A - Weightage Factor)
# =============================================================================

# Angular houses: Maximum visibility and impact
ANGULAR_HOUSES = [1, 4, 7, 10]
ANGULAR_MULTIPLIER = 3.0

# Succedent houses: Stabilization and resource building
SUCCEDENT_HOUSES = [2, 5, 8, 11]
SUCCEDENT_MULTIPLIER = 2.0

# Cadent houses: Mental and transitional processes
CADENT_HOUSES = [3, 6, 9, 12]
CADENT_MULTIPLIER = 1.0

def get_house_multiplier(house_number: int) -> float:
    """Get house multiplier based on house classification."""
    if house_number in ANGULAR_HOUSES:
        return ANGULAR_MULTIPLIER
    elif house_number in SUCCEDENT_HOUSES:
        return SUCCEDENT_MULTIPLIER
    elif house_number in CADENT_HOUSES:
        return CADENT_MULTIPLIER
    else:
        raise ValueError(f"Invalid house number: {house_number}")

# =============================================================================
# Chart Ruler Bonus (Section 2.3.A - Weightage Factor)
# =============================================================================

CHART_RULER_BONUS = 5.0

# =============================================================================
# Personal Sensitivity (Section 2.3.A - Weightage Factor)
# =============================================================================

DEFAULT_SENSITIVITY = 1.0
MIN_SENSITIVITY = 0.5
MAX_SENSITIVITY = 2.0

# =============================================================================
# Aspect Base Intensity (Section 2.3.B - Transit Power)
# =============================================================================

ASPECT_BASE_INTENSITY: Dict[AspectType, float] = {
    AspectType.CONJUNCTION: 10.0,
    AspectType.OPPOSITION: 9.0,
    AspectType.SQUARE: 8.0,
    AspectType.TRINE: 6.0,
    AspectType.SEXTILE: 4.0,
}

# Aspect exact angles (for aspect detection and direction calculation)
ASPECT_EXACT_ANGLES: Dict[AspectType, int] = {
    AspectType.CONJUNCTION: 0,
    AspectType.SEXTILE: 60,
    AspectType.SQUARE: 90,
    AspectType.TRINE: 120,
    AspectType.OPPOSITION: 180,
}

# =============================================================================
# Maximum Orbs by Aspect and Planet Type (Section 4.1 - Aspect Detection)
# =============================================================================

# Luminaries get wider orbs
LUMINARIES = {Planet.SUN, Planet.MOON}

# Outer planets get tighter orbs
OUTER_PLANETS = {Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO}

# Social planets
SOCIAL_PLANETS = {Planet.JUPITER, Planet.SATURN}

# Inner/Personal planets
INNER_PLANETS = {Planet.MERCURY, Planet.VENUS, Planet.MARS}

# Maximum orbs for major aspects (conjunction, opposition)
MAJOR_ASPECT_ORB_LUMINARY = 10.0
MAJOR_ASPECT_ORB_PLANET = 8.0
MAJOR_ASPECT_ORB_OUTER = 6.0

# Maximum orbs for square and trine
MEDIUM_ASPECT_ORB_LUMINARY = 8.0
MEDIUM_ASPECT_ORB_PLANET = 7.0
MEDIUM_ASPECT_ORB_OUTER = 5.0

# Maximum orbs for sextile
MINOR_ASPECT_ORB_LUMINARY = 6.0
MINOR_ASPECT_ORB_PLANET = 5.0
MINOR_ASPECT_ORB_OUTER = 4.0

def get_max_orb(
    aspect_type: AspectType,
    natal_planet: Planet,
    transit_planet: Planet
) -> float:
    """
    Determine maximum orb based on aspect type and planets involved.

    From spec Section 4.1: Wider orbs for luminaries and major aspects,
    tighter orbs for outer planets and minor aspects.
    """
    is_luminary_involved = (natal_planet in LUMINARIES or
                           transit_planet in LUMINARIES)
    is_outer_transit = transit_planet in OUTER_PLANETS

    # Major aspects: conjunction, opposition
    if aspect_type in [AspectType.CONJUNCTION, AspectType.OPPOSITION]:
        if is_luminary_involved:
            return MAJOR_ASPECT_ORB_LUMINARY
        elif is_outer_transit:
            return MAJOR_ASPECT_ORB_OUTER
        else:
            return MAJOR_ASPECT_ORB_PLANET

    # Medium aspects: square, trine
    elif aspect_type in [AspectType.SQUARE, AspectType.TRINE]:
        if is_luminary_involved:
            return MEDIUM_ASPECT_ORB_LUMINARY
        elif is_outer_transit:
            return MEDIUM_ASPECT_ORB_OUTER
        else:
            return MEDIUM_ASPECT_ORB_PLANET

    # Minor aspects: sextile
    elif aspect_type == AspectType.SEXTILE:
        if is_luminary_involved:
            return MINOR_ASPECT_ORB_LUMINARY
        elif is_outer_transit:
            return MINOR_ASPECT_ORB_OUTER
        else:
            return MINOR_ASPECT_ORB_PLANET

    else:
        raise ValueError(f"Unknown aspect type: {aspect_type}")

# =============================================================================
# Direction Modifiers (Section 2.3.B - Transit Power)
# =============================================================================

# Applying: aspect is forming, getting tighter
APPLYING_MODIFIER = 1.3

# Exact: aspect is within 0.5 degrees of exact
EXACT_MODIFIER = 1.5
EXACT_THRESHOLD_DEGREES = 0.5

# Separating: aspect is waning, getting wider
SEPARATING_MODIFIER = 0.7

# =============================================================================
# Station Modifiers (Section 2.3.B - Transit Power)
# =============================================================================

# Station: planet within 5 days of retrograde direction change
STATION_MODIFIER_MAX = 1.8
STATION_MODIFIER_MIN = 1.2
STATION_WINDOW_DAYS = 5

def get_station_modifier(days_from_station: int) -> float:
    """
    Calculate station modifier based on days from station.

    Peak at exact station (1.8), declining linearly over 5 days to 1.2.
    From spec Section 4.5: Station Intensity Boost
    """
    if days_from_station > STATION_WINDOW_DAYS:
        return 1.0

    # Linear decay from 1.8 to 1.2 over 5 days
    decline_per_day = (STATION_MODIFIER_MAX - STATION_MODIFIER_MIN) / STATION_WINDOW_DAYS
    return STATION_MODIFIER_MAX - (decline_per_day * days_from_station)

# =============================================================================
# Transit Planet Weights (Section 2.3.B - Transit Power)
# =============================================================================

TRANSIT_PLANET_WEIGHTS: Dict[Planet, float] = {
    # Outer planets: months to years duration
    Planet.PLUTO: 1.5,
    Planet.NEPTUNE: 1.5,
    Planet.URANUS: 1.5,

    # Social planets: weeks to months duration
    Planet.SATURN: 1.2,
    Planet.JUPITER: 1.2,

    # Inner planets: days to weeks duration
    Planet.MARS: 1.0,
    Planet.VENUS: 1.0,
    Planet.MERCURY: 1.0,
    Planet.SUN: 1.0,

    # Moon: hours to days duration (de-emphasized)
    Planet.MOON: 0.8,

    # North Node: karmic/destiny point (slow-moving, similar to outer planets)
    Planet.NORTH_NODE: 1.5,
}

# =============================================================================
# Quality Factors (Section 2.3.C - Quality Factor)
# =============================================================================

# Fixed quality scores for non-conjunction aspects
QUALITY_TRINE = 1.0
QUALITY_SEXTILE = 1.0
QUALITY_SQUARE = -1.0
QUALITY_OPPOSITION = -1.0

# Benefic and malefic planets for conjunction quality
BENEFIC_PLANETS = {Planet.VENUS, Planet.JUPITER}
MALEFIC_PLANETS = {Planet.MARS, Planet.SATURN}
TRANSFORMATIONAL_PLANETS = {Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO}

# Conjunction quality values
CONJUNCTION_DOUBLE_BENEFIC = 0.8
CONJUNCTION_DOUBLE_MALEFIC = -0.8
CONJUNCTION_BENEFIC_MALEFIC = 0.2
CONJUNCTION_TRANSFORMATIONAL = -0.3
CONJUNCTION_DEFAULT = 0.0

# Quality label thresholds (exact mapping to actual quality values)
QUALITY_BLISSFUL_THRESHOLD = 1.0           # +1.0 (trine, sextile)
QUALITY_VERY_HARMONIOUS_THRESHOLD = 0.8    # +0.8 (double benefic)
QUALITY_HARMONIOUS_THRESHOLD = 0.2         # +0.2 (benefic-malefic)
QUALITY_NEUTRAL_THRESHOLD = -0.3           # 0.0, -0.3 (default/transformational)
QUALITY_CHALLENGING_THRESHOLD = -0.8       # -0.8 (double malefic)
QUALITY_VERY_CHALLENGING_THRESHOLD = -1.0  # -1.0 (square, opposition)
# < -1.0: Extremely Challenging (reserved for future)

# =============================================================================
# Essential Dignity Scores (Section 3.2 - Planetary Dignity)
# =============================================================================

DIGNITY_DOMICILE = 5
DIGNITY_EXALTATION = 4
DIGNITY_NEUTRAL = 0
DIGNITY_DETRIMENT = -5
DIGNITY_FALL = -4

# Essential Dignity Table
# Planet -> {domicile: [signs], exaltation: [(sign, degree)], detriment: [signs], fall: [(sign, degree)]}
ESSENTIAL_DIGNITIES = {
    Planet.SUN: {
        "domicile": [ZodiacSign.LEO],
        "exaltation": [(ZodiacSign.ARIES, 19)],
        "detriment": [ZodiacSign.AQUARIUS],
        "fall": [(ZodiacSign.LIBRA, 19)]
    },
    Planet.MOON: {
        "domicile": [ZodiacSign.CANCER],
        "exaltation": [(ZodiacSign.TAURUS, 3)],
        "detriment": [ZodiacSign.CAPRICORN],
        "fall": [(ZodiacSign.SCORPIO, 3)]
    },
    Planet.MERCURY: {
        "domicile": [ZodiacSign.GEMINI, ZodiacSign.VIRGO],
        "exaltation": [(ZodiacSign.VIRGO, 15)],
        "detriment": [ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES],
        "fall": [(ZodiacSign.PISCES, 15)]
    },
    Planet.VENUS: {
        "domicile": [ZodiacSign.TAURUS, ZodiacSign.LIBRA],
        "exaltation": [(ZodiacSign.PISCES, 27)],
        "detriment": [ZodiacSign.SCORPIO, ZodiacSign.ARIES],
        "fall": [(ZodiacSign.VIRGO, 27)]
    },
    Planet.MARS: {
        "domicile": [ZodiacSign.ARIES, ZodiacSign.SCORPIO],
        "exaltation": [(ZodiacSign.CAPRICORN, 28)],
        "detriment": [ZodiacSign.LIBRA, ZodiacSign.TAURUS],
        "fall": [(ZodiacSign.CANCER, 28)]
    },
    Planet.JUPITER: {
        "domicile": [ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES],
        "exaltation": [(ZodiacSign.CANCER, 15)],
        "detriment": [ZodiacSign.GEMINI, ZodiacSign.VIRGO],
        "fall": [(ZodiacSign.CAPRICORN, 15)]
    },
    Planet.SATURN: {
        "domicile": [ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS],
        "exaltation": [(ZodiacSign.LIBRA, 21)],
        "detriment": [ZodiacSign.CANCER, ZodiacSign.LEO],
        "fall": [(ZodiacSign.ARIES, 21)]
    },
    # Outer planets don't have traditional dignities
    Planet.URANUS: {
        "domicile": [],
        "exaltation": [],
        "detriment": [],
        "fall": []
    },
    Planet.NEPTUNE: {
        "domicile": [],
        "exaltation": [],
        "detriment": [],
        "fall": []
    },
    Planet.PLUTO: {
        "domicile": [],
        "exaltation": [],
        "detriment": [],
        "fall": []
    },
}

# =============================================================================
# Normalization Constants (Section 2.4 - Placeholder values)
# =============================================================================

# These are PLACEHOLDER values for MVP
# Per spec: must be empirically calibrated with 10,000+ charts
# For now, use reasonable estimates

DTI_MAX_ESTIMATE = 200.0  # 95th percentile estimate
HQS_MAX_POSITIVE_ESTIMATE = 100.0  # 95th percentile for harmonious periods
HQS_MAX_NEGATIVE_ESTIMATE = 100.0  # 95th percentile for challenging periods

# Target scale for normalized meters
METER_SCALE = 100

# Harmony meter neutral point
HARMONY_NEUTRAL = 50

# Intensity meter thresholds (from spec Section 2.5 Interpretation Matrix)
INTENSITY_QUIET_THRESHOLD = 31       # 0-30: Quiet
INTENSITY_MILD_THRESHOLD = 51        # 31-50: Mild
INTENSITY_MODERATE_THRESHOLD = 71    # 51-70: Moderate
INTENSITY_HIGH_THRESHOLD = 86        # 71-85: High
# >= 86: Extreme

# Harmony meter thresholds (from spec Section 2.5 Interpretation Matrix)
HARMONY_CHALLENGING_THRESHOLD = 31   # 0-30: Challenging
HARMONY_HARMONIOUS_THRESHOLD = 70    # 70-100: Harmonious
# 31-69: Mixed/Neutral

# =============================================================================
# Meter Importance Weights (for Super-Group Aggregation)
# =============================================================================

# Weight individual meters for super-group calculations
# Higher weights indicate meters that users engage with more or are more impactful
# Weights are normalized during aggregation, so these are relative importance

METER_IMPORTANCE_WEIGHTS: Dict[Meter, float] = {
    # OVERVIEW - Highest importance (dashboard summary)
    Meter.OVERALL_INTENSITY: 2.0,
    Meter.OVERALL_HARMONY: 2.0,

    # MIND - High importance (daily cognitive function)
    Meter.MENTAL_CLARITY: 2.0,
    Meter.DECISION_QUALITY: 1.5,
    Meter.COMMUNICATION_FLOW: 1.5,

    # EMOTIONS - High importance (emotional well-being)
    Meter.EMOTIONAL_INTENSITY: 2.0,
    Meter.RELATIONSHIP_HARMONY: 1.5,
    Meter.EMOTIONAL_RESILIENCE: 1.5,

    # BODY - High importance (physical energy and action)
    Meter.PHYSICAL_ENERGY: 2.0,
    Meter.MOTIVATION_DRIVE: 1.5,
    Meter.CONFLICT_RISK: 1.0,

    # CAREER - High importance (professional life)
    Meter.CAREER_AMBITION: 2.0,
    Meter.OPPORTUNITY_WINDOW: 1.5,

    # EVOLUTION - Medium-high importance (personal growth)
    Meter.CHALLENGE_INTENSITY: 1.5,
    Meter.TRANSFORMATION_PRESSURE: 1.5,
    Meter.INNOVATION_BREAKTHROUGH: 1.0,

    # ELEMENTS - Medium importance (temperament patterns)
    Meter.FIRE_ENERGY: 0.7,
    Meter.EARTH_ENERGY: 0.7,
    Meter.AIR_ENERGY: 0.7,
    Meter.WATER_ENERGY: 0.7,

    # SPIRITUAL - Medium importance (spiritual awareness)
    Meter.INTUITION_SPIRITUALITY: 1.0,
    Meter.KARMIC_LESSONS: 1.0,

    # COLLECTIVE - Lower importance (less personally immediate)
    Meter.SOCIAL_COLLECTIVE: 0.5,
}

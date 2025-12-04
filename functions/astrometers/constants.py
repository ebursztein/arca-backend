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

    # South Node - karmic/destiny point (same as North Node)
    Planet.SOUTH_NODE: 3.0,
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
# Transit Planet Weights (Section 2.3.B - Transit Power) - LEGACY
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

    # South Node: karmic/destiny point (same as North Node)
    Planet.SOUTH_NODE: 1.5,
}

# =============================================================================
# Velocity-Based Tiered System (V2 - "The Symphony")
# =============================================================================
# Transit planet defines time scale AND weight scale.
# Fast planets = loud melody (high daily weight, short window)
# Slow planets = quiet bass (low daily weight, long window)
#
# The key insight: normalize by "total area under curve" so that
# rare long aspects don't drown out frequent short aspects.

class TransitTier:
    """Transit tier configuration."""
    def __init__(self, name: str, window_days: float, weight: float):
        self.name = name
        self.window_days = window_days  # How long aspect is "active"
        self.weight = weight  # Daily contribution weight


# =============================================================================
# Mixing Profiles - Different philosophies for tier weighting
# =============================================================================
# Each profile creates a different "feel" for the app:
#
# DAILY_PULSE: High engagement, gamification. Score changes dramatically daily.
#   - Risk: Ignores major life transits, feels superficial during crisis
#   - Target: ~50% trigger, ~30% event, ~20% context
#
# DEEP_CURRENT: Psychological accuracy. Life phases set the stage, days are actors.
#   - Benefit: High credibility, acknowledges both daily mood and life chapter
#   - Target: ~30% trigger, ~30% event, ~20% season, ~20% era
#
# FORECAST: Event prediction. Emphasizes external happenings over internal mood.
#   - Target: ~20% trigger, ~50% event, ~30% outer

MIXING_PROFILES: Dict[str, Dict[str, float]] = {
    'daily_pulse': {
        'trigger': 10.0,  # Moon dominates
        'event': 4.0,
        'season': 1.5,
        'era': 0.5,
    },
    'deep_current': {
        'trigger': 3.0,   # Compressed spread
        'event': 3.0,     # Equal to trigger
        'season': 2.0,    # Boosted
        'era': 2.0,       # Boosted significantly
    },
    'forecast': {
        'trigger': 2.0,   # Moon just for timing
        'event': 5.0,     # Inner planets dominate
        'season': 2.0,
        'era': 3.0,       # Outer planets matter for big events
    },
}

# Active mixing profile (can be changed at runtime or via config)
ACTIVE_MIXING_PROFILE = 'deep_current'


def get_tier_weights(profile: str = None) -> Dict[str, float]:
    """Get tier weights for a mixing profile."""
    if profile is None:
        profile = ACTIVE_MIXING_PROFILE
    return MIXING_PROFILES.get(profile, MIXING_PROFILES['deep_current'])


# Tier definitions - time windows are fixed, weights come from mixing profile
TRANSIT_TIERS: Dict[str, TransitTier] = {
    # THE TRIGGER - Moon is the "second hand", provides daily variance
    # ~12-24 hour window
    'trigger': TransitTier('trigger', window_days=1.0, weight=get_tier_weights()['trigger']),

    # THE EVENT - Inner planets are the "minute hand", weekly events
    # ~4 day window
    'event': TransitTier('event', window_days=4.0, weight=get_tier_weights()['event']),

    # THE SEASON - Social planets are the "hour hand", monthly context
    # ~45 day window
    'season': TransitTier('season', window_days=45.0, weight=get_tier_weights()['season']),

    # THE ERA - Outer planets are the "calendar", tectonic shifts
    # ~100 day window
    'era': TransitTier('era', window_days=100.0, weight=get_tier_weights()['era']),
}


def set_mixing_profile(profile: str) -> None:
    """
    Change the active mixing profile and update tier weights.

    Args:
        profile: One of 'daily_pulse', 'deep_current', 'forecast'
    """
    global ACTIVE_MIXING_PROFILE, TRANSIT_TIERS

    if profile not in MIXING_PROFILES:
        raise ValueError(f"Unknown profile: {profile}. Choose from {list(MIXING_PROFILES.keys())}")

    ACTIVE_MIXING_PROFILE = profile
    weights = MIXING_PROFILES[profile]

    # Update tier weights
    TRANSIT_TIERS['trigger'] = TransitTier('trigger', window_days=1.0, weight=weights['trigger'])
    TRANSIT_TIERS['event'] = TransitTier('event', window_days=4.0, weight=weights['event'])
    TRANSIT_TIERS['season'] = TransitTier('season', window_days=45.0, weight=weights['season'])
    TRANSIT_TIERS['era'] = TransitTier('era', window_days=100.0, weight=weights['era'])

# Map planets to their tiers
PLANET_TO_TIER: Dict[Planet, str] = {
    # Trigger tier - the melody
    Planet.MOON: 'trigger',

    # Event tier - weekly rhythm
    Planet.SUN: 'event',
    Planet.MERCURY: 'event',
    Planet.VENUS: 'event',
    Planet.MARS: 'event',

    # Season tier - monthly context
    Planet.JUPITER: 'season',
    Planet.SATURN: 'season',

    # Era tier - the bass
    Planet.URANUS: 'era',
    Planet.NEPTUNE: 'era',
    Planet.PLUTO: 'era',
    Planet.NORTH_NODE: 'era',
    Planet.SOUTH_NODE: 'era',
}


def get_transit_tier(planet: Planet) -> TransitTier:
    """Get the tier configuration for a transit planet."""
    tier_name = PLANET_TO_TIER.get(planet, 'event')
    return TRANSIT_TIERS[tier_name]

# =============================================================================
# Quality Factors (Section 2.3.C - Quality Factor)
# =============================================================================

# Fixed quality scores for non-conjunction aspects - FLAT BASELINE
# Used in raw score calculations and calibration
QUALITY_TRINE = 1.0
QUALITY_SEXTILE = 1.0
QUALITY_SQUARE = -1.0
QUALITY_OPPOSITION = -1.0

# Benefic and malefic planets for conjunction quality
BENEFIC_PLANETS = {Planet.VENUS, Planet.JUPITER}
MALEFIC_PLANETS = {Planet.MARS, Planet.SATURN}
TRANSFORMATIONAL_PLANETS = {Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO}

# Planetary Nature Multipliers (applied via harmonic_boost function)
# Based on 2,000+ years of observational astrology
# Applied AFTER raw score calculation, BEFORE normalization
BENEFIC_QUALITY_MULTIPLIER = 2.0    # Venus/Jupiter enhance harmonious aspects (optimistic: 2x boost)
MALEFIC_QUALITY_MULTIPLIER = 0.5    # Mars/Saturn soften challenging aspects (optimistic: 0.5x softening)

# Conjunction quality values
CONJUNCTION_DOUBLE_BENEFIC = 0.8
CONJUNCTION_DOUBLE_MALEFIC = -0.8
CONJUNCTION_BENEFIC_MALEFIC = 0.2
CONJUNCTION_TRANSFORMATIONAL = -0.3
CONJUNCTION_DEFAULT = 0.0

# Quality label thresholds (V2 Optimistic Model - updated for new ranges)
# New range: +1.32 (trine × benefic) to -0.85 (opposition × malefic)
QUALITY_BLISSFUL_THRESHOLD = 1.1           # ≥1.1 (trine/sextile with benefic boost)
QUALITY_VERY_HARMONIOUS_THRESHOLD = 0.8    # ≥0.8 (double benefic, strong harmonious)
QUALITY_HARMONIOUS_THRESHOLD = 0.2         # ≥0.2 (benefic-malefic, mild positive)
QUALITY_NEUTRAL_THRESHOLD = -0.3           # ≥-0.3 (default/transformational conjunctions)
QUALITY_CHALLENGING_THRESHOLD = -0.7       # ≥-0.7 (softened challenging aspects)
QUALITY_VERY_CHALLENGING_THRESHOLD = -0.85 # ≥-0.85 (harsh aspects, still softened)
# < -0.85: Extremely Challenging (rare, double malefic)

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
# Unified Score V2 Constants (Polar-style with sigmoid stretch)
# =============================================================================

# Base formula weights for polar-style calculation
# unified_score combines intensity (magnitude) with harmony (direction)
UNIFIED_SCORE_BASE_WEIGHT = 0.3      # Minimum harmony signal preserved (even at intensity=0)
UNIFIED_SCORE_INTENSITY_WEIGHT = 0.7  # How much intensity amplifies the signal

# Sigmoid stretch factor - controls how much middle values spread toward extremes
# Uses tanh for natural S-curve: lower = more stretch, higher = less stretch
UNIFIED_SCORE_TANH_FACTOR = 50.0

# Empowering asymmetry - positive experiences emphasized, negative softened
# This creates an optimistic bias aligned with empowering brand voice
UNIFIED_SCORE_POSITIVE_BOOST = 1.2   # Amplify positive scores
UNIFIED_SCORE_NEGATIVE_DAMPEN = 0.7  # Soften negative scores

# =============================================================================
# Cosmic Background Noise Constants
# =============================================================================

# Adds daily variation for natural meter movement (seeded by user_id + date)
# Only applied when aspect_count > 0 (no noise on truly quiet days)
COSMIC_NOISE_INTENSITY_MIN = -5.0    # Minimum intensity noise
COSMIC_NOISE_INTENSITY_MAX = 10.0    # Maximum intensity noise (slight positive bias)
COSMIC_NOISE_HARMONY_MIN = 0.0       # Minimum harmony nudge (never negative - empowering)
COSMIC_NOISE_HARMONY_MAX = 3.0       # Maximum harmony nudge

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
    # MIND - High importance (daily cognitive function)
    Meter.CLARITY: 2.0,
    Meter.FOCUS: 1.5,
    Meter.COMMUNICATION: 1.5,

    # EMOTIONS - High importance (emotional well-being)
    Meter.FLOW: 2.0,
    Meter.RESILIENCE: 1.5,
    Meter.VULNERABILITY: 1.0,

    # BODY - High importance (physical energy and action)
    Meter.ENERGY: 2.0,
    Meter.DRIVE: 1.5,
    Meter.STRENGTH: 1.0,

    # SPIRIT - Medium-high importance (spiritual and creative expression)
    Meter.VISION: 1.5,
    Meter.FLOW: 1.0,
    Meter.INTUITION: 1.0,
    Meter.CREATIVITY: 1.2,

    # GROWTH - High importance (career and personal evolution)
    Meter.MOMENTUM: 1.5,
    Meter.AMBITION: 2.0,
    Meter.EVOLUTION: 1.5,
    Meter.CIRCLE: 1.0,
}

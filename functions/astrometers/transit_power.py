"""
Transit Power (P_i) calculations for astrometers.

Part 1: Aspect detection and orb factor calculation
Part 2: Direction modifiers and station detection (TODO)

Calculates the strength of a transiting aspect based on:
- Aspect type base intensity (conjunction=10, opposition=9, etc.)
- Orb tightness (linear decay from exact to max orb)
- Transit planet weight (outer=×1.5, social=×1.2, inner=×1.0)

Formula (Part 1):
P_i = Aspect_Base × Orb_Factor × Transit_Weight

Formula (Complete, with Part 2):
P_i = Aspect_Base × Orb_Factor × Direction_Mod × Station_Mod × Transit_Weight

From spec Section 2.3.B (Transit Power) and Section 4.1-4.2 (Aspect Detection)
"""

import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Tuple
from astro import Planet, AspectType
from .constants import (
    ASPECT_BASE_INTENSITY,
    ASPECT_EXACT_ANGLES,
    get_max_orb,
    TRANSIT_PLANET_WEIGHTS,
)


def calculate_angular_separation(longitude1: float, longitude2: float) -> float:
    """
    Calculate the shortest arc between two zodiacal longitudes.

    The zodiac is a circle (0-360°), so we need to take the shorter path
    around the circle.

    Args:
        longitude1: First longitude in degrees (0-360)
        longitude2: Second longitude in degrees (0-360)

    Returns:
        float: Angular separation in degrees (0-180)

    Examples:
        >>> calculate_angular_separation(10, 20)
        10.0
        >>> calculate_angular_separation(350, 10)
        20.0  # Shorter path crosses 0°
        >>> calculate_angular_separation(180, 0)
        180.0
    """
    diff = abs(longitude1 - longitude2)

    # Take shorter arc around the circle
    if diff > 180:
        diff = 360 - diff

    return diff


def detect_aspect(
    transit_longitude: float,
    natal_longitude: float,
    transit_planet: Planet,
    natal_planet: Planet
) -> Optional[Tuple[AspectType, float, float]]:
    """
    Detect if two planets form an aspect within orb.

    Tests all major aspects (conjunction, sextile, square, trine, opposition)
    and returns the aspect with the tightest orb if within allowable range.

    Args:
        transit_longitude: Transit planet longitude (0-360)
        natal_longitude: Natal planet longitude (0-360)
        transit_planet: The transiting planet
        natal_planet: The natal planet

    Returns:
        Optional[Tuple[AspectType, float, float]]:
            (aspect_type, deviation_from_exact, max_orb) or None if no aspect

    Example:
        >>> detect_aspect(90.5, 0, Planet.SATURN, Planet.SUN)
        (AspectType.SQUARE, 0.5, 8.0)  # Saturn square Sun, 0.5° from exact
    """
    angle = calculate_angular_separation(transit_longitude, natal_longitude)

    # Find closest aspect within orb
    best_aspect = None
    best_deviation = float('inf')

    for aspect_type, exact_angle in ASPECT_EXACT_ANGLES.items():
        deviation = abs(angle - exact_angle)
        max_orb = get_max_orb(aspect_type, natal_planet, transit_planet)

        if deviation <= max_orb:
            # Track the tightest aspect (smallest deviation)
            if deviation < best_deviation:
                best_aspect = aspect_type
                best_deviation = deviation

    if best_aspect is not None:
        max_orb = get_max_orb(best_aspect, natal_planet, transit_planet)
        return (best_aspect, best_deviation, max_orb)

    return None


def calculate_orb_factor(deviation: float, max_orb: float) -> float:
    """
    Calculate aspect strength based on orb tightness.

    Linear decay from 1.0 (exact) to 0.0 (max orb).

    Args:
        deviation: Degrees from exact aspect (e.g., 2° from exact 90° square)
        max_orb: Maximum allowable orb for this aspect

    Returns:
        float: Orb factor (0.0 to 1.0)

    Examples:
        >>> calculate_orb_factor(0, 8)
        1.0  # Exact aspect
        >>> calculate_orb_factor(4, 8)
        0.5  # Halfway from exact to max
        >>> calculate_orb_factor(8, 8)
        0.0  # At max orb
        >>> calculate_orb_factor(9, 8)
        0.0  # Beyond max orb
    """
    if deviation > max_orb:
        return 0.0

    return 1.0 - (deviation / max_orb)


def calculate_transit_power_basic(
    aspect_type: AspectType,
    orb_deviation: float,
    max_orb: float,
    transit_planet: Planet
) -> float:
    """
    Calculate basic transit power (without direction/station modifiers).

    This is Part 1 of the transit power calculation. Part 2 will add
    applying/separating and station modifiers.

    Formula: P_i = Aspect_Base × Orb_Factor × Transit_Weight

    Args:
        aspect_type: Type of aspect (conjunction, square, etc.)
        orb_deviation: Degrees from exact aspect
        max_orb: Maximum orb for this aspect
        transit_planet: The transiting planet

    Returns:
        float: Transit power (P_i) before direction/station modifiers

    Example from spec:
        >>> # Transit Saturn square Natal Sun
        >>> # Orb: 2° from exact 90° (max orb 8°)
        >>> # Orb Factor: 1 - (2/8) = 0.778
        >>> # Transit Weight: Social planet = 1.2
        >>> calculate_transit_power_basic(
        ...     AspectType.SQUARE, 2.0, 8.0, Planet.SATURN
        ... )
        # 8 × 0.778 × 1.2 = 7.4688 (spec shows 9.70 but includes direction modifier)
    """
    aspect_base = ASPECT_BASE_INTENSITY[aspect_type]
    orb_factor = calculate_orb_factor(orb_deviation, max_orb)
    transit_weight = TRANSIT_PLANET_WEIGHTS[transit_planet]

    power = aspect_base * orb_factor * transit_weight

    return power


def get_aspect_strength_label(orb_factor: float) -> str:
    """
    Get human-readable label for aspect strength based on orb factor.

    Args:
        orb_factor: Orb factor (0.0 to 1.0)

    Returns:
        str: Strength label
    """
    if orb_factor >= 0.9:
        return "Exact"
    elif orb_factor >= 0.7:
        return "Very Strong"
    elif orb_factor >= 0.5:
        return "Strong"
    elif orb_factor >= 0.3:
        return "Moderate"
    elif orb_factor > 0:
        return "Weak"
    else:
        return "None"


# =============================================================================
# Part 2: Direction and Station Modifiers (Phase 4)
# =============================================================================

def get_direction_modifier(today_deviation: float, tomorrow_deviation: float) -> Tuple[str, float]:
    """
    Determine if aspect is applying, exact, or separating.

    Applying aspects are forming (getting tighter).
    Separating aspects are waning (getting wider).

    Args:
        today_deviation: Degrees from exact aspect today
        tomorrow_deviation: Degrees from exact aspect tomorrow

    Returns:
        Tuple[str, float]: (status, modifier)
            status: "exact", "applying", or "separating"
            modifier: 1.5 for exact, 1.3 for applying, 0.7 for separating

    Examples:
        >>> get_direction_modifier(0.3, 0.5)
        ("exact", 1.5)  # Within 0.5° is exact
        >>> get_direction_modifier(2.0, 1.5)
        ("applying", 1.3)  # Getting closer
        >>> get_direction_modifier(1.5, 2.0)
        ("separating", 0.7)  # Getting wider
    """
    from .constants import (
        EXACT_MODIFIER,
        EXACT_THRESHOLD_DEGREES,
        APPLYING_MODIFIER,
        SEPARATING_MODIFIER
    )

    if today_deviation <= EXACT_THRESHOLD_DEGREES:
        return ("exact", EXACT_MODIFIER)
    elif tomorrow_deviation < today_deviation:
        return ("applying", APPLYING_MODIFIER)
    else:
        return ("separating", SEPARATING_MODIFIER)


def calculate_station_modifier(days_from_station: Optional[int]) -> float:
    """
    Calculate station modifier based on days from retrograde station.

    When a planet is stationary (changing direction), its influence
    is amplified. Peak at exact station (×1.8), declining over 5 days.

    Args:
        days_from_station: Days from nearest station (0-5), or None if not stationary

    Returns:
        float: Station modifier (1.0 if not stationary, 1.2-1.8 if stationary)

    Examples:
        >>> calculate_station_modifier(0)
        1.8  # Exact station
        >>> calculate_station_modifier(3)
        1.44  # 3 days from station
        >>> calculate_station_modifier(5)
        1.2  # 5 days from station
        >>> calculate_station_modifier(None)
        1.0  # Not stationary
    """
    from .constants import get_station_modifier as get_modifier

    if days_from_station is None:
        return 1.0

    return get_modifier(days_from_station)


def calculate_transit_power_complete(
    aspect_type: AspectType,
    orb_deviation: float,
    max_orb: float,
    transit_planet: Planet,
    today_deviation: Optional[float] = None,
    tomorrow_deviation: Optional[float] = None,
    days_from_station: Optional[int] = None
) -> Tuple[float, dict]:
    """
    Complete transit power calculation with all modifiers.

    Formula: P_i = Aspect_Base × Orb_Factor × Direction_Mod × Station_Mod × Transit_Weight

    Args:
        aspect_type: Type of aspect
        orb_deviation: Degrees from exact aspect
        max_orb: Maximum orb for this aspect
        transit_planet: The transiting planet
        today_deviation: Today's deviation for direction calculation (optional)
        tomorrow_deviation: Tomorrow's deviation for direction calculation (optional)
        days_from_station: Days from nearest station (optional)

    Returns:
        Tuple[float, dict]: (power, breakdown)
            power: Complete transit power value
            breakdown: Dict with all components for explainability

    Example from spec:
        >>> # Transit Saturn square Natal Sun
        >>> # Orb: 2° from exact 90° (max orb 8°)
        >>> # Applying (tomorrow 1.5°)
        >>> # Not stationary
        >>> power, breakdown = calculate_transit_power_complete(
        ...     AspectType.SQUARE, 2.0, 8.0, Planet.SATURN,
        ...     today_deviation=2.0, tomorrow_deviation=1.5
        ... )
        >>> # 8 × 0.75 × 1.3 × 1.0 × 1.2 = 9.36
        >>> round(power, 2)
        9.36
    """
    # Calculate base components
    aspect_base = ASPECT_BASE_INTENSITY[aspect_type]
    orb_factor = calculate_orb_factor(orb_deviation, max_orb)
    transit_weight = TRANSIT_PLANET_WEIGHTS[transit_planet]

    # Calculate direction modifier
    if today_deviation is not None and tomorrow_deviation is not None:
        direction_status, direction_mod = get_direction_modifier(
            today_deviation, tomorrow_deviation
        )
    else:
        direction_status = "unknown"
        direction_mod = 1.0  # Neutral if not provided

    # Calculate station modifier
    station_mod = calculate_station_modifier(days_from_station)

    # Complete formula
    power = aspect_base * orb_factor * direction_mod * station_mod * transit_weight

    # Build breakdown for explainability
    breakdown = {
        'aspect_base': aspect_base,
        'orb_factor': orb_factor,
        'direction_modifier': direction_mod,
        'direction_status': direction_status,
        'station_modifier': station_mod,
        'transit_weight': transit_weight,
        'power': power,
        'is_stationary': days_from_station is not None
    }

    return power, breakdown


def get_aspect_direction_status(
    transit_longitude_today: float,
    natal_longitude: float,
    transit_longitude_tomorrow: float,
    aspect_type: AspectType
) -> Tuple[str, float]:
    """
    Helper to determine direction status from planet positions.

    Args:
        transit_longitude_today: Transit planet position today
        natal_longitude: Natal planet position
        transit_longitude_tomorrow: Transit planet position tomorrow
        aspect_type: The aspect type being checked

    Returns:
        Tuple[str, float]: (status, modifier)
    """
    # Get exact angle for this aspect
    exact_angle = ASPECT_EXACT_ANGLES[aspect_type]

    # Calculate deviations
    angle_today = calculate_angular_separation(transit_longitude_today, natal_longitude)
    angle_tomorrow = calculate_angular_separation(transit_longitude_tomorrow, natal_longitude)

    today_deviation = abs(angle_today - exact_angle)
    tomorrow_deviation = abs(angle_tomorrow - exact_angle)

    return get_direction_modifier(today_deviation, tomorrow_deviation)


# =============================================================================
# Part 3: Velocity-Based Tiered Scoring ("The Symphony")
# =============================================================================
# This is the V2 scoring system that uses time-normalized orbs and
# frequency-based weighting to create dynamic daily meter variation.
#
# Key principles:
# 1. Transit planet defines time scale (fast = short window, slow = long window)
# 2. Transit planet defines weight scale (fast = high weight, slow = low weight)
# 3. Squared closeness ("The Spike") makes exact aspects pop
# 4. Total area under curve is normalized so Moon doesn't get drowned out

# Safety clamps for dynamic orb limits
DYNAMIC_ORB_MIN = 0.5  # Floor: don't let slow planets have vanishing orbs
DYNAMIC_ORB_MAX = 8.0  # Cap: don't let fast planets have huge orbs

# Aspect type modifiers (simpler than ASPECT_BASE_INTENSITY)
ASPECT_MODIFIERS = {
    AspectType.CONJUNCTION: 1.0,
    AspectType.OPPOSITION: 1.0,
    AspectType.SQUARE: 1.0,
    AspectType.TRINE: 0.8,
    AspectType.SEXTILE: 0.5,
}


def calculate_velocity_score(
    transit_planet: Planet,
    deviation_deg: float,
    transit_speed: float,
    aspect_type: AspectType,
) -> Tuple[float, dict]:
    """
    Calculate aspect score using velocity-based tiered system.

    Scores based on TIME (velocity) rather than SPACE (degrees).
    The transit planet defines both the time window and the weight.

    Formula:
        dynamic_limit = (window_days * speed) / 2  (half window each side)
        dynamic_limit = clamp(dynamic_limit, 0.5, 8.0)  (safety bounds)
        closeness = 1 - (deviation / dynamic_limit)
        intensity = closeness^2  (The Spike - sharper peak)
        score = intensity * tier_weight * aspect_modifier

    Args:
        transit_planet: The transiting planet (defines tier)
        deviation_deg: Degrees from exact aspect (orb)
        transit_speed: Transit planet speed in degrees/day
        aspect_type: Type of aspect (for modifier)

    Returns:
        Tuple[float, dict]: (score, breakdown)
            score: The velocity-adjusted aspect score
            breakdown: Components for debugging/visualization

    Example:
        >>> # Moon at 2 degrees from exact, moving 13 deg/day
        >>> # dynamic_limit = (1.0 * 13) / 2 = 6.5 deg
        >>> # closeness = 1 - (2 / 6.5) = 0.69
        >>> # intensity = 0.69^2 = 0.48
        >>> # score = 0.48 * 10.0 * 1.0 = 4.8

        >>> # Pluto at 2 degrees from exact, moving 0.02 deg/day
        >>> # dynamic_limit = (100 * 0.02) / 2 = 1.0 deg (clamped from calc)
        >>> # closeness = 1 - (2 / 1.0) = -1.0 -> out of window
        >>> # score = 0.0
    """
    from .constants import get_transit_tier

    tier = get_transit_tier(transit_planet)

    # Safety floor for stationary/retrograde planets
    # 0.05 deg/day ensures stationary planets still register intensity
    # (0.001 was too small - made stationary planets have zero intensity)
    speed = max(abs(transit_speed), 0.05)

    # Calculate dynamic orb limit based on time window
    # Formula: Orb = (Days * Speed) / 2
    # Divide by 2 because window is total (applying + separating)
    dynamic_limit = (tier.window_days * speed) / 2.0

    # Safety clamps to prevent extreme values
    # - Moon at 13 deg/day, 1 day window: 6.5 deg (reasonable)
    # - Pluto at 0.02 deg/day, 100 day window: 1.0 deg (reasonable)
    # - But stationary planet could get ~0, so floor at 0.5
    # - And very fast Mercury could get >10, so cap at 8
    dynamic_limit = max(DYNAMIC_ORB_MIN, min(dynamic_limit, DYNAMIC_ORB_MAX))

    # Calculate days from exact for reporting
    days_from_exact = deviation_deg / speed

    # Outside the dynamic limit = no contribution
    if deviation_deg > dynamic_limit:
        return 0.0, {
            'tier': tier.name,
            'dynamic_limit': dynamic_limit,
            'days_from_exact': days_from_exact,
            'closeness': 0.0,
            'intensity': 0.0,
            'tier_weight': tier.weight,
            'aspect_modifier': ASPECT_MODIFIERS.get(aspect_type, 0.5),
            'score': 0.0,
            'in_window': False,
        }

    # Normalized closeness (0 at limit edge, 1 at exact)
    closeness = 1.0 - (deviation_deg / dynamic_limit)

    # The Spike: squared for sharper peak at exactitude
    intensity = closeness ** 2

    # Get aspect modifier
    aspect_modifier = ASPECT_MODIFIERS.get(aspect_type, 0.5)

    # Final score: intensity * tier weight * aspect modifier
    score = intensity * tier.weight * aspect_modifier

    breakdown = {
        'tier': tier.name,
        'dynamic_limit': dynamic_limit,
        'days_from_exact': days_from_exact,
        'closeness': closeness,
        'intensity': intensity,
        'tier_weight': tier.weight,
        'aspect_modifier': aspect_modifier,
        'score': score,
        'in_window': True,
    }

    return score, breakdown


def calculate_velocity_score_simple(
    transit_planet: Planet,
    deviation_deg: float,
    transit_speed: float,
) -> float:
    """
    Simplified velocity score without aspect type weighting.

    Useful for quick calculations where aspect type is handled separately.

    Returns:
        float: Score from 0 to tier_weight (at exact)
    """
    from .constants import get_transit_tier

    tier = get_transit_tier(transit_planet)
    speed = max(abs(transit_speed), 0.001)

    dynamic_limit = (tier.window_days * speed) / 2.0
    dynamic_limit = max(DYNAMIC_ORB_MIN, min(dynamic_limit, DYNAMIC_ORB_MAX))

    if deviation_deg > dynamic_limit:
        return 0.0

    closeness = 1.0 - (deviation_deg / dynamic_limit)
    intensity = closeness ** 2

    return intensity * tier.weight


def get_tier_contribution_breakdown(
    aspects: list,
) -> dict:
    """
    Break down total score by tier for visualization.

    Args:
        aspects: List of dicts with 'transit_planet', 'score', 'tier'

    Returns:
        dict: {'trigger': X, 'event': Y, 'season': Z, 'era': W, 'total': T}
    """
    from .constants import TRANSIT_TIERS

    breakdown = {tier: 0.0 for tier in TRANSIT_TIERS.keys()}
    breakdown['total'] = 0.0

    for asp in aspects:
        tier = asp.get('tier', 'event')
        score = asp.get('score', 0.0)
        breakdown[tier] += score
        breakdown['total'] += score

    return breakdown


# =============================================================================
# Part 4: Gaussian Mixture Scoring
# =============================================================================
# This approach replaces hard orb cutoffs with smooth Gaussian curves.
#
# Key benefits:
# 1. No hard edges - influence fades asymptotically to zero
# 2. Constructive interference - overlapping aspects sum naturally
# 3. Mathematically elegant - well-understood statistical properties
#
# Formula: f(t) = A * exp(-(t - mu)^2 / (2 * sigma^2))
# Where:
#   t - mu = time to exact (in days)
#   A = tier weight
#   sigma = time_window / 3 (so 99% within window)

# Minimum contribution threshold (skip negligible influences)
GAUSSIAN_MIN_CONTRIBUTION = 0.01

# Sigma divisor: higher = narrower curve = more variation
# 3.0 = 99% within window (standard), 9.0 = optimal for 35-50% variation
# Tested values: 3.0=18%, 5.0=27%, 7.0=33%, 9.0=39%, 12.0=48%
GAUSSIAN_SIGMA_DIVISOR = 9.0


def calculate_gaussian_score(
    transit_planet: Planet,
    deviation_deg: float,
    transit_speed: float,
    aspect_type: AspectType,
) -> Tuple[float, dict]:
    """
    Calculate aspect score using Gaussian (bell curve) decay.

    Instead of a hard cutoff at the orb limit, the influence fades
    smoothly following a Gaussian distribution. This creates:
    - No hard edges (asymptotic fade to zero)
    - Natural constructive interference when aspects overlap
    - Sharper peaks at exactitude than squared closeness

    Formula:
        sigma = window_days / 3  (99% within window)
        deviation_days = deviation_deg / speed
        intensity = exp(-(deviation_days^2) / (2 * sigma^2))
        score = intensity * tier_weight * aspect_modifier

    At 1 sigma (1/3 of window): intensity = 60.7%
    At 2 sigma (2/3 of window): intensity = 13.5%
    At 3 sigma (full window):   intensity = 1.1%

    Args:
        transit_planet: The transiting planet (defines tier)
        deviation_deg: Degrees from exact aspect (orb)
        transit_speed: Transit planet speed in degrees/day
        aspect_type: Type of aspect (for modifier)

    Returns:
        Tuple[float, dict]: (score, breakdown)
            score: The Gaussian-weighted aspect score
            breakdown: Components for debugging/visualization

    Example:
        >>> # Moon at 2 degrees from exact, moving 13 deg/day
        >>> # deviation_days = 2 / 13 = 0.154 days
        >>> # sigma = 1.0 / 3 = 0.333 days
        >>> # intensity = exp(-(0.154^2) / (2 * 0.333^2)) = 0.90
        >>> # score = 0.90 * 10.0 * 1.0 = 9.0
    """
    from .constants import get_transit_tier

    tier = get_transit_tier(transit_planet)

    # Safety floor for stationary/retrograde planets
    # 0.05 deg/day ensures stationary planets still register intensity
    # (0.001 was too small - made stationary planets have zero intensity)
    speed = max(abs(transit_speed), 0.05)

    # Convert deviation from degrees to days
    deviation_days = deviation_deg / speed

    # Calculate sigma: window_days / divisor controls the width
    # Higher divisor = narrower curve = more day-to-day variation
    sigma = tier.window_days / GAUSSIAN_SIGMA_DIVISOR

    # Gaussian intensity: exp(-(t^2) / (2 * sigma^2))
    intensity = math.exp(-(deviation_days ** 2) / (2 * sigma ** 2))

    # Skip negligible contributions (> 3 sigma out)
    if intensity < GAUSSIAN_MIN_CONTRIBUTION:
        return 0.0, {
            'tier': tier.name,
            'sigma': sigma,
            'deviation_days': deviation_days,
            'intensity': intensity,
            'tier_weight': tier.weight,
            'aspect_modifier': ASPECT_MODIFIERS.get(aspect_type, 0.5),
            'score': 0.0,
            'in_window': False,
        }

    # Get aspect modifier
    aspect_modifier = ASPECT_MODIFIERS.get(aspect_type, 0.5)

    # Final score: intensity * tier weight * aspect modifier
    score = intensity * tier.weight * aspect_modifier

    breakdown = {
        'tier': tier.name,
        'sigma': sigma,
        'deviation_days': deviation_days,
        'intensity': intensity,
        'tier_weight': tier.weight,
        'aspect_modifier': aspect_modifier,
        'score': score,
        'in_window': True,
    }

    return score, breakdown


def calculate_gaussian_score_simple(
    transit_planet: Planet,
    deviation_deg: float,
    transit_speed: float,
) -> float:
    """
    Simplified Gaussian score without aspect type weighting.

    Returns:
        float: Score from 0 to tier_weight (at exact)
    """
    from .constants import get_transit_tier

    tier = get_transit_tier(transit_planet)
    speed = max(abs(transit_speed), 0.001)

    deviation_days = deviation_deg / speed
    sigma = tier.window_days / GAUSSIAN_SIGMA_DIVISOR

    intensity = math.exp(-(deviation_days ** 2) / (2 * sigma ** 2))

    if intensity < GAUSSIAN_MIN_CONTRIBUTION:
        return 0.0

    return intensity * tier.weight


def compare_scoring_methods(
    transit_planet: Planet,
    deviation_deg: float,
    transit_speed: float,
    aspect_type: AspectType,
) -> dict:
    """
    Compare velocity (squared closeness) vs Gaussian scoring for same input.

    Useful for understanding the difference between the two approaches.

    Returns:
        dict with 'velocity' and 'gaussian' scores and their breakdowns
    """
    vel_score, vel_breakdown = calculate_velocity_score(
        transit_planet, deviation_deg, transit_speed, aspect_type
    )

    gauss_score, gauss_breakdown = calculate_gaussian_score(
        transit_planet, deviation_deg, transit_speed, aspect_type
    )

    return {
        'velocity': {'score': vel_score, 'breakdown': vel_breakdown},
        'gaussian': {'score': gauss_score, 'breakdown': gauss_breakdown},
        'difference': gauss_score - vel_score,
        'ratio': gauss_score / vel_score if vel_score > 0 else float('inf'),
    }

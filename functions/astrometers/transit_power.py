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
    today_deviation: float = None,
    tomorrow_deviation: float = None,
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

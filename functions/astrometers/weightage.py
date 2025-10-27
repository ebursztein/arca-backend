"""
Weightage Factor (W_i) calculations for astrometers.

Calculates the inherent importance of a natal planet based on:
- Planet base score (Sun/Moon=10, Mercury/Venus/Mars=7, etc.)
- Essential dignity (domicile, exaltation, detriment, fall)
- House position (angular=×3, succedent=×2, cadent=×1)
- Chart ruler bonus (+5 if planet rules Ascendant)
- Personal sensitivity (user-reported, default 1.0)

Formula: W_i = (Planet_Base + Dignity_Score + Ruler_Bonus) × House_Multiplier × Sensitivity_Factor

From spec Section 2.3.A: Weightage Factor
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astro import Planet, ZodiacSign, SIGN_RULERS
from .constants import (
    PLANET_BASE_SCORES,
    get_house_multiplier,
    CHART_RULER_BONUS,
    DEFAULT_SENSITIVITY,
)
from .dignity import calculate_dignity_score


def calculate_weightage(
    planet: Planet,
    sign: ZodiacSign,
    house_number: int,
    ascendant_sign: ZodiacSign | None = None,
    degree_in_sign: float = 0.0,
    sensitivity: float = DEFAULT_SENSITIVITY
) -> float:
    """
    Calculate weightage factor (W_i) for a natal planet.

    Args:
        planet: The natal planet (Planet enum)
        sign: Zodiac sign the planet is in (ZodiacSign enum)
        house_number: House number (1-12)
        ascendant_sign: Ascendant sign for chart ruler calculation (optional)
        degree_in_sign: Degree within sign (0-29.99) for precise dignity (optional)
        sensitivity: Personal sensitivity multiplier (0.5-2.0, default 1.0)

    Returns:
        float: Weightage factor (W_i)

    Example from spec:
        >>> # Natal Sun in Leo (Domicile) in 10th House (Angular), Chart Ruler
        >>> calculate_weightage(
        ...     planet=Planet.SUN,
        ...     sign=ZodiacSign.LEO,
        ...     house_number=10,
        ...     ascendant_sign=ZodiacSign.LEO
        ... )
        60.0  # (10 + 5 + 5) × 3 × 1.0 = 60
    """
    # 1. Planet base score
    planet_base = PLANET_BASE_SCORES[planet]

    # 2. Essential dignity score
    dignity_score = calculate_dignity_score(planet, sign, degree_in_sign)

    # 3. Chart ruler bonus
    ruler_bonus = 0.0
    if ascendant_sign is not None:
        chart_ruler = SIGN_RULERS.get(ascendant_sign)
        if chart_ruler == planet:
            ruler_bonus = CHART_RULER_BONUS

    # 4. House multiplier
    house_multiplier = get_house_multiplier(house_number)

    # 5. Sensitivity factor
    # Note: In a full implementation, this could be user-reported
    # For now, we use the provided value (defaults to 1.0)
    sensitivity_factor = sensitivity

    # Calculate W_i
    weightage = (planet_base + dignity_score + ruler_bonus) * house_multiplier * sensitivity_factor

    return weightage


def calculate_chart_ruler(ascendant_sign: ZodiacSign) -> Planet:
    """
    Determine the chart ruler based on Ascendant sign.

    Args:
        ascendant_sign: The Ascendant (Rising) sign

    Returns:
        Planet: The planet that rules the Ascendant

    Example:
        >>> calculate_chart_ruler(ZodiacSign.LEO)
        <Planet.SUN: 'sun'>
        >>> calculate_chart_ruler(ZodiacSign.SCORPIO)
        <Planet.PLUTO: 'pluto'>  # Modern ruler
    """
    return SIGN_RULERS[ascendant_sign]


def get_weightage_breakdown(
    planet: Planet,
    sign: ZodiacSign,
    house_number: int,
    ascendant_sign: ZodiacSign | None = None,
    degree_in_sign: float = 0.0,
    sensitivity: float = DEFAULT_SENSITIVITY
) -> dict:
    """
    Calculate weightage with detailed breakdown for explainability.

    Returns all intermediate values for debugging and user display.

    Args:
        planet: The natal planet
        sign: Zodiac sign the planet is in
        house_number: House number (1-12)
        ascendant_sign: Ascendant sign (optional)
        degree_in_sign: Degree within sign (optional)
        sensitivity: Personal sensitivity multiplier

    Returns:
        dict: Breakdown with all components
            {
                'weightage': float,
                'planet_base': float,
                'dignity_score': int,
                'ruler_bonus': float,
                'house_multiplier': float,
                'sensitivity_factor': float,
                'is_chart_ruler': bool
            }
    """
    planet_base = PLANET_BASE_SCORES[planet]
    dignity_score = calculate_dignity_score(planet, sign, degree_in_sign)

    is_chart_ruler = False
    ruler_bonus = 0.0
    if ascendant_sign is not None:
        chart_ruler = SIGN_RULERS.get(ascendant_sign)
        if chart_ruler == planet:
            is_chart_ruler = True
            ruler_bonus = CHART_RULER_BONUS

    house_multiplier = get_house_multiplier(house_number)
    sensitivity_factor = sensitivity

    weightage = (planet_base + dignity_score + ruler_bonus) * house_multiplier * sensitivity_factor

    return {
        'weightage': weightage,
        'planet_base': planet_base,
        'dignity_score': dignity_score,
        'ruler_bonus': ruler_bonus,
        'house_multiplier': house_multiplier,
        'sensitivity_factor': sensitivity_factor,
        'is_chart_ruler': is_chart_ruler,
        'house_type': _get_house_type(house_number)
    }


def _get_house_type(house_number: int) -> str:
    """Get house type label (Angular, Succedent, Cadent)."""
    from .constants import ANGULAR_HOUSES, SUCCEDENT_HOUSES, CADENT_HOUSES

    if house_number in ANGULAR_HOUSES:
        return "Angular"
    elif house_number in SUCCEDENT_HOUSES:
        return "Succedent"
    elif house_number in CADENT_HOUSES:
        return "Cadent"
    else:
        return "Unknown"

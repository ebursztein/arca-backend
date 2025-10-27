"""
Essential dignity calculations for astrometers.

Implements planetary dignity scoring based on traditional astrology:
- Domicile: Planet in its ruling sign (+5)
- Exaltation: Planet in its exalted sign (+4)
- Detriment: Planet in opposite of ruling sign (-5)
- Fall: Planet in opposite of exalted sign (-4)
- Peregrine: Planet in neutral position (0)

From spec Section 3.2: Planetary Dignity Scoring
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astro import Planet, ZodiacSign
from .constants import (
    ESSENTIAL_DIGNITIES,
    DIGNITY_DOMICILE,
    DIGNITY_EXALTATION,
    DIGNITY_DETRIMENT,
    DIGNITY_FALL,
    DIGNITY_NEUTRAL,
)


def calculate_dignity_score(
    planet: Planet,
    sign: ZodiacSign,
    degree: float = None
) -> int:
    """
    Calculate essential dignity score for a planet in a sign.

    Args:
        planet: The planet (Planet enum)
        sign: The zodiac sign (ZodiacSign enum)
        degree: Optional degree within sign (0-29.99) for exact exaltation/fall

    Returns:
        int: Dignity score
            +5 for domicile
            +4 for exaltation (if degree matches)
            -5 for detriment
            -4 for fall (if degree matches)
             0 for peregrine (neutral)

    Examples:
        >>> calculate_dignity_score(Planet.SUN, ZodiacSign.LEO)
        5  # Sun in domicile
        >>> calculate_dignity_score(Planet.SUN, ZodiacSign.ARIES, degree=19)
        4  # Sun exalted at 19° Aries
        >>> calculate_dignity_score(Planet.SUN, ZodiacSign.AQUARIUS)
        -5  # Sun in detriment
        >>> calculate_dignity_score(Planet.SUN, ZodiacSign.GEMINI)
        0  # Sun peregrine (neutral)
    """
    dignities = ESSENTIAL_DIGNITIES.get(planet)

    if not dignities:
        # Outer planets (Uranus, Neptune, Pluto) have no traditional dignities
        return DIGNITY_NEUTRAL

    assert isinstance(dignities, dict)

    # Check domicile
    if sign in dignities["domicile"]:
        return DIGNITY_DOMICILE

    # Check detriment
    if sign in dignities["detriment"]:
        return DIGNITY_DETRIMENT

    # Check exaltation (requires degree match for precision)
    for exalt_sign, exalt_degree in dignities["exaltation"]:
        if sign == exalt_sign:
            # If no degree provided, give benefit of the doubt
            if degree is None:
                return DIGNITY_EXALTATION

            # Check if within orb of exact exaltation degree
            # Using ±5° orb for exaltation (common traditional practice)
            degree_diff = abs(degree - exalt_degree)
            if degree_diff <= 5.0 or degree_diff >= (30.0 - 5.0):
                return DIGNITY_EXALTATION

            # In exaltation sign but not at exaltation degree
            # Some traditions give partial credit, we'll be neutral
            return DIGNITY_NEUTRAL

    # Check fall (requires degree match for precision)
    for fall_sign, fall_degree in dignities["fall"]:
        if sign == fall_sign:
            # If no degree provided, give "benefit of the doubt" as fall
            if degree is None:
                return DIGNITY_FALL

            # Check if within orb of exact fall degree
            degree_diff = abs(degree - fall_degree)
            if degree_diff <= 5.0 or degree_diff >= (30.0 - 5.0):
                return DIGNITY_FALL

            # In fall sign but not at fall degree
            return DIGNITY_NEUTRAL

    # Peregrine: neither in dignity nor debility
    return DIGNITY_NEUTRAL


def get_dignity_label(dignity_score: int) -> str:
    """
    Get human-readable label for a dignity score.

    Args:
        dignity_score: Dignity score (-5 to +5)

    Returns:
        str: Label (Domicile, Exaltation, Neutral, Detriment, Fall)
    """
    if dignity_score == DIGNITY_DOMICILE:
        return "Domicile"
    elif dignity_score == DIGNITY_EXALTATION:
        return "Exaltation"
    elif dignity_score == DIGNITY_DETRIMENT:
        return "Detriment"
    elif dignity_score == DIGNITY_FALL:
        return "Fall"
    else:
        return "Neutral (Peregrine)"


def is_in_dignity(planet: Planet, sign: ZodiacSign) -> bool:
    """
    Check if a planet is in a position of strength (domicile or exaltation).

    Args:
        planet: The planet
        sign: The zodiac sign

    Returns:
        bool: True if in domicile or exaltation
    """
    score = calculate_dignity_score(planet, sign)
    return score > 0


def is_in_debility(planet: Planet, sign: ZodiacSign) -> bool:
    """
    Check if a planet is in a position of weakness (detriment or fall).

    Args:
        planet: The planet
        sign: The zodiac sign

    Returns:
        bool: True if in detriment or fall
    """
    score = calculate_dignity_score(planet, sign)
    return score < 0

"""
Quality Factor (Q_i) calculations for astrometers.

Determines the harmonic nature of aspects:
- Harmonious aspects (trine, sextile): +1.0
- Challenging aspects (square, opposition): -1.0
- Conjunctions: Dynamic based on planet combinations

Formula:
HQS = Σ(W_i × P_i × Q_i)

From spec Section 2.3.C (Quality Factor)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astro import Planet, AspectType
from .constants import (
    QUALITY_TRINE,
    QUALITY_SEXTILE,
    QUALITY_SQUARE,
    QUALITY_OPPOSITION,
    BENEFIC_PLANETS,
    MALEFIC_PLANETS,
    TRANSFORMATIONAL_PLANETS,
    CONJUNCTION_DOUBLE_BENEFIC,
    CONJUNCTION_DOUBLE_MALEFIC,
    CONJUNCTION_BENEFIC_MALEFIC,
    CONJUNCTION_TRANSFORMATIONAL,
    CONJUNCTION_DEFAULT,
    QUALITY_BLISSFUL_THRESHOLD,
    QUALITY_VERY_HARMONIOUS_THRESHOLD,
    QUALITY_HARMONIOUS_THRESHOLD,
    QUALITY_NEUTRAL_THRESHOLD,
    QUALITY_CHALLENGING_THRESHOLD,
    QUALITY_VERY_CHALLENGING_THRESHOLD,
)


def calculate_quality_factor(
    aspect_type: AspectType,
    natal_planet: Planet,
    transit_planet: Planet
) -> float:
    """
    Calculate the quality factor for an aspect.

    Fixed values for non-conjunction aspects:
    - Trine: +1.0 (flow, ease, natural talent expression)
    - Sextile: +1.0 (opportunity, requires some initiative)
    - Square: -1.0 (friction, growth through challenge)
    - Opposition: -1.0 (tension, awareness through polarity)

    Dynamic values for conjunctions based on planet natures:
    - Double benefic (Venus/Jupiter): +0.8 (harmonious)
    - Double malefic (Mars/Saturn): -0.8 (intensely challenging)
    - Benefic + Malefic: +0.2 (mitigating influence)
    - Transformational planet (Uranus/Neptune/Pluto): -0.3 (slight tension)
    - Default (luminaries, Mercury): 0.0 (neutral)

    Args:
        aspect_type: Type of aspect
        natal_planet: The natal planet
        transit_planet: The transiting planet

    Returns:
        float: Quality factor (-1.0 to +1.0)

    Examples:
        >>> calculate_quality_factor(AspectType.TRINE, Planet.SUN, Planet.JUPITER)
        1.0
        >>> calculate_quality_factor(AspectType.SQUARE, Planet.MOON, Planet.SATURN)
        -1.0
        >>> calculate_quality_factor(AspectType.CONJUNCTION, Planet.VENUS, Planet.JUPITER)
        0.8  # Double benefic
    """
    # Fixed quality scores for non-conjunction aspects
    if aspect_type == AspectType.TRINE:
        return QUALITY_TRINE
    elif aspect_type == AspectType.SEXTILE:
        return QUALITY_SEXTILE
    elif aspect_type == AspectType.SQUARE:
        return QUALITY_SQUARE
    elif aspect_type == AspectType.OPPOSITION:
        return QUALITY_OPPOSITION

    # Dynamic conjunction quality based on planet combination
    elif aspect_type == AspectType.CONJUNCTION:
        return _calculate_conjunction_quality(natal_planet, transit_planet)

    else:
        raise ValueError(f"Unknown aspect type: {aspect_type}")


def _calculate_conjunction_quality(planet1: Planet, planet2: Planet) -> float:
    """
    Calculate quality factor for conjunctions based on planet natures.

    Order doesn't matter (Venus-Jupiter = Jupiter-Venus).

    Args:
        planet1: First planet in conjunction
        planet2: Second planet in conjunction

    Returns:
        float: Conjunction quality (-0.8 to +0.8)
    """
    # Check if either planet is transformational (takes precedence)
    if planet1 in TRANSFORMATIONAL_PLANETS or planet2 in TRANSFORMATIONAL_PLANETS:
        return CONJUNCTION_TRANSFORMATIONAL

    # Both planets are benefics
    if planet1 in BENEFIC_PLANETS and planet2 in BENEFIC_PLANETS:
        return CONJUNCTION_DOUBLE_BENEFIC

    # Both planets are malefics
    if planet1 in MALEFIC_PLANETS and planet2 in MALEFIC_PLANETS:
        return CONJUNCTION_DOUBLE_MALEFIC

    # One benefic, one malefic (balancing)
    is_benefic_malefic = (
        (planet1 in BENEFIC_PLANETS and planet2 in MALEFIC_PLANETS) or
        (planet1 in MALEFIC_PLANETS and planet2 in BENEFIC_PLANETS)
    )
    if is_benefic_malefic:
        return CONJUNCTION_BENEFIC_MALEFIC

    # Default: Luminaries (Sun/Moon), Mercury, or any other combination
    return CONJUNCTION_DEFAULT


def get_quality_label(quality: float) -> str:
    """
    Get human-readable label for quality factor.

    Args:
        quality: Quality factor (-1.0 to +1.0)

    Returns:
        str: Quality label

    Examples:
        >>> get_quality_label(1.0)
        'Blissful'
        >>> get_quality_label(0.8)
        'Very Harmonious'
        >>> get_quality_label(0.2)
        'Harmonious'
        >>> get_quality_label(0.0)
        'Neutral'
        >>> get_quality_label(-0.3)
        'Neutral'
        >>> get_quality_label(-0.8)
        'Challenging'
        >>> get_quality_label(-1.0)
        'Very Challenging'
    """
    if quality >= QUALITY_BLISSFUL_THRESHOLD:
        return "Blissful"
    elif quality >= QUALITY_VERY_HARMONIOUS_THRESHOLD:
        return "Very Harmonious"
    elif quality >= QUALITY_HARMONIOUS_THRESHOLD:
        return "Harmonious"
    elif quality >= QUALITY_NEUTRAL_THRESHOLD:
        return "Neutral"
    elif quality >= QUALITY_CHALLENGING_THRESHOLD:
        return "Challenging"
    elif quality >= QUALITY_VERY_CHALLENGING_THRESHOLD:
        return "Very Challenging"
    else:
        return "Extremely Challenging"

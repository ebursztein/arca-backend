"""
Core DTI and HQS calculations for astrometers.

DTI (Dual Transit Influence): Σ(W_i × P_i)
- Measures total magnitude of astrological activity

HQS (Harmonic Quality Score): Σ(W_i × P_i × Q_i)
- Measures supportive vs challenging nature

From spec Section 2.1-2.2 (Core Formulas)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from astro import Planet, AspectType, ZodiacSign
from .weightage import calculate_weightage
from .transit_power import calculate_transit_power_complete
from .quality import calculate_quality_factor


@dataclass
class TransitAspect:
    """
    Represents a single transit aspect for DTI/HQS calculation.

    Contains all information needed to calculate W_i, P_i, and Q_i.
    """
    # Required fields first
    # Natal planet information (for W_i)
    natal_planet: Planet
    natal_sign: ZodiacSign
    natal_house: int

    # Transit planet information (for P_i and Q_i)
    transit_planet: Planet
    aspect_type: AspectType
    orb_deviation: float
    max_orb: float

    # Optional fields after required fields
    natal_degree_in_sign: Optional[float] = None
    ascendant_sign: Optional[ZodiacSign] = None
    sensitivity: float = 1.0

    # Direction/station modifiers (for P_i)
    today_deviation: Optional[float] = None
    tomorrow_deviation: Optional[float] = None
    days_from_station: Optional[int] = None

    # Optional metadata
    label: Optional[str] = None  # e.g., "Transit Saturn square Natal Sun"


@dataclass
class AspectContribution:
    """Breakdown of a single aspect's contribution to DTI and HQS."""
    label: str
    natal_planet: Planet
    transit_planet: Planet
    aspect_type: AspectType
    weightage: float
    transit_power: float
    quality_factor: float
    dti_contribution: float  # W_i × P_i
    hqs_contribution: float  # W_i × P_i × Q_i


@dataclass
class AstrometerScore:
    """Complete DTI and HQS scores with detailed breakdowns."""
    dti: float  # Total Dual Transit Influence
    hqs: float  # Total Harmonic Quality Score
    aspect_count: int
    contributions: List[AspectContribution]


def calculate_aspect_contribution(aspect: TransitAspect) -> AspectContribution:
    """
    Calculate DTI and HQS contribution for a single transit aspect.

    Formula:
    - W_i = (Planet_Base + Dignity + Ruler_Bonus) × House_Mult × Sensitivity
    - P_i = Aspect_Base × Orb_Factor × Direction_Mod × Station_Mod × Transit_Weight
    - Q_i = Quality Factor (aspect-dependent)
    - DTI contribution = W_i × P_i
    - HQS contribution = W_i × P_i × Q_i

    Args:
        aspect: TransitAspect with all necessary data

    Returns:
        AspectContribution with detailed breakdown

    Example:
        >>> # Transit Saturn square Natal Sun (from spec Section 6.2)
        >>> aspect = TransitAspect(
        ...     natal_planet=Planet.SUN,
        ...     natal_sign=ZodiacSign.LEO,
        ...     natal_house=10,
        ...     transit_planet=Planet.SATURN,
        ...     aspect_type=AspectType.SQUARE,
        ...     orb_deviation=2.25,
        ...     max_orb=8.0,
        ...     today_deviation=2.25,
        ...     tomorrow_deviation=2.0,
        ...     label="Transit Saturn square Natal Sun"
        ... )
        >>> contrib = calculate_aspect_contribution(aspect)
        >>> # W_i = (10 + 5) × 3 × 1.0 = 45
        >>> # P_i = 8 × 0.75 × 1.3 × 1.0 × 1.2 = 9.36
        >>> # Q_i = -1.0
        >>> # DTI = 45 × 9.36 = 421.2
        >>> # HQS = 421.2 × (-1.0) = -421.2
    """
    # Calculate W_i (Weightage Factor)
    weightage = calculate_weightage(
        planet=aspect.natal_planet,
        sign=aspect.natal_sign,
        house_number=aspect.natal_house,
        degree_in_sign=aspect.natal_degree_in_sign,
        ascendant_sign=aspect.ascendant_sign,
        sensitivity=aspect.sensitivity
    )

    # Calculate P_i (Transit Power)
    transit_power, _ = calculate_transit_power_complete(
        aspect_type=aspect.aspect_type,
        orb_deviation=aspect.orb_deviation,
        max_orb=aspect.max_orb,
        transit_planet=aspect.transit_planet,
        today_deviation=aspect.today_deviation,
        tomorrow_deviation=aspect.tomorrow_deviation,
        days_from_station=aspect.days_from_station
    )

    # Calculate Q_i (Quality Factor)
    quality_factor = calculate_quality_factor(
        aspect_type=aspect.aspect_type,
        natal_planet=aspect.natal_planet,
        transit_planet=aspect.transit_planet
    )

    # Calculate contributions
    dti_contribution = weightage * transit_power
    hqs_contribution = weightage * transit_power * quality_factor

    # Create label if not provided
    label = aspect.label or f"Transit {aspect.transit_planet.value} {aspect.aspect_type.value} Natal {aspect.natal_planet.value}"

    return AspectContribution(
        label=label,
        natal_planet=aspect.natal_planet,
        transit_planet=aspect.transit_planet,
        aspect_type=aspect.aspect_type,
        weightage=weightage,
        transit_power=transit_power,
        quality_factor=quality_factor,
        dti_contribution=dti_contribution,
        hqs_contribution=hqs_contribution
    )


def calculate_astrometers(aspects: List[TransitAspect]) -> AstrometerScore:
    """
    Calculate DTI and HQS scores from a list of transit aspects.

    This is the main entry point for the astrometer calculation system.

    Formula:
    - DTI = Σ(W_i × P_i)  [sum of all weighted transit powers]
    - HQS = Σ(W_i × P_i × Q_i)  [sum with quality modifiers]

    Args:
        aspects: List of TransitAspect objects representing all active transits

    Returns:
        AstrometerScore with total DTI, HQS, and detailed breakdowns

    Example from spec Section 6.2:
        >>> aspects = [
        ...     TransitAspect(  # Saturn square Sun
        ...         natal_planet=Planet.SUN, natal_sign=ZodiacSign.LEO,
        ...         natal_house=10, transit_planet=Planet.SATURN,
        ...         aspect_type=AspectType.SQUARE, orb_deviation=2.25, max_orb=8.0,
        ...         today_deviation=2.25, tomorrow_deviation=2.0
        ...     ),
        ...     TransitAspect(  # Jupiter trine Venus
        ...         natal_planet=Planet.VENUS, natal_sign=ZodiacSign.TAURUS,
        ...         natal_house=5, transit_planet=Planet.JUPITER,
        ...         aspect_type=AspectType.TRINE, orb_deviation=1.0, max_orb=7.0,
        ...         today_deviation=1.0, tomorrow_deviation=0.8
        ...     )
        ... ]
        >>> score = calculate_astrometers(aspects)
        >>> # DTI = 421.2 + 197.5 = 618.7 (approximately)
        >>> # HQS = -421.2 + 197.5 = -223.7 (approximately)
    """
    if not aspects:
        return AstrometerScore(
            dti=0.0,
            hqs=0.0,
            aspect_count=0,
            contributions=[]
        )

    # Calculate contribution for each aspect
    contributions = [calculate_aspect_contribution(aspect) for aspect in aspects]

    # Sum up DTI and HQS
    total_dti = sum(c.dti_contribution for c in contributions)
    total_hqs = sum(c.hqs_contribution for c in contributions)

    return AstrometerScore(
        dti=total_dti,
        hqs=total_hqs,
        aspect_count=len(contributions),
        contributions=contributions
    )


def get_score_breakdown_text(score: AstrometerScore) -> str:
    """
    Generate human-readable breakdown text for debugging/display.

    Args:
        score: AstrometerScore with calculations

    Returns:
        str: Formatted breakdown text
    """
    lines = []
    lines.append(f"Total DTI: {score.dti:.2f}")
    lines.append(f"Total HQS: {score.hqs:.2f}")
    lines.append(f"Active Aspects: {score.aspect_count}")
    lines.append("")
    lines.append("Aspect Contributions:")
    lines.append("=" * 60)

    for i, contrib in enumerate(score.contributions, 1):
        lines.append(f"\n{i}. {contrib.label}")
        lines.append(f"   W_i = {contrib.weightage:.2f}")
        lines.append(f"   P_i = {contrib.transit_power:.2f}")
        lines.append(f"   Q_i = {contrib.quality_factor:.2f}")
        lines.append(f"   DTI contribution: {contrib.dti_contribution:.2f}")
        lines.append(f"   HQS contribution: {contrib.hqs_contribution:.2f}")

    return "\n".join(lines)

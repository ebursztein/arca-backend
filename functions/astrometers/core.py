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
    """
    Breakdown of a single aspect's contribution to DTI and HQS.

    Includes full explainability data for iOS client.
    """
    # Basic aspect info
    label: str
    natal_planet: Planet
    transit_planet: Planet
    aspect_type: AspectType

    # Calculation components
    weightage: float  # W_i
    transit_power: float  # P_i
    quality_factor: float  # Q_i (-1 to +1)
    dti_contribution: float  # W_i × P_i
    hqs_contribution: float  # W_i × P_i × Q_i

    # Explainability - strength indicators (for iOS)
    orb_deviation: float = 0.0  # Exact orb in degrees
    max_orb: float = 6.0  # Maximum orb for this aspect type

    # Explainability - phase/timing (for iOS)
    today_deviation: Optional[float] = None  # Today's orb
    tomorrow_deviation: Optional[float] = None  # Tomorrow's orb (for phase calculation)

    # Explainability - context (for iOS)
    natal_planet_house: int = 1  # House containing natal planet
    natal_planet_sign: ZodiacSign = ZodiacSign.ARIES  # Sign of natal planet


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
        degree_in_sign=aspect.natal_degree_in_sign or 0.0,
        ascendant_sign=aspect.ascendant_sign,
        sensitivity=aspect.sensitivity
    )

    # Calculate P_i (Transit Power)
    transit_power, _ = calculate_transit_power_complete(
        aspect_type=aspect.aspect_type,
        orb_deviation=aspect.orb_deviation,
        max_orb=aspect.max_orb,
        transit_planet=aspect.transit_planet,
        today_deviation=aspect.today_deviation or 0.0,
        tomorrow_deviation=aspect.tomorrow_deviation or 0.0,
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
        hqs_contribution=hqs_contribution,
        # Explainability fields
        orb_deviation=aspect.orb_deviation,
        max_orb=aspect.max_orb,
        today_deviation=aspect.today_deviation,
        tomorrow_deviation=aspect.tomorrow_deviation,
        natal_planet_house=aspect.natal_house,
        natal_planet_sign=aspect.natal_sign
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


def calculate_all_aspects(natal_chart: dict, transit_chart: dict, orb: float = 8.0) -> List[TransitAspect]:
    """
    Calculate all natal-transit aspects.

    Wraps astro.find_natal_transit_aspects() and converts to TransitAspect format.

    Args:
        natal_chart: Natal chart dict
        transit_chart: Transit chart dict
        orb: Maximum orb in degrees (default 8.0 for astrometers)

    Returns:
        List of TransitAspect objects for DTI/HQS calculation
    """
    from astro import find_natal_transit_aspects, Planet, ZodiacSign

    # Get aspects from astro.py
    natal_transit_aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=orb)

    # Convert to TransitAspect format
    transit_aspects = []
    ascendant_sign = None
    if "angles" in natal_chart and "asc" in natal_chart["angles"]:
        ascendant_sign = ZodiacSign(natal_chart["angles"]["asc"]["sign"])

    for nta in natal_transit_aspects:
        # Get natal planet info from chart
        natal_planet_info = next((p for p in natal_chart["planets"] if p["name"] == nta.natal_planet), None)
        if not natal_planet_info:
            continue

        transit_aspect = TransitAspect(
            natal_planet=Planet(nta.natal_planet),
            natal_sign=ZodiacSign(nta.natal_sign),
            natal_house=nta.natal_house,
            transit_planet=Planet(nta.transit_planet),
            aspect_type=nta.aspect_type,
            orb_deviation=nta.orb,
            max_orb=orb,
            natal_degree_in_sign=natal_planet_info.get("signed_deg", 0),
            ascendant_sign=ascendant_sign,
            today_deviation=nta.orb,  # Simplified - no tomorrow data yet
            tomorrow_deviation=None,
            days_from_station=None,
            label=f"Transit {nta.transit_planet} {nta.aspect_type.value} Natal {nta.natal_planet}"
        )
        transit_aspects.append(transit_aspect)

    return transit_aspects


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

"""
Core DTI and HQS calculations for astrometers.

V1 (Legacy):
- DTI (Dual Transit Influence): Σ(W_i × P_i)
- HQS (Harmonic Quality Score): Σ(W_i × P_i × Q_i)
- Problem: DTI and HQS are coupled (share W_i × P_i)

V2 (Decoupled - December 2025):
- Intensity = Σ(Power) where Power = W_i × Gaussian_Score
- Harmony = Σ(Power × Polarity) / (Intensity + Ballast)
- Intensity is magnitude (volume), Harmony is polarity (sign)
- Ballast prevents instability at low intensity

From spec Section 2.1-2.2 (Core Formulas) and ASTROMETERS_V2.md
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from astro import Planet, AspectType, ZodiacSign
from .weightage import calculate_weightage
from .transit_power import calculate_transit_power_complete, calculate_gaussian_score
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

    # V2: Transit speed for Gaussian scoring (degrees/day)
    transit_speed: Optional[float] = None

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

    # V1 Calculation components (legacy)
    weightage: float  # W_i
    transit_power: float  # P_i
    quality_factor: float  # Q_i (-1 to +1)
    dti_contribution: float  # W_i × P_i
    hqs_contribution: float  # W_i × P_i × Q_i

    # V2 Calculation components (decoupled)
    gaussian_power: float = 0.0  # W_i × Gaussian_Score (velocity-based)
    polarity: float = 0.0  # -1 to +1 (aspect quality sign)

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
    # V1 (legacy) - coupled scores
    dti: float  # Total Dual Transit Influence
    hqs: float  # Total Harmonic Quality Score

    # V2 (decoupled) - intensity and harmony
    intensity: float = 0.0  # Σ(Power) - magnitude/volume
    harmony_coefficient: float = 0.0  # -1.0 to +1.0 - polarity/sign

    aspect_count: int = 0
    contributions: List[AspectContribution] = field(default_factory=list)


def calculate_aspect_contribution(aspect: TransitAspect) -> AspectContribution:
    """
    Calculate DTI and HQS contribution for a single transit aspect.

    V1 Formula (legacy):
    - W_i = (Planet_Base + Dignity + Ruler_Bonus) × House_Mult × Sensitivity
    - P_i = Aspect_Base × Orb_Factor × Direction_Mod × Station_Mod × Transit_Weight
    - Q_i = Quality Factor (aspect-dependent)
    - DTI contribution = W_i × P_i
    - HQS contribution = W_i × P_i × Q_i

    V2 Formula (decoupled):
    - Gaussian_Score = velocity-based power (tier_weight × gaussian_intensity)
    - Power = W_i × Gaussian_Score
    - Polarity = Q_i (quality factor, -1 to +1)

    Args:
        aspect: TransitAspect with all necessary data

    Returns:
        AspectContribution with detailed breakdown (both V1 and V2 fields)
    """
    # Calculate W_i (Weightage Factor) - used by both V1 and V2
    weightage = calculate_weightage(
        planet=aspect.natal_planet,
        sign=aspect.natal_sign,
        house_number=aspect.natal_house,
        degree_in_sign=aspect.natal_degree_in_sign or 0.0,
        ascendant_sign=aspect.ascendant_sign,
        sensitivity=aspect.sensitivity
    )

    # V1: Calculate P_i (Transit Power) - static orb-based
    transit_power, _ = calculate_transit_power_complete(
        aspect_type=aspect.aspect_type,
        orb_deviation=aspect.orb_deviation,
        max_orb=aspect.max_orb,
        transit_planet=aspect.transit_planet,
        today_deviation=aspect.today_deviation or 0.0,
        tomorrow_deviation=aspect.tomorrow_deviation or 0.0,
        days_from_station=aspect.days_from_station
    )

    # Calculate Q_i (Quality Factor) - used by both V1 and V2
    quality_factor = calculate_quality_factor(
        aspect_type=aspect.aspect_type,
        natal_planet=aspect.natal_planet,
        transit_planet=aspect.transit_planet
    )

    # V1: Calculate contributions (legacy)
    dti_contribution = weightage * transit_power
    hqs_contribution = weightage * transit_power * quality_factor

    # V2: Calculate Gaussian power (velocity-based)
    gaussian_power = 0.0
    if aspect.transit_speed is not None:
        gaussian_score, _ = calculate_gaussian_score(
            transit_planet=aspect.transit_planet,
            deviation_deg=aspect.orb_deviation,
            transit_speed=aspect.transit_speed,
            aspect_type=aspect.aspect_type,
        )
        # Power = W_i × Gaussian_Score (personalized by natal chart)
        gaussian_power = weightage * gaussian_score

    # V2: Polarity is just the quality factor (-1 to +1)
    polarity = quality_factor

    # Create label if not provided
    label = aspect.label or f"Transit {aspect.transit_planet.value} {aspect.aspect_type.value} Natal {aspect.natal_planet.value}"

    return AspectContribution(
        label=label,
        natal_planet=aspect.natal_planet,
        transit_planet=aspect.transit_planet,
        aspect_type=aspect.aspect_type,
        # V1 components
        weightage=weightage,
        transit_power=transit_power,
        quality_factor=quality_factor,
        dti_contribution=dti_contribution,
        hqs_contribution=hqs_contribution,
        # V2 components
        gaussian_power=gaussian_power,
        polarity=polarity,
        # Explainability fields
        orb_deviation=aspect.orb_deviation,
        max_orb=aspect.max_orb,
        today_deviation=aspect.today_deviation,
        tomorrow_deviation=aspect.tomorrow_deviation,
        natal_planet_house=aspect.natal_house,
        natal_planet_sign=aspect.natal_sign
    )


# Default ballast value (noise floor for harmony calculation)
# Prevents instability at low intensity - a quiet day with one weak aspect
# shouldn't register as "pure euphoria" or "pure hell"
DEFAULT_BALLAST = 10.0

# Per-meter ballast values derived from calibration data
# Formula: Ballast = Median Intensity (P50) / 2
# This ensures the ballast is proportional to typical meter activity
# Meters with only fast planets (Mercury, Moon, Venus) have lower median intensity
# and need lower ballast to let their harmony signal through
METER_BALLAST = {
    "ambition": 10.9,
    "circle": 7.2,
    "clarity": 8.5,
    "communication": 3.9,  # Only Mercury - needs low ballast
    "connections": 8.6,
    "creativity": 4.8,
    "drive": 14.7,
    "energy": 6.4,
    "evolution": 9.6,
    "flow": 2.1,           # Low intensity meter
    "focus": 5.2,          # Only Mercury
    "intuition": 9.3,
    "momentum": 7.9,
    "resilience": 2.5,     # Only Moon - needs low ballast
    "strength": 10.5,
    "vision": 16.6,
    "vulnerability": 5.1,
}


def get_ballast_for_meter(meter_name: Optional[str] = None) -> float:
    """Get the appropriate ballast value for a meter.

    Args:
        meter_name: Name of the meter, or None for default

    Returns:
        Calibration-derived ballast for the meter, or DEFAULT_BALLAST if not found
    """
    if meter_name is None:
        return DEFAULT_BALLAST
    return METER_BALLAST.get(meter_name, DEFAULT_BALLAST)


def get_cosmic_background(natal_chart_hash: int, date_ordinal: int, meter_name: str = "") -> tuple[float, float]:
    """
    Simulates the 'Cosmic Background' - aggregate hum of minor astrological influences
    (asteroids, fixed stars, minor aspects, midpoints) that we don't explicitly model.

    This prevents dead-flat neutral days by adding deterministic "dithering" noise.

    Args:
        natal_chart_hash: Hash of the natal chart (for per-person variation)
        date_ordinal: Date as ordinal (date.toordinal()) for per-day variation
        meter_name: Name of meter (for per-meter variation)

    Returns:
        Tuple of (intensity, polarity) where:
        - intensity: 1.0-3.0 (small, won't overpower sensitive meters like 'flow' P50=4.2)
        - polarity: -0.4 to +0.4 (mild bias, never radical)
    """
    import random

    # Create LOCAL deterministic generator (don't pollute global random state)
    # Combining chart hash + date + meter ensures:
    # - Same person + same day + same meter = Same background (Deterministic)
    # - Different person or day or meter = Different background
    seed_value = natal_chart_hash + date_ordinal + hash(meter_name) % 10000
    rng = random.Random(seed_value)

    # Intensity: The "Hum" (1.0-3.0 range)
    # Kept low to not overpower sensitive meters
    intensity = 1.0 + (rng.random() * 2.0)

    # Polarity: The "Drift" (-0.4 to +0.4)
    # Avoid +/- 1.0 to ensure background is never "radical"
    polarity = rng.uniform(-0.4, 0.4)

    return intensity, polarity


def get_cosmic_dither(natal_chart_hash: int, date_ordinal: int, meter_name: str = "") -> float:
    """
    Get deterministic dither value to apply directly to unified score.

    This prevents the exact-50 spike by nudging neutral days slightly positive or negative.

    Args:
        natal_chart_hash: Hash of the natal chart (for per-person variation)
        date_ordinal: Date as ordinal (date.toordinal()) for per-day variation
        meter_name: Name of meter (for per-meter variation)

    Returns:
        Dither value in range -5 to +5 (applied to unified score before post-sigmoid)
    """
    import random

    # Create LOCAL deterministic generator
    seed_value = natal_chart_hash + date_ordinal + hash(meter_name) % 10000
    rng = random.Random(seed_value)

    # Dither: -8 to +8 range (will be scaled by proximity to neutral)
    # Applied to raw_unified before post-sigmoid stretch
    return rng.uniform(-8.0, 8.0)


def calculate_astrometers(
    aspects: List[TransitAspect],
    ballast: float = DEFAULT_BALLAST,
    meter_name: Optional[str] = None,
    natal_chart_hash: Optional[int] = None,
    date_ordinal: Optional[int] = None,
) -> AstrometerScore:
    """
    Calculate DTI and HQS scores from a list of transit aspects.

    This is the main entry point for the astrometer calculation system.

    V1 Formula (legacy - coupled):
    - DTI = Σ(W_i × P_i)  [sum of all weighted transit powers]
    - HQS = Σ(W_i × P_i × Q_i)  [sum with quality modifiers]

    V2 Formula (decoupled):
    - Intensity = Σ(Power) where Power = W_i × Gaussian_Score
    - Harmony = Σ(Power × Polarity) / (Intensity + Ballast)
    - Intensity is magnitude (0 to ~100+), Harmony is polarity (-1 to +1)

    Args:
        aspects: List of TransitAspect objects representing all active transits
        ballast: Noise floor for harmony calculation (default: 10.0)

    Returns:
        AstrometerScore with both V1 (dti/hqs) and V2 (intensity/harmony_coefficient)
    """
    if not aspects:
        return AstrometerScore(
            dti=0.0,
            hqs=0.0,
            intensity=0.0,
            harmony_coefficient=0.0,
            aspect_count=0,
            contributions=[]
        )

    # Calculate contribution for each aspect
    contributions = [calculate_aspect_contribution(aspect) for aspect in aspects]

    # V1: Sum up DTI and HQS (legacy)
    total_dti = sum(c.dti_contribution for c in contributions)
    total_hqs = sum(c.hqs_contribution for c in contributions)

    # V2: Calculate decoupled Intensity and Harmony
    total_intensity = sum(c.gaussian_power for c in contributions)
    net_quality_sum = sum(c.gaussian_power * c.polarity for c in contributions)

    # Add Cosmic Background ("Dithering") to prevent dead-flat neutral days
    # This simulates the aggregate hum of minor influences we don't model
    if natal_chart_hash is not None and date_ordinal is not None:
        bg_intensity, bg_polarity = get_cosmic_background(natal_chart_hash, date_ordinal)
        total_intensity += bg_intensity
        net_quality_sum += bg_intensity * bg_polarity

    # Use meter-specific ballast if meter_name provided, otherwise use passed ballast
    effective_ballast = get_ballast_for_meter(meter_name) if meter_name else ballast

    # Harmony coefficient: -1.0 to +1.0
    # Ballast prevents instability at low intensity
    if total_intensity > 0:
        harmony_coefficient = net_quality_sum / (total_intensity + effective_ballast)
    else:
        harmony_coefficient = 0.0

    return AstrometerScore(
        dti=total_dti,
        hqs=total_hqs,
        intensity=total_intensity,
        harmony_coefficient=harmony_coefficient,
        aspect_count=len(contributions),
        contributions=contributions
    )


def _get_planet_speed(chart: dict, planet_name: str) -> float:
    """
    Extract planet speed from chart data.

    Args:
        chart: Chart dict with 'planets' list
        planet_name: Planet name (e.g., 'moon', 'saturn')

    Returns:
        Absolute speed in degrees/day (defaults to 1.0 if not found)
    """
    for p in chart.get('planets', []):
        if p['name'].lower() == planet_name.lower():
            return abs(p.get('speed', 1.0))
    return 1.0  # Default fallback


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

        # V2: Get transit planet speed for Gaussian scoring
        transit_speed = _get_planet_speed(transit_chart, nta.transit_planet)

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
            transit_speed=transit_speed,  # V2: for Gaussian scoring
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

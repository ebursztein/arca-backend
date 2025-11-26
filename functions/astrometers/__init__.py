"""
Astrometers: Quantitative astrological analysis system.

Implements the dual-metric scoring system (DTI and HQS) for measuring
the intensity and quality of astrological transits.
"""

# Import only what exists (will expand as we implement more modules)
from .dignity import calculate_dignity_score
from .weightage import calculate_weightage, calculate_chart_ruler, get_weightage_breakdown
from .transit_power import (
    calculate_angular_separation,
    detect_aspect,
    calculate_orb_factor,
    calculate_transit_power_basic,
    get_aspect_strength_label,
    get_direction_modifier,
    calculate_station_modifier,
    calculate_transit_power_complete,
    get_aspect_direction_status,
)
from .quality import calculate_quality_factor, get_quality_label
from .core import (
    TransitAspect,
    AspectContribution,
    AstrometerScore,
    calculate_aspect_contribution,
    calculate_astrometers,
    get_score_breakdown_text,
)
from .normalization import (
    MeterInterpretation,
    normalize_with_soft_ceiling,
    normalize_intensity,
    normalize_harmony,
    normalize_meters,
    get_intensity_label,
    get_harmony_label,
    get_meter_interpretation,
)
# Import new 17-meter system
from .meters import (
    MeterReading,
    AllMetersReading,
    get_meters,
    METER_CONFIGS,
)
from .summary import daily_meters_summary


def get_meter_list(all_meters: AllMetersReading) -> list:
    """
    Extract all 17 meters from AllMetersReading as a list.

    Returns meters in consistent order matching the 5-category grouping:
    - Mind (3): clarity, focus, communication
    - Heart (3): connections, resilience, vulnerability
    - Body (3): energy, drive, strength
    - Instincts (4): vision, flow, intuition, creativity
    - Growth (4): momentum, ambition, evolution, circle

    Args:
        all_meters: AllMetersReading object from get_meters()

    Returns:
        List of 17 MeterReading objects
    """
    return [
        # Mind (3)
        all_meters.clarity,
        all_meters.focus,
        all_meters.communication,
        # Heart (3)
        all_meters.connections,
        all_meters.resilience,
        all_meters.vulnerability,
        # Body (3)
        all_meters.energy,
        all_meters.drive,
        all_meters.strength,
        # Instincts (4)
        all_meters.vision,
        all_meters.flow,
        all_meters.intuition,
        all_meters.creativity,
        # Growth (4)
        all_meters.momentum,
        all_meters.ambition,
        all_meters.evolution,
        all_meters.circle,
    ]


__all__ = [
    # Core calculation modules
    "calculate_dignity_score",
    "calculate_weightage",
    "calculate_chart_ruler",
    "get_weightage_breakdown",
    "calculate_angular_separation",
    "detect_aspect",
    "calculate_orb_factor",
    "calculate_transit_power_basic",
    "get_aspect_strength_label",
    "get_direction_modifier",
    "calculate_station_modifier",
    "calculate_transit_power_complete",
    "get_aspect_direction_status",
    "calculate_quality_factor",
    "get_quality_label",
    "TransitAspect",
    "AspectContribution",
    "AstrometerScore",
    "calculate_aspect_contribution",
    "calculate_astrometers",
    "get_score_breakdown_text",
    # Normalization
    "MeterInterpretation",
    "normalize_with_soft_ceiling",
    "normalize_intensity",
    "normalize_harmony",
    "normalize_meters",
    "get_intensity_label",
    "get_harmony_label",
    "get_meter_interpretation",
    # 17-meter system
    "MeterReading",
    "AllMetersReading",
    "get_meters",
    "METER_CONFIGS",
    # Summary and helpers
    "daily_meters_summary",
    "get_meter_list",
]

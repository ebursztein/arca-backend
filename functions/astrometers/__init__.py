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
    - Mind (3): mental_clarity, focus, communication
    - Emotions (3): love, inner_stability, sensitivity
    - Body (3): vitality, drive, wellness
    - Spirit (4): purpose, connection, intuition, creativity
    - Growth (4): opportunities, career, growth, social_life

    Args:
        all_meters: AllMetersReading object from get_meters()

    Returns:
        List of 17 MeterReading objects
    """
    return [
        # Mind (3)
        all_meters.mental_clarity,
        all_meters.focus,
        all_meters.communication,
        # Emotions (3)
        all_meters.love,
        all_meters.inner_stability,
        all_meters.sensitivity,
        # Body (3)
        all_meters.vitality,
        all_meters.drive,
        all_meters.wellness,
        # Spirit (4)
        all_meters.purpose,
        all_meters.connection,
        all_meters.intuition,
        all_meters.creativity,
        # Growth (4)
        all_meters.opportunities,
        all_meters.career,
        all_meters.growth,
        all_meters.social_life,
    ]


__all__ = [
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
    "MeterInterpretation",
    "normalize_with_soft_ceiling",
    "normalize_intensity",
    "normalize_harmony",
    "normalize_meters",
    "get_intensity_label",
    "get_harmony_label",
    "get_meter_interpretation",
    # Meter functions
    "MeterReading",
    "AllMetersReading",
    "get_meters",
    "group_meters_by_domain",
    "calculate_overall_intensity_meter",
    "calculate_overall_harmony_meter",
    "calculate_mental_clarity_meter",
    "calculate_decision_quality_meter",
    "calculate_communication_flow_meter",
    "calculate_emotional_intensity_meter",
    "calculate_relationship_harmony_meter",
    "calculate_emotional_resilience_meter",
    "calculate_physical_energy_meter",
    "calculate_conflict_risk_meter",
    "calculate_motivation_drive_meter",
    "calculate_career_ambition_meter",
    "calculate_opportunity_window_meter",
    "calculate_challenge_intensity_meter",
    "calculate_transformation_pressure_meter",
    "calculate_element_distribution",
    "calculate_fire_energy_meter",
    "calculate_earth_energy_meter",
    "calculate_air_energy_meter",
    "calculate_water_energy_meter",
    "calculate_intuition_spirituality_meter",
    "calculate_innovation_breakthrough_meter",
    "calculate_karmic_lessons_meter",
    "calculate_social_collective_meter",
    # Summary function
    "daily_meters_summary",
    # Helper function
    "get_meter_list",
]

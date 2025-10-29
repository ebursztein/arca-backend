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
from .meters import (
    MeterReading,
    AllMetersReading,
    get_meters,
    group_meters_by_domain,
    calculate_overall_intensity_meter,
    calculate_overall_harmony_meter,
    calculate_mental_clarity_meter,
    calculate_decision_quality_meter,
    calculate_communication_flow_meter,
    calculate_emotional_intensity_meter,
    calculate_relationship_harmony_meter,
    calculate_emotional_resilience_meter,
    calculate_physical_energy_meter,
    calculate_conflict_risk_meter,
    calculate_motivation_drive_meter,
    calculate_career_ambition_meter,
    calculate_opportunity_window_meter,
    calculate_challenge_intensity_meter,
    calculate_transformation_pressure_meter,
    calculate_element_distribution,
    calculate_fire_energy_meter,
    calculate_earth_energy_meter,
    calculate_air_energy_meter,
    calculate_water_energy_meter,
    calculate_intuition_spirituality_meter,
    calculate_innovation_breakthrough_meter,
    calculate_karmic_lessons_meter,
    calculate_social_collective_meter,
)
from .summary import daily_meters_summary


def get_meter_list(all_meters: AllMetersReading) -> list:
    """
    Extract all 23 meters from AllMetersReading as a list.

    Returns meters in consistent order (not alphabetical) matching the logical grouping:
    - Overview (2): overall_intensity, overall_harmony
    - Mind (3): mental_clarity, decision_quality, communication_flow
    - Emotions (3): emotional_intensity, relationship_harmony, emotional_resilience
    - Body (3): physical_energy, conflict_risk, motivation_drive
    - Career (2): career_ambition, opportunity_window
    - Evolution (3): challenge_intensity, transformation_pressure, innovation_breakthrough
    - Elements (4): fire_energy, earth_energy, air_energy, water_energy
    - Spiritual (2): intuition_spirituality, karmic_lessons
    - Collective (1): social_collective

    Args:
        all_meters: AllMetersReading object from get_meters()

    Returns:
        List of 23 MeterReading objects
    """
    return [
        # Overview (2)
        all_meters.overall_intensity,
        all_meters.overall_harmony,
        # Mind (3)
        all_meters.mental_clarity,
        all_meters.decision_quality,
        all_meters.communication_flow,
        # Emotions (3)
        all_meters.emotional_intensity,
        all_meters.relationship_harmony,
        all_meters.emotional_resilience,
        # Body (3)
        all_meters.physical_energy,
        all_meters.conflict_risk,
        all_meters.motivation_drive,
        # Career (2)
        all_meters.career_ambition,
        all_meters.opportunity_window,
        # Evolution (3)
        all_meters.challenge_intensity,
        all_meters.transformation_pressure,
        all_meters.innovation_breakthrough,
        # Elements (4)
        all_meters.fire_energy,
        all_meters.earth_energy,
        all_meters.air_energy,
        all_meters.water_energy,
        # Spiritual (2)
        all_meters.intuition_spirituality,
        all_meters.karmic_lessons,
        # Collective (1)
        all_meters.social_collective,
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

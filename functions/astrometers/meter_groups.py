"""
Meter Groups Aggregation Module

Provides functions to aggregate individual meters into 5 life-area groups
(Mind, Heart, Body, Instincts, Growth) with scores, state labels, and trends.

NOTE: Experience labels have been removed from JSON files. iOS handles bucket
labels based on unified_score. The backend provides scores only.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from .hierarchy import MeterGroupV2, get_meters_in_group_v2, get_group_v2_display_name
from .meters import (
    MeterReading,
    aggregate_meter_scores,
    calculate_unified_score,
    get_intensity_level,
    get_harmony_level,
    QualityLabel,
)


# =============================================================================
# Group Label Loading
# =============================================================================

_GROUP_LABEL_CACHE: Dict[str, Dict] = {}


def load_group_labels(group_name: str) -> Dict:
    """Load labels from JSON file for a specific meter group."""
    if group_name in _GROUP_LABEL_CACHE:
        return _GROUP_LABEL_CACHE[group_name]

    labels_dir = os.path.join(os.path.dirname(__file__), "labels", "groups")
    label_file = os.path.join(labels_dir, f"{group_name}.json")

    with open(label_file, "r") as f:
        labels = json.load(f)

    _GROUP_LABEL_CACHE[group_name] = labels
    return labels


def get_group_bucket_labels(group_name: str) -> tuple:
    """
    Get bucket labels for a group from JSON.

    Returns:
        Tuple of 4 labels: (0-25 label, 25-50 label, 50-75 label, 75-100 label)
    """
    try:
        labels = load_group_labels(group_name)
        bucket_labels = labels.get("bucket_labels")
        if bucket_labels:
            # New dict format: {"0-25": {"label": "...", "guidance": "..."}, ...}
            if isinstance(bucket_labels, dict):
                return (
                    bucket_labels.get("0-25", {}).get("label", "Low"),
                    bucket_labels.get("25-50", {}).get("label", "Mixed"),
                    bucket_labels.get("50-75", {}).get("label", "Good"),
                    bucket_labels.get("75-100", {}).get("label", "Peak"),
                )
            # Legacy list format: ["label0", "label1", "label2", "label3"]
            elif isinstance(bucket_labels, list) and len(bucket_labels) == 4:
                return tuple(bucket_labels)
    except (KeyError, FileNotFoundError):
        pass
    # Fallback
    return ("Low", "Mixed", "Good", "Peak")


def get_group_bucket_guidance(group_name: str, unified_score: float) -> str:
    """
    Get LLM guidance for a group based on unified_score.

    Args:
        group_name: Name of the meter group
        unified_score: Unified score on 0-100 scale

    Returns:
        Guidance string for LLM on how to write about this state
    """
    try:
        labels = load_group_labels(group_name)
        bucket_labels = labels.get("bucket_labels", {})
        if isinstance(bucket_labels, dict):
            if unified_score < 25:
                return bucket_labels.get("0-25", {}).get("guidance", "")
            elif unified_score < 50:
                return bucket_labels.get("25-50", {}).get("guidance", "")
            elif unified_score < 75:
                return bucket_labels.get("50-75", {}).get("guidance", "")
            else:
                return bucket_labels.get("75-100", {}).get("guidance", "")
    except (KeyError, FileNotFoundError):
        pass
    return ""


def get_group_state_label(group_name: str, unified_score: float) -> str:
    """
    Get state label for a group based on unified_score.

    Maps unified_score (0-100 scale) to one of 4 bucket labels per group.
    Labels are loaded from JSON files to stay in sync with iOS.

    Symmetric quartile thresholds (matches iOS):
        score < 25  -> bucket_labels[0]
        score >= 25 && < 50  -> bucket_labels[1]
        score >= 50 && < 75  -> bucket_labels[2]
        score >= 75 -> bucket_labels[3]

    Args:
        group_name: Name of the meter group
        unified_score: Unified score on 0-100 scale

    Returns:
        Bucket label string (e.g., "Clear", "Grounded", "Surging")
    """
    labels = get_group_bucket_labels(group_name)

    if unified_score < 25:
        return labels[0]
    elif unified_score < 50:
        return labels[1]
    elif unified_score < 75:
        return labels[2]
    else:
        return labels[3]


def get_group_advice_category(group_name: str, intensity: float, harmony: float) -> str:
    """Get advice category for a group from JSON."""
    try:
        labels = load_group_labels(group_name)
        intensity_level = get_intensity_level(intensity)
        harmony_level = get_harmony_level(harmony)
        advice_templates = labels.get("advice_templates", {})
        return advice_templates.get(intensity_level, {}).get(harmony_level, "Focus on this area")
    except (KeyError, FileNotFoundError):
        return "Focus on this area"


def get_group_description(group_name: str) -> Dict[str, str]:
    """Get group description from JSON."""
    labels = load_group_labels(group_name)
    return labels["description"]


# =============================================================================
# Top 2 Weighted Aggregation
# =============================================================================

def calculate_group_scores_top_2(meters: List[MeterReading]) -> Dict:
    """
    Calculate group scores using Top 2 by Intensity weighted average.

    This approach:
    - Selects the 2 highest-intensity meters (the "loudest voices")
    - Weights their scores by intensity
    - Filters out neutral noise from inactive meters

    Why Top 2:
    - Groups have 3-4 meters; Top 2 captures primary conflict without dilution
    - Inactive meters (low intensity) don't drag score toward neutral
    - More responsive and "alive" feeling for users

    Args:
        meters: List of MeterReading objects for this group

    Returns:
        Dict with unified_score, intensity, harmony, and driver (name of top meter)
    """
    # Safety check
    if not meters:
        return {"unified_score": 50.0, "intensity": 0.0, "harmony": 50.0, "driver": None}

    # Sort by intensity (loudest first), stable sort for determinism
    sorted_meters = sorted(meters, key=lambda m: m.intensity, reverse=True)

    # Slice top 2 (gracefully handles 1-item lists)
    top_meters = sorted_meters[:2]

    # The driver is the highest-intensity meter
    driver = top_meters[0].meter_name

    # Weighted average of top 2
    total_weighted_unified = 0.0
    total_weighted_intensity = 0.0
    total_weighted_harmony = 0.0
    total_weight = 0.0

    for m in top_meters:
        # Use intensity as weight (add epsilon for safety)
        weight = m.intensity + 0.01
        total_weighted_unified += m.unified_score * weight
        total_weighted_intensity += m.intensity * weight
        total_weighted_harmony += m.harmony * weight
        total_weight += weight

    return {
        "unified_score": round(total_weighted_unified / total_weight, 1),
        "intensity": round(total_weighted_intensity / total_weight, 1),
        "harmony": round(total_weighted_harmony / total_weight, 1),
        "driver": driver,
    }


# =============================================================================
# Quality Label Determination
# =============================================================================

def determine_quality_label(harmony: float, intensity: float) -> tuple[str, str]:
    """
    Determine quality label based on unified_score (0-100 scale).

    Calculates unified_score internally and maps to quality labels.

    Returns:
        (quality, label) tuple based on unified_score quartiles:
        - < 25: ("challenging", "Challenging")
        - 25-50: ("turbulent", "Turbulent")
        - 50-75: ("peaceful", "Peaceful")
        - >= 75: ("flowing", "Flowing")
    """
    unified_score, _ = calculate_unified_score(intensity, harmony)

    if unified_score < 25:
        return ("challenging", "Challenging")
    elif unified_score < 50:
        return ("turbulent", "Turbulent")
    elif unified_score < 75:
        return ("peaceful", "Peaceful")
    else:
        return ("flowing", "Flowing")


# =============================================================================
# Trend Calculation
# =============================================================================

def calculate_trend_metric(
    today_value: float,
    yesterday_value: float,
    metric_type: str  # "unified_score", "harmony", or "intensity"
) -> Dict:
    """
    Calculate trend data for a single metric.

    Args:
        today_value: Today's score
        yesterday_value: Yesterday's score
        metric_type: Type of metric for direction determination

    Returns:
        Dict with previous, delta, direction, change_rate
    """
    delta = today_value - yesterday_value

    # Determine direction based on metric type
    if metric_type in ["unified_score", "harmony"]:
        # For these, positive change is "improving", negative is "worsening"
        if abs(delta) < 3:
            direction = "stable"
        elif delta > 0:
            direction = "improving"
        else:
            direction = "worsening"
    else:  # intensity
        # For intensity, just say "increasing" or "decreasing"
        if abs(delta) < 3:
            direction = "stable"
        elif delta > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

    # Determine change rate
    abs_delta = abs(delta)
    if abs_delta >= 15:
        change_rate = "rapid"
    elif abs_delta >= 5:
        change_rate = "moderate"
    else:
        change_rate = "slow"

    return {
        "previous": yesterday_value,
        "delta": delta,
        "direction": direction,
        "change_rate": change_rate
    }


def calculate_group_trends(
    today_meters: List[MeterReading],
    yesterday_meters: List[MeterReading]
) -> Optional[Dict]:
    """
    Calculate trend data for a group by aggregating trends from member meters.

    Args:
        today_meters: List of MeterReading objects for today
        yesterday_meters: List of MeterReading objects for yesterday

    Returns:
        Dict with unified_score, harmony, intensity trend data, or None if no yesterday data
    """
    if not yesterday_meters or len(yesterday_meters) == 0:
        return None

    # Calculate yesterday's aggregated scores
    yesterday_intensity, yesterday_harmony = aggregate_meter_scores(yesterday_meters)
    yesterday_unified, _ = calculate_unified_score(yesterday_intensity, yesterday_harmony)

    # Calculate today's aggregated scores
    today_intensity, today_harmony = aggregate_meter_scores(today_meters)
    today_unified, _ = calculate_unified_score(today_intensity, today_harmony)

    # Calculate trend for each metric
    return {
        "unified_score": calculate_trend_metric(today_unified, yesterday_unified, "unified_score"),
        "harmony": calculate_trend_metric(today_harmony, yesterday_harmony, "harmony"),
        "intensity": calculate_trend_metric(today_intensity, yesterday_intensity, "intensity")
    }


# =============================================================================
# Main Aggregation Function
# =============================================================================

def build_meter_group_data(
    group: MeterGroupV2,
    today_meters: List[MeterReading],
    llm_interpretation: Optional[str],
    yesterday_meters: Optional[List[MeterReading]] = None
) -> Dict:
    """
    Build complete MeterGroupData for a single group.

    Args:
        group: The MeterGroupV2 enum
        today_meters: List of MeterReading objects for this group (today)
        llm_interpretation: LLM-generated interpretation text (or None if not yet generated)
        yesterday_meters: Optional list of MeterReading objects for this group (yesterday)

    Returns:
        Dict with complete group data
    """
    # Calculate all scores using Top 2 Weighted approach
    # This selects the 2 highest-intensity meters and weights by intensity,
    # filtering out neutral noise from inactive meters
    scores = calculate_group_scores_top_2(today_meters)
    unified_score = scores["unified_score"]

    # Get state label from unified_score (0-100 scale)
    state_label = get_group_state_label(group.value, unified_score)

    # Determine quality from unified_score quartiles
    if unified_score < 25:
        quality = "challenging"
    elif unified_score < 50:
        quality = "turbulent"
    elif unified_score < 75:
        quality = "peaceful"
    else:
        quality = "flowing"

    # Calculate trends if yesterday data available
    trend = calculate_group_trends(today_meters, yesterday_meters) if yesterday_meters else None

    # Get meter IDs
    meter_ids = [m.meter_name for m in today_meters]

    # Find the top aspect driving this group (from the driver meter or highest intensity)
    top_aspect = None
    top_aspect_str = None
    driver_meter_name = scores.get("driver")
    if driver_meter_name:
        # Find the driver meter and get its top aspect
        for m in today_meters:
            if m.meter_name == driver_meter_name and m.top_aspects:
                asp = m.top_aspects[0]
                top_aspect = asp
                # Format as readable string: "Mars square natal Saturn"
                top_aspect_str = f"{asp.transit_planet.value.title()} {asp.aspect_type.value} natal {asp.natal_planet.value.title()}"
                break

    # Use LLM interpretation if provided, otherwise use fallback from JSON description
    if llm_interpretation:
        interpretation = llm_interpretation
    else:
        # Fallback: use description from JSON labels
        description = get_group_description(group.value)
        interpretation = f"{description['overview']} {description['detailed']}"

    return {
        "group_name": group.value,
        "display_name": get_group_v2_display_name(group),
        "scores": scores,  # Contains unified_score, intensity, harmony, driver from Top 2
        "state": {
            "label": state_label,
            "quality": quality
        },
        "interpretation": interpretation,
        "trend": trend,
        "meter_ids": meter_ids,
        "top_aspect": top_aspect_str  # Key transit driving this group
    }


def build_all_meter_groups(
    all_meters_reading,  # AllMetersReading object
    llm_interpretations: Optional[Dict[str, str]] = None,
    yesterday_all_meters_reading = None  # Optional AllMetersReading for yesterday
) -> Dict[str, Dict]:
    """
    Build complete meter groups data for all 5 groups.

    Args:
        all_meters_reading: AllMetersReading object with all individual meters
        llm_interpretations: Dict mapping group_name -> interpretation text (from LLM)
        yesterday_all_meters_reading: Optional AllMetersReading for yesterday (for trends)

    Returns:
        Dict mapping group_name -> complete group data
    """
    from .hierarchy import Meter

    # Get all individual meters as dict
    all_meters_dict = {}
    for meter in Meter:
        # Skip overview and super-group meters
        if meter.value in ["overall_intensity", "overall_harmony"]:
            continue
        if "_super_group" in meter.value:
            continue

        # Get meter reading from AllMetersReading
        meter_reading = getattr(all_meters_reading, meter.value, None)
        if meter_reading:
            all_meters_dict[meter.value] = meter_reading

    # Get yesterday meters if available
    yesterday_meters_dict = {}
    if yesterday_all_meters_reading:
        for meter in Meter:
            if meter.value in ["overall_intensity", "overall_harmony"]:
                continue
            if "_super_group" in meter.value:
                continue

            meter_reading = getattr(yesterday_all_meters_reading, meter.value, None)
            if meter_reading:
                yesterday_meters_dict[meter.value] = meter_reading

    # Build data for each group
    meter_groups = {}
    for group in MeterGroupV2:
        # Get meters for this group
        group_meter_enums = get_meters_in_group_v2(group)
        today_group_meters = [all_meters_dict[m.value] for m in group_meter_enums if m.value in all_meters_dict]

        # Get yesterday meters for this group
        yesterday_group_meters = None
        if yesterday_meters_dict:
            yesterday_group_meters = [yesterday_meters_dict[m.value] for m in group_meter_enums if m.value in yesterday_meters_dict]
            if len(yesterday_group_meters) == 0:
                yesterday_group_meters = None

        # Get LLM interpretation if available
        llm_interp = llm_interpretations.get(group.value) if llm_interpretations else None

        # Build group data
        group_data = build_meter_group_data(
            group,
            today_group_meters,
            llm_interp,
            yesterday_group_meters
        )

        meter_groups[group.value] = group_data

    return meter_groups

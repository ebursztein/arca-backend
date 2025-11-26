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


def get_group_state_label(group_name: str, intensity: float, harmony: float) -> str:
    """
    Get state label for a group based on unified_score.

    Maps unified_score to one of 4 bucket labels per group.
    Thresholds based on quartiles (P25, P50, P75).

    Returns:
        Bucket label string (e.g., "Clear", "Grounded", "Surging")
    """
    # Calculate unified_score from intensity and harmony
    unified_score, _ = calculate_unified_score(intensity, harmony)

    # Bucket thresholds (quartile-based)
    # Bucket 1: < -25 (Challenge)
    # Bucket 2: -25 to 10 (Mixed)
    # Bucket 3: 10 to 50 (Good)
    # Bucket 4: >= 50 (Peak)

    # Group-specific bucket labels
    BUCKET_LABELS = {
        "mind": ("Overloaded", "Hazy", "Clear", "Sharp"),
        "heart": ("Heavy", "Tender", "Grounded", "Magnetic"),
        "body": ("Depleted", "Low Power Mode", "Powering Through", "Surging"),
        "instincts": ("Disconnected", "Noisy", "Tuned In", "Aligned"),
        "growth": ("Uphill", "Pacing", "Climbing", "Unstoppable"),
        "overall": ("Challenging", "Chaotic", "Peaceful", "Flowing"),
    }

    labels = BUCKET_LABELS.get(group_name, ("Low", "Mixed", "Good", "Peak"))

    if unified_score < -25:
        return labels[0]  # Challenge bucket
    elif unified_score < 10:
        return labels[1]  # Mixed bucket
    elif unified_score < 50:
        return labels[2]  # Good bucket
    else:
        return labels[3]  # Peak bucket


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
# Quality Label Determination
# =============================================================================

def determine_quality_label(harmony: float, intensity: float) -> tuple[str, str]:
    """
    Determine quality label and display label based on harmony and intensity.

    Returns:
        (quality, label) tuple
        quality: enum value ("excellent", "supportive", "harmonious", etc.)
        label: human-readable string ("Excellent", "Supportive", etc.)
    """
    if harmony >= 75:
        if intensity >= 75:
            return ("excellent", "Excellent")
        elif intensity >= 40:
            return ("supportive", "Supportive")
        else:
            return ("peaceful", "Peaceful")
    elif harmony >= 50:
        if intensity >= 60:
            return ("mixed", "Mixed")
        else:
            return ("quiet", "Quiet")
    else:
        if intensity >= 60:
            return ("intense", "Intense")
        else:
            return ("challenging", "Challenging")


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
    # Aggregate scores
    avg_intensity, avg_harmony = aggregate_meter_scores(today_meters)
    unified_score, unified_quality = calculate_unified_score(avg_intensity, avg_harmony)

    # Get state label from JSON labels
    state_label = get_group_state_label(group.value, avg_intensity, avg_harmony)

    # Determine quality enum from harmony/intensity
    quality, _ = determine_quality_label(avg_harmony, avg_intensity)

    # Calculate trends if yesterday data available
    trend = calculate_group_trends(today_meters, yesterday_meters) if yesterday_meters else None

    # Get meter IDs
    meter_ids = [m.meter_name for m in today_meters]

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
        "scores": {
            "unified_score": round(unified_score, 1),
            "harmony": round(avg_harmony, 1),
            "intensity": round(avg_intensity, 1)
        },
        "state": {
            "label": state_label,  # From JSON labels (contextual to group)
            "quality": quality      # Generic enum (excellent, supportive, etc.)
        },
        "interpretation": interpretation,
        "trend": trend,
        "meter_ids": meter_ids
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

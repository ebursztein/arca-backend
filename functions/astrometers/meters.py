"""
Clean data-driven astrometer system - 17 specialized meters.

Architecture:
- Configuration-driven: Meters defined as data, not code
- Single calculation function for all meters
- Composable filter functions
- Type-safe with Pydantic
- ~400 lines instead of 2,000+

Usage:
    from astrometers.meters import get_meters

    all_readings = get_meters(natal_chart, transit_chart)
    print(all_readings.love.unified_score)  # 85.3
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field

# Core dependencies
from astro import Planet, AspectType, ZodiacSign, House
from .core import TransitAspect, AspectContribution, calculate_astrometers, AstrometerScore
from .normalization import normalize_intensity, normalize_harmony
from .quality import harmonic_boost
from .hierarchy import Meter, MeterGroupV2, get_group_v2
from .constants import (
    INTENSITY_QUIET_THRESHOLD,
    INTENSITY_MILD_THRESHOLD,
    INTENSITY_MODERATE_THRESHOLD,
    INTENSITY_HIGH_THRESHOLD,
    HARMONY_CHALLENGING_THRESHOLD,
    HARMONY_HARMONIOUS_THRESHOLD
)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class QualityLabel(str, Enum):
    """Unified quality labels for meter readings."""
    HARMONIOUS = "harmonious"
    CHALLENGING = "challenging"
    MIXED = "mixed"
    QUIET = "quiet"
    PEACEFUL = "peaceful"


class TrendData(BaseModel):
    """Trend information comparing today vs yesterday."""
    previous: float
    delta: float
    direction: str  # "improving", "worsening", "stable"
    change_rate: str  # "stable", "slow", "moderate", "rapid"


class MeterTrends(BaseModel):
    """Separate trend data for intensity, harmony, and unified_score."""
    intensity: TrendData
    harmony: TrendData
    unified_score: TrendData


class MeterReading(BaseModel):
    """Complete meter reading with all metadata."""
    meter_name: str
    date: datetime
    group: MeterGroupV2

    # Primary scores
    unified_score: float = Field(ge=0, le=100)
    intensity: float = Field(ge=0, le=100)
    harmony: float = Field(ge=0, le=100)

    # Labels
    unified_quality: QualityLabel
    state_label: str

    # Metadata
    interpretation: str
    advice: List[str]
    top_aspects: List[AspectContribution]
    raw_scores: Dict[str, float]

    # Trend (optional)
    trend: Optional[MeterTrends] = None


class AllMetersReading(BaseModel):
    """All 17 meter readings + 2 overall aggregates."""
    date: datetime

    # Overall aggregates (for main page display)
    overall_intensity: MeterReading
    overall_harmony: MeterReading
    overall_unified_quality: QualityLabel  # Direct access to overall quality
    aspect_count: int  # Total aspects analyzed across all meters
    key_aspects: List[AspectContribution]  # Top aspects driving today's energy

    # Mind (3)
    mental_clarity: MeterReading
    focus: MeterReading
    communication: MeterReading

    # Emotions (3)
    love: MeterReading
    inner_stability: MeterReading
    sensitivity: MeterReading

    # Body (3)
    vitality: MeterReading
    drive: MeterReading
    wellness: MeterReading

    # Spirit (4)
    purpose: MeterReading
    connection: MeterReading
    intuition: MeterReading
    creativity: MeterReading

    # Growth (4)
    opportunities: MeterReading
    career: MeterReading
    growth: MeterReading
    social_life: MeterReading


class MeterConfig(BaseModel):
    """Configuration for a single meter."""
    name: str
    group: MeterGroupV2

    # Filter criteria
    natal_planets: List[Planet] = []
    natal_houses: List[int] = []
    transit_planets: List[Planet] = []
    aspect_types: List[AspectType] = []  # Empty = all types

    # Modifiers
    retrograde_modifiers: Dict[Planet, float] = {}


# =============================================================================
# METER CONFIGURATIONS (Loaded from JSON)
# =============================================================================

def _load_meter_configs() -> Dict[str, MeterConfig]:
    """Load meter configurations from JSON label files."""
    labels_dir = os.path.join(os.path.dirname(__file__), "labels")
    configs = {}

    # Meter names and their groups
    meter_groups = {
        "mental_clarity": MeterGroupV2.MIND,
        "focus": MeterGroupV2.MIND,
        "communication": MeterGroupV2.MIND,
        "love": MeterGroupV2.EMOTIONS,
        "inner_stability": MeterGroupV2.EMOTIONS,
        "sensitivity": MeterGroupV2.EMOTIONS,
        "vitality": MeterGroupV2.BODY,
        "drive": MeterGroupV2.BODY,
        "wellness": MeterGroupV2.BODY,
        "purpose": MeterGroupV2.SPIRIT,
        "connection": MeterGroupV2.SPIRIT,
        "intuition": MeterGroupV2.SPIRIT,
        "creativity": MeterGroupV2.SPIRIT,
        "opportunities": MeterGroupV2.GROWTH,
        "career": MeterGroupV2.GROWTH,
        "growth": MeterGroupV2.GROWTH,
        "social_life": MeterGroupV2.GROWTH,
    }

    for meter_name, group in meter_groups.items():
        label_file = os.path.join(labels_dir, f"{meter_name}.json")

        with open(label_file, "r") as f:
            data = json.load(f)

        config_data = data.get("configuration", {})

        # Convert planet strings to Planet enums
        natal_planets = [Planet(p) for p in config_data.get("natal_planets", [])]

        # Convert retrograde modifier keys to Planet enums
        retro_mods = {}
        for planet_str, value in config_data.get("retrograde_modifiers", {}).items():
            retro_mods[Planet(planet_str)] = value

        configs[meter_name] = MeterConfig(
            name=meter_name,
            group=group,
            natal_planets=natal_planets,
            natal_houses=config_data.get("natal_houses", []),
            transit_planets=[],  # All transits allowed
            aspect_types=[],  # All aspects allowed
            retrograde_modifiers=retro_mods
        )

    return configs

# Load configs from JSON on module import
METER_CONFIGS: Dict[str, MeterConfig] = _load_meter_configs()


# =============================================================================
# COMPOSABLE FILTER FUNCTIONS
# =============================================================================


# =============================================================================
# COMPOSABLE FILTER FUNCTIONS
# =============================================================================

def filter_aspects(
    all_aspects: List[TransitAspect],
    config: MeterConfig,
    natal_chart: dict
) -> List[TransitAspect]:
    """
    Filter aspects based on meter configuration.

    Logic: natal_planets OR natal_houses (whichever is specified)
           AND transit_planets (if specified)
           AND aspect_types (if specified)

    Args:
        all_aspects: All natal-transit aspects
        config: Meter configuration
        natal_chart: Natal chart data (for house lookups)

    Returns:
        Filtered list of relevant aspects
    """
    filtered = []

    for aspect in all_aspects:
        # Step 1: Check natal filters (planets OR houses)
        natal_match = False

        # If natal_planets specified, check if this aspect's natal planet matches
        if config.natal_planets:
            if aspect.natal_planet in config.natal_planets:
                natal_match = True

        # If natal_houses specified, check if this aspect's natal planet is in those houses
        if config.natal_houses and not natal_match:
            # Get house for this natal planet
            natal_house = None
            for planet in natal_chart.get("planets", []):
                if planet["name"] == aspect.natal_planet.value:
                    natal_house = planet["house"]
                    break

            if natal_house in config.natal_houses:
                natal_match = True

        # If no natal filters specified, all aspects match
        if not config.natal_planets and not config.natal_houses:
            natal_match = True

        # Skip if natal filters didn't match
        if not natal_match:
            continue

        # Step 2: Check transit planet filter (must match if specified)
        if config.transit_planets and aspect.transit_planet not in config.transit_planets:
            continue

        # Step 3: Check aspect type filter (must match if specified)
        if config.aspect_types and aspect.aspect_type not in config.aspect_types:
            continue

        # Passed all filters
        filtered.append(aspect)

    return filtered


# =============================================================================
# LABEL LOADING
# =============================================================================

_LABEL_CACHE: Dict[str, Dict] = {}

def load_meter_labels(meter_name: str) -> Dict:
    """Load labels from JSON file."""
    if meter_name in _LABEL_CACHE:
        return _LABEL_CACHE[meter_name]

    labels_dir = os.path.join(os.path.dirname(__file__), "labels")
    label_file = os.path.join(labels_dir, f"{meter_name}.json")

    with open(label_file, "r") as f:
        labels = json.load(f)

    _LABEL_CACHE[meter_name] = labels
    return labels


def get_intensity_level(intensity: float) -> str:
    """Map intensity score to level."""
    if intensity < INTENSITY_QUIET_THRESHOLD:
        return "quiet"
    elif intensity < INTENSITY_MILD_THRESHOLD:
        return "mild"
    elif intensity < INTENSITY_MODERATE_THRESHOLD:
        return "moderate"
    elif intensity < INTENSITY_HIGH_THRESHOLD:
        return "high"
    else:
        return "extreme"


def get_harmony_level(harmony: float) -> str:
    """Map harmony score to level."""
    if harmony < HARMONY_CHALLENGING_THRESHOLD:
        return "challenging"
    elif harmony < HARMONY_HARMONIOUS_THRESHOLD:
        return "mixed"
    else:
        return "harmonious"


def get_state_label(meter_name: str, intensity: float, harmony: float) -> str:
    """Get state label from JSON."""
    try:
        labels = load_meter_labels(meter_name)
        intensity_level = get_intensity_level(intensity)
        harmony_level = get_harmony_level(harmony)

        return labels["experience_labels"]["combined"][intensity_level][harmony_level]
    except (KeyError, FileNotFoundError):
        # Fallback
        return f"{get_intensity_level(intensity).title()} & {get_harmony_level(harmony).title()}"


def get_quality_label(intensity: float, harmony: float) -> QualityLabel:
    """Determine unified quality label."""
    if intensity < INTENSITY_QUIET_THRESHOLD:
        return QualityLabel.QUIET if harmony >= 50 else QualityLabel.CHALLENGING
    elif harmony >= HARMONY_HARMONIOUS_THRESHOLD:
        return QualityLabel.HARMONIOUS
    elif harmony <= HARMONY_CHALLENGING_THRESHOLD:
        return QualityLabel.CHALLENGING
    else:
        return QualityLabel.MIXED


def calculate_unified_score(intensity: float, harmony: float) -> tuple[float, QualityLabel]:
    """
    Calculate unified score and quality label.

    Design: unified_score = harmonic mean of intensity and harmony.
    This ensures both metrics contribute - low value in either dimension reduces the unified score.

    Args:
        intensity: Intensity meter (0-100) - how much is happening
        harmony: Harmony meter (0-100) - quality of what's happening

    Returns:
        Tuple of (unified_score, quality_label):
        - unified_score: Harmonic mean of intensity and harmony
        - quality_label: QualityLabel enum based on intensity + harmony combination
    """
    # Harmonic mean: 2 * (a * b) / (a + b)
    # Handle edge case where both are 0
    if intensity + harmony == 0:
        unified_score = 0.0
    else:
        unified_score = 2 * intensity * harmony / (intensity + harmony)

    quality = get_quality_label(intensity, harmony)
    return unified_score, quality


def aggregate_meter_scores(meters: list[MeterReading]) -> tuple[float, float]:
    """
    Calculate simple average of intensity and harmony across multiple meters.

    Args:
        meters: List of MeterReading objects to aggregate

    Returns:
        Tuple of (avg_intensity, avg_harmony)

    Example:
        >>> meters = [mental_clarity, focus, communication]
        >>> intensity, harmony = aggregate_meter_scores(meters)
        >>> # Returns average intensity and harmony for Mind group
    """
    if not meters:
        return 0.0, 50.0  # No meters = neutral

    total_intensity = sum(m.intensity for m in meters)
    total_harmony = sum(m.harmony for m in meters)

    avg_intensity = total_intensity / len(meters)
    avg_harmony = total_harmony / len(meters)

    return avg_intensity, avg_harmony


# =============================================================================
# CORE CALCULATION (Single Function for All Meters)
# =============================================================================

def calculate_meter(
    meter_name: str,
    config: MeterConfig,
    all_aspects: List[TransitAspect],
    natal_chart: dict,
    transit_chart: dict,
    date: datetime,
    apply_harmonic_boost: bool = True,
    benefic_multiplier: float = 2.0,
    malefic_multiplier: float = 0.5
) -> MeterReading:
    """
    Calculate a single meter reading.

    This is the ONLY calculation function needed for all 17 meters.

    Args:
        meter_name: Meter identifier
        config: Meter configuration
        all_aspects: All natal-transit aspects
        natal_chart: Natal chart data
        transit_chart: Transit chart data
        date: Date of reading
        apply_harmonic_boost: Apply planetary nature multipliers (default: True)
        benefic_multiplier: Multiplier for benefic+harmonious aspects (default: 2.0)
        malefic_multiplier: Multiplier for malefic+challenging aspects (default: 0.5)

    Returns:
        Complete MeterReading
    """
    # Step 1: Filter aspects
    filtered_aspects = filter_aspects(all_aspects, config, natal_chart)

    # Step 2: Calculate raw scores (flat baseline quality factors)
    if not filtered_aspects:
        # No activity
        raw_score = AstrometerScore(dti=0.0, hqs=0.0, aspect_count=0, contributions=[])
    else:
        raw_score = calculate_astrometers(filtered_aspects)

    # Step 2.5: Apply planetary nature adjustments (harmonic boost) - OPTIONAL
    # Benefic + harmonious: benefic_multiplier enhancement (default 1.1x)
    # Malefic + challenging: malefic_multiplier softening (default 0.85x)
    # Applied AFTER raw calculation, BEFORE normalization against flat baseline
    if apply_harmonic_boost and raw_score.contributions:
        boosted_hqs = harmonic_boost(
            raw_score.hqs,
            raw_score.contributions,
            benefic_multiplier=benefic_multiplier,
            malefic_multiplier=malefic_multiplier
        )
    else:
        boosted_hqs = raw_score.hqs  # No boost applied

    # Step 3: Normalize to 0-100 (against flat baseline calibration)
    intensity = normalize_intensity(raw_score.dti, meter_name)
    harmony = normalize_harmony(boosted_hqs, meter_name)  # Normalize (boosted or flat)

    # Step 4: Apply retrograde modifiers
    for planet, modifier in config.retrograde_modifiers.items():
        if is_planet_retrograde(transit_chart, planet):
            harmony = harmony * modifier
            harmony = max(0.0, min(100.0, harmony))  # Clamp

    # Step 5: Calculate unified score (harmonic mean)
    unified_score, _ = calculate_unified_score(intensity, harmony)

    # Step 6: Get labels
    state_label = get_state_label(meter_name, intensity, harmony)
    quality_label = get_quality_label(intensity, harmony)

    # Step 7: Get interpretation and advice
    try:
        labels = load_meter_labels(meter_name)
        interpretation = labels["metadata"]["description"]
        advice = labels.get("advice_templates", {}).get("general", ["Focus on this area today"])
    except (KeyError, FileNotFoundError):
        interpretation = f"Measures {meter_name.replace('_', ' ')}"
        advice = ["Stay aware of this energy"]

    # Step 8: Build reading
    return MeterReading(
        meter_name=meter_name,
        date=date,
        group=config.group,
        unified_score=unified_score,
        intensity=intensity,
        harmony=harmony,
        unified_quality=quality_label,
        state_label=state_label,
        interpretation=interpretation,
        advice=advice,
        top_aspects=raw_score.contributions[:5],
        raw_scores={
            "dti": raw_score.dti,
            "hqs": raw_score.hqs
        }
    )


def is_planet_retrograde(transit_chart: dict, planet: Planet) -> bool:
    """Check if a planet is retrograde in transit chart."""
    for p in transit_chart.get("planets", []):
        if p["name"] == planet.value:
            return p.get("retrograde", False)
    return False


# =============================================================================
# PUBLIC API
# =============================================================================

def get_meters(
    natal_chart: dict,
    transit_chart: dict,
    date: Optional[datetime] = None,
    calculate_trends: bool = True,
    apply_harmonic_boost: bool = True,
    benefic_multiplier: float = 2.0,
    malefic_multiplier: float = 0.5
) -> AllMetersReading:
    """
    Calculate all 17 meters.

    Args:
        natal_chart: User's natal chart
        transit_chart: Current transit chart
        date: Date of reading (default: now)
        calculate_trends: Whether to calculate trends (requires yesterday's data)
        apply_harmonic_boost: Apply planetary nature multipliers (default: True)
        benefic_multiplier: Multiplier for benefic+harmonious aspects (default: 2.0)
        malefic_multiplier: Multiplier for malefic+challenging aspects (default: 0.5)

    Returns:
        AllMetersReading with all 17 meters
    """
    if date is None:
        date = datetime.now()

    # Calculate all aspects once
    from .core import calculate_all_aspects
    all_aspects = calculate_all_aspects(natal_chart, transit_chart)

    # Calculate all 17 meters
    readings = {}
    for meter_name, config in METER_CONFIGS.items():
        readings[meter_name] = calculate_meter(
            meter_name,
            config,
            all_aspects,
            natal_chart,
            transit_chart,
            date,
            apply_harmonic_boost=apply_harmonic_boost,
            benefic_multiplier=benefic_multiplier,
            malefic_multiplier=malefic_multiplier
        )

    # Calculate trends if requested
    if calculate_trends:
        from astro import compute_birth_chart
        yesterday = date - timedelta(days=1)
        yesterday_transit, _ = compute_birth_chart(
            yesterday.strftime("%Y-%m-%d"),
            "12:00"
        )
        yesterday_aspects = calculate_all_aspects(natal_chart, yesterday_transit)

        for meter_name, config in METER_CONFIGS.items():
            yesterday_reading = calculate_meter(
                meter_name,
                config,
                yesterday_aspects,
                natal_chart,
                yesterday_transit,
                yesterday
            )

            # Helper function to calculate single trend
            def calc_trend(today_val: float, yesterday_val: float, metric_name: str) -> TrendData:
                delta = today_val - yesterday_val

                if abs(delta) < 2.0:
                    change_rate = "stable"
                elif abs(delta) < 5.5:
                    change_rate = "slow"
                elif abs(delta) < 10.5:
                    change_rate = "moderate"
                else:
                    change_rate = "rapid"

                # Direction depends on metric type
                if metric_name == "harmony":
                    direction = "improving" if delta > 0 else "worsening" if delta < 0 else "stable"
                else:  # intensity or unified_score
                    direction = "increasing" if delta > 0 else "decreasing" if delta < 0 else "stable"

                return TrendData(
                    previous=yesterday_val,
                    delta=delta,
                    direction=direction,
                    change_rate=change_rate
                )

            # Calculate trends for all three metrics
            today_reading = readings[meter_name]
            readings[meter_name].trend = MeterTrends(
                intensity=calc_trend(today_reading.intensity, yesterday_reading.intensity, "intensity"),
                harmony=calc_trend(today_reading.harmony, yesterday_reading.harmony, "harmony"),
                unified_score=calc_trend(today_reading.unified_score, yesterday_reading.unified_score, "unified_score")
            )

    # Calculate overall aggregates using DYNAMIC WEIGHTED AVERAGE
    # Weight = intensity * (1 + |delta|/100) to favor active, changing meters
    all_17_meters = [
        readings["mental_clarity"], readings["focus"], readings["communication"],
        readings["love"], readings["inner_stability"], readings["sensitivity"],
        readings["vitality"], readings["drive"], readings["wellness"],
        readings["purpose"], readings["connection"], readings["intuition"], readings["creativity"],
        readings["opportunities"], readings["career"], readings["growth"], readings["social_life"]
    ]

    total_weighted_intensity = 0.0
    total_weighted_harmony = 0.0
    total_weight = 0.0

    for meter in all_17_meters:
        # Base weight on intensity (active meters matter more)
        base_weight = meter.intensity / 100.0  # 0-1 range

        # Boost weight if meter is changing (trending meters matter more)
        change_multiplier = 1.0
        if meter.trend:
            # Use unified_score delta as proxy for overall change
            abs_delta = abs(meter.trend.unified_score.delta)
            change_multiplier = 1.0 + (abs_delta / 50.0)  # Up to 3x weight for rapidly changing meters

        weight = base_weight * change_multiplier

        total_weighted_intensity += meter.intensity * weight
        total_weighted_harmony += meter.harmony * weight
        total_weight += weight

    # Calculate weighted averages
    if total_weight > 0:
        avg_intensity = total_weighted_intensity / total_weight
        avg_harmony = total_weighted_harmony / total_weight
    else:
        # Fallback to simple average if no weights
        avg_intensity = sum(m.intensity for m in all_17_meters) / len(all_17_meters)
        avg_harmony = sum(m.harmony for m in all_17_meters) / len(all_17_meters)

    overall_unified_score, overall_quality = calculate_unified_score(avg_intensity, avg_harmony)

    # Aggregate key aspects across all meters (find aspects affecting multiple meters)
    aspect_contributions_map = {}  # aspect_description -> (aspect, count, affected_meters)
    total_aspect_count = 0

    for meter in all_17_meters:
        total_aspect_count += len(meter.top_aspects)
        for aspect_contrib in meter.top_aspects[:5]:  # Top 5 from each meter
            key = f"{aspect_contrib.transit_planet}_{aspect_contrib.aspect_type}_{aspect_contrib.natal_planet}"
            if key not in aspect_contributions_map:
                aspect_contributions_map[key] = {
                    "aspect_contrib": aspect_contrib,  # Keep first instance
                    "count": 0,
                    "meters": [],
                    "total_dti": 0.0,
                    "total_hqs": 0.0
                }
            aspect_contributions_map[key]["count"] += 1
            aspect_contributions_map[key]["meters"].append(meter.meter_name)
            aspect_contributions_map[key]["total_dti"] += aspect_contrib.dti_contribution
            aspect_contributions_map[key]["total_hqs"] += aspect_contrib.hqs_contribution

    # Convert to list, sorted by meter count (cross-cutting aspects)
    key_aspects_list = []
    for key, data in aspect_contributions_map.items():
        # Use the first AspectContribution but add aggregated info
        asp = data["aspect_contrib"]
        key_aspects_list.append({
            "aspect": asp,
            "meter_count": data["count"],
            "affected_meters": data["meters"],
            "description": f"{asp.transit_planet.value.title()} {asp.aspect_type.value} your natal {asp.natal_planet.value.title()}"
        })

    # Sort by meter_count descending (aspects affecting multiple meters are more important)
    key_aspects_list.sort(key=lambda x: (x["meter_count"], x["aspect"].dti_contribution), reverse=True)

    # Keep just AspectContribution objects for compatibility
    key_aspects_list = [x["aspect"] for x in key_aspects_list]

    # Create overall intensity meter (shows activity level)
    readings["overall_intensity"] = MeterReading(
        meter_name="overall_intensity",
        date=date,
        group=MeterGroupV2.GROWTH,  # Arbitrary
        unified_score=overall_unified_score,
        intensity=avg_intensity,
        harmony=avg_harmony,
        unified_quality=overall_quality,
        state_label=get_state_label("overall_intensity", avg_intensity, avg_harmony),
        interpretation=f"Across all life areas, intensity is at {avg_intensity:.0f}/100",
        advice=["Monitor all areas", "Balance your energy"],
        top_aspects=[],
        raw_scores={"intensity": avg_intensity, "harmony": avg_harmony}
    )

    # Create overall harmony meter (shows quality of energy)
    readings["overall_harmony"] = MeterReading(
        meter_name="overall_harmony",
        date=date,
        group=MeterGroupV2.GROWTH,  # Arbitrary
        unified_score=overall_unified_score,
        intensity=avg_intensity,
        harmony=avg_harmony,
        unified_quality=overall_quality,
        state_label=get_state_label("overall_harmony", avg_intensity, avg_harmony),
        interpretation=f"Across all life areas, harmony is at {avg_harmony:.0f}/100",
        advice=["Stay balanced", "Trust the flow"],
        top_aspects=[],
        raw_scores={"intensity": avg_intensity, "harmony": avg_harmony}
    )

    # Build AllMetersReading
    return AllMetersReading(
        date=date,
        # Overall aggregates (for main page)
        overall_intensity=readings["overall_intensity"],
        overall_harmony=readings["overall_harmony"],
        overall_unified_quality=overall_quality,
        aspect_count=total_aspect_count,
        key_aspects=key_aspects_list[:10],  # Top 10 cross-cutting aspects
        # Mind
        mental_clarity=readings["mental_clarity"],
        focus=readings["focus"],
        communication=readings["communication"],
        # Emotions
        love=readings["love"],
        inner_stability=readings["inner_stability"],
        sensitivity=readings["sensitivity"],
        # Body
        vitality=readings["vitality"],
        drive=readings["drive"],
        wellness=readings["wellness"],
        # Spirit
        purpose=readings["purpose"],
        connection=readings["connection"],
        intuition=readings["intuition"],
        creativity=readings["creativity"],
        # Growth
        opportunities=readings["opportunities"],
        career=readings["career"],
        growth=readings["growth"],
        social_life=readings["social_life"],
    )


def get_meter(
    meter_name: str,
    natal_chart: dict,
    transit_chart: dict,
    date: Optional[datetime] = None
) -> MeterReading:
    """
    Calculate a single meter.

    Args:
        meter_name: Name of meter to calculate
        natal_chart: User's natal chart
        transit_chart: Current transit chart
        date: Date of reading

    Returns:
        Single MeterReading
    """
    if meter_name not in METER_CONFIGS:
        raise ValueError(f"Unknown meter: {meter_name}")

    if date is None:
        date = datetime.now()

    from .core import calculate_all_aspects
    all_aspects = calculate_all_aspects(natal_chart, transit_chart)

    config = METER_CONFIGS[meter_name]
    return calculate_meter(
        meter_name,
        config,
        all_aspects,
        natal_chart,
        transit_chart,
        date
    )

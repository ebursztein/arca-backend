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
    unified_score: float = Field(ge=-100, le=100)  # V2: polar-style -100 to +100
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
    clarity: MeterReading
    focus: MeterReading
    communication: MeterReading

    # Heart (3)
    resilience: MeterReading
    connections: MeterReading
    vulnerability: MeterReading

    # Body (3)
    energy: MeterReading
    drive: MeterReading
    strength: MeterReading

    # Instincts (4)
    vision: MeterReading
    flow: MeterReading
    intuition: MeterReading
    creativity: MeterReading

    # Growth (4)
    momentum: MeterReading
    ambition: MeterReading
    evolution: MeterReading
    circle: MeterReading


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
        "clarity": MeterGroupV2.MIND,
        "focus": MeterGroupV2.MIND,
        "communication": MeterGroupV2.MIND,
        "resilience": MeterGroupV2.HEART,
        "connections": MeterGroupV2.HEART,
        "vulnerability": MeterGroupV2.HEART,
        "energy": MeterGroupV2.BODY,
        "drive": MeterGroupV2.BODY,
        "strength": MeterGroupV2.BODY,
        "vision": MeterGroupV2.INSTINCTS,
        "flow": MeterGroupV2.INSTINCTS,
        "intuition": MeterGroupV2.INSTINCTS,
        "creativity": MeterGroupV2.INSTINCTS,
        "momentum": MeterGroupV2.GROWTH,
        "ambition": MeterGroupV2.GROWTH,
        "evolution": MeterGroupV2.GROWTH,
        "circle": MeterGroupV2.GROWTH,
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
    """
    Get state label for a meter based on unified_score.

    Maps unified_score to one of 4 bucket labels based on the meter's group.
    Individual meters inherit bucket labels from their parent group.

    Returns:
        Bucket label string (e.g., "Clear", "Grounded", "Surging")
    """
    from .hierarchy import METER_TO_GROUP_V2, Meter

    # Calculate unified_score
    unified_score, _ = calculate_unified_score(intensity, harmony)

    # Get the meter's group
    try:
        meter_enum = Meter(meter_name)
        group = METER_TO_GROUP_V2.get(meter_enum)
        group_name = group.value if group else "overall"
    except ValueError:
        group_name = "overall"

    # Group-specific bucket labels
    BUCKET_LABELS = {
        "mind": ("Overloaded", "Hazy", "Clear", "Sharp"),
        "heart": ("Heavy", "Tender", "Grounded", "Magnetic"),
        "body": ("Depleted", "Low Power Mode", "Powering Through", "Surging"),
        "instincts": ("Disconnected", "Noisy", "Tuned In", "Aligned"),
        "growth": ("Uphill", "Pacing", "Climbing", "Unstoppable"),
        "overall": ("Challenging", "Turbulent", "Peaceful", "Flowing"),
    }

    labels = BUCKET_LABELS.get(group_name, ("Low", "Mixed", "Good", "Peak"))

    # Map unified_score to bucket (quartile-based thresholds)
    if unified_score < -25:
        return labels[0]  # Challenge bucket
    elif unified_score < 10:
        return labels[1]  # Mixed bucket
    elif unified_score < 50:
        return labels[2]  # Good bucket
    else:
        return labels[3]  # Peak bucket


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
    Calculate unified score and quality label using polar-style formula with sigmoid stretch.

    Design: unified_score combines intensity (magnitude) with harmony (direction).
    - Harmony determines direction: above 50 = positive, below 50 = negative
    - Intensity amplifies the signal (but harmony is always partially visible)
    - Sigmoid (tanh) stretches middle values toward extremes for better range use
    - Empowering asymmetry: positive boosted, negative dampened

    Args:
        intensity: Intensity meter (0-100) - how much is happening
        harmony: Harmony meter (0-100) - quality of what's happening (50 = neutral)

    Returns:
        Tuple of (unified_score, quality_label):
        - unified_score: -100 to +100 (positive = harmonious, negative = challenging)
        - quality_label: QualityLabel enum based on intensity + harmony combination
    """
    import math
    from astrometers.constants import (
        UNIFIED_SCORE_BASE_WEIGHT,
        UNIFIED_SCORE_INTENSITY_WEIGHT,
        UNIFIED_SCORE_TANH_FACTOR,
        UNIFIED_SCORE_POSITIVE_BOOST,
        UNIFIED_SCORE_NEGATIVE_DAMPEN,
    )

    # Base direction from harmony: -100 to +100
    base_direction = (harmony - 50) * 2

    # Intensity as amplification factor: BASE_WEIGHT to 1.0
    # Even at intensity=0, we preserve BASE_WEIGHT of the harmony signal
    magnitude_factor = UNIFIED_SCORE_BASE_WEIGHT + UNIFIED_SCORE_INTENSITY_WEIGHT * (intensity / 100)

    # Raw score before stretch
    raw_score = base_direction * magnitude_factor

    # Apply sigmoid stretch using tanh - spreads middle values toward extremes
    stretched = 100 * math.tanh(raw_score / UNIFIED_SCORE_TANH_FACTOR)

    # Apply empowering asymmetry: boost positive, dampen negative
    if stretched >= 0:
        unified_score = min(100, round(stretched * UNIFIED_SCORE_POSITIVE_BOOST, 1))
    else:
        unified_score = max(-100, round(stretched * UNIFIED_SCORE_NEGATIVE_DAMPEN, 1))

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


def calculate_cosmic_background(
    user_id: str,
    date: str,
    meter_name: str,
    aspect_count: int
) -> tuple[float, float]:
    """
    Calculate cosmic background noise for natural daily meter variation.

    Adds reproducible randomness tied to user+date+meter for personalized feel.
    Only applies when there are active transits (aspect_count > 0).

    Args:
        user_id: User identifier for reproducible randomness
        date: Date string (YYYY-MM-DD) for reproducible randomness
        meter_name: Meter identifier for reproducible randomness
        aspect_count: Number of active aspects for this meter

    Returns:
        Tuple of (intensity_noise, harmony_nudge):
        - intensity_noise: -5 to +10 (slight positive bias)
        - harmony_nudge: 0 to +3 (always positive - empowering)
    """
    import hashlib
    import random
    from astrometers.constants import (
        COSMIC_NOISE_INTENSITY_MIN,
        COSMIC_NOISE_INTENSITY_MAX,
        COSMIC_NOISE_HARMONY_MIN,
        COSMIC_NOISE_HARMONY_MAX,
    )

    # No noise if no transits - the meter should stay quiet
    if aspect_count == 0:
        return 0.0, 0.0

    # Create deterministic seed from user + date + meter
    # This ensures same user gets same noise on same day for same meter
    seed_string = f"{user_id}:{date}:{meter_name}"
    seed_hash = int(hashlib.sha256(seed_string.encode()).hexdigest()[:8], 16)

    # Use seed for reproducible randomness
    rng = random.Random(seed_hash)

    # Intensity noise: slight positive bias
    intensity_noise = rng.uniform(COSMIC_NOISE_INTENSITY_MIN, COSMIC_NOISE_INTENSITY_MAX)

    # Harmony nudge: always positive (empowering)
    harmony_nudge = rng.uniform(COSMIC_NOISE_HARMONY_MIN, COSMIC_NOISE_HARMONY_MAX)

    return intensity_noise, harmony_nudge


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
    malefic_multiplier: float = 0.5,
    user_id: Optional[str] = None
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
        user_id: User ID for cosmic background noise (optional)

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

    # Step 3.5: Apply cosmic background noise (if user_id provided)
    if user_id:
        date_str = date.strftime("%Y-%m-%d")
        intensity_noise, harmony_nudge = calculate_cosmic_background(
            user_id=user_id,
            date=date_str,
            meter_name=meter_name,
            aspect_count=raw_score.aspect_count
        )
        intensity = max(0.0, min(100.0, intensity + intensity_noise))
        harmony = max(0.0, min(100.0, harmony + harmony_nudge))

    # Step 4: Apply retrograde modifiers
    for planet, modifier in config.retrograde_modifiers.items():
        if is_planet_retrograde(transit_chart, planet):
            harmony = harmony * modifier
            harmony = max(0.0, min(100.0, harmony))  # Clamp

    # Step 5: Calculate unified score (polar-style with sigmoid stretch)
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
    malefic_multiplier: float = 0.5,
    user_id: Optional[str] = None
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
        user_id: User ID for cosmic background noise (optional)

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
            malefic_multiplier=malefic_multiplier,
            user_id=user_id
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
        readings["clarity"], readings["focus"], readings["communication"],
        readings["resilience"], readings["connections"], readings["vulnerability"],
        readings["energy"], readings["drive"], readings["strength"],
        readings["vision"], readings["flow"], readings["intuition"], readings["creativity"],
        readings["momentum"], readings["ambition"], readings["evolution"], readings["circle"]
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
        clarity=readings["clarity"],
        focus=readings["focus"],
        communication=readings["communication"],
        # Heart
        resilience=readings["resilience"],
        connections=readings["connections"],
        vulnerability=readings["vulnerability"],
        # Body
        energy=readings["energy"],
        drive=readings["drive"],
        strength=readings["strength"],
        # Instincts
        vision=readings["vision"],
        flow=readings["flow"],
        intuition=readings["intuition"],
        creativity=readings["creativity"],
        # Growth
        momentum=readings["momentum"],
        ambition=readings["ambition"],
        evolution=readings["evolution"],
        circle=readings["circle"],
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


# =============================================================================
# WORD BANKS & FEATURED SELECTION (for LLM curation)
# =============================================================================

_WORD_BANKS_CACHE = None

def load_word_banks() -> dict:
    """Load word banks from JSON config file."""
    global _WORD_BANKS_CACHE
    if _WORD_BANKS_CACHE is not None:
        return _WORD_BANKS_CACHE

    word_banks_file = os.path.join(
        os.path.dirname(__file__), "labels", "word_banks.json"
    )
    with open(word_banks_file, "r") as f:
        _WORD_BANKS_CACHE = json.load(f)

    return _WORD_BANKS_CACHE


def get_quadrant(intensity: float, harmony: float) -> str:
    """
    Determine which quadrant based on intensity and harmony.

    Uses empirical thresholds from 102k data points (P33/P67).

    Returns:
        One of: "high_intensity_high_harmony", "high_intensity_low_harmony",
                "low_intensity_high_harmony", "low_intensity_low_harmony", "moderate"
    """
    word_banks = load_word_banks()
    thresholds = word_banks["thresholds"]

    int_low = thresholds["intensity"]["low"]   # 19
    int_high = thresholds["intensity"]["high"]  # 38
    harm_low = thresholds["harmony"]["low"]     # 52
    harm_high = thresholds["harmony"]["high"]   # 65

    is_int_high = intensity > int_high
    is_int_low = intensity < int_low
    is_harm_high = harmony > harm_high
    is_harm_low = harmony < harm_low

    if is_int_high and is_harm_high:
        return "high_intensity_high_harmony"
    elif is_int_high and is_harm_low:
        return "high_intensity_low_harmony"
    elif is_int_low and is_harm_high:
        return "low_intensity_high_harmony"
    elif is_int_low and is_harm_low:
        return "low_intensity_low_harmony"
    else:
        return "moderate"


def select_state_words(
    group_name: str,
    intensity: float,
    harmony: float,
    user_id: str,
    date: str,
    count: int = 2
) -> list[str]:
    """
    Select N words from the word bank for a group based on its quadrant.

    Uses reproducible randomness tied to user+date+group for consistency.

    Args:
        group_name: Group name (mind, emotions, body, spirit, growth, overall)
        intensity: Group intensity score
        harmony: Group harmony score
        user_id: User ID for reproducible selection
        date: Date string for reproducible selection
        count: Number of words to select (default 2)

    Returns:
        List of selected words as creative inspiration for LLM
    """
    import hashlib
    import random

    word_banks = load_word_banks()
    quadrant = get_quadrant(intensity, harmony)
    words = word_banks["quadrants"][quadrant].get(group_name, [])

    if not words:
        return ["shifting", "in motion"]  # fallback

    # Reproducible random selection
    seed_string = f"{user_id}:{date}:{group_name}:state_words"
    seed_hash = int(hashlib.sha256(seed_string.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed_hash)

    # Select N unique words
    selected = rng.sample(words, min(count, len(words)))
    return selected


def select_featured_meters(
    all_meters: AllMetersReading,
    user_id: str,
    date: str,
    num_groups: int = 2,
    num_meters_per_group: int = 2
) -> dict:
    """
    Select featured groups and meters for today's horoscope using weighted random.

    Higher absolute unified_score = more likely to be selected.
    This provides programmatic curation - we decide what's important, not the LLM.

    Args:
        all_meters: Complete meter readings
        user_id: User ID for reproducible selection
        date: Date string for reproducible selection
        num_groups: Number of groups to feature (default 2)
        num_meters_per_group: Number of meters per group (default 2)

    Returns:
        Dict with:
        - featured_groups: List of group names
        - featured_meters: Dict mapping group_name -> list of meter readings
        - group_words: Dict mapping group_name -> list of state word inspirations
    """
    import hashlib
    import random
    from .hierarchy import MeterGroupV2, get_meters_in_group_v2

    # Create reproducible RNG
    seed_string = f"{user_id}:{date}:featured_selection"
    seed_hash = int(hashlib.sha256(seed_string.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed_hash)

    # Calculate group scores
    group_scores = {}
    group_meters = {}

    for group in MeterGroupV2:
        meter_enums = get_meters_in_group_v2(group)
        meters_in_group = []

        for meter_enum in meter_enums:
            meter_reading = getattr(all_meters, meter_enum.value, None)
            if meter_reading:
                meters_in_group.append(meter_reading)

        if meters_in_group:
            avg_intensity = sum(m.intensity for m in meters_in_group) / len(meters_in_group)
            avg_harmony = sum(m.harmony for m in meters_in_group) / len(meters_in_group)
            unified, _ = calculate_unified_score(avg_intensity, avg_harmony)

            group_scores[group.value] = {
                "unified_score": unified,
                "intensity": avg_intensity,
                "harmony": avg_harmony,
                "weight": max(10, abs(unified))  # Use absolute score as weight, min 10
            }
            group_meters[group.value] = meters_in_group

    # Weighted random selection of groups
    groups = list(group_scores.keys())
    weights = [group_scores[g]["weight"] for g in groups]
    featured_groups = []

    for _ in range(min(num_groups, len(groups))):
        if not groups:
            break
        selected = rng.choices(groups, weights=weights, k=1)[0]
        featured_groups.append(selected)
        # Remove selected to avoid duplicates
        idx = groups.index(selected)
        groups.pop(idx)
        weights.pop(idx)

    # For each featured group, select meters with weighted random
    featured_meters = {}
    group_words = {}

    for group_name in featured_groups:
        meters = group_meters[group_name]
        meter_weights = [max(10, abs(m.unified_score)) for m in meters]

        selected_meters = []
        available_meters = list(meters)
        available_weights = list(meter_weights)

        for _ in range(min(num_meters_per_group, len(available_meters))):
            if not available_meters:
                break
            selected = rng.choices(available_meters, weights=available_weights, k=1)[0]
            selected_meters.append(selected)
            idx = available_meters.index(selected)
            available_meters.pop(idx)
            available_weights.pop(idx)

        featured_meters[group_name] = selected_meters

        # Get state words for this group
        group_data = group_scores[group_name]
        group_words[group_name] = select_state_words(
            group_name=group_name,
            intensity=group_data["intensity"],
            harmony=group_data["harmony"],
            user_id=user_id,
            date=date,
            count=2
        )

    return {
        "featured_groups": featured_groups,
        "featured_meters": featured_meters,
        "group_words": group_words,
        "group_scores": {g: group_scores[g] for g in featured_groups}
    }

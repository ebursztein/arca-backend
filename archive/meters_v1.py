"""
Meter taxonomy implementation - 23 specialized meters.

Each meter:
1. Filters aspects to relevant planets/houses
2. Calculates DTI/HQS using core algorithms
3. Normalizes to 0-100 scales
4. Generates interpretations and advice
5. Provides explainability via AspectContribution breakdown

Spec Reference: astrometers.md Section 5
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import json

# Import from existing modules
from astro import Planet, AspectType, ZodiacSign, House
from .core import (
    TransitAspect,
    AspectContribution,
    calculate_astrometers,
    AstrometerScore
)
from .normalization import (
    normalize_intensity,
    normalize_harmony,
    get_intensity_label,
    get_harmony_label
)
# Import new hierarchy system (streamlined 17-meter system)
from .hierarchy import Meter, MeterGroupV2, get_group_v2
from .constants import (
    INTENSITY_QUIET_THRESHOLD,
    INTENSITY_MILD_THRESHOLD,
    INTENSITY_MODERATE_THRESHOLD,
    INTENSITY_HIGH_THRESHOLD,
    HARMONY_CHALLENGING_THRESHOLD,
    HARMONY_HARMONIOUS_THRESHOLD
)


# ============================================================================
# Label Loading from JSON
# ============================================================================

# Cache for loaded labels
_LABEL_CACHE: Dict[str, Dict] = {}

def load_meter_labels(meter_id: str) -> Dict:
    """Load labels from JSON file for a specific meter."""
    if meter_id in _LABEL_CACHE:
        return _LABEL_CACHE[meter_id]

    labels_dir = os.path.join(os.path.dirname(__file__), "labels")
    label_file = os.path.join(labels_dir, f"{meter_id}.json")

    with open(label_file, "r") as f:
        labels = json.load(f)

    _LABEL_CACHE[meter_id] = labels
    return labels


def get_intensity_level(intensity: float) -> str:
    """Determine intensity level from score."""
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
    """Determine harmony level from score."""
    if harmony < HARMONY_CHALLENGING_THRESHOLD:
        return "challenging"
    elif harmony < HARMONY_HARMONIOUS_THRESHOLD:
        return "mixed"
    else:
        return "harmonious"


def get_state_label_from_json(meter_id: str, intensity: float, harmony: float) -> str:
    """Get state label from JSON based on intensity and harmony."""
    labels = load_meter_labels(meter_id)

    intensity_level = get_intensity_level(intensity)
    harmony_level = get_harmony_level(harmony)

    # Get from combined labels
    combined = labels["experience_labels"]["combined"]
    return combined[intensity_level][harmony_level]


def get_advice_category_from_json(meter_id: str, intensity: float, harmony: float) -> str:
    """Get advice category from JSON based on intensity and harmony."""
    labels = load_meter_labels(meter_id)

    intensity_level = get_intensity_level(intensity)
    harmony_level = get_harmony_level(harmony)

    # Get from advice templates
    advice_templates = labels["advice_templates"]
    return advice_templates[intensity_level][harmony_level]


def get_meter_description_from_json(meter_id: str) -> Dict[str, Any]:
    """Get meter description from JSON."""
    labels = load_meter_labels(meter_id)
    return labels["description"]


def apply_labels_to_reading(reading: 'MeterReading', meter_id: str) -> None:
    """
    Apply JSON labels to a MeterReading object.

    Sets:
    - state_label: from experience_labels.combined
    - interpretation: from description.overview + detailed
    - advice: list with advice category

    The advice category will be used by LLM to generate personalized advice.
    """
    # Get state label
    reading.state_label = get_state_label_from_json(
        meter_id,
        reading.intensity,
        reading.harmony
    )

    # Get description for interpretation
    description = get_meter_description_from_json(meter_id)
    reading.interpretation = f"{description['overview']} {description['detailed']}"

    # Get advice category
    advice_category = get_advice_category_from_json(
        meter_id,
        reading.intensity,
        reading.harmony
    )
    reading.advice = [f"Advice type: {advice_category}"]


# ============================================================================
# Meter Organization - Quality Labels
# ============================================================================
# Note: MeterGroupV2 enum now imported from hierarchy.py (single source of truth)


class QualityLabel(str, Enum):
    """
    Semantic quality labels for unified meter display.

    These describe the nature of astrological activity and allow
    the UI to make appropriate styling decisions (colors, icons, etc.)
    without the API prescribing specific visual treatments.
    """
    QUIET = "quiet"              # Very low intensity (< 25) - negligible activity
    PEACEFUL = "peaceful"        # Low intensity + high harmony - calm and positive
    HARMONIOUS = "harmonious"    # High harmony (≥ 70) - supportive energy
    MIXED = "mixed"              # Both supportive and challenging aspects
    CHALLENGING = "challenging"  # Low harmony (≤ 30) - difficult energy


# ============================================================================
# Unified Score Calculation
# ============================================================================

def calculate_unified_score(
    intensity: float,
    harmony: float
) -> Tuple[float, QualityLabel]:
    """
    Calculate unified score and quality label.

    Design: unified_score = intensity (bar length in UI).
    Quality label is derived from intensity + harmony combination.

    Args:
        intensity: Intensity meter (0-100) - how much is happening
        harmony: Harmony meter (0-100) - quality of what's happening

    Returns:
        Tuple of (unified_score, quality_label):
        - unified_score: Always equals intensity (bar length)
        - quality_label: QualityLabel enum based on intensity + harmony combination

    Examples:
        >>> calculate_unified_score(20, 90)
        (20, QualityLabel.QUIET)  # Low intensity = quiet

        >>> calculate_unified_score(35, 80)
        (35, QualityLabel.PEACEFUL)  # Low intensity + high harmony = peaceful

        >>> calculate_unified_score(80, 90)
        (80, QualityLabel.HARMONIOUS)  # High intensity + high harmony = harmonious

        >>> calculate_unified_score(80, 30)
        (80, QualityLabel.CHALLENGING)  # High intensity + low harmony = challenging

        >>> calculate_unified_score(70, 50)
        (70, QualityLabel.MIXED)  # Moderate intensity + moderate harmony = mixed
    """
    # Unified score equals intensity (this is the bar length in UI)
    unified_score = intensity

    # Determine quality label based on intensity + harmony combination
    if intensity < 25:
        # Very low intensity = quiet regardless of harmony
        quality = QualityLabel.QUIET
    elif intensity < 40 and harmony >= 70:
        # Low intensity + high harmony = peaceful
        quality = QualityLabel.PEACEFUL
    elif harmony >= 70:
        # High harmony = harmonious
        quality = QualityLabel.HARMONIOUS
    elif harmony <= 30:
        # Low harmony = challenging
        quality = QualityLabel.CHALLENGING
    else:
        # Everything else = mixed
        quality = QualityLabel.MIXED

    return unified_score, quality


# ============================================================================
# MeterReading Model (Spec Section 7.4.2)
# ============================================================================

class ChangeRate(str, Enum):
    """Rate of change magnitude (quantile-based from empirical analysis of 855K transitions)."""
    STABLE = "stable"      # Below 50th percentile (most common daily changes)
    SLOW = "slow"          # 50th-75th percentile (typical noticeable shifts)
    MODERATE = "moderate"  # 75th-90th percentile (clear significant changes)
    RAPID = "rapid"        # Above 90th percentile (dramatic shifts, top 10%)


class TrendDirection(str, Enum):
    """Direction of change for specific metric."""
    IMPROVING = "improving"      # Harmony: increasing (getting better)
    STABLE = "stable"            # No significant change
    WORSENING = "worsening"      # Harmony: decreasing (getting worse)
    INCREASING = "increasing"    # Intensity/Unified: going up
    DECREASING = "decreasing"    # Intensity/Unified: going down


class MetricTrend(BaseModel):
    """Trend data for a single metric (harmony, intensity, or unified_score)."""
    previous: float = Field(description="Yesterday's value")
    delta: float = Field(description="Change from yesterday (positive = increase, negative = decrease)")
    direction: TrendDirection = Field(description="Direction of change")
    change_rate: ChangeRate = Field(description="Magnitude classification")


class TrendData(BaseModel):
    """
    Complete trend analysis comparing today vs yesterday.

    Tracks all three key scores separately with metric-specific empirical thresholds
    based on analysis of 855,000 daily transitions across 2,500 diverse birth charts.

    Each metric has its own thresholds because they change at different rates:
    - Harmony changes most (quality shifts)
    - Intensity changes similarly to harmony (activity shifts)
    - Unified score changes less (it's a combined metric)
    """
    harmony: MetricTrend = Field(description="Quality trend (most meaningful for users)")
    intensity: MetricTrend = Field(description="Activity level trend")
    unified_score: MetricTrend = Field(description="Combined score trend")


# Empirically-derived thresholds for change_rate classification
# Based on quantile analysis: 50th, 75th, 90th percentiles
HARMONY_THRESHOLDS = {
    'stable': 2.0,     # < 2.0 points (50% of changes)
    'slow': 5.5,       # 2.0-5.5 points (50th-75th percentile)
    'moderate': 10.5   # 5.5-10.5 points (75th-90th percentile)
    # rapid: > 10.5 points (top 10%)
}

INTENSITY_THRESHOLDS = {
    'stable': 2.0,
    'slow': 5.0,
    'moderate': 9.5
}

UNIFIED_THRESHOLDS = {
    'stable': 0.5,
    'slow': 2.5,
    'moderate': 5.5
}


def classify_change_rate(abs_delta: float, thresholds: dict) -> ChangeRate:
    """
    Classify magnitude of change based on metric-specific thresholds.

    Args:
        abs_delta: Absolute value of change
        thresholds: Dict with 'stable', 'slow', 'moderate' keys

    Returns:
        ChangeRate enum
    """
    if abs_delta < thresholds['stable']:
        return ChangeRate.STABLE
    elif abs_delta < thresholds['slow']:
        return ChangeRate.SLOW
    elif abs_delta < thresholds['moderate']:
        return ChangeRate.MODERATE
    else:
        return ChangeRate.RAPID


class MeterReading(BaseModel):
    """Complete meter reading with unified score and explainability."""
    meter_name: str
    date: datetime

    # Organization
    group: MeterGroupV2 = Field(description="Life domain category")

    # Unified display (primary) - for single-bar UI
    unified_score: float = Field(
        ge=0, le=100,
        description="Primary display score: intensity value (bar length)"
    )
    unified_quality: QualityLabel = Field(
        description="Semantic quality label for UI styling decisions"
    )

    # Detailed breakdown (expandable)
    intensity: float = Field(ge=0, le=100, description="How much is happening")
    harmony: float = Field(ge=0, le=100, description="Quality of what's happening")
    state_label: str
    interpretation: str
    advice: List[str]
    top_aspects: List[AspectContribution]
    raw_scores: Dict[str, float]
    additional_context: Dict[str, Any] = Field(default_factory=dict)

    # Trend (optional) - set via calculate_trend() when comparing with previous day
    trend: Optional[TrendData] = Field(
        None,
        description="Complete trend analysis vs previous reading (optional, calculated on-demand)"
    )

    def calculate_trend(self, previous_reading: "MeterReading") -> TrendData:
        """
        Calculate complete trend analysis by comparing all three key scores.

        Tracks harmony (quality), intensity (activity), and unified_score (combined)
        with metric-specific empirical thresholds.

        Args:
            previous_reading: Yesterday's reading for same meter

        Returns:
            TrendData with separate trend analysis for each metric

        Example:
            >>> today.harmony = 75, yesterday.harmony = 60
            >>> trend = today.calculate_trend(yesterday)
            >>> trend.harmony.direction  # TrendDirection.IMPROVING
            >>> trend.harmony.change_rate  # ChangeRate.MODERATE (delta=15)
        """
        # Harmony trend (quality)
        harmony_delta = self.harmony - previous_reading.harmony
        harmony_abs = abs(harmony_delta)
        harmony_direction = (
            TrendDirection.IMPROVING if harmony_delta >= 2.0
            else TrendDirection.WORSENING if harmony_delta <= -2.0
            else TrendDirection.STABLE
        )
        harmony_rate = classify_change_rate(harmony_abs, HARMONY_THRESHOLDS)

        # Intensity trend (activity)
        intensity_delta = self.intensity - previous_reading.intensity
        intensity_abs = abs(intensity_delta)
        intensity_direction = (
            TrendDirection.INCREASING if intensity_delta >= 2.0
            else TrendDirection.DECREASING if intensity_delta <= -2.0
            else TrendDirection.STABLE
        )
        intensity_rate = classify_change_rate(intensity_abs, INTENSITY_THRESHOLDS)

        # Unified score trend (combined)
        unified_delta = self.unified_score - previous_reading.unified_score
        unified_abs = abs(unified_delta)
        unified_direction = (
            TrendDirection.INCREASING if unified_delta >= 0.5
            else TrendDirection.DECREASING if unified_delta <= -0.5
            else TrendDirection.STABLE
        )
        unified_rate = classify_change_rate(unified_abs, UNIFIED_THRESHOLDS)

        return TrendData(
            harmony=MetricTrend(
                previous=previous_reading.harmony,
                delta=harmony_delta,
                direction=harmony_direction,
                change_rate=harmony_rate
            ),
            intensity=MetricTrend(
                previous=previous_reading.intensity,
                delta=intensity_delta,
                direction=intensity_direction,
                change_rate=intensity_rate
            ),
            unified_score=MetricTrend(
                previous=previous_reading.unified_score,
                delta=unified_delta,
                direction=unified_direction,
                change_rate=unified_rate
            )
        )


class KeyAspect(BaseModel):
    """
    Major transit aspect appearing across multiple meters.

    This deduplicates aspects that affect multiple life domains,
    showing users which transits are driving their overall day.
    """
    aspect: AspectContribution
    affected_meters: List[str] = Field(description="Meter names where this aspect appears")
    meter_count: int = Field(description="Number of meters affected")

    @property
    def description(self) -> str:
        """Generate human-readable description."""
        return (
            f"Transit {self.aspect.transit_planet.value.title()} "
            f"{self.aspect.aspect_type.value} "
            f"Natal {self.aspect.natal_planet.value.title()}"
        )


# ============================================================================
# Planetary Motion Constants
# ============================================================================

# Average daily motion in degrees (approximate)
PLANET_DAILY_MOTION = {
    Planet.MOON: 13.0,
    Planet.SUN: 1.0,
    Planet.MERCURY: 1.5,
    Planet.VENUS: 1.2,
    Planet.MARS: 0.5,
    Planet.JUPITER: 0.08,
    Planet.SATURN: 0.03,
    Planet.URANUS: 0.01,
    Planet.NEPTUNE: 0.006,
    Planet.PLUTO: 0.004,
    Planet.NORTH_NODE: -0.05,  # Moves backward
}


def calculate_tomorrow_orb(
    aspect_orb: float,
    aspect_applying: bool,
    transit_planet: Planet,
    transit_planet_rx: bool = False
) -> float:
    """
    Calculate expected orb deviation tomorrow based on planetary velocity.

    Planets move at vastly different speeds (Moon: 13°/day, Saturn: 0.03°/day).
    This function uses actual velocities instead of a fixed 0.2° assumption.

    Args:
        aspect_orb: Current orb deviation in degrees
        aspect_applying: Is the aspect applying (moving toward exact)?
        transit_planet: The transiting planet
        transit_planet_rx: Is the transit planet retrograde?

    Returns:
        float: Expected orb tomorrow
    """
    base_speed = PLANET_DAILY_MOTION.get(transit_planet, 0.5)

    # Retrograde reduces speed by ~40% on average
    if transit_planet_rx:
        base_speed *= 0.6

    if aspect_applying:
        # Moving toward exact - orb decreases
        tomorrow_orb = max(0.0, aspect_orb - base_speed)
    else:
        # Moving away from exact - orb increases
        tomorrow_orb = aspect_orb + base_speed

    return tomorrow_orb


# ============================================================================
# Helper Functions
# ============================================================================

def filter_aspects_by_natal_planet(
    aspects: List[TransitAspect],
    planets: List[Planet]
) -> List[TransitAspect]:
    """Filter aspects to specific natal planets."""
    return [a for a in aspects if a.natal_planet in planets]


def filter_aspects_by_transit_planet(
    aspects: List[TransitAspect],
    planets: List[Planet]
) -> List[TransitAspect]:
    """Filter aspects to specific transit planets."""
    return [a for a in aspects if a.transit_planet in planets]


def filter_aspects_by_natal_house(
    aspects: List[TransitAspect],
    houses: List[int]
) -> List[TransitAspect]:
    """Filter aspects to planets in specific natal houses."""
    return [a for a in aspects if a.natal_house in houses]


def filter_hard_aspects(aspects: List[TransitAspect]) -> List[TransitAspect]:
    """Filter to hard aspects only (square, opposition)."""
    hard = [AspectType.SQUARE, AspectType.OPPOSITION]
    return [a for a in aspects if a.aspect_type in hard]


def filter_soft_aspects(aspects: List[TransitAspect]) -> List[TransitAspect]:
    """Filter to soft aspects only (trine, sextile)."""
    soft = [AspectType.TRINE, AspectType.SEXTILE]
    return [a for a in aspects if a.aspect_type in soft]


def apply_retrograde_modifier(
    reading: MeterReading,
    transit_chart: dict,
    planet: Planet,
    harmony_multiplier: float = 0.7,
    note: str = None
) -> MeterReading:
    """
    Apply retrograde modifier to a meter reading.

    When a planet is retrograde, its energy is internalized, delayed, or requires
    extra patience. This typically reduces harmony (increases friction) but doesn't
    change intensity.

    Args:
        reading: MeterReading to modify
        transit_chart: Transit chart with planetary data
        planet: Planet to check for retrograde
        harmony_multiplier: How much to reduce harmony (default 0.7 = 30% reduction)
        note: Custom note to append to interpretation (uses default if None)

    Returns:
        Modified MeterReading (modifies in place and returns for chaining)
    """
    planet_data = next(
        (p for p in transit_chart["planets"] if p["name"] == planet),
        None
    )

    if planet_data and planet_data.get("retrograde", False):
        reading.harmony *= harmony_multiplier
        reading.additional_context[f"{planet.value}_retrograde"] = True

        default_note = f"\n\nNote: {planet.value.title()} is retrograde - themes are internalized or delayed."
        reading.interpretation += note or default_note

    return reading


def calculate_meter_score(
    aspects: List[TransitAspect],
    meter_name: str,
    date: datetime,
    group: MeterGroupV2
) -> MeterReading:
    """
    Generic meter calculation function.

    Uses existing calculate_astrometers() from core.py
    Returns MeterReading with all fields populated including unified score

    Args:
        aspects: List of transit aspects to analyze
        meter_name: Name of the meter
        date: Date of reading
        group: MeterGroupV2 for dashboard organization
    """
    if not aspects:
        # Empty case: no activity
        unified_score, unified_quality = calculate_unified_score(0.0, 50.0)
        return MeterReading(
            meter_name=meter_name,
            date=date,
            group=group,
            unified_score=unified_score,
            unified_quality=unified_quality,
            intensity=0.0,
            harmony=50.0,
            state_label="Quiet",
            interpretation=f"No significant astrological activity for {meter_name}.",
            advice=["Normal baseline period - routine operations"],
            top_aspects=[],
            raw_scores={"dti": 0.0, "hqs": 0.0}
        )

    # Calculate using core algorithm
    score = calculate_astrometers(aspects)

    # Normalize with meter-specific calibration
    intensity = normalize_intensity(score.dti, meter_name=meter_name)
    harmony = normalize_harmony(score.hqs, meter_name=meter_name)

    # Calculate unified score
    unified_score, unified_quality = calculate_unified_score(intensity, harmony)

    # Get labels
    intensity_label = get_intensity_label(intensity)
    harmony_label = get_harmony_label(harmony)
    state_label = f"{intensity_label} + {harmony_label}"

    # Sort by contribution
    top_aspects = sorted(
        score.contributions,
        key=lambda a: abs(a.dti_contribution),
        reverse=True
    )[:5]

    return MeterReading(
        meter_name=meter_name,
        date=date,
        group=group,
        unified_score=unified_score,
        unified_quality=unified_quality,
        intensity=intensity,
        harmony=harmony,
        state_label=state_label,
        interpretation="",  # Filled by specific meter function
        advice=[],  # Filled by specific meter function
        top_aspects=top_aspects,
        raw_scores={"dti": score.dti, "hqs": score.hqs}
    )


# ============================================================================
# GLOBAL METERS (Spec Section 5.2)
# ============================================================================

def calculate_overall_intensity_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Overall Intensity Gauge - measures total astrological activity.

    Spec: Section 5.2.1
    Formula: Total DTI across all transits
    """
    reading = calculate_meter_score(all_aspects, "overall_intensity", date, MeterGroupV2.MIND)

    # Apply labels from JSON
    apply_labels_to_reading(reading, "overall_intensity")

    # Add top contributors
    if reading.top_aspects:
        top_3 = reading.top_aspects[:3]
        contrib_text = "\n\nTop contributing aspects:\n"
        for aspect in top_3:
            contrib_text += f"• {aspect.label} (DTI: {aspect.dti_contribution:.1f})\n"
        reading.interpretation += contrib_text

    return reading


def calculate_overall_harmony_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Overall Harmony Meter - measures net supportive vs challenging quality.

    Spec: Section 5.2.2
    Formula: Total HQS across all transits
    Scale: 0-100 where 50 is neutral
    """
    reading = calculate_meter_score(all_aspects, "overall_harmony", date, MeterGroupV2.MIND)

    # Count supportive vs challenging aspects
    supportive = sum(1 for a in reading.top_aspects if a.quality_factor > 0)
    challenging = sum(1 for a in reading.top_aspects if a.quality_factor < 0)
    neutral = sum(1 for a in reading.top_aspects if a.quality_factor == 0)

    reading.additional_context = {
        "supportive_count": supportive,
        "challenging_count": challenging,
        "neutral_count": neutral
    }

    # Apply labels from JSON
    apply_labels_to_reading(reading, "overall_harmony")

    # Add breakdown
    breakdown = f"\n\nAspect breakdown: {supportive} supportive, {challenging} challenging, {neutral} neutral"
    reading.interpretation += breakdown

    return reading


# ============================================================================
# COGNITIVE METERS (Spec Section 5.4)
# ============================================================================

def calculate_mental_clarity_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    transit_chart: dict
) -> MeterReading:
    """
    Mental Clarity Meter - ease of thinking, concentration, mental processing.

    Spec: Section 5.4.1
    Primary: All aspects to natal Mercury + 3rd house
    Transit filter: ONLY fast-moving transits (Mercury/Venus/Mars) = daily thinking
    Modifier: Mercury retrograde (×0.6 to clarity)
    Note: Separated from innovation_breakthrough by using fast transits vs Uranus transits
    """
    # Filter to Mercury aspects + 3rd house
    mercury_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.MERCURY])
    third_house = filter_aspects_by_natal_house(all_aspects, [3])
    combined = mercury_aspects + third_house

    # Filter to fast-moving transits only (daily thinking, not breakthrough moments)
    fast_transits = [Planet.MERCURY, Planet.VENUS, Planet.MARS]
    filtered_clarity = filter_aspects_by_transit_planet(combined, fast_transits)

    reading = calculate_meter_score(filtered_clarity, "mental_clarity", date, MeterGroupV2.MIND)

    # Apply Mercury retrograde modifier (affects harmony calculation)
    mercury_data = next(
        (p for p in transit_chart["planets"] if p["name"] == Planet.MERCURY),
        None
    )
    if mercury_data and mercury_data.get("retrograde", False):
        reading.harmony *= 0.6
        reading.additional_context["mercury_retrograde"] = True

    # Apply labels from JSON
    apply_labels_to_reading(reading, "mental_clarity")

    # Add retrograde note if applicable (after interpretation is set)
    if reading.additional_context.get("mercury_retrograde", False):
        reading.interpretation += "\n\nNote: Mercury is retrograde, adding review, revision, and reconsideration themes."

    return reading


def calculate_decision_quality_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Decision Quality Meter - wisdom, judgment, strategic thinking.

    Spec: Section 5.4.2
    Planets: Jupiter (wisdom), Saturn (discernment), Neptune (intuition vs confusion)
    Note: Mercury removed - mental_clarity handles thinking speed, this meter handles wisdom
    """
    decision_planets = [Planet.JUPITER, Planet.SATURN, Planet.NEPTUNE]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, decision_planets)

    reading = calculate_meter_score(filtered_aspects, "decision_quality", date, MeterGroupV2.MIND)


    # Apply labels from JSON
    apply_labels_to_reading(reading, "decision_quality")

    return reading


def calculate_communication_flow_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Communication Flow Meter - expression, connection, being heard.

    Spec: Section 5.4.3
    Planets: Mercury (words), Venus (diplomacy), Mars (directness)
    """
    comm_planets = [Planet.MERCURY, Planet.VENUS, Planet.MARS]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, comm_planets)

    reading = calculate_meter_score(filtered_aspects, "communication_flow", date, MeterGroupV2.MIND)


    # Apply labels from JSON
    apply_labels_to_reading(reading, "communication_flow")

    return reading


# ============================================================================
# EMOTIONAL METERS (Spec Section 5.5)
# ============================================================================

def calculate_emotional_intensity_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Emotional Intensity Meter - depth of feeling, emotional activation.

    Spec: Section 5.5.1
    Planets: Moon (emotions), Venus (affection), Pluto (depth)
    Note: Neptune removed - it's spiritual/mystical, not emotional. Moved to intuition_spirituality
    """
    emotion_planets = [Planet.MOON, Planet.VENUS, Planet.PLUTO]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, emotion_planets)

    reading = calculate_meter_score(filtered_aspects, "emotional_intensity", date, MeterGroupV2.EMOTIONS)


    # Apply labels from JSON
    apply_labels_to_reading(reading, "emotional_intensity")

    return reading


def calculate_relationship_harmony_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    transit_chart: dict
) -> MeterReading:
    """
    Relationship Harmony Meter - connection quality, partnership dynamics.

    Spec: Section 5.5.2
    Primary: Venus aspects + 7th house transits
    Modifier: Venus retrograde (relationships require extra patience)
    """
    # Venus aspects
    venus_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.VENUS])
    # 7th house planets
    seventh_house = filter_aspects_by_natal_house(all_aspects, [7])
    # Combine (simple concatenation - duplicates don't matter for scoring)
    combined = venus_aspects + seventh_house

    reading = calculate_meter_score(combined, "relationship_harmony", date, MeterGroupV2.EMOTIONS)

    # Apply Venus retrograde modifier (affects harmony calculation)
    venus_data = next(
        (p for p in transit_chart["planets"] if p["name"] == Planet.VENUS),
        None
    )
    if venus_data and venus_data.get("retrograde", False):
        reading.harmony *= 0.7
        reading.additional_context["venus_retrograde"] = True


    # Apply labels from JSON
    apply_labels_to_reading(reading, "relationship_harmony")

    # Add retrograde note if applicable (after interpretation is set)
    if reading.additional_context.get("venus_retrograde", False):
        reading.interpretation += "\n\nNote: Venus retrograde - relationships require extra patience and reflection."

    return reading


def calculate_emotional_resilience_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Emotional Resilience Meter - capacity to handle stress, emotional stability.

    Spec: Section 5.5.3
    Focus: Moon (emotional nature) + Saturn (emotional structure) + 4th house (foundation)

    Rationale: Emotional resilience is specifically about emotional regulation and stress.
    Moon = core emotional response patterns
    Saturn = discipline, boundaries, stress management
    4th house = emotional foundation, security needs, family patterns
    """
    resilience_planets = [Planet.MOON, Planet.SATURN]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, resilience_planets)

    # Add 4th house (emotional foundation)
    fourth_house = filter_aspects_by_natal_house(all_aspects, [4])

    # Combine
    combined = filtered_aspects + fourth_house

    reading = calculate_meter_score(combined, "emotional_resilience", date, MeterGroupV2.EMOTIONS)

    # Apply labels from JSON
    apply_labels_to_reading(reading, "emotional_resilience")

    return reading


# ============================================================================
# PHYSICAL/ACTION METERS (Spec Section 5.6)
# ============================================================================

def calculate_physical_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    transit_chart: dict
) -> MeterReading:
    """
    Physical Energy Meter - vitality, stamina, body energy.

    Spec: Section 5.6.1
    Planets: Sun (vitality) + Mars (action)
    Modifier: Mars retrograde (energy may feel blocked or require strategic direction)
    """
    energy_planets = [Planet.SUN, Planet.MARS]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, energy_planets)

    reading = calculate_meter_score(filtered_aspects, "physical_energy", date, MeterGroupV2.BODY)

    # Apply Mars retrograde modifier (affects harmony calculation)
    mars_data = next(
        (p for p in transit_chart["planets"] if p["name"] == Planet.MARS),
        None
    )
    if mars_data and mars_data.get("retrograde", False):
        reading.harmony *= 0.65  # Mars Rx feels more frustrating
        reading.additional_context["mars_retrograde"] = True


    # Apply labels from JSON
    apply_labels_to_reading(reading, "physical_energy")

    # Add retrograde note if applicable (after interpretation is set)
    if reading.additional_context.get("mars_retrograde", False):
        reading.interpretation += "\n\nNote: Mars retrograde - energy may feel blocked or require strategic direction."

    return reading


def calculate_conflict_risk_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    transit_chart: dict
) -> MeterReading:
    """
    Conflict Risk Meter - direct confrontations, power struggles, external conflicts.

    Spec: Section 5.6.2
    Focus: OPPOSITIONS ONLY from Mars/Pluto/Saturn transits to Mars/Pluto natal
    Modifier: Mars retrograde (anger may be internalized or passive-aggressive)

    Rationale:
    - Oppositions = external, direct confrontations (not internal friction)
    - Natal Mars/Pluto = confrontation nature
    - Transit Mars/Pluto/Saturn = active conflict triggers
    - Mars-Pluto oppositions = power struggles
    - Mars-Mars oppositions = direct clashes
    - Saturn oppositions = obstacles from authority/structure
    """
    # Filter by natal planets: Mars, Pluto (confrontation nature)
    natal_conflict = [Planet.MARS, Planet.PLUTO]
    filtered_natal = filter_aspects_by_natal_planet(all_aspects, natal_conflict)

    # Filter by transit planets: Mars, Pluto, Saturn (active triggers)
    transit_conflict = [Planet.MARS, Planet.PLUTO, Planet.SATURN]
    filtered_transit = filter_aspects_by_transit_planet(filtered_natal, transit_conflict)

    # Filter to oppositions only (external conflicts)
    oppositions = [a for a in filtered_transit if a.aspect_type == AspectType.OPPOSITION]

    reading = calculate_meter_score(oppositions, "conflict_risk", date, MeterGroupV2.BODY)

    # Apply Mars retrograde modifier (affects harmony calculation)
    mars_data = next(
        (p for p in transit_chart["planets"] if p["name"] == Planet.MARS),
        None
    )
    if mars_data and mars_data.get("retrograde", False):
        reading.harmony *= 0.65
        reading.additional_context["mars_retrograde"] = True

    # Apply labels from JSON
    apply_labels_to_reading(reading, "conflict_risk")

    # Add retrograde note if applicable (after interpretation is set)
    if reading.additional_context.get("mars_retrograde", False):
        reading.interpretation += "\n\nNote: Mars retrograde - anger may be internalized or express as passive-aggression."

    return reading


def calculate_motivation_drive_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    transit_chart: dict
) -> MeterReading:
    """
    Motivation Drive Meter - ambition, initiative, pushing forward.

    Spec: Section 5.6.3
    Planets: Mars (drive), Jupiter (expansion/enthusiasm)
    Modifier: Mars retrograde (drive may feel stalled or require redirection)
    Note: Saturn removed - discipline/structure belongs in decision_quality, not motivation
    """
    motivation_planets = [Planet.MARS, Planet.JUPITER]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, motivation_planets)

    reading = calculate_meter_score(filtered_aspects, "motivation_drive", date, MeterGroupV2.BODY)

    # Apply Mars retrograde modifier (affects harmony calculation)
    mars_data = next(
        (p for p in transit_chart["planets"] if p["name"] == Planet.MARS),
        None
    )
    if mars_data and mars_data.get("retrograde", False):
        reading.harmony *= 0.65
        reading.additional_context["mars_retrograde"] = True


    # Apply labels from JSON
    apply_labels_to_reading(reading, "motivation_drive")

    # Add retrograde note if applicable (after interpretation is set)
    if reading.additional_context.get("mars_retrograde", False):
        reading.interpretation += "\n\nNote: Mars retrograde - drive may feel stalled or require redirection."

    return reading


# ============================================================================
# LIFE DOMAIN METERS (Spec Section 5.7)
# ============================================================================

def calculate_career_ambition_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    transit_chart: dict
) -> MeterReading:
    """
    Career Ambition Meter - professional drive, status-seeking, public recognition.

    Spec: Section 5.7.1
    Focus: 10th house planets, but ONLY transiting Saturn/Mars/Sun

    Rationale: 10th house = Midheaven, career, public life, professional reputation
    Transit filter prevents overlap with opportunity_window (Jupiter):
    - Transit Saturn = career structure, ambition, achievement
    - Transit Mars = career drive, action, competition
    - Transit Sun = career recognition, visibility, leadership

    Note: Separated from opportunity_window (which uses Jupiter for general luck/expansion).
    """
    # 10th house (career/public status arena)
    tenth_house = filter_aspects_by_natal_house(all_aspects, [10])

    # Filter by transiting Saturn/Mars/Sun only (career-specific transits)
    career_transits = [Planet.SATURN, Planet.MARS, Planet.SUN]
    filtered_career = filter_aspects_by_transit_planet(tenth_house, career_transits)

    reading = calculate_meter_score(filtered_career, "career_ambition", date, MeterGroupV2.GROWTH)

    # Apply Saturn retrograde modifier
    saturn_data = next((p for p in transit_chart.get("planets", []) if p["name"] == Planet.SATURN), None)
    if saturn_data and saturn_data.get("retrograde", False):
        reading.harmony *= 0.70  # Saturn Rx delays career progress
        reading.additional_context["saturn_retrograde"] = True

    # Apply labels from JSON
    apply_labels_to_reading(reading, "career_ambition")

    # Add retrograde note if applicable (after interpretation is set)
    if reading.additional_context.get("saturn_retrograde", False):
        reading.interpretation += "\n\nNote: Saturn is retrograde - career progress may feel delayed or require internal restructuring."

    return reading


def calculate_opportunity_window_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    transit_chart: dict
) -> MeterReading:
    """
    Opportunity Window Meter - luck, expansion, doors opening.

    Spec: Section 5.7.2
    Focus: Jupiter aspects (the Great Benefic)
    Modifier: Jupiter retrograde (opportunities are internalized or require inner work)
    """
    jupiter_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.JUPITER])

    reading = calculate_meter_score(jupiter_aspects, "opportunity_window", date, MeterGroupV2.GROWTH)

    # Apply Jupiter retrograde modifier (affects harmony calculation)
    jupiter_data = next(
        (p for p in transit_chart["planets"] if p["name"] == Planet.JUPITER),
        None
    )
    if jupiter_data and jupiter_data.get("retrograde", False):
        reading.harmony *= 0.7
        reading.additional_context["jupiter_retrograde"] = True


    # Apply labels from JSON
    apply_labels_to_reading(reading, "opportunity_window")

    # Add retrograde note if applicable (after interpretation is set)
    if reading.additional_context.get("jupiter_retrograde", False):
        reading.interpretation += "\n\nNote: Jupiter retrograde - opportunities are internalized or require inner work first."

    return reading


def calculate_challenge_intensity_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Challenge Intensity Meter - growth challenges, internal friction, tests requiring action.

    Spec: Section 5.7.3
    Focus: SQUARES ONLY from Saturn/Uranus/Pluto transits to Saturn/Mars natal

    Rationale:
    - Squares = internal friction, challenges requiring action (not external conflict)
    - Natal Saturn/Mars = areas of hardship and frustration
    - Transit Saturn/Uranus/Pluto = outer planet pressure for growth
    - Saturn squares = structural tests, limits
    - Uranus squares = disruption, forced change
    - Pluto squares = transformation pressure, death/rebirth
    """
    # Filter by natal planets: Saturn, Mars (hardship + frustration)
    natal_challenge = [Planet.SATURN, Planet.MARS]
    filtered_natal = filter_aspects_by_natal_planet(all_aspects, natal_challenge)

    # Filter by transit planets: Saturn, Uranus, Pluto (outer planet pressure)
    transit_challenge = [Planet.SATURN, Planet.URANUS, Planet.PLUTO]
    filtered_transit = filter_aspects_by_transit_planet(filtered_natal, transit_challenge)

    # Filter to squares only (internal friction)
    squares = [a for a in filtered_transit if a.aspect_type == AspectType.SQUARE]

    reading = calculate_meter_score(squares, "challenge_intensity", date, MeterGroupV2.GROWTH)

    # Apply labels from JSON
    apply_labels_to_reading(reading, "challenge_intensity")

    return reading


def calculate_transformation_pressure_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Transformation Pressure Meter - evolutionary push, metamorphosis.

    Spec: Section 5.7.4
    Focus: Pluto, Uranus, Neptune (agents of transformation)
    """
    transform_planets = [Planet.PLUTO, Planet.URANUS, Planet.NEPTUNE]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, transform_planets)

    reading = calculate_meter_score(filtered_aspects, "transformation_pressure", date, MeterGroupV2.GROWTH)


    # Apply labels from JSON
    apply_labels_to_reading(reading, "transformation_pressure")

    return reading


# ============================================================================
# ELEMENT METERS (Spec Section 5.3)
# ============================================================================

def get_sign_strength(degree_in_sign: float) -> float:
    """
    Calculate planet strength based on position in sign.

    Planets are stronger in the middle of a sign (15°) and weaker
    at the boundaries (0° and 29°). This reflects the concept that
    a planet just entering or leaving a sign is less established.

    Args:
        degree_in_sign: Position within sign (0-29.999°)

    Returns:
        float: Strength multiplier (0.7 to 1.0)
              - 1.0 at 15° (center of sign)
              - 0.7 at 0° or 29° (boundaries)

    Example:
        >>> get_sign_strength(15.0)  # Center
        1.0
        >>> get_sign_strength(0.0)   # Just entered
        0.7
        >>> get_sign_strength(29.0)  # About to leave
        0.72
    """
    # Simple parabolic curve: strongest at 15° (middle)
    distance_from_center = abs(degree_in_sign - 15.0)
    strength = 1.0 - (distance_from_center / 15.0) * 0.3  # 70-100% strength
    return max(0.7, min(1.0, strength))


def calculate_element_distribution(
    natal_chart: dict,
    transit_chart: dict
) -> Dict[str, float]:
    """
    Calculate element distribution (blend of natal + transit).

    Spec: Section 5.3
    Formula: 70% natal baseline + 30% current transits

    Enhancement: Weights planets by their position in sign.
    A planet at 15° (middle of sign) has full strength (1.0).
    A planet at 0° or 29° (boundaries) has reduced strength (0.7).

    Returns: {fire: %, earth: %, air: %, water: %}
    """
    # Count planets by element in natal chart (weighted by sign position)
    natal_elements = {"fire": 0.0, "earth": 0.0, "air": 0.0, "water": 0.0}
    for planet in natal_chart.get("planets", []):
        element = planet.get("element")
        if element and element in natal_elements:
            degree = planet.get("degree_in_sign", 15.0)  # Default to mid-sign
            weight = get_sign_strength(degree)
            natal_elements[element] += weight

    # Count planets by element in transit chart (weighted by sign position)
    transit_elements = {"fire": 0.0, "earth": 0.0, "air": 0.0, "water": 0.0}
    for planet in transit_chart.get("planets", []):
        element = planet.get("element")
        if element and element in transit_elements:
            degree = planet.get("degree_in_sign", 15.0)  # Default to mid-sign
            weight = get_sign_strength(degree)
            transit_elements[element] += weight

    # Calculate percentages (70% natal, 30% transit)
    total_natal = sum(natal_elements.values())
    total_transit = sum(transit_elements.values())
    blended = {}
    for elem in ["fire", "earth", "air", "water"]:
        natal_pct = (natal_elements[elem] / total_natal * 100) if total_natal > 0 else 25.0
        transit_pct = (transit_elements[elem] / total_transit * 100) if total_transit > 0 else 25.0
        blended[elem] = (0.7 * natal_pct) + (0.3 * transit_pct)

    return blended


def calculate_fire_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    element_dist: Dict[str, float]
) -> MeterReading:
    """
    Fire Energy Meter - initiative, enthusiasm, action, passion.

    Spec: Section 5.3.1
    Fire signs: Aries, Leo, Sagittarius
    Fire planets: Sun, Mars, Jupiter
    """
    fire_planets = [Planet.SUN, Planet.MARS, Planet.JUPITER]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, fire_planets)

    reading = calculate_meter_score(filtered_aspects, "fire_energy", date, MeterGroupV2.SPIRIT)

    fire_pct = element_dist.get("fire", 25.0)
    reading.additional_context["fire_percentage"] = fire_pct

    # Adjust interpretation based on element balance
    if fire_pct > 35:
        emphasis = "Fire is naturally strong in your chart."
    elif fire_pct < 15:
        emphasis = "Fire is naturally weak in your chart - transits may feel more impactful."
    else:
        emphasis = "Fire is balanced in your chart."


    # Apply labels from JSON
    apply_labels_to_reading(reading, "fire_energy")

    return reading


def calculate_earth_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    element_dist: Dict[str, float]
) -> MeterReading:
    """
    Earth Energy Meter - stability, practicality, grounding, material world.

    Spec: Section 5.3.2
    Earth signs: Taurus, Virgo, Capricorn
    Earth planets: Venus, Mercury (Virgo), Saturn
    """
    earth_planets = [Planet.VENUS, Planet.SATURN]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, earth_planets)

    reading = calculate_meter_score(filtered_aspects, "earth_energy", date, MeterGroupV2.SPIRIT)

    earth_pct = element_dist.get("earth", 25.0)
    reading.additional_context["earth_percentage"] = earth_pct

    if earth_pct > 35:
        emphasis = "Earth is naturally strong in your chart."
    elif earth_pct < 15:
        emphasis = "Earth is naturally weak in your chart - grounding may require extra attention."
    else:
        emphasis = "Earth is balanced in your chart."


    # Apply labels from JSON
    apply_labels_to_reading(reading, "earth_energy")

    return reading


def calculate_air_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    element_dist: Dict[str, float]
) -> MeterReading:
    """
    Air Energy Meter - communication, ideas, logic, connection.

    Spec: Section 5.3.3
    Air signs: Gemini, Libra, Aquarius
    Air planets: Mercury, Venus (Libra), Uranus
    """
    air_planets = [Planet.MERCURY, Planet.URANUS]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, air_planets)

    reading = calculate_meter_score(filtered_aspects, "air_energy", date, MeterGroupV2.SPIRIT)

    air_pct = element_dist.get("air", 25.0)
    reading.additional_context["air_percentage"] = air_pct

    if air_pct > 35:
        emphasis = "Air is naturally strong in your chart."
    elif air_pct < 15:
        emphasis = "Air is naturally weak in your chart - mental activity may feel amplified."
    else:
        emphasis = "Air is balanced in your chart."


    # Apply labels from JSON
    apply_labels_to_reading(reading, "air_energy")

    return reading


def calculate_water_energy_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    element_dist: Dict[str, float]
) -> MeterReading:
    """
    Water Energy Meter - emotion, intuition, empathy, spirituality.

    Spec: Section 5.3.4
    Water signs: Cancer, Scorpio, Pisces
    Water planets: Moon, Pluto, Neptune
    """
    water_planets = [Planet.MOON, Planet.PLUTO, Planet.NEPTUNE]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, water_planets)

    reading = calculate_meter_score(filtered_aspects, "water_energy", date, MeterGroupV2.SPIRIT)

    water_pct = element_dist.get("water", 25.0)
    reading.additional_context["water_percentage"] = water_pct

    if water_pct > 35:
        emphasis = "Water is naturally strong in your chart."
    elif water_pct < 15:
        emphasis = "Water is naturally weak in your chart - emotional themes may feel more intense."
    else:
        emphasis = "Water is balanced in your chart."


    # Apply labels from JSON
    apply_labels_to_reading(reading, "water_energy")

    return reading


# ============================================================================
# SPECIALIZED METERS (Spec Section 5.8)
# ============================================================================

def calculate_intuition_spirituality_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Intuition/Spirituality Meter - psychic sensitivity, spiritual connection.

    Spec: Section 5.8.1
    Focus: Neptune + Moon + 12th house
    """
    spirit_planets = [Planet.NEPTUNE, Planet.MOON]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, spirit_planets)
    twelfth_house = filter_aspects_by_natal_house(all_aspects, [12])
    combined = filtered_aspects + twelfth_house

    reading = calculate_meter_score(combined, "intuition_spirituality", date, MeterGroupV2.SPIRIT)


    # Apply labels from JSON
    apply_labels_to_reading(reading, "intuition_spirituality")

    return reading


def calculate_innovation_breakthrough_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Innovation/Breakthrough Meter - eureka moments, revolutionary thinking, sudden insights.

    Spec: Section 5.8.2
    Focus: Uranus + Mercury natal, but ONLY transiting Uranus
    Transit filter: ONLY Uranus transits = breakthrough moments (not daily thinking)

    Rationale: Mercury-Uranus aspects represent breakthrough ideas and "aha!" moments,
    but only when Uranus is transiting (sudden paradigm shifts).
    Note: Separated from mental_clarity by using Uranus transits vs fast transits
    """
    innovation_planets = [Planet.URANUS, Planet.MERCURY]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, innovation_planets)

    # Filter to Uranus transits only (breakthrough moments, not daily thinking)
    uranus_transits = filter_aspects_by_transit_planet(filtered_aspects, [Planet.URANUS])

    reading = calculate_meter_score(uranus_transits, "innovation_breakthrough", date, MeterGroupV2.GROWTH)

    # Apply labels from JSON
    apply_labels_to_reading(reading, "innovation_breakthrough")

    return reading


def calculate_karmic_lessons_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Karmic Lessons Meter - soul growth, destiny themes, spiritual evolution.

    Spec: Section 5.8.3
    Focus: Saturn (the Teacher) + North Node (destiny) + 12th house (karma/past life)

    Rationale: ALL aspects matter for karmic lessons (not just hard ones).
    12th house = karma, past life patterns, hidden spiritual themes.
    """
    karmic_planets = [Planet.SATURN, Planet.NORTH_NODE]
    filtered_aspects = filter_aspects_by_natal_planet(all_aspects, karmic_planets)

    # KEY CHANGE: Add 12th house planets for distinctiveness
    twelfth_house = filter_aspects_by_natal_house(all_aspects, [12])

    # Combine (simple concatenation - duplicates handled by scoring algorithm)
    combined = filtered_aspects + twelfth_house

    reading = calculate_meter_score(combined, "karmic_lessons", date, MeterGroupV2.SPIRIT)

    # Apply labels from JSON
    apply_labels_to_reading(reading, "karmic_lessons")

    return reading


def calculate_social_collective_meter(
    all_aspects: List[TransitAspect],
    date: datetime
) -> MeterReading:
    """
    Social/Collective Energy Meter - community, society, collective themes.

    Spec: Section 5.8.4
    Focus: Outer planets (Uranus, Neptune, Pluto) + 11th house
    """
    collective_planets = [Planet.URANUS, Planet.NEPTUNE, Planet.PLUTO]
    filtered_aspects = filter_aspects_by_transit_planet(all_aspects, collective_planets)
    eleventh_house = filter_aspects_by_natal_house(all_aspects, [11])
    combined = filtered_aspects + eleventh_house

    reading = calculate_meter_score(combined, "social_collective", date, MeterGroupV2.GROWTH)


    # Apply labels from JSON
    apply_labels_to_reading(reading, "social_collective")

    return reading


# ============================================================================
# Master Function: Get All Meters
# ============================================================================

def convert_to_transit_aspects(
    natal_chart: dict,
    transit_chart: dict,
    natal_transit_aspects: list
) -> List[TransitAspect]:
    """
    Convert NatalTransitAspect objects to TransitAspect format.

    Maps data from astro.find_natal_transit_aspects() to format
    expected by astrometers.core algorithms.
    """
    transit_aspects = []

    for aspect in natal_transit_aspects:
        # Get natal planet data
        natal_planet_data = next(
            (p for p in natal_chart["planets"] if p["name"] == aspect.natal_planet),
            None
        )
        if not natal_planet_data:
            continue

        # Get transit planet data
        transit_planet_data = next(
            (p for p in transit_chart["planets"] if p["name"] == aspect.transit_planet),
            None
        )
        if not transit_planet_data:
            continue

        # Determine max orb based on aspect type (from constants)
        max_orb_map = {
            AspectType.CONJUNCTION: 8.0,
            AspectType.OPPOSITION: 8.0,
            AspectType.TRINE: 8.0,
            AspectType.SQUARE: 7.0,
            AspectType.SEXTILE: 6.0,
        }
        max_orb = max_orb_map.get(aspect.aspect_type, 8.0)

        # Calculate tomorrow's orb using actual planetary velocities
        transit_rx = transit_planet_data.get("retrograde", False)
        tomorrow_deviation = calculate_tomorrow_orb(
            aspect.orb,
            aspect.applying,
            aspect.transit_planet,
            transit_rx
        )

        # Create TransitAspect
        ta = TransitAspect(
            natal_planet=aspect.natal_planet,
            natal_sign=aspect.natal_sign,
            natal_house=aspect.natal_house,
            transit_planet=aspect.transit_planet,
            aspect_type=aspect.aspect_type,
            orb_deviation=aspect.orb,
            max_orb=max_orb,
            natal_degree_in_sign=natal_planet_data.get("signed_degree", 0.0),
            ascendant_sign=natal_chart.get("ascendant_sign"),
            sensitivity=1.0,
            today_deviation=aspect.orb,
            tomorrow_deviation=tomorrow_deviation,
            label=f"Transit {aspect.transit_planet.value.title()} {aspect.aspect_type.value.title()} Natal {aspect.natal_planet.value.title()}"
        )
        transit_aspects.append(ta)

    return transit_aspects


class AllMetersReading(BaseModel):
    """Complete reading of all 23 meters with metadata."""
    date: datetime
    natal_chart_summary: Dict[str, Any]
    transit_summary: Dict[str, Any]
    aspect_count: int
    key_aspects: List[KeyAspect] = Field(
        default_factory=list,
        description="Major transit aspects affecting multiple meters (deduplicated)"
    )

    # Overall unified score (top-level summary)
    overall_unified_score: float = Field(
        ge=0, le=100,
        description="Overall unified score for the entire day (from overall_intensity meter)"
    )
    overall_unified_quality: QualityLabel = Field(
        description="Overall quality for the entire day"
    )

    # Global Meters (2)
    overall_intensity: MeterReading
    overall_harmony: MeterReading

    # Element Meters (4)
    fire_energy: MeterReading
    earth_energy: MeterReading
    air_energy: MeterReading
    water_energy: MeterReading

    # Cognitive Meters (3)
    mental_clarity: MeterReading
    decision_quality: MeterReading
    communication_flow: MeterReading

    # Emotional Meters (3)
    emotional_intensity: MeterReading
    relationship_harmony: MeterReading
    emotional_resilience: MeterReading

    # Physical/Action Meters (3)
    physical_energy: MeterReading
    conflict_risk: MeterReading
    motivation_drive: MeterReading

    # Life Domain Meters (4)
    career_ambition: MeterReading
    opportunity_window: MeterReading
    challenge_intensity: MeterReading
    transformation_pressure: MeterReading

    # Specialized Meters (4)
    intuition_spirituality: MeterReading
    innovation_breakthrough: MeterReading
    karmic_lessons: MeterReading
    social_collective: MeterReading

    # Super-Group Aggregate Meters (5) - Optional, calculated on-demand
    overview_super_group: Optional[MeterReading] = None
    inner_world_super_group: Optional[MeterReading] = None
    outer_world_super_group: Optional[MeterReading] = None
    evolution_super_group: Optional[MeterReading] = None
    deeper_dimensions_super_group: Optional[MeterReading] = None


def group_meters_by_domain(all_meters: AllMetersReading) -> Dict[str, Dict[str, MeterReading]]:
    """
    Group meters by the new 9-group taxonomy for easy access in templates.

    Args:
        all_meters: Complete AllMetersReading object

    Returns:
        Dictionary mapping group names to their relevant meters:
        {
            "overview": {"overall_intensity": MeterReading, "overall_harmony": MeterReading},
            "mind": {"mental_clarity": MeterReading, ...},
            ...
        }
    """
    return {
        "overview": {
            "overall_intensity": all_meters.overall_intensity,
            "overall_harmony": all_meters.overall_harmony
        },
        "mind": {
            "mental_clarity": all_meters.mental_clarity,
            "decision_quality": all_meters.decision_quality,
            "communication_flow": all_meters.communication_flow
        },
        "emotions": {
            "emotional_intensity": all_meters.emotional_intensity,
            "relationship_harmony": all_meters.relationship_harmony,
            "emotional_resilience": all_meters.emotional_resilience
        },
        "body": {
            "physical_energy": all_meters.physical_energy,
            "conflict_risk": all_meters.conflict_risk,
            "motivation_drive": all_meters.motivation_drive
        },
        "career": {
            "career_ambition": all_meters.career_ambition,
            "opportunity_window": all_meters.opportunity_window
        },
        "evolution": {
            "challenge_intensity": all_meters.challenge_intensity,
            "transformation_pressure": all_meters.transformation_pressure,
            "innovation_breakthrough": all_meters.innovation_breakthrough
        },
        "elements": {
            "fire_energy": all_meters.fire_energy,
            "earth_energy": all_meters.earth_energy,
            "air_energy": all_meters.air_energy,
            "water_energy": all_meters.water_energy
        },
        "spiritual": {
            "intuition_spirituality": all_meters.intuition_spirituality,
            "karmic_lessons": all_meters.karmic_lessons
        },
        "collective": {
            "social_collective": all_meters.social_collective
        }
    }


def extract_key_aspects(
    all_meters: AllMetersReading,
    top_n: int = 5,
    min_dti_threshold: float = 100.0
) -> List[KeyAspect]:
    """
    Extract and deduplicate major transit aspects from all meters.

    Identifies aspects that appear across multiple meters, showing which
    transits are driving the overall astrological climate.

    Args:
        all_meters: AllMetersReading with all 23 calculated meters
        top_n: Maximum number of key aspects to return
        min_dti_threshold: Minimum DTI strength to consider

    Returns:
        List of KeyAspect objects, sorted by DTI strength (descending)

    Example:
        >>> key_aspects = extract_key_aspects(meters, top_n=5)
        >>> for ka in key_aspects:
        ...     print(f"{ka.description}: affects {ka.meter_count} meters")
    """
    # Dictionary to track aspects: (natal_planet, transit_planet, aspect_type) -> data
    aspect_map: Dict[tuple, Dict] = {}

    # Get all meter readings
    meters = [
        all_meters.overall_intensity,
        all_meters.overall_harmony,
        all_meters.fire_energy,
        all_meters.earth_energy,
        all_meters.air_energy,
        all_meters.water_energy,
        all_meters.mental_clarity,
        all_meters.decision_quality,
        all_meters.communication_flow,
        all_meters.emotional_intensity,
        all_meters.relationship_harmony,
        all_meters.emotional_resilience,
        all_meters.physical_energy,
        all_meters.conflict_risk,
        all_meters.motivation_drive,
        all_meters.career_ambition,
        all_meters.opportunity_window,
        all_meters.challenge_intensity,
        all_meters.transformation_pressure,
        all_meters.intuition_spirituality,
        all_meters.innovation_breakthrough,
        all_meters.karmic_lessons,
        all_meters.social_collective,
    ]

    # Collect all aspects from all meters
    for meter in meters:
        for aspect in meter.top_aspects:
            # Filter by DTI threshold
            if aspect.dti_contribution < min_dti_threshold:
                continue

            # Create unique key for this aspect
            key = (aspect.natal_planet, aspect.transit_planet, aspect.aspect_type)

            if key not in aspect_map:
                aspect_map[key] = {
                    "aspect": aspect,
                    "meters": [],
                    "max_dti": aspect.dti_contribution
                }

            # Track which meter this appears in
            if meter.meter_name not in aspect_map[key]["meters"]:
                aspect_map[key]["meters"].append(meter.meter_name)

            # Track highest DTI value across all meters
            aspect_map[key]["max_dti"] = max(aspect_map[key]["max_dti"], aspect.dti_contribution)

    # Convert to KeyAspect objects
    key_aspects = [
        KeyAspect(
            aspect=data["aspect"],
            affected_meters=data["meters"],
            meter_count=len(data["meters"])
        )
        for key, data in aspect_map.items()
    ]

    # Sort by DTI strength (descending)
    key_aspects.sort(key=lambda ka: ka.aspect.dti_contribution, reverse=True)

    # Return top N
    return key_aspects[:top_n]


# ============================================================================
# Super-Group Aggregation Functions
# ============================================================================

def aggregate_meter_scores(
    meters: List[MeterReading],
    weights: Optional[Dict[Meter, float]] = None
) -> Tuple[float, float]:
    """
    Calculate weighted average of intensity and harmony across multiple meters.

    Args:
        meters: List of MeterReading objects to aggregate
        weights: Optional weights dict (Meter -> float). If None, uses equal weighting.

    Returns:
        Tuple of (avg_intensity, avg_harmony)

    Example:
        >>> meters = [mental_clarity, decision_quality, communication_flow]
        >>> intensity, harmony = aggregate_meter_scores(meters, METER_IMPORTANCE_WEIGHTS)
        >>> # Returns weighted average intensity and harmony for Mind super-group
    """
    from .constants import METER_IMPORTANCE_WEIGHTS

    if not meters:
        return 0.0, 50.0  # No meters = neutral

    if weights is None:
        # Equal weighting
        weights = {Meter(m.meter_name): 1.0 for m in meters}

    total_intensity = 0.0
    total_harmony = 0.0
    total_weight = 0.0

    for meter in meters:
        meter_enum = Meter(meter.meter_name)
        weight = weights.get(meter_enum, 1.0)

        total_intensity += meter.intensity * weight
        total_harmony += meter.harmony * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0, 50.0

    avg_intensity = total_intensity / total_weight
    avg_harmony = total_harmony / total_weight

    return avg_intensity, avg_harmony


def aggregate_top_aspects(
    meters: List[MeterReading],
    top_n: int = 5
) -> List[AspectContribution]:
    """
    Merge and rank top contributing aspects from multiple meters.

    Deduplicates aspects that appear in multiple meters and ranks by
    maximum DTI contribution across all meters.

    Args:
        meters: List of MeterReading objects
        top_n: Number of top aspects to return

    Returns:
        List of top N AspectContribution objects, sorted by DTI (descending)

    Example:
        >>> meters = [emotional_intensity, relationship_harmony, emotional_resilience]
        >>> top_aspects = aggregate_top_aspects(meters, top_n=5)
        >>> # Returns top 5 aspects affecting the Emotions super-group
    """
    # Map: (transit_planet, natal_planet, aspect_type) -> AspectContribution
    aspect_map: Dict[Tuple, AspectContribution] = {}

    for meter in meters:
        for aspect in meter.top_aspects:
            key = (
                aspect.transit_planet,
                aspect.natal_planet,
                aspect.aspect_type
            )

            # Keep the aspect with highest DTI
            if key not in aspect_map or aspect.dti_contribution > aspect_map[key].dti_contribution:
                aspect_map[key] = aspect

    # Convert to list and sort by DTI
    aspects = list(aspect_map.values())
    aspects.sort(key=lambda a: a.dti_contribution, reverse=True)

    return aspects[:top_n]


# def calculate_super_group_meter(
#     super_group: SuperGroup,
#     meters: List[MeterReading],
#     date: datetime
# ) -> MeterReading:
#     """
#     Calculate aggregate meter for a super-group by combining all member meters.
# 
#     Uses weighted aggregation based on METER_IMPORTANCE_WEIGHTS to calculate
#     intensity and harmony, then generates a complete MeterReading with
#     unified score, quality label, and aggregated top aspects.
# 
#     Args:
#         super_group: The SuperGroup enum (e.g., SuperGroup.INNER_WORLD)
#         meters: List of individual MeterReading objects in this super-group
#         date: Date for the reading
# 
#     Returns:
#         Complete MeterReading for the super-group
# 
#     Example:
#         >>> inner_world_meters = [
#         ...     mental_clarity, decision_quality, communication_flow,
#         ...     emotional_intensity, relationship_harmony, emotional_resilience
#         ... ]
#         >>> inner_world_sg = calculate_super_group_meter(
#         ...     SuperGroup.INNER_WORLD,
#         ...     inner_world_meters,
#         ...     datetime.now()
#         ... )
#         >>> print(f"Inner World: {inner_world_sg.unified_score:.1f}/100")
#     """
#     from .constants import METER_IMPORTANCE_WEIGHTS
#     from .hierarchy import SUPER_GROUP_TO_METER, get_meters_in_super_group
# 
#     # Get super-group aggregate meter enum
#     meter_enum = SUPER_GROUP_TO_METER[super_group]
#     meter_name = meter_enum.value
# 
#     # Calculate weighted aggregates
#     avg_intensity, avg_harmony = aggregate_meter_scores(meters, METER_IMPORTANCE_WEIGHTS)
# 
#     # Aggregate top aspects
#     top_aspects = aggregate_top_aspects(meters, top_n=5)
# 
#     # Calculate unified score and quality
#     unified_score, unified_quality = calculate_unified_score(avg_intensity, avg_harmony)
# 
#     # Get state label (using first member meter's labels as template)
#     # Super-group meters will have their own JSON labels generated
#     intensity_level = get_intensity_level(avg_intensity)
#     harmony_level = get_harmony_level(avg_harmony)
# 
#     # Try to load super-group-specific labels, fallback to generic
#     try:
#         state_label = get_state_label_from_json(meter_name, avg_intensity, avg_harmony)
#         description = get_meter_description_from_json(meter_name)
#         interpretation = f"{description['overview']} {description['detailed']}"
#         advice_category = get_advice_category_from_json(meter_name, avg_intensity, avg_harmony)
#         advice = [f"Advice type: {advice_category}"]
#     except FileNotFoundError:
#         # Fallback if JSON labels don't exist yet
#         state_label = f"{intensity_level.title()} & {harmony_level.title()}"
#         interpretation = f"Aggregate reading for {super_group.value.replace('_', ' ').title()}"
#         advice = [f"Based on {len(meters)} meters in this super-group"]
# 
#     # Create MeterReading
#     return MeterReading(
#         meter_name=meter_name,
#         date=date,
#         group=MeterGroupV2.MIND,  # Super-groups use OVERVIEW group for now
#         unified_score=unified_score,
#         unified_quality=unified_quality,
#         intensity=avg_intensity,
#         harmony=avg_harmony,
#         state_label=state_label,
#         interpretation=interpretation,
#         advice=advice,
#         top_aspects=top_aspects,
#         raw_scores={
#             "dti": sum(a.dti_contribution for a in top_aspects[:3]),
#             "hqs": sum(a.hqs_contribution for a in top_aspects[:3]) / len(top_aspects[:3]) if top_aspects else 0.0,
#             "member_count": len(meters),
#         },
#         additional_context={
#             "super_group": super_group.value,
#             "member_meters": [m.meter_name for m in meters],
#             "aggregation_method": "weighted_average",
#         }
#     )


def _calculate_meters_no_trends(
    natal_chart: dict,
    transit_chart: dict,
    date: datetime
) -> AllMetersReading:
    """
    Internal helper: Calculate all meters WITHOUT trend analysis.
    Used by get_meters() to avoid infinite recursion.
    """
    # Import here to avoid circular import
    from astro import find_natal_transit_aspects

    # Find all natal-transit aspects
    natal_transit_aspects = find_natal_transit_aspects(
        natal_chart,
        transit_chart,
        orb=8.0
    )

    # Convert to TransitAspect format
    all_aspects = convert_to_transit_aspects(
        natal_chart,
        transit_chart,
        natal_transit_aspects
    )

    # Calculate element distribution
    element_dist = calculate_element_distribution(natal_chart, transit_chart)

    # Calculate global meters first (needed for overall unified score)
    overall_intensity_meter = calculate_overall_intensity_meter(all_aspects, date)
    overall_harmony_meter = calculate_overall_harmony_meter(all_aspects, date)

    # Calculate all meters
    all_meters = AllMetersReading(
        date=date,
        natal_chart_summary={
            "sun_sign": natal_chart.get("sun_sign"),
            "ascendant_sign": natal_chart.get("ascendant_sign"),
            "moon_sign": next((p["sign"] for p in natal_chart["planets"] if p["name"] == "moon"), None)
        },
        transit_summary={
            "sun_sign": transit_chart.get("sun_sign"),
            "aspect_count": len(natal_transit_aspects)
        },
        aspect_count=len(all_aspects),

        # Overall unified score (top-level summary)
        overall_unified_score=overall_intensity_meter.unified_score,
        overall_unified_quality=overall_intensity_meter.unified_quality,

        # Global Meters
        overall_intensity=overall_intensity_meter,
        overall_harmony=overall_harmony_meter,

        # Element Meters
        fire_energy=calculate_fire_energy_meter(all_aspects, date, element_dist),
        earth_energy=calculate_earth_energy_meter(all_aspects, date, element_dist),
        air_energy=calculate_air_energy_meter(all_aspects, date, element_dist),
        water_energy=calculate_water_energy_meter(all_aspects, date, element_dist),

        # Cognitive Meters
        mental_clarity=calculate_mental_clarity_meter(all_aspects, date, transit_chart),
        decision_quality=calculate_decision_quality_meter(all_aspects, date),
        communication_flow=calculate_communication_flow_meter(all_aspects, date),

        # Emotional Meters
        emotional_intensity=calculate_emotional_intensity_meter(all_aspects, date),
        relationship_harmony=calculate_relationship_harmony_meter(all_aspects, date, transit_chart),
        emotional_resilience=calculate_emotional_resilience_meter(all_aspects, date),

        # Physical/Action Meters
        physical_energy=calculate_physical_energy_meter(all_aspects, date, transit_chart),
        conflict_risk=calculate_conflict_risk_meter(all_aspects, date, transit_chart),
        motivation_drive=calculate_motivation_drive_meter(all_aspects, date, transit_chart),

        # Life Domain Meters
        career_ambition=calculate_career_ambition_meter(all_aspects, date, transit_chart),
        opportunity_window=calculate_opportunity_window_meter(all_aspects, date, transit_chart),
        challenge_intensity=calculate_challenge_intensity_meter(all_aspects, date),
        transformation_pressure=calculate_transformation_pressure_meter(all_aspects, date),

        # Specialized Meters
        intuition_spirituality=calculate_intuition_spirituality_meter(all_aspects, date),
        innovation_breakthrough=calculate_innovation_breakthrough_meter(all_aspects, date),
        karmic_lessons=calculate_karmic_lessons_meter(all_aspects, date),
        social_collective=calculate_social_collective_meter(all_aspects, date),
    )

    # Extract key aspects (major transits affecting multiple meters)
    all_meters.key_aspects = extract_key_aspects(all_meters, top_n=5, min_dti_threshold=100.0)

#     # Calculate super-group aggregate meters
#     # Overview Super-Group (2 meters)
#     all_meters.overview_super_group = calculate_super_group_meter(
#         SuperGroup.OVERVIEW,
#         [all_meters.overall_intensity, all_meters.overall_harmony],
#         date
#     )
# 
#     # Inner World Super-Group (6 meters: 3 Mind + 3 Emotions)
#     all_meters.inner_world_super_group = calculate_super_group_meter(
#         SuperGroup.INNER_WORLD,
#         [
#             all_meters.mental_clarity,
#             all_meters.decision_quality,
#             all_meters.communication_flow,
#             all_meters.emotional_intensity,
#             all_meters.relationship_harmony,
#             all_meters.emotional_resilience,
#         ],
#         date
#     )
# 
#     # Outer World Super-Group (5 meters: 3 Body + 2 Career)
#     all_meters.outer_world_super_group = calculate_super_group_meter(
#         SuperGroup.OUTER_WORLD,
#         [
#             all_meters.physical_energy,
#             all_meters.conflict_risk,
#             all_meters.motivation_drive,
#             all_meters.career_ambition,
#             all_meters.opportunity_window,
#         ],
#         date
#     )
# 
#     # Evolution Super-Group (3 meters)
#     all_meters.evolution_super_group = calculate_super_group_meter(
#         SuperGroup.EVOLUTION,
#         [
#             all_meters.challenge_intensity,
#             all_meters.transformation_pressure,
#             all_meters.innovation_breakthrough,
#         ],
#         date
#     )
# 
#     # Deeper Dimensions Super-Group (7 meters: 4 Elements + 2 Spiritual + 1 Collective)
#     all_meters.deeper_dimensions_super_group = calculate_super_group_meter(
#         SuperGroup.DEEPER_DIMENSIONS,
#         [
#             all_meters.fire_energy,
#             all_meters.earth_energy,
#             all_meters.air_energy,
#             all_meters.water_energy,
#             all_meters.intuition_spirituality,
#             all_meters.karmic_lessons,
#             all_meters.social_collective,
#         ],
#         date
#     )
# 
#     return all_meters


def get_meters(
    natal_chart: dict,
    transit_chart: dict,
    date: Optional[datetime] = None
) -> AllMetersReading:
    """
    Calculate all 28 astrological meters (23 individual + 5 super-groups) with automatic trend analysis.

    This function automatically calculates yesterday's transits and populates trend fields
    for all meters, showing whether each area is improving, stable, or worsening.

    Args:
        natal_chart: User's natal chart from compute_birth_chart()
        transit_chart: Transit chart for target date from compute_birth_chart()
        date: Date for calculation (defaults to today)

    Returns:
        AllMetersReading with all 28 meters calculated and all trend fields populated

    Example:
        >>> from astro import compute_birth_chart
        >>> from datetime import datetime
        >>> natal_chart, _ = compute_birth_chart("1990-06-15")
        >>> transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")
        >>> meters = get_meters(natal_chart, transit_chart)
        >>> print(f"Overall Intensity: {meters.overall_intensity.intensity:.1f}/100")
        >>> print(f"Trend: {meters.overall_intensity.trend}")  # Always populated!
    """
    # Import here to avoid circular import
    from astro import compute_birth_chart
    from datetime import timedelta

    if date is None:
        date = datetime.now()

    # Calculate today's meters (without trends)
    all_meters = _calculate_meters_no_trends(natal_chart, transit_chart, date)

    # Calculate yesterday's meters for trend comparison
    yesterday_date = date - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime('%Y-%m-%d')
    yesterday_transit_chart, _ = compute_birth_chart(
        birth_date=yesterday_date_str,
        birth_time="12:00"  # Use noon for transits
    )
    yesterday_meters = _calculate_meters_no_trends(natal_chart, yesterday_transit_chart, yesterday_date)

    # Populate trend fields for all 28 meters
    meter_names = [
        'overall_intensity', 'overall_harmony',
        'mental_clarity', 'decision_quality', 'communication_flow',
        'emotional_intensity', 'relationship_harmony', 'emotional_resilience',
        'physical_energy', 'conflict_risk', 'motivation_drive',
        'career_ambition', 'opportunity_window', 'challenge_intensity',
        'transformation_pressure', 'fire_energy', 'earth_energy',
        'air_energy', 'water_energy', 'intuition_spirituality',
        'innovation_breakthrough', 'karmic_lessons', 'social_collective',
        'overview_super_group', 'inner_world_super_group',
        'outer_world_super_group', 'evolution_super_group',
        'deeper_dimensions_super_group'
    ]

    # Calculate trends by comparing with yesterday
    for meter_name in meter_names:
        today_meter = getattr(all_meters, meter_name)
        yesterday_meter = getattr(yesterday_meters, meter_name)

        # Super-group meters might be None if not calculated
        if today_meter and yesterday_meter:
            today_meter.trend = today_meter.calculate_trend(yesterday_meter)

    return all_meters

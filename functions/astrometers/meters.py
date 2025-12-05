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
from .core import TransitAspect, AspectContribution, calculate_astrometers, AstrometerScore, get_cosmic_dither
from .normalization import normalize_intensity, normalize_intensity_v2, normalize_harmony
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
    """Unified quality labels based on unified_score quartiles (0-100 scale)."""
    CHALLENGING = "challenging"  # unified_score < 25
    TURBULENT = "turbulent"      # unified_score 25-50
    PEACEFUL = "peaceful"        # unified_score 50-75
    FLOWING = "flowing"          # unified_score >= 75


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
    Labels are loaded from JSON to stay in sync with iOS.

    Symmetric quartile thresholds (matches iOS):
        score < 25  -> bucket_labels[0]
        score >= 25 && < 50  -> bucket_labels[1]
        score >= 50 && < 75  -> bucket_labels[2]
        score >= 75 -> bucket_labels[3]

    Returns:
        Bucket label string (e.g., "Clear", "Grounded", "Surging")
    """
    from .hierarchy import METER_TO_GROUP_V2, Meter
    from .meter_groups import get_group_bucket_labels

    # Calculate unified_score
    unified_score, _ = calculate_unified_score(intensity, harmony)

    # Get the meter's group
    try:
        meter_enum = Meter(meter_name)
        group = METER_TO_GROUP_V2.get(meter_enum)
        group_name = group.value if group else "overall"
    except ValueError:
        group_name = "overall"

    # Load bucket labels from JSON
    labels = get_group_bucket_labels(group_name)

    # Map unified_score (0-100) to bucket using symmetric quartiles
    if unified_score < 25:
        return labels[0]
    elif unified_score < 50:
        return labels[1]
    elif unified_score < 75:
        return labels[2]
    else:
        return labels[3]


def get_quality_label(unified_score: float) -> QualityLabel:
    """
    Determine quality label from unified_score (0-100 scale).

    Thresholds (symmetric quartiles):
    - < 25: Challenging
    - 25-50: Turbulent
    - 50-75: Peaceful
    - >= 75: Flowing
    """
    if unified_score < 25:
        return QualityLabel.CHALLENGING
    elif unified_score < 50:
        return QualityLabel.TURBULENT
    elif unified_score < 75:
        return QualityLabel.PEACEFUL
    else:
        return QualityLabel.FLOWING


def calculate_unified_score(
    intensity: float,
    harmony: float,
    dither: float = 0.0
) -> tuple[float, QualityLabel]:
    """
    Calculate unified score using intensity stretch + linear combination + post-sigmoid.

    Design:
    - Intensity drives the VALUE (how much is happening)
    - Harmony determines the DIRECTION (positive or negative)
    - Intensity stretch boosts low-intensity days so they still show variation
    - Dither ("Cosmic Background") prevents exact-50 clustering
    - Post-sigmoid stretches distribution away from 50 toward extremes

    Formula:
    - Step 1 (Intensity stretch): stretched_I = 100 * tanh(I / 60)
    - Step 2 (Linear): raw = 50 + (stretched_I / 2) * harmony_coef
    - Step 2.5 (Dither): raw += dither (prevents exact-50 spike)
    - Step 3 (Post-stretch): unified = 50 + 50 * tanh(deviation / 25)

    Args:
        intensity: Intensity meter (0-100) - how much is happening
        harmony: Harmony meter (0-100) - quality of what's happening (50 = neutral)
        dither: Cosmic background dither (-5 to +5) to prevent 50-spike

    Returns:
        Tuple of (unified_score, quality_label):
        - unified_score: 0-100 (50 = neutral, >50 = positive, <50 = challenging)
        - quality_label: QualityLabel enum based on score
    """
    import math

    # Convert harmony (0-100) to harmony_coefficient (-1 to +1)
    harmony_coef = (harmony - 50) / 50

    # Step 1: Stretch intensity with moderate gain
    # tanh(I/60): Provides lift for low values without over-amplifying
    # 5->8.3, 20->32, 50->70, 80->87, 100->93
    stretched_intensity = 100 * math.tanh(intensity / 60)

    # Step 2: Linear combination
    # Stretched intensity drives magnitude, harmony drives direction
    raw_unified = 50 + (stretched_intensity / 2) * harmony_coef

    # Step 2.5: Apply cosmic background dither with diminishing intensity
    # Full dither when neutral (raw=50), diminishing as signal gets stronger
    # This prevents the exact-50 spike without interfering with strong signals
    proximity_to_neutral = 1.0 - abs(raw_unified - 50) / 50  # 1 at 50, 0 at extremes
    proximity_to_neutral = max(0.0, proximity_to_neutral)  # Clamp to 0-1
    scaled_dither = dither * proximity_to_neutral
    raw_unified += scaled_dither

    # Step 3: Post-sigmoid stretch with headroom
    # Divisor of 25 ensures P95 maps to ~80, leaving 80-100 for exceptional days
    deviation = raw_unified - 50  # Range: -50 to +50
    stretch_factor = 25  # Higher = softer curve, more headroom at extremes
    stretched = 50 * math.tanh(deviation / stretch_factor)
    unified_score = 50 + stretched

    # Round to 1 decimal place
    unified_score = round(unified_score, 1)

    quality = get_quality_label(unified_score)
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
    user_id: Optional[str] = None,
    use_v2_scoring: bool = True
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
        use_v2_scoring: Use decoupled V2 scoring (Gaussian + ballast) (default: True)

    Returns:
        Complete MeterReading
    """
    # Step 1: Filter aspects
    filtered_aspects = filter_aspects(all_aspects, config, natal_chart)

    # Step 2: Calculate raw scores
    # Generate chart hash for cosmic background (deterministic per-chart noise)
    # Use natal chart's sun and moon positions as a stable identifier
    natal_sun_deg = 0.0
    natal_moon_deg = 0.0
    planets = natal_chart.get("planets", [])
    if isinstance(planets, list):
        for p in planets:
            if p.get("name") == "sun":
                natal_sun_deg = p.get("absolute_degree", 0)
            elif p.get("name") == "moon":
                natal_moon_deg = p.get("absolute_degree", 0)
    elif isinstance(planets, dict):
        natal_sun_deg = planets.get("sun", {}).get("abs_pos", 0)
        natal_moon_deg = planets.get("moon", {}).get("abs_pos", 0)
    natal_chart_hash = int((natal_sun_deg * 1000 + natal_moon_deg * 100) % 1000000)
    date_ordinal = date.toordinal() if hasattr(date, 'toordinal') else date.date().toordinal()

    if not filtered_aspects:
        # No activity - but still apply cosmic background
        raw_score = calculate_astrometers(
            [],
            meter_name=meter_name,
            natal_chart_hash=natal_chart_hash,
            date_ordinal=date_ordinal
        )
    else:
        # Pass meter_name and cosmic background params
        raw_score = calculate_astrometers(
            filtered_aspects,
            meter_name=meter_name,
            natal_chart_hash=natal_chart_hash,
            date_ordinal=date_ordinal
        )

    if use_v2_scoring:
        # V2: Decoupled scoring (Gaussian power + ballast)
        # Intensity: Gaussian power sum, normalized via percentiles
        # Harmony: coefficient -1 to +1, mapped to 0-100
        intensity = normalize_intensity_v2(raw_score.intensity, meter_name)

        # Direct mapping: -1 to +1 → 0 to 100
        harmony = (raw_score.harmony_coefficient + 1) * 50
        harmony = max(0.0, min(100.0, harmony))  # Clamp to 0-100
    else:
        # V1: Legacy coupled scoring (DTI/HQS)
        # Step 2.5: Apply planetary nature adjustments (harmonic boost) - OPTIONAL
        if apply_harmonic_boost and raw_score.contributions:
            boosted_hqs = harmonic_boost(
                raw_score.hqs,
                raw_score.contributions,
                benefic_multiplier=benefic_multiplier,
                malefic_multiplier=malefic_multiplier
            )
        else:
            boosted_hqs = raw_score.hqs

        # Step 3: Normalize to 0-100 (against flat baseline calibration)
        intensity = normalize_intensity(raw_score.dti, meter_name)
        harmony = normalize_harmony(boosted_hqs, meter_name)

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

    # Step 4: Apply retrograde modifiers (to deviation from neutral only)
    # Retrograde affects how far harmony deviates from neutral (50),
    # but preserves neutral as the baseline
    for planet, modifier in config.retrograde_modifiers.items():
        if is_planet_retrograde(transit_chart, planet):
            deviation = harmony - 50.0
            harmony = 50.0 + deviation * modifier
            harmony = max(0.0, min(100.0, harmony))  # Clamp

    # Step 5: Calculate unified score (polar-style with sigmoid stretch)
    # Add cosmic background dither to prevent exact-50 clustering
    dither = get_cosmic_dither(natal_chart_hash, date_ordinal, meter_name)
    unified_score, _ = calculate_unified_score(intensity, harmony, dither=dither)

    # Step 6: Get labels
    state_label = get_state_label(meter_name, intensity, harmony)
    quality_label = get_quality_label(unified_score)

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
            # V1 (legacy)
            "dti": raw_score.dti,
            "hqs": raw_score.hqs,
            # V2 (decoupled)
            "intensity_raw": raw_score.intensity,
            "harmony_coefficient": raw_score.harmony_coefficient,
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
    user_id: Optional[str] = None,
    use_v2_scoring: bool = True
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
        use_v2_scoring: Use decoupled V2 scoring (Gaussian + ballast) (default: True)

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
            user_id=user_id,
            use_v2_scoring=use_v2_scoring
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
                yesterday,
                use_v2_scoring=use_v2_scoring
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


def get_quadrant_from_unified_score(unified_score: float) -> str:
    """
    Map unified_score to word bank quadrant for backward compatibility.

    Unified score (0-100) maps to quadrant names using symmetric quartiles:
    - >= 75: "high_intensity_high_harmony" (flowing, peak energy)
    - 50-75: "low_intensity_high_harmony" (peaceful, gentle positive)
    - 25-50: "moderate" (turbulent, in flux)
    - < 25: "low_intensity_low_harmony" (challenging, stuck/blocked)

    Returns:
        Quadrant name for word bank lookup
    """
    if unified_score >= 75:
        return "high_intensity_high_harmony"
    elif unified_score >= 50:
        return "low_intensity_high_harmony"
    elif unified_score >= 25:
        return "moderate"
    else:
        return "low_intensity_low_harmony"


def select_state_words(
    group_name: str,
    unified_score: float,
    user_id: str,
    date: str,
    count: int = 2
) -> list[str]:
    """
    Select N words from the word bank for a group based on unified_score.

    Uses reproducible randomness tied to user+date+group for consistency.

    Args:
        group_name: Group name (mind, heart, body, instincts, growth, overall)
        unified_score: Group unified score (0-100, 50=neutral)
        user_id: User ID for reproducible selection
        date: Date string for reproducible selection
        count: Number of words to select (default 2)

    Returns:
        List of selected words as creative inspiration for LLM
    """
    import hashlib
    import random

    word_banks = load_word_banks()
    quadrant = get_quadrant_from_unified_score(unified_score)
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
) -> dict:
    """
    Select featured meters for today's horoscope using weighted random.

    Logic:
    - Weight = distance from neutral (50). Extremes are more interesting.
    - If top 2 have CONTRAST (one >50, one <50): show both
    - If top 2 are SAME DIRECTION: show only the most extreme one

    Each meter is labeled:
    - "flowing": score >= 50 (lean into it)
    - "pushing": score < 50 (push through it)

    Args:
        all_meters: Complete meter readings
        user_id: User ID for reproducible selection
        date: Date string for reproducible selection

    Returns:
        Dict with:
        - featured_meters: Dict mapping group_name -> list of meter readings
        - featured_list: Flat list of featured meters with direction labels
        - featured_groups: List of unique group names for featured meters
        - group_words: Dict mapping group_name -> list of state word inspirations
        - group_scores: Dict with scores for featured groups
    """
    import hashlib
    import random
    from .hierarchy import Meter, MeterGroupV2, get_meters_in_group_v2
    from .meter_groups import calculate_group_scores_top_2

    # Create reproducible RNG
    seed_string = f"{user_id}:{date}:featured_selection"
    seed_hash = int(hashlib.sha256(seed_string.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed_hash)

    # Collect all 17 individual meters with their weights
    all_individual_meters = []
    for meter in Meter:
        if meter.value in ["overall_intensity", "overall_harmony"]:
            continue
        if "_super_group" in meter.value:
            continue
        meter_reading = getattr(all_meters, meter.value, None)
        if meter_reading:
            all_individual_meters.append(meter_reading)

    if not all_individual_meters:
        return {
            "featured_meters": {},
            "featured_list": [],
            "featured_groups": [],
            "group_words": {},
            "group_scores": {}
        }

    # Calculate weights: distance from neutral (50)
    meter_weights = [abs(m.unified_score - 50) + 0.1 for m in all_individual_meters]

    # Weighted random selection of top 2 candidates
    available_meters = list(all_individual_meters)
    available_weights = list(meter_weights)
    candidates = []

    for _ in range(min(2, len(available_meters))):
        if not available_meters:
            break
        selected = rng.choices(available_meters, weights=available_weights, k=1)[0]
        candidates.append(selected)
        idx = available_meters.index(selected)
        available_meters.pop(idx)
        available_weights.pop(idx)

    # Determine if we have contrast or same direction
    if len(candidates) == 2:
        first_positive = candidates[0].unified_score >= 50
        second_positive = candidates[1].unified_score >= 50
        has_contrast = first_positive != second_positive

        if has_contrast:
            # Show both - interesting contrast
            selected_meters = candidates
        else:
            # Same direction - show only the most extreme
            if abs(candidates[0].unified_score - 50) >= abs(candidates[1].unified_score - 50):
                selected_meters = [candidates[0]]
            else:
                selected_meters = [candidates[1]]
    else:
        selected_meters = candidates

    # Build featured_list with direction labels
    featured_list = []
    for meter in selected_meters:
        direction = "flowing" if meter.unified_score >= 50 else "pushing"
        featured_list.append({
            "meter": meter,
            "direction": direction,
        })

    # Build featured_meters dict keyed by group
    featured_meters_by_group: dict = {}
    featured_groups = []

    for meter in selected_meters:
        group_name = meter.group.value
        if group_name not in featured_meters_by_group:
            featured_meters_by_group[group_name] = []
            featured_groups.append(group_name)
        featured_meters_by_group[group_name].append(meter)

    # Calculate group scores for featured groups using Top 2 Weighted
    group_scores = {}
    for group_name in featured_groups:
        group_enum = MeterGroupV2(group_name)
        meter_enums = get_meters_in_group_v2(group_enum)
        meters_in_group = []
        for meter_enum in meter_enums:
            meter_reading = getattr(all_meters, meter_enum.value, None)
            if meter_reading:
                meters_in_group.append(meter_reading)

        if meters_in_group:
            scores = calculate_group_scores_top_2(meters_in_group)
            group_scores[group_name] = {
                "unified_score": scores["unified_score"],
                "intensity": scores["intensity"],
                "harmony": scores["harmony"],
            }

    # Get state words for featured groups
    group_words = {}
    for group_name in featured_groups:
        if group_name in group_scores:
            group_words[group_name] = select_state_words(
                group_name=group_name,
                unified_score=group_scores[group_name]["unified_score"],
                user_id=user_id,
                date=date,
                count=2
            )

    # Generate headline guidance based on the 16-case matrix
    headline_guidance = generate_headline_guidance(featured_list)

    return {
        "featured_groups": featured_groups,
        "featured_meters": featured_meters_by_group,
        "featured_list": featured_list,  # New: flat list with direction labels
        "group_words": group_words,
        "group_scores": group_scores,
        "headline_guidance": headline_guidance,  # Programmatic guidance for LLM
    }


# =============================================================================
# HEADLINE GUIDANCE - 16 CASE MATRIX
# =============================================================================

def get_score_band(score: float) -> str:
    """
    Map unified_score to one of 4 bands.

    Bands:
    - high: 75-100
    - mid_high: 55-75
    - mid_low: 35-55
    - low: 0-35
    """
    if score >= 75:
        return "high"
    elif score >= 55:
        return "mid_high"
    elif score >= 35:
        return "mid_low"
    else:
        return "low"


# 16-case matrix: (band1, band2) -> (pattern, conjunction, tone)
HEADLINE_MATRIX = {
    # High + X
    ("high", "high"): ("both_thriving", "and", "expansive, celebratory"),
    ("high", "mid_high"): ("strong_and_solid", "and", "confident, stable"),
    ("high", "mid_low"): ("contrast_up", "but", "balanced pivot"),
    ("high", "low"): ("stark_contrast_up", "but", "strong pivot, acknowledge the struggle"),
    # Mid-High + X
    ("mid_high", "high"): ("solid_and_strong", "and", "confident"),
    ("mid_high", "mid_high"): ("both_solid", "and", "steady, grounded"),
    ("mid_high", "mid_low"): ("slight_contrast", "but", "gentle pivot"),
    ("mid_high", "low"): ("contrast_down", "but", "acknowledge then redirect"),
    # Mid-Low + X
    ("mid_low", "high"): ("contrast_up", "but", "find the bright spot"),
    ("mid_low", "mid_high"): ("slight_contrast", "but", "gentle pivot"),
    ("mid_low", "mid_low"): ("both_struggling", "and", "compassionate, normalize the strain"),
    ("mid_low", "low"): ("both_low", "and", "honest, rest-focused"),
    # Low + X
    ("low", "high"): ("stark_contrast_up", "but", "anchor to positive"),
    ("low", "mid_high"): ("contrast_down", "but", "acknowledge then redirect"),
    ("low", "mid_low"): ("both_low", "and", "honest, rest-focused"),
    ("low", "low"): ("both_depleted", "and", "survival-mode validation"),
}


def generate_headline_guidance(featured_list: list[dict]) -> dict:
    """
    Generate programmatic headline guidance based on the 16-case matrix.

    This provides the LLM with:
    - The correct conjunction ("and" vs "but")
    - The pattern name for the combination
    - The tone/angle to take
    - Concrete instruction text

    Args:
        featured_list: List of dicts with 'meter' and 'direction' keys

    Returns:
        Dict with pattern, conjunction, tone, and instruction text
    """
    if not featured_list:
        return {
            "pattern": "neutral",
            "conjunction": None,
            "tone": "balanced, flexible",
            "meter_count": 0,
            "meters": [],
            "instruction": "Neutral day - no standout meters. Focus on balance and flexibility.",
        }

    # Load meter descriptions and planets
    meter_descriptions = _load_meter_overviews()
    meter_planets = _load_meter_planets()

    # Build meter info with all context
    meters_info = []
    for item in featured_list:
        meter = item["meter"]
        score = meter.unified_score
        band = get_score_band(score)
        # Get the GROUP label (not the meter label)
        group_label = _get_group_label(meter.group.value, score)
        # Get top aspect driving this meter
        top_aspect = None
        if meter.top_aspects:
            asp = meter.top_aspects[0]
            top_aspect = f"{asp.transit_planet.value.title()} {asp.aspect_type.value} natal {asp.natal_planet.value.title()}"
        # Get trend info
        trend_str = None
        if meter.trend:
            t = meter.trend.unified_score
            trend_str = f"{t.direction} ({t.change_rate}, {t.delta:+.0f} from yesterday)"
        meters_info.append({
            "group": meter.group.value,
            "group_label": group_label,
            "meter_name": meter.meter_name,
            "meter_label": meter.state_label,
            "score": round(score),  # Group score (integer for cleaner prompts)
            "driver_score": round(meter.unified_score),  # Driver meter score
            "driver_meaning": meter_descriptions.get(meter.meter_name, ""),
            "driver_planets": meter_planets.get(meter.meter_name, ""),
            "band": band,
            "top_aspect": top_aspect,
            "trend": trend_str,
        })

    if len(featured_list) == 1:
        # Single meter case
        m = meters_info[0]
        band = m["band"]

        if band == "high":
            tone = "confident, lean into it"
            instruction = f"Lead with {m['group'].upper()} ({m['group_label']}). Emphasize {m['meter_name']} as the driver."
        elif band == "mid_high":
            tone = "steady, reliable"
            instruction = f"Acknowledge solid {m['group'].upper()} ({m['group_label']}). Emphasize {m['meter_name']} as the driver."
        elif band == "mid_low":
            tone = "honest but not dire"
            instruction = f"Name that {m['group'].upper()} is challenged ({m['group_label']}). Emphasize {m['meter_name']} as the main issue."
        else:  # low
            tone = "compassionate, rest-focused"
            instruction = f"Validate that {m['group'].upper()} is depleted ({m['group_label']}). Emphasize {m['meter_name']} as the main issue."

        return {
            "pattern": f"single_{band}",
            "conjunction": None,
            "tone": tone,
            "meter_count": 1,
            "meters": meters_info,
            "instruction": instruction,
        }

    # Two meters - use the 16-case matrix
    m1, m2 = meters_info[0], meters_info[1]
    band1, band2 = m1["band"], m2["band"]

    pattern, conjunction, tone = HEADLINE_MATRIX.get(
        (band1, band2),
        ("mixed", "and", "balanced")  # fallback
    )

    # Generate specific instruction based on pattern
    instruction = _build_headline_instruction(pattern, conjunction, tone, m1, m2)

    return {
        "pattern": pattern,
        "conjunction": conjunction,
        "tone": tone,
        "meter_count": 2,
        "meters": meters_info,
        "instruction": instruction,
    }


def _build_headline_instruction(
    pattern: str,
    conjunction: str,
    tone: str,
    m1: dict,
    m2: dict
) -> str:
    """Build concrete instruction text for the LLM based on pattern."""

    g1, gl1, mn1 = m1["group"].upper(), m1["group_label"], m1["meter_name"]
    g2, gl2, mn2 = m2["group"].upper(), m2["group_label"], m2["meter_name"]

    # Pattern-specific instructions
    instructions = {
        "both_thriving": (
            f"Celebrate {g1} ({gl1}) AND {g2} ({gl2}). "
            f"Use 'and'. Expansive tone. Drivers: {mn1} and {mn2}."
        ),
        "strong_and_solid": (
            f"Lead with {g1} ({gl1}) AND {g2} ({gl2}) supports it. "
            f"Use 'and'. Drivers: {mn1} and {mn2}."
        ),
        "solid_and_strong": (
            f"{g1} ({gl1}) is solid AND {g2} ({gl2}) is even stronger. "
            f"Use 'and'. Drivers: {mn1} and {mn2}."
        ),
        "both_solid": (
            f"Both {g1} ({gl1}) and {g2} ({gl2}) are reliable. "
            f"Use 'and'. Steady tone. Drivers: {mn1} and {mn2}."
        ),
        "contrast_up": (
            f"{g1} ({gl1}) is struggling BUT {g2} ({gl2}) is strong. "
            f"Use 'but' to pivot. Drivers: {mn1} and {mn2}."
        ),
        "stark_contrast_up": (
            f"Be honest: {g1} ({gl1}) is hard. BUT {g2} ({gl2}) is strong - anchor there. "
            f"Use 'but'. Drivers: {mn1} and {mn2}."
        ),
        "slight_contrast": (
            f"{g1} ({gl1}) and {g2} ({gl2}) are mismatched. "
            f"Use 'but' for gentle pivot. Drivers: {mn1} and {mn2}."
        ),
        "contrast_down": (
            f"Lead with {g1} ({gl1}) BUT {g2} ({gl2}) needs care. "
            f"Use 'but'. Drivers: {mn1} and {mn2}."
        ),
        "both_struggling": (
            f"Both {g1} ({gl1}) AND {g2} ({gl2}) are challenged. "
            f"Use 'and' - no fake contrast. Compassionate. Drivers: {mn1} and {mn2}."
        ),
        "both_low": (
            f"{g1} ({gl1}) AND {g2} ({gl2}) are both depleted. "
            f"Use 'and'. Rest-focused. Drivers: {mn1} and {mn2}."
        ),
        "both_depleted": (
            f"{g1} ({gl1}) AND {g2} ({gl2}) are both at the bottom. "
            f"Use 'and'. Survival mode is okay. Drivers: {mn1} and {mn2}."
        ),
    }

    return instructions.get(pattern, (
        f"Combine {g1} ({gl1}) {conjunction.upper()} {g2} ({gl2}). "
        f"Tone: {tone}. Drivers: {mn1} and {mn2}."
    ))


def generate_overview_guidance(
    all_meters: "AllMetersReading",
    featured_list: list[dict],
    headline_guidance: dict,
) -> dict:
    """
    Generate guidance for daily_overview that expands on the headline.

    Selects the most active groups to highlight, ensuring the headline group
    is included plus additional interesting groups.

    Args:
        all_meters: Complete meter readings
        featured_list: The meters featured in the headline
        headline_guidance: The headline guidance dict

    Returns:
        Dict with overview highlights including group, key meter, transit, and meaning
    """
    from .meter_groups import calculate_group_scores_top_2

    # Load meter descriptions and planets from JSON
    meter_descriptions = _load_meter_overviews()
    meter_planets = _load_meter_planets()

    # Get featured group names from headline
    headline_groups = set()
    for item in featured_list:
        headline_groups.add(item["meter"].group.value)

    # Build detailed info for all groups
    all_group_info = []
    group_names = ["mind", "heart", "body", "instincts", "growth"]

    for group_name in group_names:
        group_meters = []
        for meter_name in _get_meters_in_group(group_name):
            meter = getattr(all_meters, meter_name, None)
            if meter:
                group_meters.append(meter)

        if group_meters:
            # Use the same Top-2 weighted calculation as all_groups for consistency
            scores = calculate_group_scores_top_2(group_meters)
            group_score = scores["unified_score"]
            driver_name = scores["driver"]

            # Get the driver meter object
            driver = next((m for m in group_meters if m.meter_name == driver_name), group_meters[0])

            # Get the top aspect for this meter
            top_aspect = None
            if driver.top_aspects:
                asp = driver.top_aspects[0]
                top_aspect = f"{asp.transit_planet.value.title()} {asp.aspect_type.value} natal {asp.natal_planet.value.title()}"

            # Get the group guidance (how to push through)
            group_guidance = _get_group_guidance(group_name, group_score)

            # Get trend info
            trend_str = None
            if driver.trend:
                t = driver.trend.unified_score
                trend_str = f"{t.direction} ({t.change_rate}, {t.delta:+.0f} from yesterday)"

            all_group_info.append({
                "group": group_name,
                "group_score": round(group_score),  # Integer for cleaner prompts
                "group_band": get_score_band(group_score),
                "group_label": _get_group_label(group_name, group_score),
                "group_guidance": group_guidance,
                "driver_meter": driver.meter_name,
                "driver_score": round(driver.unified_score),  # Integer for cleaner prompts
                "driver_label": driver.state_label,
                "driver_aspect": top_aspect,
                "driver_meaning": meter_descriptions.get(driver.meter_name, ""),
                "driver_planets": meter_planets.get(driver.meter_name, ""),
                "driver_trend": trend_str,
                "in_headline": group_name in headline_groups,
                "distance_from_neutral": abs(group_score - 50),
            })

    # Sort by distance from neutral (most extreme first)
    all_group_info.sort(key=lambda g: g["distance_from_neutral"], reverse=True)

    # Select highlights for overview:
    # 1. ALWAYS include headline groups (so LLM has context for what it's writing)
    # 2. Add most extreme non-headline groups (up to 1-2 more)
    overview_highlights = []

    # First: add ALL headline groups (critical for LLM context)
    for group in all_group_info:
        if group["in_headline"]:
            overview_highlights.append(group)

    # Then: add most extreme non-headline groups (up to ~3 total)
    for group in all_group_info:
        if len(overview_highlights) >= 3:
            break
        if not group["in_headline"]:
            # Only include if interesting (outside 40-60 range)
            if group["group_score"] < 40 or group["group_score"] > 60:
                overview_highlights.append(group)

    # Format for template - no labels, just scores and guidance
    formatted_highlights = []
    for h in overview_highlights:
        lines = [
            f"{h['group'].upper()}: {h['group_score']}/100",
            f"  Driver: {h['driver_meter']} ({h['driver_score']}/100)",
            f"  What {h['driver_meter']} is: {h['driver_meaning']}",
            f"  Planets tracked: {h['driver_planets']}",
            f"  Why: {h['driver_aspect'] or 'multiple transits'}",
        ]
        if h.get('driver_trend'):
            lines.append(f"  Trend: {h['driver_trend']}")
        lines.append(f"  How to write about it: {h['group_guidance']}")
        formatted_highlights.append("\n".join(lines))

    return {
        "highlights": overview_highlights,
        "formatted_highlights": formatted_highlights,
        "highlight_count": len(overview_highlights),
    }


def _get_meters_in_group(group_name: str) -> list[str]:
    """Return meter names in a group."""
    mapping = {
        "mind": ["clarity", "focus", "communication"],
        "heart": ["resilience", "connections", "vulnerability"],
        "body": ["energy", "drive", "strength"],
        "instincts": ["vision", "flow", "intuition", "creativity"],
        "growth": ["momentum", "ambition", "evolution", "circle"],
    }
    return mapping.get(group_name, [])


def _load_meter_overviews() -> dict[str, str]:
    """Load the overview description for each meter from JSON labels."""
    descriptions = {}
    labels_dir = os.path.join(os.path.dirname(__file__), "labels")

    meter_names = [
        "clarity", "focus", "communication",
        "resilience", "connections", "vulnerability",
        "energy", "drive", "strength",
        "vision", "flow", "intuition", "creativity",
        "momentum", "ambition", "evolution", "circle",
    ]

    for meter_name in meter_names:
        label_file = os.path.join(labels_dir, f"{meter_name}.json")
        try:
            with open(label_file, "r") as f:
                data = json.load(f)
                # Get the overview from description
                descriptions[meter_name] = data.get("description", {}).get("overview", "")
        except Exception:
            descriptions[meter_name] = ""

    return descriptions


def _load_meter_planets() -> dict[str, str]:
    """Load the natal planets tracked for each meter from JSON labels."""
    planets = {}
    labels_dir = os.path.join(os.path.dirname(__file__), "labels")

    meter_names = [
        "clarity", "focus", "communication",
        "resilience", "connections", "vulnerability",
        "energy", "drive", "strength",
        "vision", "flow", "intuition", "creativity",
        "momentum", "ambition", "evolution", "circle",
    ]

    for meter_name in meter_names:
        label_file = os.path.join(labels_dir, f"{meter_name}.json")
        try:
            with open(label_file, "r") as f:
                data = json.load(f)
                # Get natal_planets_tracked from astrological_foundation
                natal_planets = data.get("astrological_foundation", {}).get("natal_planets_tracked", [])
                if natal_planets:
                    planets[meter_name] = ", ".join([p.capitalize() for p in natal_planets])
                else:
                    planets[meter_name] = "all planets"
        except Exception:
            planets[meter_name] = ""

    return planets


def _get_score_bucket(score: float) -> str:
    """Get the bucket key for a score (0-25, 25-50, 50-75, 75-100)."""
    if score < 25:
        return "0-25"
    elif score < 50:
        return "25-50"
    elif score < 75:
        return "50-75"
    else:
        return "75-100"


def _get_group_label(group_name: str, score: float) -> str:
    """Get the state label for a group at a given score."""
    labels_dir = os.path.join(os.path.dirname(__file__), "labels", "groups")
    label_file = os.path.join(labels_dir, f"{group_name}.json")

    try:
        with open(label_file, "r") as f:
            data = json.load(f)
            bucket = _get_score_bucket(score)
            return data.get("bucket_labels", {}).get(bucket, {}).get("label", "")
    except Exception:
        return ""


def _get_group_guidance(group_name: str, score: float) -> str:
    """Get the guidance for a group at a given score (how to push through)."""
    labels_dir = os.path.join(os.path.dirname(__file__), "labels", "groups")
    label_file = os.path.join(labels_dir, f"{group_name}.json")

    try:
        with open(label_file, "r") as f:
            data = json.load(f)
            bucket = _get_score_bucket(score)
            return data.get("bucket_labels", {}).get(bucket, {}).get("guidance", "")
    except Exception:
        return ""

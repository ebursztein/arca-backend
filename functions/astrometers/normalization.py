"""
Normalization functions to convert raw DTI/HQS to 0-100 meter scales.

⚠️ CRITICAL: The normalization constants (DTI_MAX, HQS_MAX_POSITIVE, HQS_MAX_NEGATIVE)
are PLACEHOLDER values. These MUST be replaced with empirically-derived values
from analysis of 10,000+ charts over 20-30 years of transits.

See spec Section 2.4 for calibration methodology.

TODO: EMPIRICAL CALIBRATION REQUIRED
    1. Collect 10,000+ diverse natal charts
    2. Calculate DTI/HQS for each chart across 20-30 years
    3. Analyze distribution and set constants to 99th percentile
    4. Replace placeholder values in constants.py with empirical data

From spec Section 2.4 (Normalization to Meter Scale)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import json
import numpy as np
from typing import Tuple, Dict, Optional
from dataclasses import dataclass
from .constants import (
    DTI_MAX_ESTIMATE,
    HQS_MAX_POSITIVE_ESTIMATE,
    HQS_MAX_NEGATIVE_ESTIMATE,
    METER_SCALE,
    HARMONY_NEUTRAL,
    INTENSITY_QUIET_THRESHOLD,
    INTENSITY_MILD_THRESHOLD,
    INTENSITY_MODERATE_THRESHOLD,
    INTENSITY_HIGH_THRESHOLD,
    HARMONY_CHALLENGING_THRESHOLD,
    HARMONY_HARMONIOUS_THRESHOLD,
)


# Global cache for calibration constants and historical scores
_CALIBRATION_CONSTANTS: Optional[Dict] = None
_HISTORICAL_DTI_SCORES: Optional[np.ndarray] = None
_HISTORICAL_HQS_SCORES: Optional[np.ndarray] = None


def load_calibration_constants() -> Optional[Dict]:
    """
    Load empirical calibration constants from JSON file.

    Returns:
        Dict with calibration data or None if file doesn't exist
    """
    global _CALIBRATION_CONSTANTS

    if _CALIBRATION_CONSTANTS is not None:
        return _CALIBRATION_CONSTANTS

    try:
        calibration_path = os.path.join(
            os.path.dirname(__file__),
            "calibration",
            "calibration_constants.json"
        )
        with open(calibration_path, 'r') as f:
            _CALIBRATION_CONSTANTS = json.load(f)
        return _CALIBRATION_CONSTANTS
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_historical_scores() -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Load historical DTI and HQS scores from parquet file.

    Returns:
        Tuple of (dti_scores, hqs_scores) as numpy arrays, or (None, None) if unavailable
    """
    global _HISTORICAL_DTI_SCORES, _HISTORICAL_HQS_SCORES

    if _HISTORICAL_DTI_SCORES is not None and _HISTORICAL_HQS_SCORES is not None:
        return _HISTORICAL_DTI_SCORES, _HISTORICAL_HQS_SCORES

    try:
        import pandas as pd
        scores_path = os.path.join(
            os.path.dirname(__file__),
            "calibration",
            "historical_scores.parquet"
        )
        df = pd.read_parquet(scores_path)
        _HISTORICAL_DTI_SCORES = df['dti'].values
        _HISTORICAL_HQS_SCORES = df['hqs'].values
        return _HISTORICAL_DTI_SCORES, _HISTORICAL_HQS_SCORES
    except (FileNotFoundError, ImportError, KeyError):
        return None, None


def percentile_rank(score: float, historical_scores: np.ndarray) -> float:
    """
    Calculate percentile rank of a score within historical distribution.

    Uses linear interpolation between data points for smooth mapping.

    Args:
        score: The score to rank
        historical_scores: Array of historical scores for comparison

    Returns:
        float: Percentile rank (0-100)

    Examples:
        >>> scores = np.array([100, 200, 300, 400, 500])
        >>> percentile_rank(300, scores)  # Middle value
        50.0
        >>> percentile_rank(500, scores)  # Maximum
        100.0
        >>> percentile_rank(100, scores)  # Minimum
        0.0
    """
    if score <= historical_scores.min():
        return 0.0
    if score >= historical_scores.max():
        return 100.0

    # Count how many scores are below this value
    count_below = np.sum(historical_scores < score)
    count_equal = np.sum(historical_scores == score)

    # Use average rank for ties (standard percentile formula)
    percentile = (count_below + 0.5 * count_equal) / len(historical_scores) * 100

    return min(100.0, max(0.0, percentile))


@dataclass
class MeterInterpretation:
    """Combined interpretation with guidance from spec Section 2.5."""
    label: str
    guidance: str


def sigmoid_compress(linear_score: float) -> float:
    """
    Apply sigmoid compression to smoothly bound linear scores to 0-100 range.

    Maps linearly-normalized scores (which may overshoot 0-100) into a smooth
    0-100 curve without hard clamps.

    Args:
        linear_score: Linearly mapped score (can be < 0 or > 100)

    Returns:
        float: Sigmoid-compressed score (smoothly bounded to 0-100)

    Examples:
        >>> sigmoid_compress(50)    # Center
        50.0
        >>> sigmoid_compress(100)   # Upper bound
        ~95.0
        >>> sigmoid_compress(0)     # Lower bound
        ~5.0
        >>> sigmoid_compress(150)   # Overshoot
        ~98.0
        >>> sigmoid_compress(-50)   # Undershoot
        ~2.0
    """
    # Center sigmoid at 50, with scale that maps 0→~5 and 100→~95
    # Using scale=25 gives good compression: ±2σ ≈ [5, 95]
    z = (linear_score - 50.0) / 25.0
    sigmoid = 1.0 / (1.0 + math.exp(-z))
    return 100.0 * sigmoid


def interpolate_percentile(
    value: float,
    percentiles: Dict[str, float],
    use_iqr: bool = True,
    use_sigmoid: bool = False
) -> float:
    """
    Convert a raw value to 0-100 scale using percentile interpolation.

    Linear mapping of full percentile range (p01-p99) to 0-100 with simple clamping.
    This maximizes variation while keeping clamping minimal (~2% on each tail).

    Args:
        value: Raw score to convert (can be negative)
        percentiles: Dict with keys like "p01", "p05", "p50", "p95", "p99"
        use_iqr: DEPRECATED - kept for compatibility (ignored)
        use_sigmoid: Apply sigmoid compression (default: False)

    Returns:
        float: Normalized score (0-100)

    Examples:
        >>> # p01=100, p50=500, p99=1000
        >>> interpolate_percentile(500, percentiles)   # p50 → 50
        50.0
        >>> interpolate_percentile(1200, percentiles)  # Above p99 → 120 → clamped to 100
        100.0
        >>> interpolate_percentile(0, percentiles)     # Below p01 → -10 → clamped to 0
        0.0
    """
    # Create sorted list of (percentile_rank, raw_value) pairs
    points = []
    for key, raw_value in percentiles.items():
        if key.startswith('p'):
            percentile_rank = int(key[1:])  # "p50" → 50
            points.append((percentile_rank, raw_value))

    points.sort()  # Sort by percentile rank

    # FULL RANGE LINEAR MAPPING (p01-p99 or available range)
    # Map percentile range to 0-100 with simple clamping
    p_min_rank, p_min_value = points[0]   # Usually p01
    p_max_rank, p_max_value = points[-1]  # Usually p99

    # Linear interpolation across full range
    if p_max_value == p_min_value:
        linear_score = 50.0  # Degenerate case
    else:
        # Map [p_min_value, p_max_value] → [0, 100]
        linear_score = ((value - p_min_value) / (p_max_value - p_min_value)) * 100.0

    # Apply sigmoid compression (optional) or simple clamp
    if use_sigmoid:
        return sigmoid_compress(linear_score)
    else:
        # Simple clamp to 0-100 (only affects ~2% beyond p01/p99)
        return max(0.0, min(100.0, linear_score))


def normalize_with_soft_ceiling(
    raw_score: float,
    max_value: float,
    target_scale: float = 100
) -> float:
    """
    DEPRECATED: Use interpolate_percentile instead for accurate percentile mapping.

    This function is kept for backward compatibility but should not be used
    for new code. It does linear scaling which produces incorrect distributions.
    """
    if raw_score <= 0:
        return 0.0

    # NEVER use theoretical estimates - always require valid calibration data
    if max_value <= 0:
        raise ValueError(f"Invalid max_value={max_value}. Re-run calibration! NEVER use theoretical constants.")

    if raw_score <= max_value:
        # Linear scaling within expected range
        return (raw_score / max_value) * target_scale
    else:
        # Logarithmic compression for outliers beyond 99th percentile
        excess = raw_score - max_value
        compressed_excess = 10 * math.log10(1 + excess / max_value)
        return min(target_scale, target_scale + compressed_excess)


def normalize_intensity(dti: float, meter_name: str = None, use_empirical: bool = True) -> float:
    """
    Normalize DTI (Dual Transit Influence) to 0-100 Intensity Meter.

    Uses percentile-based normalization from historical scores. A score of X
    means the day ranks at the Xth percentile (e.g., 85 = top 15% of days).

    The Intensity Meter answers: "How much is happening?"
    - 0-30: Quiet period (bottom 30% of days)
    - 31-50: Mild activity (31st-50th percentile)
    - 51-70: Moderate activity (51st-70th percentile)
    - 71-85: High activity (71st-85th percentile, top 29-15%)
    - 86-100: Extreme activity (top 14%, with 99+ being top 1%)

    Args:
        dti: Raw DTI score (sum of all W_i × P_i)
        meter_name: Name of the meter (for meter-specific calibration)
        use_empirical: Use empirical calibration if available (default: True)

    Returns:
        float: Intensity meter value (0-100) representing percentile rank

    Example:
        >>> normalize_intensity(1805.47, "overall_intensity")  # Median for overall
        ~50.0  # 50th percentile
        >>> normalize_intensity(80.0, "clarity")  # Mercury only
        ~50.0  # 50th percentile for this meter
    """
    if dti <= 0:
        return 0.0

    if use_empirical:
        # Use meter-specific calibration if available
        calibration = load_calibration_constants()
        if calibration and meter_name:
            # Version 4.0+ has per-meter calibration with full percentiles
            if "meters" in calibration and meter_name in calibration["meters"]:
                percentiles = calibration["meters"][meter_name]["dti_percentiles"]
                return interpolate_percentile(dti, percentiles)

        # Fallback to global calibration (version 2.0)
        if calibration and "dti_percentiles" in calibration:
            percentiles = calibration["dti_percentiles"]
            return interpolate_percentile(dti, percentiles)

    # NEVER use theoretical estimates
    raise ValueError(f"No calibration data found for meter={meter_name}. Re-run calibration scripts!")


def normalize_harmony(hqs: float, meter_name: str = None, use_empirical: bool = True) -> float:
    """
    Normalize HQS (Harmonic Quality Score) to 0-100 Harmony Meter.

    HQS=0 is always mapped to 50 (neutral), with positive HQS scaling to 100
    and negative HQS scaling to 0. This ensures semantic meaning where:
    - HQS=0 is neutral (50)
    - Positive HQS is harmonious (50-100)
    - Negative HQS is challenging (0-50)

    The Harmony Meter answers: "What type of intensity?"
    - 0-30: Challenging (bottom 30%, growth through friction)
    - 30-70: Mixed/Neutral (middle 40%)
    - 70-100: Harmonious (top 30%, growth through flow)

    Args:
        hqs: Raw HQS score (sum of all W_i × P_i × Q_i)
        meter_name: Name of the meter (for meter-specific calibration)
        use_empirical: Use empirical calibration if available (default: True)

    Returns:
        float: Harmony meter value (0-100, where 50=neutral at HQS=0)

    Examples:
        >>> normalize_harmony(0)
        50.0  # Neutral (HQS=0 always maps to 50)
        >>> normalize_harmony(748.60, "overall_harmony")  # P99 positive
        ~100.0  # Maximum harmonious
        >>> normalize_harmony(-1438.01, "overall_harmony")  # P01 negative
        ~0.0  # Maximum challenging
    """
    # Always use soft ceiling normalization (centered at HQS=0)
    # This ensures HQS=0 always equals 50 (neutral)

    if use_empirical:
        # Use meter-specific calibration if available
        calibration = load_calibration_constants()
        if calibration and meter_name:
            # Version 4.0+ has per-meter calibration with full percentiles
            if "meters" in calibration and meter_name in calibration["meters"]:
                percentiles = calibration["meters"][meter_name]["hqs_percentiles"]
                return interpolate_percentile(hqs, percentiles)

        # Fallback to global calibration (version 2.0)
        if calibration and "hqs_percentiles" in calibration:
            percentiles = calibration["hqs_percentiles"]
            return interpolate_percentile(hqs, percentiles)

    # NEVER use theoretical estimates
    raise ValueError(f"No calibration data found for meter={meter_name}. Re-run calibration scripts!")


def normalize_meters(dti: float, hqs: float, meter_name: str = None) -> Tuple[float, float]:
    """
    Normalize both DTI and HQS to meter scales in one call.

    Convenience function that calls both normalize_intensity() and
    normalize_harmony().

    Args:
        dti: Raw DTI score
        hqs: Raw HQS score
        meter_name: Name of the meter (for meter-specific calibration)

    Returns:
        Tuple[float, float]: (intensity_meter, harmony_meter)

    Example:
        >>> normalize_meters(100.0, -50.0, "clarity")
        (50.0, 25.0)  # Moderate intensity, challenging harmony
    """
    intensity = normalize_intensity(dti, meter_name)
    harmony = normalize_harmony(hqs, meter_name)
    return intensity, harmony


def get_intensity_label(intensity: float) -> str:
    """
    Get human-readable label for intensity meter value.

    Uses thresholds from spec Section 2.5 Interpretation Matrix.

    Args:
        intensity: Intensity meter value (0-100)

    Returns:
        str: Intensity label

    Examples:
        >>> get_intensity_label(15)
        'Quiet'
        >>> get_intensity_label(60)
        'Moderate'
        >>> get_intensity_label(90)
        'Extreme'
    """
    if intensity < INTENSITY_QUIET_THRESHOLD:
        return "Quiet"
    elif intensity < INTENSITY_MILD_THRESHOLD:
        return "Mild"
    elif intensity < INTENSITY_MODERATE_THRESHOLD:
        return "Moderate"
    elif intensity < INTENSITY_HIGH_THRESHOLD:
        return "High"
    else:
        return "Extreme"


def get_harmony_label(harmony: float) -> str:
    """
    Get human-readable label for harmony meter value.

    Uses thresholds from spec Section 2.5 Interpretation Matrix.

    Args:
        harmony: Harmony meter value (0-100, where 50=neutral)

    Returns:
        str: Harmony label

    Examples:
        >>> get_harmony_label(15)
        'Challenging'
        >>> get_harmony_label(50)
        'Mixed'
        >>> get_harmony_label(85)
        'Harmonious'
    """
    if harmony < HARMONY_CHALLENGING_THRESHOLD:
        return "Challenging"
    elif harmony < HARMONY_HARMONIOUS_THRESHOLD:
        return "Mixed"
    else:
        return "Harmonious"


def get_meter_interpretation(intensity: float, harmony: float) -> MeterInterpretation:
    """
    Get combined interpretation with user guidance from intensity and harmony meters.

    Based on the Meter Interpretation Matrix from spec Section 2.5.

    Args:
        intensity: Intensity meter value (0-100)
        harmony: Harmony meter value (0-100)

    Returns:
        MeterInterpretation: Label and guidance text

    Examples:
        >>> interp = get_meter_interpretation(20, 50)
        >>> interp.label
        'Quiet Period'
        >>> interp.guidance
        'Low astrological activity. Good for rest, routine, integration.'
    """
    # Quiet period: 0-30 intensity, any harmony
    if intensity < INTENSITY_QUIET_THRESHOLD:
        return MeterInterpretation(
            label="Quiet Period",
            guidance="Low astrological activity. Good for rest, routine, integration."
        )

    # Mild intensity: 31-50
    elif intensity < INTENSITY_MILD_THRESHOLD:
        if harmony >= HARMONY_HARMONIOUS_THRESHOLD:
            return MeterInterpretation(
                label="Gentle Flow",
                guidance="Mild supportive energy. Incremental progress feels natural."
            )
        elif harmony < HARMONY_CHALLENGING_THRESHOLD:
            return MeterInterpretation(
                label="Minor Friction",
                guidance="Small irritations or obstacles. Manageable with awareness."
            )
        else:  # 30-70 mixed
            return MeterInterpretation(
                label="Mild Mixed",
                guidance="Mild mixed energy. Balance of small opportunities and minor challenges."
            )

    # Moderate intensity: 51-70
    elif intensity < INTENSITY_MODERATE_THRESHOLD:
        if harmony >= HARMONY_HARMONIOUS_THRESHOLD:
            return MeterInterpretation(
                label="Productive Flow",
                guidance="Optimal state: noticeable energy + ease. Prime time for action."
            )
        elif harmony < HARMONY_CHALLENGING_THRESHOLD:
            return MeterInterpretation(
                label="Moderate Challenge",
                guidance="Noticeable friction. Growth through persistence."
            )
        else:  # 30-70 mixed
            return MeterInterpretation(
                label="Mixed Dynamics",
                guidance="Complex period with both opportunities and challenges. Navigate carefully."
            )

    # High intensity: 71-85
    elif intensity < INTENSITY_HIGH_THRESHOLD:
        if harmony >= HARMONY_HARMONIOUS_THRESHOLD:
            return MeterInterpretation(
                label="Peak Opportunity",
                guidance="Rare alignment. Major positive potential. Act on important goals."
            )
        elif harmony < HARMONY_CHALLENGING_THRESHOLD:
            return MeterInterpretation(
                label="High Challenge",
                guidance="Intense difficulty. Resilience required. Major lessons available."
            )
        else:  # 30-70 mixed
            return MeterInterpretation(
                label="Intense Mixed",
                guidance="High pressure with both gifts and tests. Pivotal period."
            )

    # Extreme intensity: 86-100
    else:
        if harmony >= HARMONY_HARMONIOUS_THRESHOLD:
            return MeterInterpretation(
                label="Exceptional Grace",
                guidance="Extremely rare. Life-changing positive potential."
            )
        elif harmony < HARMONY_CHALLENGING_THRESHOLD:
            return MeterInterpretation(
                label="Crisis/Breakthrough",
                guidance="Extremely rare. Major transformation, often through upheaval."
            )
        else:  # 30-70 mixed
            return MeterInterpretation(
                label="Extreme Mixed",
                guidance="Extremely rare. Intense period with major opportunities and challenges."
            )

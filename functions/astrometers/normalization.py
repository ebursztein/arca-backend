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


def normalize_with_soft_ceiling(
    raw_score: float,
    max_value: float,
    target_scale: float = 100
) -> float:
    """
    Normalize score with logarithmic compression for outliers.

    Scores within the expected maximum (99th percentile) scale linearly.
    Scores beyond are compressed logarithmically to prevent extreme outliers
    from breaking the meter scale.

    Args:
        raw_score: The raw score to normalize (DTI or HQS)
        max_value: Expected maximum (99th percentile from empirical data)
        target_scale: Target scale (default 100, or 50 for half-scale)

    Returns:
        float: Normalized score, capped at target_scale

    Examples:
        >>> normalize_with_soft_ceiling(100, 200, 100)
        50.0  # Linear: within expected range
        >>> normalize_with_soft_ceiling(200, 200, 100)
        100.0  # At expected maximum
        >>> normalize_with_soft_ceiling(300, 200, 100)
        100.0  # Outlier: compressed and capped

    Math:
        - If raw_score <= max_value:
            result = (raw_score / max_value) × target_scale
        - If raw_score > max_value:
            excess = raw_score - max_value
            compressed = 10 × log₁₀(1 + excess / max_value)
            result = min(target_scale, target_scale + compressed)
    """
    if raw_score <= 0:
        return 0.0

    if raw_score <= max_value:
        # Linear scaling within expected range
        return (raw_score / max_value) * target_scale
    else:
        # Logarithmic compression for outliers beyond 99th percentile
        excess = raw_score - max_value
        compressed_excess = 10 * math.log10(1 + excess / max_value)
        return min(target_scale, target_scale + compressed_excess)


def normalize_intensity(dti: float, use_empirical: bool = True) -> float:
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
        use_empirical: Use empirical calibration if available (default: True)

    Returns:
        float: Intensity meter value (0-100) representing percentile rank

    Example:
        >>> normalize_intensity(1805.47)  # Median from empirical data
        ~50.0  # 50th percentile
        >>> normalize_intensity(3575.73)  # P99 from empirical data
        ~99.0  # 99th percentile (top 1%)
    """
    if dti <= 0:
        return 0.0

    if use_empirical:
        # Try percentile-based normalization first
        dti_scores, _ = load_historical_scores()
        if dti_scores is not None:
            return percentile_rank(dti, dti_scores)

        # Fallback to soft ceiling with P99
        calibration = load_calibration_constants()
        if calibration:
            dti_max = calibration["dti_percentiles"]["p99"]
            return normalize_with_soft_ceiling(dti, dti_max, METER_SCALE)

    # Ultimate fallback to theoretical estimate
    return normalize_with_soft_ceiling(dti, DTI_MAX_ESTIMATE, METER_SCALE)


def normalize_harmony(hqs: float, use_empirical: bool = True) -> float:
    """
    Normalize HQS (Harmonic Quality Score) to 0-100 Harmony Meter.

    Uses percentile-based normalization centered at 50 (neutral). The score
    represents where this day ranks in the harmony distribution:
    - Score 50 = neutral harmony (HQS around 0)
    - Score 75 = 75th percentile (more harmonious than 75% of days)
    - Score 25 = 25th percentile (more challenging than 75% of days)

    The Harmony Meter answers: "What type of intensity?"
    - 0-30: Challenging (bottom 30%, growth through friction)
    - 30-70: Mixed/Neutral (middle 40%)
    - 70-100: Harmonious (top 30%, growth through flow)

    Args:
        hqs: Raw HQS score (sum of all W_i × P_i × Q_i)
        use_empirical: Use empirical calibration if available (default: True)

    Returns:
        float: Harmony meter value (0-100, where 50=neutral)

    Examples:
        >>> normalize_harmony(0)
        ~50.0  # Neutral (around median)
        >>> normalize_harmony(748.60)  # P99 positive from empirical
        ~99.0  # Top 1% harmonious
        >>> normalize_harmony(-1438.01)  # P01 negative from empirical
        ~1.0  # Bottom 1% challenging
    """
    if use_empirical:
        # Try percentile-based normalization first
        _, hqs_scores = load_historical_scores()
        if hqs_scores is not None:
            # Calculate percentile rank across full HQS distribution
            # This naturally centers around median (HQS ~ -200)
            return percentile_rank(hqs, hqs_scores)

        # Fallback to soft ceiling with P99/P01
        calibration = load_calibration_constants()
        if calibration:
            hqs_max_pos = calibration["hqs_percentiles"]["p99"]
            hqs_max_neg = abs(calibration["hqs_percentiles"]["p01"])

            if hqs >= 0:
                # Positive HQS: harmonious transits (50 to 100)
                normalized = normalize_with_soft_ceiling(
                    hqs, hqs_max_pos, METER_SCALE / 2
                )
                return HARMONY_NEUTRAL + normalized
            else:
                # Negative HQS: challenging transits (0 to 50)
                normalized = normalize_with_soft_ceiling(
                    abs(hqs), hqs_max_neg, METER_SCALE / 2
                )
                return HARMONY_NEUTRAL - normalized

    # Ultimate fallback to theoretical estimate
    if hqs >= 0:
        # Positive HQS: harmonious transits (50 to 100)
        normalized = normalize_with_soft_ceiling(
            hqs, HQS_MAX_POSITIVE_ESTIMATE, METER_SCALE / 2
        )
        return HARMONY_NEUTRAL + normalized
    else:
        # Negative HQS: challenging transits (0 to 50)
        normalized = normalize_with_soft_ceiling(
            abs(hqs), HQS_MAX_NEGATIVE_ESTIMATE, METER_SCALE / 2
        )
        return HARMONY_NEUTRAL - normalized


def normalize_meters(dti: float, hqs: float) -> Tuple[float, float]:
    """
    Normalize both DTI and HQS to meter scales in one call.

    Convenience function that calls both normalize_intensity() and
    normalize_harmony().

    Args:
        dti: Raw DTI score
        hqs: Raw HQS score

    Returns:
        Tuple[float, float]: (intensity_meter, harmony_meter)

    Example:
        >>> normalize_meters(100.0, -50.0)
        (50.0, 25.0)  # Moderate intensity, challenging harmony
    """
    intensity = normalize_intensity(dti)
    harmony = normalize_harmony(hqs)
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

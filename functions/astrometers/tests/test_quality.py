"""
Tests for quality factor (Q_i) calculations.

Tests the harmonic nature of aspects:
- Fixed quality for trine/sextile/square/opposition
- Dynamic conjunction quality based on planet combinations
- Quality labels for all possible values
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from astro import Planet, AspectType
from astrometers.quality import (
    calculate_quality_factor,
    get_quality_label,
)
from astrometers.constants import (
    QUALITY_TRINE,
    QUALITY_SEXTILE,
    QUALITY_SQUARE,
    QUALITY_OPPOSITION,
    CONJUNCTION_DOUBLE_BENEFIC,
    CONJUNCTION_DOUBLE_MALEFIC,
    CONJUNCTION_BENEFIC_MALEFIC,
    CONJUNCTION_TRANSFORMATIONAL,
    CONJUNCTION_DEFAULT,
    QUALITY_BLISSFUL_THRESHOLD,
    QUALITY_VERY_HARMONIOUS_THRESHOLD,
    QUALITY_HARMONIOUS_THRESHOLD,
    QUALITY_NEUTRAL_THRESHOLD,
    QUALITY_CHALLENGING_THRESHOLD,
    QUALITY_VERY_CHALLENGING_THRESHOLD,
)


# =============================================================================
# Fixed Quality Scores Tests
# =============================================================================

def test_trine_quality():
    """Trine aspects have quality factor +1.0."""
    quality = calculate_quality_factor(AspectType.TRINE, Planet.SUN, Planet.JUPITER)
    assert quality == QUALITY_TRINE
    assert quality == 1.0


def test_sextile_quality():
    """Sextile aspects have quality factor +1.0."""
    quality = calculate_quality_factor(AspectType.SEXTILE, Planet.MOON, Planet.VENUS)
    assert quality == QUALITY_SEXTILE
    assert quality == 1.0


def test_square_quality():
    """Square aspects have quality factor -1.0."""
    quality = calculate_quality_factor(AspectType.SQUARE, Planet.SUN, Planet.SATURN)
    assert quality == QUALITY_SQUARE
    assert quality == -1.0


def test_opposition_quality():
    """Opposition aspects have quality factor -1.0."""
    quality = calculate_quality_factor(AspectType.OPPOSITION, Planet.MOON, Planet.MARS)
    assert quality == QUALITY_OPPOSITION
    assert quality == -1.0


# =============================================================================
# Conjunction Quality Tests - Double Benefic
# =============================================================================

def test_conjunction_venus_jupiter():
    """Venus-Jupiter conjunction is double benefic (+0.8)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.VENUS, Planet.JUPITER)
    assert quality == CONJUNCTION_DOUBLE_BENEFIC
    assert quality == 0.8


def test_conjunction_jupiter_venus():
    """Jupiter-Venus conjunction (reversed order) is also +0.8."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.JUPITER, Planet.VENUS)
    assert quality == CONJUNCTION_DOUBLE_BENEFIC
    assert quality == 0.8


# =============================================================================
# Conjunction Quality Tests - Double Malefic
# =============================================================================

def test_conjunction_mars_saturn():
    """Mars-Saturn conjunction is double malefic (-0.8)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.MARS, Planet.SATURN)
    assert quality == CONJUNCTION_DOUBLE_MALEFIC
    assert quality == -0.8


def test_conjunction_saturn_mars():
    """Saturn-Mars conjunction (reversed order) is also -0.8."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.SATURN, Planet.MARS)
    assert quality == CONJUNCTION_DOUBLE_MALEFIC
    assert quality == -0.8


# =============================================================================
# Conjunction Quality Tests - Benefic-Malefic Mix
# =============================================================================

def test_conjunction_venus_mars():
    """Venus-Mars conjunction is benefic-malefic mix (+0.2)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.VENUS, Planet.MARS)
    assert quality == CONJUNCTION_BENEFIC_MALEFIC
    assert quality == 0.2


def test_conjunction_jupiter_saturn():
    """Jupiter-Saturn conjunction is benefic-malefic mix (+0.2)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.JUPITER, Planet.SATURN)
    assert quality == CONJUNCTION_BENEFIC_MALEFIC
    assert quality == 0.2


def test_conjunction_mars_venus():
    """Mars-Venus conjunction (reversed) is also +0.2."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.MARS, Planet.VENUS)
    assert quality == CONJUNCTION_BENEFIC_MALEFIC
    assert quality == 0.2


def test_conjunction_saturn_jupiter():
    """Saturn-Jupiter conjunction (reversed) is also +0.2."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.SATURN, Planet.JUPITER)
    assert quality == CONJUNCTION_BENEFIC_MALEFIC
    assert quality == 0.2


# =============================================================================
# Conjunction Quality Tests - Transformational Planets
# =============================================================================

def test_conjunction_uranus_sun():
    """Uranus conjunction has slight tension (-0.3)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.URANUS, Planet.SUN)
    assert quality == CONJUNCTION_TRANSFORMATIONAL
    assert quality == -0.3


def test_conjunction_neptune_moon():
    """Neptune conjunction has slight tension (-0.3)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.NEPTUNE, Planet.MOON)
    assert quality == CONJUNCTION_TRANSFORMATIONAL
    assert quality == -0.3


def test_conjunction_pluto_venus():
    """Pluto conjunction has slight tension (-0.3)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.PLUTO, Planet.VENUS)
    assert quality == CONJUNCTION_TRANSFORMATIONAL
    assert quality == -0.3


def test_conjunction_transformational_takes_precedence_over_benefic():
    """Transformational nature takes precedence over benefic."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.PLUTO, Planet.VENUS)
    assert quality == CONJUNCTION_TRANSFORMATIONAL
    assert quality == -0.3


def test_conjunction_transformational_takes_precedence_over_malefic():
    """Transformational nature takes precedence over malefic."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.URANUS, Planet.MARS)
    assert quality == CONJUNCTION_TRANSFORMATIONAL
    assert quality == -0.3


# =============================================================================
# Conjunction Quality Tests - Default (Neutral)
# =============================================================================

def test_conjunction_sun_moon():
    """Sun-Moon conjunction is neutral (0.0)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.SUN, Planet.MOON)
    assert quality == CONJUNCTION_DEFAULT
    assert quality == 0.0


def test_conjunction_sun_mercury():
    """Sun-Mercury conjunction is neutral (0.0)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.SUN, Planet.MERCURY)
    assert quality == CONJUNCTION_DEFAULT
    assert quality == 0.0


def test_conjunction_mercury_moon():
    """Mercury-Moon conjunction is neutral (0.0)."""
    quality = calculate_quality_factor(AspectType.CONJUNCTION, Planet.MERCURY, Planet.MOON)
    assert quality == CONJUNCTION_DEFAULT
    assert quality == 0.0


# =============================================================================
# Quality Label Tests (Updated for V2 Optimistic Model thresholds)
# =============================================================================

def test_quality_label_blissful():
    """Quality >= 1.1 returns 'Blissful'."""
    assert get_quality_label(1.1) == "Blissful"
    assert get_quality_label(1.5) == "Blissful"


def test_quality_label_very_harmonious():
    """Quality >= 0.8 and < 1.1 returns 'Very Harmonious'."""
    assert get_quality_label(0.8) == "Very Harmonious"
    assert get_quality_label(1.0) == "Very Harmonious"  # 1.0 < 1.1 threshold


def test_quality_label_harmonious():
    """Quality >= 0.2 and < 0.8 returns 'Harmonious'."""
    assert get_quality_label(0.2) == "Harmonious"
    assert get_quality_label(0.5) == "Harmonious"
    assert get_quality_label(0.7) == "Harmonious"


def test_quality_label_neutral():
    """Quality >= -0.3 and < 0.2 returns 'Neutral'."""
    assert get_quality_label(0.0) == "Neutral"
    assert get_quality_label(0.1) == "Neutral"
    assert get_quality_label(-0.3) == "Neutral"


def test_quality_label_challenging():
    """Quality >= -0.7 and < -0.3 returns 'Challenging'."""
    assert get_quality_label(-0.4) == "Challenging"
    assert get_quality_label(-0.5) == "Challenging"
    assert get_quality_label(-0.7) == "Challenging"


def test_quality_label_very_challenging():
    """Quality >= -0.85 and < -0.7 returns 'Very Challenging'."""
    assert get_quality_label(-0.8) == "Very Challenging"
    assert get_quality_label(-0.85) == "Very Challenging"


def test_quality_label_extremely_challenging():
    """Quality < -0.85 returns 'Extremely Challenging'."""
    assert get_quality_label(-0.9) == "Extremely Challenging"
    assert get_quality_label(-1.0) == "Extremely Challenging"
    assert get_quality_label(-1.5) == "Extremely Challenging"


def test_quality_labels_at_thresholds():
    """Test labels exactly at threshold boundaries."""
    # Test each threshold exactly
    assert get_quality_label(QUALITY_BLISSFUL_THRESHOLD) == "Blissful"
    assert get_quality_label(QUALITY_VERY_HARMONIOUS_THRESHOLD) == "Very Harmonious"
    assert get_quality_label(QUALITY_HARMONIOUS_THRESHOLD) == "Harmonious"
    assert get_quality_label(QUALITY_NEUTRAL_THRESHOLD) == "Neutral"
    assert get_quality_label(QUALITY_CHALLENGING_THRESHOLD) == "Challenging"
    assert get_quality_label(QUALITY_VERY_CHALLENGING_THRESHOLD) == "Very Challenging"


# =============================================================================
# Integration Tests with All Aspect Types
# =============================================================================

def test_all_harmonious_aspects_positive():
    """All harmonious aspects (trine, sextile) have positive quality."""
    harmonious_aspects = [AspectType.TRINE, AspectType.SEXTILE]
    for aspect in harmonious_aspects:
        quality = calculate_quality_factor(aspect, Planet.SUN, Planet.JUPITER)
        assert quality > 0, f"{aspect} should be positive"


def test_all_challenging_aspects_negative():
    """All challenging aspects (square, opposition) have negative quality."""
    challenging_aspects = [AspectType.SQUARE, AspectType.OPPOSITION]
    for aspect in challenging_aspects:
        quality = calculate_quality_factor(aspect, Planet.SUN, Planet.SATURN)
        assert quality < 0, f"{aspect} should be negative"


def test_conjunction_quality_range():
    """All conjunction qualities are within -0.8 to +0.8 range."""
    test_cases = [
        (Planet.VENUS, Planet.JUPITER),   # +0.8
        (Planet.MARS, Planet.SATURN),     # -0.8
        (Planet.VENUS, Planet.MARS),      # +0.2
        (Planet.SUN, Planet.MOON),        # 0.0
        (Planet.URANUS, Planet.SUN),      # -0.3
    ]
    for planet1, planet2 in test_cases:
        quality = calculate_quality_factor(AspectType.CONJUNCTION, planet1, planet2)
        assert -0.8 <= quality <= 0.8, f"{planet1}-{planet2} out of range"


# =============================================================================
# Edge Cases and Validation
# =============================================================================

def test_invalid_aspect_type_raises_error():
    """Invalid aspect type should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown aspect type"):
        calculate_quality_factor("invalid_aspect", Planet.SUN, Planet.MOON)


def test_quality_factor_symmetric():
    """Conjunction quality should be symmetric (order doesn't matter)."""
    quality1 = calculate_quality_factor(AspectType.CONJUNCTION, Planet.VENUS, Planet.MARS)
    quality2 = calculate_quality_factor(AspectType.CONJUNCTION, Planet.MARS, Planet.VENUS)
    assert quality1 == quality2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

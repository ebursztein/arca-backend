"""
Tests for weightage factor (W_i) calculations.

Tests the formula: W_i = (Planet_Base + Dignity_Score + Ruler_Bonus) × House_Multiplier × Sensitivity_Factor
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from astro import Planet, ZodiacSign
from astrometers.weightage import (
    calculate_weightage,
    calculate_chart_ruler,
    get_weightage_breakdown,
)
from astrometers.constants import (
    PLANET_BASE_SCORES,
    CHART_RULER_BONUS,
    DEFAULT_SENSITIVITY,
)


# =============================================================================
# Spec Example Test
# =============================================================================

def test_spec_example_sun_in_leo_10th_house_chart_ruler():
    """
    Test the exact example from spec Section 2.3.A:
    Natal Sun in Leo (Domicile) in 10th House (Angular), Chart Ruler
    Expected: (10 + 5 + 5) × 3 × 1.0 = 60
    """
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.LEO,
        house_number=10,
        ascendant_sign=ZodiacSign.LEO  # Leo rising makes Sun the chart ruler
    )
    assert weightage == 60.0


# =============================================================================
# Planet Base Score Tests
# =============================================================================

def test_luminary_base_scores():
    """Sun and Moon have base score of 10."""
    # Sun in neutral position, cadent house, no bonuses
    sun_weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.GEMINI,  # Neutral
        house_number=3  # Cadent (×1)
    )
    # (10 + 0 + 0) × 1 × 1.0 = 10
    assert sun_weightage == 10.0

    # Moon in neutral position, cadent house
    moon_weightage = calculate_weightage(
        planet=Planet.MOON,
        sign=ZodiacSign.ARIES,  # Neutral
        house_number=3  # Cadent
    )
    # (10 + 0 + 0) × 1 × 1.0 = 10
    assert moon_weightage == 10.0


def test_personal_planet_base_scores():
    """Mercury, Venus, Mars have base score of 7."""
    mercury_weightage = calculate_weightage(
        planet=Planet.MERCURY,
        sign=ZodiacSign.LEO,  # Neutral
        house_number=3  # Cadent
    )
    # (7 + 0 + 0) × 1 × 1.0 = 7
    assert mercury_weightage == 7.0


def test_social_planet_base_scores():
    """Jupiter and Saturn have base score of 5."""
    jupiter_weightage = calculate_weightage(
        planet=Planet.JUPITER,
        sign=ZodiacSign.LEO,  # Neutral
        house_number=3  # Cadent
    )
    # (5 + 0 + 0) × 1 × 1.0 = 5
    assert jupiter_weightage == 5.0


def test_outer_planet_base_scores():
    """Uranus, Neptune, Pluto have base score of 3."""
    uranus_weightage = calculate_weightage(
        planet=Planet.URANUS,
        sign=ZodiacSign.ARIES,  # Neutral (no dignity)
        house_number=3  # Cadent
    )
    # (3 + 0 + 0) × 1 × 1.0 = 3
    assert uranus_weightage == 3.0


# =============================================================================
# House Multiplier Tests
# =============================================================================

def test_angular_house_multiplier():
    """Angular houses (1, 4, 7, 10) have multiplier of ×3."""
    for house in [1, 4, 7, 10]:
        weightage = calculate_weightage(
            planet=Planet.SUN,
            sign=ZodiacSign.GEMINI,  # Neutral
            house_number=house
        )
        # (10 + 0 + 0) × 3 × 1.0 = 30
        assert weightage == 30.0, f"Failed for house {house}"


def test_succedent_house_multiplier():
    """Succedent houses (2, 5, 8, 11) have multiplier of ×2."""
    for house in [2, 5, 8, 11]:
        weightage = calculate_weightage(
            planet=Planet.SUN,
            sign=ZodiacSign.GEMINI,  # Neutral
            house_number=house
        )
        # (10 + 0 + 0) × 2 × 1.0 = 20
        assert weightage == 20.0, f"Failed for house {house}"


def test_cadent_house_multiplier():
    """Cadent houses (3, 6, 9, 12) have multiplier of ×1."""
    for house in [3, 6, 9, 12]:
        weightage = calculate_weightage(
            planet=Planet.SUN,
            sign=ZodiacSign.GEMINI,  # Neutral
            house_number=house
        )
        # (10 + 0 + 0) × 1 × 1.0 = 10
        assert weightage == 10.0, f"Failed for house {house}"


# =============================================================================
# Dignity Impact Tests
# =============================================================================

def test_domicile_increases_weightage():
    """Planet in domicile (+5) should increase weightage."""
    # Sun in Leo (domicile), cadent house
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.LEO,
        house_number=3
    )
    # (10 + 5 + 0) × 1 × 1.0 = 15
    assert weightage == 15.0


def test_exaltation_increases_weightage():
    """Planet in exaltation (+4) should increase weightage."""
    # Sun in Aries (exaltation), cadent house
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.ARIES,
        degree_in_sign=19.0,  # Exact exaltation degree
        house_number=3
    )
    # (10 + 4 + 0) × 1 × 1.0 = 14
    assert weightage == 14.0


def test_detriment_decreases_weightage():
    """Planet in detriment (-5) should decrease weightage."""
    # Sun in Aquarius (detriment), cadent house
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.AQUARIUS,
        house_number=3
    )
    # (10 + (-5) + 0) × 1 × 1.0 = 5
    assert weightage == 5.0


def test_fall_decreases_weightage():
    """Planet in fall (-4) should decrease weightage."""
    # Sun in Libra (fall), cadent house
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.LIBRA,
        degree_in_sign=19.0,  # Exact fall degree
        house_number=3
    )
    # (10 + (-4) + 0) × 1 × 1.0 = 6
    assert weightage == 6.0


# =============================================================================
# Chart Ruler Tests
# =============================================================================

def test_chart_ruler_bonus_leo_rising():
    """Leo rising makes Sun the chart ruler (+5 bonus)."""
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.GEMINI,  # Neutral
        house_number=3,  # Cadent
        ascendant_sign=ZodiacSign.LEO
    )
    # (10 + 0 + 5) × 1 × 1.0 = 15
    assert weightage == 15.0


def test_chart_ruler_bonus_aries_rising():
    """Aries rising makes Mars the chart ruler."""
    weightage = calculate_weightage(
        planet=Planet.MARS,
        sign=ZodiacSign.GEMINI,  # Neutral
        house_number=3,  # Cadent
        ascendant_sign=ZodiacSign.ARIES
    )
    # (7 + 0 + 5) × 1 × 1.0 = 12
    assert weightage == 12.0


def test_not_chart_ruler():
    """Planet that is not chart ruler should get no bonus."""
    # Leo rising, but calculating Moon (not chart ruler)
    weightage = calculate_weightage(
        planet=Planet.MOON,
        sign=ZodiacSign.GEMINI,  # Neutral
        house_number=3,  # Cadent
        ascendant_sign=ZodiacSign.LEO  # Sun is chart ruler, not Moon
    )
    # (10 + 0 + 0) × 1 × 1.0 = 10
    assert weightage == 10.0


def test_chart_ruler_function():
    """Test chart ruler identification function (using modern rulerships)."""
    assert calculate_chart_ruler(ZodiacSign.ARIES) == Planet.MARS
    assert calculate_chart_ruler(ZodiacSign.TAURUS) == Planet.VENUS
    assert calculate_chart_ruler(ZodiacSign.GEMINI) == Planet.MERCURY
    assert calculate_chart_ruler(ZodiacSign.CANCER) == Planet.MOON
    assert calculate_chart_ruler(ZodiacSign.LEO) == Planet.SUN
    assert calculate_chart_ruler(ZodiacSign.VIRGO) == Planet.MERCURY
    assert calculate_chart_ruler(ZodiacSign.LIBRA) == Planet.VENUS
    assert calculate_chart_ruler(ZodiacSign.SCORPIO) == Planet.PLUTO  # Modern (traditional: Mars)
    assert calculate_chart_ruler(ZodiacSign.SAGITTARIUS) == Planet.JUPITER
    assert calculate_chart_ruler(ZodiacSign.CAPRICORN) == Planet.SATURN
    assert calculate_chart_ruler(ZodiacSign.AQUARIUS) == Planet.URANUS  # Modern (traditional: Saturn)
    assert calculate_chart_ruler(ZodiacSign.PISCES) == Planet.NEPTUNE  # Modern (traditional: Jupiter)


# =============================================================================
# Sensitivity Factor Tests
# =============================================================================

def test_default_sensitivity():
    """Default sensitivity should be 1.0."""
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.GEMINI,
        house_number=3
    )
    # (10 + 0 + 0) × 1 × 1.0 = 10
    assert weightage == 10.0


def test_high_sensitivity():
    """High sensitivity (2.0) should double weightage."""
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.GEMINI,
        house_number=3,
        sensitivity=2.0
    )
    # (10 + 0 + 0) × 1 × 2.0 = 20
    assert weightage == 20.0


def test_low_sensitivity():
    """Low sensitivity (0.5) should halve weightage."""
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.GEMINI,
        house_number=3,
        sensitivity=0.5
    )
    # (10 + 0 + 0) × 1 × 0.5 = 5
    assert weightage == 5.0


# =============================================================================
# Complex Scenario Tests
# =============================================================================

def test_complex_scenario_strong_planet():
    """
    Test a very strong planet:
    Mars in Aries (domicile) in 1st house (angular), chart ruler
    """
    weightage = calculate_weightage(
        planet=Planet.MARS,
        sign=ZodiacSign.ARIES,  # Domicile (+5)
        house_number=1,  # Angular (×3)
        ascendant_sign=ZodiacSign.ARIES  # Chart ruler (+5)
    )
    # (7 + 5 + 5) × 3 × 1.0 = 51
    assert weightage == 51.0


def test_complex_scenario_weak_planet():
    """
    Test a weak planet:
    Mars in Libra (detriment) in 12th house (cadent), not chart ruler
    """
    weightage = calculate_weightage(
        planet=Planet.MARS,
        sign=ZodiacSign.LIBRA,  # Detriment (-5)
        house_number=12,  # Cadent (×1)
        ascendant_sign=ZodiacSign.LEO  # Not chart ruler (Sun is)
    )
    # (7 + (-5) + 0) × 1 × 1.0 = 2
    assert weightage == 2.0


def test_complex_scenario_with_sensitivity():
    """
    Test complex scenario with high sensitivity:
    Venus in Pisces (exaltation) in 7th house (angular), high sensitivity
    """
    weightage = calculate_weightage(
        planet=Planet.VENUS,
        sign=ZodiacSign.PISCES,  # Exaltation (+4)
        degree_in_sign=27.0,
        house_number=7,  # Angular (×3)
        sensitivity=1.5
    )
    # (7 + 4 + 0) × 3 × 1.5 = 49.5
    assert weightage == 49.5


# =============================================================================
# Breakdown Function Tests
# =============================================================================

def test_weightage_breakdown():
    """Test that breakdown returns all components."""
    breakdown = get_weightage_breakdown(
        planet=Planet.SUN,
        sign=ZodiacSign.LEO,
        house_number=10,
        ascendant_sign=ZodiacSign.LEO
    )

    assert breakdown['weightage'] == 60.0
    assert breakdown['planet_base'] == 10.0
    assert breakdown['dignity_score'] == 5  # Domicile
    assert breakdown['ruler_bonus'] == 5.0
    assert breakdown['house_multiplier'] == 3.0
    assert breakdown['sensitivity_factor'] == 1.0
    assert breakdown['is_chart_ruler'] is True
    assert breakdown['house_type'] == "Angular"


def test_breakdown_house_types():
    """Test that breakdown correctly identifies house types."""
    angular = get_weightage_breakdown(
        planet=Planet.SUN,
        sign=ZodiacSign.GEMINI,
        house_number=1
    )
    assert angular['house_type'] == "Angular"

    succedent = get_weightage_breakdown(
        planet=Planet.SUN,
        sign=ZodiacSign.GEMINI,
        house_number=2
    )
    assert succedent['house_type'] == "Succedent"

    cadent = get_weightage_breakdown(
        planet=Planet.SUN,
        sign=ZodiacSign.GEMINI,
        house_number=3
    )
    assert cadent['house_type'] == "Cadent"


# =============================================================================
# Edge Cases
# =============================================================================

def test_negative_weightage_possible():
    """
    Test that weightage can be negative or very low in extreme cases.
    Outer planet in detriment in cadent house.
    """
    weightage = calculate_weightage(
        planet=Planet.SATURN,
        sign=ZodiacSign.CANCER,  # Detriment (-5)
        house_number=12  # Cadent (×1)
    )
    # (5 + (-5) + 0) × 1 × 1.0 = 0
    assert weightage == 0.0


def test_no_ascendant_provided():
    """When no ascendant is provided, no chart ruler bonus."""
    weightage = calculate_weightage(
        planet=Planet.SUN,
        sign=ZodiacSign.LEO,
        house_number=1
        # No ascendant_sign provided
    )
    # (10 + 5 + 0) × 3 × 1.0 = 45 (no chart ruler bonus)
    assert weightage == 45.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for essential dignity calculations.

Tests all 7 traditional planets (Sun through Saturn) in various signs
to ensure correct dignity scoring.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from astro import Planet, ZodiacSign
from astrometers.dignity import (
    calculate_dignity_score,
    get_dignity_label,
    is_in_dignity,
    is_in_debility,
)
from astrometers.constants import (
    DIGNITY_DOMICILE,
    DIGNITY_EXALTATION,
    DIGNITY_DETRIMENT,
    DIGNITY_FALL,
    DIGNITY_NEUTRAL,
)


# =============================================================================
# Sun Dignity Tests
# =============================================================================

def test_sun_in_domicile():
    """Sun in Leo should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.LEO) == DIGNITY_DOMICILE
    assert get_dignity_label(DIGNITY_DOMICILE) == "Domicile"


def test_sun_in_exaltation():
    """Sun at 19° Aries should return +4 (exaltation)."""
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.ARIES, degree=19) == DIGNITY_EXALTATION


def test_sun_in_exaltation_within_orb():
    """Sun at 17° Aries (within 5° orb) should return +4 (exaltation)."""
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.ARIES, degree=17) == DIGNITY_EXALTATION


def test_sun_in_aries_outside_exaltation_orb():
    """Sun at 5° Aries (outside exaltation orb) should return 0 (neutral)."""
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.ARIES, degree=5) == DIGNITY_NEUTRAL


def test_sun_in_detriment():
    """Sun in Aquarius should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.AQUARIUS) == DIGNITY_DETRIMENT


def test_sun_in_fall():
    """Sun at 19° Libra should return -4 (fall)."""
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.LIBRA, degree=19) == DIGNITY_FALL


def test_sun_neutral():
    """Sun in Gemini should return 0 (peregrine/neutral)."""
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.GEMINI) == DIGNITY_NEUTRAL


# =============================================================================
# Moon Dignity Tests
# =============================================================================

def test_moon_in_domicile():
    """Moon in Cancer should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.MOON, ZodiacSign.CANCER) == DIGNITY_DOMICILE


def test_moon_in_exaltation():
    """Moon at 3° Taurus should return +4 (exaltation)."""
    assert calculate_dignity_score(Planet.MOON, ZodiacSign.TAURUS, degree=3) == DIGNITY_EXALTATION


def test_moon_in_detriment():
    """Moon in Capricorn should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.MOON, ZodiacSign.CAPRICORN) == DIGNITY_DETRIMENT


def test_moon_in_fall():
    """Moon at 3° Scorpio should return -4 (fall)."""
    assert calculate_dignity_score(Planet.MOON, ZodiacSign.SCORPIO, degree=3) == DIGNITY_FALL


def test_moon_neutral():
    """Moon in Aries should return 0 (neutral)."""
    assert calculate_dignity_score(Planet.MOON, ZodiacSign.ARIES) == DIGNITY_NEUTRAL


# =============================================================================
# Mercury Dignity Tests
# =============================================================================

def test_mercury_in_domicile_gemini():
    """Mercury in Gemini should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.MERCURY, ZodiacSign.GEMINI) == DIGNITY_DOMICILE


def test_mercury_in_domicile_virgo():
    """Mercury in Virgo should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.MERCURY, ZodiacSign.VIRGO) == DIGNITY_DOMICILE


def test_mercury_in_exaltation():
    """Mercury at 15° Virgo returns +5 (domicile takes precedence over exaltation)."""
    # Note: Mercury is both domiciled AND exalted in Virgo
    # Domicile (+5) takes precedence over exaltation (+4)
    assert calculate_dignity_score(Planet.MERCURY, ZodiacSign.VIRGO, degree=15) == DIGNITY_DOMICILE


def test_mercury_in_detriment_sagittarius():
    """Mercury in Sagittarius should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.MERCURY, ZodiacSign.SAGITTARIUS) == DIGNITY_DETRIMENT


def test_mercury_in_detriment_pisces():
    """Mercury in Pisces should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.MERCURY, ZodiacSign.PISCES) == DIGNITY_DETRIMENT


def test_mercury_in_fall():
    """Mercury at 15° Pisces returns -5 (detriment takes precedence over fall)."""
    # Note: Mercury is both in detriment AND fall in Pisces
    # Detriment (-5) takes precedence over fall (-4)
    assert calculate_dignity_score(Planet.MERCURY, ZodiacSign.PISCES, degree=15) == DIGNITY_DETRIMENT


def test_mercury_neutral():
    """Mercury in Leo should return 0 (neutral)."""
    assert calculate_dignity_score(Planet.MERCURY, ZodiacSign.LEO) == DIGNITY_NEUTRAL


# =============================================================================
# Venus Dignity Tests
# =============================================================================

def test_venus_in_domicile_taurus():
    """Venus in Taurus should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.VENUS, ZodiacSign.TAURUS) == DIGNITY_DOMICILE


def test_venus_in_domicile_libra():
    """Venus in Libra should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.VENUS, ZodiacSign.LIBRA) == DIGNITY_DOMICILE


def test_venus_in_exaltation():
    """Venus at 27° Pisces should return +4 (exaltation)."""
    assert calculate_dignity_score(Planet.VENUS, ZodiacSign.PISCES, degree=27) == DIGNITY_EXALTATION


def test_venus_in_detriment_scorpio():
    """Venus in Scorpio should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.VENUS, ZodiacSign.SCORPIO) == DIGNITY_DETRIMENT


def test_venus_in_detriment_aries():
    """Venus in Aries should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.VENUS, ZodiacSign.ARIES) == DIGNITY_DETRIMENT


def test_venus_in_fall():
    """Venus at 27° Virgo should return -4 (fall)."""
    assert calculate_dignity_score(Planet.VENUS, ZodiacSign.VIRGO, degree=27) == DIGNITY_FALL


def test_venus_neutral():
    """Venus in Gemini should return 0 (neutral)."""
    assert calculate_dignity_score(Planet.VENUS, ZodiacSign.GEMINI) == DIGNITY_NEUTRAL


# =============================================================================
# Mars Dignity Tests
# =============================================================================

def test_mars_in_domicile_aries():
    """Mars in Aries should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.MARS, ZodiacSign.ARIES) == DIGNITY_DOMICILE


def test_mars_in_domicile_scorpio():
    """Mars in Scorpio should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.MARS, ZodiacSign.SCORPIO) == DIGNITY_DOMICILE


def test_mars_in_exaltation():
    """Mars at 28° Capricorn should return +4 (exaltation)."""
    assert calculate_dignity_score(Planet.MARS, ZodiacSign.CAPRICORN, degree=28) == DIGNITY_EXALTATION


def test_mars_in_detriment_libra():
    """Mars in Libra should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.MARS, ZodiacSign.LIBRA) == DIGNITY_DETRIMENT


def test_mars_in_detriment_taurus():
    """Mars in Taurus should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.MARS, ZodiacSign.TAURUS) == DIGNITY_DETRIMENT


def test_mars_in_fall():
    """Mars at 28° Cancer should return -4 (fall)."""
    assert calculate_dignity_score(Planet.MARS, ZodiacSign.CANCER, degree=28) == DIGNITY_FALL


def test_mars_neutral():
    """Mars in Sagittarius should return 0 (neutral)."""
    assert calculate_dignity_score(Planet.MARS, ZodiacSign.SAGITTARIUS) == DIGNITY_NEUTRAL


# =============================================================================
# Jupiter Dignity Tests
# =============================================================================

def test_jupiter_in_domicile_sagittarius():
    """Jupiter in Sagittarius should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.JUPITER, ZodiacSign.SAGITTARIUS) == DIGNITY_DOMICILE


def test_jupiter_in_domicile_pisces():
    """Jupiter in Pisces should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.JUPITER, ZodiacSign.PISCES) == DIGNITY_DOMICILE


def test_jupiter_in_exaltation():
    """Jupiter at 15° Cancer should return +4 (exaltation)."""
    assert calculate_dignity_score(Planet.JUPITER, ZodiacSign.CANCER, degree=15) == DIGNITY_EXALTATION


def test_jupiter_in_detriment_gemini():
    """Jupiter in Gemini should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.JUPITER, ZodiacSign.GEMINI) == DIGNITY_DETRIMENT


def test_jupiter_in_detriment_virgo():
    """Jupiter in Virgo should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.JUPITER, ZodiacSign.VIRGO) == DIGNITY_DETRIMENT


def test_jupiter_in_fall():
    """Jupiter at 15° Capricorn should return -4 (fall)."""
    assert calculate_dignity_score(Planet.JUPITER, ZodiacSign.CAPRICORN, degree=15) == DIGNITY_FALL


def test_jupiter_neutral():
    """Jupiter in Leo should return 0 (neutral)."""
    assert calculate_dignity_score(Planet.JUPITER, ZodiacSign.LEO) == DIGNITY_NEUTRAL


# =============================================================================
# Saturn Dignity Tests
# =============================================================================

def test_saturn_in_domicile_capricorn():
    """Saturn in Capricorn should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.SATURN, ZodiacSign.CAPRICORN) == DIGNITY_DOMICILE


def test_saturn_in_domicile_aquarius():
    """Saturn in Aquarius should return +5 (domicile)."""
    assert calculate_dignity_score(Planet.SATURN, ZodiacSign.AQUARIUS) == DIGNITY_DOMICILE


def test_saturn_in_exaltation():
    """Saturn at 21° Libra should return +4 (exaltation)."""
    assert calculate_dignity_score(Planet.SATURN, ZodiacSign.LIBRA, degree=21) == DIGNITY_EXALTATION


def test_saturn_in_detriment_cancer():
    """Saturn in Cancer should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.SATURN, ZodiacSign.CANCER) == DIGNITY_DETRIMENT


def test_saturn_in_detriment_leo():
    """Saturn in Leo should return -5 (detriment)."""
    assert calculate_dignity_score(Planet.SATURN, ZodiacSign.LEO) == DIGNITY_DETRIMENT


def test_saturn_in_fall():
    """Saturn at 21° Aries should return -4 (fall)."""
    assert calculate_dignity_score(Planet.SATURN, ZodiacSign.ARIES, degree=21) == DIGNITY_FALL


def test_saturn_neutral():
    """Saturn in Taurus should return 0 (neutral)."""
    assert calculate_dignity_score(Planet.SATURN, ZodiacSign.TAURUS) == DIGNITY_NEUTRAL


# =============================================================================
# Outer Planets (No Traditional Dignities)
# =============================================================================

def test_uranus_always_neutral():
    """Uranus has no traditional dignities, always neutral."""
    assert calculate_dignity_score(Planet.URANUS, ZodiacSign.ARIES) == DIGNITY_NEUTRAL
    assert calculate_dignity_score(Planet.URANUS, ZodiacSign.LEO) == DIGNITY_NEUTRAL
    assert calculate_dignity_score(Planet.URANUS, ZodiacSign.AQUARIUS) == DIGNITY_NEUTRAL


def test_neptune_always_neutral():
    """Neptune has no traditional dignities, always neutral."""
    assert calculate_dignity_score(Planet.NEPTUNE, ZodiacSign.PISCES) == DIGNITY_NEUTRAL
    assert calculate_dignity_score(Planet.NEPTUNE, ZodiacSign.CANCER) == DIGNITY_NEUTRAL


def test_pluto_always_neutral():
    """Pluto has no traditional dignities, always neutral."""
    assert calculate_dignity_score(Planet.PLUTO, ZodiacSign.SCORPIO) == DIGNITY_NEUTRAL
    assert calculate_dignity_score(Planet.PLUTO, ZodiacSign.CAPRICORN) == DIGNITY_NEUTRAL


# =============================================================================
# Helper Function Tests
# =============================================================================

def test_is_in_dignity():
    """Test is_in_dignity helper function."""
    assert is_in_dignity(Planet.SUN, ZodiacSign.LEO) is True  # Domicile
    assert is_in_dignity(Planet.MOON, ZodiacSign.TAURUS) is True  # Exaltation (no degree)
    assert is_in_dignity(Planet.VENUS, ZodiacSign.GEMINI) is False  # Neutral


def test_is_in_debility():
    """Test is_in_debility helper function."""
    assert is_in_debility(Planet.MARS, ZodiacSign.LIBRA) is True  # Detriment
    assert is_in_debility(Planet.JUPITER, ZodiacSign.CAPRICORN) is True  # Fall (no degree)
    assert is_in_debility(Planet.MERCURY, ZodiacSign.GEMINI) is False  # Domicile


def test_dignity_labels():
    """Test dignity label helper function."""
    assert get_dignity_label(5) == "Domicile"
    assert get_dignity_label(4) == "Exaltation"
    assert get_dignity_label(0) == "Neutral (Peregrine)"
    assert get_dignity_label(-4) == "Fall"
    assert get_dignity_label(-5) == "Detriment"


# =============================================================================
# Edge Cases
# =============================================================================

def test_exaltation_without_degree_assumes_exalted():
    """When no degree provided for exaltation sign, give benefit of doubt."""
    # Sun in Aries without degree should be considered exalted
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.ARIES) == DIGNITY_EXALTATION


def test_fall_without_degree_assumes_fallen():
    """When no degree provided for fall sign, give 'benefit of doubt' as fall."""
    # Sun in Libra without degree should be considered fallen
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.LIBRA) == DIGNITY_FALL


def test_exaltation_degree_boundary():
    """Test exaltation at exact orb boundary (5 degrees)."""
    # Sun exalted at 19° Aries, test at 24° (exactly 5° away)
    assert calculate_dignity_score(Planet.SUN, ZodiacSign.ARIES, degree=24) == DIGNITY_EXALTATION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

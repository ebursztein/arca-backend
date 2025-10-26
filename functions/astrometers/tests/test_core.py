"""
Tests for core DTI and HQS calculations.

Tests the main astrometer formulas:
- DTI = Σ(W_i × P_i)
- HQS = Σ(W_i × P_i × Q_i)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from astro import Planet, AspectType, ZodiacSign
from astrometers.core import (
    TransitAspect,
    AspectContribution,
    AstrometerScore,
    calculate_aspect_contribution,
    calculate_astrometers,
    get_score_breakdown_text,
)


# =============================================================================
# Single Aspect Contribution Tests
# =============================================================================

def test_aspect_contribution_spec_example():
    """
    Test spec example: Transit Saturn square Natal Sun (Section 6.2).

    W_i = (10 + 5) × 3 × 1.0 = 45
    P_i = 8 × 0.75 × 1.3 × 1.0 × 1.2 = 9.36
    Q_i = -1.0
    DTI = 45 × 9.36 = 421.2
    HQS = 421.2 × (-1.0) = -421.2
    """
    aspect = TransitAspect(
        natal_planet=Planet.SUN,
        natal_sign=ZodiacSign.LEO,  # Domicile (+5)
        natal_house=10,  # Angular (×3)
        transit_planet=Planet.SATURN,
        aspect_type=AspectType.SQUARE,
        orb_deviation=2.0,  # Orb factor = 1 - (2/8) = 0.75
        max_orb=8.0,
        today_deviation=2.0,
        tomorrow_deviation=1.5,  # Applying (×1.3)
        label="Transit Saturn square Natal Sun"
    )

    contrib = calculate_aspect_contribution(aspect)

    # Verify components
    assert contrib.weightage == 45.0  # (10 + 5) × 3
    assert abs(contrib.transit_power - 9.36) < 0.01  # 8 × 0.75 × 1.3 × 1.0 × 1.2
    assert contrib.quality_factor == -1.0  # Square

    # Verify contributions
    assert abs(contrib.dti_contribution - 421.2) < 0.5  # 45 × 9.36
    assert abs(contrib.hqs_contribution - (-421.2)) < 0.5  # 421.2 × (-1.0)


def test_aspect_contribution_harmonious():
    """Test harmonious aspect (Jupiter trine Venus from spec)."""
    aspect = TransitAspect(
        natal_planet=Planet.VENUS,
        natal_sign=ZodiacSign.TAURUS,  # Domicile (+5)
        natal_house=5,  # Succedent (×2)
        transit_planet=Planet.JUPITER,
        aspect_type=AspectType.TRINE,
        orb_deviation=1.0,  # Orb factor ≈ 0.86 (assuming max 7°)
        max_orb=7.0,
        today_deviation=1.0,
        tomorrow_deviation=0.8,  # Applying (×1.3)
    )

    contrib = calculate_aspect_contribution(aspect)

    # W_i = (7 + 5) × 2 = 24
    assert contrib.weightage == 24.0

    # P_i = 6 × 0.857 × 1.3 × 1.0 × 1.2 ≈ 8.03
    assert contrib.transit_power > 7.5
    assert contrib.transit_power < 8.5

    # Q_i = +1.0 (Trine)
    assert contrib.quality_factor == 1.0

    # DTI and HQS should both be positive
    assert contrib.dti_contribution > 0
    assert contrib.hqs_contribution > 0
    assert contrib.hqs_contribution == pytest.approx(contrib.dti_contribution)  # Q_i = +1.0


def test_aspect_contribution_conjunction_benefic():
    """Test benefic conjunction (Venus conjunct Jupiter)."""
    aspect = TransitAspect(
        natal_planet=Planet.JUPITER,
        natal_sign=ZodiacSign.SAGITTARIUS,  # Domicile
        natal_house=9,  # Cadent
        transit_planet=Planet.VENUS,
        aspect_type=AspectType.CONJUNCTION,
        orb_deviation=0.5,  # Very tight
        max_orb=8.0,
    )

    contrib = calculate_aspect_contribution(aspect)

    # Q_i should be +0.8 (double benefic)
    assert contrib.quality_factor == 0.8

    # HQS should be 80% of DTI (positive)
    assert contrib.hqs_contribution > 0
    assert contrib.hqs_contribution == pytest.approx(contrib.dti_contribution * 0.8)


def test_aspect_contribution_conjunction_malefic():
    """Test malefic conjunction (Mars conjunct Saturn)."""
    aspect = TransitAspect(
        natal_planet=Planet.SATURN,
        natal_sign=ZodiacSign.CAPRICORN,  # Domicile
        natal_house=10,  # Angular
        transit_planet=Planet.MARS,
        aspect_type=AspectType.CONJUNCTION,
        orb_deviation=1.0,
        max_orb=8.0,
    )

    contrib = calculate_aspect_contribution(aspect)

    # Q_i should be -0.8 (double malefic)
    assert contrib.quality_factor == -0.8

    # HQS should be -80% of DTI (negative)
    assert contrib.hqs_contribution < 0
    assert contrib.hqs_contribution == pytest.approx(contrib.dti_contribution * -0.8)


# =============================================================================
# Multi-Aspect DTI/HQS Calculation Tests
# =============================================================================

def test_calculate_astrometers_single_aspect():
    """Test with a single aspect."""
    aspects = [
        TransitAspect(
            natal_planet=Planet.MOON,
            natal_sign=ZodiacSign.CANCER,  # Domicile
            natal_house=4,  # Angular
            transit_planet=Planet.JUPITER,
            aspect_type=AspectType.TRINE,
            orb_deviation=0.0,  # Exact
            max_orb=7.0,
        )
    ]

    score = calculate_astrometers(aspects)

    assert score.aspect_count == 1
    assert len(score.contributions) == 1
    assert score.dti > 0
    assert score.hqs > 0  # Harmonious aspect
    assert score.hqs == pytest.approx(score.dti)  # Q_i = +1.0 for trine


def test_calculate_astrometers_multiple_aspects():
    """Test with multiple aspects (harmonious and challenging)."""
    aspects = [
        # Challenging: Saturn square Sun
        TransitAspect(
            natal_planet=Planet.SUN,
            natal_sign=ZodiacSign.LEO,
            natal_house=10,
            transit_planet=Planet.SATURN,
            aspect_type=AspectType.SQUARE,
            orb_deviation=2.0,
            max_orb=8.0,
            today_deviation=2.0,
            tomorrow_deviation=1.5,
        ),
        # Harmonious: Jupiter trine Venus
        TransitAspect(
            natal_planet=Planet.VENUS,
            natal_sign=ZodiacSign.TAURUS,
            natal_house=5,
            transit_planet=Planet.JUPITER,
            aspect_type=AspectType.TRINE,
            orb_deviation=1.0,
            max_orb=7.0,
            today_deviation=1.0,
            tomorrow_deviation=0.8,
        )
    ]

    score = calculate_astrometers(aspects)

    assert score.aspect_count == 2
    assert len(score.contributions) == 2

    # DTI should be sum of both (always positive)
    assert score.dti > 0

    # HQS should be mixed (one negative, one positive)
    # Saturn square contribution is negative and larger
    assert score.hqs < 0  # Net challenging

    # Verify sum
    expected_dti = sum(c.dti_contribution for c in score.contributions)
    expected_hqs = sum(c.hqs_contribution for c in score.contributions)
    assert score.dti == pytest.approx(expected_dti)
    assert score.hqs == pytest.approx(expected_hqs)


def test_calculate_astrometers_all_harmonious():
    """Test with all harmonious aspects."""
    aspects = [
        TransitAspect(
            natal_planet=Planet.SUN,
            natal_sign=ZodiacSign.LEO,
            natal_house=10,
            transit_planet=Planet.JUPITER,
            aspect_type=AspectType.TRINE,
            orb_deviation=0.0,
            max_orb=7.0,
        ),
        TransitAspect(
            natal_planet=Planet.MOON,
            natal_sign=ZodiacSign.CANCER,
            natal_house=4,
            transit_planet=Planet.VENUS,
            aspect_type=AspectType.SEXTILE,
            orb_deviation=0.5,
            max_orb=6.0,
        )
    ]

    score = calculate_astrometers(aspects)

    # Both DTI and HQS should be positive
    assert score.dti > 0
    assert score.hqs > 0

    # HQS should approximately equal DTI (all Q_i = +1.0)
    assert score.hqs == pytest.approx(score.dti, rel=0.01)


def test_calculate_astrometers_all_challenging():
    """Test with all challenging aspects."""
    aspects = [
        TransitAspect(
            natal_planet=Planet.SUN,
            natal_sign=ZodiacSign.LEO,
            natal_house=10,
            transit_planet=Planet.SATURN,
            aspect_type=AspectType.SQUARE,
            orb_deviation=1.0,
            max_orb=8.0,
        ),
        TransitAspect(
            natal_planet=Planet.MOON,
            natal_sign=ZodiacSign.CANCER,
            natal_house=4,
            transit_planet=Planet.MARS,
            aspect_type=AspectType.OPPOSITION,
            orb_deviation=2.0,
            max_orb=9.0,
        )
    ]

    score = calculate_astrometers(aspects)

    # DTI should be positive
    assert score.dti > 0

    # HQS should be negative (all Q_i = -1.0)
    assert score.hqs < 0

    # HQS should approximately equal -DTI (all Q_i = -1.0)
    assert score.hqs == pytest.approx(-score.dti, rel=0.01)


def test_calculate_astrometers_empty_list():
    """Test with no aspects."""
    score = calculate_astrometers([])

    assert score.dti == 0.0
    assert score.hqs == 0.0
    assert score.aspect_count == 0
    assert len(score.contributions) == 0


# =============================================================================
# Sensitivity and Chart Ruler Tests
# =============================================================================

def test_aspect_contribution_with_sensitivity():
    """Test that sensitivity factor affects both DTI and HQS."""
    aspect_normal = TransitAspect(
        natal_planet=Planet.MERCURY,
        natal_sign=ZodiacSign.GEMINI,
        natal_house=3,
        transit_planet=Planet.URANUS,
        aspect_type=AspectType.TRINE,
        orb_deviation=1.0,
        max_orb=6.0,
        sensitivity=1.0
    )

    aspect_high_sensitivity = TransitAspect(
        natal_planet=Planet.MERCURY,
        natal_sign=ZodiacSign.GEMINI,
        natal_house=3,
        transit_planet=Planet.URANUS,
        aspect_type=AspectType.TRINE,
        orb_deviation=1.0,
        max_orb=6.0,
        sensitivity=2.0
    )

    contrib_normal = calculate_aspect_contribution(aspect_normal)
    contrib_high = calculate_aspect_contribution(aspect_high_sensitivity)

    # High sensitivity should double weightage
    assert contrib_high.weightage == pytest.approx(contrib_normal.weightage * 2.0)

    # DTI and HQS should also double
    assert contrib_high.dti_contribution == pytest.approx(contrib_normal.dti_contribution * 2.0)
    assert contrib_high.hqs_contribution == pytest.approx(contrib_normal.hqs_contribution * 2.0)


def test_aspect_contribution_chart_ruler():
    """Test that chart ruler bonus increases weightage."""
    aspect_no_ruler = TransitAspect(
        natal_planet=Planet.MERCURY,
        natal_sign=ZodiacSign.VIRGO,  # Domicile
        natal_house=1,  # Angular
        transit_planet=Planet.JUPITER,
        aspect_type=AspectType.TRINE,
        orb_deviation=0.5,
        max_orb=7.0,
        ascendant_sign=ZodiacSign.LEO  # Sun is chart ruler, not Mercury
    )

    aspect_with_ruler = TransitAspect(
        natal_planet=Planet.MERCURY,
        natal_sign=ZodiacSign.VIRGO,  # Domicile
        natal_house=1,  # Angular
        transit_planet=Planet.JUPITER,
        aspect_type=AspectType.TRINE,
        orb_deviation=0.5,
        max_orb=7.0,
        ascendant_sign=ZodiacSign.VIRGO  # Mercury is chart ruler
    )

    contrib_no_ruler = calculate_aspect_contribution(aspect_no_ruler)
    contrib_with_ruler = calculate_aspect_contribution(aspect_with_ruler)

    # Chart ruler bonus adds 5 points before multipliers
    # W_i (no ruler) = (7 + 5 + 0) × 3 = 36
    # W_i (ruler) = (7 + 5 + 5) × 3 = 51
    assert contrib_no_ruler.weightage == 36.0
    assert contrib_with_ruler.weightage == 51.0

    # DTI and HQS should be proportionally higher
    ratio = contrib_with_ruler.weightage / contrib_no_ruler.weightage
    assert contrib_with_ruler.dti_contribution == pytest.approx(contrib_no_ruler.dti_contribution * ratio)


# =============================================================================
# Breakdown Text Tests
# =============================================================================

def test_score_breakdown_text():
    """Test that breakdown text is generated correctly."""
    aspects = [
        TransitAspect(
            natal_planet=Planet.SUN,
            natal_sign=ZodiacSign.LEO,
            natal_house=10,
            transit_planet=Planet.SATURN,
            aspect_type=AspectType.SQUARE,
            orb_deviation=2.0,
            max_orb=8.0,
            label="Transit Saturn square Natal Sun"
        )
    ]

    score = calculate_astrometers(aspects)
    text = get_score_breakdown_text(score)

    # Verify key information is present
    assert "Total DTI:" in text
    assert "Total HQS:" in text
    assert "Active Aspects: 1" in text
    assert "Transit Saturn square Natal Sun" in text
    assert "W_i" in text
    assert "P_i" in text
    assert "Q_i" in text


def test_score_breakdown_text_multiple_aspects():
    """Test breakdown text with multiple aspects."""
    aspects = [
        TransitAspect(
            natal_planet=Planet.SUN,
            natal_sign=ZodiacSign.LEO,
            natal_house=10,
            transit_planet=Planet.SATURN,
            aspect_type=AspectType.SQUARE,
            orb_deviation=2.0,
            max_orb=8.0,
        ),
        TransitAspect(
            natal_planet=Planet.VENUS,
            natal_sign=ZodiacSign.TAURUS,
            natal_house=5,
            transit_planet=Planet.JUPITER,
            aspect_type=AspectType.TRINE,
            orb_deviation=1.0,
            max_orb=7.0,
        )
    ]

    score = calculate_astrometers(aspects)
    text = get_score_breakdown_text(score)

    assert "Active Aspects: 2" in text
    assert "1." in text
    assert "2." in text


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================

def test_aspect_contribution_exact_aspect():
    """Test exact aspect (0° orb)."""
    aspect = TransitAspect(
        natal_planet=Planet.MARS,
        natal_sign=ZodiacSign.ARIES,
        natal_house=1,
        transit_planet=Planet.URANUS,
        aspect_type=AspectType.CONJUNCTION,
        orb_deviation=0.0,  # Exact
        max_orb=8.0,
        today_deviation=0.3,  # Within exact threshold
        tomorrow_deviation=0.5,
    )

    contrib = calculate_aspect_contribution(aspect)

    # Exact aspect should have maximum orb factor (1.0)
    # and direction modifier should be "exact" (1.5)
    assert contrib.transit_power > 15  # Base 10 × 1.0 × 1.5 × 1.0 × 1.5 (transformational)


def test_aspect_contribution_with_station():
    """Test aspect with retrograde station."""
    aspect = TransitAspect(
        natal_planet=Planet.SUN,
        natal_sign=ZodiacSign.LEO,
        natal_house=10,
        transit_planet=Planet.SATURN,
        aspect_type=AspectType.SQUARE,
        orb_deviation=1.0,
        max_orb=8.0,
        days_from_station=0,  # Exact station (×1.8)
    )

    contrib = calculate_aspect_contribution(aspect)

    # Station modifier should significantly boost transit power
    assert contrib.transit_power > 10  # Should be amplified


def test_calculate_astrometers_complex_scenario():
    """Test complex scenario with varied aspects."""
    aspects = [
        # Strong challenging aspect
        TransitAspect(
            natal_planet=Planet.SUN,
            natal_sign=ZodiacSign.LEO,
            natal_house=10,
            transit_planet=Planet.PLUTO,
            aspect_type=AspectType.SQUARE,
            orb_deviation=0.5,
            max_orb=7.0,
            today_deviation=0.5,
            tomorrow_deviation=0.3,
        ),
        # Moderate harmonious aspect
        TransitAspect(
            natal_planet=Planet.VENUS,
            natal_sign=ZodiacSign.LIBRA,
            natal_house=7,
            transit_planet=Planet.JUPITER,
            aspect_type=AspectType.TRINE,
            orb_deviation=3.0,
            max_orb=7.0,
        ),
        # Weak neutral conjunction
        TransitAspect(
            natal_planet=Planet.MERCURY,
            natal_sign=ZodiacSign.SAGITTARIUS,
            natal_house=12,
            transit_planet=Planet.SUN,
            aspect_type=AspectType.CONJUNCTION,
            orb_deviation=5.0,
            max_orb=8.0,
        )
    ]

    score = calculate_astrometers(aspects)

    assert score.aspect_count == 3
    assert score.dti > 0  # Always positive
    # HQS depends on relative strengths


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

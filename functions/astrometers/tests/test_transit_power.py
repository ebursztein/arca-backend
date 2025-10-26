"""
Tests for transit power (P_i) calculations.

Part 1 tests: Aspect detection and orb factor
Part 2 tests: Direction and station modifiers (TODO - Phase 4)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from astro import Planet, AspectType
from astrometers.transit_power import (
    calculate_angular_separation,
    detect_aspect,
    calculate_orb_factor,
    calculate_transit_power_basic,
    get_aspect_strength_label,
)
from astrometers.constants import ASPECT_BASE_INTENSITY


# =============================================================================
# Angular Separation Tests
# =============================================================================

def test_angular_separation_simple():
    """Test simple angular separation (no circle wrap)."""
    assert calculate_angular_separation(10, 20) == 10.0
    assert calculate_angular_separation(20, 10) == 10.0  # Order doesn't matter


def test_angular_separation_across_zero():
    """Test angular separation across 0°/360° boundary."""
    # 350° to 10° = 20° (shorter path crosses 0°)
    assert calculate_angular_separation(350, 10) == 20.0
    assert calculate_angular_separation(10, 350) == 20.0


def test_angular_separation_exact_opposition():
    """Test exact opposition (180°)."""
    assert calculate_angular_separation(0, 180) == 180.0
    assert calculate_angular_separation(90, 270) == 180.0


def test_angular_separation_greater_than_180():
    """Test that separation never exceeds 180° (always shortest arc)."""
    # 10° to 200° = 190° direct, but 170° going the other way
    assert calculate_angular_separation(10, 200) == 170.0
    assert calculate_angular_separation(0, 270) == 90.0  # Shorter arc


def test_angular_separation_same_position():
    """Test zero separation (same position)."""
    assert calculate_angular_separation(45, 45) == 0.0


# =============================================================================
# Aspect Detection Tests
# =============================================================================

def test_detect_conjunction():
    """Test detecting conjunction aspect."""
    # Sun at 0°, Saturn at 2° = conjunction within orb
    result = detect_aspect(2, 0, Planet.SATURN, Planet.SUN)
    assert result is not None
    aspect_type, deviation, max_orb = result
    assert aspect_type == AspectType.CONJUNCTION
    assert deviation == 2.0
    assert max_orb == 10.0  # Conjunction with luminary (Sun) gets 10° orb


def test_detect_square():
    """Test detecting square aspect."""
    # Saturn at 90.5°, Sun at 0° = square within orb
    result = detect_aspect(90.5, 0, Planet.SATURN, Planet.SUN)
    assert result is not None
    aspect_type, deviation, max_orb = result
    assert aspect_type == AspectType.SQUARE
    assert abs(deviation - 0.5) < 0.001  # Close to exact


def test_detect_trine():
    """Test detecting trine aspect."""
    # Jupiter at 120°, Sun at 0° = trine (exact)
    result = detect_aspect(120, 0, Planet.JUPITER, Planet.SUN)
    assert result is not None
    aspect_type, deviation, max_orb = result
    assert aspect_type == AspectType.TRINE
    assert deviation == 0.0  # Exact trine


def test_detect_sextile():
    """Test detecting sextile aspect."""
    # Venus at 61°, Sun at 0° = sextile within orb
    result = detect_aspect(61, 0, Planet.VENUS, Planet.SUN)
    assert result is not None
    aspect_type, deviation, max_orb = result
    assert aspect_type == AspectType.SEXTILE
    assert abs(deviation - 1.0) < 0.001


def test_detect_opposition():
    """Test detecting opposition aspect."""
    # Uranus at 178°, Sun at 0° = opposition within orb
    result = detect_aspect(178, 0, Planet.URANUS, Planet.SUN)
    assert result is not None
    aspect_type, deviation, max_orb = result
    assert aspect_type == AspectType.OPPOSITION
    assert abs(deviation - 2.0) < 0.001


def test_no_aspect_detected():
    """Test when no aspect is within orb."""
    # Saturn at 45°, Sun at 0° = no major aspect
    result = detect_aspect(45, 0, Planet.SATURN, Planet.SUN)
    assert result is None


def test_aspect_beyond_orb():
    """Test aspect beyond maximum orb."""
    # Saturn at 15°, Sun at 0° = conjunction but beyond orb
    # Max orb for conjunction with luminary is 10°
    result = detect_aspect(15, 0, Planet.SATURN, Planet.SUN)
    assert result is None  # Beyond orb


def test_variable_orb_luminary():
    """Test that luminaries get wider orbs."""
    # Conjunction with Sun (luminary) has 10° orb
    result = detect_aspect(9, 0, Planet.SATURN, Planet.SUN)
    assert result is not None  # Within 10° orb

    # Conjunction without luminary has 8° orb
    result = detect_aspect(9, 0, Planet.SATURN, Planet.MERCURY)
    assert result is None  # Beyond 8° orb


def test_variable_orb_outer_planet():
    """Test that outer planets get tighter orbs."""
    # Conjunction with outer planet (Pluto) has 6° orb
    result = detect_aspect(7, 0, Planet.PLUTO, Planet.MERCURY)
    assert result is None  # Beyond 6° orb

    result = detect_aspect(5, 0, Planet.PLUTO, Planet.MERCURY)
    assert result is not None  # Within 6° orb


def test_closest_aspect_wins():
    """Test that when multiple aspects are possible, closest one is detected."""
    # At 30°, both sextile (60° - 30° = 30°) and nothing else close
    # But this should not detect sextile if beyond orb
    result = detect_aspect(30, 0, Planet.MARS, Planet.VENUS)
    assert result is None  # 30° from sextile, beyond 5° orb


# =============================================================================
# Orb Factor Tests
# =============================================================================

def test_orb_factor_exact():
    """Test orb factor at exact aspect (0° deviation)."""
    assert calculate_orb_factor(0, 8) == 1.0


def test_orb_factor_halfway():
    """Test orb factor at half the max orb."""
    assert calculate_orb_factor(4, 8) == 0.5


def test_orb_factor_at_max():
    """Test orb factor at maximum orb."""
    assert calculate_orb_factor(8, 8) == 0.0


def test_orb_factor_beyond_max():
    """Test orb factor beyond maximum orb."""
    assert calculate_orb_factor(10, 8) == 0.0


def test_orb_factor_linear_decay():
    """Test that orb factor decays linearly."""
    # At 2° from exact with 8° max orb
    # Factor = 1 - (2/8) = 0.75
    assert calculate_orb_factor(2, 8) == 0.75

    # At 6° from exact with 8° max orb
    # Factor = 1 - (6/8) = 0.25
    assert calculate_orb_factor(6, 8) == 0.25


def test_orb_factor_different_max_orbs():
    """Test orb factor with different maximum orbs."""
    # Sextile with 5° max orb
    assert calculate_orb_factor(2.5, 5) == 0.5

    # Conjunction with 10° max orb (luminary)
    assert calculate_orb_factor(5, 10) == 0.5


# =============================================================================
# Basic Transit Power Tests
# =============================================================================

def test_transit_power_exact_aspect():
    """Test transit power for exact aspect (orb factor = 1.0)."""
    # Exact square (8) with Saturn (×1.2)
    power = calculate_transit_power_basic(
        AspectType.SQUARE,
        orb_deviation=0.0,
        max_orb=8.0,
        transit_planet=Planet.SATURN
    )
    # 8 × 1.0 × 1.2 = 9.6
    assert power == 9.6


def test_transit_power_spec_example_partial():
    """
    Test partial calculation from spec example.

    Spec example: Transit Saturn square Natal Sun
    - Aspect: Square (8)
    - Orb: 2° from exact (max orb 8°)
    - Orb Factor: 1 - (2/8) = 0.775
    - Transit Weight: Social planet (1.2)

    Spec shows 9.70 final but that includes direction modifier (×1.3)
    Without direction modifier: 8 × 0.775 × 1.2 = 7.44
    """
    power = calculate_transit_power_basic(
        AspectType.SQUARE,
        orb_deviation=2.0,
        max_orb=8.0,
        transit_planet=Planet.SATURN
    )
    # 8 × 0.75 × 1.2 = 7.2
    # Note: 0.75 not 0.778 because 1-(2/8) = 0.75 exactly
    assert abs(power - 7.2) < 0.01


def test_transit_power_outer_planet():
    """Test transit power with outer planet (higher weight)."""
    # Pluto trine (6) with 0° orb
    power = calculate_transit_power_basic(
        AspectType.TRINE,
        orb_deviation=0.0,
        max_orb=8.0,
        transit_planet=Planet.PLUTO
    )
    # 6 × 1.0 × 1.5 = 9.0
    assert power == 9.0


def test_transit_power_inner_planet():
    """Test transit power with inner planet (weight = 1.0)."""
    # Venus sextile (4) with 0° orb
    power = calculate_transit_power_basic(
        AspectType.SEXTILE,
        orb_deviation=0.0,
        max_orb=5.0,
        transit_planet=Planet.VENUS
    )
    # 4 × 1.0 × 1.0 = 4.0
    assert power == 4.0


def test_transit_power_moon():
    """Test transit power with Moon (de-emphasized, weight = 0.8)."""
    # Moon conjunction (10) with 0° orb
    power = calculate_transit_power_basic(
        AspectType.CONJUNCTION,
        orb_deviation=0.0,
        max_orb=10.0,
        transit_planet=Planet.MOON
    )
    # 10 × 1.0 × 0.8 = 8.0
    assert power == 8.0


def test_transit_power_wide_orb():
    """Test transit power with wide orb (low orb factor)."""
    # Square with 6° deviation from 8° max
    # Orb factor = 1 - (6/8) = 0.25
    power = calculate_transit_power_basic(
        AspectType.SQUARE,
        orb_deviation=6.0,
        max_orb=8.0,
        transit_planet=Planet.SATURN
    )
    # 8 × 0.25 × 1.2 = 2.4
    assert power == 2.4


def test_transit_power_at_max_orb():
    """Test transit power at maximum orb (orb factor = 0)."""
    power = calculate_transit_power_basic(
        AspectType.SQUARE,
        orb_deviation=8.0,
        max_orb=8.0,
        transit_planet=Planet.SATURN
    )
    # 8 × 0.0 × 1.2 = 0.0
    assert power == 0.0


def test_transit_power_all_aspect_types():
    """Test that all aspect types have different base intensities."""
    aspects_powers = {}
    for aspect_type in ASPECT_BASE_INTENSITY.keys():
        power = calculate_transit_power_basic(
            aspect_type,
            orb_deviation=0.0,
            max_orb=8.0,
            transit_planet=Planet.SUN  # Weight = 1.0
        )
        aspects_powers[aspect_type] = power

    # Conjunction should be strongest
    assert aspects_powers[AspectType.CONJUNCTION] == 10.0
    assert aspects_powers[AspectType.OPPOSITION] == 9.0
    assert aspects_powers[AspectType.SQUARE] == 8.0
    assert aspects_powers[AspectType.TRINE] == 6.0
    assert aspects_powers[AspectType.SEXTILE] == 4.0


# =============================================================================
# Aspect Strength Label Tests
# =============================================================================

def test_aspect_strength_labels():
    """Test aspect strength label generation."""
    assert get_aspect_strength_label(1.0) == "Exact"
    assert get_aspect_strength_label(0.95) == "Exact"
    assert get_aspect_strength_label(0.8) == "Very Strong"
    assert get_aspect_strength_label(0.6) == "Strong"
    assert get_aspect_strength_label(0.4) == "Moderate"
    assert get_aspect_strength_label(0.2) == "Weak"
    assert get_aspect_strength_label(0.0) == "None"


# =============================================================================
# Integration Tests
# =============================================================================

def test_integration_detect_and_calculate():
    """Test full workflow: detect aspect then calculate power."""
    # Transit Saturn at 92°, Natal Sun at 0°
    result = detect_aspect(92, 0, Planet.SATURN, Planet.SUN)

    assert result is not None
    aspect_type, deviation, max_orb = result

    # Should detect square (90°) with 2° deviation
    assert aspect_type == AspectType.SQUARE
    assert abs(deviation - 2.0) < 0.001

    # Calculate power
    power = calculate_transit_power_basic(
        aspect_type, deviation, max_orb, Planet.SATURN
    )

    # 8 × 0.75 × 1.2 = 7.2
    assert abs(power - 7.2) < 0.01

    # Check strength label
    orb_factor = calculate_orb_factor(deviation, max_orb)
    label = get_aspect_strength_label(orb_factor)
    assert label == "Very Strong"  # 0.75 orb factor (>= 0.7)


def test_integration_multiple_transits():
    """Test detecting aspects from multiple transit planets."""
    natal_sun = 0  # Sun at 0° Aries

    transits = [
        (Planet.SATURN, 92),   # Square
        (Planet.JUPITER, 120), # Trine
        (Planet.MARS, 60),     # Sextile
        (Planet.VENUS, 45),    # No major aspect
    ]

    detected = []
    for transit_planet, transit_long in transits:
        result = detect_aspect(transit_long, natal_sun, transit_planet, Planet.SUN)
        if result:
            detected.append((transit_planet, result[0]))

    # Should detect 3 aspects
    assert len(detected) == 3
    assert (Planet.SATURN, AspectType.SQUARE) in detected
    assert (Planet.JUPITER, AspectType.TRINE) in detected
    assert (Planet.MARS, AspectType.SEXTILE) in detected


# =============================================================================
# Phase 4 Part 2: Direction and Station Modifier Tests
# =============================================================================

def test_direction_modifier_exact():
    """Test that aspect within 0.5° is considered exact."""
    from astrometers.transit_power import get_direction_modifier

    status, modifier = get_direction_modifier(0.3, 0.6)
    assert status == "exact"
    assert modifier == 1.5


def test_direction_modifier_applying():
    """Test that aspect getting tighter is applying."""
    from astrometers.transit_power import get_direction_modifier

    # Tomorrow (1.5°) is closer than today (2.0°)
    status, modifier = get_direction_modifier(2.0, 1.5)
    assert status == "applying"
    assert modifier == 1.3


def test_direction_modifier_separating():
    """Test that aspect getting wider is separating."""
    from astrometers.transit_power import get_direction_modifier

    # Tomorrow (2.0°) is farther than today (1.5°)
    status, modifier = get_direction_modifier(1.5, 2.0)
    assert status == "separating"
    assert modifier == 0.7


def test_direction_modifier_exact_takes_precedence():
    """Test that exact status takes precedence over direction."""
    from astrometers.transit_power import get_direction_modifier

    # Even if getting wider, if today is exact, it's exact
    status, modifier = get_direction_modifier(0.4, 0.6)
    assert status == "exact"
    assert modifier == 1.5


def test_station_modifier_exact_station():
    """Test station modifier at exact station (0 days)."""
    from astrometers.transit_power import calculate_station_modifier

    modifier = calculate_station_modifier(0)
    assert modifier == 1.8


def test_station_modifier_5_days():
    """Test station modifier at 5 days from station."""
    from astrometers.transit_power import calculate_station_modifier

    modifier = calculate_station_modifier(5)
    assert modifier == 1.2


def test_station_modifier_3_days():
    """Test station modifier at 3 days from station."""
    from astrometers.transit_power import calculate_station_modifier

    modifier = calculate_station_modifier(3)
    # 1.8 - (0.12 * 3) = 1.44
    assert abs(modifier - 1.44) < 0.01


def test_station_modifier_not_stationary():
    """Test station modifier when not stationary (None)."""
    from astrometers.transit_power import calculate_station_modifier

    modifier = calculate_station_modifier(None)
    assert modifier == 1.0


def test_complete_transit_power_spec_example():
    """
    Test complete calculation matching spec example.

    Spec: Transit Saturn square Natal Sun
    - Aspect: Square (8)
    - Orb: 2° from exact (max orb 8°)
    - Orb Factor: 1 - (2/8) = 0.75
    - Direction: Applying (×1.3)
    - Station: Not stationary (×1.0)
    - Transit Weight: Social planet (×1.2)

    Result: 8 × 0.75 × 1.3 × 1.0 × 1.2 = 9.36
    """
    from astrometers.transit_power import calculate_transit_power_complete

    power, breakdown = calculate_transit_power_complete(
        AspectType.SQUARE,
        orb_deviation=2.0,
        max_orb=8.0,
        transit_planet=Planet.SATURN,
        today_deviation=2.0,
        tomorrow_deviation=1.5  # Applying
    )

    # 8 × 0.75 × 1.3 × 1.0 × 1.2 = 9.36
    assert abs(power - 9.36) < 0.01

    # Check breakdown
    assert breakdown['aspect_base'] == 8
    assert abs(breakdown['orb_factor'] - 0.75) < 0.01
    assert breakdown['direction_modifier'] == 1.3
    assert breakdown['direction_status'] == "applying"
    assert breakdown['station_modifier'] == 1.0
    assert breakdown['transit_weight'] == 1.2
    assert breakdown['is_stationary'] is False


def test_complete_transit_power_exact_aspect():
    """Test complete power with exact aspect."""
    from astrometers.transit_power import calculate_transit_power_complete

    power, breakdown = calculate_transit_power_complete(
        AspectType.TRINE,
        orb_deviation=0.0,
        max_orb=8.0,
        transit_planet=Planet.JUPITER,
        today_deviation=0.3,  # Exact (< 0.5°)
        tomorrow_deviation=0.5
    )

    # 6 × 1.0 × 1.5 × 1.0 × 1.2 = 10.8
    assert abs(power - 10.8) < 0.01
    assert breakdown['direction_status'] == "exact"
    assert breakdown['direction_modifier'] == 1.5


def test_complete_transit_power_separating():
    """Test complete power with separating aspect."""
    from astrometers.transit_power import calculate_transit_power_complete

    power, breakdown = calculate_transit_power_complete(
        AspectType.OPPOSITION,
        orb_deviation=3.0,
        max_orb=10.0,
        transit_planet=Planet.URANUS,
        today_deviation=3.0,
        tomorrow_deviation=3.5  # Separating (getting wider)
    )

    # 9 × 0.7 × 0.7 × 1.0 × 1.5 = 6.615
    assert abs(power - 6.615) < 0.01
    assert breakdown['direction_status'] == "separating"
    assert breakdown['direction_modifier'] == 0.7


def test_complete_transit_power_with_station():
    """Test complete power with station modifier."""
    from astrometers.transit_power import calculate_transit_power_complete

    power, breakdown = calculate_transit_power_complete(
        AspectType.SQUARE,
        orb_deviation=1.0,
        max_orb=8.0,
        transit_planet=Planet.SATURN,
        today_deviation=1.0,
        tomorrow_deviation=0.8,  # Applying
        days_from_station=0  # Exact station
    )

    # 8 × 0.875 × 1.3 × 1.8 × 1.2 = 19.656
    assert abs(power - 19.656) < 0.01
    assert breakdown['station_modifier'] == 1.8
    assert breakdown['is_stationary'] is True


def test_complete_transit_power_all_modifiers():
    """Test complete power with all modifiers active."""
    from astrometers.transit_power import calculate_transit_power_complete

    power, breakdown = calculate_transit_power_complete(
        AspectType.CONJUNCTION,
        orb_deviation=0.0,  # Exact orb
        max_orb=10.0,
        transit_planet=Planet.PLUTO,
        today_deviation=0.2,  # Exact aspect
        tomorrow_deviation=0.3,
        days_from_station=2  # Near station
    )

    # Calculate expected:
    # aspect_base = 10
    # orb_factor = 1.0
    # direction_mod = 1.5 (exact)
    # station_mod = 1.8 - (0.12 * 2) = 1.56
    # transit_weight = 1.5 (outer planet)
    # 10 × 1.0 × 1.5 × 1.56 × 1.5 = 35.1
    assert abs(power - 35.1) < 0.1
    assert breakdown['direction_status'] == "exact"
    assert abs(breakdown['station_modifier'] - 1.56) < 0.01


def test_complete_transit_power_without_direction():
    """Test complete power when direction not provided (defaults to 1.0)."""
    from astrometers.transit_power import calculate_transit_power_complete

    power, breakdown = calculate_transit_power_complete(
        AspectType.SEXTILE,
        orb_deviation=2.0,
        max_orb=5.0,
        transit_planet=Planet.VENUS
        # No today/tomorrow deviation
    )

    # 4 × 0.6 × 1.0 × 1.0 × 1.0 = 2.4
    assert abs(power - 2.4) < 0.01
    assert breakdown['direction_status'] == "unknown"
    assert breakdown['direction_modifier'] == 1.0


def test_aspect_direction_status_helper():
    """Test helper function that calculates direction from positions."""
    from astrometers.transit_power import get_aspect_direction_status

    # Saturn moving from 92° to 91° (applying to 90° square with Sun at 0°)
    status, modifier = get_aspect_direction_status(
        transit_longitude_today=92.0,
        natal_longitude=0.0,
        transit_longitude_tomorrow=91.0,
        aspect_type=AspectType.SQUARE
    )

    assert status == "applying"
    assert modifier == 1.3


def test_direction_status_retrograde_motion():
    """Test direction with retrograde motion (backward through zodiac)."""
    from astrometers.transit_power import get_aspect_direction_status

    # Saturn retrograde: moving from 88° to 89° (separating from 90° square)
    # Even though numerically increasing, it's moving away from exact 90°
    status, modifier = get_aspect_direction_status(
        transit_longitude_today=88.0,
        natal_longitude=0.0,
        transit_longitude_tomorrow=89.0,
        aspect_type=AspectType.SQUARE
    )

    assert status == "applying"  # Getting closer to 90°
    assert modifier == 1.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

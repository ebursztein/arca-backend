"""
Unit tests for meters module - retrograde handling and velocity calculations.

Tests Issue #2 (retrograde modifiers) and Issue #3 (planetary velocities).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from datetime import datetime
from astro import Planet, AspectType, compute_birth_chart, find_natal_transit_aspects
from astrometers.meters import (
    calculate_tomorrow_orb,
    PLANET_DAILY_MOTION,
    convert_to_transit_aspects,
    get_meters
)


# ============================================================================
# Issue #3: Planetary Velocity Tests
# ============================================================================

class TestPlanetaryVelocities:
    """Test velocity-based orb calculations."""

    def test_planet_daily_motion_constants(self):
        """Test that all major planets have velocity constants."""
        required_planets = [
            Planet.MOON, Planet.SUN, Planet.MERCURY, Planet.VENUS,
            Planet.MARS, Planet.JUPITER, Planet.SATURN, Planet.URANUS,
            Planet.NEPTUNE, Planet.PLUTO, Planet.NORTH_NODE
        ]
        for planet in required_planets:
            assert planet in PLANET_DAILY_MOTION, f"{planet} missing velocity constant"
            assert PLANET_DAILY_MOTION[planet] != 0, f"{planet} has zero velocity"

    def test_velocity_order(self):
        """Test that planetary velocities follow expected order (Moon fastest, Pluto slowest)."""
        assert PLANET_DAILY_MOTION[Planet.MOON] > PLANET_DAILY_MOTION[Planet.SUN]
        assert PLANET_DAILY_MOTION[Planet.SUN] > PLANET_DAILY_MOTION[Planet.MARS]
        assert PLANET_DAILY_MOTION[Planet.MARS] > PLANET_DAILY_MOTION[Planet.JUPITER]
        assert PLANET_DAILY_MOTION[Planet.JUPITER] > PLANET_DAILY_MOTION[Planet.SATURN]
        assert PLANET_DAILY_MOTION[Planet.SATURN] > PLANET_DAILY_MOTION[Planet.PLUTO]

    def test_moon_fast_applying(self):
        """Test Moon (fast mover) applying aspect calculation."""
        # Moon at 5° orb, applying, should decrease by 13°/day
        tomorrow = calculate_tomorrow_orb(5.0, True, Planet.MOON, False)
        assert tomorrow == 0.0  # Capped at 0 (would be -8° otherwise)

    def test_moon_fast_separating(self):
        """Test Moon (fast mover) separating aspect calculation."""
        # Moon at 2° orb, separating, should increase by 13°/day
        tomorrow = calculate_tomorrow_orb(2.0, False, Planet.MOON, False)
        assert tomorrow == pytest.approx(15.0, abs=0.1)

    def test_saturn_slow_applying(self):
        """Test Saturn (slow mover) applying aspect calculation."""
        # Saturn at 2° orb, applying, should decrease by 0.03°/day
        tomorrow = calculate_tomorrow_orb(2.0, True, Planet.SATURN, False)
        assert tomorrow == pytest.approx(1.97, abs=0.01)

    def test_saturn_slow_separating(self):
        """Test Saturn (slow mover) separating aspect calculation."""
        # Saturn at 1.5° orb, separating, should increase by 0.03°/day
        tomorrow = calculate_tomorrow_orb(1.5, False, Planet.SATURN, False)
        assert tomorrow == pytest.approx(1.53, abs=0.01)

    def test_venus_medium_speed(self):
        """Test Venus (medium speed) calculation."""
        # Venus at 3° orb, separating, should increase by 1.2°/day
        tomorrow = calculate_tomorrow_orb(3.0, False, Planet.VENUS, False)
        assert tomorrow == pytest.approx(4.2, abs=0.1)

    def test_mars_retrograde_applying(self):
        """Test Mars retrograde (slower by 40%) applying calculation."""
        # Mars at 1.5° orb, applying, retrograde
        # Normal speed: 0.5°/day, retrograde: 0.3°/day
        tomorrow = calculate_tomorrow_orb(1.5, True, Planet.MARS, True)
        assert tomorrow == pytest.approx(1.2, abs=0.1)

    def test_jupiter_retrograde_separating(self):
        """Test Jupiter retrograde separating calculation."""
        # Jupiter at 0.5° orb, separating, retrograde
        # Normal speed: 0.08°/day, retrograde: 0.048°/day
        tomorrow = calculate_tomorrow_orb(0.5, False, Planet.JUPITER, True)
        assert tomorrow == pytest.approx(0.548, abs=0.01)

    def test_orb_cannot_go_negative(self):
        """Test that applying aspects cap at 0° (can't go negative)."""
        # Venus at 0.5° orb, applying, would go to -0.7° but should cap at 0°
        tomorrow = calculate_tomorrow_orb(0.5, True, Planet.VENUS, False)
        assert tomorrow == 0.0

    def test_north_node_backward_motion(self):
        """Test North Node moves backward (negative velocity)."""
        assert PLANET_DAILY_MOTION[Planet.NORTH_NODE] < 0


class TestConvertToTransitAspects:
    """Test that convert_to_transit_aspects uses velocity-based calculations."""

    def test_uses_velocity_calculation(self):
        """Test that converted aspects use velocity-based tomorrow orb."""
        # Get charts
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        # Find aspects
        nt_aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=8.0)

        # Convert
        transit_aspects = convert_to_transit_aspects(natal_chart, transit_chart, nt_aspects)

        # Check that we have aspects
        assert len(transit_aspects) > 0

        # Check that tomorrow_deviation is NOT just today_deviation ± 0.2
        for ta in transit_aspects:
            fixed_calc_applying = ta.today_deviation - 0.2
            fixed_calc_separating = ta.today_deviation + 0.2

            # Tomorrow deviation should NOT match the old fixed calculation
            # (unless by coincidence, which is unlikely for most aspects)
            if ta.transit_planet in [Planet.MOON, Planet.SATURN]:
                # For very fast or very slow planets, it definitely won't match
                assert ta.tomorrow_deviation not in [fixed_calc_applying, fixed_calc_separating]


# ============================================================================
# Issue #2: Retrograde Handling Tests
# ============================================================================

class TestRetrogradeHandling:
    """Test retrograde modifier application."""

    def test_saturn_retrograde_affects_career_ambition(self):
        """Test that Saturn retrograde reduces career_ambition harmony."""
        # Create a date when Saturn is retrograde
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        # Check Saturn is retrograde
        saturn_data = next((p for p in transit_chart["planets"] if p["name"] == Planet.SATURN), None)
        assert saturn_data is not None
        assert saturn_data.get("retrograde", False) == True

        # Get meters
        meters = get_meters(natal_chart, transit_chart)

        # Check that Saturn retrograde is tracked
        assert meters.career_ambition.additional_context.get("saturn_retrograde", False) == True

        # Check that retrograde note is present
        assert "retrograde" in meters.career_ambition.interpretation.lower()

    def test_venus_direct_no_retrograde_note(self):
        """Test that Venus direct (not retrograde) doesn't add retrograde note."""
        # Create a date when Venus is direct
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        # Check Venus is direct
        venus_data = next((p for p in transit_chart["planets"] if p["name"] == Planet.VENUS), None)
        assert venus_data is not None
        assert venus_data.get("retrograde", False) == False

        # Get meters
        meters = get_meters(natal_chart, transit_chart)

        # Check that Venus retrograde is NOT tracked
        assert meters.relationship_harmony.additional_context.get("venus_retrograde", False) == False

        # Check that retrograde note is NOT present
        assert "venus retrograde" not in meters.relationship_harmony.interpretation.lower()

    def test_retrograde_harmony_multiplier(self):
        """Test that retrograde reduces harmony by expected multiplier."""
        # This is an indirect test since we can't easily isolate the multiplier effect
        # But we can verify the context flag is set correctly
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        meters = get_meters(natal_chart, transit_chart)

        # Saturn is retrograde on this date
        assert meters.career_ambition.additional_context.get("saturn_retrograde") == True

        # Uranus and Neptune are also retrograde on this date
        # But they don't have dedicated meters with retrograde handling yet
        uranus_data = next((p for p in transit_chart["planets"] if p["name"] == Planet.URANUS), None)
        neptune_data = next((p for p in transit_chart["planets"] if p["name"] == Planet.NEPTUNE), None)
        assert uranus_data.get("retrograde") == True
        assert neptune_data.get("retrograde") == True

    def test_multiple_retrogrades_tracked(self):
        """Test that multiple retrograde planets are tracked independently."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        meters = get_meters(natal_chart, transit_chart)

        # Check which meters track retrogrades
        meters_with_rx = []
        for meter_name in ['mental_clarity', 'relationship_harmony', 'physical_energy',
                           'conflict_risk', 'motivation_drive', 'career_ambition',
                           'opportunity_window']:
            meter = getattr(meters, meter_name)
            has_rx = any('retrograde' in k for k in meter.additional_context.keys())
            if has_rx:
                meters_with_rx.append(meter_name)

        # At least career_ambition should have Saturn retrograde
        assert 'career_ambition' in meters_with_rx


class TestRetrogradeNotes:
    """Test that retrograde notes are correctly formatted."""

    def test_saturn_rx_note_format(self):
        """Test Saturn retrograde note format."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        meters = get_meters(natal_chart, transit_chart)

        interp = meters.career_ambition.interpretation

        # Should contain "Note:"
        assert "Note:" in interp or "note:" in interp.lower()

        # Should mention Saturn and retrograde
        assert "saturn" in interp.lower()
        assert "retrograde" in interp.lower()

        # Should provide context about delays/restructuring
        assert "delay" in interp.lower() or "restructur" in interp.lower()


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""

    def test_full_meters_calculation_with_all_features(self):
        """Test complete meter calculation with retrograde and velocity features."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        # This should work without errors and include all features
        meters = get_meters(natal_chart, transit_chart)

        # Verify basic structure
        assert meters.aspect_count > 0
        assert meters.overall_intensity.intensity >= 0
        assert meters.overall_intensity.intensity <= 100
        assert meters.overall_harmony.harmony >= 0
        assert meters.overall_harmony.harmony <= 100

        # Verify key aspects are extracted
        assert len(meters.key_aspects) > 0

        # Verify all 23 meters are present
        meter_names = [
            'overall_intensity', 'overall_harmony',
            'mental_clarity', 'decision_quality', 'communication_flow',
            'emotional_intensity', 'relationship_harmony', 'emotional_resilience',
            'physical_energy', 'conflict_risk', 'motivation_drive',
            'career_ambition', 'opportunity_window', 'challenge_intensity', 'transformation_pressure',
            'fire_energy', 'earth_energy', 'air_energy', 'water_energy',
            'intuition_spirituality', 'innovation_breakthrough', 'karmic_lessons', 'social_collective'
        ]
        for name in meter_names:
            assert hasattr(meters, name), f"Missing meter: {name}"
            meter = getattr(meters, name)
            assert meter.meter_name == name
            assert meter.intensity >= 0 and meter.intensity <= 100
            assert meter.harmony >= 0 and meter.harmony <= 100


# ============================================================================
# Issue #4: Sign Strength Weighting Tests
# ============================================================================

class TestSignStrengthWeighting:
    """Test sign strength calculation for element distribution."""

    def test_center_of_sign_full_strength(self):
        """Test that 15° (center) has full strength."""
        from astrometers.meters import get_sign_strength
        assert get_sign_strength(15.0) == 1.0

    def test_sign_boundaries_reduced_strength(self):
        """Test that 0° and 29° (boundaries) have reduced strength."""
        from astrometers.meters import get_sign_strength
        assert get_sign_strength(0.0) == pytest.approx(0.7, abs=0.01)
        assert get_sign_strength(29.0) == pytest.approx(0.72, abs=0.02)

    def test_parabolic_curve(self):
        """Test that strength follows parabolic curve from center."""
        from astrometers.meters import get_sign_strength

        # Strength should decrease as we move away from 15°
        center = get_sign_strength(15.0)
        quarter1 = get_sign_strength(7.5)
        quarter2 = get_sign_strength(22.5)

        assert center == 1.0
        assert quarter1 < center
        assert quarter2 < center
        assert quarter1 == pytest.approx(quarter2, abs=0.01)  # Symmetric

    def test_strength_range(self):
        """Test that strength is always between 0.7 and 1.0."""
        from astrometers.meters import get_sign_strength

        for degree in [0, 5, 10, 15, 20, 25, 29]:
            strength = get_sign_strength(degree)
            assert 0.7 <= strength <= 1.0

    def test_element_distribution_uses_weighting(self):
        """Test that element distribution uses weighted calculations."""
        from astrometers.meters import calculate_element_distribution

        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        # Calculate element distribution
        element_dist = calculate_element_distribution(natal_chart, transit_chart)

        # Check that we get valid percentages
        assert len(element_dist) == 4
        assert all(elem in element_dist for elem in ["fire", "earth", "air", "water"])

        # Check that percentages sum to ~100%
        total = sum(element_dist.values())
        assert total == pytest.approx(100.0, abs=1.0)

        # Check that all values are reasonable (not all equal)
        values = list(element_dist.values())
        assert max(values) - min(values) > 0  # Some variance expected


# ============================================================================
# Unified Score Tests
# ============================================================================

class TestUnifiedScore:
    """Test unified score calculation for single-bar display."""

    def test_quiet_very_low_intensity(self):
        """Test that very low intensity (< 25) always returns quiet."""
        from astrometers.meters import calculate_unified_score, QualityLabel

        # Low intensity, high harmony -> quiet
        score, quality = calculate_unified_score(20, 90)
        assert score == 20
        assert quality == QualityLabel.QUIET

        # Low intensity, low harmony -> quiet
        score, quality = calculate_unified_score(15, 10)
        assert score == 15
        assert quality == QualityLabel.QUIET

    def test_peaceful_low_intensity_high_harmony(self):
        """Test peaceful state (25-40 intensity + high harmony)."""
        from astrometers.meters import calculate_unified_score, QualityLabel

        score, quality = calculate_unified_score(35, 80)
        assert score == 35
        assert quality == QualityLabel.PEACEFUL

        score, quality = calculate_unified_score(39, 70)
        assert score == 39
        assert quality == QualityLabel.PEACEFUL

    def test_harmonious_high_harmony(self):
        """Test harmonious quality (harmony >= 70)."""
        from astrometers.meters import calculate_unified_score, QualityLabel

        score, quality = calculate_unified_score(85, 90)
        assert score == 85
        assert quality == QualityLabel.HARMONIOUS

        score, quality = calculate_unified_score(50, 75)
        assert score == 50
        assert quality == QualityLabel.HARMONIOUS

    def test_challenging_low_harmony(self):
        """Test challenging quality (harmony <= 30)."""
        from astrometers.meters import calculate_unified_score, QualityLabel

        score, quality = calculate_unified_score(85, 25)
        assert score == 85
        assert quality == QualityLabel.CHALLENGING

        score, quality = calculate_unified_score(60, 15)
        assert score == 60
        assert quality == QualityLabel.CHALLENGING

    def test_mixed_moderate_harmony(self):
        """Test mixed quality (31-69 harmony)."""
        from astrometers.meters import calculate_unified_score, QualityLabel

        score, quality = calculate_unified_score(70, 50)
        assert score == 70
        assert quality == QualityLabel.MIXED

        score, quality = calculate_unified_score(45, 40)
        assert score == 45
        assert quality == QualityLabel.MIXED

    def test_unified_score_equals_intensity(self):
        """Test that unified score always equals intensity."""
        from astrometers.meters import calculate_unified_score

        test_cases = [
            (10, 20), (25, 50), (50, 80), (85, 15), (100, 100)
        ]

        for intensity, harmony in test_cases:
            score, _ = calculate_unified_score(intensity, harmony)
            assert score == intensity

    def test_quality_boundaries(self):
        """Test exact boundary conditions."""
        from astrometers.meters import calculate_unified_score, QualityLabel

        # Boundary at 25 intensity
        assert calculate_unified_score(24.9, 50)[1] == QualityLabel.QUIET
        assert calculate_unified_score(25.0, 50)[1] == QualityLabel.MIXED

        # Boundary at 40 intensity for peaceful
        assert calculate_unified_score(39.9, 70)[1] == QualityLabel.PEACEFUL
        assert calculate_unified_score(40.0, 70)[1] == QualityLabel.HARMONIOUS

        # Boundary at 30 harmony
        assert calculate_unified_score(50, 30)[1] == QualityLabel.CHALLENGING
        assert calculate_unified_score(50, 31)[1] == QualityLabel.MIXED

        # Boundary at 70 harmony
        assert calculate_unified_score(50, 69)[1] == QualityLabel.MIXED
        assert calculate_unified_score(50, 70)[1] == QualityLabel.HARMONIOUS

    def test_meter_reading_includes_unified_fields(self):
        """Test that MeterReading objects include unified score fields."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        meters = get_meters(natal_chart, transit_chart)

        # Check all meters have unified fields
        for meter_name in ['overall_intensity', 'overall_harmony', 'mental_clarity',
                           'relationship_harmony', 'career_ambition']:
            meter = getattr(meters, meter_name)
            assert hasattr(meter, 'unified_score')
            assert hasattr(meter, 'unified_quality')
            assert 0 <= meter.unified_score <= 100
            assert meter.unified_quality in ['quiet', 'peaceful', 'harmonious', 'mixed', 'challenging']


# ============================================================================
# Meter Organization Tests (Group and Trend)
# ============================================================================

class TestMeterOrganization:
    """Test meter grouping and trend calculation."""

    def test_all_meters_have_groups(self):
        """Test that all meters are assigned to groups."""
        from astrometers.meters import MeterGroup

        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        meters = get_meters(natal_chart, transit_chart)

        # Check all 23 meters have groups
        meter_names = [
            'overall_intensity', 'overall_harmony',
            'mental_clarity', 'decision_quality', 'communication_flow',
            'emotional_intensity', 'relationship_harmony', 'emotional_resilience',
            'physical_energy', 'conflict_risk', 'motivation_drive',
            'career_ambition', 'opportunity_window', 'challenge_intensity', 'transformation_pressure',
            'fire_energy', 'earth_energy', 'air_energy', 'water_energy',
            'intuition_spirituality', 'innovation_breakthrough', 'karmic_lessons', 'social_collective'
        ]

        for name in meter_names:
            meter = getattr(meters, name)
            assert hasattr(meter, 'group')
            assert isinstance(meter.group, MeterGroup)

    def test_group_mapping_correctness(self):
        """Test that meters are mapped to correct groups."""
        from astrometers.meters import MeterGroup

        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        meters = get_meters(natal_chart, transit_chart)

        # Test specific group assignments (new 9-group system)
        assert meters.overall_intensity.group == MeterGroup.OVERVIEW
        assert meters.overall_harmony.group == MeterGroup.OVERVIEW

        assert meters.mental_clarity.group == MeterGroup.MIND
        assert meters.decision_quality.group == MeterGroup.MIND
        assert meters.communication_flow.group == MeterGroup.MIND

        assert meters.emotional_intensity.group == MeterGroup.EMOTIONS
        assert meters.relationship_harmony.group == MeterGroup.EMOTIONS
        assert meters.emotional_resilience.group == MeterGroup.EMOTIONS

        assert meters.physical_energy.group == MeterGroup.BODY
        assert meters.conflict_risk.group == MeterGroup.BODY
        assert meters.motivation_drive.group == MeterGroup.BODY

        assert meters.career_ambition.group == MeterGroup.CAREER
        assert meters.opportunity_window.group == MeterGroup.CAREER

        assert meters.challenge_intensity.group == MeterGroup.EVOLUTION
        assert meters.transformation_pressure.group == MeterGroup.EVOLUTION
        assert meters.innovation_breakthrough.group == MeterGroup.EVOLUTION

        assert meters.fire_energy.group == MeterGroup.ELEMENTS
        assert meters.earth_energy.group == MeterGroup.ELEMENTS
        assert meters.air_energy.group == MeterGroup.ELEMENTS
        assert meters.water_energy.group == MeterGroup.ELEMENTS

        assert meters.intuition_spirituality.group == MeterGroup.SPIRITUAL
        assert meters.karmic_lessons.group == MeterGroup.SPIRITUAL

        assert meters.social_collective.group == MeterGroup.COLLECTIVE

    def test_calculate_trend_improving(self):
        """Test trend calculation for improving harmony."""
        from astrometers.meters import MeterReading, MeterGroup, QualityLabel, TrendDirection

        yesterday = MeterReading(
            meter_name="test",
            date=datetime(2025, 10, 25),
            group=MeterGroup.OVERVIEW,
            unified_score=50,
            unified_quality=QualityLabel.MIXED,
            intensity=50,
            harmony=40,
            state_label="Test",
            interpretation="Test",
            advice=[],
            top_aspects=[],
            raw_scores={}
        )

        today = MeterReading(
            meter_name="test",
            date=datetime(2025, 10, 26),
            group=MeterGroup.OVERVIEW,
            unified_score=50,
            unified_quality=QualityLabel.MIXED,
            intensity=50,
            harmony=55,  # +15 points
            state_label="Test",
            interpretation="Test",
            advice=[],
            top_aspects=[],
            raw_scores={}
        )

        trend = today.calculate_trend(yesterday)
        assert trend == TrendDirection.IMPROVING

    def test_calculate_trend_worsening(self):
        """Test trend calculation for worsening harmony."""
        from astrometers.meters import MeterReading, MeterGroup, QualityLabel, TrendDirection

        yesterday = MeterReading(
            meter_name="test",
            date=datetime(2025, 10, 25),
            group=MeterGroup.OVERVIEW,
            unified_score=50,
            unified_quality=QualityLabel.MIXED,
            intensity=50,
            harmony=60,
            state_label="Test",
            interpretation="Test",
            advice=[],
            top_aspects=[],
            raw_scores={}
        )

        today = MeterReading(
            meter_name="test",
            date=datetime(2025, 10, 26),
            group=MeterGroup.OVERVIEW,
            unified_score=50,
            unified_quality=QualityLabel.MIXED,
            intensity=50,
            harmony=45,  # -15 points
            state_label="Test",
            interpretation="Test",
            advice=[],
            top_aspects=[],
            raw_scores={}
        )

        trend = today.calculate_trend(yesterday)
        assert trend == TrendDirection.WORSENING

    def test_calculate_trend_stable(self):
        """Test trend calculation for stable harmony."""
        from astrometers.meters import MeterReading, MeterGroup, QualityLabel, TrendDirection

        yesterday = MeterReading(
            meter_name="test",
            date=datetime(2025, 10, 25),
            group=MeterGroup.OVERVIEW,
            unified_score=50,
            unified_quality=QualityLabel.MIXED,
            intensity=50,
            harmony=50,
            state_label="Test",
            interpretation="Test",
            advice=[],
            top_aspects=[],
            raw_scores={}
        )

        today = MeterReading(
            meter_name="test",
            date=datetime(2025, 10, 26),
            group=MeterGroup.OVERVIEW,
            unified_score=50,
            unified_quality=QualityLabel.MIXED,
            intensity=50,
            harmony=55,  # +5 points (within stable range)
            state_label="Test",
            interpretation="Test",
            advice=[],
            top_aspects=[],
            raw_scores={}
        )

        trend = today.calculate_trend(yesterday)
        assert trend == TrendDirection.STABLE

    def test_overall_unified_score_in_all_meters(self):
        """Test that AllMetersReading includes top-level overall unified score."""
        natal_chart, _ = compute_birth_chart("1990-06-15")
        transit_chart, _ = compute_birth_chart("2025-10-26", birth_time="12:00")

        meters = get_meters(natal_chart, transit_chart)

        # Check that overall unified score exists at top level
        assert hasattr(meters, 'overall_unified_score')
        assert hasattr(meters, 'overall_unified_quality')
        assert 0 <= meters.overall_unified_score <= 100

        # Check that it matches the overall_intensity meter
        assert meters.overall_unified_score == meters.overall_intensity.unified_score
        assert meters.overall_unified_quality == meters.overall_intensity.unified_quality

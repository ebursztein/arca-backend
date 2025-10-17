"""
Tests for astrology functions.

Run with: pytest functions/astro_test.py -v
"""

import pytest
from astro import (
    get_sun_sign,
    get_sun_sign_profile,
    SunSignProfile,
    compute_birth_chart,
    summarize_transits,
    ZodiacSign,
    Element,
    Modality
)


class TestGetSunSign:
    """Tests for sun sign calculator."""

    def test_aries(self):
        assert get_sun_sign("1990-03-21") == ZodiacSign.ARIES
        assert get_sun_sign("1990-04-19") == ZodiacSign.ARIES

    def test_taurus(self):
        assert get_sun_sign("1990-04-20") == ZodiacSign.TAURUS
        assert get_sun_sign("1990-05-20") == ZodiacSign.TAURUS

    def test_gemini(self):
        assert get_sun_sign("1990-05-21") == ZodiacSign.GEMINI
        assert get_sun_sign("1990-06-20") == ZodiacSign.GEMINI

    def test_cancer(self):
        assert get_sun_sign("1990-06-21") == ZodiacSign.CANCER
        assert get_sun_sign("1990-07-22") == ZodiacSign.CANCER

    def test_leo(self):
        assert get_sun_sign("1990-07-23") == ZodiacSign.LEO
        assert get_sun_sign("1990-08-22") == ZodiacSign.LEO

    def test_virgo(self):
        assert get_sun_sign("1990-08-23") == ZodiacSign.VIRGO
        assert get_sun_sign("1990-09-22") == ZodiacSign.VIRGO

    def test_libra(self):
        assert get_sun_sign("1990-09-23") == ZodiacSign.LIBRA
        assert get_sun_sign("1990-10-22") == ZodiacSign.LIBRA

    def test_scorpio(self):
        assert get_sun_sign("1990-10-23") == ZodiacSign.SCORPIO
        assert get_sun_sign("1990-11-21") == ZodiacSign.SCORPIO

    def test_sagittarius(self):
        assert get_sun_sign("1990-11-22") == ZodiacSign.SAGITTARIUS
        assert get_sun_sign("1990-12-21") == ZodiacSign.SAGITTARIUS

    def test_capricorn(self):
        assert get_sun_sign("1990-12-22") == ZodiacSign.CAPRICORN
        assert get_sun_sign("1990-01-19") == ZodiacSign.CAPRICORN

    def test_aquarius(self):
        assert get_sun_sign("1990-01-20") == ZodiacSign.AQUARIUS
        assert get_sun_sign("1990-02-18") == ZodiacSign.AQUARIUS

    def test_pisces(self):
        assert get_sun_sign("1990-02-19") == ZodiacSign.PISCES
        assert get_sun_sign("1990-03-20") == ZodiacSign.PISCES

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_sun_sign("invalid-date")

        with pytest.raises(ValueError):
            get_sun_sign("1990/03/21")  # Wrong separator


class TestGetSunSignProfile:
    """Tests for sun sign profile loader."""

    def test_aries_profile_loads(self):
        """Test loading Aries profile from JSON file."""
        profile = get_sun_sign_profile(ZodiacSign.ARIES)

        assert profile is not None
        assert isinstance(profile, SunSignProfile)
        assert profile.sign == "Aries"
        # Check that string values are converted to enums
        assert profile.element == Element.FIRE
        assert isinstance(profile.element, Element)
        assert profile.modality == Modality.CARDINAL
        assert isinstance(profile.modality, Modality)
        assert profile.ruling_planet == "Mars"
        assert "March 21" in profile.dates and "April 19" in profile.dates
        assert profile.summary is not None
        assert len(profile.summary) > 0

    def test_profile_has_all_8_domains(self):
        """Test that profile has all 8 life domains."""
        profile = get_sun_sign_profile(ZodiacSign.ARIES)

        if profile is not None:
            domains = profile.domain_profiles
            assert domains.love_and_relationships is not None
            assert domains.family_and_friendships is not None
            assert domains.path_and_profession is not None
            assert domains.personal_growth_and_wellbeing is not None
            assert domains.finance_and_abundance is not None
            assert domains.life_purpose_and_spirituality is not None
            assert domains.home_and_environment is not None
            assert domains.decisions_and_crossroads is not None

    def test_all_signs_have_profiles(self):
        """Test that all 12 signs have profile JSON files. HARD FAIL if any missing."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value} missing JSON profile file"
            assert profile.summary is not None, f"{sign.value} missing summary"
            assert len(profile.summary) > 0, f"{sign.value} has empty summary"

    def test_all_profiles_have_required_fields(self):
        """HARD CHECK: All profiles must have all required top-level fields."""
        required_string_fields = [
            'sign', 'dates', 'symbol', 'glyph', 'polarity',
            'ruling_planet', 'ruling_planet_glyph', 'life_lesson',
            'evolutionary_goal', 'mythology', 'seasonal_association', 'summary'
        ]

        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value}: JSON file missing - HARD FAIL"

            # Check all required string fields exist and are non-empty
            for field in required_string_fields:
                value = getattr(profile, field)
                assert value is not None, f"{sign.value}: {field} is None - HARD FAIL"
                assert len(value) > 0, f"{sign.value}: {field} is empty - HARD FAIL"

            # Check enums are proper types
            assert isinstance(profile.element, Element), f"{sign.value}: element is not Element enum - HARD FAIL"
            assert isinstance(profile.modality, Modality), f"{sign.value}: modality is not Modality enum - HARD FAIL"

            # Check arrays are non-empty
            assert len(profile.body_parts_ruled) > 0, f"{sign.value}: body_parts_ruled is empty - HARD FAIL"
            assert len(profile.keywords) > 0, f"{sign.value}: keywords is empty - HARD FAIL"
            assert len(profile.positive_traits) > 0, f"{sign.value}: positive_traits is empty - HARD FAIL"
            assert len(profile.shadow_traits) > 0, f"{sign.value}: shadow_traits is empty - HARD FAIL"
            assert len(profile.archetypal_roles) > 0, f"{sign.value}: archetypal_roles is empty - HARD FAIL"

    def test_all_profiles_have_valid_planetary_dignities(self):
        """HARD CHECK: Planetary dignities must be complete and valid."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value}: JSON file missing - HARD FAIL"

            dignities = profile.planetary_dignities
            assert dignities.exaltation, f"{sign.value}: exaltation is empty - HARD FAIL"
            assert dignities.detriment, f"{sign.value}: detriment is empty - HARD FAIL"
            assert dignities.fall, f"{sign.value}: fall is empty - HARD FAIL"

            # No placeholder text allowed
            assert "TBD" not in dignities.exaltation.upper(), f"{sign.value}: exaltation is TBD - HARD FAIL"
            assert "TBD" not in dignities.detriment.upper(), f"{sign.value}: detriment is TBD - HARD FAIL"
            assert "TBD" not in dignities.fall.upper(), f"{sign.value}: fall is TBD - HARD FAIL"

    def test_all_profiles_have_valid_correspondences(self):
        """HARD CHECK: Correspondences must be complete."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value}: JSON file missing - HARD FAIL"

            corr = profile.correspondences
            assert corr.tarot, f"{sign.value}: tarot correspondence is empty - HARD FAIL"
            assert len(corr.colors) > 0, f"{sign.value}: colors list is empty - HARD FAIL"
            assert len(corr.gemstones) > 0, f"{sign.value}: gemstones list is empty - HARD FAIL"
            assert corr.metal, f"{sign.value}: metal is empty - HARD FAIL"
            assert corr.day_of_week, f"{sign.value}: day_of_week is empty - HARD FAIL"
            assert len(corr.lucky_numbers) > 0, f"{sign.value}: lucky_numbers is empty - HARD FAIL"

            # Validate lucky numbers are positive
            for num in corr.lucky_numbers:
                assert num > 0, f"{sign.value}: lucky number {num} is not positive - HARD FAIL"

    def test_all_profiles_have_valid_health_tendencies(self):
        """HARD CHECK: Health information must be complete."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value}: JSON file missing - HARD FAIL"

            health = profile.health_tendencies
            assert health.strengths, f"{sign.value}: health strengths is empty - HARD FAIL"
            assert health.vulnerabilities, f"{sign.value}: health vulnerabilities is empty - HARD FAIL"
            assert health.wellness_advice, f"{sign.value}: wellness_advice is empty - HARD FAIL"
            assert len(health.wellness_advice) > 20, f"{sign.value}: wellness_advice too short - HARD FAIL"

    def test_all_profiles_have_valid_compatibility(self):
        """HARD CHECK: Compatibility overview must be complete."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value}: JSON file missing - HARD FAIL"

            compat = profile.compatibility_overview
            assert compat.same_sign, f"{sign.value}: same_sign compatibility is empty - HARD FAIL"
            assert len(compat.most_compatible) > 0, f"{sign.value}: most_compatible list is empty - HARD FAIL"
            assert len(compat.challenging) > 0, f"{sign.value}: challenging list is empty - HARD FAIL"
            assert len(compat.growth_oriented) > 0, f"{sign.value}: growth_oriented list is empty - HARD FAIL"

            # Validate all compatibility entries
            for entry in compat.most_compatible:
                assert entry.sign, f"{sign.value}: most_compatible entry missing sign - HARD FAIL"
                assert entry.reason, f"{sign.value}: most_compatible entry missing reason - HARD FAIL"

            for entry in compat.challenging:
                assert entry.sign, f"{sign.value}: challenging entry missing sign - HARD FAIL"
                assert entry.reason, f"{sign.value}: challenging entry missing reason - HARD FAIL"

            for entry in compat.growth_oriented:
                assert entry.sign, f"{sign.value}: growth_oriented entry missing sign - HARD FAIL"
                assert entry.reason, f"{sign.value}: growth_oriented entry missing reason - HARD FAIL"

    def test_all_domain_profiles_are_complete(self):
        """HARD CHECK: All 8 domain profiles must have all required fields."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value}: JSON file missing - HARD FAIL"

            domains = profile.domain_profiles

            # Love & Relationships
            love = domains.love_and_relationships
            assert love.style, f"{sign.value}: love style is empty - HARD FAIL"
            assert love.needs, f"{sign.value}: love needs is empty - HARD FAIL"
            assert love.gives, f"{sign.value}: love gives is empty - HARD FAIL"
            assert love.challenges, f"{sign.value}: love challenges is empty - HARD FAIL"
            assert love.attracts, f"{sign.value}: love attracts is empty - HARD FAIL"
            assert love.communication_style, f"{sign.value}: love communication_style is empty - HARD FAIL"

            # Family & Friendships
            family = domains.family_and_friendships
            assert family.friendship_style, f"{sign.value}: friendship_style is empty - HARD FAIL"
            assert family.parenting_style, f"{sign.value}: parenting_style is empty - HARD FAIL"
            assert family.childhood_needs, f"{sign.value}: childhood_needs is empty - HARD FAIL"
            assert family.family_role, f"{sign.value}: family_role is empty - HARD FAIL"
            assert family.sibling_dynamics, f"{sign.value}: sibling_dynamics is empty - HARD FAIL"

            # Path & Profession
            career = domains.path_and_profession
            assert len(career.career_strengths) > 0, f"{sign.value}: career_strengths is empty - HARD FAIL"
            assert career.work_style, f"{sign.value}: work_style is empty - HARD FAIL"
            assert career.leadership_approach, f"{sign.value}: leadership_approach is empty - HARD FAIL"
            assert career.ideal_work_environment, f"{sign.value}: ideal_work_environment is empty - HARD FAIL"
            assert career.growth_area, f"{sign.value}: career growth_area is empty - HARD FAIL"

            # Personal Growth & Wellbeing
            growth = domains.personal_growth_and_wellbeing
            assert growth.growth_path, f"{sign.value}: growth_path is empty - HARD FAIL"
            assert len(growth.healing_modalities) > 0, f"{sign.value}: healing_modalities is empty - HARD FAIL"
            assert growth.stress_triggers, f"{sign.value}: stress_triggers is empty - HARD FAIL"
            assert growth.stress_relief_practices, f"{sign.value}: stress_relief_practices is empty - HARD FAIL"
            assert growth.mindfulness_approach, f"{sign.value}: mindfulness_approach is empty - HARD FAIL"

            # Finance & Abundance
            finance = domains.finance_and_abundance
            assert finance.money_mindset, f"{sign.value}: money_mindset is empty - HARD FAIL"
            assert finance.earning_style, f"{sign.value}: earning_style is empty - HARD FAIL"
            assert finance.spending_patterns, f"{sign.value}: spending_patterns is empty - HARD FAIL"
            assert finance.abundance_lesson, f"{sign.value}: abundance_lesson is empty - HARD FAIL"
            assert finance.financial_advisory_note, f"{sign.value}: financial_advisory_note is empty - HARD FAIL"

            # Life Purpose & Spirituality
            purpose = domains.life_purpose_and_spirituality
            assert purpose.spiritual_path, f"{sign.value}: spiritual_path is empty - HARD FAIL"
            assert purpose.soul_mission, f"{sign.value}: soul_mission is empty - HARD FAIL"
            assert len(purpose.spiritual_practices) > 0, f"{sign.value}: spiritual_practices is empty - HARD FAIL"
            assert purpose.connection_to_divine, f"{sign.value}: connection_to_divine is empty - HARD FAIL"

            # Home & Environment
            home = domains.home_and_environment
            assert home.home_needs, f"{sign.value}: home_needs is empty - HARD FAIL"
            assert home.decorating_style, f"{sign.value}: decorating_style is empty - HARD FAIL"
            assert home.location_preferences, f"{sign.value}: location_preferences is empty - HARD FAIL"
            assert home.relationship_to_space, f"{sign.value}: relationship_to_space is empty - HARD FAIL"
            assert home.seasonal_home_adjustments, f"{sign.value}: seasonal_home_adjustments is empty - HARD FAIL"

            # Decisions & Crossroads
            decisions = domains.decisions_and_crossroads
            assert decisions.decision_making_style, f"{sign.value}: decision_making_style is empty - HARD FAIL"
            assert decisions.decision_tips, f"{sign.value}: decision_tips is empty - HARD FAIL"
            assert decisions.when_stuck, f"{sign.value}: when_stuck is empty - HARD FAIL"
            assert decisions.crisis_response, f"{sign.value}: crisis_response is empty - HARD FAIL"
            assert decisions.advice_for_major_choices, f"{sign.value}: advice_for_major_choices is empty - HARD FAIL"

    def test_profiles_have_reasonable_content_length(self):
        """HARD CHECK: Text fields must have reasonable length (not just placeholders)."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value}: JSON file missing - HARD FAIL"

            # Summary must be substantial (at least 100 chars)
            assert len(profile.summary) >= 100, \
                f"{sign.value}: summary too short ({len(profile.summary)} chars) - HARD FAIL"

            # Life lesson must be meaningful
            assert len(profile.life_lesson) >= 50, \
                f"{sign.value}: life_lesson too short ({len(profile.life_lesson)} chars) - HARD FAIL"

            # Evolutionary goal must be meaningful
            assert len(profile.evolutionary_goal) >= 50, \
                f"{sign.value}: evolutionary_goal too short ({len(profile.evolutionary_goal)} chars) - HARD FAIL"

            # Mythology must tell a story
            assert len(profile.mythology) >= 100, \
                f"{sign.value}: mythology too short ({len(profile.mythology)} chars) - HARD FAIL"

    def test_profiles_have_no_placeholder_text(self):
        """HARD CHECK: Profiles must not contain placeholder text."""
        placeholder_patterns = ["TBD", "TODO", "FIXME", "XXX", "[PLACEHOLDER]", "LOREM IPSUM"]

        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value}: JSON file missing - HARD FAIL"

            # Convert entire profile to JSON string for searching
            profile_json = profile.model_dump_json().upper()

            for pattern in placeholder_patterns:
                assert pattern not in profile_json, \
                    f"{sign.value}: contains placeholder text '{pattern}' - HARD FAIL"

    def test_element_and_modality_combinations_are_valid(self):
        """HARD CHECK: Element/modality combinations must follow astrological rules."""
        # Each element should have exactly one of each modality across the zodiac
        element_modality_count = {
            Element.FIRE: {Modality.CARDINAL: 0, Modality.FIXED: 0, Modality.MUTABLE: 0},
            Element.EARTH: {Modality.CARDINAL: 0, Modality.FIXED: 0, Modality.MUTABLE: 0},
            Element.AIR: {Modality.CARDINAL: 0, Modality.FIXED: 0, Modality.MUTABLE: 0},
            Element.WATER: {Modality.CARDINAL: 0, Modality.FIXED: 0, Modality.MUTABLE: 0},
        }

        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None, f"{sign.value}: JSON file missing - HARD FAIL"

            element_modality_count[profile.element][profile.modality] += 1

        # Check that we have exactly one sign for each element/modality combination (12 total)
        for element, modalities in element_modality_count.items():
            for modality, count in modalities.items():
                assert count == 1, \
                    f"Element {element.value} + Modality {modality.value}: " \
                    f"found {count} signs, expected exactly 1 - HARD FAIL"


class TestComputeBirthChart:
    """Tests for compute_birth_chart function."""

    def test_approximate_chart_no_birth_time(self):
        """Test V1 approximate chart with just birth date."""
        chart_data, exact = compute_birth_chart("1990-06-15")

        # Should be approximate chart
        assert exact is False

        # Chart data should be a dict
        assert isinstance(chart_data, dict)

        # Should have correct structure
        assert chart_data["chart_type"] == "natal"
        assert chart_data["datetime_utc"] == "1990-06-15 12:00"
        assert chart_data["location_lat"] == 0.0
        assert chart_data["location_lon"] == 0.0

        # Should have planets, houses, aspects, angles, distributions
        assert "planets" in chart_data
        assert "houses" in chart_data
        assert "aspects" in chart_data
        assert "angles" in chart_data
        assert "distributions" in chart_data

        # Planets list should have 11 planets (sun through pluto)
        assert len(chart_data["planets"]) == 11

        # Houses should be 12
        assert len(chart_data["houses"]) == 12

        # Verify planet structure
        sun = chart_data["planets"][0]
        assert sun["name"] == "sun"
        assert "sign" in sun
        assert "degree_in_sign" in sun
        assert "house" in sun
        assert "retrograde" in sun

    def test_exact_chart_with_full_info(self):
        """Test V2 exact chart with full birth information."""
        chart_data, exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",  # TODO: timezone conversion not yet implemented
            birth_lat=40.7128,
            birth_lon=-74.0060
        )

        # Should be exact chart
        assert exact is True

        # Chart data should be a dict
        assert isinstance(chart_data, dict)

        # Should use provided coordinates
        assert chart_data["location_lat"] == 40.7128
        assert chart_data["location_lon"] == -74.0060

        # Should use provided time (in UTC for now, until timezone conversion implemented)
        assert chart_data["datetime_utc"] == "1990-06-15 14:30"

        # Should have all chart components
        assert "planets" in chart_data
        assert "houses" in chart_data
        assert "aspects" in chart_data
        assert "angles" in chart_data
        assert "distributions" in chart_data

    def test_partial_info_is_approximate(self):
        """Test that missing any field results in approximate chart."""
        # Missing time
        chart_data, exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert exact is False

        # Missing timezone
        chart_data, exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        assert exact is False

        # Missing coordinates
        chart_data, exact = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York"
        )
        assert exact is False

    def test_chart_has_valid_distributions(self):
        """Test that chart contains valid element/modality distributions."""
        chart_data, _ = compute_birth_chart("1990-06-15")

        distributions = chart_data["distributions"]

        # Should have elements
        assert "elements" in distributions
        elements = distributions["elements"]
        assert "fire" in elements
        assert "earth" in elements
        assert "air" in elements
        assert "water" in elements

        # Should have modalities
        assert "modalities" in distributions
        modalities = distributions["modalities"]
        assert "cardinal" in modalities
        assert "fixed" in modalities
        assert "mutable" in modalities

        # Should have quadrants
        assert "quadrants" in distributions
        quadrants = distributions["quadrants"]
        assert "first" in quadrants
        assert "second" in quadrants
        assert "third" in quadrants
        assert "fourth" in quadrants

        # Should have hemispheres
        assert "hemispheres" in distributions
        hemispheres = distributions["hemispheres"]
        assert "northern" in hemispheres
        assert "southern" in hemispheres
        assert "eastern" in hemispheres
        assert "western" in hemispheres

        # Sum of elements should equal 11 (all planets)
        total_elements = sum([
            elements["fire"],
            elements["earth"],
            elements["air"],
            elements["water"]
        ])
        assert total_elements == 11

    def test_chart_has_four_angles(self):
        """Test that chart contains all four angles."""
        chart_data, _ = compute_birth_chart("1990-06-15")

        angles = chart_data["angles"]

        # Should have all four angles
        assert "ascendant" in angles
        assert "imum_coeli" in angles
        assert "descendant" in angles
        assert "midheaven" in angles

        # Each angle should have sign and degree
        for angle_name in ["ascendant", "imum_coeli", "descendant", "midheaven"]:
            angle = angles[angle_name]
            assert "sign" in angle
            assert "degree_in_sign" in angle
            assert "absolute_degree" in angle
            assert "position_dms" in angle

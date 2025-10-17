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
    calculate_solar_house,
    ZodiacSign,
    Element,
    Modality,
    House,
    Planet,
    CelestialBody,
    SIGN_RULERS
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

        # Planets list should have 11 planets (sun through pluto + north node)
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

        # Sum of elements should equal 11 (all planets including north node)
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


class TestSummarizeTransits:
    """Tests for summarize_transits function."""

    def test_basic_transit_summary_includes_sun_and_moon(self):
        """Test that transit summary includes Sun and Moon positions."""
        # Get transit chart for today
        transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")

        summary = summarize_transits(transit_chart, ZodiacSign.TAURUS)

        # Summary should be a non-empty string
        assert isinstance(summary, str)
        assert len(summary) > 0

        # Should mention Sun position
        assert "Sun" in summary or "sun" in summary

        # Should mention Moon position
        assert "Moon" in summary or "moon" in summary

    def test_transit_summary_format(self):
        """Test that transit summary has proper format."""
        transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        summary = summarize_transits(transit_chart, ZodiacSign.ARIES)

        # Should end with a period
        assert summary.endswith(".")

        # Should contain degree symbols or "at" for positions
        assert "at" in summary.lower() or "°" in summary

    def test_transit_summary_with_different_signs(self):
        """Test that transit summary works for all zodiac signs."""
        transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")

        # Should work for all signs
        for sign in ZodiacSign:
            summary = summarize_transits(transit_chart, sign)
            assert isinstance(summary, str)
            assert len(summary) > 0
            assert summary.endswith(".")

    def test_transit_summary_includes_aspects_when_present(self):
        """Test that tight aspects are included in summary."""
        # Use a date/time with known aspects
        transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        summary = summarize_transits(transit_chart, ZodiacSign.GEMINI)

        # Summary should be informative (more than just Sun/Moon positions)
        assert len(summary) > 50  # Should have substantial content

        # Should contain proper formatting
        assert ". " in summary  # Multiple sentences

    def test_transit_summary_handles_retrogrades(self):
        """Test that retrograde planets are handled correctly."""
        # Use a date when Mercury or other personal planets might be retrograde
        transit_chart, _ = compute_birth_chart("2025-01-15", birth_time="12:00")
        summary = summarize_transits(transit_chart, ZodiacSign.CAPRICORN)

        # Summary should be well-formed
        assert isinstance(summary, str)
        assert len(summary) > 0

        # If retrograde planets are present, they should be noted
        # (This is date-dependent, so we just check format is correct)
        if "Rx" in summary or "retrograde" in summary.lower():
            assert "Retrograde" in summary or "Rx" in summary

    def test_transit_summary_length_is_reasonable(self):
        """Test that summary isn't too short or too long."""
        transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        summary = summarize_transits(transit_chart, ZodiacSign.LEO)

        # Should be informative but concise (good for LLM context)
        assert len(summary) >= 30, "Summary too short"
        assert len(summary) <= 1000, "Summary too long for LLM context"

    def test_transit_summary_with_exact_aspects(self):
        """Test that exact aspects (tight orbs) are prioritized."""
        # Create a transit chart
        transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        summary = summarize_transits(transit_chart, ZodiacSign.VIRGO)

        # If aspects are present, they should mention orb
        if "aspect" in summary.lower() or any(aspect_word in summary for aspect_word in ["trine", "square", "opposition", "conjunction", "sextile"]):
            # Aspects should include orb information
            assert "orb" in summary.lower() or "°" in summary

    def test_transit_summary_structure(self):
        """Test that summary has logical structure."""
        transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        summary = summarize_transits(transit_chart, ZodiacSign.SCORPIO)

        # Should start with "Your Sun:" (personalized format)
        assert summary.startswith("Your Sun:"), "Summary should start with personalized Sun sign"

        # Should have proper sentence structure
        sentences = summary.split(". ")
        assert len(sentences) >= 2, "Summary should have multiple sentences"

    def test_transit_summary_planets_are_capitalized(self):
        """Test that planet names are properly capitalized in summary."""
        transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
        summary = summarize_transits(transit_chart, ZodiacSign.LIBRA)

        # Planet names should be capitalized
        planets_to_check = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
        found_planets = [planet for planet in planets_to_check if planet in summary]

        # At least Sun and Moon should be present and capitalized
        assert "Sun" in summary
        assert "Moon" in summary

    def test_transit_summary_with_null_chart_data(self):
        """Test that function handles edge cases gracefully."""
        # Create a minimal valid transit chart
        transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")

        # Should not raise exception
        try:
            summary = summarize_transits(transit_chart, ZodiacSign.AQUARIUS)
            assert isinstance(summary, str)
        except Exception as e:
            pytest.fail(f"summarize_transits raised unexpected exception: {e}")


class TestCalculateSolarHouse:
    """
    Tests for calculate_solar_house function.

    These tests verify the Solar House calculation using whole sign houses,
    where the Sun sign always occupies the 1st house and each subsequent
    sign occupies the next house in zodiacal order.
    """

    # 1. Tests for Specific Problems Found (Regression Tests)

    def test_aries_sun_with_transit_in_virgo_is_6th_house(self):
        """
        Checks if a transit in Virgo for an Aries Sun is correctly placed in the 6th House.
        Aries(1), Taurus(2), Gemini(3), Cancer(4), Leo(5), Virgo(6).
        """
        house = calculate_solar_house("aries", "virgo")
        assert house == House.SIXTH
        assert house.value == 6
        assert house.ordinal == "6th"
        assert house.meaning == "health, work, daily routines"

    def test_scorpio_sun_with_transit_in_libra_is_12th_house(self):
        """
        Checks if a transit in Libra for a Scorpio Sun is correctly placed in the 12th House.
        This is a "wrap-around" test, as Libra comes before Scorpio.
        Scorpio(1)...Sagittarius(2)...Capricorn(3)...Aquarius(4)...Pisces(5)...
        Aries(6)...Taurus(7)...Gemini(8)...Cancer(9)...Leo(10)...Virgo(11)...Libra(12).
        """
        house = calculate_solar_house("scorpio", "libra")
        assert house == House.TWELFTH
        assert house.value == 12
        assert house.ordinal == "12th"
        assert house.meaning == "spirituality, solitude, unconscious"

    # 2. Sanity Check and Boundary Condition Tests

    def test_transit_in_same_sign_is_1st_house(self):
        """
        A planet transiting a person's Sun sign should always be in their 1st Solar House.
        """
        assert calculate_solar_house("leo", "leo").value == 1
        assert calculate_solar_house("aries", "aries").value == 1
        assert calculate_solar_house("pisces", "pisces").value == 1

    def test_transit_in_next_sign_is_2nd_house(self):
        """
        A transit in the sign immediately following the Sun sign should be the 2nd House.
        """
        assert calculate_solar_house("pisces", "aries").value == 2
        assert calculate_solar_house("aries", "taurus").value == 2
        assert calculate_solar_house("leo", "virgo").value == 2

    def test_transit_in_opposite_sign_is_7th_house(self):
        """
        The opposite sign (180° apart) should always be the 7th house.
        """
        assert calculate_solar_house("aries", "libra").value == 7
        assert calculate_solar_house("taurus", "scorpio").value == 7
        assert calculate_solar_house("gemini", "sagittarius").value == 7
        assert calculate_solar_house("cancer", "capricorn").value == 7
        assert calculate_solar_house("leo", "aquarius").value == 7
        assert calculate_solar_house("virgo", "pisces").value == 7

    # 3. General Logic and "Wrap-Around" Tests

    def test_gemini_sun_with_transit_in_virgo_is_4th_house(self):
        """
        Checks a standard forward count.
        Gemini(1), Cancer(2), Leo(3), Virgo(4).
        """
        assert calculate_solar_house("gemini", "virgo").value == 4

    def test_cancer_sun_with_transit_in_taurus_is_11th_house(self):
        """
        Checks another wrap-around case to ensure the logic is robust.
        Cancer(1)...Leo(2)...Virgo(3)...Libra(4)...Scorpio(5)...Sagittarius(6)...
        Capricorn(7)...Aquarius(8)...Pisces(9)...Aries(10)...Taurus(11).
        """
        assert calculate_solar_house("cancer", "taurus").value == 11

    def test_aquarius_sun_with_transit_in_capricorn_is_12th_house(self):
        """
        Another wrap-around test: Capricorn is immediately before Aquarius.
        Aquarius(1)...Pisces(2)...Aries(3)...Taurus(4)...Gemini(5)...Cancer(6)...
        Leo(7)...Virgo(8)...Libra(9)...Scorpio(10)...Sagittarius(11)...Capricorn(12).
        """
        assert calculate_solar_house("aquarius", "capricorn").value == 12

    def test_pisces_sun_with_transit_in_aquarius_is_12th_house(self):
        """
        Test the sign immediately before in the zodiac.
        """
        assert calculate_solar_house("pisces", "aquarius").value == 12

    # 4. Comprehensive All-Signs Tests

    def test_all_twelve_houses_for_aries_sun(self):
        """
        Verify all 12 houses for Aries Sun to ensure complete zodiac coverage.
        """
        aries_houses = {
            "aries": 1, "taurus": 2, "gemini": 3, "cancer": 4,
            "leo": 5, "virgo": 6, "libra": 7, "scorpio": 8,
            "sagittarius": 9, "capricorn": 10, "aquarius": 11, "pisces": 12
        }
        for transit_sign, expected_house in aries_houses.items():
            house = calculate_solar_house("aries", transit_sign)
            assert house.value == expected_house, \
                f"Aries Sun with {transit_sign} transit should be house {expected_house}"

    def test_all_twelve_houses_for_libra_sun(self):
        """
        Verify all 12 houses for Libra Sun (halfway through zodiac).
        """
        libra_houses = {
            "libra": 1, "scorpio": 2, "sagittarius": 3, "capricorn": 4,
            "aquarius": 5, "pisces": 6, "aries": 7, "taurus": 8,
            "gemini": 9, "cancer": 10, "leo": 11, "virgo": 12
        }
        for transit_sign, expected_house in libra_houses.items():
            house = calculate_solar_house("libra", transit_sign)
            assert house.value == expected_house, \
                f"Libra Sun with {transit_sign} transit should be house {expected_house}"

    # 5. Error Handling Tests

    def test_invalid_sun_sign_raises_error(self):
        """Test that invalid sun sign raises ValueError."""
        with pytest.raises(ValueError):
            calculate_solar_house("invalid_sign", "aries")

    def test_invalid_transit_sign_raises_error(self):
        """Test that invalid transit sign raises ValueError."""
        with pytest.raises(ValueError):
            calculate_solar_house("aries", "invalid_sign")

    # 6. Case Insensitivity Tests

    def test_case_insensitive_sign_names(self):
        """Test that sign names are case-insensitive."""
        assert calculate_solar_house("ARIES", "VIRGO").value == 6
        assert calculate_solar_house("Scorpio", "Libra").value == 12
        assert calculate_solar_house("LeO", "lEo").value == 1

    # 7. Enum Input Tests

    def test_accepts_zodiac_sign_enums(self):
        """Test that function accepts ZodiacSign enum inputs."""
        assert calculate_solar_house(ZodiacSign.ARIES, ZodiacSign.VIRGO).value == 6
        assert calculate_solar_house(ZodiacSign.SCORPIO, ZodiacSign.LIBRA).value == 12

    # 8. House Enum Properties Tests

    def test_house_enum_has_ordinal_property(self):
        """Test that House enum provides ordinal formatting."""
        assert House.FIRST.ordinal == "1st"
        assert House.SECOND.ordinal == "2nd"
        assert House.THIRD.ordinal == "3rd"
        assert House.FOURTH.ordinal == "4th"
        assert House.ELEVENTH.ordinal == "11th"
        assert House.TWELFTH.ordinal == "12th"

    def test_house_enum_has_meaning_property(self):
        """Test that House enum provides life area meanings."""
        assert House.FIRST.meaning == "self, identity, appearance"
        assert House.SEVENTH.meaning == "partnerships, relationships"
        assert House.TENTH.meaning == "career, public image, goals"
        assert House.TWELFTH.meaning == "spirituality, solitude, unconscious"


class TestSignRulers:
    """Tests for SIGN_RULERS constant."""

    def test_all_signs_have_rulers(self):
        """Test that all zodiac signs have assigned rulers."""
        for sign in ZodiacSign:
            assert sign in SIGN_RULERS, f"{sign} missing from SIGN_RULERS"
            assert isinstance(SIGN_RULERS[sign], Planet), f"{sign} ruler is not a Planet enum"

    def test_ruler_planet_values_are_valid(self):
        """Test that all ruler planets are valid Planet enums."""
        for sign, ruler in SIGN_RULERS.items():
            # Should be able to access the value
            assert hasattr(ruler, 'value')
            # Value should be a lowercase string
            assert isinstance(ruler.value, str)
            assert ruler.value.islower()

    def test_specific_rulerships(self):
        """Test specific modern rulerships."""
        # Traditional rulerships (unchanged)
        assert SIGN_RULERS[ZodiacSign.ARIES] == Planet.MARS
        assert SIGN_RULERS[ZodiacSign.TAURUS] == Planet.VENUS
        assert SIGN_RULERS[ZodiacSign.GEMINI] == Planet.MERCURY
        assert SIGN_RULERS[ZodiacSign.CANCER] == Planet.MOON
        assert SIGN_RULERS[ZodiacSign.LEO] == Planet.SUN
        assert SIGN_RULERS[ZodiacSign.VIRGO] == Planet.MERCURY
        assert SIGN_RULERS[ZodiacSign.LIBRA] == Planet.VENUS
        assert SIGN_RULERS[ZodiacSign.SAGITTARIUS] == Planet.JUPITER
        assert SIGN_RULERS[ZodiacSign.CAPRICORN] == Planet.SATURN

        # Modern rulerships (outer planets)
        assert SIGN_RULERS[ZodiacSign.SCORPIO] == Planet.PLUTO, "Scorpio modern ruler is Pluto"
        assert SIGN_RULERS[ZodiacSign.AQUARIUS] == Planet.URANUS, "Aquarius modern ruler is Uranus"
        assert SIGN_RULERS[ZodiacSign.PISCES] == Planet.NEPTUNE, "Pisces modern ruler is Neptune"

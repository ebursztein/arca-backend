"""
Comprehensive tests for sun sign profiles and related functionality.
"""
import pytest
from astro import (
    get_sun_sign,
    get_sun_sign_profile,
    ZodiacSign,
    Element,
    Modality,
    Planet
)


class TestSunSignProfiles:
    """Test sun sign profile loading and validation."""

    def test_all_signs_load_successfully(self):
        """Test that all 12 sun sign profiles can be loaded."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile is not None
            assert profile.sign == sign
            print(f"✓ {sign.value.title()} profile loads")

    def test_profile_has_correct_element(self):
        """Test element assignments for all signs."""
        element_assignments = {
            ZodiacSign.ARIES: Element.FIRE,
            ZodiacSign.TAURUS: Element.EARTH,
            ZodiacSign.GEMINI: Element.AIR,
            ZodiacSign.CANCER: Element.WATER,
            ZodiacSign.LEO: Element.FIRE,
            ZodiacSign.VIRGO: Element.EARTH,
            ZodiacSign.LIBRA: Element.AIR,
            ZodiacSign.SCORPIO: Element.WATER,
            ZodiacSign.SAGITTARIUS: Element.FIRE,
            ZodiacSign.CAPRICORN: Element.EARTH,
            ZodiacSign.AQUARIUS: Element.AIR,
            ZodiacSign.PISCES: Element.WATER
        }

        for sign, expected_element in element_assignments.items():
            profile = get_sun_sign_profile(sign)
            assert profile.element == expected_element
            print(f"✓ {sign.value.title()}: {expected_element.value}")

    def test_profile_has_correct_modality(self):
        """Test modality assignments for all signs."""
        modality_assignments = {
            ZodiacSign.ARIES: Modality.CARDINAL,
            ZodiacSign.TAURUS: Modality.FIXED,
            ZodiacSign.GEMINI: Modality.MUTABLE,
            ZodiacSign.CANCER: Modality.CARDINAL,
            ZodiacSign.LEO: Modality.FIXED,
            ZodiacSign.VIRGO: Modality.MUTABLE,
            ZodiacSign.LIBRA: Modality.CARDINAL,
            ZodiacSign.SCORPIO: Modality.FIXED,
            ZodiacSign.SAGITTARIUS: Modality.MUTABLE,
            ZodiacSign.CAPRICORN: Modality.CARDINAL,
            ZodiacSign.AQUARIUS: Modality.FIXED,
            ZodiacSign.PISCES: Modality.MUTABLE
        }

        for sign, expected_modality in modality_assignments.items():
            profile = get_sun_sign_profile(sign)
            assert profile.modality == expected_modality
            print(f"✓ {sign.value.title()}: {expected_modality.value}")

    def test_ruling_planets(self):
        """Test ruling planet assignments."""
        ruling_planets = {
            ZodiacSign.ARIES: "Mars",
            ZodiacSign.TAURUS: "Venus",
            ZodiacSign.GEMINI: "Mercury",
            ZodiacSign.CANCER: "Moon",
            ZodiacSign.LEO: "Sun",
            ZodiacSign.VIRGO: "Mercury",
            ZodiacSign.LIBRA: "Venus",
            ZodiacSign.SCORPIO: "Pluto",  # Modern ruler
            ZodiacSign.SAGITTARIUS: "Jupiter",
            ZodiacSign.CAPRICORN: "Saturn",
            ZodiacSign.AQUARIUS: "Uranus",  # Modern ruler
            ZodiacSign.PISCES: "Neptune"  # Modern ruler
        }

        for sign, expected_ruler in ruling_planets.items():
            profile = get_sun_sign_profile(sign)
            assert profile.ruling_planet == expected_ruler
            print(f"✓ {sign.value.title()}: Ruled by {expected_ruler}")

    def test_profile_summary_exists(self):
        """Test that all profiles have non-empty summaries."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile.summary
            assert len(profile.summary) > 100
            assert "TBD" not in profile.summary
            assert "TODO" not in profile.summary
            print(f"✓ {sign.value.title()}: Summary length {len(profile.summary)}")

    def test_profile_strengths_and_challenges(self):
        """Test that all profiles have strengths and challenges."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile.strengths
            assert len(profile.strengths) >= 3
            assert profile.challenges
            assert len(profile.challenges) >= 3
            print(f"✓ {sign.value.title()}: {len(profile.strengths)} strengths, {len(profile.challenges)} challenges")

    def test_profile_life_domains_complete(self):
        """Test that all 8 life domains are present and complete."""
        required_domains = [
            'love_and_relationships',
            'family_and_friendships',
            'career_and_ambition',
            'personal_growth_and_learning',
            'finance_and_resources',
            'life_purpose_and_meaning',
            'home_and_environment',
            'decision_making_and_action'
        ]

        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            domain_profiles = profile.domain_profiles

            for domain in required_domains:
                assert hasattr(domain_profiles, domain)
                domain_data = getattr(domain_profiles, domain)
                assert domain_data is not None
                # Check that each domain has content
                assert len(str(domain_data.model_dump())) > 50

            print(f"✓ {sign.value.title()}: All 8 domains present")


class TestSunSignCompatibility:
    """Test compatibility data in sun sign profiles."""

    def test_compatibility_fields_exist(self):
        """Test that compatibility fields exist for all signs."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            assert profile.most_compatible_signs
            assert len(profile.most_compatible_signs) >= 2
            assert profile.challenging_signs
            assert len(profile.challenging_signs) >= 2
            assert profile.growth_oriented_signs
            assert len(profile.growth_oriented_signs) >= 2
            print(f"✓ {sign.value.title()}: Compatibility data complete")

    def test_compatibility_signs_are_valid(self):
        """Test that compatibility lists contain valid sign names."""
        valid_signs = {sign.value for sign in ZodiacSign}

        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)

            for compatible_sign in profile.most_compatible_signs:
                assert compatible_sign in valid_signs

            for challenging_sign in profile.challenging_signs:
                assert challenging_sign in valid_signs

            for growth_sign in profile.growth_oriented_signs:
                assert growth_sign in valid_signs

            print(f"✓ {sign.value.title()}: All compatibility signs valid")


class TestSunSignPlanetaryDignities:
    """Test planetary dignities in sun sign profiles."""

    def test_planetary_dignities_structure(self):
        """Test that planetary dignities are properly structured."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            dignities = profile.planetary_dignities

            assert dignities.exalted
            assert dignities.detriment
            assert dignities.fall

            # All should be valid planet names
            valid_planets = {"Sun", "Moon", "Mercury", "Venus", "Mars",
                           "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}

            for planet in [dignities.exalted, dignities.detriment, dignities.fall]:
                assert planet in valid_planets

            print(f"✓ {sign.value.title()}: Dignities valid")


class TestSunSignCorrespondences:
    """Test correspondences (colors, crystals, etc.) in profiles."""

    def test_correspondences_exist(self):
        """Test that correspondences fields are populated."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            corr = profile.correspondences

            assert corr.colors
            assert len(corr.colors) >= 1

            assert corr.crystals
            assert len(corr.crystals) >= 2

            assert corr.body_parts
            assert len(corr.body_parts) >= 1

            assert corr.tarot_card

            print(f"✓ {sign.value.title()}: Correspondences complete")


class TestSunSignCalculation:
    """Test sun sign calculation from birth dates."""

    def test_sun_sign_boundary_dates(self):
        """Test sun sign calculations at sign boundaries."""
        test_cases = [
            ("2024-03-20", ZodiacSign.PISCES),  # Day before Aries
            ("2024-03-21", ZodiacSign.ARIES),   # First day of Aries
            ("2024-04-19", ZodiacSign.ARIES),   # Last day of Aries
            ("2024-04-20", ZodiacSign.TAURUS),  # First day of Taurus
            ("2024-12-21", ZodiacSign.SAGITTARIUS),  # Last day of Sag
            ("2024-12-22", ZodiacSign.CAPRICORN),    # First day of Cap
        ]

        for birth_date, expected_sign in test_cases:
            calculated_sign = get_sun_sign(birth_date)
            assert calculated_sign == expected_sign
            print(f"✓ {birth_date} → {expected_sign.value}")

    def test_all_months_covered(self):
        """Test that get_sun_sign works for all months."""
        test_dates = [
            "2024-01-15",  # Capricorn
            "2024-02-15",  # Aquarius
            "2024-03-15",  # Pisces
            "2024-04-15",  # Aries
            "2024-05-15",  # Taurus
            "2024-06-15",  # Gemini
            "2024-07-15",  # Cancer
            "2024-08-15",  # Leo
            "2024-09-15",  # Virgo
            "2024-10-15",  # Libra
            "2024-11-15",  # Scorpio
            "2024-12-15",  # Sagittarius
        ]

        for date in test_dates:
            sign = get_sun_sign(date)
            assert sign in ZodiacSign
            print(f"✓ {date} → {sign.value}")


class TestSunSignDomainDetails:
    """Test specific domain data in profiles."""

    def test_love_domain_has_required_fields(self):
        """Test that love domain has all required fields."""
        profile = get_sun_sign_profile(ZodiacSign.GEMINI)
        love = profile.domain_profiles.love_and_relationships

        assert love.style
        assert len(love.style) > 20

        assert love.needs
        assert len(love.needs) > 20

        assert love.challenges
        assert len(love.challenges) > 20

        assert love.growth_path
        assert len(love.growth_path) > 20

        print("✓ Love domain complete")

    def test_career_domain_has_required_fields(self):
        """Test that career domain has all required fields."""
        profile = get_sun_sign_profile(ZodiacSign.CAPRICORN)
        career = profile.domain_profiles.career_and_ambition

        assert career.natural_talents
        assert len(career.natural_talents) > 20

        assert career.career_paths
        assert len(career.career_paths) > 20

        assert career.work_style
        assert len(career.work_style) > 20

        assert career.challenges
        assert len(career.challenges) > 20

        print("✓ Career domain complete")

    def test_growth_domain_has_required_fields(self):
        """Test that growth domain has all required fields."""
        profile = get_sun_sign_profile(ZodiacSign.SCORPIO)
        growth = profile.domain_profiles.personal_growth_and_learning

        assert growth.learning_style
        assert len(growth.learning_style) > 20

        assert growth.growth_areas
        assert len(growth.growth_areas) > 20

        assert growth.spiritual_path
        assert len(growth.spiritual_path) > 20

        assert growth.shadow_work
        assert len(growth.shadow_work) > 20

        print("✓ Growth domain complete")


class TestSunSignHealthData:
    """Test health tendencies in profiles."""

    def test_health_tendencies_exist(self):
        """Test that health tendencies are present."""
        for sign in ZodiacSign:
            profile = get_sun_sign_profile(sign)
            health = profile.health_tendencies

            assert health.vulnerable_areas
            assert len(health.vulnerable_areas) >= 1

            assert health.wellness_practices
            assert len(health.wellness_practices) >= 2

            print(f"✓ {sign.value.title()}: Health data complete")


class TestSunSignEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_date_format(self):
        """Test that invalid date format raises error."""
        with pytest.raises(ValueError):
            get_sun_sign("invalid-date")

    def test_future_dates_work(self):
        """Test that future dates work correctly."""
        future_sign = get_sun_sign("2030-07-04")
        assert future_sign == ZodiacSign.CANCER
        print("✓ Future dates work")

    def test_past_dates_work(self):
        """Test that past dates work correctly."""
        past_sign = get_sun_sign("1900-01-01")
        assert past_sign == ZodiacSign.CAPRICORN
        print("✓ Past dates work")

    def test_leap_year_dates(self):
        """Test leap year dates."""
        leap_year_sign = get_sun_sign("2024-02-29")
        assert leap_year_sign == ZodiacSign.PISCES
        print("✓ Leap year dates work")

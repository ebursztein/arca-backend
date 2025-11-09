"""
Integration tests for LLM module - verify daily horoscope generation
"""
import pytest
from datetime import datetime
from astro import compute_birth_chart, get_sun_sign, get_sun_sign_profile, format_transit_summary_for_ui
from models import UserProfile, create_empty_memory
from llm import generate_daily_horoscope
import os


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile for testing."""
    birth_date = "1987-06-02"
    natal_chart, is_exact = compute_birth_chart(birth_date)
    sun_sign = get_sun_sign(birth_date)

    return UserProfile(
        user_id="test_user_001",
        name="Test User",
        email="test@example.com",
        birth_date=birth_date,
        birth_time=None,
        birth_timezone=None,
        birth_lat=None,
        birth_lon=None,
        sun_sign=sun_sign.value,
        natal_chart=natal_chart,
        exact_chart=is_exact,
        created_at=datetime.now().isoformat(),
        last_active=datetime.now().isoformat()
    )


@pytest.fixture
def transit_data():
    """Generate transit data for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    transit_chart, _ = compute_birth_chart(today, birth_time="12:00")
    return transit_chart


class TestDailyHoroscopeGeneration:
    """Test daily horoscope generation pipeline."""

    @pytest.mark.xfail(reason="KNOWN ISSUE: quality_factor validation error - astrometer computation being reworked")
    @pytest.mark.skipif(
        not os.environ.get("GEMINI_API_KEY") or not os.environ.get("POSTHOG_API_KEY"),
        reason="Requires GEMINI_API_KEY and POSTHOG_API_KEY environment variables"
    )
    def test_generate_daily_horoscope_returns_all_fields(self, sample_user_profile, transit_data):
        """Verify that generate_daily_horoscope returns all expected fields."""
        today = datetime.now().strftime("%Y-%m-%d")
        sun_sign = get_sun_sign(sample_user_profile.birth_date)
        sun_sign_profile = get_sun_sign_profile(sun_sign)

        transit_summary = format_transit_summary_for_ui(
            sample_user_profile.natal_chart,
            transit_data,
            max_aspects=5
        )

        memory = create_empty_memory(sample_user_profile.user_id)

        horoscope = generate_daily_horoscope(
            date=today,
            user_profile=sample_user_profile,
            sun_sign_profile=sun_sign_profile,
            transit_summary=transit_summary,
            memory=memory,
            model_name="gemini-2.5-flash-lite"
        )

        # Check core LLM fields
        assert horoscope.technical_analysis
        assert len(horoscope.technical_analysis) > 50

        assert horoscope.daily_theme_headline
        assert len(horoscope.daily_theme_headline.split()) <= 15

        assert horoscope.daily_overview
        assert len(horoscope.daily_overview) > 50

        assert horoscope.actionable_advice
        assert horoscope.actionable_advice.do
        assert horoscope.actionable_advice.dont
        assert horoscope.actionable_advice.reflect_on

        assert horoscope.look_ahead_preview
        assert horoscope.energy_rhythm
        assert horoscope.relationship_weather
        assert horoscope.collective_energy

        # Check moon interpretation is nested correctly
        assert horoscope.moon_detail
        assert horoscope.moon_detail.interpretation
        assert len(horoscope.moon_detail.interpretation) > 50

        # Check astrometers
        assert horoscope.astrometers
        assert len(horoscope.astrometers.groups) == 5

        # Verify all groups have interpretations
        for group in horoscope.astrometers.groups:
            assert group.interpretation
            assert len(group.interpretation) > 50

            # Verify all meters in group have interpretations
            for meter in group.meters:
                assert meter.interpretation
                assert len(meter.interpretation) > 20

        # Check metadata
        assert horoscope.date == today
        assert horoscope.sun_sign == sample_user_profile.sun_sign
        assert horoscope.model_used
        assert horoscope.generation_time_ms > 0

        print(f"✓ All fields present and valid")
        print(f"✓ Generated in {horoscope.generation_time_ms}ms")
        print(f"✓ Output tokens: {horoscope.usage.get('candidates_token_count', 0)}")


class TestMoonDetailIntegration:
    """Test that moon_detail.interpretation is populated correctly."""

    def test_moon_detail_has_interpretation_field(self):
        """Verify MoonTransitDetail has interpretation field."""
        from moon import get_moon_transit_detail
        from astro import compute_birth_chart

        # Generate real moon detail
        natal_chart, _ = compute_birth_chart("1987-06-02")
        transit_chart, _ = compute_birth_chart("2025-11-06", birth_time="12:00")

        moon_detail = get_moon_transit_detail(
            natal_chart=natal_chart,
            transit_chart=transit_chart,
            current_datetime="2025-11-06T12:00:00"
        )

        # Should have default empty interpretation
        assert hasattr(moon_detail, 'interpretation')
        assert moon_detail.interpretation == ""  # Default value

        # Should be able to set it
        moon_detail.interpretation = "Test interpretation"
        assert moon_detail.interpretation == "Test interpretation"

        print("✓ MoonTransitDetail.interpretation field exists and works")

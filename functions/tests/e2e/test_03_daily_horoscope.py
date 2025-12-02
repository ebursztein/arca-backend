"""
E2E Tests for Journey 3: Daily Horoscope & Astrometers.

Tests the ACTUAL Cloud Functions via Firebase emulator:
- get_astrometers: Calculate all 17 meters
- get_daily_horoscope: Generate daily horoscope with LLM

NO MOCKS. Real HTTP calls to emulator. Real Gemini API.

OPTIMIZATION: Uses module-scoped fixtures to cache LLM responses.
One create_user_profile call, one get_astrometers call, multiple assertions.
"""
import pytest
import uuid

from .conftest import call_function


# Meter names for validation
MIND_METERS = ["clarity", "focus", "communication"]
HEART_METERS = ["resilience", "connections", "vulnerability"]
BODY_METERS = ["energy", "drive", "strength"]
INSTINCTS_METERS = ["vision", "flow", "intuition", "creativity"]
GROWTH_METERS = ["momentum", "ambition", "evolution", "circle"]
ALL_METERS = MIND_METERS + HEART_METERS + BODY_METERS + INSTINCTS_METERS + GROWTH_METERS

GROUP_METER_MAP = {
    "mind": MIND_METERS,
    "heart": HEART_METERS,
    "body": BODY_METERS,
    "instincts": INSTINCTS_METERS,
    "growth": GROWTH_METERS,
}


# ============================================================================
# MODULE-SCOPED FIXTURES (LLM calls cached for entire module)
# ============================================================================

@pytest.fixture(scope="module")
def astrometers_user_id():
    """Fixed user ID for astrometers tests (module-scoped)."""
    return "test_user_b"  # Dev account from DEV_ACCOUNT_UIDS


@pytest.fixture(scope="module")
def astrometers_user_profile(astrometers_user_id):
    """Create user profile once for all astrometers tests."""
    call_function("create_user_profile", {
        "user_id": astrometers_user_id,
        "name": "Astro Test User",
        "email": f"{astrometers_user_id}@test.com",
        "birth_date": "1990-06-15",
        "birth_time": "14:30",
        "birth_timezone": "America/New_York",
        "birth_lat": 40.7128,
        "birth_lon": -74.0060,
    })
    return astrometers_user_id


@pytest.fixture(scope="module")
def astrometers_response(astrometers_user_profile):
    """Fetch astrometers once for all tests in this module."""
    return call_function("get_astrometers", {"user_id": astrometers_user_profile})


@pytest.fixture(scope="module")
def horoscope_user_id():
    """Fixed user ID for horoscope tests (module-scoped)."""
    return "test_user_c"  # Dev account from DEV_ACCOUNT_UIDS


@pytest.fixture(scope="module")
def horoscope_user_profile(horoscope_user_id):
    """Create user profile once for all horoscope tests."""
    call_function("create_user_profile", {
        "user_id": horoscope_user_id,
        "name": "Horoscope Test User",
        "email": f"{horoscope_user_id}@test.com",
        "birth_date": "1990-06-15",
    })
    return horoscope_user_id


@pytest.fixture(scope="module")
def horoscope_response(horoscope_user_profile):
    """Fetch horoscope once for all tests in this module."""
    return call_function("get_daily_horoscope", {"user_id": horoscope_user_profile})


# ============================================================================
# ASTROMETERS TESTS (all use cached astrometers_response)
# ============================================================================

class TestGetAstrometers:
    """E2E tests for get_astrometers Cloud Function."""

    @pytest.mark.llm
    def test_has_date(self, astrometers_response):
        """Test response includes date."""
        assert "date" in astrometers_response

    @pytest.mark.llm
    def test_has_all_meters(self, astrometers_response):
        """Test response includes all 17 meters."""
        for meter in ALL_METERS:
            assert meter in astrometers_response, f"Missing meter: {meter}"

    @pytest.mark.llm
    def test_has_overall_intensity(self, astrometers_response):
        """Test response includes overall_intensity."""
        assert "overall_intensity" in astrometers_response
        overall = astrometers_response["overall_intensity"]
        assert "intensity" in overall
        assert 0 <= overall["intensity"] <= 100

    @pytest.mark.llm
    def test_has_overall_harmony(self, astrometers_response):
        """Test response includes overall_harmony."""
        assert "overall_harmony" in astrometers_response
        overall = astrometers_response["overall_harmony"]
        assert "harmony" in overall
        assert 0 <= overall["harmony"] <= 100

    @pytest.mark.llm
    def test_meter_has_required_fields(self, astrometers_response):
        """Test each meter has required fields."""
        for meter_name in ALL_METERS:
            meter = astrometers_response[meter_name]
            assert "intensity" in meter, f"{meter_name} missing intensity"
            assert "harmony" in meter, f"{meter_name} missing harmony"
            assert "unified_score" in meter, f"{meter_name} missing unified_score"
            assert "state_label" in meter, f"{meter_name} missing state_label"

    @pytest.mark.llm
    def test_meter_scores_in_range(self, astrometers_response):
        """Test meter scores are in valid ranges."""
        for meter_name in ALL_METERS:
            meter = astrometers_response[meter_name]
            assert 0 <= meter["intensity"] <= 100, f"{meter_name} intensity out of range"
            assert 0 <= meter["harmony"] <= 100, f"{meter_name} harmony out of range"
            # unified_score is polar-style: -100 to +100 (positive=harmonious, negative=challenging)
            assert -100 <= meter["unified_score"] <= 100, f"{meter_name} unified_score out of range"

    @pytest.mark.llm
    def test_meters_have_correct_groups(self, astrometers_response):
        """Test meters are assigned to correct groups."""
        for group_name, meters in GROUP_METER_MAP.items():
            for meter_name in meters:
                meter = astrometers_response[meter_name]
                assert meter["group"] == group_name, f"{meter_name} should be in {group_name}"

    @pytest.mark.llm
    def test_has_aspect_count(self, astrometers_response):
        """Test response includes aspect_count."""
        assert "aspect_count" in astrometers_response
        assert isinstance(astrometers_response["aspect_count"], int)
        assert astrometers_response["aspect_count"] >= 0

    def test_missing_user_raises_error(self):
        """Test missing user_id raises error."""
        with pytest.raises(Exception):
            call_function("get_astrometers", {})


class TestAstrometersDateVariation:
    """Test that different dates produce different scores (separate LLM call)."""

    @pytest.mark.llm
    def test_different_dates_different_scores(self, astrometers_user_profile):
        """Test different dates produce different scores."""
        result1 = call_function("get_astrometers", {
            "user_id": astrometers_user_profile,
            "date": "2025-01-15",
        })

        result2 = call_function("get_astrometers", {
            "user_id": astrometers_user_profile,
            "date": "2025-06-15",
        })

        # At least some meters should differ for different dates
        differences = 0
        for meter in ALL_METERS:
            if result1[meter]["unified_score"] != result2[meter]["unified_score"]:
                differences += 1

        assert differences > 0, "Expected at least some meters to differ between dates"


# ============================================================================
# HOROSCOPE TESTS (all use cached horoscope_response)
# ============================================================================

class TestGetDailyHoroscope:
    """E2E tests for get_daily_horoscope Cloud Function."""

    @pytest.mark.llm
    def test_has_date(self, horoscope_response):
        """Test horoscope includes date."""
        assert "date" in horoscope_response

    @pytest.mark.llm
    def test_has_sun_sign(self, horoscope_response):
        """Test horoscope includes sun_sign."""
        assert "sun_sign" in horoscope_response

    @pytest.mark.llm
    def test_has_daily_theme_headline(self, horoscope_response):
        """Test horoscope includes daily_theme_headline."""
        assert "daily_theme_headline" in horoscope_response
        assert len(horoscope_response["daily_theme_headline"]) > 0

    @pytest.mark.llm
    def test_has_daily_overview(self, horoscope_response):
        """Test horoscope includes daily_overview."""
        assert "daily_overview" in horoscope_response
        assert len(horoscope_response["daily_overview"]) > 0

    @pytest.mark.llm
    def test_has_actionable_advice(self, horoscope_response):
        """Test horoscope has do/dont/reflect_on advice."""
        assert "actionable_advice" in horoscope_response
        advice = horoscope_response["actionable_advice"]
        assert "do" in advice
        assert "dont" in advice
        assert "reflect_on" in advice

    @pytest.mark.llm
    def test_has_astrometers(self, horoscope_response):
        """Test horoscope includes astrometers data."""
        assert "astrometers" in horoscope_response

    def test_missing_user_raises_error(self):
        """Test missing user raises error."""
        with pytest.raises(Exception):
            call_function("get_daily_horoscope", {
                "user_id": "nonexistent_user_xyz_999",
            })


class TestHoroscopeCaching:
    """Test horoscope caching (separate LLM call needed)."""

    @pytest.mark.skip(reason="Server-side caching not yet implemented - horoscope regenerates each call")
    @pytest.mark.llm
    def test_same_day_returns_cached(self, horoscope_user_profile):
        """Test horoscope is cached (second call returns same result)."""
        result1 = call_function("get_daily_horoscope", {"user_id": horoscope_user_profile})
        result2 = call_function("get_daily_horoscope", {"user_id": horoscope_user_profile})

        # Same date should return same horoscope
        assert result1["daily_theme_headline"] == result2["daily_theme_headline"]

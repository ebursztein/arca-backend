"""
E2E Tests for Journey 1: User Onboarding.

Tests the ACTUAL Cloud Functions via Firebase emulator HTTP calls:
- get_sun_sign_from_date: Calculate sun sign from birth date
- natal_chart: Generate natal chart
- daily_transit: Generate daily transit chart
- user_transit: Generate user-specific transit
- create_user_profile: Create user profile (requires LLM)
- get_user_profile: Retrieve user profile from Firestore
- get_memory: Retrieve user memory

NO MOCKS. Real HTTP calls to emulator. Real Gemini API. Real Firestore.
"""
import pytest

from .conftest import call_function


class TestGetSunSignFromDate:
    """E2E tests for get_sun_sign_from_date Cloud Function."""

    def test_gemini(self):
        """Test sun sign calculation for Gemini."""
        result = call_function("get_sun_sign_from_date", {"birth_date": "1990-06-15"})

        assert result["sun_sign"] == "gemini"
        assert "profile" in result
        assert result["profile"]["element"] == "air"

    def test_leo(self):
        """Test sun sign calculation for Leo."""
        result = call_function("get_sun_sign_from_date", {"birth_date": "1992-08-15"})

        assert result["sun_sign"] == "leo"
        assert result["profile"]["element"] == "fire"

    def test_capricorn(self):
        """Test sun sign calculation for Capricorn."""
        result = call_function("get_sun_sign_from_date", {"birth_date": "1985-01-10"})

        assert result["sun_sign"] == "capricorn"
        assert result["profile"]["element"] == "earth"

    @pytest.mark.parametrize("sign,birth_date", [
        ("aries", "1990-04-10"),
        ("taurus", "1990-05-05"),
        ("gemini", "1990-06-10"),
        ("cancer", "1990-07-10"),
        ("leo", "1990-08-10"),
        ("virgo", "1990-09-10"),
        ("libra", "1990-10-10"),
        ("scorpio", "1990-11-10"),
        ("sagittarius", "1990-12-10"),
        ("capricorn", "1990-01-10"),
        ("aquarius", "1990-02-10"),
        ("pisces", "1990-03-10"),
    ])
    def test_all_signs(self, sign, birth_date):
        """Test sun sign calculation for all 12 signs."""
        result = call_function("get_sun_sign_from_date", {"birth_date": birth_date})

        assert result["sun_sign"] == sign

    def test_missing_date_raises_error(self):
        """Test missing birth_date raises error."""
        with pytest.raises(Exception):
            call_function("get_sun_sign_from_date", {})

    def test_invalid_date_raises_error(self):
        """Test invalid birth_date format raises error."""
        with pytest.raises(Exception):
            call_function("get_sun_sign_from_date", {"birth_date": "not-a-date"})

    def test_profile_has_required_fields(self):
        """Test sun sign profile contains all required fields."""
        result = call_function("get_sun_sign_from_date", {"birth_date": "1990-06-15"})

        profile = result["profile"]
        assert "element" in profile
        assert "modality" in profile
        assert "ruling_planet" in profile
        assert "keywords" in profile
        assert "summary" in profile


class TestNatalChart:
    """E2E tests for natal_chart Cloud Function."""

    def test_basic(self):
        """Test natal chart generation with valid inputs."""
        result = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        assert "planets" in result
        assert "houses" in result
        assert "aspects" in result
        assert "angles" in result
        assert len(result["planets"]) == 12

    def test_missing_params_raises_error(self):
        """Test missing parameters raises error."""
        with pytest.raises(Exception):
            call_function("natal_chart", {"utc_dt": "1990-06-15 14:30"})

    def test_sun_in_gemini(self):
        """Test natal chart for June 15 has Sun in Gemini."""
        result = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        sun = next(p for p in result["planets"] if p["name"] == "sun")
        assert sun["sign"] == "gemini"

    def test_all_planets_present(self):
        """Test natal chart contains all 11 planets."""
        result = call_function("natal_chart", {
            "utc_dt": "1990-06-15 14:30",
            "lat": 40.7128,
            "lon": -74.0060
        })

        planet_names = {p["name"] for p in result["planets"]}
        expected = {"sun", "moon", "mercury", "venus", "mars", "jupiter",
                    "saturn", "uranus", "neptune", "pluto", "north node", "south node"}
        assert planet_names == expected


class TestDailyTransit:
    """E2E tests for daily_transit Cloud Function."""

    def test_default_date(self):
        """Test daily transit with default date (today)."""
        result = call_function("daily_transit", {})

        assert "planets" in result
        assert "aspects" in result
        assert len(result["planets"]) == 12

    def test_specific_date(self):
        """Test daily transit for specific date."""
        result = call_function("daily_transit", {"utc_dt": "2025-01-15 00:00"})

        assert "planets" in result
        assert len(result["planets"]) == 12


class TestUserTransit:
    """E2E tests for user_transit Cloud Function."""

    def test_with_location(self):
        """Test user transit with birth location."""
        result = call_function("user_transit", {
            "birth_lat": 40.7128,
            "birth_lon": -74.0060
        })

        assert "planets" in result
        assert "houses" in result
        assert len(result["planets"]) == 12

    def test_missing_location_raises_error(self):
        """Test missing location raises error."""
        with pytest.raises(Exception):
            call_function("user_transit", {})


class TestCreateUserProfile:
    """
    E2E tests for create_user_profile Cloud Function.
    Requires GEMINI_API_KEY in emulator environment.
    """

    def test_missing_fields_raises_error(self):
        """Test missing required fields raises error."""
        with pytest.raises(Exception):
            call_function("create_user_profile", {"user_id": "test_user"})

    @pytest.mark.llm
    def test_v1_profile(self, test_user_id):
        """Test creating V1 profile (birth date only)."""
        result = call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        assert result["success"] is True
        assert result["user_id"] == test_user_id
        assert result["sun_sign"] == "gemini"
        assert result["exact_chart"] is False
        assert result["mode"] == "v1"

    @pytest.mark.llm
    def test_v2_profile(self, test_user_id):
        """Test creating V2 profile (full birth data)."""
        result = call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User V2",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "birth_timezone": "America/New_York",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
        })

        assert result["success"] is True
        assert result["exact_chart"] is True
        assert result["mode"] == "v2"


class TestGetUserProfile:
    """E2E tests for get_user_profile Cloud Function."""

    def test_unauthenticated_rejected(self):
        """Test get_user_profile rejects unauthenticated requests."""
        with pytest.raises(Exception) as exc_info:
            call_function("get_user_profile", {"user_id": "not_a_dev_account"})

        assert "UNAUTHENTICATED" in str(exc_info.value)

    @pytest.mark.llm
    def test_returns_profile(self, test_user_id):
        """Test get_user_profile returns existing profile."""
        # First create profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Then retrieve it
        result = call_function("get_user_profile", {"user_id": test_user_id})

        assert result["user_id"] == test_user_id
        assert result["sun_sign"] == "gemini"
        assert result["natal_chart"] is not None

    @pytest.mark.llm
    def test_create_user_and_get_natal_chart(self, test_user_id):
        """Test creating test_user_a and retrieving its natal chart."""
        # Create profile for test_user_a
        create_result = call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User A",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-12-10",  # Sagittarius
        })

        assert create_result["success"] is True
        assert create_result["user_id"] == test_user_id
        assert create_result["sun_sign"] == "sagittarius"

        # Get the profile and verify natal chart structure
        profile = call_function("get_user_profile", {"user_id": test_user_id})

        assert profile["user_id"] == test_user_id
        assert profile["sun_sign"] == "sagittarius"
        assert profile["name"] == "Test User A"

        # Verify natal chart exists and has expected structure
        natal_chart = profile["natal_chart"]
        assert natal_chart is not None

        # Check planets
        assert "planets" in natal_chart
        assert len(natal_chart["planets"]) >= 10  # At least 10 planets

        planet_names = {p["name"] for p in natal_chart["planets"]}
        assert "sun" in planet_names
        assert "moon" in planet_names
        assert "mercury" in planet_names

        # Verify sun is in Sagittarius
        sun = next(p for p in natal_chart["planets"] if p["name"] == "sun")
        assert sun["sign"] == "sagittarius"

        # Check aspects exist
        assert "aspects" in natal_chart

        # Check summary was generated
        assert "summary" in natal_chart
        assert natal_chart["summary"] is not None
        assert len(natal_chart["summary"]) > 0

    @pytest.mark.llm
    def test_updates_last_active(self, test_user_id):
        """Test get_user_profile updates last_active timestamp."""
        import time

        # Create profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Get initial profile
        result1 = call_function("get_user_profile", {"user_id": test_user_id})
        initial_last_active = result1["last_active"]

        # Wait a moment
        time.sleep(0.5)

        # Get profile again
        result2 = call_function("get_user_profile", {"user_id": test_user_id})
        new_last_active = result2["last_active"]

        assert new_last_active > initial_last_active


class TestGetMemory:
    """E2E tests for get_memory Cloud Function."""

    def test_returns_empty_memory_if_not_exists(self, test_user_id):
        """Test get_memory returns empty memory for new user."""
        result = call_function("get_memory", {"user_id": test_user_id})

        assert result["user_id"] == test_user_id
        assert "categories" in result

    @pytest.mark.llm
    def test_returns_existing_memory(self, test_user_id):
        """Test get_memory returns memory after profile creation."""
        # Create profile (which initializes memory)
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Get memory
        result = call_function("get_memory", {"user_id": test_user_id})

        assert result["user_id"] == test_user_id
        assert "categories" in result

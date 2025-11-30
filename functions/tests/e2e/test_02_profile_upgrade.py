"""
E2E Tests for Journey 2: Profile Upgrade (V1 -> V2).

Tests the ACTUAL Cloud Functions via Firebase emulator:
- update_user_profile: Upgrade profile with birth time/location
- Verifies chart regeneration when birth data is added
- Verifies exact_chart flag changes correctly

NO MOCKS. Real HTTP calls to emulator. Real Gemini API. Real Firestore.
"""
import pytest

from .conftest import call_function


class TestUpdateUserProfile:
    """E2E tests for update_user_profile Cloud Function."""

    @pytest.mark.llm
    def test_upgrade_v1_to_v2(self, test_user_id):
        """Test upgrading V1 profile to V2 with full birth data."""
        # First create V1 profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Verify V1 profile
        profile_v1 = call_function("get_user_profile", {"user_id": test_user_id})
        assert profile_v1["exact_chart"] is False

        # Upgrade to V2
        result = call_function("update_user_profile", {
            "user_id": test_user_id,
            "birth_time": "14:30",
            "birth_timezone": "America/New_York",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
        })

        assert result["success"] is True

        # Verify V2 profile
        profile_v2 = result["profile"]
        assert profile_v2["exact_chart"] is True
        assert profile_v2["birth_time"] == "14:30"
        assert profile_v2["birth_timezone"] == "America/New_York"

    @pytest.mark.llm
    def test_upgrade_preserves_user_data(self, test_user_id):
        """Test upgrade preserves existing user data."""
        # Create V1 profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Original Name",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Upgrade to V2
        result = call_function("update_user_profile", {
            "user_id": test_user_id,
            "birth_time": "14:30",
            "birth_timezone": "America/New_York",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
        })

        profile = result["profile"]
        assert profile["name"] == "Original Name"
        assert profile["sun_sign"] == "gemini"
        assert profile["birth_date"] == "1990-06-15"

    @pytest.mark.llm
    def test_upgrade_regenerates_chart(self, test_user_id):
        """Test upgrade regenerates natal chart with new data."""
        # Create V1 profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Get V1 chart
        profile_v1 = call_function("get_user_profile", {"user_id": test_user_id})
        chart_v1 = profile_v1["natal_chart"]

        # Upgrade to V2
        result = call_function("update_user_profile", {
            "user_id": test_user_id,
            "birth_time": "14:30",
            "birth_timezone": "America/New_York",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
        })

        chart_v2 = result["profile"]["natal_chart"]

        # V2 chart should have accurate houses (V1 has estimated)
        assert "houses" in chart_v2
        assert len(chart_v2["houses"]) == 12

        # V2 chart should have angles (ascendant, midheaven)
        assert "angles" in chart_v2
        assert "ascendant" in chart_v2["angles"]
        assert "midheaven" in chart_v2["angles"]

    @pytest.mark.llm
    def test_upgrade_regenerates_summary(self, test_user_id):
        """Test upgrade regenerates natal chart summary."""
        # Create V1 profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Upgrade to V2
        result = call_function("update_user_profile", {
            "user_id": test_user_id,
            "birth_time": "14:30",
            "birth_timezone": "America/New_York",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
        })

        chart = result["profile"]["natal_chart"]
        assert "summary" in chart
        assert len(chart["summary"]) > 0

    def test_update_missing_user_raises_error(self):
        """Test updating nonexistent user raises error."""
        with pytest.raises(Exception) as exc_info:
            call_function("update_user_profile", {
                "user_id": "nonexistent_user_xyz_999",
                "birth_time": "14:30",
            })

        assert "NOT_FOUND" in str(exc_info.value)

    def test_update_missing_user_id_raises_error(self):
        """Test update without user_id raises error."""
        with pytest.raises(Exception):
            call_function("update_user_profile", {
                "birth_time": "14:30",
            })


class TestPhotoUpdate:
    """E2E tests for photo path update."""

    @pytest.mark.llm
    def test_update_photo_path(self, test_user_id):
        """Test updating photo path only (no chart regeneration)."""
        # Create profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Update photo path only
        result = call_function("update_user_profile", {
            "user_id": test_user_id,
            "photo_path": "users/test_user/profile.jpg",
        })

        assert result["success"] is True
        assert result["profile"]["photo_path"] == "users/test_user/profile.jpg"

    @pytest.mark.llm
    def test_photo_update_preserves_chart(self, test_user_id):
        """Test photo update doesn't regenerate chart."""
        # Create V2 profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "birth_timezone": "America/New_York",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
        })

        # Get original chart
        profile_before = call_function("get_user_profile", {"user_id": test_user_id})
        chart_before = profile_before["natal_chart"]

        # Update photo only
        result = call_function("update_user_profile", {
            "user_id": test_user_id,
            "photo_path": "users/test_user/profile.jpg",
        })

        # Chart should be unchanged
        chart_after = result["profile"]["natal_chart"]

        # Compare planets (should be identical)
        planets_before = {p["name"]: p["absolute_degree"] for p in chart_before["planets"]}
        planets_after = {p["name"]: p["absolute_degree"] for p in chart_after["planets"]}

        assert planets_before == planets_after


class TestPartialUpgrade:
    """E2E tests for partial profile upgrades."""

    @pytest.mark.llm
    def test_add_birth_time_only(self, test_user_id):
        """Test adding only birth time (no location)."""
        # Create V1 profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Add birth time only
        result = call_function("update_user_profile", {
            "user_id": test_user_id,
            "birth_time": "14:30",
        })

        assert result["success"] is True
        profile = result["profile"]
        assert profile["birth_time"] == "14:30"
        # Without location, still not fully exact
        # The exact_chart flag depends on implementation

    @pytest.mark.llm
    def test_incremental_upgrade(self, test_user_id):
        """Test upgrading profile incrementally (time first, then location)."""
        # Create V1 profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Add birth time first
        call_function("update_user_profile", {
            "user_id": test_user_id,
            "birth_time": "14:30",
        })

        # Then add location
        result = call_function("update_user_profile", {
            "user_id": test_user_id,
            "birth_timezone": "America/New_York",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
        })

        assert result["success"] is True
        profile = result["profile"]
        assert profile["birth_time"] == "14:30"
        assert profile["birth_timezone"] == "America/New_York"
        assert profile["exact_chart"] is True

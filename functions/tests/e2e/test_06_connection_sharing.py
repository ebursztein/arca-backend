"""
E2E Tests for Journey 6: Connection Sharing.

Tests the ACTUAL Cloud Functions via Firebase emulator:
- get_share_link: Generate/retrieve share link
- get_public_profile: Retrieve public profile from share link
- import_connection: Add connection from share link
- update_share_mode: Toggle public/request-only mode
- list_connection_requests: List pending requests
- respond_to_request: Approve/reject connection requests

NO MOCKS. Real HTTP calls to emulator. Real Firestore.
"""
import pytest

from .conftest import call_function


class TestGetShareLink:
    """E2E tests for get_share_link Cloud Function."""

    @pytest.mark.llm
    def test_creates_share_link(self, test_user_id):
        """Test get_share_link creates a new share link."""
        # Create user profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        result = call_function("get_share_link", {"user_id": test_user_id})

        assert "share_url" in result
        assert "share_mode" in result
        assert "qr_code_data" in result
        assert "arca-app.com" in result["share_url"]

    @pytest.mark.llm
    def test_returns_same_link_on_second_call(self, test_user_id):
        """Test get_share_link returns same link on subsequent calls."""
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        result1 = call_function("get_share_link", {"user_id": test_user_id})
        result2 = call_function("get_share_link", {"user_id": test_user_id})

        assert result1["share_url"] == result2["share_url"]

    def test_missing_user_raises_error(self):
        """Test get_share_link for nonexistent user raises error."""
        with pytest.raises(Exception):
            call_function("get_share_link", {"user_id": "nonexistent_user_xyz"})


class TestGetPublicProfile:
    """E2E tests for get_public_profile Cloud Function."""

    @pytest.mark.llm
    def test_returns_public_profile(self, test_user_id):
        """Test get_public_profile returns profile data."""
        # Create user and get share link
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        share_result = call_function("get_share_link", {"user_id": test_user_id})

        # Extract share secret from URL
        share_secret = share_result["share_url"].split("/")[-1]

        # Get public profile
        result = call_function("get_public_profile", {"share_secret": share_secret})

        assert "profile" in result
        assert "share_mode" in result
        assert "can_add" in result
        assert result["profile"]["name"] == "Test User"

    def test_invalid_share_secret_raises_error(self):
        """Test invalid share secret raises error."""
        with pytest.raises(Exception):
            call_function("get_public_profile", {"share_secret": "invalid_secret_xyz"})


class TestImportConnection:
    """E2E tests for import_connection Cloud Function."""

    @pytest.mark.llm
    def test_imports_connection_from_public_profile(self):
        """Test import_connection adds connection from public share link."""
        # Use dedicated dev accounts for sharing tests
        source_user_id = "test_sharing_source"
        importing_user_id = "test_sharing_importer"

        # Create source user
        call_function("create_user_profile", {
            "user_id": source_user_id,
            "name": "Source User",
            "email": f"{source_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Get share link for source user
        share_result = call_function("get_share_link", {"user_id": source_user_id})
        share_secret = share_result["share_url"].split("/")[-1]

        # Create importing user
        call_function("create_user_profile", {
            "user_id": importing_user_id,
            "name": "Importing User",
            "email": f"{importing_user_id}@test.com",
            "birth_date": "1992-08-15",
        })

        # Import connection
        result = call_function("import_connection", {
            "user_id": importing_user_id,
            "share_secret": share_secret,
            "relationship_category": "friend",
            "relationship_label": "friend",
        })

        assert result["success"] is True
        assert "connection_id" in result

        # Verify connection was created
        connections = call_function("list_connections", {"user_id": importing_user_id})
        assert len(connections["connections"]) == 1
        assert connections["connections"][0]["name"] == "Source User"

    @pytest.mark.llm
    def test_cannot_import_self(self, test_user_id):
        """Test cannot import yourself as a connection."""
        # Create user
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Get own share link
        share_result = call_function("get_share_link", {"user_id": test_user_id})
        share_secret = share_result["share_url"].split("/")[-1]

        # Try to import self
        with pytest.raises(Exception) as exc_info:
            call_function("import_connection", {
                "user_id": test_user_id,
                "share_secret": share_secret,
                "relationship_category": "friend",
                "relationship_label": "friend",
            })

        assert "yourself" in str(exc_info.value).lower()


class TestUpdateShareMode:
    """E2E tests for update_share_mode Cloud Function."""

    @pytest.mark.llm
    def test_update_to_request_mode(self, test_user_id):
        """Test updating share mode to request."""
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        result = call_function("update_share_mode", {
            "user_id": test_user_id,
            "share_mode": "request",
        })

        assert result["share_mode"] == "request"

    @pytest.mark.llm
    def test_update_to_public_mode(self, test_user_id):
        """Test updating share mode to public."""
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # First set to request
        call_function("update_share_mode", {
            "user_id": test_user_id,
            "share_mode": "request",
        })

        # Then back to public
        result = call_function("update_share_mode", {
            "user_id": test_user_id,
            "share_mode": "public",
        })

        assert result["share_mode"] == "public"

    def test_missing_user_raises_error(self):
        """Test update_share_mode for nonexistent user raises error."""
        with pytest.raises(Exception):
            call_function("update_share_mode", {
                "user_id": "nonexistent_user_xyz",
                "share_mode": "request",
            })


class TestListConnectionRequests:
    """E2E tests for list_connection_requests Cloud Function."""

    @pytest.mark.llm
    def test_returns_empty_list_initially(self, test_user_id):
        """Test list_connection_requests returns empty list for new user."""
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        result = call_function("list_connection_requests", {"user_id": test_user_id})

        assert "requests" in result
        assert len(result["requests"]) == 0


class TestRespondToRequest:
    """E2E tests for respond_to_request Cloud Function."""

    def test_nonexistent_request_raises_error(self, test_user_id):
        """Test responding to nonexistent request raises error."""
        with pytest.raises(Exception):
            call_function("respond_to_request", {
                "user_id": test_user_id,
                "request_id": "nonexistent_request_xyz",
                "action": "approve",
            })

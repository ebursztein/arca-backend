"""
E2E Tests for Journey 5: Connection CRUD Operations.

Tests the ACTUAL Cloud Functions via Firebase emulator:
- create_connection: Create a new connection
- list_connections: List all user's connections
- update_connection: Update connection details
- delete_connection: Remove a connection

NO MOCKS. Real HTTP calls to emulator. Real Firestore.
"""
import pytest

from .conftest import call_function


class TestCreateConnection:
    """E2E tests for create_connection Cloud Function."""

    @pytest.mark.llm
    def test_create_minimal_connection(self, test_user_id):
        """Test creating connection with minimal data."""
        # First create user profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Create connection
        result = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "John",
                "birth_date": "1992-08-15",
                "relationship_type": "friend",
            }
        })

        assert "connection_id" in result
        assert result["sun_sign"] == "leo"
        assert result["name"] == "John"

    @pytest.mark.llm
    def test_create_connection_with_full_data(self, test_user_id):
        """Test creating connection with full birth data."""
        # Create user profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Create connection with full data
        result = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "Jane",
                "birth_date": "1995-03-22",
                "birth_time": "14:30",
                "birth_timezone": "America/New_York",
                "birth_lat": 40.7128,
                "birth_lon": -74.0060,
                "relationship_type": "partner",
            }
        })

        assert "connection_id" in result
        assert result["sun_sign"] == "aries"
        assert result["name"] == "Jane"

    def test_create_connection_missing_user_raises_error(self):
        """Test creating connection for nonexistent user raises error."""
        with pytest.raises(Exception):
            call_function("create_connection", {
                "user_id": "nonexistent_user_xyz",
                "connection": {
                    "name": "John",
                    "birth_date": "1992-08-15",
                    "relationship_type": "friend",
                }
            })

    def test_create_connection_missing_fields_raises_error(self, test_user_id):
        """Test creating connection without required fields raises error."""
        with pytest.raises(Exception):
            call_function("create_connection", {
                "user_id": test_user_id,
                "connection": {
                    "name": "John",
                    # Missing birth_date and relationship_type
                }
            })


class TestListConnections:
    """E2E tests for list_connections Cloud Function."""

    @pytest.mark.llm
    def test_list_empty_connections(self, test_user_id):
        """Test listing connections when user has none."""
        # Create user profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        result = call_function("list_connections", {"user_id": test_user_id})

        assert "connections" in result
        assert len(result["connections"]) == 0

    @pytest.mark.llm
    def test_list_multiple_connections(self, test_user_id):
        """Test listing multiple connections."""
        # Create user profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Create multiple connections
        call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "John",
                "birth_date": "1992-08-15",
                "relationship_type": "friend",
            }
        })

        call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "Jane",
                "birth_date": "1995-03-22",
                "relationship_type": "partner",
            }
        })

        call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "Mom",
                "birth_date": "1965-07-10",
                "relationship_type": "family",
            }
        })

        result = call_function("list_connections", {"user_id": test_user_id})

        assert len(result["connections"]) == 3

        names = {c["name"] for c in result["connections"]}
        assert names == {"John", "Jane", "Mom"}

    @pytest.mark.llm
    def test_list_connections_has_required_fields(self, test_user_id):
        """Test each connection in list has required fields."""
        # Create user profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Create a connection
        call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "John",
                "birth_date": "1992-08-15",
                "relationship_type": "friend",
            }
        })

        result = call_function("list_connections", {"user_id": test_user_id})
        conn = result["connections"][0]

        assert "connection_id" in conn
        assert "name" in conn
        assert "birth_date" in conn
        assert "relationship_type" in conn
        assert "sun_sign" in conn
        assert "created_at" in conn


class TestUpdateConnection:
    """E2E tests for update_connection Cloud Function."""

    @pytest.mark.llm
    def test_update_connection_name(self, test_user_id):
        """Test updating connection name."""
        # Create user and connection
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        create_result = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "John",
                "birth_date": "1992-08-15",
                "relationship_type": "friend",
            }
        })

        conn_id = create_result["connection_id"]

        # Update name
        update_result = call_function("update_connection", {
            "user_id": test_user_id,
            "connection_id": conn_id,
            "updates": {"name": "Johnny"},
        })

        assert update_result["name"] == "Johnny"
        assert "connection_id" in update_result

        # Verify update via list
        connections = call_function("list_connections", {"user_id": test_user_id})
        conn = connections["connections"][0]
        assert conn["name"] == "Johnny"

    @pytest.mark.llm
    def test_update_connection_relationship_type(self, test_user_id):
        """Test updating connection relationship type."""
        # Create user and connection
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        create_result = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "Jane",
                "birth_date": "1995-03-22",
                "relationship_type": "friend",
            }
        })

        conn_id = create_result["connection_id"]

        # Update relationship type
        update_result = call_function("update_connection", {
            "user_id": test_user_id,
            "connection_id": conn_id,
            "updates": {"relationship_type": "partner"},
        })

        assert update_result["relationship_type"] == "partner"
        assert "connection_id" in update_result

        # Verify update via list
        connections = call_function("list_connections", {"user_id": test_user_id})
        conn = connections["connections"][0]
        assert conn["relationship_type"] == "partner"

    def test_update_nonexistent_connection_raises_error(self, test_user_id):
        """Test updating nonexistent connection raises error."""
        with pytest.raises(Exception):
            call_function("update_connection", {
                "user_id": test_user_id,
                "connection_id": "nonexistent_conn_xyz",
                "updates": {"name": "Updated Name"},
            })


class TestDeleteConnection:
    """E2E tests for delete_connection Cloud Function."""

    @pytest.mark.llm
    def test_delete_connection(self, test_user_id):
        """Test deleting a connection."""
        # Create user and connection
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        create_result = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "John",
                "birth_date": "1992-08-15",
                "relationship_type": "friend",
            }
        })

        conn_id = create_result["connection_id"]

        # Verify connection exists
        connections_before = call_function("list_connections", {"user_id": test_user_id})
        assert len(connections_before["connections"]) == 1

        # Delete connection
        delete_result = call_function("delete_connection", {
            "user_id": test_user_id,
            "connection_id": conn_id,
        })

        assert delete_result["success"] is True

        # Verify deletion
        connections_after = call_function("list_connections", {"user_id": test_user_id})
        assert len(connections_after["connections"]) == 0

    @pytest.mark.llm
    def test_delete_one_of_multiple_connections(self, test_user_id):
        """Test deleting one connection leaves others intact."""
        # Create user and multiple connections
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        result1 = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "John",
                "birth_date": "1992-08-15",
                "relationship_type": "friend",
            }
        })

        call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "Jane",
                "birth_date": "1995-03-22",
                "relationship_type": "partner",
            }
        })

        # Delete first connection
        call_function("delete_connection", {
            "user_id": test_user_id,
            "connection_id": result1["connection_id"],
        })

        # Verify only Jane remains
        connections = call_function("list_connections", {"user_id": test_user_id})
        assert len(connections["connections"]) == 1
        assert connections["connections"][0]["name"] == "Jane"

    def test_delete_nonexistent_connection_raises_error(self, test_user_id):
        """Test deleting nonexistent connection raises error."""
        with pytest.raises(Exception):
            call_function("delete_connection", {
                "user_id": test_user_id,
                "connection_id": "nonexistent_conn_xyz",
            })

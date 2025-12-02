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
from .emulator_helpers import clear_subcollection


@pytest.fixture
def crud_user_id():
    """Dedicated user ID for CRUD tests to avoid pollution from other tests."""
    return "test_crud_user"


@pytest.fixture
def clean_connections(firestore_emulator, crud_user_id):
    """Clear all connections for test user before and after test."""
    # Clear before test
    count = clear_subcollection(firestore_emulator, f"users/{crud_user_id}", "connections")
    print(f"[CLEANUP] Deleted {count} connections for {crud_user_id} BEFORE test")
    yield crud_user_id
    # Clear after test
    count = clear_subcollection(firestore_emulator, f"users/{crud_user_id}", "connections")
    print(f"[CLEANUP] Deleted {count} connections for {crud_user_id} AFTER test")


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
                "relationship_category": "friend",
                "relationship_label": "friend",
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
                "relationship_category": "love",
                "relationship_label": "partner",
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
                    "relationship_category": "friend",
                    "relationship_label": "friend",
                }
            })

    def test_create_connection_missing_fields_raises_error(self, test_user_id):
        """Test creating connection without required fields raises error."""
        with pytest.raises(Exception):
            call_function("create_connection", {
                "user_id": test_user_id,
                "connection": {
                    "name": "John",
                    # Missing birth_date and relationship fields
                }
            })


class TestListConnections:
    """E2E tests for list_connections Cloud Function."""

    @pytest.mark.llm
    def test_list_connections_structure(self, test_user_id):
        """Test list_connections returns proper structure."""
        # Create user profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        result = call_function("list_connections", {"user_id": test_user_id})

        # Verify structure (not count - other tests may have added connections)
        assert "connections" in result
        assert "total_count" in result
        assert isinstance(result["connections"], list)

    @pytest.mark.llm
    def test_create_and_list_connections(self, test_user_id):
        """Test creating connections increases count."""
        # Create user profile
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Get initial count
        before = call_function("list_connections", {"user_id": test_user_id})
        initial_count = len(before["connections"])

        # Create 3 connections
        call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "TestJohn",
                "birth_date": "1992-08-15",
                "relationship_category": "friend",
                "relationship_label": "friend",
            }
        })

        call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "TestJane",
                "birth_date": "1995-03-22",
                "relationship_category": "love",
                "relationship_label": "partner",
            }
        })

        call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "TestMom",
                "birth_date": "1965-07-10",
                "relationship_category": "family",
                "relationship_label": "mother",
            }
        })

        result = call_function("list_connections", {"user_id": test_user_id})

        # Verify count increased by 3
        assert len(result["connections"]) == initial_count + 3

        # Verify our new connections exist
        names = {c["name"] for c in result["connections"]}
        assert "TestJohn" in names
        assert "TestJane" in names
        assert "TestMom" in names

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
                "relationship_category": "friend",
                "relationship_label": "friend",
            }
        })

        result = call_function("list_connections", {"user_id": test_user_id})
        conn = result["connections"][0]

        assert "connection_id" in conn
        assert "name" in conn
        assert "birth_date" in conn
        assert "relationship_category" in conn
        assert "relationship_label" in conn
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
                "relationship_category": "friend",
                "relationship_label": "friend",
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
    def test_update_connection_relationship(self, test_user_id):
        """Test updating connection relationship category and label."""
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
                "relationship_category": "friend",
                "relationship_label": "friend",
            }
        })

        conn_id = create_result["connection_id"]

        # Update relationship category and label
        update_result = call_function("update_connection", {
            "user_id": test_user_id,
            "connection_id": conn_id,
            "updates": {
                "relationship_category": "love",
                "relationship_label": "partner",
            },
        })

        assert update_result["relationship_category"] == "love"
        assert update_result["relationship_label"] == "partner"
        assert "connection_id" in update_result

        # Verify update via list
        connections = call_function("list_connections", {"user_id": test_user_id})
        conn = connections["connections"][0]
        assert conn["relationship_category"] == "love"
        assert conn["relationship_label"] == "partner"

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
        """Test deleting a connection decreases count."""
        # Create user and connection
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Create a connection to delete
        create_result = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "ToBeDeleted",
                "birth_date": "1992-08-15",
                "relationship_category": "friend",
                "relationship_label": "friend",
            }
        })

        conn_id = create_result["connection_id"]

        # Get count before delete
        connections_before = call_function("list_connections", {"user_id": test_user_id})
        count_before = len(connections_before["connections"])

        # Delete connection
        delete_result = call_function("delete_connection", {
            "user_id": test_user_id,
            "connection_id": conn_id,
        })

        assert delete_result["success"] is True

        # Verify count decreased by 1
        connections_after = call_function("list_connections", {"user_id": test_user_id})
        assert len(connections_after["connections"]) == count_before - 1

        # Verify the deleted connection is gone
        conn_ids = {c["connection_id"] for c in connections_after["connections"]}
        assert conn_id not in conn_ids

    @pytest.mark.llm
    def test_delete_specific_connection(self, test_user_id):
        """Test deleting one connection leaves others intact."""
        # Create user
        call_function("create_user_profile", {
            "user_id": test_user_id,
            "name": "Test User",
            "email": f"{test_user_id}@test.com",
            "birth_date": "1990-06-15",
        })

        # Create two connections
        result1 = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "DeleteMe",
                "birth_date": "1992-08-15",
                "relationship_category": "friend",
                "relationship_label": "friend",
            }
        })

        result2 = call_function("create_connection", {
            "user_id": test_user_id,
            "connection": {
                "name": "KeepMe",
                "birth_date": "1995-03-22",
                "relationship_category": "love",
                "relationship_label": "partner",
            }
        })

        # Get count before
        before = call_function("list_connections", {"user_id": test_user_id})
        count_before = len(before["connections"])

        # Delete first connection
        call_function("delete_connection", {
            "user_id": test_user_id,
            "connection_id": result1["connection_id"],
        })

        # Verify count decreased by 1 and KeepMe still exists
        after = call_function("list_connections", {"user_id": test_user_id})
        assert len(after["connections"]) == count_before - 1

        conn_ids = {c["connection_id"] for c in after["connections"]}
        assert result1["connection_id"] not in conn_ids
        assert result2["connection_id"] in conn_ids

    def test_delete_nonexistent_connection_raises_error(self, test_user_id):
        """Test deleting nonexistent connection raises error."""
        with pytest.raises(Exception):
            call_function("delete_connection", {
                "user_id": test_user_id,
                "connection_id": "nonexistent_conn_xyz",
            })

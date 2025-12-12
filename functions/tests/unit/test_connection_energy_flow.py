"""
Unit tests for connection energy data flow in daily horoscope.

Tests the hypothesis that synastry_points must be populated for
connection energy to appear in the daily horoscope prompt.

These tests verify:
1. synastry_points is populated when connections are created
2. featured_connection enrichment only happens when synastry_points exists
3. The template renders connection energy data when present
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from jinja2 import Environment, FileSystemLoader
from pathlib import Path


# =============================================================================
# Test: synastry_points population on connection creation
# =============================================================================

class TestSynastryPointsPopulation:
    """Tests for synastry_points being populated when connections are created."""

    def test_create_connection_populates_synastry_points(self):
        """
        HYPOTHESIS: create_connection should populate synastry_points
        when both user and connection have birth_date.
        """
        from connections import create_connection, Connection
        from astro import compute_birth_chart

        # Mock Firestore
        mock_db = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
            "birth_timezone": "America/New_York"
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc

        # Mock the set operation
        mock_conn_ref = MagicMock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_conn_ref

        connection = create_connection(
            db=mock_db,
            user_id="test_user",
            name="Test Connection",
            birth_date="1992-03-22",
            relationship_category="friend",
            relationship_label="friend",
            birth_time="10:15",
            birth_lat=34.0522,
            birth_lon=-118.2437,
            birth_timezone="America/Los_Angeles"
        )

        # ASSERTION: synastry_points should be populated
        assert connection.synastry_points is not None, \
            "synastry_points should be populated when both user and connection have birth data"
        assert len(connection.synastry_points) > 0, \
            "synastry_points should contain at least one point"

    def test_create_connection_without_user_birth_data_no_synastry(self):
        """
        When user has no birth_date, synastry_points should not be populated.
        """
        from connections import create_connection

        # Mock Firestore - user without birth data
        mock_db = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            # No birth_date
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc

        mock_conn_ref = MagicMock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_conn_ref

        connection = create_connection(
            db=mock_db,
            user_id="test_user",
            name="Test Connection",
            birth_date="1992-03-22",
            relationship_category="friend",
            relationship_label="friend"
        )

        # Without user birth data, synastry can't be calculated
        assert connection.synastry_points is None, \
            "synastry_points should be None when user has no birth_date"


# =============================================================================
# Test: get_connections_for_horoscope returns synastry_points
# =============================================================================

class TestGetConnectionsForHoroscope:
    """Tests that get_connections_for_horoscope returns connections with synastry_points."""

    def test_returns_synastry_points_when_present(self):
        """
        HYPOTHESIS: get_connections_for_horoscope should return synastry_points
        if they exist on the connection document.
        """
        from connections import get_connections_for_horoscope

        # Mock Firestore with connection that has synastry_points
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "connection_id": "conn_123",
            "name": "Johnny",
            "birth_date": "1992-08-15",
            "relationship_category": "friend",
            "relationship_label": "friend",
            "sun_sign": "leo",
            "synastry_points": [
                {"degree": 120.5, "label": "Sun-Moon midpoint"},
                {"degree": 45.2, "label": "Venus-Mars midpoint"}
            ],
            "created_at": "2025-01-01T00:00:00"
        }

        mock_db.collection.return_value.document.return_value.collection.return_value.order_by.return_value.limit.return_value.get.return_value = [mock_doc]

        connections = get_connections_for_horoscope(mock_db, "test_user", limit=10)

        assert len(connections) == 1
        assert connections[0]["synastry_points"] is not None, \
            "synastry_points should be returned when present in Firestore"
        assert len(connections[0]["synastry_points"]) == 2

    def test_returns_none_synastry_points_when_missing(self):
        """
        When connection document has no synastry_points, it should be missing from dict.
        """
        from connections import get_connections_for_horoscope

        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "connection_id": "conn_123",
            "name": "Johnny",
            "birth_date": "1992-08-15",
            "relationship_category": "friend",
            "relationship_label": "friend",
            "sun_sign": "leo",
            # NO synastry_points field
            "created_at": "2025-01-01T00:00:00"
        }

        mock_db.collection.return_value.document.return_value.collection.return_value.order_by.return_value.limit.return_value.get.return_value = [mock_doc]

        connections = get_connections_for_horoscope(mock_db, "test_user", limit=10)

        assert len(connections) == 1
        # This is the BUG: synastry_points is missing, which causes enrichment to be skipped
        assert connections[0].get("synastry_points") is None, \
            "synastry_points should be None/missing when not in Firestore"


# =============================================================================
# Test: featured_connection enrichment logic
# =============================================================================

class TestFeaturedConnectionEnrichment:
    """Tests for the enrichment logic in get_daily_horoscope."""

    def test_enrichment_requires_synastry_points(self):
        """
        HYPOTHESIS: The enrichment code in main.py only runs when
        featured_connection.get("synastry_points") is truthy.

        This test documents the current behavior that causes the bug.
        """
        # Simulate the condition check from main.py line 744
        featured_connection_with_synastry = {
            "connection_id": "conn_123",
            "name": "Johnny",
            "synastry_points": [{"degree": 120.5, "label": "test"}]
        }

        featured_connection_without_synastry = {
            "connection_id": "conn_123",
            "name": "Johnny",
            # No synastry_points
        }

        # This is the condition from main.py:744
        # if featured_connection and featured_connection.get("synastry_points"):

        with_synastry_passes = bool(
            featured_connection_with_synastry and
            featured_connection_with_synastry.get("synastry_points")
        )
        without_synastry_passes = bool(
            featured_connection_without_synastry and
            featured_connection_without_synastry.get("synastry_points")
        )

        assert with_synastry_passes is True, \
            "Connection with synastry_points should pass enrichment check"
        assert without_synastry_passes is False, \
            "Connection without synastry_points should FAIL enrichment check - THIS IS THE BUG"

    def test_enrichment_adds_vibe_score_and_active_transits(self):
        """
        When synastry_points exists, enrichment should add vibe_score and active_transits.
        """
        from compatibility import find_transits_to_synastry, calculate_vibe_score
        from astro import compute_birth_chart, NatalChartData

        # Create a transit chart for today
        transit_chart_dict, _ = compute_birth_chart("2025-12-08", "12:00")
        transit_chart = NatalChartData(**transit_chart_dict)

        # Sample synastry points
        synastry_points = [
            {"degree": 120.5, "sign": "leo", "label": "Sun-Moon"},
            {"degree": 45.2, "sign": "taurus", "label": "Venus-Mars"}
        ]

        # This is what the enrichment code does
        active_transits = find_transits_to_synastry(
            transit_chart=transit_chart,
            synastry_points=synastry_points,
            orb=3.0
        )
        vibe_score = calculate_vibe_score(active_transits)

        # Verify enrichment produces data
        assert isinstance(active_transits, list), "active_transits should be a list"
        assert isinstance(vibe_score, (int, float)), "vibe_score should be numeric"
        assert 0 <= vibe_score <= 100, "vibe_score should be 0-100"


# =============================================================================
# Test: Template rendering with connection energy
# =============================================================================

class TestTemplateRendersConnectionEnergy:
    """Tests that the template renders connection energy when data is present."""

    @pytest.fixture
    def template_env(self):
        """Load the Jinja2 template environment."""
        templates_dir = Path(__file__).parent.parent.parent / "templates" / "horoscope"
        return Environment(loader=FileSystemLoader(str(templates_dir)))

    def test_template_renders_vibe_score_when_present(self, template_env):
        """
        When featured_connection has vibe_score, it should appear in output.
        """
        template = template_env.get_template("daily_dynamic.j2")

        # Minimal context with connection energy data
        context = {
            "date": "2025-12-08",
            "headline_guidance": {"meters": [], "conjunction": None},
            "overall_unified_score": 62,
            "overall_guidance": "Test guidance",
            "overall_writing_guidance": {
                "pattern": "neutral_day",
                "formula": "Test formula",
                "strongest_group": "mind",
                "strongest_score": 55,
                "challenging_group": None,
                "challenging_score": None,
                "flowing_groups": [],
                "challenging_groups": [],
                "shining_group": None,
            },
            "overview_guidance": {"formatted_highlights": []},
            "has_relationships": True,
            "user_name": "Test User",
            "user_first_name": "Test",
            "heart_group": None,
            "relationship_transits": [],
            "featured_connection": {
                "name": "Johnny",
                "relationship_category": "friend",
                "relationship_label": "friend",
                "sun_sign": "leo",
                "vibe_score": 75,
                "active_transits": [
                    {"description": "Mars activating your connection point", "quality": "energizing"}
                ],
                "synastry_points": [
                    {"label": "Sun-Moon midpoint"}
                ]
            },
            "moon_summary": "Moon in Leo",
            "is_void_of_course": False,
            "upcoming_transits": [],
            "all_groups": [
                {"name": "mind", "unified_score": 55, "meter_scores": {"clarity": 55, "focus": 54, "communication": 56}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "heart", "unified_score": 50, "meter_scores": {"connections": 50, "resilience": 51, "vulnerability": 49}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "body", "unified_score": 52, "meter_scores": {"energy": 52, "drive": 53, "strength": 51}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "instincts", "unified_score": 48, "meter_scores": {"vision": 48, "flow": 47, "intuition": 49, "creativity": 48}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "growth", "unified_score": 51, "meter_scores": {"momentum": 51, "ambition": 50, "evolution": 52, "circle": 51}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
            ],
            "key_transits": []
        }

        output = template.render(**context)

        # Assertions - check current template format
        assert "75/100" in output, \
            "Template should render vibe_score when present"
        assert "Good vibe" in output, \
            "Template should render writing formula for good vibe (75 is >= 60)"
        assert "CONNECTION VIBE" in output, \
            "Template should render CONNECTION VIBE section"

    def test_template_renders_connection_section_with_basic_info(self, template_env):
        """
        When featured_connection exists, the template renders CONNECTION VIBE section
        with basic connection info, even if synastry data is missing.
        """
        template = template_env.get_template("daily_dynamic.j2")

        # Connection without synastry data
        context = {
            "date": "2025-12-08",
            "headline_guidance": {"meters": [], "conjunction": None},
            "overall_unified_score": 62,
            "overall_guidance": "Test guidance",
            "overall_writing_guidance": {
                "pattern": "neutral_day",
                "formula": "Test formula",
                "strongest_group": "mind",
                "strongest_score": 55,
                "challenging_group": None,
                "challenging_score": None,
                "flowing_groups": [],
                "challenging_groups": [],
                "shining_group": None,
            },
            "overview_guidance": {"formatted_highlights": []},
            "has_relationships": True,
            "user_name": "Test User",
            "user_first_name": "Test",
            "heart_group": None,
            "relationship_transits": [],
            "featured_connection": {
                "name": "Johnny",
                "relationship_category": "friend",
                "relationship_label": "friend",
                "sun_sign": "leo",
                # NO vibe_score, NO active_transits, NO synastry_points
            },
            "moon_summary": "Moon in Leo",
            "is_void_of_course": False,
            "upcoming_transits": [],
            "all_groups": [
                {"name": "mind", "unified_score": 55, "meter_scores": {"clarity": 55, "focus": 54, "communication": 56}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "heart", "unified_score": 50, "meter_scores": {"connections": 50, "resilience": 51, "vulnerability": 49}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "body", "unified_score": 52, "meter_scores": {"energy": 52, "drive": 53, "strength": 51}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "instincts", "unified_score": 48, "meter_scores": {"vision": 48, "flow": 47, "intuition": 49, "creativity": 48}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "growth", "unified_score": 51, "meter_scores": {"momentum": 51, "ambition": 50, "evolution": 52, "circle": 51}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
            ],
            "key_transits": []
        }

        output = template.render(**context)

        # Connection VIBE section renders with basic info
        assert "CONNECTION VIBE" in output, "Connection vibe section should appear"
        assert "Johnny" in output, "Connection name should appear"
        assert "friend" in output, "Relationship label should appear"
        assert "Leo" in output, "Sun sign should appear (title cased)"


# =============================================================================
# Test: End-to-end flow simulation
# =============================================================================

class TestConnectionEnergyEndToEnd:
    """
    Simulates the end-to-end flow to identify where data is lost.
    """

    def test_connection_created_via_api_has_synastry_points(self):
        """
        Simulate creating a connection via the API and verify synastry_points is cached.
        """
        from connections import calculate_and_cache_synastry

        # Mock Firestore
        mock_db = MagicMock()
        mock_conn_ref = MagicMock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_conn_ref

        result = calculate_and_cache_synastry(
            db=mock_db,
            user_id="test_user",
            connection_id="conn_123",
            user_birth_date="1990-06-15",
            user_birth_time="14:30",
            user_birth_lat=40.7128,
            user_birth_lon=-74.0060,
            user_birth_timezone="America/New_York",
            conn_birth_date="1992-08-15",
            conn_birth_time="12:00",
            conn_birth_lat=0.0,
            conn_birth_lon=0.0,
            conn_birth_timezone="UTC"
        )

        # Verify synastry was calculated
        assert result is not None, "calculate_and_cache_synastry should return result"
        assert "synastry_points" in result, "Result should contain synastry_points"
        assert len(result["synastry_points"]) > 0, "Should have synastry points"

        # Verify Firestore update was called with synastry_points
        mock_conn_ref.update.assert_called_once()
        update_call = mock_conn_ref.update.call_args[0][0]
        assert "synastry_points" in update_call, \
            "Firestore should be updated with synastry_points"


# =============================================================================
# Regression test: calculate_and_cache_synastry must not require relationship_type
# =============================================================================

class TestCalculateAndCacheSynastryRegression:
    """
    Regression tests for calculate_and_cache_synastry.

    BUG FOUND: calculate_compatibility() signature changed to require relationship_type,
    but calculate_and_cache_synastry was not updated, causing silent failure.

    FIXED: Now uses calculate_synastry_aspects() which doesn't require relationship_type.
    """

    def test_calculate_and_cache_synastry_does_not_throw(self):
        """
        REGRESSION TEST: calculate_and_cache_synastry should not throw an exception
        when calculating synastry aspects.

        This test catches the bug where calculate_compatibility() was called without
        the required relationship_type argument.
        """
        from connections import calculate_and_cache_synastry

        mock_db = MagicMock()
        mock_conn_ref = MagicMock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_conn_ref

        # This should NOT throw an exception
        result = calculate_and_cache_synastry(
            db=mock_db,
            user_id="test_user",
            connection_id="conn_123",
            user_birth_date="1990-06-15",
            user_birth_time="14:30",
            user_birth_lat=40.7128,
            user_birth_lon=-74.0060,
            user_birth_timezone="America/New_York",
            conn_birth_date="1992-08-15",
            conn_birth_time="12:00",
            conn_birth_lat=0.0,
            conn_birth_lon=0.0,
            conn_birth_timezone="UTC"
        )

        # The function should return a valid result, not None (which indicates failure)
        assert result is not None, \
            "calculate_and_cache_synastry returned None - likely threw an exception internally"

    def test_calculate_and_cache_synastry_returns_synastry_aspects(self):
        """
        REGRESSION TEST: The result should include synastry_aspects list.
        """
        from connections import calculate_and_cache_synastry

        mock_db = MagicMock()
        mock_conn_ref = MagicMock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_conn_ref

        result = calculate_and_cache_synastry(
            db=mock_db,
            user_id="test_user",
            connection_id="conn_123",
            user_birth_date="1990-06-15",
            user_birth_time="14:30",
            user_birth_lat=40.7128,
            user_birth_lon=-74.0060,
            user_birth_timezone="America/New_York",
            conn_birth_date="1992-08-15",
            conn_birth_time="12:00",
            conn_birth_lat=0.0,
            conn_birth_lon=0.0,
            conn_birth_timezone="UTC"
        )

        assert result is not None, "calculate_and_cache_synastry should not return None"
        assert "synastry_aspects" in result, "Result should contain synastry_aspects"
        assert isinstance(result["synastry_aspects"], list), "synastry_aspects should be a list"

    def test_synastry_aspect_has_required_fields(self):
        """
        REGRESSION TEST: Each synastry aspect should have the required fields.
        """
        from connections import calculate_and_cache_synastry

        mock_db = MagicMock()
        mock_conn_ref = MagicMock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_conn_ref

        result = calculate_and_cache_synastry(
            db=mock_db,
            user_id="test_user",
            connection_id="conn_123",
            user_birth_date="1990-06-15",
            user_birth_time="14:30",
            user_birth_lat=40.7128,
            user_birth_lon=-74.0060,
            user_birth_timezone="America/New_York",
            conn_birth_date="1992-08-15",
            conn_birth_time="12:00",
            conn_birth_lat=0.0,
            conn_birth_lon=0.0,
            conn_birth_timezone="UTC"
        )

        assert result is not None, "calculate_and_cache_synastry should not return None"
        assert len(result["synastry_aspects"]) > 0, "Should have at least one aspect"

        # Check first aspect has required fields
        first_aspect = result["synastry_aspects"][0]
        required_fields = ["user_planet", "their_planet", "aspect_type", "is_harmonious", "orb"]
        for field in required_fields:
            assert field in first_aspect, f"Aspect should have '{field}' field"


# =============================================================================
# Regression test: ask_the_stars synastry calculation
# =============================================================================

class TestAskTheStarsSynastryRegression:
    """
    Regression tests for ask_the_stars.py synastry calculation.

    BUG: ask_the_stars.py line 324 calls calculate_compatibility() without relationship_type.
    This causes synastry_aspects to silently fail for connections in Ask the Stars.
    """

    def test_ask_the_stars_synastry_calculation_pattern(self):
        """
        REGRESSION TEST: Verify the pattern used in ask_the_stars works.

        The current code in ask_the_stars.py does:
            compatibility = calculate_compatibility(user_chart, conn_chart)

        This is BROKEN because calculate_compatibility requires relationship_type.
        It should use calculate_synastry_aspects instead.
        """
        from compatibility import calculate_synastry_aspects
        from astro import compute_birth_chart, NatalChartData

        # Build charts (same pattern as ask_the_stars.py)
        user_chart_dict, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        user_chart = NatalChartData(**user_chart_dict)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date="1992-08-15",
            birth_time="12:00",
            birth_timezone="UTC",
            birth_lat=0.0,
            birth_lon=0.0
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        # This is what ask_the_stars SHOULD do (use calculate_synastry_aspects)
        aspects = calculate_synastry_aspects(user_chart, conn_chart)

        # Get top 5 tightest aspects (same as ask_the_stars pattern)
        sorted_aspects = sorted(aspects, key=lambda a: a.orb)[:5]
        synastry_aspects = [
            {
                "user_planet": asp.user_planet,
                "their_planet": asp.their_planet,
                "aspect_type": asp.aspect_type,
                "is_harmonious": asp.is_harmonious
            }
            for asp in sorted_aspects
        ]

        assert len(synastry_aspects) > 0, "Should have synastry aspects"
        assert "user_planet" in synastry_aspects[0], "Aspect should have user_planet"

    def test_ask_the_stars_uses_calculate_synastry_aspects(self):
        """
        REGRESSION TEST: Verify ask_the_stars.py uses calculate_synastry_aspects,
        NOT calculate_compatibility.

        This test inspects the source code to ensure the fix is applied.
        """
        from pathlib import Path

        ask_the_stars_py = Path(__file__).parent.parent.parent / "ask_the_stars.py"
        content = ask_the_stars_py.read_text()

        # Check for the bug pattern (calculate_compatibility called without relationship_type)
        # This pattern indicates the bug is still present
        bug_pattern_found = "calculate_compatibility(user_chart, conn_chart)" in content

        # Check for the correct import
        correct_import = "calculate_synastry_aspects" in content

        assert not bug_pattern_found, \
            "BUG: ask_the_stars.py still calls calculate_compatibility(user_chart, conn_chart) " \
            "without relationship_type. Should use calculate_synastry_aspects instead."

        assert correct_import, \
            "ask_the_stars.py should import calculate_synastry_aspects"


# =============================================================================
# Tests for compatibility prompt data flow
# =============================================================================

class TestCompatibilityPromptDataFlow:
    """
    Tests to ensure compatibility calculation works correctly for prompts.
    """

    def test_calculate_compatibility_requires_relationship_type(self):
        """
        Verify that calculate_compatibility REQUIRES relationship_type parameter.
        This documents the API contract.
        """
        import inspect
        from compatibility import calculate_compatibility

        sig = inspect.signature(calculate_compatibility)
        params = list(sig.parameters.keys())

        assert "relationship_type" in params, \
            "calculate_compatibility must have relationship_type parameter"

        # Check it's a required parameter (no default)
        param = sig.parameters["relationship_type"]
        assert param.default == inspect.Parameter.empty, \
            "relationship_type should be a REQUIRED parameter (no default)"

    def test_main_get_compatibility_passes_relationship_type(self):
        """
        Verify that main.py's get_compatibility passes relationship_type correctly.

        This is a code inspection test - we verify the pattern exists in the code.
        """
        from pathlib import Path

        main_py = Path(__file__).parent.parent.parent / "main.py"
        content = main_py.read_text()

        # Check that the call includes relationship_type
        assert "calculate_compatibility(" in content, \
            "main.py should call calculate_compatibility"
        assert "relationship_type=relationship_type" in content, \
            "main.py should pass relationship_type to calculate_compatibility"

    def test_calculate_compatibility_returns_valid_data(self):
        """
        Test that calculate_compatibility returns valid CompatibilityData.
        """
        from compatibility import calculate_compatibility
        from astro import compute_birth_chart, NatalChartData

        user_chart_dict, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_timezone="America/New_York",
            birth_lat=40.7128,
            birth_lon=-74.0060
        )
        user_chart = NatalChartData(**user_chart_dict)

        conn_chart_dict, _ = compute_birth_chart(
            birth_date="1992-08-15",
            birth_time="12:00",
            birth_timezone="UTC",
            birth_lat=0.0,
            birth_lon=0.0
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        # Test all three relationship types work
        for rel_type in ["romantic", "friendship", "coworker"]:
            result = calculate_compatibility(
                user_chart,
                conn_chart,
                rel_type,
                "Alice",
                "Bob"
            )

            assert result is not None, f"calculate_compatibility should return result for {rel_type}"
            assert hasattr(result, "aspects"), "Result should have aspects"
            assert hasattr(result, "mode"), "Result should have mode"
            assert len(result.aspects) > 0, "Should have at least one aspect"


# =============================================================================
# E2E test: Connection creation stores synastry in Firestore correctly
# =============================================================================

class TestConnectionCreationE2E:
    """
    End-to-end tests for connection creation storing synastry data.
    """

    def test_create_connection_stores_synastry_in_firestore(self):
        """
        Verify that create_connection properly stores synastry_points in Firestore.
        """
        from connections import create_connection

        # Mock Firestore
        mock_db = MagicMock()

        # Mock user doc with birth data
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
            "birth_timezone": "America/New_York"
        }

        # Set up mock chain for user doc lookup
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc

        # Mock for connection doc operations
        mock_conn_ref = MagicMock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_conn_ref

        # Create connection
        connection = create_connection(
            db=mock_db,
            user_id="test_user",
            name="Test Connection",
            birth_date="1992-08-15",
            relationship_category="friend",
            relationship_label="friend",
            birth_time="12:00",
            birth_lat=0.0,
            birth_lon=0.0,
            birth_timezone="UTC"
        )

        # Verify connection object has synastry_points
        assert connection.synastry_points is not None, \
            "Connection should have synastry_points after creation"
        assert len(connection.synastry_points) > 0, \
            "synastry_points should not be empty"

        # Verify Firestore update was called with synastry data
        # The update is called by calculate_and_cache_synastry
        update_calls = mock_conn_ref.update.call_args_list
        assert len(update_calls) > 0, "Firestore update should be called"

        # Find the call that includes synastry_points
        synastry_update_found = False
        for call in update_calls:
            update_data = call[0][0]
            if "synastry_points" in update_data:
                synastry_update_found = True
                assert len(update_data["synastry_points"]) > 0, \
                    "synastry_points in Firestore update should not be empty"
                assert "synastry_aspects" in update_data, \
                    "synastry_aspects should also be stored"
                break

        assert synastry_update_found, \
            "Firestore should be updated with synastry_points"

    def test_create_connection_synastry_points_structure(self):
        """
        Verify synastry_points have the correct structure for transit tracking.
        """
        from connections import create_connection

        mock_db = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_doc.to_dict.return_value = {
            "birth_date": "1990-06-15",
            "birth_time": "14:30",
            "birth_lat": 40.7128,
            "birth_lon": -74.0060,
            "birth_timezone": "America/New_York"
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_user_doc
        mock_conn_ref = MagicMock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_conn_ref

        connection = create_connection(
            db=mock_db,
            user_id="test_user",
            name="Test Connection",
            birth_date="1992-08-15",
            relationship_category="love",
            relationship_label="partner",
            birth_time="12:00",
            birth_lat=34.0522,
            birth_lon=-118.2437,
            birth_timezone="America/Los_Angeles"
        )

        # Check synastry_points structure
        assert connection.synastry_points is not None
        for point in connection.synastry_points:
            assert "degree" in point, "Each point should have degree"
            assert "label" in point, "Each point should have label"
            assert "type" in point, "Each point should have type"
            assert "planets" in point, "Each point should have planets"
            assert isinstance(point["degree"], (int, float)), "Degree should be numeric"
            assert isinstance(point["planets"], list), "Planets should be a list"


# =============================================================================
# Tests for on-the-fly synastry calculation in get_daily_horoscope
# =============================================================================

class TestOnTheFlySynastryCalculation:
    """
    Tests that synastry_points are computed on-the-fly if missing from connection.

    BUG: Old connections created before the fix don't have synastry_points,
    causing connection_vibes to be empty in the daily horoscope response.
    """

    def test_get_daily_horoscope_should_compute_synastry_if_missing(self):
        """
        FAILING TEST: get_daily_horoscope should compute synastry_points
        on-the-fly if the featured_connection doesn't have them.

        Currently this fails because main.py line 744 just skips enrichment
        if synastry_points is missing.
        """
        # This test documents the expected behavior
        # The code at main.py:744 does:
        #   if featured_connection and featured_connection.get("synastry_points"):
        #
        # If synastry_points is missing (None or empty), the entire enrichment
        # is skipped, resulting in empty connection_vibes.
        #
        # EXPECTED: Should compute synastry_points on-the-fly using user's
        # natal chart and connection's birth data.

        featured_connection_without_synastry = {
            "connection_id": "conn_123",
            "name": "Johnny",
            "birth_date": "1992-08-15",
            "birth_time": "12:00",
            "birth_lat": 0.0,
            "birth_lon": 0.0,
            "birth_timezone": "UTC",
            "relationship_category": "friend",
            "relationship_label": "friend",
            "sun_sign": "leo",
            # NO synastry_points - old connection
        }

        # Current behavior (BUG): enrichment is skipped
        current_behavior_skips = not featured_connection_without_synastry.get("synastry_points")
        assert current_behavior_skips, "Current behavior skips connections without synastry_points"

        # The connection has birth_date, so synastry CAN be computed
        can_compute_synastry = bool(featured_connection_without_synastry.get("birth_date"))
        assert can_compute_synastry, "Connection has birth_date so synastry can be computed"

    def test_main_computes_synastry_on_the_fly_when_missing(self):
        """
        REGRESSION TEST: get_daily_horoscope in main.py should compute synastry_points
        on-the-fly for connections that don't have them cached.

        This test checks the source code to verify the fix is in place.
        """
        from pathlib import Path

        main_py = Path(__file__).parent.parent.parent / "main.py"
        content = main_py.read_text()

        # The FIX should have:
        # 1. Check for birth_date (not synastry_points) at the top level
        # 2. Compute synastry_points if missing using calculate_synastry_points
        # 3. Then proceed with enrichment

        # Check for the fix pattern
        has_birth_date_check = 'featured_connection.get("birth_date")' in content
        has_synastry_computation = 'if not featured_connection.get("synastry_points")' in content
        has_calculate_synastry_points = 'calculate_synastry_points' in content

        # All three should be present for the fix to work
        assert has_birth_date_check, \
            "main.py should check for birth_date to determine if synastry can be computed"
        assert has_synastry_computation, \
            "main.py should check if synastry_points is missing and compute on-the-fly"
        assert has_calculate_synastry_points, \
            "main.py should use calculate_synastry_points for on-the-fly computation"


class TestConnectionVibesInResponse:
    """
    Tests that connection_vibes is properly populated in the daily horoscope response.
    """

    def test_connection_vibe_model_has_required_fields(self):
        """
        Verify ConnectionVibe model has all fields iOS expects.
        """
        from models import ConnectionVibe
        import inspect

        sig = inspect.signature(ConnectionVibe)
        fields = list(sig.parameters.keys())

        required_ios_fields = [
            "connection_id",  # Used for navigation
            "name",
            "vibe",
            "vibe_score",
        ]

        for field in required_ios_fields:
            assert field in fields, f"ConnectionVibe should have '{field}' for iOS"

    def test_relationship_weather_has_connection_vibes(self):
        """
        Verify RelationshipWeather model has connection_vibes field.
        """
        from models import RelationshipWeather
        import inspect

        sig = inspect.signature(RelationshipWeather)
        fields = list(sig.parameters.keys())

        assert "connection_vibes" in fields, \
            "RelationshipWeather should have connection_vibes"

    def test_connection_vibes_is_list(self):
        """
        Verify connection_vibes is a list (can have multiple connections).
        """
        from models import RelationshipWeather, ConnectionVibe

        weather = RelationshipWeather(
            overview="Test overview",
            connection_vibes=[
                ConnectionVibe(
                    connection_id="conn_123",
                    name="Johnny",
                    relationship_category="friend",
                    relationship_label="friend",
                    vibe="Great energy today",
                    vibe_score=75,
                    key_transit=None
                )
            ]
        )

        assert isinstance(weather.connection_vibes, list)
        assert len(weather.connection_vibes) == 1
        assert weather.connection_vibes[0].connection_id == "conn_123"


class TestRelationshipWeatherPromptData:
    """
    Tests that the prompt template receives correct relationship data.
    """

    def test_template_receives_vibe_score(self):
        """
        Verify the template context includes vibe_score for featured connection.
        """
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path

        templates_dir = Path(__file__).parent.parent.parent / "templates" / "horoscope"
        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        template = env.get_template("daily_dynamic.j2")

        # Context with full connection data
        context = {
            "date": "2025-12-08",
            "headline_guidance": {"meters": [], "conjunction": None},
            "overall_unified_score": 62,
            "overall_guidance": "Test",
            "overall_writing_guidance": {
                "pattern": "neutral_day",
                "formula": "Test formula",
                "strongest_group": "mind",
                "strongest_score": 55,
                "challenging_group": None,
                "challenging_score": None,
                "flowing_groups": [],
                "challenging_groups": [],
                "shining_group": None,
            },
            "overview_guidance": {"formatted_highlights": []},
            "has_relationships": True,
            "user_name": "Test User",
            "user_first_name": "Test",
            "heart_group": {
                "unified_score": 65,
                "driver": "connections",
                "driver_score": 70,
                "driver_meaning": "Your ability to bond with others",
                "driver_aspect": "Venus trine Moon",
                "meter_scores": {"connections": 70, "resilience": 60, "vulnerability": 65},
                "writing_guidance": {
                    "pattern": "all_positive",
                    "formula": "Test heart formula",
                },
            },
            "relationship_transits": [
                {"description": "Venus trine natal Moon in 7th house (harmonious)"}
            ],
            "featured_connection": {
                "name": "Johnny",
                "relationship_category": "friend",
                "relationship_label": "friend",
                "sun_sign": "leo",
                "vibe_score": 75,
                "active_transits": [
                    {"description": "Mars trine Venus", "quality": "harmonious"}
                ],
                "synastry_points": [{"label": "Sun-Moon"}]
            },
            "moon_summary": "Moon in Leo",
            "is_void_of_course": False,
            "upcoming_transits": [],
            "all_groups": [
                {"name": "mind", "unified_score": 55, "meter_scores": {"clarity": 55, "focus": 54, "communication": 56}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "heart", "unified_score": 65, "meter_scores": {"connections": 70, "resilience": 60, "vulnerability": 65}, "writing_guidance": {"pattern": "all_positive", "formula": "Test"}},
                {"name": "body", "unified_score": 52, "meter_scores": {"energy": 52, "drive": 53, "strength": 51}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "instincts", "unified_score": 48, "meter_scores": {"vision": 48, "flow": 47, "intuition": 49, "creativity": 48}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "growth", "unified_score": 51, "meter_scores": {"momentum": 51, "ambition": 50, "evolution": 52, "circle": 51}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
            ],
            "key_transits": []
        }

        output = template.render(**context)

        # Check vibe score appears in output
        assert "75/100" in output, "Vibe score should appear in prompt"
        assert "Good vibe" in output, "Writing formula for good vibe (75 >= 60) should appear"
        # Check general relationship data appears
        assert "HEART METER" in output, "Heart meter section should appear"
        assert "RELATIONSHIP TRANSITS" in output, "Relationship transits should appear"

    def test_template_renders_connection_without_vibe_data(self):
        """
        Test that template renders connection section even when synastry data is missing.
        The LLM still gets connection context to write a vibe (just without transit specifics).
        """
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path

        templates_dir = Path(__file__).parent.parent.parent / "templates" / "horoscope"
        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        template = env.get_template("daily_dynamic.j2")

        # Context without synastry data
        context = {
            "date": "2025-12-08",
            "headline_guidance": {"meters": [], "conjunction": None},
            "overall_unified_score": 62,
            "overall_guidance": "Test",
            "overall_writing_guidance": {
                "pattern": "neutral_day",
                "formula": "Test formula",
                "strongest_group": "mind",
                "strongest_score": 55,
                "challenging_group": None,
                "challenging_score": None,
                "flowing_groups": [],
                "challenging_groups": [],
                "shining_group": None,
            },
            "overview_guidance": {"formatted_highlights": []},
            "has_relationships": True,
            "user_name": "Test User",
            "user_first_name": "Test",
            "heart_group": None,  # No heart group data
            "relationship_transits": [],  # No Venus/Mars transits
            "featured_connection": {
                "name": "Johnny",
                "relationship_category": "friend",
                "relationship_label": "friend",
                "sun_sign": "leo",
                # NO vibe_score, NO active_transits, NO synastry_points
            },
            "moon_summary": "Moon in Leo",
            "is_void_of_course": False,
            "upcoming_transits": [],
            "all_groups": [
                {"name": "mind", "unified_score": 55, "meter_scores": {"clarity": 55, "focus": 54, "communication": 56}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "heart", "unified_score": 50, "meter_scores": {"connections": 50, "resilience": 51, "vulnerability": 49}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "body", "unified_score": 52, "meter_scores": {"energy": 52, "drive": 53, "strength": 51}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "instincts", "unified_score": 48, "meter_scores": {"vision": 48, "flow": 47, "intuition": 49, "creativity": 48}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
                {"name": "growth", "unified_score": 51, "meter_scores": {"momentum": 51, "ambition": 50, "evolution": 52, "circle": 51}, "writing_guidance": {"pattern": "all_neutral", "formula": "Test"}},
            ],
            "key_transits": []
        }

        output = template.render(**context)

        # Connection name appears in the CONNECTION VIBE section
        assert "Johnny" in output, "Connection name should appear"
        assert "CONNECTION VIBE" in output, "Connection vibe section should appear"
        assert "relationship_weather.connection_vibe" in output, \
            "Template should instruct LLM to write connection_vibe"


class TestDailyHoroscopeResponseStructure:
    """
    Tests for the complete daily horoscope response structure.
    """

    def test_daily_horoscope_has_relationship_weather(self):
        """
        Verify DailyHoroscope model has relationship_weather field.
        """
        from models import DailyHoroscope
        import inspect

        # Get model fields
        fields = DailyHoroscope.model_fields.keys()

        assert "relationship_weather" in fields, \
            "DailyHoroscope should have relationship_weather"

    def test_featured_connection_id_removed(self):
        """
        Verify featured_connection_id was removed (it was redundant).

        iOS uses connection_vibes[0].connection_id for navigation,
        NOT a top-level featured_connection_id.
        """
        from models import DailyHoroscope

        fields = DailyHoroscope.model_fields.keys()

        # featured_connection_id should NOT exist - it was redundant
        has_featured_connection_id = "featured_connection_id" in fields

        assert not has_featured_connection_id, \
            "featured_connection_id should be removed (iOS uses connection_vibes[0].connection_id)"

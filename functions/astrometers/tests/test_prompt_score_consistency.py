"""
Test score consistency between different parts of the daily horoscope prompt.

This catches bugs where different functions calculate group scores differently,
leading to mismatched numbers in the LLM prompt (e.g., "BODY: 55/100" in one
section but "BODY: 57.2/100" in another).

The bug this catches:
- all_groups uses calculate_group_scores_top_2 (Top-2 weighted)
- generate_overview_guidance was using simple average
- These produce different numbers for the same group
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from datetime import datetime
from astrometers.meters import (
    MeterReading,
    QualityLabel,
    generate_overview_guidance,
    select_featured_meters,
    get_meters,
)
from astrometers.meter_groups import (
    build_all_meter_groups,
    calculate_group_scores_top_2,
)
from astro import compute_birth_chart


# =============================================================================
# Mock Data Helpers
# =============================================================================

def create_mock_meter(
    meter_name: str,
    unified_score: float,
    intensity: float,
    harmony: float,
    group: str = "mind",
) -> MeterReading:
    """Create a mock MeterReading for testing."""
    if unified_score < 25:
        unified_quality = QualityLabel.CHALLENGING
    elif unified_score < 50:
        unified_quality = QualityLabel.TURBULENT
    elif unified_score < 75:
        unified_quality = QualityLabel.PEACEFUL
    else:
        unified_quality = QualityLabel.FLOWING

    return MeterReading(
        meter_name=meter_name,
        date=datetime(2025, 11, 2),
        group=group,
        unified_score=unified_score,
        unified_quality=unified_quality,
        intensity=intensity,
        harmony=harmony,
        state_label="Test",
        interpretation="Test interpretation",
        advice=["Test advice"],
        top_aspects=[],
        raw_scores={"dti": 0, "hqs": 0},
        additional_context={},
        trend=None
    )


class MockAllMetersReading:
    """Mock AllMetersReading with controlled scores to test consistency."""

    def __init__(self, meter_scores: dict[str, tuple[float, float, float]]):
        """
        Args:
            meter_scores: Dict of meter_name -> (unified_score, intensity, harmony)
        """
        self.date = datetime(2025, 11, 2)

        # Mind meters
        self.clarity = create_mock_meter("clarity", *meter_scores.get("clarity", (50, 50, 50)), "mind")
        self.focus = create_mock_meter("focus", *meter_scores.get("focus", (50, 50, 50)), "mind")
        self.communication = create_mock_meter("communication", *meter_scores.get("communication", (50, 50, 50)), "mind")

        # Heart meters
        self.resilience = create_mock_meter("resilience", *meter_scores.get("resilience", (50, 50, 50)), "heart")
        self.connections = create_mock_meter("connections", *meter_scores.get("connections", (50, 50, 50)), "heart")
        self.vulnerability = create_mock_meter("vulnerability", *meter_scores.get("vulnerability", (50, 50, 50)), "heart")

        # Body meters
        self.energy = create_mock_meter("energy", *meter_scores.get("energy", (50, 50, 50)), "body")
        self.drive = create_mock_meter("drive", *meter_scores.get("drive", (50, 50, 50)), "body")
        self.strength = create_mock_meter("strength", *meter_scores.get("strength", (50, 50, 50)), "body")

        # Instincts meters
        self.vision = create_mock_meter("vision", *meter_scores.get("vision", (50, 50, 50)), "instincts")
        self.flow = create_mock_meter("flow", *meter_scores.get("flow", (50, 50, 50)), "instincts")
        self.intuition = create_mock_meter("intuition", *meter_scores.get("intuition", (50, 50, 50)), "instincts")
        self.creativity = create_mock_meter("creativity", *meter_scores.get("creativity", (50, 50, 50)), "instincts")

        # Growth meters
        self.momentum = create_mock_meter("momentum", *meter_scores.get("momentum", (50, 50, 50)), "growth")
        self.ambition = create_mock_meter("ambition", *meter_scores.get("ambition", (50, 50, 50)), "growth")
        self.evolution = create_mock_meter("evolution", *meter_scores.get("evolution", (50, 50, 50)), "growth")
        self.circle = create_mock_meter("circle", *meter_scores.get("circle", (50, 50, 50)), "growth")

        # Overall scores (mock as MeterReading)
        self.overall_intensity = create_mock_meter("overall_intensity", 50, 50, 50, "growth")
        self.overall_harmony = create_mock_meter("overall_harmony", 50, 50, 50, "growth")
        self.overall_unified_quality = QualityLabel.PEACEFUL
        self.key_aspects = []


# =============================================================================
# Score Consistency Tests
# =============================================================================

class TestPromptScoreConsistency:
    """
    Test that group scores are consistent across different functions.

    The daily horoscope prompt has multiple sections that show group scores:
    1. [ALL GROUPS - reference only] - from all_groups variable
    2. === FOR daily_overview === - from overview_guidance variable

    Both must show the same numbers for the same groups.
    """

    def test_overview_guidance_uses_top2_weighted_scoring(self):
        """
        Test that generate_overview_guidance uses calculate_group_scores_top_2.

        This is the core test that catches the bug where overview_guidance
        used simple averaging while all_groups used Top-2 weighted.
        """
        # Create meters with different scores to expose averaging vs Top-2 differences
        # The key is having one high-intensity meter and others with different scores
        meter_scores = {
            # Body group: high intensity drive, lower energy and strength
            "energy": (40, 30, 45),      # low intensity
            "drive": (70, 80, 75),       # HIGH intensity - should dominate Top-2
            "strength": (50, 60, 55),    # medium intensity
        }

        mock_meters = MockAllMetersReading(meter_scores)

        # Get the body group meters
        body_meters = [mock_meters.energy, mock_meters.drive, mock_meters.strength]

        # Calculate using Top-2 weighted (the correct method)
        top2_scores = calculate_group_scores_top_2(body_meters)
        top2_unified = top2_scores["unified_score"]

        # Calculate simple average (the buggy method)
        simple_avg = sum(m.unified_score for m in body_meters) / len(body_meters)

        # These should be different due to intensity weighting
        # Top-2 weights by intensity, so high-intensity drive (70) dominates
        # Simple avg = (40 + 70 + 50) / 3 = 53.3
        print(f"Top-2 weighted score: {top2_unified}")
        print(f"Simple average score: {simple_avg}")

        # Now test that generate_overview_guidance uses Top-2
        featured_list = [{
            "meter": mock_meters.drive,
            "direction": "flowing",
        }]
        headline_guidance = {"instruction": "Test", "conjunction": "and"}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        # Find body group in highlights
        body_highlight = None
        for h in overview["highlights"]:
            if h["group"] == "body":
                body_highlight = h
                break

        if body_highlight:
            overview_score = body_highlight["group_score"]
            print(f"Overview guidance score: {overview_score}")

            # The score should match Top-2, not simple average
            assert abs(overview_score - top2_unified) < 0.1, \
                f"Overview score {overview_score} should match Top-2 score {top2_unified}, not simple avg {simple_avg}"

    def test_all_groups_and_overview_guidance_match(self):
        """
        Test that all_groups and overview_guidance show identical scores.

        This simulates what happens in llm.py generate_daily_horoscope():
        - meter_groups = build_all_meter_groups(...)
        - all_groups is built from meter_groups
        - overview_guidance = generate_overview_guidance(...)

        Both should show the same scores for the same groups.
        """
        # Create varied scores across all groups
        meter_scores = {
            # Mind: varied intensities
            "clarity": (65, 70, 68),
            "focus": (45, 40, 48),
            "communication": (55, 55, 56),
            # Heart: low scores
            "resilience": (25, 30, 22),
            "connections": (20, 25, 18),
            "vulnerability": (30, 35, 28),
            # Body: high variability
            "energy": (40, 30, 45),
            "drive": (70, 80, 75),
            "strength": (50, 60, 55),
            # Instincts: medium
            "vision": (55, 55, 56),
            "flow": (50, 50, 51),
            "intuition": (45, 45, 46),
            "creativity": (60, 60, 61),
            # Growth: varied
            "momentum": (65, 70, 63),
            "ambition": (55, 50, 58),
            "evolution": (50, 45, 53),
            "circle": (45, 40, 48),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        # Build meter_groups (as done in llm.py)
        meter_groups = build_all_meter_groups(mock_meters, llm_interpretations=None)

        # Build all_groups dict (as done in llm.py)
        all_groups_scores = {}
        for group_name, group_data in meter_groups.items():
            all_groups_scores[group_name] = round(group_data["scores"]["unified_score"], 1)

        # Build overview_guidance
        featured_list = [{
            "meter": mock_meters.drive,
            "direction": "flowing",
        }]
        headline_guidance = {"instruction": "Test", "conjunction": "and"}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        # Build overview_scores dict
        overview_scores = {}
        for h in overview["highlights"]:
            overview_scores[h["group"]] = h["group_score"]

        # Check that all groups in overview match all_groups
        # Note: overview uses integer rounding, all_groups uses 1 decimal place
        # So tolerance should be 1.0 to account for rounding difference
        print("\nScore comparison:")
        for group_name in overview_scores:
            all_groups_score = all_groups_scores[group_name]
            overview_score = overview_scores[group_name]
            print(f"  {group_name}: all_groups={all_groups_score}, overview={overview_score}")

            assert abs(all_groups_score - overview_score) < 1.0, \
                f"{group_name} mismatch: all_groups={all_groups_score}, overview={overview_score}"

    def test_driver_meter_consistency(self):
        """
        Test that the driver meter is selected consistently.

        Both all_groups and overview_guidance should identify the same
        driver meter for each group (the highest-intensity meter).
        """
        # Create meters where one clearly dominates by intensity
        meter_scores = {
            "energy": (40, 20, 45),      # low intensity
            "drive": (70, 90, 75),       # VERY HIGH intensity - clear driver
            "strength": (50, 50, 55),    # medium intensity
        }

        mock_meters = MockAllMetersReading(meter_scores)
        body_meters = [mock_meters.energy, mock_meters.drive, mock_meters.strength]

        # Get driver from Top-2 calculation
        top2_scores = calculate_group_scores_top_2(body_meters)
        expected_driver = top2_scores["driver"]

        # Get driver from overview_guidance
        featured_list = [{
            "meter": mock_meters.drive,
            "direction": "flowing",
        }]
        headline_guidance = {"instruction": "Test", "conjunction": "and"}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        body_highlight = None
        for h in overview["highlights"]:
            if h["group"] == "body":
                body_highlight = h
                break

        if body_highlight:
            overview_driver = body_highlight["driver_meter"]
            assert overview_driver == expected_driver, \
                f"Driver mismatch: expected {expected_driver}, got {overview_driver}"


class TestRealChartConsistency:
    """Test with real chart data to ensure consistency in production-like scenarios."""

    def test_real_chart_score_consistency(self):
        """
        Test score consistency using actual chart calculations.

        This is an integration test that uses real astrometer calculations
        to verify the fix works end-to-end.
        """
        # Use a real chart
        natal_chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_lat=40.7128,
            birth_lon=-74.0060,
            birth_timezone="America/New_York"
        )

        transit_chart, _ = compute_birth_chart(
            birth_date="2025-01-15",
            birth_time="12:00"
        )

        # Calculate all meters
        all_meters = get_meters(
            natal_chart=natal_chart,
            transit_chart=transit_chart,
            date=datetime(2025, 1, 15),
            user_id="test_user_123"
        )

        # Build meter_groups
        meter_groups = build_all_meter_groups(all_meters, llm_interpretations=None)

        # Build overview_guidance using select_featured_meters for realistic featured_list
        featured = select_featured_meters(
            all_meters=all_meters,
            user_id="test_user_123",
            date="2025-01-15",
        )

        overview = generate_overview_guidance(
            all_meters=all_meters,
            featured_list=featured["featured_list"],
            headline_guidance=featured.get("headline_guidance", {}),
        )

        # Compare scores for all groups present in overview
        # Note: overview uses integer rounding, meter_groups uses 1 decimal place
        # So tolerance should be 1.0 to account for rounding difference
        print("\nReal chart score comparison:")
        for h in overview["highlights"]:
            group_name = h["group"]
            overview_score = h["group_score"]
            all_groups_score = round(meter_groups[group_name]["scores"]["unified_score"], 1)

            print(f"  {group_name}: meter_groups={all_groups_score}, overview={overview_score}")

            assert abs(all_groups_score - overview_score) < 1.0, \
                f"{group_name} score mismatch in real chart: " \
                f"meter_groups={all_groups_score}, overview={overview_score}"


class TestPromptDeterminism:
    """
    Test that prompt generation is deterministic for the same user/day.

    The prompt should be identical when generated multiple times for the
    same user on the same day. Any randomness must be seeded by user_id + date.
    """

    def test_select_featured_meters_is_deterministic(self):
        """
        select_featured_meters should return identical results for same user/day.

        This function uses weighted random selection, but seeds RNG with
        user_id + date, so results must be reproducible.
        """
        meter_scores = {
            "clarity": (65, 70, 68),
            "focus": (45, 40, 48),
            "communication": (55, 55, 56),
            "resilience": (25, 30, 22),
            "connections": (20, 25, 18),
            "vulnerability": (30, 35, 28),
            "energy": (40, 30, 45),
            "drive": (70, 80, 75),
            "strength": (50, 60, 55),
            "vision": (55, 55, 56),
            "flow": (50, 50, 51),
            "intuition": (45, 45, 46),
            "creativity": (60, 60, 61),
            "momentum": (65, 70, 63),
            "ambition": (55, 50, 58),
            "evolution": (50, 45, 53),
            "circle": (45, 40, 48),
        }

        mock_meters = MockAllMetersReading(meter_scores)
        user_id = "test_user_determinism_123"
        date = "2025-01-15"

        # Call multiple times
        results = []
        for i in range(5):
            featured = select_featured_meters(
                all_meters=mock_meters,
                user_id=user_id,
                date=date,
            )
            results.append(featured)

        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], start=2):
            # Compare featured_groups
            assert result["featured_groups"] == first_result["featured_groups"], \
                f"Call {i}: featured_groups differs from call 1"

            # Compare featured meter names
            first_meters = [m["meter"].meter_name for m in first_result["featured_list"]]
            this_meters = [m["meter"].meter_name for m in result["featured_list"]]
            assert this_meters == first_meters, \
                f"Call {i}: featured meters {this_meters} differs from call 1 {first_meters}"

            # Compare headline guidance
            assert result["headline_guidance"] == first_result["headline_guidance"], \
                f"Call {i}: headline_guidance differs from call 1"

        print(f"All 5 calls returned identical results: {first_result['featured_groups']}")

    def test_select_featured_meters_varies_by_user(self):
        """Different users should get different featured meters (with high probability)."""
        meter_scores = {
            "clarity": (65, 70, 68),
            "focus": (45, 40, 48),
            "communication": (55, 55, 56),
            "resilience": (25, 30, 22),
            "connections": (20, 25, 18),
            "vulnerability": (30, 35, 28),
            "energy": (40, 30, 45),
            "drive": (70, 80, 75),
            "strength": (50, 60, 55),
            "vision": (55, 55, 56),
            "flow": (50, 50, 51),
            "intuition": (45, 45, 46),
            "creativity": (60, 60, 61),
            "momentum": (65, 70, 63),
            "ambition": (55, 50, 58),
            "evolution": (50, 45, 53),
            "circle": (45, 40, 48),
        }

        mock_meters = MockAllMetersReading(meter_scores)
        date = "2025-01-15"

        # Get results for 10 different users
        user_results = {}
        for i in range(10):
            user_id = f"user_{i}_test"
            featured = select_featured_meters(
                all_meters=mock_meters,
                user_id=user_id,
                date=date,
            )
            meters = tuple(m["meter"].meter_name for m in featured["featured_list"])
            user_results[user_id] = meters

        # Check that we have some variety (not all identical)
        unique_results = set(user_results.values())
        print(f"Unique featured meter combinations across 10 users: {len(unique_results)}")
        print(f"Results: {unique_results}")

        # With weighted random, we expect some variety
        # (though extreme scores will dominate, so not guaranteed to be 10 unique)
        assert len(unique_results) >= 2, \
            "Expected at least some variety across different users"

    def test_select_featured_meters_varies_by_date(self):
        """Same user on different days should get different featured meters."""
        meter_scores = {
            "clarity": (65, 70, 68),
            "focus": (45, 40, 48),
            "communication": (55, 55, 56),
            "resilience": (25, 30, 22),
            "connections": (20, 25, 18),
            "vulnerability": (30, 35, 28),
            "energy": (40, 30, 45),
            "drive": (70, 80, 75),
            "strength": (50, 60, 55),
            "vision": (55, 55, 56),
            "flow": (50, 50, 51),
            "intuition": (45, 45, 46),
            "creativity": (60, 60, 61),
            "momentum": (65, 70, 63),
            "ambition": (55, 50, 58),
            "evolution": (50, 45, 53),
            "circle": (45, 40, 48),
        }

        mock_meters = MockAllMetersReading(meter_scores)
        user_id = "consistent_user_123"

        # Get results for 10 different dates
        date_results = {}
        for day in range(1, 11):
            date = f"2025-01-{day:02d}"
            featured = select_featured_meters(
                all_meters=mock_meters,
                user_id=user_id,
                date=date,
            )
            meters = tuple(m["meter"].meter_name for m in featured["featured_list"])
            date_results[date] = meters

        # Check variety across dates
        unique_results = set(date_results.values())
        print(f"Unique featured meter combinations across 10 days: {len(unique_results)}")
        print(f"Results: {unique_results}")

        assert len(unique_results) >= 2, \
            "Expected at least some variety across different dates"

    def test_overview_guidance_is_deterministic(self):
        """generate_overview_guidance should be deterministic (no randomness)."""
        meter_scores = {
            "clarity": (69, 50, 70),
            "focus": (69, 50, 70),
            "communication": (69, 50, 70),
            "resilience": (12, 40, 15),
            "connections": (20, 35, 22),
            "vulnerability": (22, 30, 24),
            "energy": (34, 45, 36),
            "drive": (34, 45, 36),
            "strength": (34, 45, 36),
            "vision": (46, 50, 47),
            "flow": (46, 50, 47),
            "intuition": (46, 50, 47),
            "creativity": (46, 50, 47),
            "momentum": (43, 50, 44),
            "ambition": (43, 50, 44),
            "evolution": (39, 50, 40),
            "circle": (43, 50, 44),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        featured_list = [
            {"meter": mock_meters.intuition, "direction": "pushing"},
            {"meter": mock_meters.evolution, "direction": "pushing"},
        ]
        headline_guidance = {"instruction": "Test", "conjunction": "but"}

        # Call multiple times
        results = []
        for _ in range(5):
            overview = generate_overview_guidance(
                all_meters=mock_meters,
                featured_list=featured_list,
                headline_guidance=headline_guidance,
            )
            results.append(overview)

        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], start=2):
            first_groups = [h["group"] for h in first_result["highlights"]]
            this_groups = [h["group"] for h in result["highlights"]]
            assert this_groups == first_groups, \
                f"Call {i}: highlights {this_groups} differs from call 1 {first_groups}"

            first_scores = [h["group_score"] for h in first_result["highlights"]]
            this_scores = [h["group_score"] for h in result["highlights"]]
            assert this_scores == first_scores, \
                f"Call {i}: scores {this_scores} differs from call 1 {first_scores}"

        print(f"All 5 calls returned identical overview highlights")

    def test_full_prompt_determinism_with_real_chart(self):
        """
        Full integration test: same user + date should produce identical prompt inputs.

        This tests the entire chain:
        1. get_meters
        2. select_featured_meters
        3. generate_overview_guidance
        4. build_all_meter_groups
        """
        from astro import compute_birth_chart

        # Use a real chart
        natal_chart, _ = compute_birth_chart(
            birth_date="1990-06-15",
            birth_time="14:30",
            birth_lat=40.7128,
            birth_lon=-74.0060,
            birth_timezone="America/New_York"
        )

        transit_chart, _ = compute_birth_chart(
            birth_date="2025-01-15",
            birth_time="12:00"
        )

        user_id = "determinism_test_user"
        date = "2025-01-15"
        date_obj = datetime(2025, 1, 15)

        # Run the full chain multiple times
        results = []
        for _ in range(3):
            # Step 1: Calculate meters
            all_meters = get_meters(
                natal_chart=natal_chart,
                transit_chart=transit_chart,
                date=date_obj,
                user_id=user_id
            )

            # Step 2: Select featured meters
            featured = select_featured_meters(
                all_meters=all_meters,
                user_id=user_id,
                date=date,
            )

            # Step 3: Generate overview guidance
            overview = generate_overview_guidance(
                all_meters=all_meters,
                featured_list=featured["featured_list"],
                headline_guidance=featured.get("headline_guidance", {}),
            )

            # Step 4: Build meter groups
            meter_groups = build_all_meter_groups(all_meters, llm_interpretations=None)

            results.append({
                "featured_groups": featured["featured_groups"],
                "featured_meters": [m["meter"].meter_name for m in featured["featured_list"]],
                "headline_guidance": featured.get("headline_guidance", {}),
                "overview_highlights": [h["group"] for h in overview["highlights"]],
                "group_scores": {name: data["scores"]["unified_score"] for name, data in meter_groups.items()},
            })

        # Compare all results
        first = results[0]
        for i, result in enumerate(results[1:], start=2):
            assert result["featured_groups"] == first["featured_groups"], \
                f"Run {i}: featured_groups mismatch"
            assert result["featured_meters"] == first["featured_meters"], \
                f"Run {i}: featured_meters mismatch"
            assert result["headline_guidance"] == first["headline_guidance"], \
                f"Run {i}: headline_guidance mismatch"
            assert result["overview_highlights"] == first["overview_highlights"], \
                f"Run {i}: overview_highlights mismatch"
            assert result["group_scores"] == first["group_scores"], \
                f"Run {i}: group_scores mismatch"

        print("Full prompt chain is deterministic:")
        print(f"  Featured groups: {first['featured_groups']}")
        print(f"  Featured meters: {first['featured_meters']}")
        print(f"  Overview highlights: {first['overview_highlights']}")


class TestHeadlineOverviewConsistency:
    """
    Test that overview provides additional coverage beyond headline.

    The overview should:
    1. NOT include headline groups (they're already covered in headline_guidance)
    2. Add the most extreme non-headline groups for broader coverage
    3. Total coverage (headline + overview) should be ~3 groups
    """

    def test_headline_groups_excluded_from_overview(self):
        """
        Groups featured in headline should NOT appear in overview.

        The LLM already has headline groups in headline_guidance section.
        Overview should add NEW groups for broader coverage.
        """
        meter_scores = {
            # Mind: moderate (69)
            "clarity": (69, 50, 70),
            "focus": (69, 50, 70),
            "communication": (69, 50, 70),
            # Heart: very low (18) - MOST EXTREME
            "resilience": (12, 40, 15),
            "connections": (20, 35, 22),
            "vulnerability": (22, 30, 24),
            # Body: low-ish (34)
            "energy": (34, 45, 36),
            "drive": (34, 45, 36),
            "strength": (34, 45, 36),
            # Instincts: near neutral (41) - IN HEADLINE
            "vision": (41, 50, 42),
            "flow": (41, 50, 42),
            "intuition": (41, 50, 42),
            "creativity": (41, 50, 42),
            # Growth: near neutral (62) - IN HEADLINE
            "momentum": (62, 50, 63),
            "ambition": (62, 50, 63),
            "evolution": (62, 50, 63),
            "circle": (62, 50, 63),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        # Headline picks INSTINCTS and GROWTH (near-neutral but featured)
        featured_list = [
            {"meter": mock_meters.vision, "direction": "pushing"},
            {"meter": mock_meters.evolution, "direction": "flowing"},
        ]
        headline_guidance = {"instruction": "Test", "conjunction": "but"}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        highlight_groups = [h["group"] for h in overview["highlights"]]
        print(f"Headline groups: instincts, growth")
        print(f"Overview highlights: {highlight_groups}")

        # Headline groups should NOT be in overview (already covered)
        assert "instincts" not in highlight_groups, \
            "INSTINCTS is in headline, should not be duplicated in overview"
        assert "growth" not in highlight_groups, \
            "GROWTH is in headline, should not be duplicated in overview"

        # Should include HEART (most extreme not in headline)
        assert "heart" in highlight_groups, \
            "HEART (score 18, most extreme) should be in overview"

    def test_overview_adds_extreme_non_headline_groups(self):
        """
        Overview should add most extreme non-headline groups for coverage.
        """
        meter_scores = {
            # Mind: high (80) - IN HEADLINE
            "clarity": (80, 60, 82),
            "focus": (80, 60, 82),
            "communication": (80, 60, 82),
            # Heart: very low (15) - EXTREME, should be added
            "resilience": (15, 50, 12),
            "connections": (15, 50, 12),
            "vulnerability": (15, 50, 12),
            # Body: low (25) - also extreme
            "energy": (25, 50, 27),
            "drive": (25, 50, 27),
            "strength": (25, 50, 27),
            # Instincts: neutral (50)
            "vision": (50, 50, 51),
            "flow": (50, 50, 51),
            "intuition": (50, 50, 51),
            "creativity": (50, 50, 51),
            # Growth: neutral (50)
            "momentum": (50, 50, 51),
            "ambition": (50, 50, 51),
            "evolution": (50, 50, 51),
            "circle": (50, 50, 51),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        # Headline has just MIND
        featured_list = [
            {"meter": mock_meters.clarity, "direction": "flowing"},
        ]
        headline_guidance = {"instruction": "Test", "conjunction": None}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        highlight_groups = [h["group"] for h in overview["highlights"]]
        print(f"Headline group: mind")
        print(f"Overview highlights: {highlight_groups}")

        # Headline group should NOT be in overview
        assert "mind" not in highlight_groups, \
            "MIND is in headline, should not be duplicated in overview"

        # Should have 2 extreme non-headline groups (since headline has 1)
        assert "heart" in highlight_groups, \
            "HEART (score 15) should be in overview as most extreme"
        assert "body" in highlight_groups, \
            "BODY (score 25) should be in overview as second most extreme"


class TestScoreRounding:
    """Test that all scores shown to LLM are rounded integers."""

    def test_headline_guidance_scores_are_rounded(self):
        """Scores in headline_guidance.meters must be rounded integers."""
        from astrometers.meters import generate_headline_guidance

        # Create meters with decimal scores
        meter_scores = {
            "clarity": (65.7, 70.3, 68.9),
            "focus": (45.2, 40.8, 48.1),
            "communication": (55.5, 55.5, 56.5),
            "resilience": (25.3, 30.7, 22.1),
            "connections": (20.9, 25.4, 18.6),
            "vulnerability": (30.2, 35.8, 28.3),
            "energy": (40.1, 30.9, 45.7),
            "drive": (70.8, 80.2, 75.4),
            "strength": (50.3, 60.7, 55.1),
            "vision": (55.6, 55.4, 56.2),
            "flow": (50.9, 50.1, 51.8),
            "intuition": (45.4, 45.6, 46.2),
            "creativity": (60.7, 60.3, 61.9),
            "momentum": (65.2, 70.8, 63.4),
            "ambition": (55.9, 50.1, 58.7),
            "evolution": (50.4, 45.6, 53.2),
            "circle": (45.1, 40.9, 48.7),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        featured_list = [
            {"meter": mock_meters.drive, "direction": "flowing"},
            {"meter": mock_meters.resilience, "direction": "pushing"},
        ]

        headline = generate_headline_guidance(featured_list)

        # Check all scores are integers
        for m in headline["meters"]:
            score = m["score"]
            assert score == int(score), \
                f"Score {score} for {m['meter_name']} should be rounded integer"
            print(f"{m['meter_name']}: {score}")

    def test_overview_guidance_scores_are_rounded(self):
        """Scores in overview_guidance must be rounded integers."""
        meter_scores = {
            "clarity": (69.7, 50.3, 70.9),
            "focus": (69.2, 50.8, 70.1),
            "communication": (69.5, 50.5, 70.5),
            "resilience": (12.3, 40.7, 15.1),
            "connections": (20.9, 35.4, 22.6),
            "vulnerability": (22.2, 30.8, 24.3),
            "energy": (34.1, 45.9, 36.7),
            "drive": (34.8, 45.2, 36.4),
            "strength": (34.3, 45.7, 36.1),
            "vision": (46.6, 50.4, 47.2),
            "flow": (46.9, 50.1, 47.8),
            "intuition": (46.4, 50.6, 47.2),
            "creativity": (46.7, 50.3, 47.9),
            "momentum": (43.2, 50.8, 44.4),
            "ambition": (43.9, 50.1, 44.7),
            "evolution": (39.4, 50.6, 40.2),
            "circle": (43.1, 50.9, 44.7),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        featured_list = [
            {"meter": mock_meters.intuition, "direction": "pushing"},
        ]
        headline_guidance = {"instruction": "Test", "conjunction": None}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        # Check all scores in highlights are integers
        for h in overview["highlights"]:
            group_score = h["group_score"]
            driver_score = h["driver_score"]

            assert group_score == int(group_score), \
                f"Group score {group_score} for {h['group']} should be rounded"
            assert driver_score == int(driver_score), \
                f"Driver score {driver_score} for {h['driver_meter']} should be rounded"

            print(f"{h['group']}: {group_score}, driver {h['driver_meter']}: {driver_score}")


class TestOverviewGuidanceSelection:
    """
    Test that overview guidance picks the most extreme groups not in headline.

    The logic should be:
    - If headline has 2 meters: add 1 most extreme non-headline group
    - If headline has 1 meter: add 2 most extreme non-headline groups
    - Goal: always cover ~3 groups total between headline + overview
    """

    def test_overview_picks_extreme_groups_not_in_headline(self):
        """
        When headline picks near-neutral groups, overview should still
        cover the most extreme groups.

        This is the core bug fix: if headline randomly picks INSTINCTS (46)
        and GROWTH (43), overview should pick HEART (18) as the most extreme.
        """
        # Create meters that simulate the bug scenario:
        # - HEART is very low (18) - most extreme
        # - INSTINCTS and GROWTH are near neutral (46, 43)
        # - MIND is moderate (69)
        # - BODY is low-ish (34)
        meter_scores = {
            # Mind: moderate (69)
            "clarity": (69, 50, 70),
            "focus": (69, 50, 70),
            "communication": (69, 50, 70),
            # Heart: very low (18) - MOST EXTREME
            "resilience": (12, 40, 15),
            "connections": (20, 35, 22),
            "vulnerability": (22, 30, 24),
            # Body: low-ish (34)
            "energy": (34, 45, 36),
            "drive": (34, 45, 36),
            "strength": (34, 45, 36),
            # Instincts: near neutral (46)
            "vision": (46, 50, 47),
            "flow": (46, 50, 47),
            "intuition": (46, 50, 47),
            "creativity": (46, 50, 47),
            # Growth: near neutral (43)
            "momentum": (43, 50, 44),
            "ambition": (43, 50, 44),
            "evolution": (39, 50, 40),
            "circle": (43, 50, 44),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        # Simulate headline picking INSTINCTS and GROWTH (near-neutral)
        featured_list = [
            {"meter": mock_meters.intuition, "direction": "pushing"},
            {"meter": mock_meters.evolution, "direction": "pushing"},
        ]
        headline_guidance = {"instruction": "Test", "conjunction": "but"}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        # With 2 headline meters, we should get 1 additional group
        # That group should be the most extreme NOT in headline
        # HEART (18) is most extreme (distance 32 from 50)
        # BODY (34) is second (distance 16 from 50)
        # MIND (69) is third (distance 19 from 50)

        highlight_groups = [h["group"] for h in overview["highlights"]]
        print(f"Headline groups: instincts, growth")
        print(f"Overview highlights: {highlight_groups}")

        # Overview should include HEART (most extreme not in headline)
        assert "heart" in highlight_groups, \
            f"HEART (score 18, most extreme) should be in overview, got: {highlight_groups}"

        # Should NOT include headline groups (instincts, growth)
        assert "instincts" not in highlight_groups, \
            "INSTINCTS is in headline, should not be in overview"
        assert "growth" not in highlight_groups, \
            "GROWTH is in headline, should not be in overview"

    def test_overview_adds_2_when_headline_has_1(self):
        """When headline has 1 meter, overview should add 2 most extreme groups."""
        meter_scores = {
            # Mind: very high (85)
            "clarity": (85, 60, 88),
            "focus": (85, 60, 88),
            "communication": (85, 60, 88),
            # Heart: very low (15)
            "resilience": (15, 50, 12),
            "connections": (15, 50, 12),
            "vulnerability": (15, 50, 12),
            # Body: low (30)
            "energy": (30, 50, 32),
            "drive": (30, 50, 32),
            "strength": (30, 50, 32),
            # Instincts: neutral (50)
            "vision": (50, 50, 51),
            "flow": (50, 50, 51),
            "intuition": (50, 50, 51),
            "creativity": (50, 50, 51),
            # Growth: neutral (50)
            "momentum": (50, 50, 51),
            "ambition": (50, 50, 51),
            "evolution": (50, 50, 51),
            "circle": (50, 50, 51),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        # Headline has just 1 meter (from MIND)
        featured_list = [
            {"meter": mock_meters.clarity, "direction": "flowing"},
        ]
        headline_guidance = {"instruction": "Test", "conjunction": None}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        highlight_groups = [h["group"] for h in overview["highlights"]]
        print(f"Headline group: mind")
        print(f"Overview highlights: {highlight_groups}")

        # With 1 headline meter, we should get 2 additional groups
        assert len(highlight_groups) == 2, \
            f"With 1 headline meter, should have 2 overview highlights, got {len(highlight_groups)}"

        # Should include HEART (15, distance 35) and BODY (30, distance 20)
        # MIND is in headline, INSTINCTS/GROWTH are neutral (distance 0)
        assert "heart" in highlight_groups, \
            f"HEART (score 15) should be in overview, got: {highlight_groups}"
        assert "body" in highlight_groups, \
            f"BODY (score 30) should be in overview, got: {highlight_groups}"

    def test_overview_adds_1_when_headline_has_2(self):
        """When headline has 2 meters from different groups, overview should add 1."""
        meter_scores = {
            # Mind: high (80)
            "clarity": (80, 60, 82),
            "focus": (80, 60, 82),
            "communication": (80, 60, 82),
            # Heart: very low (10)
            "resilience": (10, 50, 8),
            "connections": (10, 50, 8),
            "vulnerability": (10, 50, 8),
            # Body: low (25)
            "energy": (25, 50, 27),
            "drive": (25, 50, 27),
            "strength": (25, 50, 27),
            # Instincts: neutral (50)
            "vision": (50, 50, 51),
            "flow": (50, 50, 51),
            "intuition": (50, 50, 51),
            "creativity": (50, 50, 51),
            # Growth: moderate (60)
            "momentum": (60, 50, 62),
            "ambition": (60, 50, 62),
            "evolution": (60, 50, 62),
            "circle": (60, 50, 62),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        # Headline has 2 meters from MIND and GROWTH
        featured_list = [
            {"meter": mock_meters.clarity, "direction": "flowing"},
            {"meter": mock_meters.momentum, "direction": "flowing"},
        ]
        headline_guidance = {"instruction": "Test", "conjunction": "and"}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        highlight_groups = [h["group"] for h in overview["highlights"]]
        print(f"Headline groups: mind, growth")
        print(f"Overview highlights: {highlight_groups}")

        # With 2 headline meters, we should get 1 additional group
        assert len(highlight_groups) == 1, \
            f"With 2 headline meters, should have 1 overview highlight, got {len(highlight_groups)}"

        # Should include HEART (10, most extreme not in headline)
        assert "heart" in highlight_groups, \
            f"HEART (score 10) should be in overview, got: {highlight_groups}"

    def test_overview_excludes_neutral_groups(self):
        """Groups near neutral (40-60) should not be included in overview."""
        meter_scores = {
            # Mind: neutral (50)
            "clarity": (50, 50, 51),
            "focus": (50, 50, 51),
            "communication": (50, 50, 51),
            # Heart: neutral (55)
            "resilience": (55, 50, 56),
            "connections": (55, 50, 56),
            "vulnerability": (55, 50, 56),
            # Body: neutral (45)
            "energy": (45, 50, 46),
            "drive": (45, 50, 46),
            "strength": (45, 50, 46),
            # Instincts: neutral (50)
            "vision": (50, 50, 51),
            "flow": (50, 50, 51),
            "intuition": (50, 50, 51),
            "creativity": (50, 50, 51),
            # Growth: high (75) - only interesting one
            "momentum": (75, 60, 77),
            "ambition": (75, 60, 77),
            "evolution": (75, 60, 77),
            "circle": (75, 60, 77),
        }

        mock_meters = MockAllMetersReading(meter_scores)

        # Headline picks GROWTH (the only interesting one)
        featured_list = [
            {"meter": mock_meters.momentum, "direction": "flowing"},
        ]
        headline_guidance = {"instruction": "Test", "conjunction": None}

        overview = generate_overview_guidance(
            all_meters=mock_meters,
            featured_list=featured_list,
            headline_guidance=headline_guidance,
        )

        highlight_groups = [h["group"] for h in overview["highlights"]]
        print(f"Headline group: growth")
        print(f"Overview highlights: {highlight_groups}")

        # All other groups are in 40-60 range, so overview should be empty
        assert len(highlight_groups) == 0, \
            f"Neutral groups (40-60) should not be in overview, got: {highlight_groups}"


if __name__ == "__main__":
    print("Running prompt score consistency tests...\n")

    test = TestPromptScoreConsistency()

    print("Test 1: Overview guidance uses Top-2 weighted scoring")
    test.test_overview_guidance_uses_top2_weighted_scoring()
    print("PASSED\n")

    print("Test 2: all_groups and overview_guidance match")
    test.test_all_groups_and_overview_guidance_match()
    print("PASSED\n")

    print("Test 3: Driver meter consistency")
    test.test_driver_meter_consistency()
    print("PASSED\n")

    print("Test 4: Real chart score consistency")
    real_test = TestRealChartConsistency()
    real_test.test_real_chart_score_consistency()
    print("PASSED\n")

    print("\nRunning prompt determinism tests...\n")

    determinism_test = TestPromptDeterminism()

    print("Test 5: select_featured_meters is deterministic")
    determinism_test.test_select_featured_meters_is_deterministic()
    print("PASSED\n")

    print("Test 6: select_featured_meters varies by user")
    determinism_test.test_select_featured_meters_varies_by_user()
    print("PASSED\n")

    print("Test 7: select_featured_meters varies by date")
    determinism_test.test_select_featured_meters_varies_by_date()
    print("PASSED\n")

    print("Test 8: overview_guidance is deterministic")
    determinism_test.test_overview_guidance_is_deterministic()
    print("PASSED\n")

    print("Test 9: Full prompt chain determinism with real chart")
    determinism_test.test_full_prompt_determinism_with_real_chart()
    print("PASSED\n")

    print("\nRunning overview guidance selection tests...\n")

    selection_test = TestOverviewGuidanceSelection()

    print("Test 10: Overview picks extreme groups not in headline")
    selection_test.test_overview_picks_extreme_groups_not_in_headline()
    print("PASSED\n")

    print("Test 11: Overview adds 2 when headline has 1")
    selection_test.test_overview_adds_2_when_headline_has_1()
    print("PASSED\n")

    print("Test 12: Overview adds 1 when headline has 2")
    selection_test.test_overview_adds_1_when_headline_has_2()
    print("PASSED\n")

    print("Test 13: Overview excludes neutral groups")
    selection_test.test_overview_excludes_neutral_groups()
    print("PASSED\n")

    print("All prompt score consistency tests passed!")

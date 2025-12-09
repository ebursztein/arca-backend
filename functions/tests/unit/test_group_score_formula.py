"""
Tests for the group score formula (median-based).

Formula:
1. Sort all meter unified_scores
2. Calculate median (average of middle values for even count)
3. Driver = meter furthest from 50 in the median's direction
   - If median >= 50, driver is the highest scoring meter
   - If median < 50, driver is the lowest scoring meter

This approach is more intuitive and resistant to outliers than
distance-based formulas.
"""

import pytest
from datetime import date
from astrometers.meters import MeterReading
from astrometers.meter_groups import calculate_group_scores


def make_meter(name: str, unified_score: float) -> MeterReading:
    """Create a MeterReading with specified unified_score."""
    return MeterReading(
        meter_name=name,
        date=date.today(),
        group="instincts",
        unified_score=unified_score,
        intensity=50.0,
        harmony=50.0,
        unified_quality="peaceful",
        state_label="Test",
        interpretation="Test meter",
        advice=["Test advice"],
        top_aspects=[],
        raw_scores={},
    )


class TestMedianCalculation:
    """Tests for median calculation."""

    def test_even_count_median(self):
        """4 meters: median is average of middle two."""
        meters = [
            make_meter("a", 30),
            make_meter("b", 40),
            make_meter("c", 60),
            make_meter("d", 70),
        ]
        # Sorted: 30, 40, 60, 70 -> median = (40 + 60) / 2 = 50
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(50.0, abs=0.1)

    def test_odd_count_median(self):
        """3 meters: median is middle value."""
        meters = [
            make_meter("a", 30),
            make_meter("b", 50),
            make_meter("c", 70),
        ]
        # Sorted: 30, 50, 70 -> median = 50
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(50.0, abs=0.1)

    def test_unsorted_input(self):
        """Meters not in order still get correct median."""
        meters = [
            make_meter("a", 70),
            make_meter("b", 30),
            make_meter("c", 60),
            make_meter("d", 40),
        ]
        # Sorted: 30, 40, 60, 70 -> median = (40 + 60) / 2 = 50
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(50.0, abs=0.1)


class TestDirectionDetermination:
    """Tests for direction based on median."""

    def test_clear_positive_majority(self):
        """3 positive, 1 negative -> positive median."""
        meters = [
            make_meter("a", 60),
            make_meter("b", 65),
            make_meter("c", 70),
            make_meter("d", 35),
        ]
        # Sorted: 35, 60, 65, 70 -> median = (60 + 65) / 2 = 62.5
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(62.5, abs=0.1)
        assert result["unified_score"] > 50, "Should be positive direction"

    def test_clear_negative_majority(self):
        """3 negative, 1 positive -> negative median."""
        meters = [
            make_meter("a", 40),
            make_meter("b", 35),
            make_meter("c", 30),
            make_meter("d", 65),
        ]
        # Sorted: 30, 35, 40, 65 -> median = (35 + 40) / 2 = 37.5
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(37.5, abs=0.1)
        assert result["unified_score"] < 50, "Should be negative direction"

    def test_count_tie_positive_median(self):
        """2 vs 2 count with positive leaning median."""
        meters = [
            make_meter("a", 80),
            make_meter("b", 60),
            make_meter("c", 45),
            make_meter("d", 40),
        ]
        # Sorted: 40, 45, 60, 80 -> median = (45 + 60) / 2 = 52.5
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(52.5, abs=0.1)
        assert result["unified_score"] > 50, "Median should be positive"

    def test_count_tie_negative_median(self):
        """2 vs 2 count with negative leaning median."""
        meters = [
            make_meter("a", 55),
            make_meter("b", 52),
            make_meter("c", 20),
            make_meter("d", 25),
        ]
        # Sorted: 20, 25, 52, 55 -> median = (25 + 52) / 2 = 38.5
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(38.5, abs=0.1)
        assert result["unified_score"] < 50, "Median should be negative"


class TestOutlierResistance:
    """Tests showing median resists outliers better than distance-based."""

    def test_strong_positive_outlier_resisted(self):
        """One extreme positive doesn't dominate with median."""
        meters = [
            make_meter("a", 90),  # extreme positive outlier
            make_meter("b", 45),
            make_meter("c", 40),
            make_meter("d", 45),
        ]
        # Old formula: positive distance=40, negative=20 -> positive wins
        # Median: sorted 40, 45, 45, 90 -> median = (45 + 45) / 2 = 45
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(45.0, abs=0.1)
        # Outlier doesn't pull group positive like old formula

    def test_strong_negative_outlier_resisted(self):
        """One extreme negative doesn't dominate with median."""
        meters = [
            make_meter("a", 55),
            make_meter("b", 55),
            make_meter("c", 10),  # extreme negative outlier
            make_meter("d", 55),
        ]
        # Old formula: positive distance=15, negative=40 -> negative wins
        # Median: sorted 10, 55, 55, 55 -> median = (55 + 55) / 2 = 55
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(55.0, abs=0.1)
        # Outlier doesn't pull group negative like old formula


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_all_positive(self):
        """All meters positive."""
        meters = [
            make_meter("a", 60),
            make_meter("b", 65),
            make_meter("c", 70),
            make_meter("d", 75),
        ]
        # Sorted: 60, 65, 70, 75 -> median = (65 + 70) / 2 = 67.5
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(67.5, abs=0.1)

    def test_all_negative(self):
        """All meters negative."""
        meters = [
            make_meter("a", 40),
            make_meter("b", 35),
            make_meter("c", 30),
            make_meter("d", 25),
        ]
        # Sorted: 25, 30, 35, 40 -> median = (30 + 35) / 2 = 32.5
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(32.5, abs=0.1)

    def test_all_exactly_50(self):
        """All meters at neutral."""
        meters = [
            make_meter("a", 50),
            make_meter("b", 50),
            make_meter("c", 50),
            make_meter("d", 50),
        ]
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(50.0, abs=0.1)

    def test_three_meters_group(self):
        """Groups with only 3 meters (Mind, Heart, Body)."""
        meters = [
            make_meter("a", 70),
            make_meter("b", 65),
            make_meter("c", 60),
        ]
        # Sorted: 60, 65, 70 -> median = 65 (odd count, middle value)
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(65.0, abs=0.1)

    def test_empty_meters(self):
        """Empty list returns neutral."""
        result = calculate_group_scores([])
        assert result["unified_score"] == 50.0

    def test_single_meter(self):
        """Single meter returns its score."""
        meters = [make_meter("a", 75)]
        result = calculate_group_scores(meters)
        assert result["unified_score"] == 75.0


class TestDriverSelection:
    """Tests for driver selection based on median direction."""

    def test_positive_median_driver_is_highest(self):
        """When median >= 50, driver is highest scoring meter."""
        meters = [
            make_meter("a", 60),
            make_meter("b", 80),  # highest
            make_meter("c", 70),
        ]
        result = calculate_group_scores(meters)
        assert result["driver"] == "b"

    def test_negative_median_driver_is_lowest(self):
        """When median < 50, driver is lowest scoring meter."""
        meters = [
            make_meter("a", 40),
            make_meter("b", 20),  # lowest
            make_meter("c", 30),
        ]
        result = calculate_group_scores(meters)
        assert result["driver"] == "b"

    def test_exactly_50_median_uses_highest(self):
        """When median = 50, use positive direction (highest)."""
        meters = [
            make_meter("a", 30),
            make_meter("b", 50),
            make_meter("c", 70),  # highest
        ]
        # Median = 50 -> driver is highest
        result = calculate_group_scores(meters)
        assert result["driver"] == "c"


class TestReturnStructure:
    """Test the return dict structure."""

    def test_returns_required_fields(self):
        """Result should have unified_score and driver."""
        meters = [
            make_meter("a", 60),
            make_meter("b", 70),
            make_meter("c", 65),
        ]
        result = calculate_group_scores(meters)

        assert "unified_score" in result
        assert "driver" in result
        assert isinstance(result["unified_score"], float)
        assert isinstance(result["driver"], str)


class TestBugScenario:
    """Test the original bug scenario from the screenshot."""

    def test_growth_bug_case(self):
        """
        Original bug: Growth group showed "Uphill" (challenging) when:
        - Momentum: 63 (positive)
        - Ambition: 23 (very negative)
        - Evolution: 65 (positive)
        - Circle: 43 (slightly negative)

        3 out of 4 meters were positive-ish, but the old formula
        calculated total distance and let Ambition (23) dominate.

        With median formula: sorted 23, 43, 63, 65 -> median = (43 + 63) / 2 = 53
        This correctly shows the group as slightly positive ("Moving").
        """
        meters = [
            make_meter("momentum", 63),
            make_meter("ambition", 23),
            make_meter("evolution", 65),
            make_meter("circle", 43),
        ]
        result = calculate_group_scores(meters)

        # Median = (43 + 63) / 2 = 53
        assert result["unified_score"] == pytest.approx(53.0, abs=0.1)
        assert result["unified_score"] > 50, "Should be positive (Moving), not Uphill!"

        # Driver should be evolution (65) - highest in positive direction
        assert result["driver"] == "evolution"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

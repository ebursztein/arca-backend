"""
Tests for the group score formula (average-based).

Formula:
1. Calculate simple average of all meter unified_scores
2. Driver = meter furthest from 50 in the average's direction
   - If average >= 50, driver is the highest scoring meter
   - If average < 50, driver is the lowest scoring meter
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


class TestAverageCalculation:
    """Tests for average calculation."""

    def test_four_meter_average(self):
        """4 meters: average of all."""
        meters = [
            make_meter("a", 30),
            make_meter("b", 40),
            make_meter("c", 60),
            make_meter("d", 70),
        ]
        # Average = (30 + 40 + 60 + 70) / 4 = 50
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(50.0, abs=0.1)

    def test_three_meter_average(self):
        """3 meters: average of all."""
        meters = [
            make_meter("a", 30),
            make_meter("b", 50),
            make_meter("c", 70),
        ]
        # Average = (30 + 50 + 70) / 3 = 50
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(50.0, abs=0.1)

    def test_unsorted_input(self):
        """Meters not in order still get correct average."""
        meters = [
            make_meter("a", 70),
            make_meter("b", 30),
            make_meter("c", 60),
            make_meter("d", 40),
        ]
        # Average = (70 + 30 + 60 + 40) / 4 = 50
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(50.0, abs=0.1)


class TestDirectionDetermination:
    """Tests for direction based on average."""

    def test_clear_positive_majority(self):
        """3 positive, 1 negative -> positive average."""
        meters = [
            make_meter("a", 60),
            make_meter("b", 65),
            make_meter("c", 70),
            make_meter("d", 35),
        ]
        # Average = (60 + 65 + 70 + 35) / 4 = 57.5
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(57.5, abs=0.1)
        assert result["unified_score"] > 50, "Should be positive direction"

    def test_clear_negative_majority(self):
        """3 negative, 1 positive -> negative average."""
        meters = [
            make_meter("a", 40),
            make_meter("b", 35),
            make_meter("c", 30),
            make_meter("d", 65),
        ]
        # Average = (40 + 35 + 30 + 65) / 4 = 42.5
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(42.5, abs=0.1)
        assert result["unified_score"] < 50, "Should be negative direction"

    def test_count_tie_positive_average(self):
        """2 vs 2 count with positive leaning average."""
        meters = [
            make_meter("a", 80),
            make_meter("b", 60),
            make_meter("c", 45),
            make_meter("d", 40),
        ]
        # Average = (80 + 60 + 45 + 40) / 4 = 56.25
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(56.25, abs=0.1)
        assert result["unified_score"] > 50, "Average should be positive"

    def test_count_tie_negative_average(self):
        """2 vs 2 count with negative leaning average."""
        meters = [
            make_meter("a", 55),
            make_meter("b", 52),
            make_meter("c", 20),
            make_meter("d", 25),
        ]
        # Average = (55 + 52 + 20 + 25) / 4 = 38
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(38.0, abs=0.1)
        assert result["unified_score"] < 50, "Average should be negative"


class TestOutlierImpact:
    """Tests showing how outliers affect average."""

    def test_strong_positive_outlier_pulls_up(self):
        """One strong positive affects the average."""
        meters = [
            make_meter("a", 90),  # positive outlier
            make_meter("b", 45),
            make_meter("c", 40),
            make_meter("d", 45),
        ]
        # Average = (90 + 45 + 40 + 45) / 4 = 55
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(55.0, abs=0.1)

    def test_strong_negative_outlier_pulls_down(self):
        """One strong negative affects the average."""
        meters = [
            make_meter("a", 55),
            make_meter("b", 55),
            make_meter("c", 10),  # negative outlier
            make_meter("d", 55),
        ]
        # Average = (55 + 55 + 10 + 55) / 4 = 43.75
        result = calculate_group_scores(meters)
        assert result["unified_score"] == pytest.approx(43.75, abs=0.1)


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
        # Average = (60 + 65 + 70 + 75) / 4 = 67.5
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
        # Average = (40 + 35 + 30 + 25) / 4 = 32.5
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
        # Average = (70 + 65 + 60) / 3 = 65
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
    """Tests for driver selection based on average direction."""

    def test_positive_average_driver_is_highest(self):
        """When average >= 50, driver is highest scoring meter."""
        meters = [
            make_meter("a", 60),
            make_meter("b", 80),  # highest
            make_meter("c", 70),
        ]
        result = calculate_group_scores(meters)
        assert result["driver"] == "b"

    def test_negative_average_driver_is_lowest(self):
        """When average < 50, driver is lowest scoring meter."""
        meters = [
            make_meter("a", 40),
            make_meter("b", 20),  # lowest
            make_meter("c", 30),
        ]
        result = calculate_group_scores(meters)
        assert result["driver"] == "b"

    def test_exactly_50_average_uses_highest(self):
        """When average = 50, use positive direction (highest)."""
        meters = [
            make_meter("a", 30),
            make_meter("b", 50),
            make_meter("c", 70),  # highest
        ]
        # Average = (30 + 50 + 70) / 3 = 50 -> driver is highest
        result = calculate_group_scores(meters)
        assert result["driver"] == "c"


class TestReturnStructure:
    """Test the return dict structure."""

    def test_returns_required_fields(self):
        """Result should have unified_score, driver, and meter_scores."""
        meters = [
            make_meter("a", 60),
            make_meter("b", 70),
            make_meter("c", 65),
        ]
        result = calculate_group_scores(meters)

        assert "unified_score" in result
        assert "driver" in result
        assert "meter_scores" in result
        assert isinstance(result["unified_score"], float)
        assert isinstance(result["driver"], str)
        assert isinstance(result["meter_scores"], dict)

    def test_meter_scores_contains_all_meters(self):
        """meter_scores dict has entry for each meter."""
        meters = [
            make_meter("a", 60),
            make_meter("b", 70),
            make_meter("c", 65),
        ]
        result = calculate_group_scores(meters)

        assert result["meter_scores"] == {"a": 60.0, "b": 70.0, "c": 65.0}


class TestRealWorldScenario:
    """Test a real scenario from the app."""

    def test_growth_case(self):
        """
        Growth group scenario:
        - Momentum: 63 (positive)
        - Ambition: 23 (very negative)
        - Evolution: 65 (positive)
        - Circle: 43 (slightly negative)

        Average = (63 + 23 + 65 + 43) / 4 = 48.5
        This shows the group as slightly challenging due to Ambition dragging it down.
        """
        meters = [
            make_meter("momentum", 63),
            make_meter("ambition", 23),
            make_meter("evolution", 65),
            make_meter("circle", 43),
        ]
        result = calculate_group_scores(meters)

        # Average = 48.5
        assert result["unified_score"] == pytest.approx(48.5, abs=0.1)

        # Driver should be ambition (23) - lowest in negative direction
        assert result["driver"] == "ambition"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

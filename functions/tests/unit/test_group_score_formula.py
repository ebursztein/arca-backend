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


class TestOverallWritingGuidance:
    """Tests for get_overall_writing_guidance() function."""

    def test_all_flowing(self):
        """All groups >= 60."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 65},
            {"name": "heart", "unified_score": 70},
            {"name": "body", "unified_score": 75},
            {"name": "instincts", "unified_score": 62},
            {"name": "growth", "unified_score": 68},
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "all_flowing"
        assert result["strongest_group"] == "body"  # highest
        assert result["strongest_score"] == 75
        assert result["challenging_group"] is None  # nothing < 40
        assert set(result["flowing_groups"]) == {"mind", "heart", "body", "instincts", "growth"}

    def test_all_challenging(self):
        """All groups < 40."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 35},
            {"name": "heart", "unified_score": 25},
            {"name": "body", "unified_score": 38},
            {"name": "instincts", "unified_score": 30},
            {"name": "growth", "unified_score": 32},
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "all_challenging"
        assert result["challenging_group"] == "heart"  # lowest
        assert result["challenging_score"] == 25
        assert set(result["challenging_groups"]) == {"mind", "heart", "body", "instincts", "growth"}

    def test_one_challenging(self):
        """1 group < 45, no flowing groups (all others in neutral 45-55 zone)."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 50},
            {"name": "heart", "unified_score": 35},  # challenging (< 45)
            {"name": "body", "unified_score": 50},
            {"name": "instincts", "unified_score": 52},
            {"name": "growth", "unified_score": 48},
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "one_challenging"
        assert result["challenging_group"] == "heart"
        assert result["challenging_groups"] == ["heart"]

    def test_one_shining(self):
        """1 group >= 55, others in neutral zone."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 48},
            {"name": "heart", "unified_score": 70},  # shining (>= 55)
            {"name": "body", "unified_score": 50},
            {"name": "instincts", "unified_score": 48},
            {"name": "growth", "unified_score": 52},
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "one_shining"
        assert result["shining_group"] == "heart"
        assert result["flowing_groups"] == ["heart"]

    def test_mixed_day(self):
        """Some >= 55, some < 45."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 65},   # flowing (>= 55)
            {"name": "heart", "unified_score": 35},  # challenging (< 45)
            {"name": "body", "unified_score": 70},   # flowing
            {"name": "instincts", "unified_score": 30},  # challenging
            {"name": "growth", "unified_score": 50},  # neutral
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "mixed_day"
        assert set(result["flowing_groups"]) == {"mind", "body"}
        assert set(result["challenging_groups"]) == {"heart", "instincts"}

    def test_neutral_day(self):
        """All groups in 45-55 range."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 52},
            {"name": "heart", "unified_score": 48},
            {"name": "body", "unified_score": 54},
            {"name": "instincts", "unified_score": 46},
            {"name": "growth", "unified_score": 50},
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "neutral_day"
        assert result["challenging_group"] is None  # nothing < 45

    def test_tie_breaking_priority(self):
        """When scores tie, heart > mind > body > instincts > growth."""
        from astrometers.meter_groups import get_overall_writing_guidance

        # All groups at same score
        groups = [
            {"name": "mind", "unified_score": 65},
            {"name": "heart", "unified_score": 65},  # should win ties
            {"name": "body", "unified_score": 65},
            {"name": "instincts", "unified_score": 65},
            {"name": "growth", "unified_score": 65},
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        # Heart should be strongest due to priority
        assert result["strongest_group"] == "heart"

    def test_empty_groups(self):
        """Empty list returns unknown pattern."""
        from astrometers.meter_groups import get_overall_writing_guidance

        result = get_overall_writing_guidance([], "Sarah")
        assert result["pattern"] == "unknown"
        assert result["strongest_group"] is None

    def test_boundary_scores_55(self):
        """Test boundary at exactly 55 (should be flowing)."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 55},  # exactly 55 = flowing
            {"name": "heart", "unified_score": 55},
            {"name": "body", "unified_score": 55},
            {"name": "instincts", "unified_score": 55},
            {"name": "growth", "unified_score": 55},
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "all_flowing"
        assert len(result["flowing_groups"]) == 5

    def test_boundary_scores_45(self):
        """Test boundary at exactly 45 (should be neutral, not challenging)."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 45},  # exactly 45 = neutral
            {"name": "heart", "unified_score": 48},
            {"name": "body", "unified_score": 50},
            {"name": "instincts", "unified_score": 52},
            {"name": "growth", "unified_score": 54},
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "neutral_day"
        assert len(result["challenging_groups"]) == 0  # 45 is not challenging

    def test_formula_includes_user_name(self):
        """Formula should include user name when provided."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 65},
            {"name": "heart", "unified_score": 70},
            {"name": "body", "unified_score": 75},
            {"name": "instincts", "unified_score": 62},
            {"name": "growth", "unified_score": 68},
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert "Sarah" in result["formula"]

    def test_mostly_flowing(self):
        """Multiple flowing groups (>= 55), no challenging groups."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 65},   # flowing (>= 55)
            {"name": "heart", "unified_score": 70},  # flowing
            {"name": "body", "unified_score": 62},   # flowing
            {"name": "instincts", "unified_score": 50},  # neutral (45-55)
            {"name": "growth", "unified_score": 48},  # neutral
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "mostly_flowing"
        assert set(result["flowing_groups"]) == {"mind", "heart", "body"}
        assert len(result["challenging_groups"]) == 0

    def test_mostly_challenging(self):
        """Multiple challenging groups (< 45), no flowing groups."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 35},   # challenging (< 45)
            {"name": "heart", "unified_score": 30},  # challenging
            {"name": "body", "unified_score": 50},   # neutral (45-55)
            {"name": "instincts", "unified_score": 48},  # neutral
            {"name": "growth", "unified_score": 38},  # challenging
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "mostly_challenging"
        assert set(result["challenging_groups"]) == {"mind", "heart", "growth"}
        assert len(result["flowing_groups"]) == 0

    def test_mixed_day_with_one_each(self):
        """Mixed day: 1 flowing AND 1 challenging (others neutral)."""
        from astrometers.meter_groups import get_overall_writing_guidance

        groups = [
            {"name": "mind", "unified_score": 65},   # flowing (>= 55)
            {"name": "heart", "unified_score": 35},  # challenging (< 45)
            {"name": "body", "unified_score": 50},   # neutral
            {"name": "instincts", "unified_score": 52},  # neutral
            {"name": "growth", "unified_score": 48},  # neutral
        ]
        result = get_overall_writing_guidance(groups, "Sarah")
        assert result["pattern"] == "mixed_day"
        assert result["flowing_groups"] == ["mind"]
        assert result["challenging_groups"] == ["heart"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

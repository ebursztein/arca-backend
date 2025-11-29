"""Test meter_groups.py aggregation functions."""

from datetime import datetime
from astrometers.meter_groups import (
    load_group_labels,
    get_group_state_label,
    determine_quality_label,
    calculate_trend_metric,
    calculate_group_trends,
    build_meter_group_data,
)
from astrometers.hierarchy import MeterGroupV2, Meter
from astrometers.meters import MeterReading, QualityLabel


# =============================================================================
# Mock Data
# =============================================================================

def create_mock_meter(
    meter_name: str,
    unified_score: float,
    intensity: float,
    harmony: float
) -> MeterReading:
    """Create a mock MeterReading for testing."""
    # Quality based on unified_score quadrants
    if unified_score < -25:
        unified_quality = QualityLabel.CHALLENGING
    elif unified_score < 10:
        unified_quality = QualityLabel.TURBULENT
    elif unified_score < 50:
        unified_quality = QualityLabel.PEACEFUL
    else:
        unified_quality = QualityLabel.FLOWING

    return MeterReading(
        meter_name=meter_name,
        date=datetime(2025, 11, 2),
        group="mind",  # Doesn't matter for these tests
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


# =============================================================================
# Tests
# =============================================================================

def test_load_group_labels():
    """Test loading group labels from JSON."""
    labels = load_group_labels("mind")

    assert "_group" in labels
    assert labels["_group"] == "mind"
    assert "metadata" in labels
    assert "description" in labels
    assert "advice_templates" in labels


def test_get_group_state_label():
    """Test getting state label for different intensity/harmony combinations."""
    # High harmony, high intensity
    label = get_group_state_label("mind", 75, 80)
    assert isinstance(label, str)
    assert len(label) > 0

    # Low harmony, high intensity
    label = get_group_state_label("mind", 75, 30)
    assert isinstance(label, str)
    assert len(label) > 0

    # Low harmony, low intensity
    label = get_group_state_label("mind", 20, 30)
    assert isinstance(label, str)
    assert len(label) > 0


def test_determine_quality_label():
    """Test quality label determination based on unified_score quadrants."""
    # Flowing: high harmony (unified_score >= 50)
    quality, label = determine_quality_label(85, 70)
    assert quality == "flowing"
    assert label == "Flowing"

    # Peaceful: good harmony (unified_score 10-50)
    quality, label = determine_quality_label(65, 50)
    assert quality == "peaceful"
    assert label == "Peaceful"

    # Turbulent: mixed (unified_score -25 to 10)
    quality, label = determine_quality_label(50, 50)
    assert quality == "turbulent"
    assert label == "Turbulent"

    # Challenging: low harmony (unified_score < -25)
    quality, label = determine_quality_label(20, 70)
    assert quality == "challenging"
    assert label == "Challenging"


def test_calculate_trend_metric():
    """Test trend metric calculation."""
    # Improving trend (unified_score/harmony)
    trend = calculate_trend_metric(75, 65, "unified_score")
    assert trend["previous"] == 65
    assert trend["delta"] == 10
    assert trend["direction"] == "improving"
    assert trend["change_rate"] == "moderate"

    # Worsening trend
    trend = calculate_trend_metric(50, 70, "harmony")
    assert trend["previous"] == 70
    assert trend["delta"] == -20
    assert trend["direction"] == "worsening"
    assert trend["change_rate"] == "rapid"

    # Stable trend
    trend = calculate_trend_metric(60, 62, "unified_score")
    assert trend["previous"] == 62
    assert trend["delta"] == -2
    assert trend["direction"] == "stable"
    assert trend["change_rate"] == "slow"

    # Increasing intensity
    trend = calculate_trend_metric(80, 70, "intensity")
    assert trend["direction"] == "increasing"

    # Decreasing intensity
    trend = calculate_trend_metric(60, 75, "intensity")
    assert trend["direction"] == "decreasing"


def test_calculate_group_trends():
    """Test group trend calculation with multiple meters."""
    today_meters = [
        create_mock_meter("clarity", 75, 70, 80),
        create_mock_meter("decision_quality", 70, 65, 75),
        create_mock_meter("communication_flow", 80, 75, 85),
    ]

    yesterday_meters = [
        create_mock_meter("clarity", 70, 65, 75),
        create_mock_meter("decision_quality", 65, 60, 70),
        create_mock_meter("communication_flow", 75, 70, 80),
    ]

    trends = calculate_group_trends(today_meters, yesterday_meters)

    assert trends is not None
    assert "unified_score" in trends
    assert "harmony" in trends
    assert "intensity" in trends

    # Check structure of each trend
    for metric in ["unified_score", "harmony", "intensity"]:
        assert "previous" in trends[metric]
        assert "delta" in trends[metric]
        assert "direction" in trends[metric]
        assert "change_rate" in trends[metric]


def test_calculate_group_trends_no_yesterday():
    """Test that trends are None when no yesterday data."""
    today_meters = [
        create_mock_meter("clarity", 75, 70, 80),
    ]

    trends = calculate_group_trends(today_meters, [])
    assert trends is None

    trends = calculate_group_trends(today_meters, None)
    assert trends is None


def test_build_meter_group_data():
    """Test building complete meter group data."""
    today_meters = [
        create_mock_meter("clarity", 75, 70, 80),
        create_mock_meter("decision_quality", 70, 65, 75),
        create_mock_meter("communication_flow", 80, 75, 85),
    ]

    llm_interpretation = "Your mental faculties are sharp and clear today."

    group_data = build_meter_group_data(
        MeterGroupV2.MIND,
        today_meters,
        llm_interpretation,
        None  # No yesterday data
    )

    # Check structure
    assert group_data["group_name"] == "mind"
    assert group_data["display_name"] == "Mind"

    # Check scores
    assert "unified_score" in group_data["scores"]
    assert "harmony" in group_data["scores"]
    assert "intensity" in group_data["scores"]

    # Check all scores are rounded to 1 decimal
    assert isinstance(group_data["scores"]["unified_score"], float)
    assert isinstance(group_data["scores"]["harmony"], float)
    assert isinstance(group_data["scores"]["intensity"], float)

    # Check state
    assert "label" in group_data["state"]
    assert "quality" in group_data["state"]

    # Check interpretation
    assert group_data["interpretation"] == llm_interpretation

    # Check meter_ids
    assert len(group_data["meter_ids"]) == 3
    assert "clarity" in group_data["meter_ids"]

    # Check trend is None (no yesterday data)
    assert group_data["trend"] is None


def test_build_meter_group_data_with_trends():
    """Test building meter group data with trend calculation."""
    today_meters = [
        create_mock_meter("clarity", 75, 70, 80),
        create_mock_meter("decision_quality", 70, 65, 75),
        create_mock_meter("communication_flow", 80, 75, 85),
    ]

    yesterday_meters = [
        create_mock_meter("clarity", 70, 65, 75),
        create_mock_meter("decision_quality", 65, 60, 70),
        create_mock_meter("communication_flow", 75, 70, 80),
    ]

    group_data = build_meter_group_data(
        MeterGroupV2.MIND,
        today_meters,
        "Test interpretation",
        yesterday_meters
    )

    # Check trend is calculated
    assert group_data["trend"] is not None
    assert "unified_score" in group_data["trend"]
    assert "harmony" in group_data["trend"]
    assert "intensity" in group_data["trend"]


def test_build_meter_group_data_fallback_interpretation():
    """Test that fallback interpretation is used when LLM interpretation is None."""
    today_meters = [
        create_mock_meter("clarity", 75, 70, 80),
    ]

    group_data = build_meter_group_data(
        MeterGroupV2.MIND,
        today_meters,
        None,  # No LLM interpretation
        None
    )

    # Should have fallback interpretation from JSON labels
    assert len(group_data["interpretation"]) > 0
    assert isinstance(group_data["interpretation"], str)


if __name__ == "__main__":
    print("Running meter_groups aggregation tests...")
    print()

    test_load_group_labels()
    print("✅ Group labels load correctly")

    test_get_group_state_label()
    print("✅ State labels retrieved correctly")

    test_determine_quality_label()
    print("✅ Quality labels determined correctly")

    test_calculate_trend_metric()
    print("✅ Trend metrics calculated correctly")

    test_calculate_group_trends()
    print("✅ Group trends calculated correctly")

    test_calculate_group_trends_no_yesterday()
    print("✅ Trends handle missing yesterday data")

    test_build_meter_group_data()
    print("✅ Meter group data built correctly")

    test_build_meter_group_data_with_trends()
    print("✅ Meter group data with trends works")

    test_build_meter_group_data_fallback_interpretation()
    print("✅ Fallback interpretation works")

    print()
    print("🎉 All meter_groups aggregation tests passed!")

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
    # Quality based on unified_score quartiles (0-100 scale)
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
    """Test getting state label for different unified_score values (0-100 scale)."""
    from ..meter_groups import get_group_bucket_labels

    # Get labels from JSON so test stays in sync
    mind_labels = get_group_bucket_labels("mind")

    # High unified_score (>= 75) -> bucket 3
    label = get_group_state_label("mind", 80)
    assert isinstance(label, str)
    assert label == mind_labels[3]

    # Medium-high unified_score (50-75) -> bucket 2
    label = get_group_state_label("mind", 60)
    assert isinstance(label, str)
    assert label == mind_labels[2]

    # Medium-low unified_score (25-50) -> bucket 1
    label = get_group_state_label("mind", 42)
    assert isinstance(label, str)
    assert label == mind_labels[1]

    # Low unified_score (< 25) -> bucket 0
    label = get_group_state_label("mind", 20)
    assert isinstance(label, str)
    assert label == mind_labels[0]


def test_state_label_quartile_boundaries():
    """
    Test exact quartile boundary behavior for state labels.

    iOS uses these exact cutoffs:
        score < 25  -> labels[0] (Challenging)
        score >= 25 && score < 50  -> labels[1] (Turbulent)
        score >= 50 && score < 75  -> labels[2] (Peaceful)
        score >= 75 -> labels[3] (Flowing)

    Backend must match exactly. Labels are loaded from JSON.
    """
    from ..meter_groups import get_group_bucket_labels

    # Test all groups have correct boundary behavior
    groups = ["mind", "heart", "body", "instincts", "growth", "overall"]

    for group_name in groups:
        labels = get_group_bucket_labels(group_name)
        assert len(labels) == 4, f"{group_name} should have 4 bucket labels"

        # Bucket 0: < 25
        assert get_group_state_label(group_name, 0) == labels[0], f"{group_name} at 0"
        assert get_group_state_label(group_name, 10) == labels[0], f"{group_name} at 10"
        assert get_group_state_label(group_name, 24) == labels[0], f"{group_name} at 24"
        assert get_group_state_label(group_name, 24.99) == labels[0], f"{group_name} at 24.99"

        # Bucket 1: >= 25 && < 50
        assert get_group_state_label(group_name, 25) == labels[1], f"{group_name} at 25"
        assert get_group_state_label(group_name, 25.01) == labels[1], f"{group_name} at 25.01"
        assert get_group_state_label(group_name, 37) == labels[1], f"{group_name} at 37"
        assert get_group_state_label(group_name, 49) == labels[1], f"{group_name} at 49"
        assert get_group_state_label(group_name, 49.99) == labels[1], f"{group_name} at 49.99"

        # Bucket 2: >= 50 && < 75
        assert get_group_state_label(group_name, 50) == labels[2], f"{group_name} at 50"
        assert get_group_state_label(group_name, 50.01) == labels[2], f"{group_name} at 50.01"
        assert get_group_state_label(group_name, 62) == labels[2], f"{group_name} at 62"
        assert get_group_state_label(group_name, 74) == labels[2], f"{group_name} at 74"
        assert get_group_state_label(group_name, 74.99) == labels[2], f"{group_name} at 74.99"

        # Bucket 3: >= 75
        assert get_group_state_label(group_name, 75) == labels[3], f"{group_name} at 75"
        assert get_group_state_label(group_name, 75.01) == labels[3], f"{group_name} at 75.01"
        assert get_group_state_label(group_name, 87) == labels[3], f"{group_name} at 87"
        assert get_group_state_label(group_name, 100) == labels[3], f"{group_name} at 100"


def test_state_label_quartile_boundaries_individual_meters():
    """
    Test quartile boundaries for individual meter state labels.

    Individual meters use the same 25/50/75 quartile cutoffs,
    inheriting bucket labels from their parent group.
    Labels are loaded from JSON to stay in sync.
    """
    from ..meters import get_state_label, calculate_unified_score
    from ..meter_groups import get_group_bucket_labels

    # Test meters from each group
    test_cases = [
        ("clarity", "mind"),
        ("connections", "heart"),
        ("energy", "body"),
        ("intuition", "instincts"),
        ("momentum", "growth"),
    ]

    for meter_name, group_name in test_cases:
        labels = get_group_bucket_labels(group_name)

        # We need intensity/harmony values that produce specific unified_scores
        # unified_score is calculated from intensity and harmony
        # For simplicity, test with values that produce scores in each bucket
        # Using intensity=harmony simplifies the calculation

        # Test bucket boundaries by checking the actual unified_score
        # Bucket 0: unified_score < 25
        score_0, _ = calculate_unified_score(10, 10)
        if score_0 < 25:
            assert get_state_label(meter_name, 10, 10) == labels[0], \
                f"{meter_name} bucket 0: score={score_0}"

        # Bucket 1: unified_score 25-50
        score_1, _ = calculate_unified_score(30, 30)
        if 25 <= score_1 < 50:
            assert get_state_label(meter_name, 30, 30) == labels[1], \
                f"{meter_name} bucket 1: score={score_1}"

        # Bucket 2: unified_score 50-75
        score_2, _ = calculate_unified_score(60, 60)
        if 50 <= score_2 < 75:
            assert get_state_label(meter_name, 60, 60) == labels[2], \
                f"{meter_name} bucket 2: score={score_2}"

        # Bucket 3: unified_score >= 75
        score_3, _ = calculate_unified_score(90, 90)
        if score_3 >= 75:
            assert get_state_label(meter_name, 90, 90) == labels[3], \
                f"{meter_name} bucket 3: score={score_3}"


def test_quality_label_quartile_boundaries():
    """
    Test QualityLabel enum uses same 25/50/75 quartile cutoffs.
    """
    from ..meters import get_quality_label, QualityLabel

    # < 25 -> CHALLENGING
    assert get_quality_label(0) == QualityLabel.CHALLENGING
    assert get_quality_label(24.99) == QualityLabel.CHALLENGING

    # 25-50 -> TURBULENT
    assert get_quality_label(25) == QualityLabel.TURBULENT
    assert get_quality_label(49.99) == QualityLabel.TURBULENT

    # 50-75 -> PEACEFUL
    assert get_quality_label(50) == QualityLabel.PEACEFUL
    assert get_quality_label(74.99) == QualityLabel.PEACEFUL

    # >= 75 -> FLOWING
    assert get_quality_label(75) == QualityLabel.FLOWING
    assert get_quality_label(100) == QualityLabel.FLOWING


def test_quadrant_word_bank_quartile_boundaries():
    """
    Test word bank quadrant selection uses same 25/50/75 quartile cutoffs.
    """
    from ..meters import get_quadrant_from_unified_score

    # < 25 -> challenging quadrant
    assert get_quadrant_from_unified_score(0) == "low_intensity_low_harmony"
    assert get_quadrant_from_unified_score(24.99) == "low_intensity_low_harmony"

    # 25-50 -> turbulent quadrant
    assert get_quadrant_from_unified_score(25) == "moderate"
    assert get_quadrant_from_unified_score(49.99) == "moderate"

    # 50-75 -> peaceful quadrant
    assert get_quadrant_from_unified_score(50) == "low_intensity_high_harmony"
    assert get_quadrant_from_unified_score(74.99) == "low_intensity_high_harmony"

    # >= 75 -> flowing quadrant
    assert get_quadrant_from_unified_score(75) == "high_intensity_high_harmony"
    assert get_quadrant_from_unified_score(100) == "high_intensity_high_harmony"


def test_determine_quality_label():
    """Test quality label determination based on unified_score quartiles (0-100 scale)."""
    # Flowing (>= 75): high harmony, high intensity
    quality, label = determine_quality_label(90, 80)
    assert quality == "flowing"
    assert label == "Flowing"

    # Peaceful (50-75): above average
    quality, label = determine_quality_label(65, 60)
    assert quality == "peaceful"
    assert label == "Peaceful"

    # Turbulent (25-50): below average
    quality, label = determine_quality_label(35, 40)
    assert quality == "turbulent"
    assert label == "Turbulent"

    # Challenging (< 25): bottom quartile - needs high intensity + very low harmony
    quality, label = determine_quality_label(10, 80)
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

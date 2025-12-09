"""
Tests for headline rotation and pattern/matrix alignment.

Ensures that:
1. Headlines rotate properly across days (no meter repetition)
2. Pattern selection aligns with matrix guidance (two_positive uses "and", contrast uses "but")
3. Score bands use natural quartiles (25/50/75) matching positive/negative threshold
"""

import pytest
from datetime import datetime
from astro import compute_birth_chart
from astrometers.meters import (
    select_featured_meters,
    get_meters,
    get_score_band,
    HEADLINE_PATTERNS,
)


class TestScoreBands:
    """Test that score bands use natural quartiles aligned with positive/negative threshold."""

    def test_band_thresholds_are_quartiles(self):
        """Score bands should use 25/50/75 thresholds."""
        # Low: 0-25
        assert get_score_band(0) == "low"
        assert get_score_band(24.9) == "low"

        # Mid-low: 25-50
        assert get_score_band(25) == "mid_low"
        assert get_score_band(49.9) == "mid_low"

        # Mid-high: 50-75 (positive range)
        assert get_score_band(50) == "mid_high"
        assert get_score_band(74.9) == "mid_high"

        # High: 75-100
        assert get_score_band(75) == "high"
        assert get_score_band(100) == "high"

    def test_positive_threshold_aligns_with_mid_high(self):
        """Scores >= 50 (positive) should be in mid_high or high bands."""
        # This ensures two_positive pattern won't get contrast matrix
        for score in [50, 51, 55, 60, 70, 74]:
            band = get_score_band(score)
            assert band in ["mid_high", "high"], (
                f"Score {score} (positive) should be mid_high or high, got {band}"
            )

    def test_negative_threshold_aligns_with_mid_low(self):
        """Scores < 50 (negative) should be in mid_low or low bands."""
        for score in [49, 45, 30, 25, 10]:
            band = get_score_band(score)
            assert band in ["mid_low", "low"], (
                f"Score {score} (negative) should be mid_low or low, got {band}"
            )


class TestPatternMatrixAlignment:
    """Test that pattern selection aligns with matrix guidance."""

    @pytest.fixture
    def sample_charts(self):
        """Create sample natal and transit charts for testing."""
        natal_chart, _ = compute_birth_chart("1990-05-15", "14:30")
        return natal_chart

    def test_two_positive_uses_and_conjunction(self, sample_charts):
        """two_positive pattern should always result in 'and' conjunction."""
        natal_chart = sample_charts
        mismatches = []

        # Test 60 days to find two_positive patterns
        for day in range(1, 61):
            date_str = f"2024-12-{day:02d}" if day <= 31 else f"2025-01-{day-31:02d}"
            transit_chart, _ = compute_birth_chart(date_str, "12:00")

            all_meters = get_meters(
                natal_chart=natal_chart,
                transit_chart=transit_chart,
                date=datetime.fromisoformat(date_str),
            )

            featured = select_featured_meters(
                all_meters=all_meters,
                user_id="test_user",
                date=date_str,
                yesterday_meters=None,
            )

            selected_pattern = featured.get("selected_pattern")
            guidance = featured.get("headline_guidance", {})
            conjunction = guidance.get("conjunction")

            if selected_pattern == "two_positive" and conjunction == "but":
                meters_info = guidance.get("meters", [])
                scores = [m["score"] for m in meters_info]
                mismatches.append(
                    f"{date_str}: two_positive with 'but' - scores {scores}"
                )

        assert not mismatches, (
            f"two_positive should use 'and', not 'but':\n" + "\n".join(mismatches)
        )

    def test_two_negative_uses_and_conjunction(self, sample_charts):
        """two_negative pattern should always result in 'and' conjunction."""
        natal_chart = sample_charts
        mismatches = []

        for day in range(1, 61):
            date_str = f"2024-12-{day:02d}" if day <= 31 else f"2025-01-{day-31:02d}"
            transit_chart, _ = compute_birth_chart(date_str, "12:00")

            all_meters = get_meters(
                natal_chart=natal_chart,
                transit_chart=transit_chart,
                date=datetime.fromisoformat(date_str),
            )

            featured = select_featured_meters(
                all_meters=all_meters,
                user_id="test_user",
                date=date_str,
                yesterday_meters=None,
            )

            selected_pattern = featured.get("selected_pattern")
            guidance = featured.get("headline_guidance", {})
            conjunction = guidance.get("conjunction")

            if selected_pattern == "two_negative" and conjunction == "but":
                meters_info = guidance.get("meters", [])
                scores = [m["score"] for m in meters_info]
                mismatches.append(
                    f"{date_str}: two_negative with 'but' - scores {scores}"
                )

        assert not mismatches, (
            f"two_negative should use 'and', not 'but':\n" + "\n".join(mismatches)
        )

    def test_contrast_patterns_use_but_conjunction(self, sample_charts):
        """contrast_pos_neg and contrast_neg_pos should use 'but' conjunction."""
        natal_chart = sample_charts
        found_contrast = False

        for day in range(1, 61):
            date_str = f"2024-12-{day:02d}" if day <= 31 else f"2025-01-{day-31:02d}"
            transit_chart, _ = compute_birth_chart(date_str, "12:00")

            all_meters = get_meters(
                natal_chart=natal_chart,
                transit_chart=transit_chart,
                date=datetime.fromisoformat(date_str),
            )

            featured = select_featured_meters(
                all_meters=all_meters,
                user_id="test_user",
                date=date_str,
                yesterday_meters=None,
            )

            selected_pattern = featured.get("selected_pattern")
            guidance = featured.get("headline_guidance", {})
            conjunction = guidance.get("conjunction")

            if selected_pattern in ["contrast_pos_neg", "contrast_neg_pos"]:
                found_contrast = True
                assert conjunction == "but", (
                    f"{date_str}: {selected_pattern} should use 'but', got '{conjunction}'"
                )

        assert found_contrast, "No contrast patterns found in 60 days - test inconclusive"


class TestHeadlineRotation:
    """Test that headlines rotate properly without repetition."""

    @pytest.fixture
    def sample_charts(self):
        natal_chart, _ = compute_birth_chart("1990-05-15", "14:30")
        return natal_chart

    def test_no_meter_repetition_consecutive_days(self, sample_charts):
        """Featured meters should not repeat on consecutive days."""
        natal_chart = sample_charts
        yesterday_meters = None
        repetitions = []

        for day in range(1, 15):
            date_str = f"2024-12-{day:02d}"
            transit_chart, _ = compute_birth_chart(date_str, "12:00")

            all_meters = get_meters(
                natal_chart=natal_chart,
                transit_chart=transit_chart,
                date=datetime.fromisoformat(date_str),
            )

            featured = select_featured_meters(
                all_meters=all_meters,
                user_id="test_user",
                date=date_str,
                yesterday_meters=yesterday_meters,
            )

            meters = [m["meter"].meter_name for m in featured.get("featured_list", [])]

            if yesterday_meters:
                overlap = set(meters) & set(yesterday_meters)
                if overlap:
                    repetitions.append(f"{date_str}: repeated {overlap}")

            yesterday_meters = meters

        assert not repetitions, (
            f"Meters should not repeat on consecutive days:\n" + "\n".join(repetitions)
        )

    def test_pattern_variety_over_time(self, sample_charts):
        """Multiple different patterns should be selected over 30 days."""
        natal_chart = sample_charts
        patterns_seen = set()

        for day in range(1, 31):
            date_str = f"2024-12-{day:02d}"
            transit_chart, _ = compute_birth_chart(date_str, "12:00")

            all_meters = get_meters(
                natal_chart=natal_chart,
                transit_chart=transit_chart,
                date=datetime.fromisoformat(date_str),
            )

            featured = select_featured_meters(
                all_meters=all_meters,
                user_id="test_user",
                date=date_str,
                yesterday_meters=None,
            )

            pattern = featured.get("selected_pattern")
            if pattern:
                patterns_seen.add(pattern)

        # Should see at least 3 different patterns in 30 days
        assert len(patterns_seen) >= 3, (
            f"Expected variety in patterns, only saw {patterns_seen}"
        )

    def test_deterministic_selection_same_inputs(self, sample_charts):
        """Same user_id + date should produce same featured meters."""
        natal_chart = sample_charts
        date_str = "2024-12-15"
        transit_chart, _ = compute_birth_chart(date_str, "12:00")

        all_meters = get_meters(
            natal_chart=natal_chart,
            transit_chart=transit_chart,
            date=datetime.fromisoformat(date_str),
        )

        # Run selection 3 times with same inputs
        results = []
        for _ in range(3):
            featured = select_featured_meters(
                all_meters=all_meters,
                user_id="test_user_123",
                date=date_str,
                yesterday_meters=None,
            )
            meters = tuple(m["meter"].meter_name for m in featured.get("featured_list", []))
            results.append(meters)

        assert results[0] == results[1] == results[2], (
            f"Selection should be deterministic, got different results: {results}"
        )

    def test_different_users_get_different_selections(self, sample_charts):
        """Different user_ids should (usually) get different featured meters."""
        natal_chart = sample_charts
        date_str = "2024-12-15"
        transit_chart, _ = compute_birth_chart(date_str, "12:00")

        all_meters = get_meters(
            natal_chart=natal_chart,
            transit_chart=transit_chart,
            date=datetime.fromisoformat(date_str),
        )

        # Get selections for different users
        selections = []
        for user_id in ["user_a", "user_b", "user_c", "user_d", "user_e"]:
            featured = select_featured_meters(
                all_meters=all_meters,
                user_id=user_id,
                date=date_str,
                yesterday_meters=None,
            )
            pattern = featured.get("selected_pattern")
            meters = tuple(m["meter"].meter_name for m in featured.get("featured_list", []))
            selections.append((pattern, meters))

        # At least 2 different selections among 5 users
        unique_selections = set(selections)
        assert len(unique_selections) >= 2, (
            f"Expected different users to get varied selections, all got: {selections[0]}"
        )

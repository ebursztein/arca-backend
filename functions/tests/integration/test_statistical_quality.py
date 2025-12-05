"""
Statistical Quality Tests for Astrometers and Compatibility

These tests verify the statistical properties of meter and compatibility scores
to catch regressions before release:
- Meter cross-correlation (should be low - meters measure different things)
- Meter distribution quality (mean ~50, reasonable stddev)
- Day-to-day correlation (moderate change, not static or chaotic)
- Compatibility category correlation (categories should be distinct)

Run with: uv run pytest functions/tests/integration/test_statistical_quality.py -v
"""

import pytest
import random
import math
import statistics
from datetime import datetime, timedelta
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from astro import compute_birth_chart
from astrometers.meters import get_meters
from astrometers.hierarchy import Meter, MeterGroupV2, METER_TO_GROUP_V2
from compatibility import get_compatibility_from_birth_data


# =============================================================================
# Test Constants
# =============================================================================

# Sample sizes - smaller than analysis scripts for CI speed, but statistically valid
N_CHARTS_DISTRIBUTION = 50  # Charts for distribution tests
N_DATES_PER_CHART = 10  # Transit dates per chart
N_CHARTS_DAY_CORR = 30  # Charts for day correlation
N_DAY_PAIRS = 15  # Day pairs per chart
N_CHARTS_COMPAT = 30  # Charts for compatibility
N_CONNECTIONS = 15  # Connections per chart

RANDOM_SEED = 42

CITIES = [
    ("New York", 40.7128, -74.0060, "America/New_York"),
    ("Los Angeles", 34.0522, -118.2437, "America/Los_Angeles"),
    ("Chicago", 41.8781, -87.6298, "America/Chicago"),
    ("London", 51.5074, -0.1278, "Europe/London"),
    ("Paris", 48.8566, 2.3522, "Europe/Paris"),
    ("Tokyo", 35.6762, 139.6503, "Asia/Tokyo"),
    ("Sydney", -33.8688, 151.2093, "Australia/Sydney"),
    ("Berlin", 52.5200, 13.4050, "Europe/Berlin"),
    ("Mumbai", 19.0760, 72.8777, "Asia/Kolkata"),
    ("Sao Paulo", -23.5505, -46.6333, "America/Sao_Paulo"),
]

METER_NAMES = [
    'clarity', 'focus', 'communication',
    'connections', 'resilience', 'vulnerability',
    'energy', 'drive', 'strength',
    'vision', 'flow', 'intuition', 'creativity',
    'momentum', 'ambition', 'evolution', 'circle'
]

GROUPS = {
    'mind': ['clarity', 'focus', 'communication'],
    'heart': ['connections', 'resilience', 'vulnerability'],
    'body': ['energy', 'drive', 'strength'],
    'instincts': ['vision', 'flow', 'intuition', 'creativity'],
    'growth': ['momentum', 'ambition', 'evolution', 'circle'],
}


# =============================================================================
# Helper Functions
# =============================================================================

def generate_random_birth_data(seed_offset: int = 0) -> dict:
    """Generate random birth data for testing."""
    start_date = datetime(1960, 1, 1)
    end_date = datetime(2005, 12, 31)
    days_range = (end_date - start_date).days
    random_date = start_date + timedelta(days=random.randint(0, days_range))

    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    birth_time = f"{hour:02d}:{minute:02d}"

    city_name, lat, lon, tz = random.choice(CITIES)

    return {
        "birth_date": random_date.strftime("%Y-%m-%d"),
        "birth_time": birth_time,
        "birth_lat": lat,
        "birth_lon": lon,
        "birth_timezone": tz,
        "city": city_name,
    }


def generate_random_transit_date() -> datetime:
    """Generate a random transit date (2020-2025)."""
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 11, 30)
    days_range = (end_date - start_date).days
    return start_date + timedelta(days=random.randint(0, days_range))


def pearson_correlation(x: list[float], y: list[float]) -> float:
    """Calculate Pearson correlation coefficient between two lists."""
    n = len(x)
    if n != len(y) or n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    var_x = sum((xi - mean_x) ** 2 for xi in x)
    var_y = sum((yi - mean_y) ** 2 for yi in y)

    if var_x == 0 or var_y == 0:
        return 0.0

    return numerator / math.sqrt(var_x * var_y)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def meter_score_data():
    """
    Generate meter scores for distribution and correlation analysis.
    Cached at module level to avoid regenerating for each test.
    """
    random.seed(RANDOM_SEED)

    charts_data = []
    for _ in range(N_CHARTS_DISTRIBUTION):
        birth_data = generate_random_birth_data()
        try:
            natal_chart, _ = compute_birth_chart(
                birth_date=birth_data["birth_date"],
                birth_time=birth_data["birth_time"],
                birth_timezone=birth_data["birth_timezone"],
                birth_lat=birth_data["birth_lat"],
                birth_lon=birth_data["birth_lon"]
            )
            charts_data.append(natal_chart)
        except Exception:
            pass

    # Collect meter scores
    meter_scores: dict[str, list[float]] = defaultdict(list)
    total_samples = 0

    for natal_chart in charts_data:
        for _ in range(N_DATES_PER_CHART):
            transit_date = generate_random_transit_date()
            date_str = transit_date.strftime("%Y-%m-%d")

            try:
                transit_chart, _ = compute_birth_chart(date_str, "12:00")
                all_meters = get_meters(
                    natal_chart,
                    transit_chart,
                    transit_date,
                    calculate_trends=False
                )

                for meter_name in METER_NAMES:
                    reading = getattr(all_meters, meter_name)
                    meter_scores[meter_name].append(reading.unified_score)

                total_samples += 1
            except Exception:
                pass

    return {
        "meter_scores": dict(meter_scores),
        "total_samples": total_samples,
        "n_charts": len(charts_data),
    }


@pytest.fixture(scope="module")
def day_correlation_data():
    """
    Generate day-to-day correlation data.
    Cached at module level.
    """
    random.seed(RANDOM_SEED + 1)

    charts = []
    for _ in range(N_CHARTS_DAY_CORR):
        birth_data = generate_random_birth_data()
        try:
            natal_chart, _ = compute_birth_chart(
                birth_date=birth_data["birth_date"],
                birth_time=birth_data["birth_time"],
                birth_timezone=birth_data["birth_timezone"],
                birth_lat=birth_data["birth_lat"],
                birth_lon=birth_data["birth_lon"]
            )
            charts.append(natal_chart)
        except Exception:
            pass

    # Collect day1 vs day2 scores
    day1_scores: dict[str, list[float]] = defaultdict(list)
    day2_scores: dict[str, list[float]] = defaultdict(list)
    total_pairs = 0

    for natal_chart in charts:
        for _ in range(N_DAY_PAIRS):
            start = datetime(2020, 1, 1)
            days_offset = random.randint(0, 365 * 5)
            day1 = start + timedelta(days=days_offset)
            day2 = day1 + timedelta(days=1)

            try:
                transit1, _ = compute_birth_chart(day1.strftime("%Y-%m-%d"), "12:00")
                meters1 = get_meters(natal_chart, transit1, day1, calculate_trends=False)

                transit2, _ = compute_birth_chart(day2.strftime("%Y-%m-%d"), "12:00")
                meters2 = get_meters(natal_chart, transit2, day2, calculate_trends=False)

                for meter_name in METER_NAMES:
                    score1 = getattr(meters1, meter_name).unified_score
                    score2 = getattr(meters2, meter_name).unified_score
                    day1_scores[meter_name].append(score1)
                    day2_scores[meter_name].append(score2)

                # Group scores
                for group_name, group_meters in GROUPS.items():
                    group_score1 = sum(getattr(meters1, m).unified_score for m in group_meters) / len(group_meters)
                    group_score2 = sum(getattr(meters2, m).unified_score for m in group_meters) / len(group_meters)
                    day1_scores[f"GROUP_{group_name}"].append(group_score1)
                    day2_scores[f"GROUP_{group_name}"].append(group_score2)

                # Overall
                overall1 = sum(getattr(meters1, m).unified_score for m in METER_NAMES) / len(METER_NAMES)
                overall2 = sum(getattr(meters2, m).unified_score for m in METER_NAMES) / len(METER_NAMES)
                day1_scores["GROUP_overall"].append(overall1)
                day2_scores["GROUP_overall"].append(overall2)

                total_pairs += 1
            except Exception:
                pass

    return {
        "day1_scores": dict(day1_scores),
        "day2_scores": dict(day2_scores),
        "total_pairs": total_pairs,
    }


@pytest.fixture(scope="module")
def compatibility_data():
    """
    Generate compatibility score data.
    Cached at module level.
    """
    random.seed(RANDOM_SEED + 2)

    charts_data = [generate_random_birth_data() for _ in range(N_CHARTS_COMPAT)]

    overall_scores: list[float] = []
    category_scores: dict[str, list[float]] = defaultdict(list)
    karmic_count = 0
    total_pairs = 0

    for i, user_data in enumerate(charts_data):
        available_indices = [j for j in range(N_CHARTS_COMPAT) if j != i]
        connection_indices = random.sample(
            available_indices,
            min(N_CONNECTIONS, len(available_indices))
        )

        for conn_idx in connection_indices:
            conn_data = charts_data[conn_idx]

            try:
                result = get_compatibility_from_birth_data(
                    user_birth_date=user_data["birth_date"],
                    user_birth_time=user_data["birth_time"],
                    user_birth_lat=user_data["birth_lat"],
                    user_birth_lon=user_data["birth_lon"],
                    user_birth_timezone=user_data["birth_timezone"],
                    connection_birth_date=conn_data["birth_date"],
                    connection_birth_time=conn_data["birth_time"],
                    connection_birth_lat=conn_data["birth_lat"],
                    connection_birth_lon=conn_data["birth_lon"],
                    connection_birth_timezone=conn_data["birth_timezone"],
                    relationship_type="romantic",
                    user_name=f"User_{i}",
                    connection_name=f"Conn_{conn_idx}",
                )

                total_pairs += 1
                overall_scores.append(result.mode.overall_score)

                for cat in result.mode.categories:
                    category_scores[cat.id].append(cat.score)

                if result.karmic.is_karmic:
                    karmic_count += 1

            except Exception:
                pass

    return {
        "overall_scores": overall_scores,
        "category_scores": dict(category_scores),
        "karmic_count": karmic_count,
        "total_pairs": total_pairs,
    }


# =============================================================================
# Meter Distribution Tests
# =============================================================================

class TestMeterDistribution:
    """Tests for meter score distribution quality."""

    def test_sufficient_samples_generated(self, meter_score_data):
        """Should generate enough samples for meaningful statistics."""
        min_expected = N_CHARTS_DISTRIBUTION * N_DATES_PER_CHART * 0.8  # 80% success
        assert meter_score_data["total_samples"] >= min_expected, (
            f"Too few samples: {meter_score_data['total_samples']} < {min_expected}"
        )

    def test_all_meters_have_scores(self, meter_score_data):
        """All 17 meters should have scores."""
        for meter_name in METER_NAMES:
            assert meter_name in meter_score_data["meter_scores"], (
                f"Missing meter: {meter_name}"
            )
            assert len(meter_score_data["meter_scores"][meter_name]) > 0, (
                f"No scores for meter: {meter_name}"
            )

    def test_meter_means_in_range(self, meter_score_data):
        """Meter means should be in [40, 60] range."""
        failures = []
        for meter_name in METER_NAMES:
            scores = meter_score_data["meter_scores"][meter_name]
            mean = statistics.mean(scores)
            if not (40 <= mean <= 60):
                failures.append(f"{meter_name}: mean={mean:.1f}")

        assert len(failures) == 0, (
            f"Meters with means outside [40,60]: {', '.join(failures)}"
        )

    def test_meter_stddevs_reasonable(self, meter_score_data):
        """Meter stddevs should be in [5, 25] range."""
        failures = []
        for meter_name in METER_NAMES:
            scores = meter_score_data["meter_scores"][meter_name]
            if len(scores) > 1:
                stddev = statistics.stdev(scores)
                if not (5 <= stddev <= 25):
                    failures.append(f"{meter_name}: stddev={stddev:.1f}")

        assert len(failures) == 0, (
            f"Meters with stddev outside [5,25]: {', '.join(failures)}"
        )

    def test_meter_scores_in_valid_range(self, meter_score_data):
        """All meter scores should be in [0, 100] range."""
        for meter_name in METER_NAMES:
            scores = meter_score_data["meter_scores"][meter_name]
            min_score = min(scores)
            max_score = max(scores)
            assert 0 <= min_score, (
                f"{meter_name} has score below 0: {min_score}"
            )
            assert max_score <= 100, (
                f"{meter_name} has score above 100: {max_score}"
            )


# =============================================================================
# Meter Correlation Tests
# =============================================================================

class TestMeterCorrelation:
    """Tests for cross-meter correlation (meters should be distinct)."""

    def test_average_cross_meter_correlation_low(self, meter_score_data):
        """Average cross-meter correlation should be < 0.35."""
        scores = meter_score_data["meter_scores"]
        correlations = []

        for i, m1 in enumerate(METER_NAMES):
            for m2 in METER_NAMES[i+1:]:
                corr = pearson_correlation(scores[m1], scores[m2])
                correlations.append(abs(corr))

        avg_corr = sum(correlations) / len(correlations)
        assert avg_corr < 0.35, (
            f"Average cross-meter |correlation| too high: {avg_corr:.3f} >= 0.35"
        )

    def test_no_extreme_meter_correlations(self, meter_score_data):
        """No meter pair should have |correlation| > 0.70."""
        scores = meter_score_data["meter_scores"]
        extreme_pairs = []

        for i, m1 in enumerate(METER_NAMES):
            for m2 in METER_NAMES[i+1:]:
                corr = pearson_correlation(scores[m1], scores[m2])
                if abs(corr) > 0.70:
                    extreme_pairs.append(f"{m1}<->{m2}: {corr:.3f}")

        assert len(extreme_pairs) == 0, (
            f"Meter pairs with extreme correlation (|r|>0.70): {', '.join(extreme_pairs)}"
        )

    def test_within_group_correlation_higher_than_between(self, meter_score_data):
        """
        Meters within same group should be more correlated than between groups.
        This validates the grouping makes semantic sense.
        """
        scores = meter_score_data["meter_scores"]

        within_group_corrs = []
        between_group_corrs = []

        for i, m1 in enumerate(METER_NAMES):
            for m2 in METER_NAMES[i+1:]:
                corr = abs(pearson_correlation(scores[m1], scores[m2]))
                group1 = METER_TO_GROUP_V2.get(Meter(m1))
                group2 = METER_TO_GROUP_V2.get(Meter(m2))

                if group1 == group2:
                    within_group_corrs.append(corr)
                else:
                    between_group_corrs.append(corr)

        avg_within = sum(within_group_corrs) / len(within_group_corrs) if within_group_corrs else 0
        avg_between = sum(between_group_corrs) / len(between_group_corrs) if between_group_corrs else 0

        # Within-group should be at least as high as between-group
        # (allowing small margin for statistical noise)
        assert avg_within >= avg_between - 0.05, (
            f"Within-group avg |r| ({avg_within:.3f}) significantly lower than "
            f"between-group ({avg_between:.3f})"
        )


# =============================================================================
# Day-to-Day Correlation Tests
# =============================================================================

class TestDayCorrelation:
    """Tests for day-to-day score stability."""

    def test_sufficient_day_pairs(self, day_correlation_data):
        """Should generate enough day pairs for meaningful statistics."""
        min_expected = N_CHARTS_DAY_CORR * N_DAY_PAIRS * 0.8
        assert day_correlation_data["total_pairs"] >= min_expected, (
            f"Too few day pairs: {day_correlation_data['total_pairs']} < {min_expected}"
        )

    def test_individual_meter_day_correlation_in_range(self, day_correlation_data):
        """Individual meter day-to-day correlations should be in [0.20, 0.90]."""
        day1 = day_correlation_data["day1_scores"]
        day2 = day_correlation_data["day2_scores"]

        too_volatile = []
        too_stable = []

        for meter_name in METER_NAMES:
            corr = pearson_correlation(day1[meter_name], day2[meter_name])
            if corr < 0.20:
                too_volatile.append(f"{meter_name}: {corr:.3f}")
            elif corr > 0.90:
                too_stable.append(f"{meter_name}: {corr:.3f}")

        failures = []
        if too_volatile:
            failures.append(f"Too volatile (corr<0.20): {', '.join(too_volatile)}")
        if too_stable:
            failures.append(f"Too stable (corr>0.90): {', '.join(too_stable)}")

        assert len(failures) == 0, " | ".join(failures)

    def test_average_day_correlation_moderate(self, day_correlation_data):
        """Average day-to-day correlation should be in [0.35, 0.75]."""
        day1 = day_correlation_data["day1_scores"]
        day2 = day_correlation_data["day2_scores"]

        correlations = []
        for meter_name in METER_NAMES:
            corr = pearson_correlation(day1[meter_name], day2[meter_name])
            correlations.append(corr)

        avg_corr = sum(correlations) / len(correlations)
        assert 0.35 <= avg_corr <= 0.75, (
            f"Average day-to-day correlation out of range: {avg_corr:.3f} not in [0.35, 0.75]"
        )

    def test_group_day_correlation_in_range(self, day_correlation_data):
        """Group-level day correlations should be in [0.35, 0.85]."""
        day1 = day_correlation_data["day1_scores"]
        day2 = day_correlation_data["day2_scores"]

        failures = []
        for group_name in GROUPS.keys():
            key = f"GROUP_{group_name}"
            if key in day1 and key in day2:
                corr = pearson_correlation(day1[key], day2[key])
                if not (0.35 <= corr <= 0.85):
                    failures.append(f"{group_name}: {corr:.3f}")

        assert len(failures) == 0, (
            f"Groups with day correlation outside [0.35, 0.85]: {', '.join(failures)}"
        )

    def test_overall_day_correlation_stable(self, day_correlation_data):
        """Overall day-to-day correlation should be moderately stable (0.45-0.85)."""
        day1 = day_correlation_data["day1_scores"]
        day2 = day_correlation_data["day2_scores"]

        if "GROUP_overall" in day1 and "GROUP_overall" in day2:
            corr = pearson_correlation(day1["GROUP_overall"], day2["GROUP_overall"])
            assert 0.45 <= corr <= 0.85, (
                f"Overall day-to-day correlation out of range: {corr:.3f} not in [0.45, 0.85]"
            )


# =============================================================================
# Compatibility Distribution Tests
# =============================================================================

class TestCompatibilityDistribution:
    """Tests for compatibility score distribution quality."""

    def test_sufficient_compatibility_pairs(self, compatibility_data):
        """Should generate enough pairs for meaningful statistics."""
        min_expected = N_CHARTS_COMPAT * N_CONNECTIONS * 0.7  # 70% success
        assert compatibility_data["total_pairs"] >= min_expected, (
            f"Too few pairs: {compatibility_data['total_pairs']} < {min_expected}"
        )

    def test_overall_score_mean_in_range(self, compatibility_data):
        """Overall compatibility mean should be in [40, 60]."""
        scores = compatibility_data["overall_scores"]
        mean = statistics.mean(scores)
        assert 40 <= mean <= 60, (
            f"Overall mean out of range: {mean:.1f} not in [40, 60]"
        )

    def test_overall_score_stddev_reasonable(self, compatibility_data):
        """Overall compatibility stddev should be in [8, 25]."""
        scores = compatibility_data["overall_scores"]
        if len(scores) > 1:
            stddev = statistics.stdev(scores)
            assert 8 <= stddev <= 25, (
                f"Overall stddev out of range: {stddev:.1f} not in [8, 25]"
            )

    def test_overall_scores_in_valid_range(self, compatibility_data):
        """All overall scores should be in [0, 100]."""
        scores = compatibility_data["overall_scores"]
        min_score = min(scores)
        max_score = max(scores)
        assert 0 <= min_score, f"Overall score below 0: {min_score}"
        assert max_score <= 100, f"Overall score above 100: {max_score}"

    def test_category_means_reasonable(self, compatibility_data):
        """Category means should be in [35, 65] range."""
        category_scores = compatibility_data["category_scores"]
        failures = []

        for cat_id, scores in category_scores.items():
            if scores:
                mean = statistics.mean(scores)
                if not (35 <= mean <= 65):
                    failures.append(f"{cat_id}: {mean:.1f}")

        assert len(failures) == 0, (
            f"Categories with means outside [35, 65]: {', '.join(failures)}"
        )

    def test_karmic_rate_in_range(self, compatibility_data):
        """Karmic rate should be between 2% and 20%."""
        karmic_pct = compatibility_data["karmic_count"] / compatibility_data["total_pairs"] * 100
        assert 2 <= karmic_pct <= 20, (
            f"Karmic rate out of range: {karmic_pct:.1f}% not in [2%, 20%]"
        )


# =============================================================================
# Compatibility Correlation Tests (CRITICAL - excessive correlation)
# =============================================================================

class TestCompatibilityCorrelation:
    """Tests for compatibility category correlation (categories should be distinct)."""

    def test_average_category_correlation_low(self, compatibility_data):
        """Average cross-category correlation should be < 0.40."""
        category_scores = compatibility_data["category_scores"]
        categories = list(category_scores.keys())

        if len(categories) < 2:
            pytest.skip("Not enough categories to test correlation")

        correlations = []
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                if category_scores[cat1] and category_scores[cat2]:
                    # Scores must be same length for correlation
                    min_len = min(len(category_scores[cat1]), len(category_scores[cat2]))
                    corr = pearson_correlation(
                        category_scores[cat1][:min_len],
                        category_scores[cat2][:min_len]
                    )
                    correlations.append(abs(corr))

        if correlations:
            avg_corr = sum(correlations) / len(correlations)
            assert avg_corr < 0.40, (
                f"Average cross-category |correlation| too high: {avg_corr:.3f} >= 0.40"
            )

    def test_no_extreme_category_correlations(self, compatibility_data):
        """No category pair should have |correlation| > 0.65."""
        category_scores = compatibility_data["category_scores"]
        categories = list(category_scores.keys())

        extreme_pairs = []
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                if category_scores[cat1] and category_scores[cat2]:
                    min_len = min(len(category_scores[cat1]), len(category_scores[cat2]))
                    corr = pearson_correlation(
                        category_scores[cat1][:min_len],
                        category_scores[cat2][:min_len]
                    )
                    if abs(corr) > 0.65:
                        extreme_pairs.append(f"{cat1}<->{cat2}: {corr:.3f}")

        assert len(extreme_pairs) == 0, (
            f"Category pairs with extreme correlation (|r|>0.65): {', '.join(extreme_pairs)}"
        )

    def test_categories_not_redundant(self, compatibility_data):
        """
        No category should be highly predictable from another.
        Tests that categories provide independent information.
        """
        category_scores = compatibility_data["category_scores"]
        categories = list(category_scores.keys())

        highly_correlated = []
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                if category_scores[cat1] and category_scores[cat2]:
                    min_len = min(len(category_scores[cat1]), len(category_scores[cat2]))
                    corr = pearson_correlation(
                        category_scores[cat1][:min_len],
                        category_scores[cat2][:min_len]
                    )
                    # r^2 > 0.36 means one explains >36% of variance of the other
                    if corr ** 2 > 0.36:
                        highly_correlated.append(f"{cat1}<->{cat2}: r={corr:.2f}, r^2={corr**2:.2f}")

        assert len(highly_correlated) == 0, (
            f"Category pairs with redundant information (r^2>0.36): {', '.join(highly_correlated)}"
        )


# =============================================================================
# Combined Health Check Test
# =============================================================================

class TestSystemHealthCheck:
    """Combined test that validates overall system health."""

    def test_system_statistical_health(
        self,
        meter_score_data,
        day_correlation_data,
        compatibility_data
    ):
        """
        Comprehensive health check that all major metrics are within bounds.
        This is a summary test - individual tests above provide details on failures.
        """
        issues = []

        # Check meter distribution
        for meter_name in METER_NAMES:
            scores = meter_score_data["meter_scores"].get(meter_name, [])
            if scores:
                mean = statistics.mean(scores)
                if not (40 <= mean <= 60):
                    issues.append(f"Meter {meter_name} mean: {mean:.1f}")

        # Check day correlation
        day1 = day_correlation_data["day1_scores"]
        day2 = day_correlation_data["day2_scores"]
        day_corrs = []
        for meter_name in METER_NAMES:
            if meter_name in day1 and meter_name in day2:
                corr = pearson_correlation(day1[meter_name], day2[meter_name])
                day_corrs.append(corr)

        if day_corrs:
            avg_day_corr = sum(day_corrs) / len(day_corrs)
            if not (0.35 <= avg_day_corr <= 0.75):
                issues.append(f"Avg day correlation: {avg_day_corr:.3f}")

        # Check compatibility
        if compatibility_data["overall_scores"]:
            compat_mean = statistics.mean(compatibility_data["overall_scores"])
            if not (40 <= compat_mean <= 60):
                issues.append(f"Compatibility mean: {compat_mean:.1f}")

        assert len(issues) == 0, f"System health issues: {'; '.join(issues)}"

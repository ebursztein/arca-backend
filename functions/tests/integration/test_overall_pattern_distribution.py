"""
Test overall writing guidance pattern distribution.

Tests N random natal charts on random days to verify the 8 patterns are
distributed reasonably and the pattern detection logic is correct.

Patterns:
- all_flowing: All 5 groups >= 60
- all_challenging: All 5 groups < 40
- mostly_flowing: Multiple groups >= 60, no challenging
- mostly_challenging: Multiple groups < 40, no flowing
- one_challenging: 1 group < 40, no flowing groups
- one_shining: 1 group >= 60, no challenging groups
- mixed_day: At least one >= 60 AND at least one < 40
- neutral_day: All groups in 40-60 range

Usage:
    uv run pytest functions/tests/integration/test_overall_pattern_distribution.py -v -s

    Or run directly:
    uv run python functions/tests/integration/test_overall_pattern_distribution.py [num_charts]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

from astro import compute_birth_chart
from astrometers.meters import get_meters
from astrometers.meter_groups import calculate_group_scores, get_overall_writing_guidance
from astrometers.hierarchy import MeterGroupV2, get_meters_in_group_v2


# Major cities for location diversity
LOCATIONS = [
    ("New York, USA", 40.7128, -74.0060, "America/New_York"),
    ("Los Angeles, USA", 34.0522, -118.2437, "America/Los_Angeles"),
    ("London, UK", 51.5074, -0.1278, "Europe/London"),
    ("Tokyo, Japan", 35.6762, 139.6503, "Asia/Tokyo"),
    ("Sydney, Australia", -33.8688, 151.2093, "Australia/Sydney"),
    ("Paris, France", 48.8566, 2.3522, "Europe/Paris"),
    ("Berlin, Germany", 52.5200, 13.4050, "Europe/Berlin"),
    ("Mumbai, India", 19.0760, 72.8777, "Asia/Kolkata"),
    ("Sao Paulo, Brazil", -23.5505, -46.6333, "America/Sao_Paulo"),
    ("Mexico City, Mexico", 19.4326, -99.1332, "America/Mexico_City"),
]


def generate_random_chart():
    """Generate a random natal chart."""
    start_date = datetime(1950, 1, 1)
    end_date = datetime(2010, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    birth_date = start_date + timedelta(days=random_days)

    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    city, lat, lon, tz = random.choice(LOCATIONS)

    try:
        chart, _ = compute_birth_chart(
            birth_date=birth_date.strftime("%Y-%m-%d"),
            birth_time=f"{hour:02d}:{minute:02d}",
            birth_timezone=tz,
            birth_lat=lat,
            birth_lon=lon
        )
        return chart, birth_date, city
    except Exception:
        return None, None, None


def generate_random_transit_date():
    """Generate a random transit date between 2024-2026."""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    return start_date + timedelta(days=random_days)


def calculate_group_unified_scores(all_meters):
    """Calculate unified scores for all 5 groups from meter readings."""
    group_scores = {}

    for group in MeterGroupV2:
        group_meter_enums = get_meters_in_group_v2(group)
        group_meters = []

        for meter_enum in group_meter_enums:
            meter_reading = getattr(all_meters, meter_enum.value, None)
            if meter_reading:
                group_meters.append(meter_reading)

        if group_meters:
            scores = calculate_group_scores(group_meters)
            group_scores[group.value] = scores["unified_score"]
        else:
            group_scores[group.value] = 50.0

    return group_scores


def analyze_chart(natal_chart, transit_date):
    """Analyze a natal chart on a specific transit date."""
    try:
        transit_chart, _ = compute_birth_chart(
            birth_date=transit_date.strftime("%Y-%m-%d")
        )

        all_meters = get_meters(
            natal_chart,
            transit_chart,
            transit_date,
            calculate_trends=False
        )

        group_scores = calculate_group_unified_scores(all_meters)

        all_groups = [
            {"name": name, "unified_score": score}
            for name, score in group_scores.items()
        ]

        guidance = get_overall_writing_guidance(all_groups, "User")

        # Count zones (thresholds: flowing >= 55, challenging < 45, neutral 45-55)
        below_45 = sum(1 for s in group_scores.values() if s < 45)
        above_55 = sum(1 for s in group_scores.values() if s >= 55)
        in_neutral = sum(1 for s in group_scores.values() if 45 <= s < 55)

        return {
            "success": True,
            "pattern": guidance["pattern"],
            "group_scores": group_scores,
            "strongest_group": guidance["strongest_group"],
            "challenging_group": guidance["challenging_group"],
            "flowing_groups": guidance["flowing_groups"],
            "challenging_groups": guidance["challenging_groups"],
            "below_45": below_45,
            "above_55": above_55,
            "in_neutral": in_neutral,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def verify_pattern_correctness(result):
    """
    Verify that the pattern assigned matches the group score configuration.

    Returns (is_correct, error_message)
    """
    if not result["success"]:
        return True, None  # Skip failed analyses

    pattern = result["pattern"]
    below_45 = result["below_45"]
    above_55 = result["above_55"]
    in_neutral = result["in_neutral"]
    total = below_45 + above_55 + in_neutral

    # Verify pattern logic (thresholds: flowing >= 55, challenging < 45)
    if pattern == "all_flowing":
        if above_55 != total:
            return False, f"all_flowing but only {above_55}/5 groups >= 55"

    elif pattern == "all_challenging":
        if below_45 != total:
            return False, f"all_challenging but only {below_45}/5 groups < 45"

    elif pattern == "mixed_day":
        if above_55 < 1 or below_45 < 1:
            return False, f"mixed_day but flowing={above_55}, challenging={below_45}"

    elif pattern == "one_challenging":
        if below_45 != 1 or above_55 != 0:
            return False, f"one_challenging but below_45={below_45}, above_55={above_55}"

    elif pattern == "one_shining":
        if above_55 != 1 or below_45 != 0:
            return False, f"one_shining but above_55={above_55}, below_45={below_45}"

    elif pattern == "mostly_flowing":
        if above_55 < 2 or below_45 != 0:
            return False, f"mostly_flowing but above_55={above_55}, below_45={below_45}"

    elif pattern == "mostly_challenging":
        if below_45 < 2 or above_55 != 0:
            return False, f"mostly_challenging but below_45={below_45}, above_55={above_55}"

    elif pattern == "neutral_day":
        if below_45 != 0 or above_55 != 0:
            return False, f"neutral_day but below_45={below_45}, above_55={above_55}"

    return True, None


def test_pattern_distribution(num_charts=200, verbose=True):
    """
    Test overall pattern distribution across random charts.

    Verifies:
    1. Pattern detection logic is correct
    2. No single pattern dominates (> 50%)
    3. Distribution is reasonable across patterns
    """
    print("\n" + "=" * 100)
    print(f"OVERALL PATTERN DISTRIBUTION TEST: {num_charts} RANDOM CHARTS x RANDOM DAYS")
    print("=" * 100 + "\n")

    pattern_counts = Counter()
    group_score_samples = {g.value: [] for g in MeterGroupV2}
    strongest_counts = Counter()
    challenging_counts = Counter()
    pattern_errors = []
    failed = 0

    print("Generating and analyzing charts...")
    for i in range(num_charts):
        natal_chart, birth_date, city = generate_random_chart()
        if natal_chart is None:
            failed += 1
            continue

        transit_date = generate_random_transit_date()
        result = analyze_chart(natal_chart, transit_date)

        if result["success"]:
            pattern_counts[result["pattern"]] += 1

            # Verify pattern correctness
            is_correct, error = verify_pattern_correctness(result)
            if not is_correct:
                pattern_errors.append({
                    "chart_num": i + 1,
                    "pattern": result["pattern"],
                    "error": error,
                    "group_scores": result["group_scores"],
                })

            # Track group scores
            for group, score in result["group_scores"].items():
                group_score_samples[group].append(score)

            # Track strongest/challenging
            if result["strongest_group"]:
                strongest_counts[result["strongest_group"]] += 1
            if result["challenging_group"]:
                challenging_counts[result["challenging_group"]] += 1
        else:
            failed += 1

        if (i + 1) % max(1, num_charts // 10) == 0:
            print(f"  Processed {i + 1}/{num_charts} charts...")

    successful = num_charts - failed

    # Results
    print(f"\n{'=' * 100}")
    print("PATTERN DISTRIBUTION")
    print(f"{'=' * 100}\n")

    print(f"Total charts tested: {num_charts}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print()

    all_patterns = [
        "all_flowing", "all_challenging",
        "mostly_flowing", "mostly_challenging",
        "one_shining", "one_challenging",
        "mixed_day", "neutral_day"
    ]

    print("Pattern Distribution:")
    print("-" * 70)
    for pattern in all_patterns:
        count = pattern_counts.get(pattern, 0)
        pct = (count / successful * 100) if successful > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {pattern:20s}: {count:4d} ({pct:5.1f}%) {bar}")

    # Group score statistics
    print(f"\n{'=' * 100}")
    print("GROUP SCORE STATISTICS")
    print(f"{'=' * 100}\n")

    print(f"{'Group':<12} {'Min':>8} {'Max':>8} {'Mean':>8} {'StdDev':>8} {'<40':>8} {'40-60':>8} {'>60':>8}")
    print("-" * 80)

    for group in MeterGroupV2:
        scores = group_score_samples[group.value]
        if scores:
            min_s = min(scores)
            max_s = max(scores)
            mean_s = statistics.mean(scores)
            std_s = statistics.stdev(scores) if len(scores) > 1 else 0
            below_40 = sum(1 for s in scores if s < 40)
            in_40_60 = sum(1 for s in scores if 40 <= s < 60)
            above_60 = sum(1 for s in scores if s >= 60)

            below_40_pct = below_40 / len(scores) * 100
            in_40_60_pct = in_40_60 / len(scores) * 100
            above_60_pct = above_60 / len(scores) * 100

            print(f"{group.value:<12} {min_s:>8.1f} {max_s:>8.1f} {mean_s:>8.1f} {std_s:>8.1f} "
                  f"{below_40_pct:>7.1f}% {in_40_60_pct:>7.1f}% {above_60_pct:>7.1f}%")

    # Pattern errors
    if pattern_errors:
        print(f"\n{'=' * 100}")
        print(f"PATTERN LOGIC ERRORS ({len(pattern_errors)} found)")
        print(f"{'=' * 100}\n")

        for err in pattern_errors[:10]:
            print(f"  Chart #{err['chart_num']}: {err['pattern']}")
            print(f"    Error: {err['error']}")
            print(f"    Scores: {err['group_scores']}")
            print()

    # Analysis
    print(f"\n{'=' * 100}")
    print("ANALYSIS")
    print(f"{'=' * 100}\n")

    issues = []

    # Check for pattern errors
    if pattern_errors:
        issues.append(f"Found {len(pattern_errors)} pattern logic errors")

    # Check if any pattern dominates (> 50%)
    for pattern, count in pattern_counts.items():
        pct = count / successful * 100 if successful > 0 else 0
        if pct > 50:
            issues.append(f"Pattern '{pattern}' dominates ({pct:.1f}%)")

    # Check that we have variety (at least 5 different patterns)
    if len(pattern_counts) < 5:
        issues.append(f"Only {len(pattern_counts)} patterns observed (expected at least 5)")

    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("All checks passed:")
        print("  - Pattern detection logic is correct")
        print("  - No single pattern dominates")
        print("  - Good variety of patterns observed")
        return True


class TestOverallPatternDistribution:
    """
    Integration test: verify overall pattern distribution across random charts.
    """

    def test_pattern_logic_correctness(self):
        """
        Generate 50 random charts and verify pattern detection logic is correct.

        For each chart, verify the assigned pattern matches the actual
        group score configuration.
        """
        errors = []
        num_charts = 50

        for i in range(num_charts):
            natal_chart, _, _ = generate_random_chart()
            if natal_chart is None:
                continue

            transit_date = generate_random_transit_date()
            result = analyze_chart(natal_chart, transit_date)

            if result["success"]:
                is_correct, error = verify_pattern_correctness(result)
                if not is_correct:
                    errors.append({
                        "chart": i,
                        "pattern": result["pattern"],
                        "error": error,
                    })

        assert len(errors) == 0, f"Pattern logic errors: {errors}"

    def test_no_single_pattern_dominates(self):
        """
        Generate 100 random charts and verify no pattern exceeds 50% of results.

        This ensures our pattern detection logic produces reasonable variety.
        """
        pattern_counts = Counter()
        successful = 0

        for _ in range(100):
            natal_chart, _, _ = generate_random_chart()
            if natal_chart is None:
                continue

            transit_date = generate_random_transit_date()
            result = analyze_chart(natal_chart, transit_date)

            if result["success"]:
                pattern_counts[result["pattern"]] += 1
                successful += 1

        # Check no pattern exceeds 50%
        for pattern, count in pattern_counts.items():
            pct = count / successful * 100 if successful > 0 else 0
            assert pct <= 50, f"Pattern '{pattern}' dominates at {pct:.1f}%"

    def test_pattern_variety(self):
        """
        Generate 150 random charts and verify we see at least 5 different patterns.

        This ensures our pattern detection covers the full range of scenarios.
        """
        pattern_counts = Counter()

        for _ in range(150):
            natal_chart, _, _ = generate_random_chart()
            if natal_chart is None:
                continue

            transit_date = generate_random_transit_date()
            result = analyze_chart(natal_chart, transit_date)

            if result["success"]:
                pattern_counts[result["pattern"]] += 1

        assert len(pattern_counts) >= 5, \
            f"Only {len(pattern_counts)} patterns observed: {list(pattern_counts.keys())}"

    def test_group_score_distribution(self):
        """
        Verify group scores are well-distributed and not clustered around 50.

        Each group should have scores spanning at least 30 points of range.
        """
        group_scores = defaultdict(list)

        for _ in range(100):
            natal_chart, _, _ = generate_random_chart()
            if natal_chart is None:
                continue

            transit_date = generate_random_transit_date()
            result = analyze_chart(natal_chart, transit_date)

            if result["success"]:
                for group, score in result["group_scores"].items():
                    group_scores[group].append(score)

        for group, scores in group_scores.items():
            if len(scores) < 10:
                continue

            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score

            assert score_range >= 30, \
                f"{group} scores too clustered: range={score_range:.1f}"


if __name__ == "__main__":
    num_charts = 200
    if len(sys.argv) > 1:
        try:
            num_charts = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [num_charts]")
            sys.exit(1)

    success = test_pattern_distribution(num_charts)
    sys.exit(0 if success else 1)

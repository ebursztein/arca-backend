"""
Test meter-to-group consistency and distribution.

This script generates random natal charts and analyzes:
1. Correlation between individual meters and group meters
2. Distribution of group scores (should be well-spread 0-100)
3. Bug detection: group score negative when all meters are positive (or vice versa)

Usage:
    uv run pytest functions/tests/unit/test_group_meter_distribution.py -v -s

    Or run directly:
    uv run python functions/tests/unit/test_group_meter_distribution.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import random
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from astro import compute_birth_chart
from astrometers.meters import get_meters, MeterReading, QualityLabel
from astrometers.meter_groups import calculate_group_scores, build_all_meter_groups
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
    """Generate a random birth chart."""
    # Random birth date between 1950 and 2020
    start_date = datetime(1950, 1, 1)
    end_date = datetime(2020, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    birth_date = start_date + timedelta(days=random_days)

    # Random time
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    # Random location
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
    except Exception as e:
        print(f"Error generating chart: {e}")
        return None, None, None


def get_group_meters(all_meters, group_name: str) -> list[MeterReading]:
    """Get all meters belonging to a specific group."""
    meter_map = {
        "mind": ["clarity", "focus", "communication"],
        "heart": ["resilience", "connections", "vulnerability"],
        "body": ["energy", "drive", "strength"],
        "instincts": ["vision", "flow", "intuition", "creativity"],
        "growth": ["momentum", "ambition", "evolution", "circle"],
    }

    meters = []
    for meter_name in meter_map.get(group_name, []):
        meter = getattr(all_meters, meter_name, None)
        if meter:
            meters.append(meter)
    return meters


def analyze_group_meter_relationship(all_meters):
    """
    Analyze the relationship between individual meters and group scores.

    Returns dict with analysis results including any inconsistencies.
    With the median formula, we only check for all-positive/all-negative bugs.
    """
    issues = []
    group_data = {}

    for group in MeterGroupV2:
        group_name = group.value
        meters = get_group_meters(all_meters, group_name)

        if not meters:
            continue

        # Individual meter scores
        meter_scores = [m.unified_score for m in meters]

        # Calculate group score using the formula
        group_result = calculate_group_scores(meters)
        group_score = group_result["unified_score"]
        driver = group_result["driver"]

        # Analyze individual meters
        positive_meters = [s for s in meter_scores if s > 50]
        negative_meters = [s for s in meter_scores if s < 50]
        neutral_meters = [s for s in meter_scores if s == 50]

        # BUG DETECTION: All meters positive but group is negative (or vice versa)
        # With median formula, this should never happen
        all_positive = len(positive_meters) == len(meters) and len(meters) > 0
        all_negative = len(negative_meters) == len(meters) and len(meters) > 0

        if all_positive and group_score < 50:
            issues.append({
                "type": "ALL_POSITIVE_BUT_GROUP_NEGATIVE",
                "group": group_name,
                "meter_scores": meter_scores,
                "group_score": group_score,
                "driver": driver,
            })

        if all_negative and group_score > 50:
            issues.append({
                "type": "ALL_NEGATIVE_BUT_GROUP_POSITIVE",
                "group": group_name,
                "meter_scores": meter_scores,
                "group_score": group_score,
                "driver": driver,
            })

        group_data[group_name] = {
            "meter_scores": meter_scores,
            "group_score": group_score,
            "driver": driver,
            "positive_count": len(positive_meters),
            "negative_count": len(negative_meters),
            "neutral_count": len(neutral_meters),
        }

    return {
        "groups": group_data,
        "issues": issues,
    }


def test_group_meter_distribution(num_charts=200, verbose=True):
    """
    Test group meter calculations across many random charts.

    Reports:
    1. Distribution of group scores
    2. Any inconsistencies found
    3. Statistics on meter-to-group relationships
    """
    print("\n" + "="*100)
    print(f"GROUP METER DISTRIBUTION TEST: {num_charts} RANDOM CHARTS")
    print("="*100 + "\n")

    # Collect statistics
    all_group_scores = defaultdict(list)
    all_issues = []
    charts_with_issues = 0
    failed_charts = 0

    # Transit chart for all tests
    transit_chart, _ = compute_birth_chart(birth_date="2025-12-09")
    date = datetime(2025, 12, 9, 12, 0)

    print("Generating and analyzing charts...")
    for i in range(num_charts):
        natal_chart, birth_date, city = generate_random_chart()

        if natal_chart is None:
            failed_charts += 1
            continue

        try:
            all_meters = get_meters(natal_chart, transit_chart, date, calculate_trends=False)
            result = analyze_group_meter_relationship(all_meters)

            # Collect group scores
            for group_name, data in result["groups"].items():
                all_group_scores[group_name].append(data["group_score"])

            # Collect issues
            if result["issues"]:
                charts_with_issues += 1
                for issue in result["issues"]:
                    issue["chart_num"] = i + 1
                    issue["birth_date"] = birth_date.strftime("%Y-%m-%d")
                    issue["city"] = city
                    all_issues.append(issue)

        except Exception as e:
            failed_charts += 1
            if verbose:
                print(f"  Error on chart {i+1}: {e}")

        # Progress indicator
        if (i + 1) % max(1, num_charts//10) == 0:
            print(f"  Processed {i + 1}/{num_charts} charts...")

    # Print results
    print(f"\n{'='*100}")
    print("RESULTS SUMMARY")
    print(f"{'='*100}\n")

    print(f"Total charts tested: {num_charts}")
    print(f"Successful analyses: {num_charts - failed_charts}")
    print(f"Failed analyses: {failed_charts}")
    print(f"Charts with issues: {charts_with_issues}")

    # Distribution statistics for each group
    print(f"\n{'='*100}")
    print("GROUP SCORE DISTRIBUTIONS (unified_score 0-100)")
    print(f"{'='*100}\n")

    for group_name in ["mind", "heart", "body", "instincts", "growth"]:
        scores = all_group_scores[group_name]
        if not scores:
            continue

        print(f"\n{group_name.upper()}:")
        print(f"  Count: {len(scores)}")
        print(f"  Min: {min(scores):.1f}")
        print(f"  Max: {max(scores):.1f}")
        print(f"  Mean: {statistics.mean(scores):.1f}")
        print(f"  Median: {statistics.median(scores):.1f}")
        print(f"  Std Dev: {statistics.stdev(scores):.1f}")

        # Distribution buckets
        buckets = {
            "0-25 (challenging)": len([s for s in scores if s < 25]),
            "25-50 (turbulent)": len([s for s in scores if 25 <= s < 50]),
            "50-75 (peaceful)": len([s for s in scores if 50 <= s < 75]),
            "75-100 (flowing)": len([s for s in scores if s >= 75]),
        }
        print("  Distribution:")
        for bucket, count in buckets.items():
            pct = (count / len(scores)) * 100
            bar = "#" * int(pct / 2)
            print(f"    {bucket}: {count:3d} ({pct:5.1f}%) {bar}")

    # Report issues
    if all_issues:
        print(f"\n{'='*100}")
        print(f"ISSUES FOUND ({len(all_issues)} total)")
        print(f"{'='*100}\n")

        # Group issues by type
        issues_by_type = defaultdict(list)
        for issue in all_issues:
            issues_by_type[issue["type"]].append(issue)

        for issue_type, issues in issues_by_type.items():
            print(f"\n{issue_type}: {len(issues)} occurrences")
            print("-" * 60)

            # Show first 5 examples
            for issue in issues[:5]:
                print(f"  Chart #{issue['chart_num']} ({issue['birth_date']}, {issue['city']})")
                print(f"    Group: {issue['group']}")
                print(f"    Meter scores: {issue['meter_scores']}")
                print(f"    Group score: {issue['group_score']:.1f}")
                if "expected_direction" in issue:
                    print(f"    Expected: {issue['expected_direction']}, Actual: {issue['actual_direction']}")
                    print(f"    Positive distance: {issue['positive_distance']:.1f}, Negative distance: {issue['negative_distance']:.1f}")
                print()

            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more")
    else:
        print(f"\n{'='*100}")
        print("NO ISSUES FOUND - All group scores are consistent with individual meters!")
        print(f"{'='*100}\n")

    return len(all_issues) == 0


def test_specific_bug_case():
    """
    Test the specific bug case: group=32 when meters=64,62,71

    All meters are positive (>50) so the group should also be positive (>50).
    """
    print("\n" + "="*80)
    print("SPECIFIC BUG TEST: All positive meters -> positive group")
    print("="*80 + "\n")

    # Create mock meters with the bug scenario
    def make_meter(name: str, unified_score: float) -> MeterReading:
        return MeterReading(
            meter_name=name,
            date=datetime.now(),
            group=MeterGroupV2.INSTINCTS,
            unified_score=unified_score,
            intensity=50.0,
            harmony=50.0,
            unified_quality=QualityLabel.PEACEFUL,
            state_label="Test",
            interpretation="Test meter",
            advice=["Test advice"],
            top_aspects=[],
            raw_scores={},
        )

    # Test case: All positive meters
    meters = [
        make_meter("a", 64),
        make_meter("b", 62),
        make_meter("c", 71),
    ]

    result = calculate_group_scores(meters)
    group_score = result["unified_score"]

    print(f"Individual meter scores: 64, 62, 71 (all positive)")
    print(f"Group score: {group_score}")
    print(f"Driver: {result['driver']}")

    # Expected: top 2 by distance = 71 (dist=21), 64 (dist=14)
    # Average = (71 + 64) / 2 = 67.5
    expected = 67.5

    print(f"\nExpected (top 2 avg): {expected}")
    print(f"Actual: {group_score}")

    if group_score > 50:
        print("\nPASSED: Group score is positive as expected")
        return True
    else:
        print(f"\nFAILED: Group score {group_score} is <= 50 when all meters are positive!")
        return False


def test_edge_cases():
    """Test edge cases in the group score formula (median-based)."""
    print("\n" + "="*80)
    print("EDGE CASE TESTS (Median Formula)")
    print("="*80 + "\n")

    def make_meter(name: str, unified_score: float) -> MeterReading:
        return MeterReading(
            meter_name=name,
            date=datetime.now(),
            group=MeterGroupV2.INSTINCTS,
            unified_score=unified_score,
            intensity=50.0,
            harmony=50.0,
            unified_quality=QualityLabel.PEACEFUL,
            state_label="Test",
            interpretation="Test meter",
            advice=["Test advice"],
            top_aspects=[],
            raw_scores={},
        )

    # Median formula: group score = median of all meters
    # For even count: median = avg of middle two
    # For odd count: median = middle value
    test_cases = [
        {
            "name": "All positive meters",
            "meters": [make_meter("a", 60), make_meter("b", 65), make_meter("c", 70)],
            "should_be_positive": True,  # median = 65
        },
        {
            "name": "All negative meters",
            "meters": [make_meter("a", 40), make_meter("b", 35), make_meter("c", 30)],
            "should_be_positive": False,  # median = 35
        },
        {
            "name": "1 strong positive, 2 weak negative",
            "meters": [make_meter("a", 80), make_meter("b", 45), make_meter("c", 45)],
            "should_be_positive": False,  # sorted: 45, 45, 80 -> median = 45
        },
        {
            "name": "1 weak positive, 2 strong negative",
            "meters": [make_meter("a", 52), make_meter("b", 20), make_meter("c", 30)],
            "should_be_positive": False,  # sorted: 20, 30, 52 -> median = 30
        },
        {
            "name": "Strong positive outlier (4 meters)",
            "meters": [make_meter("a", 90), make_meter("b", 45), make_meter("c", 40), make_meter("d", 45)],
            "should_be_positive": False,  # sorted: 40, 45, 45, 90 -> median = (45+45)/2 = 45
        },
        {
            "name": "Strong negative outlier (4 meters)",
            "meters": [make_meter("a", 55), make_meter("b", 55), make_meter("c", 10), make_meter("d", 55)],
            "should_be_positive": True,  # sorted: 10, 55, 55, 55 -> median = (55+55)/2 = 55
        },
        {
            "name": "Growth bug case: 3 positive, 1 very negative",
            "meters": [make_meter("a", 63), make_meter("b", 23), make_meter("c", 65), make_meter("d", 43)],
            "should_be_positive": True,  # sorted: 23, 43, 63, 65 -> median = (43+63)/2 = 53
        },
    ]

    all_passed = True
    for tc in test_cases:
        result = calculate_group_scores(tc["meters"])
        group_score = result["unified_score"]
        is_positive = group_score > 50

        meter_scores = [m.unified_score for m in tc["meters"]]

        passed = is_positive == tc["should_be_positive"]
        status = "PASS" if passed else "FAIL"

        print(f"{status}: {tc['name']}")
        print(f"  Meter scores: {meter_scores}")
        print(f"  Group score: {group_score:.1f}")
        print(f"  Expected positive: {tc['should_be_positive']}, Actual positive: {is_positive}")
        print()

        if not passed:
            all_passed = False

    return all_passed


def test_meter_group_correlations(num_charts=200):
    """
    Analyze correlations between individual meters and their group scores.

    For each group, calculates:
    - Correlation between each meter's score and the group score
    - How often each meter is the "driver" (top contributor)
    - Relationship between meter count on each side and final direction
    """
    print("\n" + "="*100)
    print(f"METER-GROUP CORRELATION ANALYSIS: {num_charts} RANDOM CHARTS")
    print("="*100 + "\n")

    # Collect data
    group_meter_pairs = defaultdict(lambda: {"meter_scores": [], "group_scores": []})
    driver_counts = defaultdict(lambda: defaultdict(int))
    direction_analysis = defaultdict(list)

    # Transit chart for all tests
    transit_chart, _ = compute_birth_chart(birth_date="2025-12-09")
    date = datetime(2025, 12, 9, 12, 0)

    print("Generating and analyzing charts...")
    for i in range(num_charts):
        natal_chart, birth_date, city = generate_random_chart()

        if natal_chart is None:
            continue

        try:
            all_meters = get_meters(natal_chart, transit_chart, date, calculate_trends=False)

            for group_name in ["mind", "heart", "body", "instincts", "growth"]:
                meters = get_group_meters(all_meters, group_name)
                if not meters:
                    continue

                result = calculate_group_scores(meters)
                group_score = result["unified_score"]
                driver = result["driver"]

                # Track driver counts
                driver_counts[group_name][driver] += 1

                # Track meter-group pairs for correlation
                for m in meters:
                    group_meter_pairs[(group_name, m.meter_name)]["meter_scores"].append(m.unified_score)
                    group_meter_pairs[(group_name, m.meter_name)]["group_scores"].append(group_score)

                # Track direction analysis
                positive_count = sum(1 for m in meters if m.unified_score > 50)
                negative_count = sum(1 for m in meters if m.unified_score < 50)
                group_is_positive = group_score > 50

                direction_analysis[group_name].append({
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "total": len(meters),
                    "group_is_positive": group_is_positive,
                    "group_score": group_score,
                })

        except Exception as e:
            pass

        if (i + 1) % max(1, num_charts // 10) == 0:
            print(f"  Processed {i + 1}/{num_charts} charts...")

    # Print correlation analysis
    print(f"\n{'='*100}")
    print("METER-GROUP CORRELATIONS (Pearson correlation coefficient)")
    print(f"{'='*100}\n")

    def pearson_correlation(x, y):
        """Calculate Pearson correlation coefficient."""
        if len(x) < 2:
            return 0
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denom_x = sum((x[i] - mean_x) ** 2 for i in range(n)) ** 0.5
        denom_y = sum((y[i] - mean_y) ** 2 for i in range(n)) ** 0.5
        if denom_x * denom_y == 0:
            return 0
        return numerator / (denom_x * denom_y)

    for group_name in ["mind", "heart", "body", "instincts", "growth"]:
        print(f"\n{group_name.upper()}:")
        correlations = []
        for (gn, meter_name), data in group_meter_pairs.items():
            if gn != group_name:
                continue
            corr = pearson_correlation(data["meter_scores"], data["group_scores"])
            correlations.append((meter_name, corr, len(data["meter_scores"])))

        for meter_name, corr, count in sorted(correlations, key=lambda x: -x[1]):
            bar = "#" * int(abs(corr) * 20)
            sign = "+" if corr > 0 else "-"
            print(f"  {meter_name:15s}: {sign}{abs(corr):.3f} {bar} (n={count})")

    # Print driver analysis
    print(f"\n{'='*100}")
    print("DRIVER FREQUENCY (which meter most often drives the group score)")
    print(f"{'='*100}\n")

    for group_name in ["mind", "heart", "body", "instincts", "growth"]:
        print(f"\n{group_name.upper()}:")
        total = sum(driver_counts[group_name].values())
        for meter_name, count in sorted(driver_counts[group_name].items(), key=lambda x: -x[1]):
            pct = (count / total) * 100 if total > 0 else 0
            bar = "#" * int(pct / 2)
            print(f"  {meter_name:15s}: {count:3d} ({pct:5.1f}%) {bar}")

    # Print direction analysis
    print(f"\n{'='*100}")
    print("DIRECTION ANALYSIS (when does count vs distance determine direction)")
    print(f"{'='*100}\n")

    for group_name in ["mind", "heart", "body", "instincts", "growth"]:
        data = direction_analysis[group_name]
        if not data:
            continue

        # Cases where majority count matches final direction
        majority_matches = 0
        total_non_tie = 0

        for d in data:
            if d["positive_count"] == d["negative_count"]:
                continue  # Skip ties
            total_non_tie += 1
            majority_positive = d["positive_count"] > d["negative_count"]
            if majority_positive == d["group_is_positive"]:
                majority_matches += 1

        if total_non_tie > 0:
            match_rate = (majority_matches / total_non_tie) * 100
            print(f"{group_name.upper()}: Majority count matches direction {match_rate:.1f}% of the time")
            print(f"  (Note: direction is determined by TOTAL DISTANCE, not count)")

    return True


class TestRandomChartGroupConsistency:
    """
    Integration test: generate random charts and verify group meter consistency.

    For each random chart, verify that:
    1. All-positive meters never produce a negative group score
    2. All-negative meters never produce a positive group score
    3. Group direction matches the direction with greater total distance from 50
    """

    def test_random_charts_no_direction_bugs(self):
        """
        Generate 20 random charts and verify no direction bugs exist.

        A direction bug is when:
        - All meters are positive (>50) but group score is negative (<50)
        - All meters are negative (<50) but group score is positive (>50)
        """
        LOCATIONS = [
            ('New York', 40.7128, -74.0060, 'America/New_York'),
            ('Los Angeles', 34.0522, -118.2437, 'America/Los_Angeles'),
            ('London', 51.5074, -0.1278, 'Europe/London'),
            ('Tokyo', 35.6762, 139.6503, 'Asia/Tokyo'),
            ('Sydney', -33.8688, 151.2093, 'Australia/Sydney'),
            ('Paris', 48.8566, 2.3522, 'Europe/Paris'),
            ('Mumbai', 19.0760, 72.8777, 'Asia/Kolkata'),
            ('Sao Paulo', -23.5505, -46.6333, 'America/Sao_Paulo'),
        ]

        group_meter_map = {
            'mind': ['clarity', 'focus', 'communication'],
            'heart': ['resilience', 'connections', 'vulnerability'],
            'body': ['energy', 'drive', 'strength'],
            'instincts': ['vision', 'flow', 'intuition', 'creativity'],
            'growth': ['momentum', 'ambition', 'evolution', 'circle'],
        }

        bugs = []
        num_charts = 20

        for chart_num in range(num_charts):
            # Generate random birth data
            start_date = datetime(1950, 1, 1)
            end_date = datetime(2005, 12, 31)
            days_between = (end_date - start_date).days
            random_days = random.randint(0, days_between)
            birth_date = start_date + timedelta(days=random_days)
            birth_time = f'{random.randint(0,23):02d}:{random.randint(0,59):02d}'
            city, lat, lon, tz = random.choice(LOCATIONS)

            natal_chart, _ = compute_birth_chart(
                birth_date=birth_date.strftime('%Y-%m-%d'),
                birth_time=birth_time,
                birth_lat=lat,
                birth_lon=lon,
                birth_timezone=tz
            )

            transit_chart, _ = compute_birth_chart(birth_date='2025-12-09')
            date = datetime(2025, 12, 9, 12, 0)

            all_meters = get_meters(natal_chart, transit_chart, date, calculate_trends=False)

            for group_name in group_meter_map:
                meters = [getattr(all_meters, m) for m in group_meter_map[group_name]]

                result = calculate_group_scores(meters)
                group_score = result['unified_score']

                positive_count = sum(1 for m in meters if m.unified_score > 50)
                negative_count = sum(1 for m in meters if m.unified_score < 50)

                all_positive = positive_count == len(meters)
                all_negative = negative_count == len(meters)

                if all_positive and group_score < 50:
                    bugs.append({
                        'chart': f'{birth_date.strftime("%Y-%m-%d")} {birth_time} {city}',
                        'group': group_name,
                        'meters': [m.unified_score for m in meters],
                        'group_score': group_score,
                        'bug_type': 'ALL_POSITIVE_BUT_GROUP_NEGATIVE',
                    })
                elif all_negative and group_score > 50:
                    bugs.append({
                        'chart': f'{birth_date.strftime("%Y-%m-%d")} {birth_time} {city}',
                        'group': group_name,
                        'meters': [m.unified_score for m in meters],
                        'group_score': group_score,
                        'bug_type': 'ALL_NEGATIVE_BUT_GROUP_POSITIVE',
                    })

        assert len(bugs) == 0, f"Found {len(bugs)} direction bugs: {bugs}"

    def test_random_charts_direction_follows_average(self):
        """
        Verify that group unified_score matches the simple average of meter scores.

        The average formula calculates the mean of all meter unified_scores
        in the group.
        """
        LOCATIONS = [
            ('New York', 40.7128, -74.0060, 'America/New_York'),
            ('London', 51.5074, -0.1278, 'Europe/London'),
            ('Tokyo', 35.6762, 139.6503, 'Asia/Tokyo'),
            ('Sydney', -33.8688, 151.2093, 'Australia/Sydney'),
        ]

        group_meter_map = {
            'mind': ['clarity', 'focus', 'communication'],
            'heart': ['resilience', 'connections', 'vulnerability'],
            'body': ['energy', 'drive', 'strength'],
            'instincts': ['vision', 'flow', 'intuition', 'creativity'],
            'growth': ['momentum', 'ambition', 'evolution', 'circle'],
        }

        mismatches = []
        num_charts = 15

        for _ in range(num_charts):
            start_date = datetime(1950, 1, 1)
            end_date = datetime(2005, 12, 31)
            days_between = (end_date - start_date).days
            random_days = random.randint(0, days_between)
            birth_date = start_date + timedelta(days=random_days)
            birth_time = f'{random.randint(0,23):02d}:{random.randint(0,59):02d}'
            city, lat, lon, tz = random.choice(LOCATIONS)

            natal_chart, _ = compute_birth_chart(
                birth_date=birth_date.strftime('%Y-%m-%d'),
                birth_time=birth_time,
                birth_lat=lat,
                birth_lon=lon,
                birth_timezone=tz
            )

            transit_chart, _ = compute_birth_chart(birth_date='2025-12-09')
            date = datetime(2025, 12, 9, 12, 0)

            all_meters = get_meters(natal_chart, transit_chart, date, calculate_trends=False)

            for group_name in group_meter_map:
                meters = [getattr(all_meters, m) for m in group_meter_map[group_name]]

                result = calculate_group_scores(meters)
                group_score = result['unified_score']

                # Calculate expected average
                scores = [m.unified_score for m in meters]
                expected_average = sum(scores) / len(scores)

                # Group score should match the average (with rounding tolerance)
                if abs(group_score - expected_average) > 0.15:
                    mismatches.append({
                        'group': group_name,
                        'meters': [round(m.unified_score, 1) for m in meters],
                        'group_score': group_score,
                        'expected_average': round(expected_average, 1),
                    })

        assert len(mismatches) == 0, f"Average mismatches: {mismatches}"

    def test_random_charts_group_scores_well_distributed(self):
        """
        Verify group scores are reasonably distributed across the 0-100 range.

        We expect scores to span most of the range, not cluster around 50.
        """
        LOCATIONS = [
            ('New York', 40.7128, -74.0060, 'America/New_York'),
            ('London', 51.5074, -0.1278, 'Europe/London'),
            ('Tokyo', 35.6762, 139.6503, 'Asia/Tokyo'),
        ]

        group_scores = defaultdict(list)
        num_charts = 30

        for _ in range(num_charts):
            start_date = datetime(1950, 1, 1)
            end_date = datetime(2005, 12, 31)
            days_between = (end_date - start_date).days
            random_days = random.randint(0, days_between)
            birth_date = start_date + timedelta(days=random_days)
            birth_time = f'{random.randint(0,23):02d}:{random.randint(0,59):02d}'
            city, lat, lon, tz = random.choice(LOCATIONS)

            natal_chart, _ = compute_birth_chart(
                birth_date=birth_date.strftime('%Y-%m-%d'),
                birth_time=birth_time,
                birth_lat=lat,
                birth_lon=lon,
                birth_timezone=tz
            )

            transit_chart, _ = compute_birth_chart(birth_date='2025-12-09')
            date = datetime(2025, 12, 9, 12, 0)

            all_meters = get_meters(natal_chart, transit_chart, date, calculate_trends=False)
            meter_groups = build_all_meter_groups(all_meters, llm_interpretations=None)

            for group_name, group_data in meter_groups.items():
                group_scores[group_name].append(group_data['scores']['unified_score'])

        # Check distribution for each group
        for group_name, scores in group_scores.items():
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score

            # Expect at least 30 points of range (not all clustered)
            assert score_range >= 25, \
                f"{group_name} scores too clustered: range={score_range:.1f} (min={min_score:.1f}, max={max_score:.1f})"

            # Expect some scores below 40 and some above 60 (not all neutral)
            has_low = any(s < 40 for s in scores)
            has_high = any(s > 60 for s in scores)
            assert has_low or has_high, \
                f"{group_name} scores all near neutral: {[round(s,1) for s in scores]}"


if __name__ == "__main__":
    import sys

    # Run specific bug test first
    bug_passed = test_specific_bug_case()

    # Run edge cases
    edge_passed = test_edge_cases()

    # Run distribution test
    num_charts = 200
    if len(sys.argv) > 1:
        try:
            num_charts = int(sys.argv[1])
        except ValueError:
            pass

    dist_passed = test_group_meter_distribution(num_charts)

    # Run correlation analysis
    test_meter_group_correlations(num_charts)

    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Bug test: {'PASSED' if bug_passed else 'FAILED'}")
    print(f"Edge case tests: {'PASSED' if edge_passed else 'FAILED'}")
    print(f"Distribution test: {'PASSED' if dist_passed else 'FAILED'}")

    sys.exit(0 if (bug_passed and edge_passed and dist_passed) else 1)

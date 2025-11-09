"""
Stress test: Run meter overlap analysis on NUM_CHARTS diverse birth charts.

This ensures fixes are robust across a wide variety of natal configurations.

NEW: Analyze daily change distributions to determine trend thresholds.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta
from astro import compute_birth_chart
from functions.astrometers.meters_v1 import get_meters, _calculate_meters_no_trends
import numpy as np


# Major cities for location diversity
LOCATIONS = [
    # --- Original List ---
    ("New York, USA", 40.7128, -74.0060, "America/New_York"),
    ("Los Angeles, USA", 34.0522, -118.2437, "America/Los_Angeles"),
    ("London, UK", 51.5074, -0.1278, "Europe/London"),
    ("Tokyo, Japan", 35.6762, 139.6503, "Asia/Tokyo"),
    ("Sydney, Australia", -33.8688, 151.2093, "Australia/Sydney"),
    ("Paris, France", 48.8566, 2.3522, "Europe/Paris"),
    ("Berlin, Germany", 52.5200, 13.4050, "Europe/Berlin"),
    ("Mumbai, India", 19.0760, 72.8777, "Asia/Kolkata"),
    ("São Paulo, Brazil", -23.5505, -46.6333, "America/Sao_Paulo"),
    ("Mexico City, Mexico", 19.4326, -99.1332, "America/Mexico_City"),

    # --- Expanded List ---
    # North America
    ("Chicago, USA", 41.8781, -87.6298, "America/Chicago"),
    ("Toronto, Canada", 43.6532, -79.3832, "America/Toronto"),
    ("Vancouver, Canada", 49.2827, -123.1207, "America/Vancouver"),

    # South America
    ("Buenos Aires, Argentina", -34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
    ("Rio de Janeiro, Brazil", -22.9068, -43.1729, "America/Sao_Paulo"),
    ("Lima, Peru", -12.0464, -77.0428, "America/Lima"),

    # Europe
    ("Moscow, Russia", 55.7558, 37.6173, "Europe/Moscow"),
    ("Madrid, Spain", 40.4168, -3.7038, "Europe/Madrid"),
    ("Rome, Italy", 41.9028, 12.4964, "Europe/Rome"),
    ("Amsterdam, Netherlands", 52.3676, 4.9041, "Europe/Amsterdam"),
    ("Istanbul, Turkey", 41.0082, 28.9784, "Europe/Istanbul"),

    # Asia
    ("Beijing, China", 39.9042, 116.4074, "Asia/Shanghai"),
    ("Dubai, UAE", 25.276987, 55.296249, "Asia/Dubai"),
    ("Singapore, Singapore", 1.3521, 103.8198, "Asia/Singapore"),
    ("Hong Kong, Hong Kong", 22.3193, 114.1694, "Asia/Hong_Kong"),
    ("Seoul, South Korea", 37.5665, 126.9780, "Asia/Seoul"),
    ("Bangkok, Thailand", 13.7563, 100.5018, "Asia/Bangkok"),

    # Africa
    ("Cairo, Egypt", 30.0444, 31.2357, "Africa/Cairo"),
    ("Johannesburg, South Africa", -26.2041, 28.0473, "Africa/Johannesburg"),
    ("Nairobi, Kenya", -1.2921, 36.8219, "Africa/Nairobi"),

    # Oceania
    ("Auckland, New Zealand", -36.8485, 174.7633, "Pacific/Auckland"),
    ("Melbourne, Australia", -37.8136, 144.9631, "Australia/Melbourne"),
]


def generate_random_chart():
    """Generate a random birth chart."""

    # Random birth date between 1950 and 2010
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


def analyze_chart_overlaps(natal_chart):
    """Analyze overlaps for a single chart."""

    # Use same transit date for all tests
    transit_chart, _ = compute_birth_chart(birth_date="2025-10-26")
    date = datetime(2025, 10, 26, 12, 0)

    try:
        # Calculate meters
        meters = get_meters(natal_chart, transit_chart, date)

        # Get all meter readings
        all_readings = [
            meters.overall_intensity,
            meters.overall_harmony,
            meters.fire_energy,
            meters.earth_energy,
            meters.air_energy,
            meters.water_energy,
            meters.mental_clarity,
            meters.decision_quality,
            meters.communication_flow,
            meters.emotional_intensity,
            meters.relationship_harmony,
            meters.emotional_resilience,
            meters.physical_energy,
            meters.conflict_risk,
            meters.motivation_drive,
            meters.career_ambition,
            meters.opportunity_window,
            meters.challenge_intensity,
            meters.transformation_pressure,
            meters.intuition_spirituality,
            meters.innovation_breakthrough,
            meters.karmic_lessons,
            meters.social_collective,
        ]

        # Build aspect sets (excluding overall meters which are intentionally identical)
        meters_to_test = [m for m in all_readings if m.meter_name not in ['overall_intensity', 'overall_harmony']]

        aspect_sets = {}
        for reading in meters_to_test:
            aspect_set = set(
                (a.natal_planet, a.transit_planet, a.aspect_type)
                for a in reading.top_aspects
            )
            aspect_sets[reading.meter_name] = aspect_set

        # Find identical pairs
        identical_pairs = []
        for i, reading1 in enumerate(meters_to_test):
            for reading2 in meters_to_test[i+1:]:
                set1 = aspect_sets[reading1.meter_name]
                set2 = aspect_sets[reading2.meter_name]

                if set1 and set2 and set1 == set2:
                    identical_pairs.append((reading1.meter_name, reading2.meter_name))

        return {
            'success': True,
            'identical_pairs': identical_pairs,
            'total_aspects': len(all_readings[0].top_aspects),
            'meters': all_readings
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def analyze_daily_change_distribution():
    """
    Analyze distribution of daily changes across random charts to determine trend thresholds.

    For NUM_CHARTS random birth charts, calculate meters for NUM_DAYS consecutive days
    and compute deltas for harmony, intensity, and unified_score.

    Returns quantile-based thresholds for "stable", "slow", "moderate", "rapid" changes.
    """
    NUM_CHARTS = 2500  # Reduced for faster analysis
    NUM_DAYS = 15     # 30 consecutive days per chart

    print("\n" + "="*100)
    print(f"DAILY CHANGE DISTRIBUTION ANALYSIS")
    print(f"Analyzing {NUM_CHARTS} charts × {NUM_DAYS} days = {NUM_CHARTS * NUM_DAYS} data points")
    print("="*100 + "\n")

    # Collect all deltas
    all_harmony_deltas = []
    all_intensity_deltas = []
    all_unified_deltas = []

    # Start date for transit analysis
    start_date = datetime(2025, 10, 1)

    print("Generating charts and calculating daily changes...")
    for chart_num in range(NUM_CHARTS):
        # Generate random natal chart
        natal_chart, birth_date, city = generate_random_chart()
        if natal_chart is None:
            continue

        # Calculate meters for NUM_DAYS consecutive days
        previous_meters = None
        for day_offset in range(NUM_DAYS):
            current_date = start_date + timedelta(days=day_offset)
            current_date_str = current_date.strftime("%Y-%m-%d")

            try:
                # Calculate transit chart for this day
                transit_chart, _ = compute_birth_chart(
                    birth_date=current_date_str,
                    birth_time="12:00"
                )

                # Calculate meters (without trends to avoid recursion)
                current_meters = _calculate_meters_no_trends(
                    natal_chart,
                    transit_chart,
                    current_date
                )

                # If we have previous day, calculate deltas
                if previous_meters is not None:
                    # Get all 23 individual meters (not super-groups)
                    meter_names = [
                        'overall_intensity', 'overall_harmony',
                        'mental_clarity', 'decision_quality', 'communication_flow',
                        'emotional_intensity', 'relationship_harmony', 'emotional_resilience',
                        'physical_energy', 'conflict_risk', 'motivation_drive',
                        'career_ambition', 'opportunity_window', 'challenge_intensity',
                        'transformation_pressure', 'fire_energy', 'earth_energy',
                        'air_energy', 'water_energy', 'intuition_spirituality',
                        'innovation_breakthrough', 'karmic_lessons', 'social_collective',
                    ]

                    for meter_name in meter_names:
                        curr = getattr(current_meters, meter_name)
                        prev = getattr(previous_meters, meter_name)

                        # Compute deltas
                        harmony_delta = abs(curr.harmony - prev.harmony)
                        intensity_delta = abs(curr.intensity - prev.intensity)
                        unified_delta = abs(curr.unified_score - prev.unified_score)

                        all_harmony_deltas.append(harmony_delta)
                        all_intensity_deltas.append(intensity_delta)
                        all_unified_deltas.append(unified_delta)

                previous_meters = current_meters

            except Exception as e:
                print(f"Error processing chart {chart_num}, day {day_offset}: {e}")
                continue

        # Progress indicator
        if (chart_num + 1) % (NUM_CHARTS // 10) == 0:
            print(f"  Processed {chart_num + 1}/{NUM_CHARTS} charts...")

    print(f"\nCollected {len(all_harmony_deltas)} daily transitions\n")

    # Convert to numpy arrays for quantile calculation
    harmony_deltas = np.array(all_harmony_deltas)
    intensity_deltas = np.array(all_intensity_deltas)
    unified_deltas = np.array(all_unified_deltas)

    # Calculate quantiles for each metric
    quantiles = [0.25, 0.50, 0.75, 0.90, 0.95]

    print("="*100)
    print("QUANTILE ANALYSIS (Absolute Changes)")
    print("="*100 + "\n")

    print("HARMONY deltas:")
    for q in quantiles:
        val = np.quantile(harmony_deltas, q)
        print(f"  {int(q*100):2d}th percentile: {val:5.2f}")

    print("\nINTENSITY deltas:")
    for q in quantiles:
        val = np.quantile(intensity_deltas, q)
        print(f"  {int(q*100):2d}th percentile: {val:5.2f}")

    print("\nUNIFIED SCORE deltas:")
    for q in quantiles:
        val = np.quantile(unified_deltas, q)
        print(f"  {int(q*100):2d}th percentile: {val:5.2f}")

    # Recommend thresholds based on quantiles
    print("\n" + "="*100)
    print("RECOMMENDED THRESHOLDS (based on quantiles)")
    print("="*100 + "\n")

    # Use harmony as primary metric (most meaningful for users)
    stable_threshold = np.quantile(harmony_deltas, 0.50)  # 50th percentile = median
    slow_threshold = np.quantile(harmony_deltas, 0.75)    # 75th percentile
    moderate_threshold = np.quantile(harmony_deltas, 0.90) # 90th percentile
    # rapid = above 90th percentile

    print("Based on HARMONY changes (most meaningful for quality assessment):")
    print(f"  stable   : < {stable_threshold:.1f} points  (50% of daily changes)")
    print(f"  slow     : {stable_threshold:.1f} - {slow_threshold:.1f} points  (50th-75th percentile)")
    print(f"  moderate : {slow_threshold:.1f} - {moderate_threshold:.1f} points  (75th-90th percentile)")
    print(f"  rapid    : > {moderate_threshold:.1f} points  (top 10% of changes)")

    print("\n" + "="*100)
    print("DISTRIBUTION STATISTICS")
    print("="*100 + "\n")

    for name, deltas in [("Harmony", harmony_deltas), ("Intensity", intensity_deltas), ("Unified", unified_deltas)]:
        print(f"{name}:")
        print(f"  Mean:   {np.mean(deltas):.2f}")
        print(f"  Median: {np.median(deltas):.2f}")
        print(f"  Std:    {np.std(deltas):.2f}")
        print(f"  Min:    {np.min(deltas):.2f}")
        print(f"  Max:    {np.max(deltas):.2f}")
        print()

    return {
        'stable_threshold': stable_threshold,
        'slow_threshold': slow_threshold,
        'moderate_threshold': moderate_threshold,
        'harmony_quantiles': {q: np.quantile(harmony_deltas, q) for q in quantiles},
        'intensity_quantiles': {q: np.quantile(intensity_deltas, q) for q in quantiles},
        'unified_quantiles': {q: np.quantile(unified_deltas, q) for q in quantiles},
    }


def test_many_charts():
    """Test NUM_CHARTS random charts and report statistics."""

    NUM_CHARTS = 1000
    print("\n" + "="*100)
    print(f"STRESS TEST: {NUM_CHARTS} RANDOM BIRTH CHARTS")
    print("="*100 + "\n")

    results = []
    failed_charts = 0

    print("Generating and analyzing charts...")
    for i in range(NUM_CHARTS):
        natal_chart, birth_date, city = generate_random_chart()

        if natal_chart is None:
            failed_charts += 1
            continue

        result = analyze_chart_overlaps(natal_chart)
        result['chart_num'] = i + 1
        result['birth_date'] = birth_date
        result['city'] = city
        results.append(result)

        # Progress indicator
        if (i + 1) % (NUM_CHARTS//10) == 0:
            print(f"  Processed {i + 1}/{NUM_CHARTS} charts...")

    # Analyze results
    successful_charts = [r for r in results if r['success']]
    charts_with_overlaps = [r for r in successful_charts if len(r['identical_pairs']) > 0]

    print(f"\n{'='*100}")
    print("RESULTS SUMMARY")
    print(f"{'='*100}\n")

    print(f"Total charts tested: {NUM_CHARTS}")
    print(f"Successful analyses: {len(successful_charts)}")
    print(f"Failed analyses: {failed_charts}")
    print(f"Charts with UNEXPECTED identical pairs: {len(charts_with_overlaps)}")

    if len(charts_with_overlaps) > 0:
        print(f"\n❌ FOUND {len(charts_with_overlaps)} CHARTS WITH OVERLAPS:\n")

        # Collect all unique overlap pairs
        overlap_frequency = {}

        for result in charts_with_overlaps:
            print(f"  Chart #{result['chart_num']}: {result['birth_date'].strftime('%Y-%m-%d')} in {result['city']}")
            for m1, m2 in result['identical_pairs']:
                pair_key = tuple(sorted([m1, m2]))
                overlap_frequency[pair_key] = overlap_frequency.get(pair_key, 0) + 1
                print(f"    - {m1} == {m2}")

        print(f"\n{'='*100}")
        print("OVERLAP FREQUENCY ACROSS ALL CHARTS")
        print(f"{'='*100}\n")

        for pair, count in sorted(overlap_frequency.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(successful_charts)) * 100
            print(f"  {pair[0]:30s} == {pair[1]:30s}: {count:3d} charts ({percentage:.1f}%)")

        print(f"\n❌ FAILURE: Meter overlaps still exist in some charts")
        print(f"   These meters need further refinement to ensure distinctiveness")

    else:
        print(f"\n✅ SUCCESS: No unexpected overlaps in any of the {NUM_CHARTS} charts!")
        print(f"   All meters are robustly distinct across diverse natal configurations")

    # Additional statistics
    print(f"\n{'='*100}")
    print("ADDITIONAL STATISTICS")
    print(f"{'='*100}\n")

    if successful_charts:
        aspect_counts = [r['total_aspects'] for r in successful_charts]
        print(f"Aspect counts per chart:")
        print(f"  Min: {min(aspect_counts)}")
        print(f"  Max: {max(aspect_counts)}")
        print(f"  Mean: {sum(aspect_counts)/len(aspect_counts):.1f}")
        print(f"  Median: {sorted(aspect_counts)[len(aspect_counts)//2]}")

    # Return status
    return len(charts_with_overlaps) == 0


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "trends":
        # Analyze daily change distribution for trend thresholds
        analyze_daily_change_distribution()
    else:
        # Original overlap test
        success = test_many_charts()
        exit(0 if success else 1)

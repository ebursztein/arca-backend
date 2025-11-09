"""
Overlap test for 17-meter system.

Tests 1,000 random charts to ensure no unexpected meter overlaps.

Usage:
    uv run python -m functions.astrometers.test_charts_stats_v2
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta
from astro import compute_birth_chart
from astrometers.meters import get_meters

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
    ("São Paulo, Brazil", -23.5505, -46.6333, "America/Sao_Paulo"),
    ("Mexico City, Mexico", 19.4326, -99.1332, "America/Mexico_City"),
    ("Chicago, USA", 41.8781, -87.6298, "America/Chicago"),
    ("Toronto, Canada", 43.6532, -79.3832, "America/Toronto"),
    ("Vancouver, Canada", 49.2827, -123.1207, "America/Vancouver"),
    ("Buenos Aires, Argentina", -34.6037, -58.3816, "America/Argentina/Buenos_Aires"),
    ("Rio de Janeiro, Brazil", -22.9068, -43.1729, "America/Sao_Paulo"),
    ("Moscow, Russia", 55.7558, 37.6173, "Europe/Moscow"),
    ("Madrid, Spain", 40.4168, -3.7038, "Europe/Madrid"),
    ("Beijing, China", 39.9042, 116.4074, "Asia/Shanghai"),
    ("Dubai, UAE", 25.276987, 55.296249, "Asia/Dubai"),
    ("Singapore", 1.3521, 103.8198, "Asia/Singapore"),
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


def analyze_chart_overlaps(natal_chart):
    """Analyze overlaps for a single chart across all 17 meters."""
    # Use same transit date for all tests
    transit_chart, _ = compute_birth_chart(birth_date="2025-11-03")
    date = datetime(2025, 11, 3, 12, 0)

    try:
        # Calculate all 17 meters
        all_meters = get_meters(natal_chart, transit_chart, date, calculate_trends=False)

        # Get all 17 meter readings
        meter_names = [
            'mental_clarity', 'focus', 'communication',
            'love', 'inner_stability', 'sensitivity',
            'vitality', 'drive', 'wellness',
            'purpose', 'connection', 'intuition', 'creativity',
            'opportunities', 'career', 'growth', 'social_life'
        ]

        # Build aspect sets for each meter
        aspect_sets = {}
        for meter_name in meter_names:
            reading = getattr(all_meters, meter_name)
            aspect_set = set(
                (a.natal_planet, a.transit_planet, a.aspect_type)
                for a in reading.top_aspects
            )
            aspect_sets[meter_name] = aspect_set

        # Find identical pairs
        identical_pairs = []
        for i, meter1 in enumerate(meter_names):
            for meter2 in meter_names[i+1:]:
                set1 = aspect_sets[meter1]
                set2 = aspect_sets[meter2]

                # Only flag if both have aspects AND they're identical
                if set1 and set2 and set1 == set2:
                    identical_pairs.append((meter1, meter2))

        # Get total aspects
        all_readings = [getattr(all_meters, m) for m in meter_names]
        total_aspects = sum(len(r.top_aspects) for r in all_readings)

        return {
            'success': True,
            'identical_pairs': identical_pairs,
            'total_aspects': total_aspects,
            'meters': all_readings
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def test_many_charts(num_charts=1000):
    """Test NUM_CHARTS random charts and report statistics."""
    print("\n" + "="*100)
    print(f"OVERLAP TEST: {num_charts} RANDOM BIRTH CHARTS (17-Meter System)")
    print("="*100 + "\n")

    results = []
    failed_charts = 0

    print("Generating and analyzing charts...")
    for i in range(num_charts):
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
        if (i + 1) % (num_charts//10) == 0:
            print(f"  Processed {i + 1}/{num_charts} charts...")

    # Analyze results
    successful_charts = [r for r in results if r['success']]
    charts_with_overlaps = [r for r in successful_charts if len(r['identical_pairs']) > 0]

    print(f"\n{'='*100}")
    print("RESULTS SUMMARY")
    print(f"{'='*100}\n")

    print(f"Total charts tested: {num_charts}")
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
        print(f"\n✅ SUCCESS: No unexpected overlaps in any of the {num_charts} charts!")
        print(f"   All 17 meters are robustly distinct across diverse natal configurations")

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

    # Default to 1000 charts
    num_charts = 1000
    if len(sys.argv) > 1:
        try:
            num_charts = int(sys.argv[1])
        except ValueError:
            print(f"Usage: {sys.argv[0]} [num_charts]")
            print(f"  num_charts: Number of charts to test (default: 1000)")
            sys.exit(1)

    success = test_many_charts(num_charts)
    sys.exit(0 if success else 1)

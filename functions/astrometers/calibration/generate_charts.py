"""
Generate sample natal charts for empirical calibration.

This script creates a diverse set of birth charts spanning:
- Birth years: 1950-2020 (70 years)
- Global locations (major cities across all continents)
- Random birth times

Usage:
    cd /Users/elie/git/arca/arca-backend
    uv run python -m functions.astrometers.calibration.generate_charts --count 1000
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
import argparse
from astro import compute_birth_chart


# Global cities with diverse locations
SAMPLE_LOCATIONS = [
    # North America
    {"city": "New York", "lat": 40.7128, "lon": -74.0060},
    {"city": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"city": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"city": "Toronto", "lat": 43.6532, "lon": -79.3832},
    {"city": "Mexico City", "lat": 19.4326, "lon": -99.1332},

    # South America
    {"city": "São Paulo", "lat": -23.5505, "lon": -46.6333},
    {"city": "Buenos Aires", "lat": -34.6037, "lon": -58.3816},
    {"city": "Lima", "lat": -12.0464, "lon": -77.0428},

    # Europe
    {"city": "London", "lat": 51.5074, "lon": -0.1278},
    {"city": "Paris", "lat": 48.8566, "lon": 2.3522},
    {"city": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"city": "Rome", "lat": 41.9028, "lon": 12.4964},
    {"city": "Madrid", "lat": 40.4168, "lon": -3.7038},
    {"city": "Moscow", "lat": 55.7558, "lon": 37.6173},

    # Asia
    {"city": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"city": "Beijing", "lat": 39.9042, "lon": 116.4074},
    {"city": "Shanghai", "lat": 31.2304, "lon": 121.4737},
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"city": "Delhi", "lat": 28.7041, "lon": 77.1025},
    {"city": "Seoul", "lat": 37.5665, "lon": 126.9780},
    {"city": "Singapore", "lat": 1.3521, "lon": 103.8198},

    # Africa
    {"city": "Cairo", "lat": 30.0444, "lon": 31.2357},
    {"city": "Lagos", "lat": 6.5244, "lon": 3.3792},
    {"city": "Johannesburg", "lat": -26.2041, "lon": 28.0473},

    # Oceania
    {"city": "Sydney", "lat": -33.8688, "lon": 151.2093},
    {"city": "Melbourne", "lat": -37.8136, "lon": 144.9631},
    {"city": "Auckland", "lat": -36.8485, "lon": 174.7633},
]


def generate_random_birth_date(start_year: int = 1950, end_year: int = 2020) -> str:
    """Generate random birth date between start_year and end_year."""
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)

    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    birth_date = start_date + timedelta(days=random_days)

    return birth_date.strftime("%Y-%m-%d")


def generate_random_birth_time() -> str:
    """Generate random birth time (HH:MM)."""
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}"


def generate_sample_charts(count: int, output_file: str = "natal_charts.json") -> None:
    """
    Generate sample natal charts with diverse birth data.

    Args:
        count: Number of charts to generate
        output_file: Output JSON file path
    """
    print(f"Generating {count} sample natal charts...")
    print(f"Birth years: 1950-2020")
    print(f"Locations: {len(SAMPLE_LOCATIONS)} global cities")
    print()

    charts = []

    for i in range(count):
        # Random birth date
        birth_date = generate_random_birth_date()

        # Random birth time
        birth_time = generate_random_birth_time()

        # Random location
        location = random.choice(SAMPLE_LOCATIONS)

        # Calculate natal chart
        try:
            natal_chart, is_exact = compute_birth_chart(
                birth_date=birth_date,
                birth_time=birth_time,
                birth_lat=float(location["lat"]),
                birth_lon=float(location["lon"])
            )

            # Store metadata
            chart_data = {
                "chart_id": f"chart_{i+1:05d}",
                "birth_date": birth_date,
                "birth_time": birth_time,
                "location": location["city"],
                "lat": location["lat"],
                "lon": location["lon"],
                "sun_sign": natal_chart.get("sun_sign"),
                "ascendant_sign": natal_chart.get("ascendant_sign"),
                "natal_chart": natal_chart
            }

            charts.append(chart_data)

            # Progress indicator
            if (i + 1) % 100 == 0:
                print(f"Generated {i + 1}/{count} charts...")

        except Exception as e:
            print(f"Error generating chart {i+1}: {e}")
            continue

    # Save to JSON
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    with open(output_path, 'w') as f:
        json.dump(charts, f, indent=2)

    print()
    print(f"Successfully generated {len(charts)} charts")
    print(f"Saved to: {output_path}")
    print()

    # Statistics
    sun_signs: dict[str, int] = {}
    for chart in charts:
        sign = chart["sun_sign"]
        sun_signs[sign] = sun_signs.get(sign, 0) + 1

    print("Sun sign distribution:")
    for sign, count in sorted(sun_signs.items()):
        print(f"  {sign}: {count}")


def main():
    parser = argparse.ArgumentParser(description="Generate sample natal charts for calibration")
    parser.add_argument("--count", type=int, default=1000, help="Number of charts to generate (default: 1000)")
    parser.add_argument("--output", type=str, default="natal_charts.json", help="Output JSON file name")

    args = parser.parse_args()

    generate_sample_charts(count=args.count, output_file=args.output)


if __name__ == "__main__":
    main()

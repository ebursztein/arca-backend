"""
Test the daily_meters_summary() function with real chart data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from astro import compute_birth_chart
from astrometers.meters import get_meters
from astrometers.summary import daily_meters_summary


def test_daily_summary():
    """Generate and display daily meter summary table."""

    # Generate test natal chart
    print("Generating natal chart...")
    natal_chart, _ = compute_birth_chart(
        birth_date="1990-06-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )

    # Generate transit charts for today and yesterday
    today = datetime(2025, 10, 28, 12, 0)
    yesterday = today - timedelta(days=1)

    print(f"Calculating meters for {yesterday.date()} (yesterday)...")
    transit_yesterday, _ = compute_birth_chart(birth_date=yesterday.strftime("%Y-%m-%d"))
    meters_yesterday = get_meters(natal_chart, transit_yesterday, yesterday)

    print(f"Calculating meters for {today.date()} (today)...")
    transit_today, _ = compute_birth_chart(birth_date=today.strftime("%Y-%m-%d"))
    meters_today = get_meters(natal_chart, transit_today, today)

    # Generate summary table
    print("\n" + "="*80)
    print("DAILY METER SUMMARY - MARKDOWN TABLE OUTPUT")
    print("="*80 + "\n")

    summary = daily_meters_summary(meters_today, meters_yesterday)
    print(summary)

    # Show token estimate
    token_estimate = len(summary.split())
    print(f"\n{'='*80}")
    print(f"SUMMARY STATISTICS")
    print(f"{'='*80}")
    print(f"Total characters: {len(summary)}")
    print(f"Estimated tokens: ~{token_estimate} tokens")
    print(f"Lines: {len(summary.splitlines())}")
    print(f"\nCompare to full meter dump: ~3000+ tokens")
    print(f"Token reduction: ~{((3000 - token_estimate) / 3000 * 100):.0f}%")


if __name__ == "__main__":
    test_daily_summary()

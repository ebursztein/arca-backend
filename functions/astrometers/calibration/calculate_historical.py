"""
Calculate historical DTI/HQS scores for empirical calibration.

For each natal chart, calculates DTI and HQS for every day in the date range.
Uses multiprocessing to parallelize calculations.

Usage:
    cd /Users/elie/git/arca/arca-backend
    uv run python -m functions.astrometers.calibration.calculate_historical
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

from astro import compute_birth_chart, find_natal_transit_aspects
from astrometers.meters import convert_to_transit_aspects
from astrometers.core import calculate_astrometers


def calculate_scores_for_date(args):
    """
    Calculate DTI/HQS for a single natal chart on a single date.

    Args:
        args: Tuple of (chart_data, date_str)

    Returns:
        Dict with scores
    """
    chart_data, date_str = args

    try:
        natal_chart = chart_data["natal_chart"]

        # Get transit chart for this date
        transit_chart, _ = compute_birth_chart(date_str, birth_time="12:00")

        # Find aspects
        nt_aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=8.0)

        if not nt_aspects:
            return {
                "chart_id": chart_data["chart_id"],
                "date": date_str,
                "dti": 0.0,
                "hqs": 0.0,
                "aspect_count": 0
            }

        # Convert to TransitAspect format
        transit_aspects = convert_to_transit_aspects(natal_chart, transit_chart, nt_aspects)

        # Calculate scores
        score = calculate_astrometers(transit_aspects)

        return {
            "chart_id": chart_data["chart_id"],
            "date": date_str,
            "dti": score.dti,
            "hqs": score.hqs,
            "aspect_count": score.aspect_count
        }

    except Exception as e:
        print(f"Error calculating scores for {chart_data['chart_id']} on {date_str}: {e}")
        return {
            "chart_id": chart_data["chart_id"],
            "date": date_str,
            "dti": 0.0,
            "hqs": 0.0,
            "aspect_count": 0,
            "error": str(e)
        }


def generate_date_range(start_year: int = 2000, end_year: int = 2025) -> List[str]:
    """Generate list of dates from start_year to end_year."""
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)

    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return dates


def calculate_historical_scores(
    charts_file: str = "natal_charts.json",
    output_file: str = "historical_scores.parquet",
    start_year: int = 2000,
    end_year: int = 2025,
    sample_charts: int = None
) -> None:
    """
    Calculate historical scores for all charts across date range.

    Args:
        charts_file: Input JSON file with natal charts
        output_file: Output parquet file
        start_year: Start year for calculations
        end_year: End year for calculations
        sample_charts: Limit to N charts for testing (None = all)
    """
    # Load charts
    charts_path = os.path.join(os.path.dirname(__file__), charts_file)
    print(f"Loading charts from {charts_path}...")
    with open(charts_path, 'r') as f:
        charts = json.load(f)

    if sample_charts:
        charts = charts[:sample_charts]
        print(f"Using first {len(charts)} charts for testing")

    # Generate date range
    print(f"Generating date range {start_year}-{end_year}...")
    dates = generate_date_range(start_year, end_year)
    print(f"Date range: {len(dates)} days")

    # Calculate total workload
    total_calculations = len(charts) * len(dates)
    print(f"Total calculations: {total_calculations:,}")
    print(f"Estimated time: {total_calculations / 1000:.1f} minutes (at ~1000 calcs/min)")
    print()

    # Prepare arguments for parallel processing
    print("Preparing calculation tasks...")
    args_list = []
    for chart in charts:
        for date in dates:
            args_list.append((chart, date))

    # Run calculations in parallel
    num_cores = cpu_count()
    print(f"Using {num_cores} CPU cores for parallel processing...")
    print("Starting calculations...")
    print()

    results = []
    with Pool(processes=num_cores) as pool:
        # Use tqdm for progress bar
        for result in tqdm(pool.imap_unordered(calculate_scores_for_date, args_list),
                          total=len(args_list),
                          desc="Calculating scores"):
            results.append(result)

    # Convert to DataFrame
    print()
    print("Converting results to DataFrame...")
    df = pd.DataFrame(results)

    # Save to parquet (compressed)
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    print(f"Saving to {output_path}...")
    df.to_parquet(output_path, compression='gzip', index=False)

    # Statistics
    print()
    print("=" * 60)
    print("CALCULATION COMPLETE")
    print("=" * 60)
    print(f"Total calculations: {len(results):,}")
    print(f"Output file: {output_path}")
    print(f"File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    print()

    # Data statistics
    print("Score Statistics:")
    print(f"  DTI range: {df['dti'].min():.2f} to {df['dti'].max():.2f}")
    print(f"  DTI mean: {df['dti'].mean():.2f}")
    print(f"  DTI median: {df['dti'].median():.2f}")
    print()
    print(f"  HQS range: {df['hqs'].min():.2f} to {df['hqs'].max():.2f}")
    print(f"  HQS mean: {df['hqs'].mean():.2f}")
    print(f"  HQS median: {df['hqs'].median():.2f}")
    print()
    print(f"  Average aspects per day: {df['aspect_count'].mean():.1f}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Calculate historical DTI/HQS scores")
    parser.add_argument("--charts", type=str, default="natal_charts.json", help="Input charts file")
    parser.add_argument("--output", type=str, default="historical_scores.parquet", help="Output file")
    parser.add_argument("--start-year", type=int, default=2000, help="Start year (default: 2000)")
    parser.add_argument("--end-year", type=int, default=2025, help="End year (default: 2025)")
    parser.add_argument("--sample", type=int, default=None, help="Sample N charts for testing")

    args = parser.parse_args()

    calculate_historical_scores(
        charts_file=args.charts,
        output_file=args.output,
        start_year=args.start_year,
        end_year=args.end_year,
        sample_charts=args.sample
    )


if __name__ == "__main__":
    main()

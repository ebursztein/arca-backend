"""
Calculate historical DTI/HQS scores for 17-meter system calibration.

Generates empirical calibration constants by calculating scores across
2,500 diverse charts over 25 years of daily transits.

Usage:
    cd /Users/elieb/git/arca-backend
    uv run python -m functions.astrometers.calibration.calculate_historical_v2
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

from astro import compute_birth_chart
from astrometers.core import calculate_all_aspects, calculate_astrometers
from astrometers.meters import METER_CONFIGS, filter_aspects


def calculate_scores_for_date(args):
    """
    Calculate DTI/HQS for all 17 meters for one chart on one date.

    Args:
        args: Tuple of (chart_data, date_str)

    Returns:
        List of dicts with scores for each meter
    """
    chart_data, date_str = args

    try:
        # Get natal chart
        natal_chart = chart_data["natal_chart"]

        # Get transit chart for this date
        transit_chart, _ = compute_birth_chart(date_str, "12:00")

        # Calculate all aspects
        all_aspects = calculate_all_aspects(natal_chart, transit_chart)

        # Calculate scores for each meter
        results = []
        for meter_name, config in METER_CONFIGS.items():
            # Filter aspects for this meter
            filtered = filter_aspects(all_aspects, config, natal_chart)

            # Calculate DTI/HQS and V2 scores
            if filtered:
                score = calculate_astrometers(filtered)
                dti = score.dti
                hqs = score.hqs
                # V2 decoupled scores
                intensity_v2 = score.intensity
                harmony_coef = score.harmony_coefficient
            else:
                dti = 0.0
                hqs = 0.0
                intensity_v2 = 0.0
                harmony_coef = 0.0

            results.append({
                "chart_id": chart_data["chart_id"],
                "date": date_str,
                "meter": meter_name,
                "dti": dti,
                "hqs": hqs,
                # V2 fields
                "intensity_v2": intensity_v2,
                "harmony_coefficient": harmony_coef,
            })

        return results

    except Exception as e:
        print(f"Error processing {chart_data['chart_id']} on {date_str}: {e}")
        return []


def load_natal_charts(charts_file: str) -> List[Dict]:
    """Load natal charts from JSON."""
    with open(charts_file, 'r') as f:
        charts = json.load(f)

    print(f"Loaded {len(charts)} natal charts")
    return charts


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """Generate list of dates in YYYY-MM-DD format."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    return dates


def calculate_historical_scores(
    charts_file: str,
    start_date: str,
    end_date: str,
    output_file: str,
    sample_size: int = None
):
    """
    Calculate historical scores for all meters.

    Args:
        charts_file: Path to natal_charts.json
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        output_file: Path to save results (CSV)
        sample_size: Optional limit on number of charts
    """
    print(f"="*60)
    print("Historical Score Calculation - 17 Meter System")
    print(f"="*60)

    # Load charts
    charts = load_natal_charts(charts_file)
    if sample_size:
        charts = charts[:sample_size]
        print(f"Using sample of {sample_size} charts")

    # Generate date range
    dates = generate_date_range(start_date, end_date)
    print(f"Date range: {start_date} to {end_date} ({len(dates)} days)")

    # Create all (chart, date) pairs
    tasks = []
    for chart in charts:
        for date in dates:
            tasks.append((chart, date))

    print(f"Total calculations: {len(tasks):,} (charts × days × 17 meters)")
    print(f"Using {cpu_count()} CPU cores")
    print()

    # Process in parallel
    results = []
    with Pool(cpu_count()) as pool:
        for result in tqdm(
            pool.imap_unordered(calculate_scores_for_date, tasks),
            total=len(tasks),
            desc="Processing"
        ):
            results.extend(result)

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"\n✓ Saved {len(df):,} scores to {output_file}")

    # Print summary stats
    print("\nSummary by Meter:")
    print("-" * 60)
    for meter in sorted(METER_CONFIGS.keys()):
        meter_data = df[df['meter'] == meter]
        dti_stats = meter_data['dti'].describe()
        hqs_stats = meter_data['hqs'].describe()

        print(f"{meter}:")
        print(f"  DTI: mean={dti_stats['mean']:.1f}, p50={dti_stats['50%']:.1f}, p99={meter_data['dti'].quantile(0.99):.1f}")
        print(f"  HQS: mean={hqs_stats['mean']:.1f}, p50={hqs_stats['50%']:.1f}, p99={meter_data['hqs'].quantile(0.99):.1f}")


def generate_calibration_constants(scores_csv: str, output_json: str):
    """
    Generate calibration constants from historical scores.

    Args:
        scores_csv: Path to CSV with historical scores
        output_json: Path to save calibration_constants.json
    """
    print(f"\n{'='*60}")
    print("Generating Calibration Constants")
    print(f"{'='*60}\n")

    # Load scores
    df = pd.read_csv(scores_csv)

    # Calculate percentiles for each meter
    meters = {}
    for meter_name in sorted(METER_CONFIGS.keys()):
        meter_data = df[df['meter'] == meter_name]

        # Calculate all 99 percentiles (p01 through p99) for perfect interpolation
        dti_percentiles = {
            f"p{pct:02d}": meter_data['dti'].quantile(pct / 100.0)
            for pct in range(1, 100)
        }

        hqs_percentiles = {
            f"p{pct:02d}": meter_data['hqs'].quantile(pct / 100.0)
            for pct in range(1, 100)
        }

        # V2: intensity percentiles (Gaussian power sum)
        intensity_v2_percentiles = {}
        if 'intensity_v2' in meter_data.columns:
            intensity_v2_percentiles = {
                f"p{pct:02d}": meter_data['intensity_v2'].quantile(pct / 100.0)
                for pct in range(1, 100)
            }

        meters[meter_name] = {
            "dti_percentiles": dti_percentiles,
            "hqs_percentiles": hqs_percentiles,
            "intensity_v2_percentiles": intensity_v2_percentiles,
        }

        print(f"{meter_name}:")
        print(f"  DTI p25={dti_percentiles['p25']:.2f}, p75={dti_percentiles['p75']:.2f}, p99={dti_percentiles['p99']:.2f}")
        if intensity_v2_percentiles:
            print(f"  V2I p25={intensity_v2_percentiles['p25']:.2f}, p75={intensity_v2_percentiles['p75']:.2f}, p99={intensity_v2_percentiles['p99']:.2f}")
        print(f"  HQS p01={hqs_percentiles['p01']:.2f}, p25={hqs_percentiles['p25']:.2f}, p75={hqs_percentiles['p75']:.2f}, p99={hqs_percentiles['p99']:.2f}")

    # Build calibration constants
    calibration = {
        "version": "4.0",
        "generated": datetime.now().isoformat(),
        "description": "Empirical calibration for 17-meter system",
        "sample_size": len(df['chart_id'].unique()),
        "days_per_chart": len(df['date'].unique()),
        "total_data_points": len(df),
        "meters": meters
    }

    # Save to JSON
    with open(output_json, 'w') as f:
        json.dump(calibration, f, indent=2)

    print(f"\n✓ Saved calibration constants to {output_json}")


if __name__ == "__main__":
    # Configuration
    CHARTS_FILE = "functions/astrometers/calibration/natal_charts.json"
    START_DATE = "2020-01-01"
    END_DATE = "2024-12-31"  # 5 years
    SCORES_CSV = "functions/astrometers/calibration/historical_scores_v2.csv"
    CONSTANTS_JSON = "functions/astrometers/calibration/calibration_constants.json"

    # Use 2000 charts over 5 years
    SAMPLE_SIZE = 2000

    print("Starting calibration process...")
    print(f"Sample size: {SAMPLE_SIZE if SAMPLE_SIZE else 'ALL'} charts")
    print()

    # Step 1: Calculate historical scores
    calculate_historical_scores(
        CHARTS_FILE,
        START_DATE,
        END_DATE,
        SCORES_CSV,
        sample_size=SAMPLE_SIZE
    )

    # Step 2: Generate calibration constants
    generate_calibration_constants(SCORES_CSV, CONSTANTS_JSON)

    print("\n" + "="*60)
    print("✓ Calibration complete!")
    print("="*60)

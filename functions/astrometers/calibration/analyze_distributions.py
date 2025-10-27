"""
Analyze historical score distributions and calculate empirical percentiles.

Generates calibration constants for normalization based on real-world data.
Now supports per-meter calibration for all 23 meters.

Usage:
    cd /Users/elie/git/arca/arca-backend
    uv run python -m functions.astrometers.calibration.analyze_distributions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import pandas as pd
import numpy as np
from datetime import datetime


def analyze_distributions(
    input_file: str = "historical_scores.parquet",
    output_file: str = "calibration_constants.json"
) -> None:
    """
    Analyze score distributions and generate per-meter calibration constants.

    Args:
        input_file: Input parquet file with historical scores (includes meter_name column)
        output_file: Output JSON file with calibration constants
    """
    # Load data
    input_path = os.path.join(os.path.dirname(__file__), input_file)
    print(f"Loading scores from {input_path}...")
    df = pd.read_parquet(input_path)

    print(f"Loaded {len(df):,} score records")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Unique charts: {df['chart_id'].nunique()}")

    # Check if we have meter_name column
    if 'meter_name' in df.columns:
        print(f"Meters: {df['meter_name'].nunique()}")
        print(f"Records per meter: {len(df) // df['meter_name'].nunique():,}")
    else:
        print("WARNING: No meter_name column found - generating global calibration only")

    print()

    # Calculate per-meter percentiles
    print("Calculating per-meter percentiles...")
    print("-" * 80)

    meter_calibrations = {}

    for meter_name in sorted(df['meter_name'].unique()):
        meter_df = df[df['meter_name'] == meter_name]

        # DTI percentiles
        dti_percentiles = {
            "p01": float(np.percentile(meter_df['dti'], 1)),
            "p05": float(np.percentile(meter_df['dti'], 5)),
            "p10": float(np.percentile(meter_df['dti'], 10)),
            "p25": float(np.percentile(meter_df['dti'], 25)),
            "p50": float(np.percentile(meter_df['dti'], 50)),
            "p75": float(np.percentile(meter_df['dti'], 75)),
            "p90": float(np.percentile(meter_df['dti'], 90)),
            "p95": float(np.percentile(meter_df['dti'], 95)),
            "p99": float(np.percentile(meter_df['dti'], 99)),
        }

        # HQS percentiles
        hqs_percentiles = {
            "p01": float(np.percentile(meter_df['hqs'], 1)),
            "p05": float(np.percentile(meter_df['hqs'], 5)),
            "p10": float(np.percentile(meter_df['hqs'], 10)),
            "p25": float(np.percentile(meter_df['hqs'], 25)),
            "p50": float(np.percentile(meter_df['hqs'], 50)),
            "p75": float(np.percentile(meter_df['hqs'], 75)),
            "p90": float(np.percentile(meter_df['hqs'], 90)),
            "p95": float(np.percentile(meter_df['hqs'], 95)),
            "p99": float(np.percentile(meter_df['hqs'], 99)),
        }

        meter_calibrations[meter_name] = {
            "dti_percentiles": dti_percentiles,
            "hqs_percentiles": hqs_percentiles,
            "stats": {
                "dti": {
                    "min": float(meter_df['dti'].min()),
                    "max": float(meter_df['dti'].max()),
                    "mean": float(meter_df['dti'].mean()),
                    "std": float(meter_df['dti'].std())
                },
                "hqs": {
                    "min": float(meter_df['hqs'].min()),
                    "max": float(meter_df['hqs'].max()),
                    "mean": float(meter_df['hqs'].mean()),
                    "std": float(meter_df['hqs'].std())
                },
                "avg_aspects": float(meter_df['aspect_count'].mean())
            }
        }

        # Print summary
        print(f"{meter_name:30s} | P99: {dti_percentiles['p99']:7.1f} | P50: {dti_percentiles['p50']:7.1f} | Avg aspects: {meter_df['aspect_count'].mean():.1f}")

    print()

    # Create calibration constants
    calibration_constants = {
        "version": "3.0",
        "generated_date": datetime.now().isoformat(),
        "dataset_size": len(df),
        "unique_charts": int(df['chart_id'].nunique()),
        "date_range": {
            "start": str(df['date'].min()),
            "end": str(df['date'].max())
        },
        "meters": meter_calibrations
    }

    # Save to JSON
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    with open(output_path, 'w') as f:
        json.dump(calibration_constants, f, indent=2)

    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Calibration constants saved to: {output_path}")
    print()
    print("Per-meter P99 DTI thresholds:")
    for meter_name in sorted(meter_calibrations.keys()):
        p99 = meter_calibrations[meter_name]["dti_percentiles"]["p99"]
        print(f"  {meter_name:30s}: {p99:7.1f}")
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze distributions and generate calibration constants")
    parser.add_argument("--input", type=str, default="historical_scores.parquet", help="Input parquet file")
    parser.add_argument("--output", type=str, default="calibration_constants.json", help="Output JSON file")

    args = parser.parse_args()

    analyze_distributions(input_file=args.input, output_file=args.output)


if __name__ == "__main__":
    main()

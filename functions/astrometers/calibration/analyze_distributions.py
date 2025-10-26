"""
Analyze historical score distributions and calculate empirical percentiles.

Generates calibration constants for normalization based on real-world data.

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
    Analyze score distributions and generate calibration constants.

    Args:
        input_file: Input parquet file with historical scores
        output_file: Output JSON file with calibration constants
    """
    # Load data
    input_path = os.path.join(os.path.dirname(__file__), input_file)
    print(f"Loading scores from {input_path}...")
    df = pd.read_parquet(input_path)

    print(f"Loaded {len(df):,} score records")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Unique charts: {df['chart_id'].nunique()}")
    print()

    # Calculate percentiles for DTI
    print("Calculating DTI percentiles...")
    dti_percentiles = {
        "p01": float(np.percentile(df['dti'], 1)),
        "p05": float(np.percentile(df['dti'], 5)),
        "p10": float(np.percentile(df['dti'], 10)),
        "p25": float(np.percentile(df['dti'], 25)),
        "p50": float(np.percentile(df['dti'], 50)),
        "p75": float(np.percentile(df['dti'], 75)),
        "p90": float(np.percentile(df['dti'], 90)),
        "p95": float(np.percentile(df['dti'], 95)),
        "p99": float(np.percentile(df['dti'], 99)),
    }

    print("  DTI Percentiles:")
    for p, value in dti_percentiles.items():
        print(f"    {p.upper()}: {value:.2f}")
    print()

    # Calculate percentiles for HQS
    print("Calculating HQS percentiles...")
    hqs_percentiles = {
        "p01": float(np.percentile(df['hqs'], 1)),
        "p05": float(np.percentile(df['hqs'], 5)),
        "p10": float(np.percentile(df['hqs'], 10)),
        "p25": float(np.percentile(df['hqs'], 25)),
        "p50": float(np.percentile(df['hqs'], 50)),
        "p75": float(np.percentile(df['hqs'], 75)),
        "p90": float(np.percentile(df['hqs'], 90)),
        "p95": float(np.percentile(df['hqs'], 95)),
        "p99": float(np.percentile(df['hqs'], 99)),
    }

    print("  HQS Percentiles:")
    for p, value in hqs_percentiles.items():
        print(f"    {p.upper()}: {value:.2f}")
    print()

    # Calculate descriptive statistics
    print("Descriptive Statistics:")
    print(f"  DTI:")
    print(f"    Min: {df['dti'].min():.2f}")
    print(f"    Max: {df['dti'].max():.2f}")
    print(f"    Mean: {df['dti'].mean():.2f}")
    print(f"    Std Dev: {df['dti'].std():.2f}")
    print()
    print(f"  HQS:")
    print(f"    Min: {df['hqs'].min():.2f}")
    print(f"    Max: {df['hqs'].max():.2f}")
    print(f"    Mean: {df['hqs'].mean():.2f}")
    print(f"    Std Dev: {df['hqs'].std():.2f}")
    print()

    # Check distribution characteristics
    print("Distribution Analysis:")
    print(f"  DTI above P99: {(df['dti'] > dti_percentiles['p99']).sum():,} ({(df['dti'] > dti_percentiles['p99']).mean()*100:.2f}%)")
    print(f"  DTI above P95: {(df['dti'] > dti_percentiles['p95']).sum():,} ({(df['dti'] > dti_percentiles['p95']).mean()*100:.2f}%)")
    print(f"  DTI above P90: {(df['dti'] > dti_percentiles['p90']).sum():,} ({(df['dti'] > dti_percentiles['p90']).mean()*100:.2f}%)")
    print()
    print(f"  HQS neutral (45-55): {((df['hqs'] >= -50) & (df['hqs'] <= 50)).sum():,} ({((df['hqs'] >= -50) & (df['hqs'] <= 50)).mean()*100:.2f}%)")
    print(f"  HQS positive (>0): {(df['hqs'] > 0).sum():,} ({(df['hqs'] > 0).mean()*100:.2f}%)")
    print(f"  HQS negative (<0): {(df['hqs'] < 0).sum():,} ({(df['hqs'] < 0).mean()*100:.2f}%)")
    print()

    # Create calibration constants
    calibration_constants = {
        "version": "2.0",
        "generated_date": datetime.now().isoformat(),
        "dataset_size": len(df),
        "unique_charts": int(df['chart_id'].nunique()),
        "date_range": {
            "start": str(df['date'].min()),
            "end": str(df['date'].max())
        },
        "dti_percentiles": dti_percentiles,
        "hqs_percentiles": hqs_percentiles,
        "descriptive_stats": {
            "dti": {
                "min": float(df['dti'].min()),
                "max": float(df['dti'].max()),
                "mean": float(df['dti'].mean()),
                "std": float(df['dti'].std())
            },
            "hqs": {
                "min": float(df['hqs'].min()),
                "max": float(df['hqs'].max()),
                "mean": float(df['hqs'].mean()),
                "std": float(df['hqs'].std())
            }
        }
    }

    # Save to JSON
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    with open(output_path, 'w') as f:
        json.dump(calibration_constants, f, indent=2)

    print("=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Calibration constants saved to: {output_path}")
    print()
    print("Key Findings:")
    print(f"  - P99 DTI threshold: {dti_percentiles['p99']:.2f} (top 1%)")
    print(f"  - P95 DTI threshold: {dti_percentiles['p95']:.2f} (top 5%)")
    print(f"  - P90 DTI threshold: {dti_percentiles['p90']:.2f} (top 10%)")
    print(f"  - HQS neutral zone: {hqs_percentiles['p25']:.2f} to {hqs_percentiles['p75']:.2f}")
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

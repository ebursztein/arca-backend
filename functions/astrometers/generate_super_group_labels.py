#!/usr/bin/env python3
"""
Generate JSON label files for the 5 super-group meters only.

Usage:
    python generate_super_group_labels.py
"""

import os
from hierarchy import Meter, is_super_group_meter, SUPER_GROUP_METERS
from generate_meter_labels import (
    generate_labels_with_gemini,
    generate_meter_file
)
from google import genai
from dotenv import load_dotenv
import json

load_dotenv()

def main():
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        return

    print("🤖 Initializing Gemini client...")
    client = genai.Client(api_key=api_key)

    print(f"Generating 5 super-group meter labels...\n")

    output_dir = "labels"
    os.makedirs(output_dir, exist_ok=True)

    successful = 0
    failed = []

    # Generate only super-group meters
    super_group_meters = [m for m in Meter if is_super_group_meter(m)]

    for i, meter in enumerate(super_group_meters, 1):
        try:
            print(f"[{i}/5] Generating {meter.value}...", end=" ", flush=True)

            # Call Gemini
            labels = generate_labels_with_gemini(meter, client)

            # Build file structure
            meter_config = generate_meter_file(meter, labels)

            # Save to file
            filename = f"{meter.value}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                json.dump(meter_config, f, indent=2)

            print(f"✅")
            successful += 1

        except Exception as e:
            print(f"❌ Failed: {e}")
            failed.append((meter.value, str(e)))

    # Summary
    print(f"\n📊 Summary:")
    print(f"   Successful: {successful}/5")
    print(f"   Failed: {len(failed)}/5")

    if failed:
        print(f"\n❌ Failed meters:")
        for meter_name, error in failed:
            print(f"   • {meter_name}: {error}")

    if successful > 0:
        print(f"\n✨ Super-group label files generated!")
        print(f"📁 Check {output_dir}/ to review")

if __name__ == "__main__":
    main()

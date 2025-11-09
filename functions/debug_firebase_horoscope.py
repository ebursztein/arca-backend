#!/usr/bin/env python3
"""
Debug script to call the actual get_daily_horoscope Cloud Function endpoint.
Analyzes response for empty fields in meters/astrometers data.

Usage:
    uv run python functions/debug_firebase_horoscope.py
"""

import json
import sys
import requests
from typing import Any, Dict, List
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

console = Console()

# Production Cloud Function endpoint
FUNCTION_URL = "https://us-central1-arca-live-app.cloudfunctions.net/get_daily_horoscope"

# Test parameters
TEST_USER_ID = "integration_test_user"
TEST_DATE = "2025-11-08"


def analyze_value(value: Any, path: str) -> List[Dict[str, str]]:
    """Recursively analyze a value for empty/missing fields."""
    issues = []

    if value is None:
        issues.append({
            "path": path,
            "issue": "NULL value",
            "value": "None"
        })
    elif isinstance(value, str) and value.strip() == "":
        issues.append({
            "path": path,
            "issue": "Empty string",
            "value": '""'
        })
    elif isinstance(value, dict):
        if len(value) == 0:
            issues.append({
                "path": path,
                "issue": "Empty dict",
                "value": "{}"
            })
        else:
            for key, val in value.items():
                issues.extend(analyze_value(val, f"{path}.{key}"))
    elif isinstance(value, list):
        if len(value) == 0:
            issues.append({
                "path": path,
                "issue": "Empty list",
                "value": "[]"
            })
        else:
            for idx, item in enumerate(value):
                issues.extend(analyze_value(item, f"{path}[{idx}]"))

    return issues


def build_structure_tree(data: Any, name: str = "root") -> Tree:
    """Build a rich Tree representation of the data structure."""
    if isinstance(data, dict):
        tree = Tree(f"[bold blue]{name}[/bold blue] (dict, {len(data)} keys)")
        for key, value in data.items():
            tree.add(build_structure_tree(value, key))
        return tree
    elif isinstance(data, list):
        tree = Tree(f"[bold green]{name}[/bold green] (list, {len(data)} items)")
        if len(data) > 0:
            tree.add(build_structure_tree(data[0], f"[0] (sample)"))
            if len(data) > 1:
                tree.add(f"[dim]... and {len(data) - 1} more items[/dim]")
        return tree
    elif isinstance(data, str):
        preview = data[:50] + "..." if len(data) > 50 else data
        return Tree(f"[yellow]{name}[/yellow] (str): {preview}")
    elif isinstance(data, (int, float)):
        return Tree(f"[cyan]{name}[/cyan] ({type(data).__name__}): {data}")
    elif data is None:
        return Tree(f"[red]{name}[/red] (None)")
    else:
        return Tree(f"[magenta]{name}[/magenta] ({type(data).__name__}): {data}")


def analyze_meters_data(response: Dict[str, Any]) -> None:
    """Specifically analyze the meters/astrometers data structure."""
    console.print("\n[bold cyan]═══ METERS DATA ANALYSIS ═══[/bold cyan]\n")

    if "astrometers" not in response:
        console.print("[red]❌ No 'astrometers' field found in response![/red]")
        return

    astrometers = response["astrometers"]

    console.print("[bold]Astrometers Structure:[/bold]")
    tree = build_structure_tree(astrometers, "astrometers")
    console.print(tree)

    # Check for groups
    if "groups" in astrometers:
        console.print(f"\n[green]✓ Found {len(astrometers['groups'])} meter groups[/green]")

        for group in astrometers["groups"]:
            group_name = group.get("name", "UNKNOWN")
            console.print(f"\n[bold]Group: {group_name}[/bold]")

            group_fields = ["name", "intensity", "harmony", "intensity_label", "harmony_label", "interpretation"]
            for field in group_fields:
                value = group.get(field)
                if value is None:
                    console.print(f"  [red]❌ {field}: NULL[/red]")
                elif isinstance(value, str) and value.strip() == "":
                    console.print(f"  [red]❌ {field}: EMPTY STRING[/red]")
                else:
                    console.print(f"  [green]✓ {field}: {type(value).__name__}[/green]")

    # Check for individual meters
    if "meters" in astrometers:
        console.print(f"\n[green]✓ Found {len(astrometers['meters'])} individual meters[/green]")

        if len(astrometers["meters"]) > 0:
            console.print("\n[bold]Sample Meter (first one):[/bold]")
            meter = astrometers["meters"][0]
            meter_name = meter.get("name", "UNKNOWN")
            console.print(f"Name: {meter_name}")

            meter_fields = ["name", "group", "intensity", "harmony",
                          "intensity_label", "harmony_label", "interpretation"]
            for field in meter_fields:
                value = meter.get(field)
                if value is None:
                    console.print(f"  [red]❌ {field}: NULL[/red]")
                elif isinstance(value, str) and value.strip() == "":
                    console.print(f"  [red]❌ {field}: EMPTY STRING[/red]")
                else:
                    preview = str(value)[:60] + "..." if len(str(value)) > 60 else str(value)
                    console.print(f"  [green]✓ {field}: {preview}[/green]")


def call_cloud_function(user_id: str, date: str) -> Dict[str, Any]:
    """Call the Cloud Function endpoint with proper Firebase client format."""
    console.print(f"\n[yellow]Calling Cloud Function...[/yellow]")
    console.print(f"URL: {FUNCTION_URL}")

    # Firebase callable functions expect data in { "data": {...} } format
    payload = {
        "data": {
            "user_id": user_id,
            "date": date
        }
    }

    console.print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            FUNCTION_URL,
            json=payload,
            headers={
                "Content-Type": "application/json"
            },
            timeout=60
        )

        console.print(f"[green]✓ Response status: {response.status_code}[/green]")

        if response.status_code != 200:
            console.print(f"[red]❌ Error response:[/red]")
            console.print(response.text)
            return None

        # Firebase callable functions return { "result": {...} }
        response_json = response.json()

        if "result" in response_json:
            return response_json["result"]
        else:
            return response_json

    except requests.exceptions.Timeout:
        console.print("[red]❌ Request timed out after 60 seconds[/red]")
        return None
    except Exception as e:
        console.print(f"[red]❌ Request failed: {e}[/red]")
        return None


def main():
    """Main execution function."""
    console.rule("[bold blue]Firebase Horoscope Debug Tool[/bold blue]")

    console.print(f"\n[bold]Parameters:[/bold]")
    console.print(f"  User ID: {TEST_USER_ID}")
    console.print(f"  Date: {TEST_DATE}")

    # Call the Cloud Function
    response = call_cloud_function(TEST_USER_ID, TEST_DATE)

    if not response:
        console.print("\n[red]❌ Failed to get response from Cloud Function[/red]")
        return 1

    # Save raw response
    output_file = "debug_horoscope_response.json"
    with open(output_file, "w") as f:
        json.dump(response, f, indent=2, default=str)
    console.print(f"\n[green]✓ Full response saved to: {output_file}[/green]")

    # Analyze the response
    console.print("\n" + "="*70)
    console.print("[bold cyan]FULL RESPONSE STRUCTURE[/bold cyan]")
    console.print("="*70 + "\n")

    tree = build_structure_tree(response, "horoscope_response")
    console.print(tree)

    # Find all empty/null fields
    console.print("\n" + "="*70)
    console.print("[bold yellow]EMPTY/NULL FIELDS ANALYSIS[/bold yellow]")
    console.print("="*70 + "\n")

    issues = analyze_value(response, "root")

    if issues:
        table = Table(title="Found Issues", show_header=True, header_style="bold red")
        table.add_column("Path", style="cyan")
        table.add_column("Issue Type", style="yellow")
        table.add_column("Value", style="red")

        for issue in issues:
            table.add_row(issue["path"], issue["issue"], issue["value"])

        console.print(table)
        console.print(f"\n[bold red]Found {len(issues)} empty/null fields![/bold red]")
    else:
        console.print("[bold green]✓ No empty/null fields found![/bold green]")

    # Specific meters analysis
    analyze_meters_data(response)

    console.rule("[bold blue]Analysis Complete[/bold blue]")

    return 0


if __name__ == "__main__":
    sys.exit(main())

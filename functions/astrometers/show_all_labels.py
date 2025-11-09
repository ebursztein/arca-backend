"""
Display all astrometer state labels in a table format for easy review.
Shows all 15 labels per meter (5 intensity levels × 3 qualities).
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

def load_labels(file_path):
    """Load experience labels from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)

    meter_name = data.get('metadata', {}).get('display_name') or data.get('_meter', 'Unknown')

    if 'experience_labels' not in data:
        return None, None

    labels = data['experience_labels']['combined']
    return meter_name, labels

def create_labels_table(meter_name, labels):
    """Create a Rich table showing all 15 labels for a meter."""
    table = Table(title=f"[bold cyan]{meter_name}[/bold cyan]", show_header=True, header_style="bold magenta")

    table.add_column("Intensity", style="dim", width=10)
    table.add_column("Challenging", style="red")
    table.add_column("Mixed", style="yellow")
    table.add_column("Harmonious", style="green")

    intensity_levels = ['quiet', 'mild', 'moderate', 'high', 'extreme']

    for intensity in intensity_levels:
        if intensity not in labels:
            continue

        challenging = labels[intensity].get('challenging', 'N/A')
        mixed = labels[intensity].get('mixed', 'N/A')
        harmonious = labels[intensity].get('harmonious', 'N/A')

        table.add_row(
            intensity.capitalize(),
            challenging,
            mixed,
            harmonious
        )

    return table

def main():
    """Display all meter labels in tables."""
    console = Console()
    labels_dir = Path(__file__).parent / 'labels'

    # Individual meters
    console.print("\n[bold blue]═══ INDIVIDUAL METERS ═══[/bold blue]\n")
    meter_files = sorted(labels_dir.glob('*.json'))

    for file_path in meter_files:
        meter_name, labels = load_labels(file_path)
        if labels:
            table = create_labels_table(meter_name, labels)
            console.print(table)
            console.print()

    # Group meters
    console.print("\n[bold blue]═══ GROUP METERS ═══[/bold blue]\n")
    group_files = sorted((labels_dir / 'groups').glob('*.json'))

    for file_path in group_files:
        meter_name, labels = load_labels(file_path)
        if labels:
            table = create_labels_table(meter_name, labels)
            console.print(table)
            console.print()

    # Summary stats
    total_files = len(meter_files) + len(group_files)
    total_labels = total_files * 15  # 5 intensity × 3 qualities
    console.print(f"\n[bold green]✓ Displayed {total_files} meters × 15 labels = {total_labels} total state labels[/bold green]\n")

if __name__ == '__main__':
    main()

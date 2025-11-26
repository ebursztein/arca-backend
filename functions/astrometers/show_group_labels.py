#!/usr/bin/env python3
"""
Show all group and individual meter state labels in formatted tables.

Usage:
    uv run python functions/astrometers/show_group_labels.py
"""

import json
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def show_individual_meter_labels():
    """Display all 17 individual meter state labels in formatted tables."""

    labels_dir = Path(__file__).parent / "labels"

    # All 17 individual meters
    meters = [
        'clarity', 'focus', 'communication',  # Mind
        'connections', 'resilience', 'vulnerability',  # Heart
        'energy', 'drive', 'strength',  # Body
        'vision', 'flow', 'intuition', 'creativity',  # Instincts
        'momentum', 'ambition', 'evolution', 'circle'  # Growth
    ]

    console.print("\n[bold cyan]═══ INDIVIDUAL METER LABELS (17 meters) ═══[/bold cyan]\n")

    for meter_name in meters:
        label_file = labels_dir / f"{meter_name}.json"

        if not label_file.exists():
            console.print(f"[red]⚠ {meter_name}.json not found[/red]")
            continue

        with open(label_file, 'r') as f:
            data = json.load(f)

        # Create table for this meter
        display_name = data['metadata']['display_name']
        group = data['metadata']['group']

        table = Table(
            title=f"{display_name} ({group})",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("Intensity", style="cyan", width=12)
        table.add_column("Challenging", style="red", width=25)
        table.add_column("Mixed", style="yellow", width=25)
        table.add_column("Harmonious", style="green", width=25)

        # Add rows for each intensity level
        labels = data['experience_labels']['combined']
        intensity_levels = ['quiet', 'mild', 'moderate', 'high', 'extreme']

        for intensity in intensity_levels:
            if intensity in labels:
                row = labels[intensity]
                table.add_row(
                    intensity.title(),
                    row['challenging'],
                    row['mixed'],
                    row['harmonious']
                )

        console.print(table)
        console.print()


def show_group_labels():
    """Display all group state labels in formatted tables."""

    labels_dir = Path(__file__).parent / "labels" / "groups"
    groups = ['mind', 'heart', 'body', 'instincts', 'growth', 'overall']

    console.print("\n[bold cyan]═══ GROUP STATE LABELS ═══[/bold cyan]\n")

    for group_name in groups:
        label_file = labels_dir / f"{group_name}.json"

        if not label_file.exists():
            console.print(f"[red]⚠ {group_name}.json not found[/red]")
            continue

        with open(label_file, 'r') as f:
            data = json.load(f)

        # Create table for this group
        table = Table(title=f"{data['metadata']['display_name']}", show_header=True, header_style="bold magenta")
        table.add_column("Intensity", style="cyan", width=12)
        table.add_column("Challenging", style="red", width=25)
        table.add_column("Mixed", style="yellow", width=25)
        table.add_column("Harmonious", style="green", width=25)

        # Add rows for each intensity level
        labels = data['experience_labels']['combined']
        intensity_levels = ['quiet', 'mild', 'moderate', 'high', 'extreme']

        for intensity in intensity_levels:
            if intensity in labels:
                row = labels[intensity]
                table.add_row(
                    intensity.title(),
                    row['challenging'],
                    row['mixed'],
                    row['harmonious']
                )

        console.print(table)
        console.print()


def show_overall_meters():
    """Display overall_intensity and overall_harmony labels."""

    labels_dir = Path(__file__).parent / "labels"

    console.print("\n[bold cyan]═══ OVERALL METER LABELS ═══[/bold cyan]\n")

    for meter_name in ['overall_intensity', 'overall_harmony']:
        label_file = labels_dir / f"{meter_name}.json"

        if not label_file.exists():
            console.print(f"[red]⚠ {meter_name}.json not found[/red]")
            continue

        with open(label_file, 'r') as f:
            data = json.load(f)

        # Create table
        table = Table(title=f"{data['metadata']['display_name']}", show_header=True, header_style="bold magenta")
        table.add_column("Intensity", style="cyan", width=12)
        table.add_column("Challenging", style="red", width=25)
        table.add_column("Mixed", style="yellow", width=25)
        table.add_column("Harmonious", style="green", width=25)

        # Add rows
        labels = data['experience_labels']['combined']
        intensity_levels = ['quiet', 'mild', 'moderate', 'high', 'extreme']

        for intensity in intensity_levels:
            if intensity in labels:
                row = labels[intensity]
                # For overall meters, all three quality columns have same value
                table.add_row(
                    intensity.title(),
                    row['challenging'],
                    row['mixed'],
                    row['harmonious']
                )

        console.print(table)
        console.print()


def check_label_quality():
    """Check for repetitive patterns in labels."""

    console.print("\n[bold cyan]═══ LABEL QUALITY CHECK ═══[/bold cyan]\n")

    labels_dir = Path(__file__).parent / "labels" / "groups"
    groups = ['mind', 'heart', 'body', 'instincts', 'growth', 'overall']

    # Check for repetitive words across groups
    all_labels = {}
    word_frequency = {}

    for group_name in groups:
        label_file = labels_dir / f"{group_name}.json"
        if not label_file.exists():
            continue

        with open(label_file, 'r') as f:
            data = json.load(f)

        labels = data['experience_labels']['combined']
        all_labels[group_name] = labels

        # Count word frequency
        for intensity in labels.values():
            for quality in intensity.values():
                words = quality.lower().split()
                for word in words:
                    word_frequency[word] = word_frequency.get(word, 0) + 1

    # Show most common words
    console.print("[yellow]Most common words across all group labels:[/yellow]")
    sorted_words = sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)
    for word, count in sorted_words[:15]:
        if count > 3:  # Only show words appearing more than 3 times
            console.print(f"  {word}: {count} times")

    console.print()

    # Check for identical labels across groups
    console.print("[yellow]Checking for duplicate labels across groups:[/yellow]")
    seen_labels = {}
    duplicates = []

    for group_name, labels in all_labels.items():
        for intensity, qualities in labels.items():
            for quality, label in qualities.items():
                key = label.lower()
                if key in seen_labels:
                    duplicates.append(f"  '{label}' appears in {seen_labels[key]} and {group_name}")
                else:
                    seen_labels[key] = f"{group_name}/{intensity}/{quality}"

    if duplicates:
        for dup in duplicates:
            console.print(f"[red]{dup}[/red]")
    else:
        console.print("[green]✓ No duplicate labels found[/green]")

    console.print()


if __name__ == "__main__":
    show_individual_meter_labels()
    show_group_labels()
    show_overall_meters()
    check_label_quality()

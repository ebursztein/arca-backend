"""
Demo script to display all 23 meters for today.

Usage:
  cd /Users/elie/git/arca/arca-backend
  uv run python -m functions.astrometers.show_meters

Fixed test user: Born 1990-06-15 (Gemini Sun)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Import astro functions
from astro import compute_birth_chart, find_natal_transit_aspects, Planet, AspectType

# Import astrometer functions
from astrometers.core import TransitAspect
from astrometers.meters import (
    calculate_overall_intensity_meter,
    calculate_overall_harmony_meter,
    calculate_mental_clarity_meter,
    calculate_decision_quality_meter,
    calculate_communication_flow_meter,
    calculate_emotional_intensity_meter,
    calculate_relationship_harmony_meter,
    calculate_emotional_resilience_meter,
    calculate_physical_energy_meter,
    calculate_conflict_risk_meter,
    calculate_motivation_drive_meter,
    calculate_career_ambition_meter,
    calculate_opportunity_window_meter,
    calculate_challenge_intensity_meter,
    calculate_transformation_pressure_meter,
    calculate_element_distribution,
    calculate_fire_energy_meter,
    calculate_earth_energy_meter,
    calculate_air_energy_meter,
    calculate_water_energy_meter,
    calculate_intuition_spirituality_meter,
    calculate_innovation_breakthrough_meter,
    calculate_karmic_lessons_meter,
    calculate_social_collective_meter,
)

console = Console()


def convert_to_transit_aspects(
    natal_chart: dict,
    transit_chart: dict,
    natal_transit_aspects: list
) -> list[TransitAspect]:
    """
    Convert NatalTransitAspect objects to TransitAspect format.

    Maps data from astro.find_natal_transit_aspects() to format
    expected by astrometers.core algorithms.
    """
    transit_aspects = []

    for aspect in natal_transit_aspects:
        # Get natal planet data
        natal_planet_data = next(
            (p for p in natal_chart["planets"] if p["name"] == aspect.natal_planet),
            None
        )
        if not natal_planet_data:
            continue

        # Get transit planet data
        transit_planet_data = next(
            (p for p in transit_chart["planets"] if p["name"] == aspect.transit_planet),
            None
        )
        if not transit_planet_data:
            continue

        # Determine max orb based on aspect type (from constants)
        max_orb_map = {
            AspectType.CONJUNCTION: 8.0,
            AspectType.OPPOSITION: 8.0,
            AspectType.TRINE: 8.0,
            AspectType.SQUARE: 7.0,
            AspectType.SEXTILE: 6.0,
        }
        max_orb = max_orb_map.get(aspect.aspect_type, 8.0)

        # Calculate tomorrow's orb (simple approximation)
        # This would ideally compute actual positions for tomorrow
        if aspect.applying:
            tomorrow_deviation = aspect.orb - 0.2  # Moving closer
        else:
            tomorrow_deviation = aspect.orb + 0.2  # Moving apart

        # Create TransitAspect
        ta = TransitAspect(
            natal_planet=aspect.natal_planet,
            natal_sign=aspect.natal_sign,
            natal_house=aspect.natal_house,
            transit_planet=aspect.transit_planet,
            aspect_type=aspect.aspect_type,
            orb_deviation=aspect.orb,
            max_orb=max_orb,
            natal_degree_in_sign=natal_planet_data.get("signed_degree", 0.0),
            ascendant_sign=natal_chart.get("ascendant_sign"),
            sensitivity=1.0,
            today_deviation=aspect.orb,
            tomorrow_deviation=tomorrow_deviation,
            label=f"Transit {aspect.transit_planet.value.title()} {aspect.aspect_type.value.title()} Natal {aspect.natal_planet.value.title()}"
        )
        transit_aspects.append(ta)

    return transit_aspects


def display_meter_reading(reading, console):
    """Display a single meter reading with rich formatting."""

    # Create header
    header = f"[bold]{reading.meter_name.replace('_', ' ').title()}[/bold]"

    # Create table for scores
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="yellow")

    table.add_row("Intensity", f"{reading.intensity:.1f}/100")
    table.add_row("Harmony", f"{reading.harmony:.1f}/100")
    table.add_row("State", reading.state_label)
    table.add_row("Raw DTI", f"{reading.raw_scores['dti']:.2f}")
    table.add_row("Raw HQS", f"{reading.raw_scores['hqs']:.2f}")

    # Build content
    content_parts = []

    # Add table
    from io import StringIO
    table_buffer = StringIO()
    table_console = Console(file=table_buffer, force_terminal=True, width=80)
    table_console.print(table)
    content_parts.append(table_buffer.getvalue())

    # Interpretation
    content_parts.append("\n[bold]Interpretation:[/bold]")
    content_parts.append(reading.interpretation)

    # Advice
    if reading.advice:
        content_parts.append("\n[bold]Advice:[/bold]")
        for advice_item in reading.advice:
            content_parts.append(f"• {advice_item}")

    # Top aspects
    if reading.top_aspects:
        content_parts.append("\n[bold]Top Contributing Aspects:[/bold]")
        for i, aspect in enumerate(reading.top_aspects[:3], 1):
            content_parts.append(f"{i}. {aspect.label}")
            content_parts.append(f"   W_i={aspect.weightage:.1f}, P_i={aspect.transit_power:.1f}, Q_i={aspect.quality_factor:.2f}")
            content_parts.append(f"   DTI={aspect.dti_contribution:.1f}, HQS={aspect.hqs_contribution:.1f}")

    content = "\n".join(content_parts)

    # Display panel
    panel = Panel(content, title=header, border_style="blue", box=box.ROUNDED)
    console.print(panel)
    console.print()


def main():
    """Run meter demo for fixed test user."""

    console.print("[bold blue]═══════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]     Astro Meters Demo - All 23 Meters    [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════[/bold blue]\n")

    # Fixed test user
    birth_date = "1990-06-15"  # Gemini Sun
    today = datetime.now().strftime("%Y-%m-%d")

    console.print(f"[cyan]Test User:[/cyan] Born {birth_date} (Gemini Sun)")
    console.print(f"[cyan]Analysis Date:[/cyan] {today}\n")

    # Get charts
    console.print("[yellow]Calculating natal chart...[/yellow]")
    natal_chart, is_exact = compute_birth_chart(birth_date)
    console.print(f"[green]✓[/green] Natal chart computed (exact: {is_exact})")

    console.print("[yellow]Calculating transit chart...[/yellow]")
    transit_chart, _ = compute_birth_chart(today, birth_time="12:00")
    console.print("[green]✓[/green] Transit chart computed")

    # Find aspects
    console.print("[yellow]Finding natal-transit aspects...[/yellow]")
    nt_aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=8.0)
    console.print(f"[green]✓[/green] Found {len(nt_aspects)} aspects\n")

    # Convert to TransitAspect format
    all_aspects = convert_to_transit_aspects(natal_chart, transit_chart, nt_aspects)

    # Calculate element distribution for element meters
    element_dist = calculate_element_distribution(natal_chart, transit_chart)

    # Calculate all meters
    date_obj = datetime.now()

    # GLOBAL METERS
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]           GLOBAL METERS (2)               [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    intensity = calculate_overall_intensity_meter(all_aspects, date_obj)
    display_meter_reading(intensity, console)

    harmony = calculate_overall_harmony_meter(all_aspects, date_obj)
    display_meter_reading(harmony, console)

    # COGNITIVE METERS
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]         COGNITIVE METERS (3)              [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    clarity = calculate_mental_clarity_meter(all_aspects, date_obj, transit_chart)
    display_meter_reading(clarity, console)

    decision = calculate_decision_quality_meter(all_aspects, date_obj)
    display_meter_reading(decision, console)

    comm = calculate_communication_flow_meter(all_aspects, date_obj)
    display_meter_reading(comm, console)

    # EMOTIONAL METERS
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]         EMOTIONAL METERS (3)              [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    emotion = calculate_emotional_intensity_meter(all_aspects, date_obj)
    display_meter_reading(emotion, console)

    relationship = calculate_relationship_harmony_meter(all_aspects, date_obj)
    display_meter_reading(relationship, console)

    resilience = calculate_emotional_resilience_meter(all_aspects, date_obj)
    display_meter_reading(resilience, console)

    # PHYSICAL/ACTION METERS
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]      PHYSICAL/ACTION METERS (3)           [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    physical = calculate_physical_energy_meter(all_aspects, date_obj)
    display_meter_reading(physical, console)

    conflict = calculate_conflict_risk_meter(all_aspects, date_obj)
    display_meter_reading(conflict, console)

    motivation = calculate_motivation_drive_meter(all_aspects, date_obj)
    display_meter_reading(motivation, console)

    # LIFE DOMAIN METERS
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]        LIFE DOMAIN METERS (4)             [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    career = calculate_career_ambition_meter(all_aspects, date_obj)
    display_meter_reading(career, console)

    opportunity = calculate_opportunity_window_meter(all_aspects, date_obj)
    display_meter_reading(opportunity, console)

    challenge = calculate_challenge_intensity_meter(all_aspects, date_obj)
    display_meter_reading(challenge, console)

    transformation = calculate_transformation_pressure_meter(all_aspects, date_obj)
    display_meter_reading(transformation, console)

    # ELEMENT METERS
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]          ELEMENT METERS (4)               [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    fire = calculate_fire_energy_meter(all_aspects, date_obj, element_dist)
    display_meter_reading(fire, console)

    earth = calculate_earth_energy_meter(all_aspects, date_obj, element_dist)
    display_meter_reading(earth, console)

    air = calculate_air_energy_meter(all_aspects, date_obj, element_dist)
    display_meter_reading(air, console)

    water = calculate_water_energy_meter(all_aspects, date_obj, element_dist)
    display_meter_reading(water, console)

    # SPECIALIZED METERS
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]        SPECIALIZED METERS (4)             [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    intuition = calculate_intuition_spirituality_meter(all_aspects, date_obj)
    display_meter_reading(intuition, console)

    innovation = calculate_innovation_breakthrough_meter(all_aspects, date_obj)
    display_meter_reading(innovation, console)

    karmic = calculate_karmic_lessons_meter(all_aspects, date_obj)
    display_meter_reading(karmic, console)

    social = calculate_social_collective_meter(all_aspects, date_obj)
    display_meter_reading(social, console)

    # Summary
    console.print("[bold blue]═══════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]               DEMO COMPLETE               [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════[/bold blue]\n")
    console.print(f"[green]✓[/green] All 23 meters calculated successfully")
    console.print(f"[green]✓[/green] Processed {len(all_aspects)} transit aspects")
    console.print(f"[green]✓[/green] Element distribution: Fire {element_dist['fire']:.1f}%, Earth {element_dist['earth']:.1f}%, Air {element_dist['air']:.1f}%, Water {element_dist['water']:.1f}%\n")


if __name__ == "__main__":
    main()

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

from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Import astro functions
from astro import compute_birth_chart, find_natal_transit_aspects, Planet, AspectType

# Import astrometer functions
from astrometers.core import TransitAspect
from astrometers.meters import get_meters, KeyAspect, AllMetersReading

console = Console()

# Note: convert_to_transit_aspects is now directly used from get_meters()
# (it was previously duplicated here but has been removed to avoid code duplication)


def display_key_aspects(key_aspects: list[KeyAspect], console):
    """Display major transit aspects affecting multiple meters."""

    if not key_aspects:
        return

    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]      MAJOR TRANSITS DRIVING YOUR DAY     [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]\n")

    intro = (
        "These key aspects are affecting multiple life areas. "
        "Understanding these major transits helps you see the bigger picture."
    )

    content_parts = [f"[italic]{intro}[/italic]\n"]

    for i, ka in enumerate(key_aspects, 1):
        aspect_symbol = {
            "conjunction": "☌",
            "opposition": "☍",
            "trine": "△",
            "square": "□",
            "sextile": "⚹",
        }.get(ka.aspect.aspect_type.value, ka.aspect.aspect_type.value)

        # Build aspect description
        transit_planet = ka.aspect.transit_planet.value.title()
        natal_planet = ka.aspect.natal_planet.value.title()

        content_parts.append(f"[bold cyan]{i}. {transit_planet} {aspect_symbol} {natal_planet}[/bold cyan]")
        content_parts.append(f"   [yellow]Strength:[/yellow] {ka.aspect.dti_contribution:.1f} DTI")
        content_parts.append(f"   [yellow]Quality:[/yellow] {'Harmonious' if ka.aspect.hqs_contribution > 0 else 'Challenging' if ka.aspect.hqs_contribution < 0 else 'Neutral'}")
        content_parts.append(f"   [yellow]Affects {ka.meter_count} meters:[/yellow]")
        content_parts.append(f"   {', '.join(ka.affected_meters)}")
        content_parts.append("")  # Blank line

    panel = Panel(
        "\n".join(content_parts),
        title="[bold magenta]🌟 Major Transits[/bold magenta]",
        border_style="magenta",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()


def display_meter_reading(reading, console):
    """Display a single meter reading with rich formatting."""

    # Trend indicator
    trend_indicator = ""
    if reading.trend:
        trend_symbols = {
            "improving": "↑ [green]Improving[/green]",
            "stable": "→ [blue]Stable[/blue]",
            "worsening": "↓ [red]Worsening[/red]"
        }
        trend_indicator = f" {trend_symbols.get(reading.trend.value, '')}"

    # Create header with unified score and trend
    header = (
        f"[bold]{reading.meter_name.replace('_', ' ').title()}[/bold] "
        f"[yellow]{reading.unified_score:.0f}/100[/yellow] "
        f"[dim]({reading.unified_quality.value})[/dim]"
        f"{trend_indicator}"
    )

    # Create table for scores
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="yellow")

    table.add_row("Group", reading.group.value.replace('_', ' ').title())
    table.add_row("Unified Score", f"{reading.unified_score:.1f}/100")
    table.add_row("Quality", reading.unified_quality.value.title())
    if reading.trend:
        table.add_row("Trend", reading.trend.value.title())
    table.add_row("", "")  # Separator
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
    today_date = datetime.now()
    yesterday_date = today_date - timedelta(days=1)

    console.print(f"[cyan]Test User:[/cyan] Born {birth_date} (Gemini Sun)")
    console.print(f"[cyan]Analysis Date:[/cyan] {today_date.strftime('%Y-%m-%d')}")
    console.print(f"[cyan]Comparing with:[/cyan] {yesterday_date.strftime('%Y-%m-%d')} (for trends)\n")

    # Get natal chart
    console.print("[yellow]Calculating natal chart...[/yellow]")
    natal_chart, is_exact = compute_birth_chart(birth_date)
    console.print(f"[green]✓[/green] Natal chart computed (exact: {is_exact})")

    # Get yesterday's meters
    console.print("[yellow]Calculating yesterday's transits...[/yellow]")
    yesterday_transit, _ = compute_birth_chart(yesterday_date.strftime("%Y-%m-%d"), birth_time="12:00")
    yesterday_meters = get_meters(natal_chart, yesterday_transit)
    console.print(f"[green]✓[/green] Yesterday computed ({yesterday_meters.aspect_count} aspects)")

    # Get today's meters
    console.print("[yellow]Calculating today's transits...[/yellow]")
    today_transit, _ = compute_birth_chart(today_date.strftime("%Y-%m-%d"), birth_time="12:00")
    all_meters = get_meters(natal_chart, today_transit)
    console.print(f"[green]✓[/green] Today computed ({all_meters.aspect_count} aspects)\n")

    # Calculate and set trends for all meters
    console.print("[yellow]Calculating trends...[/yellow]")
    meter_names = [
        'overall_intensity', 'overall_harmony',
        'mental_clarity', 'decision_quality', 'communication_flow',
        'emotional_intensity', 'relationship_harmony', 'emotional_resilience',
        'physical_energy', 'conflict_risk', 'motivation_drive',
        'career_ambition', 'opportunity_window', 'challenge_intensity', 'transformation_pressure',
        'fire_energy', 'earth_energy', 'air_energy', 'water_energy',
        'intuition_spirituality', 'innovation_breakthrough', 'karmic_lessons', 'social_collective'
    ]
    for meter_name in meter_names:
        today_meter = getattr(all_meters, meter_name)
        yesterday_meter = getattr(yesterday_meters, meter_name)
        today_meter.trend = today_meter.calculate_trend(yesterday_meter)
    console.print(f"[green]✓[/green] Trends calculated\n")

    # Display overall unified score at the top
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]         OVERALL DAY SUMMARY                [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]\n")
    console.print(f"[bold yellow]Overall Unified Score:[/bold yellow] {all_meters.overall_unified_score:.1f}/100")
    console.print(f"[bold yellow]Overall Quality:[/bold yellow] {all_meters.overall_unified_quality.value.title()}")
    console.print(f"[bold yellow]Total Aspects:[/bold yellow] {all_meters.aspect_count}\n")

    # Display key aspects first (deduplicated major transits)
    display_key_aspects(all_meters.key_aspects, console)

    # OVERVIEW METERS (Group: OVERVIEW)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]         OVERVIEW - Overall Energy (2)     [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.overall_intensity, console)
    display_meter_reading(all_meters.overall_harmony, console)

    # DECISIONS METERS (Group: DECISIONS)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]      DECISIONS - Mental & Communication (3)[/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.mental_clarity, console)
    display_meter_reading(all_meters.decision_quality, console)
    display_meter_reading(all_meters.communication_flow, console)

    # LOVE METERS (Group: LOVE)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]         LOVE - Relationships & Romance (2) [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.emotional_intensity, console)
    display_meter_reading(all_meters.relationship_harmony, console)

    # HOME METERS (Group: HOME)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]       HOME - Foundation & Security (1)     [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.emotional_resilience, console)

    # MIND_BODY METERS (Group: MIND_BODY)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]      MIND_BODY - Physical Energy (3)       [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.physical_energy, console)
    display_meter_reading(all_meters.conflict_risk, console)
    display_meter_reading(all_meters.motivation_drive, console)

    # CAREER METERS (Group: CAREER)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]        CAREER - Professional Life (2)      [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.career_ambition, console)
    display_meter_reading(all_meters.opportunity_window, console)

    # GROWTH METERS (Group: GROWTH)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]       GROWTH - Transformation (3)          [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.challenge_intensity, console)
    display_meter_reading(all_meters.transformation_pressure, console)
    display_meter_reading(all_meters.innovation_breakthrough, console)

    # ELEMENTAL METERS (Group: ELEMENTAL)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]        ELEMENTAL - Energy Qualities (4)    [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.fire_energy, console)
    display_meter_reading(all_meters.earth_energy, console)
    display_meter_reading(all_meters.air_energy, console)
    display_meter_reading(all_meters.water_energy, console)

    # PURPOSE METERS (Group: PURPOSE)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]      PURPOSE - Spiritual Path (2)          [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.intuition_spirituality, console)
    display_meter_reading(all_meters.karmic_lessons, console)

    # FAMILY METERS (Group: FAMILY)
    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]        FAMILY - Social Connections (1)     [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    display_meter_reading(all_meters.social_collective, console)

    # Summary
    console.print("[bold blue]═══════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]               DEMO COMPLETE               [/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════[/bold blue]\n")
    console.print(f"[green]✓[/green] All 23 meters calculated successfully")
    console.print(f"[green]✓[/green] Identified {len(all_meters.key_aspects)} major transits affecting multiple domains\n")


if __name__ == "__main__":
    main()

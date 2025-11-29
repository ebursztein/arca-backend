"""
Test script for enhanced transit reporting features.

Tests:
- Critical degree detection
- Transit speed analysis
- Priority scoring
- Formatted UI summaries
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from astro import (
    compute_birth_chart,
    find_natal_transit_aspects,
    format_transit_summary_for_ui,
    check_critical_degrees,
    analyze_planet_speed,
    ZodiacSign,
    Planet
)
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

console = Console()


def test_critical_degrees():
    """Test critical degree detection."""
    console.print("\n[bold cyan]Testing Critical Degree Detection[/bold cyan]")
    console.print("=" * 80)

    test_cases = [
        (29.2, ZodiacSign.SCORPIO, "Anaretic (29°)"),
        (0.5, ZodiacSign.ARIES, "Avatar (0°) + Cardinal"),
        (13.1, ZodiacSign.CANCER, "Critical Cardinal (13°)"),
        (15.0, ZodiacSign.TAURUS, "No critical degree")
    ]

    for degree, sign, expected in test_cases:
        result = check_critical_degrees(degree, sign)
        console.print(f"\n{sign.value.title()} {degree}° - Expected: {expected}")
        if result:
            for deg_type, desc in result:
                console.print(f"  Found: {deg_type.value} - {desc}", style="green")
        else:
            console.print("  No critical degrees", style="dim")


def test_speed_analysis():
    """Test transit speed classification."""
    console.print("\n\n[bold cyan]Testing Transit Speed Analysis[/bold cyan]")
    console.print("=" * 80)

    test_cases = [
        (Planet.MARS, 0.05, "Stationary"),
        (Planet.MARS, 0.2, "Slow"),
        (Planet.MARS, 0.5, "Average"),
        (Planet.MARS, 0.8, "Fast"),
        (Planet.MERCURY, -0.05, "Stationary/Retrograde")
    ]

    for planet, motion, expected in test_cases:
        speed_enum, desc = analyze_planet_speed(planet, motion)
        console.print(f"\n{planet.value.title()}: {motion}°/day - Expected: {expected}")
        console.print(f"  Result: {speed_enum.value} - {desc}", style="green")


def test_full_transit_analysis():
    """Test complete transit analysis with real charts."""
    console.print("\n\n[bold cyan]Testing Full Transit Analysis[/bold cyan]")
    console.print("=" * 80)

    # Create natal chart (May 15, 1985)
    natal_chart, _ = compute_birth_chart(
        birth_date="1985-05-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )

    # Create transit chart (today)
    transit_chart, _ = compute_birth_chart(
        birth_date="2025-11-03",
        birth_time="12:00",
        birth_timezone="UTC",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )

    console.print(f"\n[yellow]Natal Chart:[/yellow] May 15, 1985, 14:30 EST (New York)")
    console.print(f"[yellow]Transit Chart:[/yellow] November 3, 2025, 12:00 UTC")

    # Find aspects
    aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=3.0)

    if not aspects:
        console.print("\n[red]No aspects found within orb[/red]")
        return

    console.print(f"\n[green]Found {len(aspects)} aspects[/green]")

    # Create table
    table = Table(title="Priority Transit Aspects (Top 10)")
    table.add_column("Priority", justify="right", style="cyan")
    table.add_column("Aspect", style="yellow")
    table.add_column("Orb", justify="right")
    table.add_column("Status", style="magenta")
    table.add_column("Speed", style="blue")
    table.add_column("Critical", style="red")

    for aspect in aspects[:10]:
        applying_status = "Applying" if aspect.applying else "Separating"

        # Format critical degrees
        critical = []
        if aspect.transit_critical_degrees:
            critical.append("T:" + aspect.transit_critical_degrees[0][0][:4])
        if aspect.natal_critical_degrees:
            critical.append("N:" + aspect.natal_critical_degrees[0][0][:4])
        critical_str = ", ".join(critical) if critical else "-"

        table.add_row(
            str(aspect.priority_score),
            f"{aspect.transit_planet.value.title()} {aspect.aspect_type.value} natal {aspect.natal_planet.value.title()}",
            f"{aspect.orb}°",
            applying_status,
            aspect.transit_speed.value if aspect.transit_speed else "-",
            critical_str
        )

    console.print(table)


def test_ui_format():
    """Test UI-formatted transit summary."""
    console.print("\n\n[bold cyan]Testing UI-Formatted Transit Summary[/bold cyan]")
    console.print("=" * 80)

    # Create charts - MUST use same birth data as test_full_transit_analysis for consistent orbs
    natal_chart, _ = compute_birth_chart(
        birth_date="1985-05-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )
    transit_chart, _ = compute_birth_chart(
        birth_date="2025-11-03",
        birth_time="12:00",
        birth_timezone="UTC",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )

    # Get formatted summary
    summary = format_transit_summary_for_ui(natal_chart, transit_chart, max_aspects=5)

    console.print("\n[yellow]Priority Transits (Top 5):[/yellow]")
    for i, transit in enumerate(summary["priority_transits"], 1):
        console.print(f"\n{i}. [bold]{transit['description']}[/bold]")
        if transit.get('intensity_label'):
            console.print(f"   {transit['intensity_label']}", style="bold magenta")
        console.print(f"   Priority: {transit['priority_score']} | Orb: {transit['orb']}° ({transit['orb_label']}, {transit['applying_label']})")
        console.print(f"   Meaning: {transit['meaning']}")

        # Enhanced speed timing details
        if transit.get('speed_timing'):
            st = transit['speed_timing']
            console.print(f"   Speed: {st['speed_description']}", style="blue")
            if st['timing_impact']:
                console.print(f"   Impact: {st['timing_impact']}", style="cyan")
            if st['peak_window']:
                console.print(f"   Peak: {st['peak_window']}", style="cyan")
            if st['best_use']:
                console.print(f"   Best use: {st['best_use']}", style="green")

        if transit['critical_degrees']:
            console.print(f"   Critical: {', '.join(transit['critical_degrees'])}", style="red")

    # Critical Degree Synthesis
    if summary["critical_degree_synthesis"]["major_timing_alert"]:
        console.print(f"\n[bold red]{summary['critical_degree_synthesis']['intensity']}:[/bold red]")
        console.print(Panel(
            summary["critical_degree_synthesis"]["interpretation"],
            title="Critical Degree Synthesis",
            border_style="red"
        ))

        if summary["critical_degree_synthesis"]["anaretic_planets"]:
            console.print("\n[red]Anaretic (29°) - Endings/Crisis:[/red]")
            for p in summary["critical_degree_synthesis"]["anaretic_planets"]:
                console.print(f"  • {p['planet']} at {p['degree']}° {p['sign']}")

        if summary["critical_degree_synthesis"]["avatar_planets"]:
            console.print("\n[green]Avatar (0°) - New Beginnings:[/green]")
            for p in summary["critical_degree_synthesis"]["avatar_planets"]:
                console.print(f"  • {p['planet']} at {p['degree']}° {p['sign']}")

    elif summary["critical_degree_alerts"]:
        console.print("\n[yellow]Critical Degree Alerts:[/yellow]")
        for alert in summary["critical_degree_alerts"]:
            console.print(f"  {alert['planet']} at {alert['degree']:.1f}° {alert['sign']} - {alert['type'].upper()}")

    # Theme Synthesis
    console.print("\n[bold cyan]Theme Synthesis:[/bold cyan]")
    console.print(Panel(
        summary["theme_synthesis"]["theme_synthesis"],
        title="Overall Pattern",
        border_style="cyan"
    ))
    console.print(f"Balance: {summary['theme_synthesis']['harmony_tension_balance'].upper()} - {summary['theme_synthesis']['balance_description']}")
    console.print(f"Harmonious: {summary['theme_synthesis']['total_harmonious']} | Challenging: {summary['theme_synthesis']['total_challenging']}")

    if summary["theme_synthesis"]["convergence_patterns"]:
        console.print("\n[magenta]Convergence Patterns:[/magenta]")
        for pattern in summary["theme_synthesis"]["convergence_patterns"]:
            console.print(f"  • {pattern['focal_planet']} ← {', '.join(pattern['aspecting_planets'])}")
            console.print(f"    {pattern['interpretation']}", style="dim")

    # House Context Examples
    console.print("\n[yellow]House Context Examples (Top 3):[/yellow]")
    for i, transit in enumerate(summary["priority_transits"][:3], 1):
        if transit.get("house_context"):
            console.print(f"\n{i}. {transit['description']}")
            console.print(f"   {transit['house_context']}", style="blue")

    if summary["retrograde_planets"]:
        console.print("\n[yellow]Retrograde Planets:[/yellow]")
        for retro in summary["retrograde_planets"]:
            console.print(f"  {retro['planet']} Rx in {retro['sign']} ({retro['degree']}°) - {retro['speed_status']}")
            if retro.get('natal_connection'):
                console.print(f"    {retro['natal_connection']['message']}", style="bold yellow")
            if retro.get('natal_aspects'):
                console.print("    Natal aspects:", style="cyan")
                for asp in retro['natal_aspects']:
                    console.print(f"      • {asp['message']} (orb {asp['orb']}°)", style="cyan")

    console.print(f"\n[green]Total aspects found: {summary['total_aspects_found']}[/green]")

    # Also print as JSON for iOS integration
    console.print("\n[yellow]JSON Output (sample for iOS):[/yellow]")
    console.print(Panel(json.dumps(summary["priority_transits"][0], indent=2), title="First Priority Transit"))
    console.print("\n[yellow]Critical Synthesis JSON:[/yellow]")
    console.print(Panel(json.dumps(summary["critical_degree_synthesis"], indent=2), title="Critical Degree Synthesis"))


def main():
    """Run all tests."""
    console.print("[bold magenta]Enhanced Transit Reporting Test Suite[/bold magenta]")
    console.print("=" * 80)

    try:
        test_critical_degrees()
        test_speed_analysis()
        test_full_transit_analysis()
        test_ui_format()

        console.print("\n\n[bold green]All tests completed successfully![/bold green]")
    except Exception as e:
        console.print(f"\n\n[bold red]Test failed with error:[/bold red]")
        console.print(f"{type(e).__name__}: {str(e)}")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()

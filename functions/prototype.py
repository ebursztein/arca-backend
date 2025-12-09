#!/usr/bin/env python3
"""
End-to-End Prototype for Arca Backend V1

Demonstrates complete user journey using INTERNAL function calls (no emulator required):
1. User onboarding with birth date
2. Sun sign calculation and profile loading
3. Daily transit data generation
4. LLM-powered horoscope generation with astrometers
5. Display of all horoscope fields including relationship weather

This prototype validates the entire V1 workflow using direct Python imports.

Usage:
    cd functions && uv run python prototype.py

Requirements:
    - GEMINI_API_KEY environment variable
    - POSTHOG_API_KEY environment variable (optional)
"""

import os
import json
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

# Internal imports - direct function calls
from astro import (
    get_sun_sign,
    get_sun_sign_profile,
    compute_birth_chart,
    format_transit_summary_for_ui,
    ZodiacSign,
    SunSignProfile,
    NatalChartData,
)
from llm import generate_daily_horoscope, select_featured_connection
from models import (
    UserProfile,
    MemoryCollection,
    DailyHoroscope,
    create_empty_memory,
)

console = Console()

# Default model
DEFAULT_MODEL = "gemini-2.5-flash-lite"


def print_section(title: str, content: str = "", style: str = "bold cyan"):
    """Print a formatted section with rich styling."""
    console.print(f"\n[{style}]{'=' * 70}[/{style}]")
    console.print(f"[{style}]{title}[/{style}]")
    if content:
        console.print(f"[{style}]{'=' * 70}[/{style}]")
        console.print(content)
    console.print(f"[{style}]{'=' * 70}[/{style}]\n")


def main(model_name: str = DEFAULT_MODEL):
    """
    Run the end-to-end prototype simulation using internal function calls.
    """

    print_section("ARCA BACKEND V1 PROTOTYPE (Internal)", style="bold magenta")

    # Check for API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY environment variable not set[/red]")
        return

    posthog_api_key = os.environ.get("POSTHOG_API_KEY")

    # ========================================================================
    # 1. USER ONBOARDING
    # ========================================================================
    print_section("1. USER ONBOARDING", style="bold cyan")

    # Simulated user data
    user_id = "test_user_internal"
    user_name = "Elie"
    birth_date = "1987-06-02"

    console.print(f"[cyan]Creating user profile...[/cyan]")
    console.print(f"  User ID: {user_id}")
    console.print(f"  Name: {user_name}")
    console.print(f"  Birth Date: {birth_date}")

    # Calculate sun sign
    sun_sign = get_sun_sign(birth_date)
    console.print(f"[green]Sun Sign: {sun_sign.value.title()}[/green]")

    # Load sun sign profile
    sun_sign_profile = get_sun_sign_profile(sun_sign)
    if not sun_sign_profile:
        console.print(f"[red]Error: Sun sign profile not found for {sun_sign.value}[/red]")
        return

    console.print(f"\n[yellow]Sun Sign Profile:[/yellow]")
    console.print(f"  Element: {sun_sign_profile.element.value.title()}")
    console.print(f"  Modality: {sun_sign_profile.modality.value.title()}")
    console.print(f"  Ruling Planet: {sun_sign_profile.ruling_planet}")

    # Compute birth chart (V1 mode - approximate, no birth time)
    console.print(f"\n[cyan]Computing birth chart...[/cyan]")
    natal_chart, is_exact = compute_birth_chart(birth_date)
    console.print(f"[green]Birth chart computed (exact: {is_exact})[/green]")
    console.print(f"  Planets: {len(natal_chart['planets'])}")
    console.print(f"  Houses: {len(natal_chart['houses'])}")
    console.print(f"  Aspects: {len(natal_chart['aspects'])}")

    # Create UserProfile
    user_profile = UserProfile(
        user_id=user_id,
        name=user_name,
        email=f"{user_id}@test.com",
        birth_date=birth_date,
        birth_time=None,
        birth_timezone=None,
        birth_lat=None,
        birth_lon=None,
        sun_sign=sun_sign.value,
        natal_chart=natal_chart,
        exact_chart=is_exact,
        created_at=datetime.now().isoformat(),
        last_active=datetime.now().isoformat()
    )
    console.print(f"[green]User profile created[/green]")

    # Initialize empty memory
    memory = create_empty_memory(user_id)
    console.print(f"[green]Memory collection initialized[/green]")

    # ========================================================================
    # 2. CREATE SAMPLE CONNECTION (for relationship weather)
    # ========================================================================
    print_section("2. SAMPLE CONNECTION", style="bold cyan")

    # Create a sample featured connection for relationship weather
    featured_connection = {
        "connection_id": "sample_conn_1",
        "name": "John",
        "birth_date": "1992-08-15",
        "birth_time": "14:30",
        "birth_timezone": "America/New_York",
        "birth_lat": 40.7128,
        "birth_lon": -74.0060,
        "relationship_category": "love",
        "relationship_label": "partner",
        "sun_sign": "leo",
    }

    console.print(f"[cyan]Featured Connection:[/cyan]")
    console.print(f"  Name: {featured_connection['name']}")
    console.print(f"  Birth Date: {featured_connection['birth_date']}")
    console.print(f"  Relationship: {featured_connection['relationship_category']} / {featured_connection['relationship_label']}")
    console.print(f"  Sun Sign: {featured_connection.get('sun_sign', 'unknown')}")

    # Compute synastry if birth data available
    if featured_connection.get("birth_date"):
        try:
            from compatibility import calculate_synastry_points, find_transits_to_synastry, calculate_vibe_score

            # Compute connection's natal chart
            conn_chart, _ = compute_birth_chart(
                birth_date=featured_connection["birth_date"],
                birth_time=featured_connection.get("birth_time"),
                birth_timezone=featured_connection.get("birth_timezone"),
                birth_lat=featured_connection.get("birth_lat"),
                birth_lon=featured_connection.get("birth_lon")
            )
            user_chart_data = NatalChartData(**natal_chart)
            conn_chart_data = NatalChartData(**conn_chart)

            # Calculate synastry points
            synastry_points = calculate_synastry_points(user_chart_data, conn_chart_data)
            featured_connection["synastry_points"] = synastry_points
            console.print(f"[green]Synastry points computed: {len(synastry_points)}[/green]")

            # Show first few synastry points
            for point in synastry_points[:3]:
                console.print(f"    - {point.get('label', 'unknown')} at {point.get('degree', 0):.1f} deg")

        except Exception as e:
            console.print(f"[yellow]Warning: Could not compute synastry: {e}[/yellow]")

    # ========================================================================
    # 3. DAILY HOROSCOPE GENERATION
    # ========================================================================
    print_section("3. DAILY HOROSCOPE GENERATION", style="bold cyan")

    today = datetime.now().strftime("%Y-%m-%d")
    console.print(f"[cyan]Date:[/cyan] {today}")

    # Compute transit chart for today
    console.print(f"\n[cyan]Computing current transits...[/cyan]")
    transit_chart, _ = compute_birth_chart(
        birth_date=today,
        birth_time="12:00"  # Use noon for transits
    )
    console.print(f"[green]Transit chart computed[/green]")

    # Generate transit summary
    console.print(f"\n[cyan]Generating transit summary...[/cyan]")
    transit_summary = format_transit_summary_for_ui(natal_chart, transit_chart, max_aspects=5)
    console.print(f"[green]Transit summary generated[/green]")
    console.print(f"  Priority transits: {len(transit_summary.get('priority_transits', []))}")

    # Enrich featured connection with transit data
    if featured_connection.get("synastry_points"):
        try:
            transit_chart_data = NatalChartData(**transit_chart)
            active_transits = find_transits_to_synastry(
                transit_chart=transit_chart_data,
                synastry_points=featured_connection["synastry_points"],
                orb=3.0
            )
            vibe_score = calculate_vibe_score(active_transits)
            featured_connection["active_transits"] = active_transits
            featured_connection["vibe_score"] = vibe_score
            console.print(f"[green]Connection vibe score: {vibe_score}/100[/green]")
            console.print(f"[green]Active transits: {len(active_transits)}[/green]")
            for t in active_transits[:5]:
                console.print(f"    - {t['description']} (harmonious: {t['is_harmonious']}, orb: {t['orb']})")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not compute vibe score: {e}[/yellow]")

    # Compute connection age
    conn_birth_date = featured_connection.get("birth_date")
    if conn_birth_date:
        try:
            conn_birth_year = int(conn_birth_date.split("-")[0])
            current_year = int(today.split("-")[0])
            featured_connection["age"] = current_year - conn_birth_year
        except (ValueError, IndexError):
            pass

    # Generate daily horoscope
    console.print(f"\n[cyan]Generating daily horoscope (this may take 30-60 seconds)...[/cyan]")
    console.print(f"  Model: {model_name}")

    daily_horoscope = generate_daily_horoscope(
        date=today,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_summary=transit_summary,
        memory=memory,
        featured_connection=featured_connection,
        api_key=api_key,
        posthog_api_key=posthog_api_key,
        model_name=model_name,
        yesterday_meters=None,
    )

    console.print(f"[green]Daily horoscope generated[/green]")
    console.print(f"  Generation time: {daily_horoscope.generation_time_ms}ms")
    console.print(f"  Model: {daily_horoscope.model_used}")

    # Save horoscope to JSON for inspection
    horoscope_dict = daily_horoscope.model_dump()
    with open('debug_daily_horoscope.json', 'w') as f:
        json.dump(horoscope_dict, f, indent=2, default=str)
    console.print(f"[dim]Saved to debug_daily_horoscope.json[/dim]")

    # ========================================================================
    # 4. DISPLAY HOROSCOPE
    # ========================================================================
    print_section("4. YOUR DAILY HOROSCOPE", style="bold magenta")

    console.print(f"[bold cyan]{today} - {sun_sign.value.title()}[/bold cyan]\n")

    # Daily Theme Headline
    console.print(Panel(
        daily_horoscope.daily_theme_headline,
        title="[bold magenta]Daily Theme[/bold magenta]",
        border_style="magenta"
    ))

    # Daily Overview
    console.print(Panel(
        daily_horoscope.daily_overview,
        title="[bold cyan]Today's Energy[/bold cyan]",
        border_style="cyan"
    ))

    # Technical Analysis
    console.print(Panel(
        daily_horoscope.technical_analysis,
        title="[bold yellow]Technical Analysis[/bold yellow]",
        border_style="yellow"
    ))

    # Actionable Advice
    advice = daily_horoscope.actionable_advice
    advice_text = f"DO: {advice.do}\n\nDON'T: {advice.dont}\n\nREFLECT ON: {advice.reflect_on}"
    console.print(Panel(
        advice_text,
        title="[bold green]Actionable Guidance[/bold green]",
        border_style="green"
    ))

    # Moon Detail
    if daily_horoscope.moon_detail:
        moon_detail = daily_horoscope.moon_detail
        moon_interp = moon_detail.get("interpretation", "") if isinstance(moon_detail, dict) else getattr(moon_detail, "interpretation", "")
        if moon_interp:
            console.print(Panel(
                moon_interp,
                title="[bold white]Lunar Cycle[/bold white]",
                border_style="white"
            ))

    # Energy Rhythm
    if daily_horoscope.energy_rhythm:
        console.print(Panel(
            daily_horoscope.energy_rhythm,
            title="[bold blue]Energy Rhythm[/bold blue]",
            border_style="blue"
        ))

    # Collective Energy
    if daily_horoscope.collective_energy:
        console.print(Panel(
            daily_horoscope.collective_energy,
            title="[bold cyan]Collective Energy[/bold cyan]",
            border_style="cyan"
        ))

    # Relationship Weather
    if daily_horoscope.relationship_weather:
        rw = daily_horoscope.relationship_weather
        rw_text = f"Overview: {rw.overview}"

        # Connection vibes
        for cv in rw.connection_vibes:
            rw_text += f"\n\n{cv.name} ({cv.relationship_label}): {cv.vibe}"
            if cv.vibe_score is not None:
                rw_text += f"\n  Vibe Score: {cv.vibe_score}/100"
            if cv.key_transit:
                rw_text += f"\n  Key Transit: {cv.key_transit}"

        console.print(Panel(
            rw_text,
            title="[bold magenta]Relationship Weather[/bold magenta]",
            border_style="magenta"
        ))

        # Debug: show raw connection vibe data
        console.print(f"\n[dim]Debug - Connection Vibe Data:[/dim]")
        for cv in rw.connection_vibes:
            console.print(f"  [dim]- name: {cv.name}[/dim]")
            console.print(f"  [dim]- vibe_score: {cv.vibe_score}[/dim]")
            console.print(f"  [dim]- key_transit: {cv.key_transit}[/dim]")

    # Look Ahead Preview
    if daily_horoscope.look_ahead_preview:
        console.print(Panel(
            daily_horoscope.look_ahead_preview,
            title="[bold yellow]Coming Soon[/bold yellow]",
            border_style="yellow"
        ))

    # Follow-up Questions
    if daily_horoscope.follow_up_questions:
        questions_text = "\n".join([f"- {q}" for q in daily_horoscope.follow_up_questions])
        console.print(Panel(
            questions_text,
            title="[bold cyan]Ask the Stars[/bold cyan]",
            border_style="cyan"
        ))

    # ========================================================================
    # 5. ASTROMETERS SUMMARY
    # ========================================================================
    print_section("5. ASTROMETERS ANALYSIS", style="bold cyan")

    astrometers = daily_horoscope.astrometers
    if astrometers:
        # Convert to dict if it's a Pydantic model
        if hasattr(astrometers, 'model_dump'):
            astrometers_dict = astrometers.model_dump()
        else:
            astrometers_dict = astrometers

        console.print(f"[yellow]Overall Metrics:[/yellow]")
        console.print(f"  - Unified Score: {astrometers_dict.get('overall_unified_score', 0):.1f}/100")
        console.print(f"  - State: {astrometers_dict.get('overall_state', 'unknown')}")
        console.print(f"  - Quality: {astrometers_dict.get('overall_quality', 'unknown').upper()}\n")

        console.print(f"[yellow]Top Meters:[/yellow]")
        console.print(f"  - Most Active: {', '.join(astrometers_dict.get('top_active_meters', []))}")
        console.print(f"  - Most Challenging: {', '.join(astrometers_dict.get('top_challenging_meters', []))}")
        console.print(f"  - Most Flowing: {', '.join(astrometers_dict.get('top_flowing_meters', []))}\n")

        # Groups
        console.print(f"\n[yellow]Meter Groups (5 Life Areas):[/yellow]\n")
        group_icons = {
            "mind": "[M]",
            "heart": "[H]",
            "body": "[B]",
            "instincts": "[I]",
            "growth": "[G]"
        }

        for group in astrometers_dict.get("groups", []):
            group_name = group.get("group_name", "")
            icon = group_icons.get(group_name, "[?]")
            meter_names = [m.get('display_name', '') for m in group.get('meters', [])]

            scores_text = (
                f"Score: {group.get('unified_score', 0):.1f}/100\n"
                f"State: {group.get('state_label', '')} ({group.get('quality', '').upper()})\n\n"
                f"{group.get('interpretation', '')}\n\n"
                f"Member Meters: {', '.join(meter_names)}"
            )

            console.print(Panel(
                scores_text,
                title=f"[bold]{icon} {group.get('display_name', '')}[/bold]",
                border_style="blue"
            ))

    # ========================================================================
    # 6. PERFORMANCE SUMMARY
    # ========================================================================
    print_section("6. PERFORMANCE SUMMARY", style="bold cyan")

    table = Table(title="LLM Token Usage", show_header=True, header_style="bold magenta")
    table.add_column("Stage", style="dim", width=25)
    table.add_column("Model", style="dim", width=22)
    table.add_column("Time (s)", justify="right")
    table.add_column("Prompt", justify="right")
    table.add_column("Output", justify="right")
    table.add_column("Thinking", justify="right")
    table.add_column("Total", justify="right")

    usage = daily_horoscope.usage or {}
    table.add_row(
        "Daily Horoscope",
        daily_horoscope.model_used or "N/A",
        f"{(daily_horoscope.generation_time_ms or 0) / 1000:.2f}",
        str(usage.get('prompt_token_count', 0)),
        str(usage.get('candidates_token_count', 0)),
        str(usage.get('thoughts_token_count', 0)),
        str(usage.get('total_token_count', 0)),
    )

    console.print(table)

    print_section("PROTOTYPE COMPLETE", style="bold magenta")


if __name__ == "__main__":
    import sys

    # Parse command line args
    model = DEFAULT_MODEL
    for arg in sys.argv[1:]:
        if arg.startswith("--model="):
            model = arg.split("=")[1]
        elif arg == "--flash":
            model = "gemini-2.5-flash"
        elif arg == "--lite":
            model = "gemini-2.5-flash-lite"

    try:
        main(model_name=model)
    except KeyboardInterrupt:
        console.print("\n[yellow]Prototype interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())

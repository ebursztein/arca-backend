#!/usr/bin/env python3
"""
End-to-End Prototype for Arca Backend V1

Demonstrates complete user journey using the REAL Cloud Functions via Firebase emulator:
1. User onboarding with birth date (create_user_profile)
2. Connection creation with synastry calculation (create_connection)
3. Daily horoscope generation with relationship weather (get_daily_horoscope)
4. Ask the Stars conversational Q&A

This prototype calls actual Cloud Functions through the emulator, ensuring
all data flows (synastry points, vibe scores, etc.) work correctly.

Usage:
    python prototype.py

Requirements:
    - Firebase emulator running on localhost:5001
    - GEMINI_API_KEY environment variable
    - POSTHOG_API_KEY environment variable (optional)
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

# Note: Most astro/models imports removed - prototype now uses Cloud Functions via emulator

console = Console()

# ---------------------------------------------------------------------------
# Firebase Emulator HTTP Client (same as e2e tests)
# ---------------------------------------------------------------------------

EMULATOR_BASE_URL = "http://localhost:5001/arca-baf77/us-central1"


def call_function(function_name: str, data: dict) -> dict:
    """
    Call a Cloud Function via the Firebase emulator.

    Args:
        function_name: Name of the function (e.g., 'create_user_profile')
        data: Request data to send

    Returns:
        The 'result' field from the response

    Raises:
        Exception if the function returns an error or emulator is not running
    """
    url = f"{EMULATOR_BASE_URL}/{function_name}"
    console.print(f"[dim]POST {url}[/dim]")

    try:
        response = requests.post(
            url,
            json={"data": data},
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Firebase emulator not running. Start it with: firebase emulators:start"
        )

    result = response.json()

    if "error" in result:
        error = result["error"]
        raise Exception(f"{error.get('status', 'ERROR')}: {error.get('message', 'Unknown error')}")

    return result.get("result", result)


def print_section(title: str, content: str = "", style: str = "bold cyan"):
    """Print a formatted section with rich styling."""
    console.print(f"\n[{style}]{'=' * 70}[/{style}]")
    console.print(f"[{style}]{title}[/{style}]")
    if content:
        console.print(f"[{style}]{'=' * 70}[/{style}]")
        console.print(content)
    console.print(f"[{style}]{'=' * 70}[/{style}]\n")


def main(skip_setup: bool = False):
    """
    Run the end-to-end prototype simulation using Firebase emulator.

    Args:
        skip_setup: If True, skip user profile and connection creation (faster)
    """

    print_section("ARCA BACKEND V1 PROTOTYPE (via Emulator)", style="bold magenta")

    # Use a dev account user ID (bypasses auth in emulator)
    # Must be one of: test_user_a, test_user_b, test_user_c, test_user_d, test_user_e
    user_id = "test_user_a"
    user_name = "Elie"
    birth_date = "1987-06-02"

    if not skip_setup:
        # ========================================================================
        # 1. USER ONBOARDING (via Cloud Function)
        # ========================================================================
        print_section("1. USER ONBOARDING", style="bold cyan")

        console.print(f"[cyan]Creating user profile via emulator...[/cyan]")
        console.print(f"  User ID: {user_id}")
        console.print(f"  Name: {user_name}")
        console.print(f"  Birth Date: {birth_date}")

        # Call create_user_profile Cloud Function
        user_profile_response = call_function("create_user_profile", {
            "user_id": user_id,
            "name": user_name,
            "email": f"{user_id}@test.com",
            "birth_date": birth_date,
        })

        sun_sign = user_profile_response.get("sun_sign", "unknown")
        console.print(f"[green]User profile created[/green]")
        console.print(f"  Sun Sign: {sun_sign.title()}")
        console.print(f"  Chart computed: {user_profile_response.get('exact_chart', False)}")

        # ========================================================================
        # 2. CREATE CONNECTIONS (via Cloud Function - computes synastry!)
        # ========================================================================
        print_section("2. CREATE CONNECTIONS", style="bold cyan")

        # Define connections to create
        connections_to_create = [
            {
                "name": "John",
                "birth_date": "1992-08-15",
                "birth_time": "14:30",
                "birth_timezone": "America/New_York",
                "birth_lat": 40.7128,
                "birth_lon": -74.0060,
                "relationship_category": "love",
                "relationship_label": "partner",
            },
            {
                "name": "Mom",
                "birth_date": "1965-07-10",
                "birth_time": "12:00",
                "birth_timezone": "UTC",
                "birth_lat": 0.0,
                "birth_lon": 0.0,
                "relationship_category": "family",
                "relationship_label": "mother",
            },
            {
                "name": "Sarah",
                "birth_date": "1995-06-05",
                "birth_time": "12:00",
                "birth_timezone": "UTC",
                "birth_lat": 0.0,
                "birth_lon": 0.0,
                "relationship_category": "friend",
                "relationship_label": "close_friend",
            },
            {
                "name": "Mike",
                "birth_date": "1980-01-12",
                "birth_time": "12:00",
                "birth_timezone": "UTC",
                "birth_lat": 0.0,
                "birth_lon": 0.0,
                "relationship_category": "coworker",
                "relationship_label": "colleague",
            },
        ]

        created_connections = []
        for conn_data in connections_to_create:
            console.print(f"[cyan]Creating connection: {conn_data['name']}...[/cyan]")

            try:
                # Note: create_connection expects data nested under "connection" key
                conn_response = call_function("create_connection", {
                    "user_id": user_id,
                    "connection": conn_data,
                })
                created_connections.append(conn_response)

                # Show synastry points if computed
                synastry_points = conn_response.get("synastry_points", [])
                console.print(f"[green]  {conn_data['name']} created[/green]")
                console.print(f"    Sun Sign: {conn_response.get('sun_sign', 'unknown')}")
                console.print(f"    Synastry Points: {len(synastry_points)} computed")
                if synastry_points:
                    for point in synastry_points[:2]:
                        console.print(f"      - {point.get('label', 'unknown')} at {point.get('degree', 0):.1f} deg")
            except Exception as e:
                console.print(f"[yellow]  Warning: {e}[/yellow]")

        console.print(f"\n[green]Created {len(created_connections)} connections with synastry data[/green]")
    else:
        console.print("[yellow]Skipping setup (--skip-setup flag). Using existing user/connections.[/yellow]")
        sun_sign = "gemini"  # Default for display

    # ========================================================================
    # 3. DAILY HOROSCOPE GENERATION (via Cloud Function - enriches connection data!)
    # ========================================================================
    print_section("3. DAILY HOROSCOPE GENERATION", style="bold cyan")

    today = datetime.now().strftime("%Y-%m-%d")
    console.print(f"[cyan]Date:[/cyan] {today}")
    console.print(f"[cyan]Generating daily horoscope via emulator...[/cyan]")
    console.print(f"  (This computes synastry on-the-fly, calculates vibe_score, etc.)")

    # Call get_daily_horoscope Cloud Function
    # This goes through main.py which does all the enrichment:
    # - Selects featured connection
    # - Computes synastry_points if missing
    # - Calculates vibe_score and active_transits
    # - Passes enriched data to LLM
    horoscope_response = call_function("get_daily_horoscope", {
        "user_id": user_id,
    })

    console.print(f"[green]Daily horoscope generated[/green]")
    console.print(f"  Generation time: {horoscope_response.get('generation_time_ms', 0)}ms")
    console.print(f"  Model: {horoscope_response.get('model_used', 'unknown')}")

    # Save horoscope to JSON for inspection
    with open('debug_daily_horoscope.json', 'w') as f:
        json.dump(horoscope_response, f, indent=2, default=str)
    console.print(f"[dim]  Saved to debug_daily_horoscope.json[/dim]")



    # ========================================================================
    # 4. DISPLAY HOROSCOPE
    # ========================================================================
    print_section("4. YOUR DAILY HOROSCOPE", style="bold magenta")

    # Display date and sign
    console.print(f"[bold cyan]{today} - {sun_sign.title()}[/bold cyan]\n")

    # Daily Theme Headline (shareable wisdom)
    console.print(Panel(
        horoscope_response.get("daily_theme_headline", ""),
        title="[bold magenta]Daily Theme[/bold magenta]",
        border_style="magenta"
    ))

    # Daily Overview
    console.print(Panel(
        horoscope_response.get("daily_overview", ""),
        title="[bold cyan]Today's Energy[/bold cyan]",
        border_style="cyan"
    ))

    # Technical Analysis
    console.print(Panel(
        horoscope_response.get("technical_analysis", ""),
        title="[bold yellow]Technical Analysis[/bold yellow]",
        border_style="yellow"
    ))

    # Astrometers Summary (iOS-optimized structure)
    astrometers = horoscope_response.get("astrometers", {})
    astrometers_summary = f"""Overall Score: {astrometers.get('overall_unified_score', 0):.1f}/100 ({astrometers.get('overall_state', 'unknown')})
Overall Quality: {astrometers.get('overall_quality', 'unknown').upper()}

Top Active Meters: {', '.join(astrometers.get('top_active_meters', [])[:3])}
Top Challenging Meters: {', '.join(astrometers.get('top_challenging_meters', [])[:3])}
Top Flowing Meters: {', '.join(astrometers.get('top_flowing_meters', [])[:3])}

Groups Summary:"""

    for group in astrometers.get("groups", []):
        astrometers_summary += f"\n- {group.get('display_name', 'unknown')}: {group.get('unified_score', 0):.1f}/100 ({group.get('state_label', '')}) - {len(group.get('meters', []))} meters"

    console.print(Panel(
        astrometers_summary,
        title="[bold cyan]Astrometers Analysis[/bold cyan]",
        border_style="cyan"
    ))

    # Actionable Advice
    advice = horoscope_response.get("actionable_advice", {})
    advice_text = f"DO: {advice.get('do', '')}\n\nDON'T: {advice.get('dont', '')}\n\nREFLECT ON: {advice.get('reflect_on', '')}"
    console.print(Panel(
        advice_text,
        title="[bold green]Actionable Guidance[/bold green]",
        border_style="green"
    ))

    # Lunar Cycle Update (now in moon_detail.interpretation)
    moon_detail = horoscope_response.get("moon_detail", {})
    console.print(Panel(
        moon_detail.get("interpretation", ""),
        title="[bold white]Lunar Cycle[/bold white]",
        border_style="white"
    ))

    # Relationship Weather - Overview + Connection Vibe
    rw = horoscope_response.get("relationship_weather")
    if rw:
        rw_text = f"Overview: {rw.get('overview', '')}"
        for cv in rw.get("connection_vibes", []):
            rw_text += f"\n\n{cv.get('name', '')} ({cv.get('relationship_label', '')}): {cv.get('vibe', '')}"
            if cv.get("vibe_score"):
                rw_text += f" [Energy: {cv.get('vibe_score')}/100]"
            if cv.get("key_transit"):
                rw_text += f"\n  Key Transit: {cv.get('key_transit')}"
        console.print(Panel(
            rw_text,
            title="[bold magenta]Relationship Weather[/bold magenta]",
            border_style="magenta"
        ))

    # Look Ahead Preview
    if horoscope_response.get("look_ahead_preview"):
        console.print(Panel(
            horoscope_response.get("look_ahead_preview", ""),
            title="[bold yellow]Coming Soon[/bold yellow]",
            border_style="yellow"
        ))


    # ========================================================================
    # 5. METER DATA VERIFICATION (DEBUG)
    # ========================================================================
    print_section("5. METER DATA VERIFICATION", style="bold yellow")

    console.print("[bold cyan]Daily Horoscope Astrometers Data (iOS-Optimized):[/bold cyan]\n")

    # Overall metrics
    console.print(f"[yellow]Overall Metrics:[/yellow]")
    console.print(f"  - Unified Score: {astrometers.get('overall_unified_score', 0):.1f}/100")
    console.print(f"  - State: {astrometers.get('overall_state', 'unknown')}")
    console.print(f"  - Quality: {astrometers.get('overall_quality', 'unknown').upper()}\n")

    # Top meters
    console.print(f"[yellow]Top Meters:[/yellow]")
    console.print(f"  - Most Active: {', '.join(astrometers.get('top_active_meters', []))}")
    console.print(f"  - Most Challenging: {', '.join(astrometers.get('top_challenging_meters', []))}")
    console.print(f"  - Most Flowing: {', '.join(astrometers.get('top_flowing_meters', []))}\n")

    # All 17 individual meters grouped in 5 groups (new iOS structure)
    console.print(f"\n[yellow]All 17 Meters by Group (iOS Structure):[/yellow]\n")

    for group in astrometers.get("groups", []):
        console.print(f"[cyan]{group.get('display_name', '')} Group ({group.get('quality', '').upper()}):[/cyan]")
        console.print(f"  Group Unified: {group.get('unified_score', 0):.1f}/100 | State: {group.get('state_label', '')}")
        interpretation = group.get('interpretation', '')
        console.print(f"  LLM Interpretation: {interpretation[:100]}...")
        console.print(f"\n  Member Meters:")
        for meter in group.get("meters", []):
            console.print(f"    - {meter.get('display_name', '')}: {meter.get('unified_score', 0):.1f}/100 ({meter.get('unified_quality', '').upper()}) | State: {meter.get('state_label', '')}")
            meter_interp = meter.get('interpretation', '')
            console.print(f"      LLM: {meter_interp[:80]}...")
            console.print(f"      Top Aspects: {len(meter.get('top_aspects', []))} aspects tracked")
        console.print()

    # ========================================================================
    # 6. METER GROUPS - 5 LIFE AREAS (NEW iOS STRUCTURE)
    # ========================================================================
    print_section("6. METER GROUPS (5 LIFE AREAS) - iOS Structure", style="bold cyan")

    # Display the 5 aggregated meter groups from new structure
    group_icons = {
        "mind": "[M]",
        "heart": "[H]",
        "body": "[B]",
        "instincts": "[I]",
        "growth": "[G]"
    }

    console.print("[yellow]Note: Groups are now nested inside astrometers.groups (new iOS-optimized structure)[/yellow]\n")

    for group in astrometers.get("groups", []):
        group_name = group.get("group_name", "")
        icon = group_icons.get(group_name, "[?]")

        # Format the group display
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
    # 7. ASK THE STARS (skipped - requires HTTP endpoint, not Cloud Function)
    # ========================================================================
    print_section("7. ASK THE STARS", style="bold magenta")
    console.print("[yellow]Skipped - Ask the Stars uses HTTP streaming endpoint, not callable function[/yellow]")
    console.print("[dim]To test Ask the Stars, use the e2e tests or call the endpoint directly[/dim]")

    # ========================================================================
    # 8. PERFORMANCE SUMMARY
    # ========================================================================
    print_section("8. PERFORMANCE SUMMARY", style="bold cyan")

    # Show token usage from horoscope response
    from rich.table import Table
    table = Table(title="LLM Token Usage", show_header=True, header_style="bold magenta")
    table.add_column("Stage", style="dim", width=30)
    table.add_column("Model", style="dim", width=20)
    table.add_column("Time (s)", justify="right")
    table.add_column("Prompt Tokens", justify="right")
    table.add_column("Output Tokens", justify="right")
    table.add_column("Total Tokens", justify="right")

    usage = horoscope_response.get("usage", {})
    table.add_row(
        "Daily Horoscope",
        horoscope_response.get("model_used", "unknown"),
        f"{horoscope_response.get('generation_time_ms', 0) / 1000:.2f}",
        str(usage.get("prompt_token_count", 0)),
        str(usage.get("candidates_token_count", 0)),
        str(usage.get("total_token_count", 0)),
    )

    console.print(table)

    print_section("PROTOTYPE COMPLETE", style="bold magenta")


if __name__ == "__main__":
    import sys
    full_setup = "--full" in sys.argv or "-f" in sys.argv

    try:
        main(skip_setup=not full_setup)
    except KeyboardInterrupt:
        console.print("\n[yellow]Prototype interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())

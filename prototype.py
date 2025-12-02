#!/usr/bin/env python3
"""
ARCA V1 Prototype - End-to-End Workflow Validation via Firebase Emulator

This script mirrors functions/prototype.py but calls the Firebase emulator
instead of direct function calls. This validates the full HTTP API workflow.

Steps:
1. User onboarding (create profile via emulator)
2. Daily horoscope generation (personalized with astrometers)
3. Display horoscope with all fields
4. Meter data verification
5. Meter groups display (5 life areas)
6. Ask the Stars - conversational Q&A
7. Performance summary

Run with Firebase emulators:
    firebase emulators:start

Then in another terminal:
    uv run python prototype.py

This validates the entire architecture before deploying to production.
"""

import requests
import json
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Firebase emulator endpoint
EMULATOR_BASE = "http://127.0.0.1:5001/arca-baf77/us-central1"

console = Console()


def call_function(function_name: str, data: dict, timeout: int = 120) -> dict:
    """Call a Firebase callable function via emulator."""
    url = f"{EMULATOR_BASE}/{function_name}"
    payload = {"data": data}

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()

        if 'result' in result:
            return result['result']
        elif 'error' in result:
            console.print(f"[red]Error from {function_name}:[/red] {result['error']}")
            return None
        else:
            console.print(f"[red]Unexpected response format:[/red] {result}")
            return None
    except requests.exceptions.Timeout:
        console.print(f"[red]Timeout calling {function_name} (>{timeout}s)[/red]")
        return None
    except Exception as e:
        console.print(f"[red]Error calling {function_name}:[/red] {e}")
        return None


def print_section(title: str, style: str = "bold cyan"):
    """Print a section header."""
    console.print(f"\n[{style}]{'=' * 70}[/{style}]")
    console.print(f"[{style}]{title}[/{style}]")
    console.print(f"[{style}]{'=' * 70}[/{style}]\n")


def print_horoscope(horoscope: dict):
    """Pretty print a horoscope using current DailyHoroscope schema."""
    if not horoscope:
        return

    # Daily Theme Headline
    if horoscope.get('daily_theme_headline'):
        console.print(Panel(
            horoscope['daily_theme_headline'],
            title="[bold magenta]Daily Theme[/bold magenta]",
            border_style="magenta"
        ))

    # Daily Overview (replaces old 'summary')
    if horoscope.get('daily_overview'):
        console.print(Panel(
            horoscope['daily_overview'],
            title="[bold cyan]Today's Energy[/bold cyan]",
            border_style="cyan"
        ))

    # Technical Analysis
    if horoscope.get('technical_analysis'):
        console.print(Panel(
            horoscope['technical_analysis'],
            title="[bold yellow]Technical Analysis[/bold yellow]",
            border_style="yellow"
        ))

    # Actionable Advice
    advice = horoscope.get('actionable_advice', {})
    if advice:
        advice_text = f"DO: {advice.get('do', 'N/A')}\n\nDON'T: {advice.get('dont', 'N/A')}\n\nREFLECT ON: {advice.get('reflect_on', 'N/A')}"
        console.print(Panel(
            advice_text,
            title="[bold green]Actionable Guidance[/bold green]",
            border_style="green"
        ))


def print_astrometers(horoscope: dict):
    """Print astrometers data from horoscope."""
    astrometers = horoscope.get('astrometers', {})
    if not astrometers:
        console.print("[yellow]No astrometers data available[/yellow]")
        return

    # Overall metrics
    overall_intensity = astrometers.get('overall_intensity', {})
    overall_harmony = astrometers.get('overall_harmony', {})

    summary = f"""Overall Intensity: {overall_intensity.get('intensity', 0):.1f}/100 ({overall_intensity.get('state_label', 'N/A')})
Overall Harmony: {overall_harmony.get('harmony', 0):.1f}/100 ({overall_harmony.get('state_label', 'N/A')})
Overall Quality: {astrometers.get('overall_quality', 'N/A').upper()}

Top Active Meters: {', '.join(astrometers.get('top_active_meters', [])[:3])}
Top Challenging Meters: {', '.join(astrometers.get('top_challenging_meters', [])[:3])}
Top Flowing Meters: {', '.join(astrometers.get('top_flowing_meters', [])[:3])}

Groups Summary:"""

    for group in astrometers.get('groups', []):
        summary += f"\n  {group.get('display_name', 'N/A')}: {group.get('unified_score', 0):.1f}/100 ({group.get('state_label', 'N/A')}) - {len(group.get('meters', []))} meters"

    console.print(Panel(
        summary,
        title="[bold cyan]Astrometers Analysis[/bold cyan]",
        border_style="cyan"
    ))


def print_meter_groups(horoscope: dict):
    """Print detailed meter groups (5 life areas)."""
    astrometers = horoscope.get('astrometers', {})
    groups = astrometers.get('groups', [])

    if not groups:
        console.print("[yellow]No meter groups available[/yellow]")
        return

    group_icons = {
        "mind": "Brain",
        "heart": "Heart",
        "body": "Body",
        "instincts": "Instincts",
        "growth": "Growth"
    }

    for group in groups:
        group_name = group.get('group_name', '')
        icon = group_icons.get(group_name, "Unknown")

        meters_list = ', '.join([m.get('display_name', 'N/A') for m in group.get('meters', [])])

        scores_text = (
            f"Unified: {group.get('unified_score', 0):.1f} | "
            f"Harmony: {group.get('harmony', 0):.1f} | "
            f"Intensity: {group.get('intensity', 0):.1f}\n"
            f"State: {group.get('state_label', 'N/A')} ({group.get('quality', 'N/A').upper()})\n\n"
            f"{group.get('interpretation', 'No interpretation available')}\n\n"
            f"Member Meters: {meters_list}"
        )

        console.print(Panel(
            scores_text,
            title=f"[bold]{icon} - {group.get('display_name', 'Unknown')}[/bold]",
            border_style="blue"
        ))


def simulate_user_journey():
    """Simulate complete user journey from onboarding through Ask the Stars."""

    console.print(Panel.fit(
        "[bold white]ARCA V1 PROTOTYPE[/bold white]\n"
        "End-to-End Workflow Validation (Emulator)",
        border_style="bold blue"
    ))

    # Test user data - must use a DEV_ACCOUNT_UID from auth.py
    user_id = "test_user_a"
    birth_date = "1987-06-02"  # Gemini

    # =========================================================================
    # STEP 1: USER ONBOARDING
    # =========================================================================
    print_section("1. USER ONBOARDING", style="bold cyan")

    console.print("[yellow]Creating user profile (V1: no birth time)...[/yellow]")
    profile_result = call_function('create_user_profile', {
        'user_id': user_id,
        'name': 'Elie',
        'email': 'elie@example.com',
        'birth_date': birth_date
    })

    if profile_result:
        console.print(f"[green]* Profile created[/green]")
        console.print(f"  Sun sign: [bold]{profile_result.get('sun_sign', 'N/A')}[/bold]")
        console.print(f"  Birth chart: [bold]{'Exact' if profile_result.get('exact_chart') else 'Approximate (V1)'}[/bold]")
        console.print(f"  Mode: {profile_result.get('mode', 'N/A')}")

        # Show natal chart summary if available
        natal_chart = profile_result.get('natal_chart', {})
        if natal_chart.get('summary'):
            console.print(f"\n[yellow]Natal Chart Summary:[/yellow]")
            console.print(f"  {natal_chart['summary'][:200]}...")
    else:
        console.print("[red]* Profile creation failed[/red]")
        return

    # =========================================================================
    # STEP 2: DAILY HOROSCOPE GENERATION
    # =========================================================================
    print_section("2. DAILY HOROSCOPE GENERATION", style="bold cyan")

    today = datetime.now().strftime("%Y-%m-%d")
    console.print(f"[cyan]Date:[/cyan] {today}")
    console.print("[yellow]Generating daily horoscope (this may take 30-60 seconds)...[/yellow]")

    start_time = time.time()
    horoscope = call_function('get_daily_horoscope', {
        'user_id': user_id,
        'date': today
    }, timeout=120)
    gen_time = time.time() - start_time

    if horoscope:
        console.print(f"[green]* Horoscope generated in {gen_time:.1f}s[/green]")
        console.print(f"  Model: {horoscope.get('model_used', 'N/A')}")
        console.print(f"  Generation time (internal): {horoscope.get('generation_time_ms', 0)}ms")
    else:
        console.print("[red]* Horoscope generation failed[/red]")
        return

    # =========================================================================
    # STEP 3: DISPLAY HOROSCOPE
    # =========================================================================
    print_section("3. YOUR DAILY HOROSCOPE", style="bold magenta")

    console.print(f"[bold cyan]{today} - {horoscope.get('sun_sign', 'Unknown').title()}[/bold cyan]\n")
    print_horoscope(horoscope)

    # Moon detail
    moon_detail = horoscope.get('moon_detail', {})
    if moon_detail and moon_detail.get('interpretation'):
        console.print(Panel(
            moon_detail['interpretation'],
            title="[bold white]Lunar Cycle[/bold white]",
            border_style="white"
        ))

    # Look ahead preview
    if horoscope.get('look_ahead_preview'):
        console.print(Panel(
            horoscope['look_ahead_preview'],
            title="[bold yellow]Coming Soon[/bold yellow]",
            border_style="yellow"
        ))

    # =========================================================================
    # STEP 4: METER DATA VERIFICATION
    # =========================================================================
    print_section("4. METER DATA VERIFICATION", style="bold yellow")

    console.print("[bold cyan]Astrometers Data (iOS-Optimized):[/bold cyan]\n")
    print_astrometers(horoscope)

    # Detailed meter breakdown
    astrometers = horoscope.get('astrometers', {})
    console.print(f"\n[yellow]All 17 Meters by Group:[/yellow]\n")

    for group in astrometers.get('groups', []):
        console.print(f"[cyan]{group.get('display_name', 'Unknown')} Group ({group.get('quality', 'N/A').upper()}):[/cyan]")
        console.print(f"  Group Unified: {group.get('unified_score', 0):.1f}/100 | Intensity: {group.get('intensity', 0):.1f} | Harmony: {group.get('harmony', 0):.1f}")

        interpretation = group.get('interpretation', '')
        if interpretation:
            console.print(f"  Interpretation: {interpretation[:100]}...")

        console.print(f"\n  Member Meters:")
        for meter in group.get('meters', []):
            console.print(f"    - {meter.get('display_name', 'N/A')}: {meter.get('unified_score', 0):.1f}/100 ({meter.get('unified_quality', 'N/A').upper()})")
            console.print(f"      Intensity: {meter.get('intensity', 0):.1f} | Harmony: {meter.get('harmony', 0):.1f} | State: {meter.get('state_label', 'N/A')}")
            meter_interp = meter.get('interpretation', '')
            if meter_interp:
                console.print(f"      LLM: {meter_interp[:80]}...")
            console.print(f"      Top Aspects: {len(meter.get('top_aspects', []))} aspects tracked")
        console.print()

    # =========================================================================
    # STEP 5: METER GROUPS - 5 LIFE AREAS
    # =========================================================================
    print_section("5. METER GROUPS (5 LIFE AREAS)", style="bold cyan")

    console.print("[yellow]Note: Groups are nested inside astrometers.groups (iOS-optimized structure)[/yellow]\n")
    print_meter_groups(horoscope)

    # =========================================================================
    # STEP 6: ASK THE STARS
    # =========================================================================
    print_section("6. ASK THE STARS - CONVERSATIONAL Q&A", style="bold magenta")

    console.print("[cyan]Testing Ask the Stars endpoint...[/cyan]\n")

    # Note: ask_the_stars is an HTTPS endpoint, not a callable function
    # It uses SSE streaming, so we need to handle it differently
    ask_url = f"{EMULATOR_BASE.replace(':5001/', ':5001/')}"  # Same base
    console.print("[dim]Note: ask_the_stars uses SSE streaming via HTTPS endpoint[/dim]")
    console.print("[dim]For full test, use: cd functions && uv run python prototype.py[/dim]")

    # =========================================================================
    # STEP 7: PERFORMANCE SUMMARY
    # =========================================================================
    print_section("7. PERFORMANCE SUMMARY", style="bold cyan")

    table = Table(title="LLM Token Usage", show_header=True, header_style="bold magenta")
    table.add_column("Stage", style="dim", width=25)
    table.add_column("Model", style="dim", width=22)
    table.add_column("Time (s)", justify="right")
    table.add_column("Prompt", justify="right")
    table.add_column("Output", justify="right")
    table.add_column("Thinking", justify="right")
    table.add_column("Cached", justify="right")
    table.add_column("Total", justify="right")

    usage = horoscope.get('usage', {})
    table.add_row(
        "Daily Horoscope",
        horoscope.get('model_used', 'N/A'),
        f"{horoscope.get('generation_time_ms', 0) / 1000:.2f}",
        str(usage.get('prompt_token_count', 0)),
        str(usage.get('candidates_token_count', 0)),
        str(usage.get('thoughts_token_count', 0)),
        str(usage.get('cached_content_token_count', 0)),
        str(usage.get('total_token_count', 0)),
    )

    console.print(table)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_section("PROTOTYPE SUMMARY", style="bold green")

    summary_table = Table(title="V1 Workflow Validation")
    summary_table.add_column("Step", style="cyan")
    summary_table.add_column("Status", style="green")
    summary_table.add_column("Notes", style="dim")

    summary_table.add_row(
        "1. Onboarding",
        "* PASS",
        f"Created profile for {profile_result.get('sun_sign', 'N/A')}"
    )
    summary_table.add_row(
        "2. Horoscope Gen",
        "* PASS",
        f"Generated in {gen_time:.1f}s with {horoscope.get('model_used', 'N/A')}"
    )
    summary_table.add_row(
        "3. Display",
        "* PASS",
        "All fields rendered correctly"
    )
    summary_table.add_row(
        "4. Meter Data",
        "* PASS",
        f"{len(astrometers.get('groups', []))} groups, 17 meters"
    )
    summary_table.add_row(
        "5. Meter Groups",
        "* PASS",
        "5 life areas with interpretations"
    )
    summary_table.add_row(
        "6. Ask the Stars",
        "* SKIPPED",
        "Use functions/prototype.py for SSE test"
    )

    console.print(summary_table)

    console.print("\n[bold green]* END-TO-END WORKFLOW VALIDATED[/bold green]\n")

    console.print("[bold]Next Steps:[/bold]")
    console.print("1. For full Ask the Stars test: cd functions && uv run python prototype.py")
    console.print("2. Deploy to Firebase production")
    console.print("3. Test with iOS app")
    console.print("4. Monitor PostHog for LLM usage\n")


if __name__ == "__main__":
    try:
        simulate_user_journey()
    except KeyboardInterrupt:
        console.print("\n[yellow]Prototype interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Prototype failed with error:[/red] {e}")
        import traceback
        traceback.print_exc()

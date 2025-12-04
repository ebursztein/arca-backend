#!/usr/bin/env python3
"""
Visualize Daily Horoscope Structure

Shows the complete structure returned by generate_daily_horoscope()

Usage:
    python visualize_dailyhoroscope.py
"""

from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from models import DailyHoroscope, UserProfile, create_empty_memory
from astro import (
    get_sun_sign,
    get_sun_sign_profile,
    compute_birth_chart,
    format_transit_summary_for_ui,
)
from llm import generate_daily_horoscope

console = Console()


def visualize_daily_horoscope(daily_horoscope: DailyHoroscope, sun_sign: str, date: str) -> None:
    """Visualize the complete structure of a DailyHoroscope object."""

    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]")
    console.print("[bold cyan]DAILY HOROSCOPE STRUCTURE[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 70}[/bold cyan]\n")

    # Display date and sign
    console.print(f"[bold cyan]{date} - {sun_sign.title()}[/bold cyan]\n")

    # Daily Theme Headline
    console.print(Panel(
        daily_horoscope.daily_theme_headline,
        title="[bold magenta]daily_theme_headline[/bold magenta]",
        border_style="magenta"
    ))

    # Daily Overview
    console.print(Panel(
        daily_horoscope.daily_overview,
        title="[bold cyan]daily_overview[/bold cyan]",
        border_style="cyan"
    ))

    # Technical Analysis
    console.print(Panel(
        daily_horoscope.technical_analysis,
        title="[bold yellow]technical_analysis[/bold yellow]",
        border_style="yellow"
    ))

    # Astrometers Summary (v2 structure)
    astrometers = daily_horoscope.astrometers
    astrometers_summary = f"""overall_unified_score: {astrometers.overall_unified_score:.1f} (-100 to +100)
overall_intensity: {astrometers.overall_intensity.intensity:.1f}/100 ({astrometers.overall_intensity.state_label})
overall_harmony: {astrometers.overall_harmony.harmony:.1f}/100 ({astrometers.overall_harmony.state_label})
overall_quality: {astrometers.overall_quality.upper()}
overall_state: {astrometers.overall_state}

Top Active Meters: {', '.join(astrometers.top_active_meters[:3])}
Top Challenging: {', '.join(astrometers.top_challenging_meters[:3])}
Top Flowing: {', '.join(astrometers.top_flowing_meters[:3])}"""

    console.print(Panel(
        astrometers_summary,
        title="[bold cyan]astrometers[/bold cyan]",
        border_style="cyan"
    ))

    # Actionable Advice
    advice_text = f"do: {daily_horoscope.actionable_advice.do}\n\ndont: {daily_horoscope.actionable_advice.dont}\n\nreflect_on: {daily_horoscope.actionable_advice.reflect_on}"
    console.print(Panel(
        advice_text,
        title="[bold green]actionable_advice[/bold green]",
        border_style="green"
    ))

    # ========================================================================
    # DETAILED METER DATA (v2 hierarchical structure)
    # ========================================================================
    console.print(f"\n[bold yellow]{'=' * 70}[/bold yellow]")
    console.print("[bold yellow]ASTROMETERS DETAILED BREAKDOWN (v2)[/bold yellow]")
    console.print(f"[bold yellow]{'=' * 70}[/bold yellow]\n")

    # Overall metrics
    console.print("[yellow]Overall Metrics:[/yellow]")
    console.print(f"  - overall_unified_score: {astrometers.overall_unified_score:.1f} (-100 to +100)")
    console.print(f"  - overall_intensity: {astrometers.overall_intensity.intensity:.1f}/100 ({astrometers.overall_intensity.state_label})")
    console.print(f"  - overall_harmony: {astrometers.overall_harmony.harmony:.1f}/100 ({astrometers.overall_harmony.state_label})")
    console.print(f"  - overall_quality: {astrometers.overall_quality.upper()}")
    console.print(f"  - overall_state: {astrometers.overall_state}\n")

    # 5 Meter Groups with nested meters
    console.print("[yellow]5 Meter Groups (17 meters total):[/yellow]\n")

    for group in astrometers.groups:
        console.print(f"[cyan]{group.display_name} ({group.group_name}):[/cyan]")
        console.print(f"  Group unified_score: {group.unified_score:.1f} | intensity: {group.intensity:.1f} | harmony: {group.harmony:.1f}")
        console.print(f"  Quality: {group.quality.upper()} | State: {group.state_label}")
        if group.interpretation:
            console.print(f"  Interpretation: {group.interpretation[:100]}...")

        # Show individual meters in this group
        console.print("  Meters:")
        for meter in group.meters:
            console.print(f"    - {meter.name}: unified={meter.unified_score:.1f}, intensity={meter.intensity:.1f}, harmony={meter.harmony:.1f}")
            console.print(f"      {meter.quality.upper()} | {meter.state_label}")
        console.print()

    # Top insights
    console.print("[yellow]Top Insights:[/yellow]")
    console.print(f"  Top Active: {', '.join(astrometers.top_active_meters)}")
    console.print(f"  Top Challenging: {', '.join(astrometers.top_challenging_meters)}")
    console.print(f"  Top Flowing: {', '.join(astrometers.top_flowing_meters)}")

    # Metadata
    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]")
    console.print("[bold cyan]METADATA[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 70}[/bold cyan]\n")

    console.print(f"[cyan]model_used:[/cyan] {daily_horoscope.model_used}")
    console.print(f"[cyan]generation_time_ms:[/cyan] {daily_horoscope.generation_time_ms}")
    console.print("[cyan]usage:[/cyan]")
    console.print(f"  - prompt_token_count: {daily_horoscope.usage.get('prompt_token_count', 0)}")
    console.print(f"  - candidates_token_count: {daily_horoscope.usage.get('candidates_token_count', 0)}")
    console.print(f"  - thoughts_token_count: {daily_horoscope.usage.get('thoughts_token_count', 0)}")
    console.print(f"  - cached_content_token_count: {daily_horoscope.usage.get('cached_content_token_count', 0)}")
    console.print(f"  - total_token_count: {daily_horoscope.usage.get('total_token_count', 0)}")

    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]\n")


def main() -> None:
    """Generate a sample daily horoscope and visualize its structure."""
    console.print("\n[bold magenta]Generating sample daily horoscope...[/bold magenta]\n")

    # Sample user data
    birth_date = "1990-02-13"
    today = datetime.now().strftime("%Y-%m-%d")

    # Calculate sun sign
    sun_sign = get_sun_sign(birth_date)
    console.print(f"[cyan]Sun Sign:[/cyan] {sun_sign.value.title()}")

    # Load sun sign profile
    sun_sign_profile = get_sun_sign_profile(sun_sign)

    # Compute birth chart
    console.print("[cyan]Computing birth chart...[/cyan]")
    natal_chart, is_exact = compute_birth_chart(birth_date)

    # Create user profile (v2 with trial fields)
    user_profile = UserProfile(
        user_id="test_user_001",
        name="Jane",
        email="test@example.com",
        birth_date=birth_date,
        birth_time=None,
        birth_timezone=None,
        birth_lat=None,
        birth_lon=None,
        sun_sign=sun_sign.value,
        natal_chart=natal_chart,
        exact_chart=is_exact,
        is_premium=False,
        premium_expiry=None,
        is_trial_active=False,
        trial_end_date=None,
        photo_path=None,
        created_at=datetime.now().isoformat(),
        last_active=datetime.now().isoformat()
    )

    # Get transit data using new API
    console.print("[cyan]Computing transits...[/cyan]")
    transit_chart, _ = compute_birth_chart(today, birth_time="12:00")
    transit_summary = format_transit_summary_for_ui(natal_chart, transit_chart)

    # Create empty memory
    memory = create_empty_memory("test_user_001")

    # Generate daily horoscope
    console.print("[cyan]Generating daily horoscope...[/cyan]\n")
    daily_horoscope = generate_daily_horoscope(
        date=today,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_summary=transit_summary,
        memory=memory,
        featured_connection=None,
        model_name="gemini-2.5-flash-lite"
    )

    # Visualize the structure
    visualize_daily_horoscope(daily_horoscope, sun_sign.value, today)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())

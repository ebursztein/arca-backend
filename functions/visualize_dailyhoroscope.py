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
    summarize_transits_with_natal,
)
from llm import generate_daily_horoscope

console = Console()


def visualize_daily_horoscope(daily_horoscope: DailyHoroscope, sun_sign: str, date: str):
    """Visualize the complete structure of a DailyHoroscope object."""

    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]")
    console.print(f"[bold cyan]DAILY HOROSCOPE STRUCTURE[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 70}[/bold cyan]\n")

    # Display date and sign
    console.print(f"[bold cyan]{date} • {sun_sign.title()}[/bold cyan]\n")

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

    # Summary
    console.print(Panel(
        daily_horoscope.summary,
        title="[bold cyan]summary[/bold cyan]",
        border_style="cyan"
    ))

    # Astrometers Summary
    astrometers_summary = f"""overall_intensity: {daily_horoscope.astrometers.overall_intensity.intensity:.1f}/100 ({daily_horoscope.astrometers.overall_intensity.state_label})
overall_harmony: {daily_horoscope.astrometers.overall_harmony.harmony:.1f}/100 ({daily_horoscope.astrometers.overall_harmony.state_label})
overall_unified_quality: {daily_horoscope.astrometers.overall_unified_quality.value.upper()}
aspect_count: {daily_horoscope.astrometers.aspect_count}

key_aspects (top 3):"""

    for key_aspect in daily_horoscope.astrometers.key_aspects[:3]:
        astrometers_summary += f"\n  • {key_aspect.description}"

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

    # Lunar Cycle Update
    console.print(Panel(
        daily_horoscope.lunar_cycle_update,
        title="[bold white]lunar_cycle_update[/bold white]",
        border_style="white"
    ))

    # ========================================================================
    # DETAILED METER DATA
    # ========================================================================
    console.print(f"\n[bold yellow]{'=' * 70}[/bold yellow]")
    console.print(f"[bold yellow]ASTROMETERS DETAILED BREAKDOWN[/bold yellow]")
    console.print(f"[bold yellow]{'=' * 70}[/bold yellow]\n")

    # Overall metrics
    console.print(f"[yellow]Overall Metrics:[/yellow]")
    console.print(f"  • overall_intensity: {daily_horoscope.astrometers.overall_intensity.intensity:.1f}/100 ({daily_horoscope.astrometers.overall_intensity.state_label})")
    console.print(f"  • overall_harmony: {daily_horoscope.astrometers.overall_harmony.harmony:.1f}/100 ({daily_horoscope.astrometers.overall_harmony.state_label})")
    console.print(f"  • overall_unified_quality: {daily_horoscope.astrometers.overall_unified_quality.value.upper()}")
    console.print(f"  • aspect_count: {daily_horoscope.astrometers.aspect_count}\n")

    # All key aspects
    console.print(f"[yellow]key_aspects ({len(daily_horoscope.astrometers.key_aspects)} total):[/yellow]")
    for i, key_aspect in enumerate(daily_horoscope.astrometers.key_aspects, 1):
        console.print(f"  {i}. {key_aspect.description}")
        console.print(f"     Affects {key_aspect.meter_count} meters: {', '.join(key_aspect.affected_meters)}")
        console.print(f"     DTI: {key_aspect.aspect.dti_contribution:.1f} | HQS: {key_aspect.aspect.hqs_contribution:.1f}")

    # All 23 individual meters grouped by domain
    console.print(f"\n[yellow]All 23 Individual Meters by Domain:[/yellow]\n")

    meters_by_domain = {
        "Global Meters": [
            ("overall_intensity", daily_horoscope.astrometers.overall_intensity),
            ("overall_harmony", daily_horoscope.astrometers.overall_harmony)
        ],
        "Emotional Meters": [
            ("emotional_intensity", daily_horoscope.astrometers.emotional_intensity),
            ("relationship_harmony", daily_horoscope.astrometers.relationship_harmony),
            ("emotional_resilience", daily_horoscope.astrometers.emotional_resilience)
        ],
        "Cognitive Meters": [
            ("mental_clarity", daily_horoscope.astrometers.mental_clarity),
            ("decision_quality", daily_horoscope.astrometers.decision_quality),
            ("communication_flow", daily_horoscope.astrometers.communication_flow)
        ],
        "Physical/Action Meters": [
            ("physical_energy", daily_horoscope.astrometers.physical_energy),
            ("conflict_risk", daily_horoscope.astrometers.conflict_risk),
            ("motivation_drive", daily_horoscope.astrometers.motivation_drive)
        ],
        "Life Domain Meters": [
            ("career_ambition", daily_horoscope.astrometers.career_ambition),
            ("opportunity_window", daily_horoscope.astrometers.opportunity_window),
            ("challenge_intensity", daily_horoscope.astrometers.challenge_intensity),
            ("transformation_pressure", daily_horoscope.astrometers.transformation_pressure)
        ],
        "Specialized Meters": [
            ("intuition_spirituality", daily_horoscope.astrometers.intuition_spirituality),
            ("innovation_breakthrough", daily_horoscope.astrometers.innovation_breakthrough),
            ("karmic_lessons", daily_horoscope.astrometers.karmic_lessons),
            ("social_collective", daily_horoscope.astrometers.social_collective)
        ],
        "Element Meters": [
            ("fire_energy", daily_horoscope.astrometers.fire_energy),
            ("earth_energy", daily_horoscope.astrometers.earth_energy),
            ("air_energy", daily_horoscope.astrometers.air_energy),
            ("water_energy", daily_horoscope.astrometers.water_energy)
        ]
    }

    for domain, meters in meters_by_domain.items():
        console.print(f"[cyan]{domain}:[/cyan]")
        for meter_name, meter_reading in meters:
            console.print(f"  • {meter_name}: {meter_reading.unified_score:.1f}/100 ({meter_reading.unified_quality.value.upper()})")
            console.print(f"    intensity: {meter_reading.intensity:.1f} | harmony: {meter_reading.harmony:.1f} | state: {meter_reading.state_label}")
        console.print()

    # Metadata
    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]")
    console.print(f"[bold cyan]METADATA[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 70}[/bold cyan]\n")

    console.print(f"[cyan]model_used:[/cyan] {daily_horoscope.model_used}")
    console.print(f"[cyan]generation_time_ms:[/cyan] {daily_horoscope.generation_time_ms}")
    console.print(f"[cyan]usage:[/cyan]")
    console.print(f"  • prompt_token_count: {daily_horoscope.usage.get('prompt_token_count', 0)}")
    console.print(f"  • candidates_token_count: {daily_horoscope.usage.get('candidates_token_count', 0)}")
    console.print(f"  • thoughts_token_count: {daily_horoscope.usage.get('thoughts_token_count', 0)}")
    console.print(f"  • cached_content_token_count: {daily_horoscope.usage.get('cached_content_token_count', 0)}")
    console.print(f"  • total_token_count: {daily_horoscope.usage.get('total_token_count', 0)}")

    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]\n")

    console.print(daily_horoscope)

def main():
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
    console.print(f"[cyan]Computing birth chart...[/cyan]")
    natal_chart, is_exact = compute_birth_chart(birth_date)

    # Create user profile
    user_profile = UserProfile(
        user_id="test_user_001",
        name="Test User",
        email="test@example.com",
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

    # Get transit data
    console.print(f"[cyan]Computing transits...[/cyan]")
    transit_chart, _ = compute_birth_chart(today, birth_time="12:00")
    transit_data = summarize_transits_with_natal(natal_chart, transit_chart)

    # Create empty memory
    memory = create_empty_memory("test_user_001")

    # Generate daily horoscope
    console.print(f"[cyan]Generating daily horoscope...[/cyan]\n")
    daily_horoscope = generate_daily_horoscope(
        date=today,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_data=transit_data,
        memory=memory,
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

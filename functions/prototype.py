#!/usr/bin/env python3
"""
End-to-End Prototype for Arca Backend V1

Demonstrates complete user journey:
1. User onboarding with birth date
2. Sun sign calculation and profile loading
3. Daily transit data generation
4. LLM-powered horoscope generation with memory/personalization
5. Journal entry creation and memory updates

This prototype validates the entire V1 workflow before Firebase integration.

Usage:
    python prototype.py

Requirements:
    - GEMINI_API_KEY environment variable
    - POSTHOG_API_KEY environment variable (optional)
"""

from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

# Import our astrology module
from astro import (
    get_sun_sign,
    get_sun_sign_profile,
    compute_birth_chart,
    format_transit_summary_for_ui,
    find_natal_transit_aspects,
    calculate_lunar_phase,
    ZodiacSign,
    SunSignProfile,
    NatalChartData,
)

# Import our LLM modules
from llm import generate_daily_horoscope

# Import our Pydantic models
from models import (
    UserProfile,
    MemoryCollection,
    CategoryEngagement,
    CategoryViewed,
    JournalEntry,
    EntryType,
    DailyHoroscope,
    create_empty_memory,
    update_memory_from_journal,
)
from astrometers.hierarchy import MeterGroupV2

console = Console()


def print_section(title: str, content: str = "", style: str = "bold cyan"):
    """Print a formatted section with rich styling."""
    console.print(f"\n[{style}]{'=' * 70}[/{style}]")
    console.print(f"[{style}]{title}[/{style}]")
    if content:
        console.print(f"[{style}]{'=' * 70}[/{style}]")
        console.print(content)
    console.print(f"[{style}]{'=' * 70}[/{style}]\n")


# Memory formatting is now handled by MemoryCollection.format_for_llm() method


def simulate_journal_entry_and_memory_update(
    user_id: str,
    date: str,
    summary: str,
    categories_viewed: list[dict],
    memory_data: dict
) -> tuple[str, dict]:
    """
    Simulate journal entry creation and memory update.

    In production, this would be:
    1. add_journal_entry() callable function writes to Firestore
    2. Firestore trigger automatically updates memory collection

    Args:
        user_id: User ID
        date: Reading date
        summary: Summary text
        categories_viewed: List of {category, text} dicts
        memory_data: Current memory data (will be updated)

    Returns:
        (entry_id, updated_memory_data)
    """
    # Generate entry ID
    entry_id = f"entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Update memory - category counts
    for cat_view in categories_viewed:
        cat_name = cat_view["category"]
        if cat_name not in memory_data["categories"]:
            memory_data["categories"][cat_name] = {"count": 0, "last_mentioned": None}

        memory_data["categories"][cat_name]["count"] += 1
        memory_data["categories"][cat_name]["last_mentioned"] = date

    # Update memory - recent readings (FIFO, max 10)
    reading = {
        "date": date,
        "summary": summary,
        "categories_viewed": categories_viewed
    }

    memory_data["recent_readings"].append(reading)

    # Keep only last 10 readings
    if len(memory_data["recent_readings"]) > 10:
        memory_data["recent_readings"] = memory_data["recent_readings"][-10:]

    memory_data["updated_at"] = datetime.now().isoformat()

    return entry_id, memory_data


def main():
    """Run the end-to-end prototype simulation."""
    model_name = "gemini-2.5-flash-lite"


    print_section("🌟 ARCA BACKEND V1 PROTOTYPE 🌟", style="bold magenta")




    # ========================================================================
    # 1. USER ONBOARDING
    # ========================================================================
    print_section("1️⃣  USER ONBOARDING", style="bold cyan")

    # Simulated user
    user = {
        "id": "test_user_001",
        "name": "Elie",
        "email": "elie@example.com"
    }

    console.print(f"[green]✓ User authenticated: {user['name']} ({user['email']})[/green]")

    # Birth information
    birth_date = "1987-06-02"
    console.print(f"\n[cyan]Birth Date:[/cyan] {birth_date}")

    # Calculate sun sign
    sun_sign = get_sun_sign(birth_date)
    console.print(f"[cyan]Sun Sign:[/cyan] {sun_sign.value.title()}")

    # Load sun sign profile
    sun_sign_profile = get_sun_sign_profile(sun_sign)
    if not sun_sign_profile:
        raise ValueError(f"Sun sign profile not found for {sun_sign.value}")

    if sun_sign_profile:
        console.print("\n[yellow]Sun Sign Profile:[/yellow]")
        console.print(f"  Element: {sun_sign_profile.element.value.title()}")
        console.print(f"  Modality: {sun_sign_profile.modality.value.title()}")
        console.print(f"  Ruling Planet: {sun_sign_profile.ruling_planet}")
        console.print(f"\n  Summary: {sun_sign_profile.summary[:200]}...")

    # Compute birth chart (V1 mode - approximate)
    console.print(f"\n[cyan]Computing birth chart...[/cyan]")
    natal_chart, is_exact = compute_birth_chart(birth_date)
    console.print(f"[green]✓ Birth chart computed (exact: {is_exact})[/green]")
    console.print(f"  Planets: {len(natal_chart['planets'])}")
    console.print(f"  Houses: {len(natal_chart['houses'])}")
    console.print(f"  Aspects: {len(natal_chart['aspects'])}")

    # Create UserProfile Pydantic model
    user_profile = UserProfile(
        user_id=user["id"],
        name=user["name"],
        email=user["email"],
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
    console.print(f"[green]✓ User profile created[/green]")

    # Initialize empty memory for first-time user using Pydantic model
    memory = create_empty_memory(user["id"])

    console.print(f"[green]✓ Memory collection initialized[/green]")

    # ========================================================================
    # 2. DAILY HOROSCOPE GENERATION
    # ========================================================================
    print_section("2️⃣  DAILY HOROSCOPE GENERATION", style="bold cyan")

    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")
    console.print(f"[cyan]Date:[/cyan] {today}")

    # Get transit data for today
    console.print(f"\n[cyan]Computing current transits...[/cyan]")
    transit_chart, _ = compute_birth_chart(
        today,
        birth_time="12:00",  # Use noon for transits
    )
    console.print("[green]✓ Transit chart computed[/green]")

    # Generate enhanced transit summary with NEW system
    console.print("\n[cyan]Analyzing natal-transit aspects with enhanced system...[/cyan]")
    transit_summary = format_transit_summary_for_ui(natal_chart, transit_chart, max_aspects=5)
    console.print("[green]✓ Enhanced transit data generated[/green]")

    # Display priority transits
    if transit_summary["priority_transits"]:
        console.print("\n[yellow]Priority Transits Today:[/yellow]")
        for i, transit in enumerate(transit_summary["priority_transits"][:3], 1):
            console.print(f"  {i}. {transit['intensity_indicator']} {transit['description']}")
            console.print(f"     Priority: {transit['priority_score']} | Orb: {transit['orb']}° ({transit['orb_label']}, {transit['applying_label']})")
            if transit.get('speed_timing'):
                console.print(f"     Timing: {transit['speed_timing']['timing_impact']}")

    # Display lunar phase
    moon = next((p for p in transit_chart["planets"] if p["name"] == "moon"), None)
    sun = next((p for p in transit_chart["planets"] if p["name"] == "sun"), None)
    if moon and sun:
        lunar_phase = calculate_lunar_phase(sun["absolute_degree"], moon["absolute_degree"])
        console.print("\n[yellow]Lunar Phase:[/yellow]")
        console.print(f"  {lunar_phase.phase_name.replace('_', ' ').title()} {lunar_phase.phase_emoji}")
        console.print(f"  Energy: {lunar_phase.energy}")

    # Display theme synthesis
    if transit_summary["theme_synthesis"].get("theme_synthesis"):
        console.print(f"\n[yellow]Transit Theme:[/yellow]")
        console.print(f"  {transit_summary['theme_synthesis']['theme_synthesis'][:150]}...")

    console.print(f"\n[yellow]Total Aspects Found:[/yellow] {transit_summary['total_aspects_found']}")

    # Format memory for LLM using Pydantic model method
    memory_context = memory.format_for_llm()
    console.print(f"\n[yellow]Memory Context:[/yellow]")
    console.print(f"  {memory_context[:200]}...")

    # Generate horoscope with ENHANCED TRANSIT SYSTEM
    console.print(f"\n[cyan]Generating daily horoscope[/cyan]")

    # Generate daily horoscope with new transit summary
    daily_horoscope = generate_daily_horoscope(
        date=today,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_summary=transit_summary,  # NEW: Enhanced transit summary dict
        memory=memory,
        model_name=model_name)
    console.print(f"[green]✓ Daily horoscope generated ({daily_horoscope.generation_time_ms}ms)[/green]")

    # Save horoscope AND transit summary to JSON for inspection
    with open('debug_daily_horoscope.json', 'w') as f:
        f.write(daily_horoscope.model_dump_json(indent=2))

    import json
    with open('debug_transit_summary.json', 'w') as f:
        json.dump(transit_summary, f, indent=2, default=str)



    # ========================================================================
    # 3. DISPLAY HOROSCOPE
    # ========================================================================
    print_section("3️⃣  YOUR DAILY HOROSCOPE", style="bold magenta")

    # Display date and sign
    console.print(f"[bold cyan]{today} • {sun_sign.value.title()}[/bold cyan]\n")

    # Daily Theme Headline (shareable wisdom)
    console.print(Panel(
        daily_horoscope.daily_theme_headline,
        title="[bold magenta]💫 Daily Theme[/bold magenta]",
        border_style="magenta"
    ))

    # Daily Overview
    console.print(Panel(
        daily_horoscope.daily_overview,
        title="[bold cyan]🌊 Today's Energy[/bold cyan]",
        border_style="cyan"
    ))

    # Technical Analysis
    console.print(Panel(
        daily_horoscope.technical_analysis,
        title="[bold yellow]⭐ Technical Analysis[/bold yellow]",
        border_style="yellow"
    ))

    # Astrometers Summary (new iOS-optimized structure)
    astrometers_summary = f"""Overall Intensity: {daily_horoscope.astrometers.overall_intensity.intensity:.1f}/100 ({daily_horoscope.astrometers.overall_intensity.state_label})
Overall Harmony: {daily_horoscope.astrometers.overall_harmony.harmony:.1f}/100 ({daily_horoscope.astrometers.overall_harmony.state_label})
Overall Quality: {daily_horoscope.astrometers.overall_quality.upper()}

Top Active Meters: {', '.join(daily_horoscope.astrometers.top_active_meters[:3])}
Top Challenging Meters: {', '.join(daily_horoscope.astrometers.top_challenging_meters[:3])}
Top Flowing Meters: {', '.join(daily_horoscope.astrometers.top_flowing_meters[:3])}

Groups Summary:"""

    for group in daily_horoscope.astrometers.groups:
        astrometers_summary += f"\n• {group.display_name}: {group.unified_score:.1f}/100 ({group.state_label}) - {len(group.meters)} meters"

    console.print(Panel(
        astrometers_summary,
        title="[bold cyan]📊 Astrometers Analysis[/bold cyan]",
        border_style="cyan"
    ))

    # Actionable Advice
    advice_text = f"✨ DO: {daily_horoscope.actionable_advice.do}\n\n🚫 DON'T: {daily_horoscope.actionable_advice.dont}\n\n🔮 REFLECT ON: {daily_horoscope.actionable_advice.reflect_on}"
    console.print(Panel(
        advice_text,
        title="[bold green]💡 Actionable Guidance[/bold green]",
        border_style="green"
    ))

    # Lunar Cycle Update (now in moon_detail.interpretation)
    console.print(Panel(
        daily_horoscope.moon_detail.interpretation,
        title="[bold white]🌙 Lunar Cycle[/bold white]",
        border_style="white"
    ))

    # General Transits Overview - DEPRECATED (was redundant with technical_analysis)
    # transits_text = "\n".join(f"• {item}" for item in detailed_horoscope.general_transits_overview)
    # console.print(Panel(
    #     transits_text,
    #     title="[bold cyan]🌌 Collective Transits[/bold cyan]",
    #     border_style="cyan"
    # ))

    # Look Ahead Preview - NOW IN DAILY HOROSCOPE
    if daily_horoscope.look_ahead_preview:
        console.print(Panel(
            daily_horoscope.look_ahead_preview,
            title="[bold yellow]🔭 Coming Soon[/bold yellow]",
            border_style="yellow"
        ))


    # ========================================================================
    # 4. METER DATA VERIFICATION (DEBUG)
    # ========================================================================
    print_section("4️⃣  METER DATA VERIFICATION", style="bold yellow")

    console.print("[bold cyan]📊 Daily Horoscope Astrometers Data (iOS-Optimized):[/bold cyan]\n")

    # Overall metrics
    console.print(f"[yellow]Overall Metrics:[/yellow]")
    console.print(f"  • Intensity: {daily_horoscope.astrometers.overall_intensity.intensity:.1f}/100 ({daily_horoscope.astrometers.overall_intensity.state_label})")
    console.print(f"  • Harmony: {daily_horoscope.astrometers.overall_harmony.harmony:.1f}/100 ({daily_horoscope.astrometers.overall_harmony.state_label})")
    console.print(f"  • Quality: {daily_horoscope.astrometers.overall_quality.upper()}\n")

    # Top meters
    console.print(f"[yellow]Top Meters:[/yellow]")
    console.print(f"  • Most Active: {', '.join(daily_horoscope.astrometers.top_active_meters)}")
    console.print(f"  • Most Challenging: {', '.join(daily_horoscope.astrometers.top_challenging_meters)}")
    console.print(f"  • Most Flowing: {', '.join(daily_horoscope.astrometers.top_flowing_meters)}\n")

    # All 17 individual meters grouped in 5 groups (new iOS structure)
    console.print(f"\n[yellow]All 17 Meters by Group (iOS Structure):[/yellow]\n")

    for group in daily_horoscope.astrometers.groups:
        console.print(f"[cyan]{group.display_name} Group ({group.quality.upper()}):[/cyan]")
        console.print(f"  Group Unified: {group.unified_score:.1f}/100 | Intensity: {group.intensity:.1f} | Harmony: {group.harmony:.1f}")
        console.print(f"  LLM Interpretation: {group.interpretation[:100]}...")
        console.print(f"\n  Member Meters:")
        for meter in group.meters:
            console.print(f"    • {meter.display_name}: {meter.unified_score:.1f}/100 ({meter.unified_quality.upper()})")
            console.print(f"      Intensity: {meter.intensity:.1f} | Harmony: {meter.harmony:.1f} | State: {meter.state_label}")
            console.print(f"      LLM: {meter.interpretation[:80]}...")
            console.print(f"      Top Aspects: {len(meter.top_aspects)} aspects tracked")
        console.print()

    # ========================================================================
    # 5. METER GROUPS - 5 LIFE AREAS (NEW iOS STRUCTURE)
    # ========================================================================
    print_section("5️⃣  METER GROUPS (5 LIFE AREAS) - iOS Structure", style="bold cyan")

    # Display the 5 aggregated meter groups from new structure
    group_icons = {
        "mind": "🧠",
        "emotions": "💕",
        "body": "💪",
        "spirit": "✨",
        "growth": "🌱"
    }

    console.print("[yellow]Note: Groups are now nested inside astrometers.groups (new iOS-optimized structure)[/yellow]\n")

    for group in daily_horoscope.astrometers.groups:
        group_name = group.group_name
        icon = group_icons.get(group_name, "🔮")

        # Format the group display
        scores_text = (
            f"Unified: {group.unified_score:.1f} | "
            f"Harmony: {group.harmony:.1f} | "
            f"Intensity: {group.intensity:.1f}\n"
            f"State: {group.state_label} ({group.quality.upper()})\n\n"
            f"{group.interpretation}\n\n"
            f"Member Meters: {', '.join([m.display_name for m in group.meters])}"
        )

        console.print(Panel(
            scores_text,
            title=f"[bold]{icon} {group.display_name}[/bold]",
            border_style="blue"
        ))

    # ========================================================================
    # 6. JOURNAL ENTRY & MEMORY UPDATE
    # ========================================================================
    # SKIPPED - Old 9-group system incompatible with new 5-group meter_groups
    # print_section("6️⃣  JOURNAL ENTRY & MEMORY UPDATE", style="bold cyan")

    # console.print("[cyan]Creating journal entry...[/cyan]")

    # # Create journal entry using Pydantic model
    # entry_id = f"entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # journal_entry = JournalEntry(
    #     entry_id=entry_id,
    #     date=today,
    #     entry_type=EntryType.HOROSCOPE_READING,
    #     summary_viewed=daily_horoscope.summary,
    #     categories_viewed=viewed_groups,
    #     time_spent_seconds=180,  # Simulated
    #     created_at=datetime.now().isoformat()
    # )

    # # Update memory using Pydantic model helper function
    # memory = update_memory_from_journal(memory, journal_entry)

    # console.print(f"[green]✓ Journal entry created: {entry_id}[/green]")
    # console.print(f"[green]✓ Groups viewed: {[c.category.value for c in viewed_groups]}[/green]")
    # console.print(f"[green]✓ Memory collection updated[/green]")

    # Show updated memory state
    console.print(f"\n[yellow]Updated Memory State:[/yellow]")
    for cat_name, cat_data in memory.categories.items():
        if cat_data.count > 0:
            console.print(f"  • {cat_name.value.replace('_', ' ').title()}: {cat_data.count} views")

    console.print(f"\n[yellow]Recent Readings:[/yellow] {len(memory.recent_readings)}")

    # ========================================================================
    # 7. PERFORMANCE SUMMARY
    # ========================================================================
    print_section("7️⃣  PERFORMANCE SUMMARY", style="bold cyan")

    # Show token usage
    from rich.table import Table
    table = Table(title="LLM Token Usage", show_header=True, header_style="bold magenta")
    table.add_column("Stage", style="dim", width=30)
    table.add_column("Model", style="dim", width=20)
    table.add_column("Time (s)", justify="right")
    table.add_column("Prompt Tokens", justify="right")
    table.add_column("Output Tokens", justify="right")
    table.add_column("Thinking Tokens", justify="right")
    table.add_column("Cached Tokens", justify="right")
    table.add_column("Total Tokens", justify="right")


    for stage, t in [
        ("Daily Horoscope", daily_horoscope),
        # ("Detailed Horoscope", detailed_horoscope)  # DEPRECATED
    ]:
        # force type hinting
        data: DailyHoroscope = t

        # example output for usage data
        # {
        #     'cache_tokens_details': None,
        #     'cached_content_token_count': None,
        #     'candidates_token_count': 1672,
        #     'candidates_tokens_details': None,
        #     'prompt_token_count': 2358,
        #     'prompt_tokens_details': [{'modality': <MediaModality.TEXT: 'TEXT'>, 'token_count': 2358}],
        #     'thoughts_token_count': 3059,
        #     'tool_use_prompt_token_count': None,
        #     'tool_use_prompt_tokens_details': None,
        #     'total_token_count': 7089,
        #     'traffic_type': None
        # }
        # console.print(data.usage)
        table.add_row(
            stage,
            data.model_used,
            str(data.generation_time_ms / 1000),
            str(data.usage.get("prompt_token_count", 0)),
            str(data.usage.get("candidates_token_count", 0)),
            str(data.usage.get("thoughts_token_count", 0)),
            str(data.usage.get("cached_content_token_count", 0)),
            str(data.usage.get("total_token_count", 0)),
        )

    console.print(table)




    print_section("", style="bold magenta")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Prototype interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())

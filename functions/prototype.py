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
    summarize_transits,
    summarize_transits_with_natal,
    get_upcoming_transits,
    ZodiacSign,
    SunSignProfile,
    NatalChartData,
)

# Import our LLM modules
from llm import (
    generate_daily_horoscope,
    generate_detailed_horoscope
)

# Import our Pydantic models
from models import (
    UserProfile,
    MemoryCollection,
    CategoryEngagement,
    CategoryViewed,
    JournalEntry,
    EntryType,
    DailyHoroscope,
    HoroscopeDetails,
    create_empty_memory,
    update_memory_from_journal,
)
from astrometers.hierarchy import MeterGroup

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

    # Generate enhanced transit summary with natal-transit aspects
    console.print("\n[cyan]Analyzing natal-transit aspects...[/cyan]")
    transit_data = summarize_transits_with_natal(natal_chart, transit_chart)
    console.print("[green]✓ Enhanced transit data generated[/green]")

    # Display primary aspect if found
    if transit_data.primary_aspect:
        aspect = transit_data.primary_aspect
        console.print("\n[yellow]Primary Aspect Today:[/yellow]")
        console.print(f"  {aspect.transit_planet.value.title()} {aspect.aspect_type.value} your natal {aspect.natal_planet.value.title()}")
        console.print(f"  Orb: {aspect.orb}° - {aspect.meaning}")
        console.print(f"  Status: {'Applying (building)' if aspect.applying else 'Separating (waning)'}")

    # Display lunar phase
    console.print("\n[yellow]Lunar Phase:[/yellow]")
    console.print(f"  {transit_data.lunar_phase.phase_name.replace('_', ' ').title()} {transit_data.lunar_phase.phase_emoji}")
    console.print(f"  Energy: {transit_data.lunar_phase.energy}")

    # Display other aspects
    if len(transit_data.all_natal_transit_aspects) > 1:
        console.print(f"\n[yellow]Other Natal-Transit Aspects:[/yellow] {len(transit_data.all_natal_transit_aspects) - 1} more")

    # Format memory for LLM using Pydantic model method
    memory_context = memory.format_for_llm()
    console.print(f"\n[yellow]Memory Context:[/yellow]")
    console.print(f"  {memory_context[:200]}...")

    # Generate horoscope with TWO-PROMPT ARCHITECTURE
    console.print(f"\n[cyan]Generating daily horoscope (Prompt 1)...[/cyan]")

    # Generate daily horosccope
    daily_horoscope = generate_daily_horoscope(
        date=today,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_data=transit_data,
        memory=memory,
        model_name=model_name)
    console.print(f"[green]✓ Daily horoscope generated ({daily_horoscope.generation_time_ms}ms)[/green]")


    detailed_horoscope = generate_detailed_horoscope(
        date=today,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_data=transit_data,
        memory=memory,
        daily_horoscope=daily_horoscope,
        model_name=model_name)
    console.print(f"[green]✓ Detailed horoscope generated ({detailed_horoscope.generation_time_ms}ms)[/green]")

    # Display uses both daily_horoscope and detailed_horoscope separately
    # (Can't combine Pydantic models dynamically)

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

    # Summary
    console.print(Panel(
        daily_horoscope.summary,
        title="[bold cyan]✨ Daily Summary[/bold cyan]",
        border_style="cyan"
    ))

    # Astrometers Summary
    astrometers_summary = f"""Overall Intensity: {daily_horoscope.astrometers.overall_intensity.intensity:.1f}/100 ({daily_horoscope.astrometers.overall_intensity.state_label})
Overall Harmony: {daily_horoscope.astrometers.overall_harmony.harmony:.1f}/100 ({daily_horoscope.astrometers.overall_harmony.state_label})
Overall Quality: {daily_horoscope.astrometers.overall_unified_quality.value.upper()}
Total Aspects Analyzed: {daily_horoscope.astrometers.aspect_count}

Key Aspects Driving Today:"""

    for key_aspect in daily_horoscope.astrometers.key_aspects[:3]:  # Show top 3
        astrometers_summary += f"\n• {key_aspect.description}"

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

    # Lunar Cycle Update
    console.print(Panel(
        daily_horoscope.lunar_cycle_update,
        title="[bold white]🌙 Lunar Cycle[/bold white]",
        border_style="white"
    ))

    # General Transits Overview
    transits_text = "\n".join(f"• {item}" for item in detailed_horoscope.general_transits_overview)
    console.print(Panel(
        transits_text,
        title="[bold cyan]🌌 Collective Transits[/bold cyan]",
        border_style="cyan"
    ))

    # Look Ahead Preview
    console.print(Panel(
        detailed_horoscope.look_ahead_preview,
        title="[bold yellow]🔭 Coming Soon[/bold yellow]",
        border_style="yellow"
    ))


    # ========================================================================
    # 4. METER DATA VERIFICATION (DEBUG)
    # ========================================================================
    print_section("4️⃣  METER DATA VERIFICATION", style="bold yellow")

    console.print("[bold cyan]📊 Daily Horoscope Astrometers Data:[/bold cyan]\n")

    # Overall metrics
    console.print(f"[yellow]Overall Metrics:[/yellow]")
    console.print(f"  • Intensity: {daily_horoscope.astrometers.overall_intensity.intensity:.1f}/100 ({daily_horoscope.astrometers.overall_intensity.state_label})")
    console.print(f"  • Harmony: {daily_horoscope.astrometers.overall_harmony.harmony:.1f}/100 ({daily_horoscope.astrometers.overall_harmony.state_label})")
    console.print(f"  • Quality: {daily_horoscope.astrometers.overall_unified_quality.value.upper()}")
    console.print(f"  • Total Aspects: {daily_horoscope.astrometers.aspect_count}\n")

    # All key aspects
    console.print(f"[yellow]Key Aspects ({len(daily_horoscope.astrometers.key_aspects)} total):[/yellow]")
    for i, key_aspect in enumerate(daily_horoscope.astrometers.key_aspects, 1):
        console.print(f"  {i}. {key_aspect.description}")
        console.print(f"     Affects {key_aspect.meter_count} meters: {', '.join(key_aspect.affected_meters)}")
        console.print(f"     DTI: {key_aspect.aspect.dti_contribution:.1f} | HQS: {key_aspect.aspect.hqs_contribution:.1f}")

    # All 23 individual meters grouped by domain
    console.print(f"\n[yellow]All 23 Meters by Domain:[/yellow]\n")

    meters_by_domain = {
        "Global Meters": [
            ("Overall Intensity", daily_horoscope.astrometers.overall_intensity),
            ("Overall Harmony", daily_horoscope.astrometers.overall_harmony)
        ],
        "Emotional Meters": [
            ("Emotional Intensity", daily_horoscope.astrometers.emotional_intensity),
            ("Relationship Harmony", daily_horoscope.astrometers.relationship_harmony),
            ("Emotional Resilience", daily_horoscope.astrometers.emotional_resilience)
        ],
        "Cognitive Meters": [
            ("Mental Clarity", daily_horoscope.astrometers.mental_clarity),
            ("Decision Quality", daily_horoscope.astrometers.decision_quality),
            ("Communication Flow", daily_horoscope.astrometers.communication_flow)
        ],
        "Physical/Action Meters": [
            ("Physical Energy", daily_horoscope.astrometers.physical_energy),
            ("Conflict Risk", daily_horoscope.astrometers.conflict_risk),
            ("Motivation Drive", daily_horoscope.astrometers.motivation_drive)
        ],
        "Life Domain Meters": [
            ("Career Ambition", daily_horoscope.astrometers.career_ambition),
            ("Opportunity Window", daily_horoscope.astrometers.opportunity_window),
            ("Challenge Intensity", daily_horoscope.astrometers.challenge_intensity),
            ("Transformation Pressure", daily_horoscope.astrometers.transformation_pressure)
        ],
        "Specialized Meters": [
            ("Intuition/Spirituality", daily_horoscope.astrometers.intuition_spirituality),
            ("Innovation/Breakthrough", daily_horoscope.astrometers.innovation_breakthrough),
            ("Karmic Lessons", daily_horoscope.astrometers.karmic_lessons),
            ("Social/Collective", daily_horoscope.astrometers.social_collective)
        ],
        "Element Meters": [
            ("Fire Energy", daily_horoscope.astrometers.fire_energy),
            ("Earth Energy", daily_horoscope.astrometers.earth_energy),
            ("Air Energy", daily_horoscope.astrometers.air_energy),
            ("Water Energy", daily_horoscope.astrometers.water_energy)
        ]
    }

    for domain, meters in meters_by_domain.items():
        console.print(f"[cyan]{domain}:[/cyan]")
        for meter_name, meter_reading in meters:
            console.print(f"  • {meter_name}: {meter_reading.unified_score:.1f}/100 ({meter_reading.unified_quality.value.upper()})")
            console.print(f"    Intensity: {meter_reading.intensity:.1f} | Harmony: {meter_reading.harmony:.1f} | State: {meter_reading.state_label}")
        console.print()

    # Domain meters used in detailed horoscope
    console.print(f"[bold cyan]📋 Domain-Grouped Meters (for Detailed Horoscope):[/bold cyan]\n")

    # Import the group function to show what detailed horoscope received
    from astrometers import group_meters_by_domain
    domain_meters = group_meters_by_domain(daily_horoscope.astrometers)

    console.print(f"[yellow]Overview Group:[/yellow]")
    console.print(f"  • Overall Intensity: {domain_meters['overview']['overall_intensity'].unified_score:.1f}/100")
    console.print(f"  • Overall Harmony: {domain_meters['overview']['overall_harmony'].unified_score:.1f}/100")

    console.print(f"\n[yellow]Mind Group:[/yellow]")
    console.print(f"  • Mental Clarity: {domain_meters['mind']['mental_clarity'].unified_score:.1f}/100")
    console.print(f"  • Decision Quality: {domain_meters['mind']['decision_quality'].unified_score:.1f}/100")
    console.print(f"  • Communication Flow: {domain_meters['mind']['communication_flow'].unified_score:.1f}/100")

    console.print(f"\n[yellow]Emotions Group:[/yellow]")
    console.print(f"  • Emotional Intensity: {domain_meters['emotions']['emotional_intensity'].unified_score:.1f}/100")
    console.print(f"  • Relationship Harmony: {domain_meters['emotions']['relationship_harmony'].unified_score:.1f}/100")
    console.print(f"  • Emotional Resilience: {domain_meters['emotions']['emotional_resilience'].unified_score:.1f}/100")

    console.print(f"\n[yellow]Body Group:[/yellow]")
    console.print(f"  • Physical Energy: {domain_meters['body']['physical_energy'].unified_score:.1f}/100")
    console.print(f"  • Conflict Risk: {domain_meters['body']['conflict_risk'].unified_score:.1f}/100")
    console.print(f"  • Motivation Drive: {domain_meters['body']['motivation_drive'].unified_score:.1f}/100")

    console.print(f"\n[yellow]Career Group:[/yellow]")
    console.print(f"  • Career Ambition: {domain_meters['career']['career_ambition'].unified_score:.1f}/100")
    console.print(f"  • Opportunity Window: {domain_meters['career']['opportunity_window'].unified_score:.1f}/100")

    console.print(f"\n[yellow]Evolution Group:[/yellow]")
    console.print(f"  • Challenge Intensity: {domain_meters['evolution']['challenge_intensity'].unified_score:.1f}/100")
    console.print(f"  • Transformation Pressure: {domain_meters['evolution']['transformation_pressure'].unified_score:.1f}/100")
    console.print(f"  • Innovation Breakthrough: {domain_meters['evolution']['innovation_breakthrough'].unified_score:.1f}/100")

    console.print(f"\n[yellow]Elements Group:[/yellow]")
    console.print(f"  • Fire Energy: {domain_meters['elements']['fire_energy'].unified_score:.1f}/100")
    console.print(f"  • Earth Energy: {domain_meters['elements']['earth_energy'].unified_score:.1f}/100")
    console.print(f"  • Air Energy: {domain_meters['elements']['air_energy'].unified_score:.1f}/100")
    console.print(f"  • Water Energy: {domain_meters['elements']['water_energy'].unified_score:.1f}/100")

    console.print(f"\n[yellow]Spiritual Group:[/yellow]")
    console.print(f"  • Intuition/Spirituality: {domain_meters['spiritual']['intuition_spirituality'].unified_score:.1f}/100")
    console.print(f"  • Karmic Lessons: {domain_meters['spiritual']['karmic_lessons'].unified_score:.1f}/100")

    console.print(f"\n[yellow]Collective Group:[/yellow]")
    console.print(f"  • Social/Collective: {domain_meters['collective']['social_collective'].unified_score:.1f}/100")

    # ========================================================================
    # 5. EXPANDED VIEW - DETAILED PREDICTIONS
    # ========================================================================
    print_section("5️⃣  DETAILED PREDICTIONS", style="bold cyan")

    # Simulate user viewing specific groups (new 9-group system)
    groups_to_view = [
        "mind",
        "emotions",
        "career",
        "spiritual"
    ]

    group_icons = {
        "overview": "📊",
        "mind": "🧠",
        "emotions": "💕",
        "body": "💪",
        "career": "💼",
        "evolution": "🌱",
        "elements": "🔥",
        "spiritual": "✨",
        "collective": "🌍"
    }

    viewed_groups = []

    for group in groups_to_view:
        icon = group_icons.get(group, "🔮")
        title = group.replace("_", " ").title()
        text = getattr(detailed_horoscope.details, group)

        console.print(Panel(
            text,
            title=f"[bold]{icon} {title}[/bold]",
            border_style="blue"
        ))

        # Track for journal entry - create CategoryViewed Pydantic model
        viewed_groups.append(
            CategoryViewed(
                category=MeterGroup(group),
                text=text
            )
        )

    # ========================================================================
    # 6. JOURNAL ENTRY & MEMORY UPDATE
    # ========================================================================
    print_section("6️⃣  JOURNAL ENTRY & MEMORY UPDATE", style="bold cyan")

    console.print("[cyan]Creating journal entry...[/cyan]")

    # Create journal entry using Pydantic model
    entry_id = f"entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    journal_entry = JournalEntry(
        entry_id=entry_id,
        date=today,
        entry_type=EntryType.HOROSCOPE_READING,
        summary_viewed=daily_horoscope.summary,
        categories_viewed=viewed_groups,
        time_spent_seconds=180,  # Simulated
        created_at=datetime.now().isoformat()
    )

    # Update memory using Pydantic model helper function
    memory = update_memory_from_journal(memory, journal_entry)

    console.print(f"[green]✓ Journal entry created: {entry_id}[/green]")
    console.print(f"[green]✓ Groups viewed: {[c.category.value for c in viewed_groups]}[/green]")
    console.print(f"[green]✓ Memory collection updated[/green]")

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
        ("Detailed Horoscope", detailed_horoscope)
    ]:
        # force type hinting
        data: DailyHoroscope | HoroscopeDetails = t

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

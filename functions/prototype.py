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
    generate_detailed_horoscope,
    create_daily_static_cache,
    create_detailed_static_cache
)

# Import our Pydantic models
from models import (
    UserProfile,
    MemoryCollection,
    CategoryEngagement,
    CategoryViewed,
    CategoryName,
    JournalEntry,
    EntryType,
    DailyHoroscope,
    HoroscopeDetails,
    create_empty_memory,
    update_memory_from_journal,
)

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
    model_name = "gemini-2.5-flash"


    print_section("🌟 ARCA BACKEND V1 PROTOTYPE 🌟", style="bold magenta")




    # ========================================================================
    # 1. USER ONBOARDING
    # ========================================================================
    print_section("1️⃣  USER ONBOARDING", style="bold cyan")

    # Simulated user
    user = {
        "id": "user_test_123",
        "name": "Alex",
        "email": "alex@example.com"
    }

    console.print(f"[green]✓ User authenticated: {user['name']} ({user['email']})[/green]")

    # Birth information
    birth_date = "1985-05-15"
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

    # Key Active Transit
    console.print(Panel(
        daily_horoscope.key_active_transit,
        title="[bold red]🔥 Key Personal Transit[/bold red]",
        border_style="red"
    ))

    # Area of Life Activated
    console.print(Panel(
        daily_horoscope.area_of_life_activated,
        title="[bold blue]🎯 Life Area Activated[/bold blue]",
        border_style="blue"
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

    console.print("\n[dim]→ Read detailed predictions below ↓[/dim]\n")

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



    # ========================================================================
    # 4. EXPANDED VIEW - DETAILED PREDICTIONS
    # ========================================================================
    print_section("4️⃣  DETAILED PREDICTIONS", style="bold cyan")

    # Simulate user viewing specific categories
    categories_to_view = [
        "love_relationships",
        "path_profession",
        "personal_growth",
        "purpose_spirituality"
    ]

    category_icons = {
        "love_relationships": "💕",
        "family_friendships": "👥",
        "path_profession": "💼",
        "personal_growth": "🌱",
        "finance_abundance": "💰",
        "purpose_spirituality": "✨",
        "home_environment": "🏡",
        "decisions_crossroads": "🔀"
    }

    viewed_categories = []

    for category in categories_to_view:
        icon = category_icons.get(category, "🔮")
        title = category.replace("_", " ").title()
        text = getattr(detailed_horoscope.details, category)

        console.print(Panel(
            text,
            title=f"[bold]{icon} {title}[/bold]",
            border_style="blue"
        ))

        # Track for journal entry - create CategoryViewed Pydantic model
        viewed_categories.append(
            CategoryViewed(
                category=CategoryName(category),
                text=text
            )
        )

    # ========================================================================
    # 5. JOURNAL ENTRY & MEMORY UPDATE
    # ========================================================================
    print_section("5️⃣  JOURNAL ENTRY & MEMORY UPDATE", style="bold cyan")

    console.print("[cyan]Creating journal entry...[/cyan]")

    # Create journal entry using Pydantic model
    entry_id = f"entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    journal_entry = JournalEntry(
        entry_id=entry_id,
        date=today,
        entry_type=EntryType.HOROSCOPE_READING,
        summary_viewed=daily_horoscope.summary,
        categories_viewed=viewed_categories,
        time_spent_seconds=180,  # Simulated
        created_at=datetime.now().isoformat()
    )

    # Update memory using Pydantic model helper function
    memory = update_memory_from_journal(memory, journal_entry)

    console.print(f"[green]✓ Journal entry created: {entry_id}[/green]")
    console.print(f"[green]✓ Categories viewed: {[c.category.value for c in viewed_categories]}[/green]")
    console.print(f"[green]✓ Memory collection updated[/green]")

    # Show updated memory state
    console.print(f"\n[yellow]Updated Memory State:[/yellow]")
    for cat_name, cat_data in memory.categories.items():
        if cat_data.count > 0:
            console.print(f"  • {cat_name.value.replace('_', ' ').title()}: {cat_data.count} views")

    console.print(f"\n[yellow]Recent Readings:[/yellow] {len(memory.recent_readings)}")

    # ========================================================================
    # 6. SUMMARY
    # ========================================================================
    print_section("✅ PROTOTYPE COMPLETE", style="bold green")

    console.print("[green]Successfully demonstrated:[/green]")
    console.print("  ✓ User onboarding with birth date")
    console.print("  ✓ Sun sign calculation and profile loading")
    console.print("  ✓ Birth chart computation (V1 mode)")
    console.print("  ✓ Transit data generation and summarization")
    console.print("  ✓ Natal-transit aspect analysis (TRUE PERSONALIZATION!)")
    console.print("  ✓ Lunar phase calculation with guidance")
    console.print("  ✓ LLM-powered horoscope generation with enhanced context")
    console.print("  ✓ Memory/personalization system")
    console.print("  ✓ Journal entry tracking")
    console.print("  ✓ Category engagement tracking")

    console.print("\n[cyan]Next Steps:[/cyan]")
    console.print("  → Integrate with Firebase (Firestore + Callable Functions)")
    console.print("  → Add PostHog LLM analytics tracking")
    console.print("  → Implement Firestore trigger for memory updates")
    console.print("  → Build iOS app integration")

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

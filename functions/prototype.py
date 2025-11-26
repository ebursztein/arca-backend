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

import os
os.environ["DEBUG_PROMPT"] = "1"  # Enable debug prompt output for prototype

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
from llm import generate_daily_horoscope, update_memory_with_relationship_mention

# Import our Pydantic models
from models import (
    UserProfile,
    MemoryCollection,
    CategoryEngagement,
    DailyHoroscope,
    create_empty_memory,
    Entity,
    EntityStatus,
    EntityCategory,
    AttributeKV,
    RelationshipMention,
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

    # Simulate one previous relationship mention to demo rotation
    # John was featured yesterday, so rotation should pick someone else
    memory.relationship_mentions = [
        RelationshipMention(
            entity_id="ent_001",
            entity_name="John",
            category=EntityCategory.PARTNER,
            date="2025-11-24",
            context="Today's energy supports deeper connection with John."
        ),
    ]

    console.print(f"[green]✓ Memory collection initialized (John mentioned yesterday)[/green]")

    # Create sample entities with categories for relationship weather
    now = datetime.now()
    sample_entities = [
        Entity(
            entity_id="ent_001",
            name="John",
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            category=EntityCategory.PARTNER,
            relationship_label="boyfriend",
            notes="Met at coffee shop last year. Anniversary in June.",
            aliases=["boyfriend", "partner"],
            attributes=[
                AttributeKV(key="relationship_status", value="dating")
            ],
            related_entities=[],
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=5,
            context_snippets=["Feeling some tension lately"],
            importance_score=0.85,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        ),
        Entity(
            entity_id="ent_002",
            name="Mom",
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            category=EntityCategory.FAMILY,
            relationship_label="mother",
            notes="Lives nearby. Weekly Sunday dinners.",
            aliases=["mother"],
            attributes=[],
            related_entities=[],
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=3,
            context_snippets=["Planning her birthday party"],
            importance_score=0.70,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        ),
        Entity(
            entity_id="ent_003",
            name="Sarah",
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            category=EntityCategory.FRIEND,
            relationship_label=None,
            notes="Best friend since college.",
            aliases=[],
            attributes=[],
            related_entities=[],
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=4,
            context_snippets=["Planning a trip together"],
            importance_score=0.75,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        ),
        Entity(
            entity_id="ent_004",
            name="Mike",
            entity_type="relationship",
            status=EntityStatus.ACTIVE,
            category=EntityCategory.COWORKER,
            relationship_label="boss",
            notes="Direct manager at TechCorp. Fair but demanding.",
            aliases=["manager"],
            attributes=[AttributeKV(key="company", value="TechCorp")],
            related_entities=[],
            first_seen=now.isoformat(),
            last_seen=now.isoformat(),
            mention_count=2,
            context_snippets=["Performance review coming up"],
            importance_score=0.65,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        ),
    ]

    console.print(f"[green]✓ Sample entities created: {len(sample_entities)} relationships[/green]")
    for entity in sample_entities:
        label = f" ({entity.relationship_label})" if entity.relationship_label else ""
        console.print(f"  - {entity.name}{label} [{entity.category.value}]")

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
    daily_horoscope, featured_relationship = generate_daily_horoscope(
        date=today,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_summary=transit_summary,  # NEW: Enhanced transit summary dict
        memory=memory,
        entities=sample_entities,  # Pass entities for relationship weather
        model_name=model_name)
    console.print(f"[green]✓ Daily horoscope generated ({daily_horoscope.generation_time_ms}ms)[/green]")

    # Update memory with relationship mention (for rotation tracking)
    if featured_relationship:
        memory = update_memory_with_relationship_mention(
            memory=memory,
            featured_relationship=featured_relationship,
            date=today,
            relationship_weather=daily_horoscope.relationship_weather or ""
        )
        console.print(f"[green]✓ Memory updated with featured relationship: {featured_relationship.name}[/green]")

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
        "heart": "💕",
        "body": "💪",
        "instincts": "✨",
        "evolution": "🌱"
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

    console.print(f"\n[yellow]Total Conversations:[/yellow] {memory.total_conversations}")

    # ========================================================================
    # 6. ASK THE STARS - CONVERSATIONAL Q&A
    # ========================================================================
    print_section("6️⃣  ASK THE STARS - CONVERSATIONAL Q&A", style="bold magenta")

    console.print("[cyan]Testing Ask the Stars feature with sample question...[/cyan]\n")

    # Import Ask the Stars modules (Entity, EntityStatus, EntityCategory, AttributeKV already imported at top)
    from models import (
        Message, MessageRole, Conversation,
        ExtractedEntities, ExtractedEntity, MergedEntities, EntityMergeAction,
        UserEntities
    )
    from entity_extraction import (
        extract_entities_from_message,
        merge_entities_with_existing,
        execute_merge_actions,
        get_top_entities_by_importance
    )
    from ask_the_stars import stream_ask_the_stars_response
    import os
    from google import genai
    import time

    # Initialize Gemini client for entity extraction
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    posthog_api_key = os.environ.get("POSTHOG_API_KEY")
    ask_the_stars_perf = None  # Default if test skipped

    if not gemini_api_key:
        console.print("[red]⚠️  GEMINI_API_KEY not set, skipping Ask the Stars test[/red]")
    else:
        gemini_client = genai.Client(api_key=gemini_api_key)

        # Create sample entities (simulating existing user data)
        now = datetime.now()
        sample_entities = [
            Entity(
                entity_id="ent_001",
                name="John",
                entity_type="relationship",
                status=EntityStatus.ACTIVE,
                aliases=["boyfriend", "partner"],
                attributes=[
                    AttributeKV(key="relationship_to_user", value="partner"),
                    AttributeKV(key="relationship_status", value="dating")
                ],
                related_entities=[],
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=5,
                context_snippets=[
                    "Met at coffee shop last year",
                    "Anniversary in June",
                    "Feeling some tension lately"
                ],
                importance_score=0.85,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            ),
            Entity(
                entity_id="ent_002",
                name="TechCorp",
                entity_type="company",
                status=EntityStatus.ACTIVE,
                aliases=[],
                attributes=[AttributeKV(key="user_role", value="software engineer")],
                related_entities=[],
                first_seen=(now).isoformat(),
                last_seen=now.isoformat(),
                mention_count=3,
                context_snippets=["Working at TechCorp for 2 years", "Big project deadline coming up"],
                importance_score=0.70,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            ),
            Entity(
                entity_id="ent_003",
                name="Luna",
                entity_type="pet",
                status=EntityStatus.ACTIVE,
                aliases=["cat"],
                attributes=[
                    AttributeKV(key="species", value="cat"),
                    AttributeKV(key="personality", value="playful")
                ],
                related_entities=[],
                first_seen=now.isoformat(),
                last_seen=now.isoformat(),
                mention_count=2,
                context_snippets=["Luna my cat keeps me company", "She's very cuddly"],
                importance_score=0.60,
                created_at=now.isoformat(),
                updated_at=now.isoformat()
            )
        ]

        console.print(f"[green]✓ Sample entities created: {len(sample_entities)} entities[/green]")
        for entity in sample_entities:
            console.print(f"  • {entity.name} ({entity.entity_type}) - {entity.mention_count} mentions")

        # User asks a question
        user_question = "Why am I feeling so much tension with John at work today? My cat Luna has been acting weird too."
        console.print(f"\n[yellow]User Question:[/yellow]")
        console.print(f"  \"{user_question}\"")

        # Create async function to run all async operations in single event loop
        import asyncio
        async def run_ask_the_stars_flow():
            # Step 1: Extract entities from message
            console.print(f"\n[cyan]Step 1: Extracting entities from message...[/cyan]")
            extracted, perf_extract = await extract_entities_from_message(
                user_message=user_question,
                current_date=today,
                gemini_client=gemini_client,
                user_id=user_profile.user_id,
                posthog_api_key=posthog_api_key
            )
            console.print(f"[green]✓ Extracted {len(extracted.entities)} entities ({perf_extract['time_ms']}ms)[/green]")
            for ent in extracted.entities:
                console.print(f"  • {ent.name} ({ent.entity_type}) - \"{ent.context}\"")
                if ent.attributes:
                    attrs_dict = {attr.key: attr.value for attr in ent.attributes}
                    console.print(f"    Attributes: {attrs_dict}")

            # Use sample entities directly (no merging in prototype)
            top_entities = sample_entities

            # Step 2: Generate answer using Ask the Stars
            console.print(f"\n[cyan]Step 2: Generating answer with Ask the Stars...[/cyan]")
            start_time = time.time()
            answer_chunks = []

            # Stream answer from LLM (sync generator, not async)
            for chunk in stream_ask_the_stars_response(
                question=user_question,
                horoscope_date=today,
                user_profile=user_profile,
                horoscope=daily_horoscope,
                entities=top_entities,
                memory=memory,
                conversation_messages=[],  # First question in conversation
                gemini_client=gemini_client,
                posthog_api_key=posthog_api_key,
                model=model_name
            ):
                # Parse SSE format: "data: {json}\n\n"
                import json
                if chunk.startswith("data: "):
                    chunk_json = json.loads(chunk[6:])  # Remove "data: " prefix
                    if chunk_json['type'] == 'chunk':
                        answer_chunks.append(chunk_json['text'])

            answer = "".join(answer_chunks)
            answer_time_ms = (time.time() - start_time) * 1000

            return answer, answer_time_ms, perf_extract

        # Run all async operations in single event loop
        answer, answer_time_ms, perf_extract = asyncio.run(run_ask_the_stars_flow())

        console.print(f"[green]✓ Generated answer ({answer_time_ms:.0f}ms)[/green]")
        console.print(f"\n[yellow]Answer:[/yellow]")
        console.print(Panel(
            answer,
            title="[bold magenta]🌟 Ask the Stars Response[/bold magenta]",
            border_style="magenta"
        ))

        console.print(f"\n[cyan]Ask the Stars test completed[/cyan]")

        # Store performance data for summary table
        ask_the_stars_perf = {
            "extract": perf_extract,
            "answer": {
                "time_ms": answer_time_ms,
                "model": model_name,
                "usage": {}  # Streaming doesn't return usage metadata
            }
        }

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

    # Add Ask the Stars performance data
    if ask_the_stars_perf:
        for stage_name, perf_data in [
            ("Entity Extraction", ask_the_stars_perf["extract"]),
            ("Answer Generation", ask_the_stars_perf["answer"])
        ]:
            usage = perf_data.get("usage", {})
            table.add_row(
                stage_name,
                perf_data.get("model", "unknown"),
                str(perf_data.get("time_ms", 0) / 1000),
                str(usage.get("prompt_token_count", 0)),
                str(usage.get("candidates_token_count", 0)),
                str(usage.get("thoughts_token_count", 0)),
                str(usage.get("cached_content_token_count", 0)),
                str(usage.get("total_token_count", 0)),
            )

    console.print(table)

    # Summary of Ask the Stars performance
    if ask_the_stars_perf:
        console.print(f"\n[yellow]Ask the Stars Summary:[/yellow]")
        extract_usage = ask_the_stars_perf["extract"]["usage"]
        console.print(f"  Entity Extraction: {ask_the_stars_perf['extract']['time_ms']}ms | {extract_usage.get('prompt_token_count', 0)}→{extract_usage.get('candidates_token_count', 0)} tokens")
        console.print(f"  Answer Generation: {ask_the_stars_perf['answer']['time_ms']:.0f}ms | (streaming - no token count)")
        console.print(f"  Total: {ask_the_stars_perf['extract']['time_ms'] + ask_the_stars_perf['answer']['time_ms']:.0f}ms")




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

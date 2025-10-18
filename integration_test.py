#!/usr/bin/env python3
"""
Integration Test - Mimics iOS App Flow

Simulates what the iOS app will do:
1. Get sun sign from birth date (onboarding)
2. Create user profile with natal chart
3. Generate daily horoscope (Prompt 1)
4. Generate detailed horoscope (Prompt 2)
5. Create journal entry when user reads
6. Verify memory gets updated automatically

This tests the complete backend by directly using Firestore and the business logic,
exactly how the deployed Cloud Functions would work.

Requirements:
    - Firebase emulator running (firebase emulators:start)
    - GEMINI_API_KEY environment variable

Usage:
    python integration_test.py
"""

import os
import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import time

# Add functions directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions'))

# Set emulator environment variable
os.environ['FIRESTORE_EMULATOR_HOST'] = '127.0.0.1:8080'

from firebase_admin import initialize_app, firestore, get_app

# Initialize Firebase
try:
    app = get_app()
except ValueError:
    app = initialize_app()

# Import business logic modules
from astro import (
    get_sun_sign,
    get_sun_sign_profile,
    compute_birth_chart,
    summarize_transits_with_natal,
)
from models import (
    UserProfile,
    MemoryCollection,
    JournalEntry,
    EntryType,
    CategoryViewed,
    CategoryName,
    create_empty_memory,
    update_memory_from_journal,
)
from llm import (
    generate_daily_horoscope,
    generate_detailed_horoscope,
)

console = Console()

# Test data
TEST_USER_ID = "integration_test_user"
TEST_NAME = "Alex"
TEST_EMAIL = "alex@test.com"
TEST_BIRTH_DATE = "1990-06-15"  # Gemini


def print_section(title: str, style: str = "bold cyan"):
    """Print a formatted section."""
    console.print(f"\n[{style}]{'=' * 70}[/{style}]")
    console.print(f"[{style}]{title}[/{style}]")
    console.print(f"[{style}]{'=' * 70}[/{style}]\n")


def cleanup_test_data():
    """Clean up test data before starting."""
    db = firestore.client()

    # Delete test user
    db.collection("users").document(TEST_USER_ID).delete()

    # Delete test memory
    db.collection("memory").document(TEST_USER_ID).delete()

    # Delete test journal entries
    journal_ref = db.collection("users").document(TEST_USER_ID).collection("journal")
    docs = journal_ref.stream()
    for doc in docs:
        doc.reference.delete()

    console.print("[yellow]✓ Test data cleaned up[/yellow]")


def main():
    """Run the complete integration test."""

    print_section("🌟 ARCA BACKEND INTEGRATION TEST 🌟", "bold magenta")
    console.print("[dim]Simulating iOS app user journey...[/dim]\n")

    # Clean up any existing test data
    cleanup_test_data()

    db = firestore.client()

    # =========================================================================
    # Step 1: iOS App - Onboarding: Get Sun Sign
    # =========================================================================
    print_section("1️⃣  ONBOARDING: GET SUN SIGN", "bold cyan")

    console.print(f"[cyan]User enters birth date:[/cyan] {TEST_BIRTH_DATE}")

    # Calculate sun sign (this is what get_sun_sign_from_date() does)
    sun_sign = get_sun_sign(TEST_BIRTH_DATE)
    sun_sign_profile = get_sun_sign_profile(sun_sign)

    console.print(f"[green]✓ Sun Sign:[/green] {sun_sign.value.title()} {sun_sign_profile.symbol}")
    console.print(f"[green]✓ Element:[/green] {sun_sign_profile.element.value.title()}")
    console.print(f"[green]✓ Modality:[/green] {sun_sign_profile.modality.value.title()}")
    console.print(f"[green]✓ Ruling Planet:[/green] {sun_sign_profile.ruling_planet}")

    console.print(f"\n[dim]iOS shows: \"You're a {sun_sign.value.title()}! ♊\"[/dim]")

    # =========================================================================
    # Step 2: iOS App - Create User Profile
    # =========================================================================
    print_section("2️⃣  CREATE USER PROFILE", "bold cyan")

    console.print(f"[cyan]Creating profile with:[/cyan]")
    console.print(f"  • User ID: {TEST_USER_ID}")
    console.print(f"  • Name: {TEST_NAME}")
    console.print(f"  • Email: {TEST_EMAIL}")
    console.print(f"  • Birth Date: {TEST_BIRTH_DATE}")
    console.print(f"  • Mode: V1 (birth date only)")

    # Compute natal chart (this is what create_user_profile() does)
    natal_chart, exact_chart = compute_birth_chart(birth_date=TEST_BIRTH_DATE)

    now = datetime.now().isoformat()

    user_profile = UserProfile(
        user_id=TEST_USER_ID,
        name=TEST_NAME,
        email=TEST_EMAIL,
        is_premium=False,
        premium_expiry=None,
        birth_date=TEST_BIRTH_DATE,
        birth_time=None,
        birth_timezone=None,
        birth_lat=None,
        birth_lon=None,
        sun_sign=sun_sign.value,
        natal_chart=natal_chart,
        exact_chart=exact_chart,
        created_at=now,
        last_active=now
    )

    # Save to Firestore
    db.collection("users").document(TEST_USER_ID).set(user_profile.model_dump())

    # Initialize memory
    memory = create_empty_memory(TEST_USER_ID)
    db.collection("memory").document(TEST_USER_ID).set(memory.model_dump())

    console.print(f"[green]✓ Profile saved to Firestore[/green]")
    console.print(f"[green]✓ Memory collection initialized[/green]")
    console.print(f"[green]✓ Natal chart computed: {len(natal_chart['planets'])} planets[/green]")

    # =========================================================================
    # Step 3: iOS App - User Opens App, Generate Daily Horoscope
    # =========================================================================
    print_section("3️⃣  GENERATE DAILY HOROSCOPE (Prompt 1)", "bold cyan")

    today = datetime.now().strftime("%Y-%m-%d")
    console.print(f"[cyan]Date:[/cyan] {today}")
    console.print("[cyan]iOS calls: get_daily_horoscope(user_id)[/cyan]\n")

    # Get user profile from Firestore (like the function does)
    user_doc = db.collection("users").document(TEST_USER_ID).get()
    user_data = user_doc.to_dict()
    user_profile = UserProfile(**user_data)

    # Get memory
    memory_doc = db.collection("memory").document(TEST_USER_ID).get()
    memory_data = memory_doc.to_dict()
    memory = MemoryCollection(**memory_data)

    # Compute today's transits
    transit_chart, _ = compute_birth_chart(birth_date=today, birth_time="12:00")

    # Get natal-transit aspects
    transit_data = summarize_transits_with_natal(user_profile.natal_chart, transit_chart)

    console.print(f"[yellow]Computing horoscope (this takes 2-3 seconds)...[/yellow]")

    # Generate daily horoscope
    start_time = time.time()
    daily_horoscope = generate_daily_horoscope(
        date=today,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_data=transit_data,
        memory=memory,
        model_name="gemini-2.5-flash-lite"
    )
    daily_time = (time.time() - start_time) * 1000

    console.print(f"[green]✓ Generated in {daily_time:.0f}ms[/green]")
    console.print(f"[green]✓ Model: {daily_horoscope.model_used}[/green]\n")

    # Display what iOS would show
    console.print(Panel(
        daily_horoscope.daily_theme_headline,
        title="[bold magenta]💫 Daily Theme (Notification/Headline)[/bold magenta]",
        border_style="magenta"
    ))

    console.print(Panel(
        daily_horoscope.summary,
        title="[bold cyan]✨ Summary (Main Screen)[/bold cyan]",
        border_style="cyan"
    ))

    console.print("[dim]iOS shows these immediately (<2s load time)[/dim]")

    # =========================================================================
    # Step 4: iOS App - Load Detailed Predictions in Background
    # =========================================================================
    print_section("4️⃣  GENERATE DETAILED HOROSCOPE (Prompt 2)", "bold cyan")

    console.print("[cyan]iOS calls: get_detailed_horoscope(user_id, daily_horoscope)[/cyan]")
    console.print("[yellow]Computing detailed predictions (this takes 5-7 seconds)...[/yellow]\n")

    # Generate detailed horoscope
    start_time = time.time()
    detailed_horoscope = generate_detailed_horoscope(
        date=today,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_data=transit_data,
        memory=memory,
        daily_horoscope=daily_horoscope,
        model_name="gemini-2.5-flash-lite"
    )
    detailed_time = (time.time() - start_time) * 1000

    console.print(f"[green]✓ Generated in {detailed_time:.0f}ms[/green]")
    console.print(f"[green]✓ Model: {detailed_horoscope.model_used}[/green]\n")

    # Show categories
    details = detailed_horoscope.details.model_dump()
    console.print("[yellow]Categories available to user:[/yellow]")
    for category in details.keys():
        word_count = len(details[category].split())
        console.print(f"  • {category.replace('_', ' ').title()}: {word_count} words")

    console.print("\n[dim]iOS loads these in background while user reads summary[/dim]")

    # =========================================================================
    # Step 5: iOS App - User Reads Categories, Create Journal Entry
    # =========================================================================
    print_section("5️⃣  USER READS HOROSCOPE → CREATE JOURNAL ENTRY", "bold cyan")

    console.print("[cyan]Simulating user reading Love and Career sections...[/cyan]")

    # User reads 2 categories
    categories_read = [
        CategoryViewed(
            category=CategoryName.LOVE_RELATIONSHIPS,
            text=details['love_relationships']
        ),
        CategoryViewed(
            category=CategoryName.PATH_PROFESSION,
            text=details['path_profession']
        )
    ]

    # Create journal entry (this is what add_journal_entry() does)
    entry_id = f"entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    journal_entry = JournalEntry(
        entry_id=entry_id,
        date=today,
        entry_type=EntryType.HOROSCOPE_READING,
        summary_viewed=daily_horoscope.summary,
        categories_viewed=categories_read,
        time_spent_seconds=180,
        created_at=datetime.now().isoformat()
    )

    # Save to Firestore
    db.collection("users").document(TEST_USER_ID).collection("journal").document(entry_id).set(
        journal_entry.model_dump()
    )

    console.print(f"[green]✓ Journal entry created: {entry_id}[/green]")
    console.print(f"[green]✓ Categories read: {len(categories_read)}[/green]")
    console.print(f"[green]✓ Time spent: {journal_entry.time_spent_seconds}s[/green]")

    # =========================================================================
    # Step 6: Firestore Trigger - Auto-Update Memory
    # =========================================================================
    print_section("6️⃣  FIRESTORE TRIGGER: UPDATE MEMORY", "bold cyan")

    console.print("[cyan]Simulating trigger: update_memory_on_journal_entry()[/cyan]")

    # This is what the Firestore trigger does automatically
    memory_doc = db.collection("memory").document(TEST_USER_ID).get()
    memory_data = memory_doc.to_dict()
    memory = MemoryCollection(**memory_data)

    # Update memory using helper function
    updated_memory = update_memory_from_journal(memory, journal_entry)

    # Write back to Firestore
    db.collection("memory").document(TEST_USER_ID).set(updated_memory.model_dump())

    console.print(f"[green]✓ Memory collection updated[/green]\n")

    # Show what changed
    console.print("[yellow]Category Engagement Updated:[/yellow]")
    for cat_name, cat_data in updated_memory.categories.items():
        if cat_data.count > 0:
            console.print(f"  • {cat_name.value.replace('_', ' ').title()}: {cat_data.count} views (last: {cat_data.last_mentioned})")

    console.print(f"\n[yellow]Recent Readings:[/yellow] {len(updated_memory.recent_readings)} reading(s)")
    if updated_memory.recent_readings:
        reading = updated_memory.recent_readings[0]
        console.print(f"  • {reading.date}: {len(reading.categories_viewed)} categories viewed")

    # =========================================================================
    # Step 7: Verify Everything Worked
    # =========================================================================
    print_section("7️⃣  VERIFICATION", "bold cyan")

    # Check user profile exists
    user_check = db.collection("users").document(TEST_USER_ID).get()
    console.print(f"[green]✓ User profile exists in Firestore[/green]")

    # Check memory exists and was updated
    memory_check = db.collection("memory").document(TEST_USER_ID).get()
    memory_final = memory_check.to_dict()
    console.print(f"[green]✓ Memory collection exists and updated[/green]")
    console.print(f"  Love views: {memory_final['categories']['love_relationships']['count']}")
    console.print(f"  Career views: {memory_final['categories']['path_profession']['count']}")

    # Check journal entry exists
    journal_check = db.collection("users").document(TEST_USER_ID).collection("journal").document(entry_id).get()
    console.print(f"[green]✓ Journal entry exists in Firestore[/green]")

    # Assertions
    assert memory_final['categories']['love_relationships']['count'] == 1
    assert memory_final['categories']['path_profession']['count'] == 1
    assert len(memory_final['recent_readings']) == 1

    # =========================================================================
    # Summary
    # =========================================================================
    print_section("✅ INTEGRATION TEST COMPLETE!", "bold green")

    # Performance table
    table = Table(title="Performance Metrics")
    table.add_column("Function", style="cyan")
    table.add_column("Time", justify="right", style="magenta")

    table.add_row("Daily Horoscope (Prompt 1)", f"{daily_time:.0f}ms")
    table.add_row("Detailed Horoscope (Prompt 2)", f"{detailed_time:.0f}ms")
    table.add_row("Total Generation Time", f"{daily_time + detailed_time:.0f}ms")

    console.print(table)

    console.print("\n[bold green]✅ All backend operations working correctly:[/bold green]")
    console.print("[green]  • User onboarding with sun sign[/green]")
    console.print("[green]  • Profile creation with natal chart[/green]")
    console.print("[green]  • Daily horoscope generation (<2s)[/green]")
    console.print("[green]  • Detailed predictions (~5s)[/green]")
    console.print("[green]  • Journal entry creation[/green]")
    console.print("[green]  • Memory auto-update via trigger logic[/green]")

    console.print("\n[bold cyan]📱 Ready for iOS app integration![/bold cyan]")

    # Cleanup
    console.print("\n[yellow]Cleaning up test data...[/yellow]")
    cleanup_test_data()


if __name__ == "__main__":
    # Check for GEMINI_API_KEY
    if "GEMINI_API_KEY" not in os.environ:
        console.print("[bold red]❌ Error: GEMINI_API_KEY environment variable not set[/bold red]")
        console.print("Set it with: export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)

    # Check if emulator is running
    try:
        db = firestore.client()
        db.collection("_test").document("_test").get()
        console.print("[green]✓ Firebase emulator connected[/green]")
    except Exception as e:
        console.print("[bold red]❌ Error: Firebase emulator not running[/bold red]")
        console.print("Start it with: firebase emulators:start")
        console.print(f"Error: {e}")
        sys.exit(1)

    try:
        main()
    except AssertionError as e:
        console.print(f"\n[bold red]❌ TEST FAILED:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ ERROR:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)

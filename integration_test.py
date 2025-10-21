#!/usr/bin/env python3
"""
Integration Test - Tests Firebase Functions via Emulator

This properly tests the deployed Cloud Functions by calling them through
the Firebase Functions emulator, exactly how the iOS app will call them.

Requirements:
    - Firebase emulator running (firebase emulators:start)
    - GEMINI_API_KEY environment variable

Usage:
    python integration_test.py
"""

import os
import sys
import requests
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Firebase Functions emulator endpoint
FUNCTIONS_EMULATOR_HOST = "http://127.0.0.1:5001"
PROJECT_ID = "arca-baf77"  # Your Firebase project ID
REGION = "us-central1"  # Default region

# Base URL for callable functions
FUNCTIONS_BASE_URL = f"{FUNCTIONS_EMULATOR_HOST}/{PROJECT_ID}/{REGION}"

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


def call_function(function_name: str, data: dict) -> dict:
    """
    Call a Firebase callable function via the emulator.

    Args:
        function_name: Name of the function
        data: Request data

    Returns:
        Response data from the function

    Raises:
        Exception if the function call fails
    """
    url = f"{FUNCTIONS_BASE_URL}/{function_name}"

    # Firebase callable functions expect data in a specific format
    payload = {"data": data}

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()

        # Check for Firebase Functions error format
        if "error" in result:
            error = result["error"]
            raise Exception(f"Function error: {error.get('message', 'Unknown error')}")

        return result.get("result", {})

    except requests.exceptions.Timeout:
        raise Exception(f"Function call timed out after 120 seconds")
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request failed: {str(e)}")


def main():
    """Run the complete integration test."""

    print_section("🌟 ARCA FIREBASE FUNCTIONS INTEGRATION TEST 🌟", "bold magenta")
    console.print("[dim]Testing via Firebase Functions Emulator...[/dim]\n")

    # Check emulator is running
    try:
        response = requests.get(FUNCTIONS_EMULATOR_HOST, timeout=5)
        console.print("[green]✓ Firebase Functions emulator is running[/green]\n")
    except:
        console.print("[bold red]❌ Error: Firebase Functions emulator not running[/bold red]")
        console.print("Start it with: firebase emulators:start")
        sys.exit(1)

    # =========================================================================
    # Step 1: Get Sun Sign (Onboarding)
    # =========================================================================
    print_section("1️⃣  ONBOARDING: GET SUN SIGN", "bold cyan")

    console.print(f"[cyan]User enters birth date:[/cyan] {TEST_BIRTH_DATE}")
    console.print(f"[cyan]Calling: get_sun_sign_from_date()[/cyan]\n")

    result = call_function("get_sun_sign_from_date", {
        "birth_date": TEST_BIRTH_DATE
    })

    sun_sign = result["sun_sign"]
    profile = result["profile"]

    console.print(f"[green]✓ Sun Sign:[/green] {sun_sign.title()} {profile['symbol']}")
    console.print(f"[green]✓ Element:[/green] {profile['element'].title()}")
    console.print(f"[green]✓ Modality:[/green] {profile['modality'].title()}")
    console.print(f"[green]✓ Ruling Planet:[/green] {profile['ruling_planet']}")

    console.print(f"\n[dim]iOS shows: \"You're a {sun_sign.title()}! {profile['symbol']}\"[/dim]")

    # =========================================================================
    # Step 2: Create User Profile
    # =========================================================================
    print_section("2️⃣  CREATE USER PROFILE", "bold cyan")

    console.print(f"[cyan]Creating profile with:[/cyan]")
    console.print(f"  • User ID: {TEST_USER_ID}")
    console.print(f"  • Name: {TEST_NAME}")
    console.print(f"  • Email: {TEST_EMAIL}")
    console.print(f"  • Birth Date: {TEST_BIRTH_DATE}")
    console.print(f"  • Mode: V1 (birth date only)")
    console.print(f"\n[cyan]Calling: create_user_profile()[/cyan]\n")

    result = call_function("create_user_profile", {
        "user_id": TEST_USER_ID,
        "name": TEST_NAME,
        "email": TEST_EMAIL,
        "birth_date": TEST_BIRTH_DATE
    })

    console.print(f"[green]✓ Profile created successfully[/green]")
    console.print(f"[green]✓ Sun sign: {result['sun_sign']}[/green]")
    console.print(f"[green]✓ Mode: {result['mode']}[/green]")
    console.print(f"[green]✓ Exact chart: {result['exact_chart']}[/green]")

    # =========================================================================
    # Step 3: Generate Daily Horoscope (Prompt 1)
    # =========================================================================
    print_section("3️⃣  GENERATE DAILY HOROSCOPE (Prompt 1)", "bold cyan")

    console.print(f"[cyan]Calling: get_daily_horoscope(user_id)[/cyan]")
    console.print("[yellow]This should take <2 seconds...[/yellow]\n")

    start_time = time.time()
    daily_result = call_function("get_daily_horoscope", {
        "user_id": TEST_USER_ID,
    })
    daily_time = (time.time() - start_time) * 1000

    console.print(f"[green]✓ Generated in {daily_time:.0f}ms[/green]")
    console.print(f"[green]✓ Model: {daily_result['model_used']}[/green]\n")

    # Display what iOS would show
    console.print(Panel(
        daily_result['daily_theme_headline'],
        title="[bold magenta]💫 Daily Theme (Notification/Headline)[/bold magenta]",
        border_style="magenta"
    ))

    console.print(Panel(
        daily_result['summary'],
        title="[bold cyan]✨ Summary (Main Screen)[/bold cyan]",
        border_style="cyan"
    ))

    console.print("[dim]iOS shows these immediately[/dim]")

    # =========================================================================
    # Step 4: Generate Detailed Horoscope (Prompt 2)
    # =========================================================================
    print_section("4️⃣  GENERATE DETAILED HOROSCOPE (Prompt 2)", "bold cyan")

    console.print("[cyan]Calling: get_detailed_horoscope(user_id, daily_horoscope)[/cyan]")
    console.print("[yellow]This should take ~5-7 seconds...[/yellow]\n")

    start_time = time.time()
    detailed_result = call_function("get_detailed_horoscope", {
        "user_id": TEST_USER_ID,
        "daily_horoscope": daily_result,
    })
    detailed_time = (time.time() - start_time) * 1000

    console.print(f"[green]✓ Generated in {detailed_time:.0f}ms[/green]")
    console.print(f"[green]✓ Model: {detailed_result['model_used']}[/green]\n")

    # Show categories
    details = detailed_result['details']
    console.print("[yellow]Categories available to user:[/yellow]")
    for category, text in details.items():
        word_count = len(text.split())
        console.print(f"  • {category.replace('_', ' ').title()}: {word_count} words")

    console.print("\n[dim]iOS loads these in background while user reads summary[/dim]")

    # =========================================================================
    # Step 5: Create Journal Entry
    # =========================================================================
    print_section("5️⃣  USER READS HOROSCOPE → CREATE JOURNAL ENTRY", "bold cyan")

    console.print("[cyan]Simulating user reading Love and Career sections...[/cyan]")
    console.print(f"[cyan]Calling: add_journal_entry()[/cyan]\n")

    # User reads 2 categories
    categories_viewed = [
        {
            "category": "love_relationships",
            "text": details['love_relationships']
        },
        {
            "category": "path_profession",
            "text": details['path_profession']
        }
    ]

    journal_result = call_function("add_journal_entry", {
        "user_id": TEST_USER_ID,
        "date": daily_result['date'],
        "entry_type": "horoscope_reading",
        "summary_viewed": daily_result['summary'],
        "categories_viewed": categories_viewed,
        "time_spent_seconds": 180
    })

    entry_id = journal_result['entry_id']

    console.print(f"[green]✓ Journal entry created: {entry_id}[/green]")
    console.print(f"[green]✓ Categories read: {len(categories_viewed)}[/green]")
    console.print(f"[green]✓ Time spent: 180s[/green]")

    # =========================================================================
    # Step 6: Wait for Trigger & Verify Memory
    # =========================================================================
    print_section("6️⃣  FIRESTORE TRIGGER: VERIFY MEMORY UPDATE", "bold cyan")

    console.print("[cyan]Waiting for trigger: update_memory_on_journal_entry()[/cyan]")
    console.print("[dim]Trigger should fire automatically when journal entry is created...[/dim]\n")

    # Wait a bit for trigger to fire
    time.sleep(2)

    # Get memory to verify it was updated
    console.print(f"[cyan]Calling: get_memory()[/cyan]\n")
    memory_result = call_function("get_memory", {
        "user_id": TEST_USER_ID
    })

    console.print(f"[green]✓ Memory collection exists[/green]\n")

    # Show what changed
    console.print("[yellow]Category Engagement Updated:[/yellow]")
    categories = memory_result['categories']
    for cat_name, cat_data in categories.items():
        if cat_data['count'] > 0:
            console.print(f"  • {cat_name.replace('_', ' ').title()}: {cat_data['count']} views (last: {cat_data['last_mentioned']})")

    recent_readings = memory_result['recent_readings']
    console.print(f"\n[yellow]Recent Readings:[/yellow] {len(recent_readings)} reading(s)")
    if recent_readings:
        reading = recent_readings[0]
        console.print(f"  • {reading['date']}: {len(reading['categories_viewed'])} categories viewed")

    # =========================================================================
    # Step 7: Verification
    # =========================================================================
    print_section("7️⃣  VERIFICATION", "bold cyan")

    # Verify profile exists
    profile_result = call_function("get_user_profile", {
        "user_id": TEST_USER_ID
    })
    console.print(f"[green]✓ User profile exists in Firestore[/green]")

    # Verify memory was updated
    assert categories['love_relationships']['count'] == 1, "Love category should have 1 view"
    assert categories['path_profession']['count'] == 1, "Career category should have 1 view"
    assert len(recent_readings) == 1, "Should have 1 recent reading"

    console.print(f"[green]✓ Memory collection updated correctly[/green]")
    console.print(f"  Love views: {categories['love_relationships']['count']}")
    console.print(f"  Career views: {categories['path_profession']['count']}")
    console.print(f"[green]✓ Journal entry stored[/green]")

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

    console.print("\n[bold green]✅ All Firebase Functions working correctly:[/bold green]")
    console.print("[green]  • get_sun_sign_from_date()[/green]")
    console.print("[green]  • create_user_profile()[/green]")
    console.print("[green]  • get_daily_horoscope()[/green]")
    console.print("[green]  • get_detailed_horoscope()[/green]")
    console.print("[green]  • add_journal_entry()[/green]")
    console.print("[green]  • get_memory()[/green]")
    console.print("[green]  • update_memory_on_journal_entry() [trigger][/green]")

    console.print("\n[bold cyan]📱 Backend ready for iOS app integration![/bold cyan]")


if __name__ == "__main__":
    # Check for GEMINI_API_KEY
    if "GEMINI_API_KEY" not in os.environ:
        console.print("[bold red]❌ Error: GEMINI_API_KEY environment variable not set[/bold red]")
        console.print("Set it with: export GEMINI_API_KEY='your-key-here'")
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

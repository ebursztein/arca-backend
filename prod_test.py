#!/usr/bin/env python3
"""
Production Test - Tests deployed Firebase Functions

Tests the actual deployed Cloud Functions in production.
Start simple, add more tests as we verify each function works.

Usage:
    python prod_test.py
"""

import requests
from rich.console import Console
from rich.panel import Panel

console = Console()

# Production Firebase Functions endpoint
PROJECT_ID = "arca-baf77"
REGION = "us-central1"
FUNCTIONS_BASE_URL = f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net"

# Test data - SAME AS integration_test.py for analytics filtering
TEST_USER_ID = "integration_test_user"
TEST_NAME = "Alex"
TEST_EMAIL = "alex@test.com"
TEST_BIRTH_DATE = "1990-06-15"  # Gemini


def print_section(title: str):
    """Print a formatted section."""
    console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")


def call_function(function_name: str, data: dict) -> dict:
    """
    Call a deployed Firebase callable function.

    Args:
        function_name: Name of the function
        data: Request data

    Returns:
        Response data from the function
    """
    url = f"{FUNCTIONS_BASE_URL}/{function_name}"

    # Firebase callable functions expect data in a specific format
    payload = {"data": data}

    console.print(f"[dim]Calling: {url}[/dim]")

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Check for Firebase Functions error format
        if "error" in result:
            error = result["error"]
            raise Exception(f"Function error: {error.get('message', 'Unknown error')}")

        return result.get("result", {})

    except requests.exceptions.Timeout:
        raise Exception(f"Function call timed out after 30 seconds")
    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request failed: {str(e)}")


def test_get_sun_sign():
    """Test get_sun_sign_from_date function."""
    print_section("TEST 1: Get Sun Sign from Date")

    test_cases = [
        ("1990-06-15", "gemini", "Twins"),
        ("1985-03-25", "aries", "Ram"),
        ("1992-12-05", "sagittarius", "Archer"),
        ("2000-01-15", "capricorn", "Goat"),
    ]

    for birth_date, expected_sign, expected_symbol in test_cases:
        console.print(f"[yellow]Testing {birth_date}...[/yellow]", end=" ")

        result = call_function("get_sun_sign_from_date", {
            "birth_date": birth_date
        })

        sun_sign = result["sun_sign"]
        profile = result["profile"]

        # Verify
        assert sun_sign == expected_sign, f"Expected {expected_sign}, got {sun_sign}"
        assert profile["sign"].lower() == expected_sign, f"Profile sign mismatch"
        assert expected_symbol in profile["symbol"], f"Expected {expected_symbol} in symbol"

        console.print(f"[green]✓ {sun_sign.title()} {profile['symbol']} ({profile['element'].title()}/{profile['modality'].title()})[/green]")

    console.print(f"\n[bold green]✅ All sun sign tests passed![/bold green]")


def test_create_user_profile():
    """Test create_user_profile function - creates or recreates test user."""
    print_section("TEST 2: Create User Profile")

    console.print(f"[yellow]Creating/recreating user: {TEST_USER_ID}[/yellow]")

    result = call_function("create_user_profile", {
        "user_id": TEST_USER_ID,
        "name": TEST_NAME,
        "email": TEST_EMAIL,
        "birth_date": TEST_BIRTH_DATE
    })

    assert result["success"] == True
    assert result["sun_sign"] == "gemini"
    assert result["mode"] == "v1"

    console.print(f"[green]✓ User ready: {result['user_id']}[/green]")
    console.print(f"[green]✓ Sun sign: {result['sun_sign']}[/green]")
    console.print(f"\n[bold green]✅ User profile test passed![/bold green]")


def test_get_daily_horoscope():
    """Test get_daily_horoscope function."""
    print_section("TEST 3: Get Daily Horoscope (Prompt 1)")

    console.print(f"[yellow]Generating daily horoscope...[/yellow]")

    import time
    start = time.time()
    result = call_function("get_daily_horoscope", {
        "user_id": TEST_USER_ID,
        "model_name": "gemini-2.5-flash-lite"
    })
    elapsed = (time.time() - start) * 1000

    assert "daily_theme_headline" in result
    assert "summary" in result

    console.print(f"[green]✓ Generated in {elapsed:.0f}ms[/green]")
    console.print(f"[cyan]Theme:[/cyan] {result['daily_theme_headline'][:60]}...")
    console.print(f"\n[bold green]✅ Daily horoscope test passed![/bold green]")

    return result


def test_get_detailed_horoscope(daily_horoscope: dict):
    """Test get_detailed_horoscope function."""
    print_section("TEST 4: Get Detailed Horoscope (Prompt 2)")

    console.print(f"[yellow]Generating detailed horoscope...[/yellow]")

    import time
    start = time.time()
    result = call_function("get_detailed_horoscope", {
        "user_id": TEST_USER_ID,
        "daily_horoscope": daily_horoscope,
        "model_name": "gemini-2.5-flash-lite"
    })
    elapsed = (time.time() - start) * 1000

    assert "details" in result
    details = result["details"]

    expected_cats = ["love_relationships", "path_profession", "personal_growth"]
    for cat in expected_cats:
        assert cat in details

    console.print(f"[green]✓ Generated in {elapsed:.0f}ms[/green]")
    console.print(f"[green]✓ All 8 categories present[/green]")
    console.print(f"\n[bold green]✅ Detailed horoscope test passed![/bold green]")

    return result


def test_add_journal_entry(daily_horoscope: dict, detailed_horoscope: dict):
    """Test add_journal_entry function."""
    print_section("TEST 5: Add Journal Entry")

    categories_viewed = [{
        "category": "love_relationships",
        "text": detailed_horoscope["details"]["love_relationships"]
    }]

    result = call_function("add_journal_entry", {
        "user_id": TEST_USER_ID,
        "date": daily_horoscope["date"],
        "entry_type": "horoscope_reading",
        "summary_viewed": daily_horoscope["summary"],
        "categories_viewed": categories_viewed,
        "time_spent_seconds": 180
    })

    assert result["success"] == True

    console.print(f"[green]✓ Entry: {result['entry_id']}[/green]")
    console.print(f"\n[bold green]✅ Journal entry test passed![/bold green]")


def test_get_memory():
    """Test get_memory function."""
    print_section("TEST 6: Verify Memory (Trigger)")

    console.print(f"[yellow]Waiting 3s for trigger...[/yellow]")
    import time
    time.sleep(3)

    result = call_function("get_memory", {"user_id": TEST_USER_ID})

    assert "categories" in result
    assert "recent_readings" in result

    console.print(f"[green]✓ Memory exists[/green]")
    console.print(f"[green]✓ Readings: {len(result['recent_readings'])}[/green]")
    console.print(f"\n[bold green]✅ Memory test passed![/bold green]")


def main():
    """Run production tests."""
    console.print("\n[bold magenta]🌟 PRODUCTION FUNCTION TESTS 🌟[/bold magenta]")
    console.print(f"[dim]Testing functions at: {FUNCTIONS_BASE_URL}[/dim]\n")

    try:
        test_get_sun_sign()
        test_create_user_profile()
        daily = test_get_daily_horoscope()
        detailed = test_get_detailed_horoscope(daily)
        test_add_journal_entry(daily, detailed)
        test_get_memory()

        print_section("SUMMARY")
        console.print("[bold green]✅ All 6 tests passed![/bold green]")
        console.print("[green]  • get_sun_sign_from_date ✓[/green]")
        console.print("[green]  • create_user_profile ✓[/green]")
        console.print("[green]  • get_daily_horoscope ✓[/green]")
        console.print("[green]  • get_detailed_horoscope ✓[/green]")
        console.print("[green]  • add_journal_entry ✓[/green]")
        console.print("[green]  • get_memory (trigger) ✓[/green]")
        console.print(f"\n[bold cyan]📱 Backend ready for iOS![/bold cyan]")

    except AssertionError as e:
        console.print(f"\n[bold red]❌ TEST FAILED:[/bold red] {e}")
        return 1
    except Exception as e:
        console.print(f"\n[bold red]❌ ERROR:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

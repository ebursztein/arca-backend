#!/usr/bin/env python3
"""
Test PostHog LLM Analytics - Call Firebase Function via emulator
"""

import os
import requests
from rich.console import Console

console = Console()

# Firebase Functions emulator endpoint
FUNCTIONS_EMULATOR_HOST = "http://127.0.0.1:5001"
PROJECT_ID = "arca-baf77"
REGION = "us-central1"
FUNCTIONS_BASE_URL = f"{FUNCTIONS_EMULATOR_HOST}/{PROJECT_ID}/{REGION}"

# Test user
TEST_USER_ID = "test_posthog_user"


def call_function(function_name: str, data: dict) -> dict:
    """Call a Firebase callable function via the emulator."""
    url = f"{FUNCTIONS_BASE_URL}/{function_name}"
    payload = {"data": data}

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            error = result["error"]
            raise Exception(f"Function error: {error.get('message', 'Unknown error')}")

        return result.get("result", {})

    except requests.exceptions.RequestException as e:
        raise Exception(f"HTTP request failed: {str(e)}")


def main():
    console.print("\n[bold magenta]🧪 PostHog LLM Analytics Test[/bold magenta]\n")

    # Check emulator is running
    try:
        requests.get(FUNCTIONS_EMULATOR_HOST, timeout=5)
        console.print("[green]✓ Firebase Functions emulator is running[/green]\n")
    except:
        console.print("[bold red]❌ Error: Firebase Functions emulator not running[/bold red]")
        console.print("Start it with: firebase emulators:start")
        exit(1)

    # Ensure user exists
    console.print(f"[cyan]Setting up test user: {TEST_USER_ID}[/cyan]\n")
    call_function("create_user_profile", {
        "user_id": TEST_USER_ID,
        "name": "PostHog Test",
        "email": "test@posthog.com",
        "birth_date": "1990-06-15"
    })

    # Generate daily horoscope (this should capture to PostHog)
    console.print(f"[cyan]Generating daily horoscope...[/cyan]")
    console.print(f"[yellow]Watch the emulator logs for PostHog output![/yellow]\n")

    result = call_function("get_daily_horoscope", {
        "user_id": TEST_USER_ID,
    })

    console.print(f"\n[green]✓ Generated successfully![/green]")
    console.print(f"[green]  Model: {result['model_used']}[/green]")
    console.print(f"[green]  Time: {result['generation_time_ms']}ms[/green]")
    console.print(f"[green]  Theme: {result['daily_theme_headline'][:60]}...[/green]\n")

    console.print(f"[bold cyan]📊 Check your PostHog dashboard for the $ai_generation event![/bold cyan]")
    console.print(f"[dim]   User: {TEST_USER_ID}[/dim]")
    console.print(f"[dim]   Provider: gemini[/dim]")
    console.print(f"[dim]   Model: {result['model_used']}[/dim]\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[bold red]❌ ERROR:[/bold red] {e}")
        exit(1)

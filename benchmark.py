#!/usr/bin/env python3
"""
Production Benchmark - Measure actual performance of deployed Firebase Functions

Tests each function 10 times and reports statistics:
- Mean, median, min, max, p95, p99
- Success rate
- Error types

Usage:
    python benchmark.py
"""

import requests
import time
import statistics
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

# Production Firebase Functions endpoint
PROJECT_ID = "arca-baf77"
REGION = "us-central1"
FUNCTIONS_BASE_URL = f"https://{REGION}-{PROJECT_ID}.cloudfunctions.net"

# Test data
TEST_USER_ID = "integration_test_user"
TEST_NAME = "Alex"
TEST_EMAIL = "alex@test.com"
TEST_BIRTH_DATE = "1990-06-15"

# Number of iterations per function
ITERATIONS = 10


def call_function(function_name: str, data: dict, timeout: int = 120) -> tuple[dict | None, float, str | None]:
    """
    Call a Firebase callable function and measure time.

    Returns:
        (result, elapsed_ms, error_message)
    """
    url = f"{FUNCTIONS_BASE_URL}/{function_name}"
    payload = {"data": data}

    start = time.time()
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        elapsed_ms = (time.time() - start) * 1000

        response.raise_for_status()
        result = response.json()

        if "error" in result:
            error = result["error"]
            return None, elapsed_ms, error.get("message", "Unknown error")

        return result.get("result", {}), elapsed_ms, None

    except requests.exceptions.Timeout:
        elapsed_ms = (time.time() - start) * 1000
        return None, elapsed_ms, f"TIMEOUT (>{timeout}s)"
    except requests.exceptions.RequestException as e:
        elapsed_ms = (time.time() - start) * 1000
        return None, elapsed_ms, str(e)


def benchmark_function(name: str, data: dict, iterations: int = ITERATIONS) -> dict:
    """
    Benchmark a function with multiple iterations.

    Returns:
        {
            "times": [ms, ms, ...],
            "successes": int,
            "failures": int,
            "errors": [error_msg, ...]
        }
    """
    times = []
    errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]Benchmarking {name}...", total=iterations)

        for i in range(iterations):
            result, elapsed_ms, error = call_function(name, data)

            if error:
                errors.append(error)
            else:
                times.append(elapsed_ms)

            progress.update(task, advance=1)

    return {
        "times": times,
        "successes": len(times),
        "failures": len(errors),
        "errors": errors,
    }


def calculate_stats(times: list[float]) -> dict:
    """Calculate statistics from timing data."""
    if not times:
        return {
            "mean": 0,
            "median": 0,
            "min": 0,
            "max": 0,
            "p95": 0,
            "p99": 0,
        }

    times_sorted = sorted(times)
    n = len(times_sorted)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "p95": times_sorted[int(n * 0.95)] if n > 1 else times_sorted[0],
        "p99": times_sorted[int(n * 0.99)] if n > 1 else times_sorted[0],
    }


def print_results(function_name: str, results: dict):
    """Print benchmark results for a function."""
    stats = calculate_stats(results["times"])

    table = Table(title=f"📊 {function_name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="magenta")

    # Success rate
    total = results["successes"] + results["failures"]
    success_rate = (results["successes"] / total * 100) if total > 0 else 0
    table.add_row("Success Rate", f"{success_rate:.1f}% ({results['successes']}/{total})")

    # Timing stats (only if we have successful calls)
    if results["successes"] > 0:
        table.add_row("Mean", f"{stats['mean']:.0f}ms")
        table.add_row("Median", f"{stats['median']:.0f}ms")
        table.add_row("Min", f"{stats['min']:.0f}ms")
        table.add_row("Max", f"{stats['max']:.0f}ms")
        table.add_row("P95", f"{stats['p95']:.0f}ms")
        table.add_row("P99", f"{stats['p99']:.0f}ms")

    console.print(table)

    # Print errors if any
    if results["errors"]:
        console.print(f"\n[red]❌ Errors ({len(results['errors'])}):[/red]")
        for error in set(results["errors"]):
            count = results["errors"].count(error)
            console.print(f"  • {error} ({count}x)")

    console.print()


def main():
    """Run production benchmarks."""
    console.print("\n[bold magenta]🔥 PRODUCTION PERFORMANCE BENCHMARK 🔥[/bold magenta]")
    console.print(f"[dim]Testing: {FUNCTIONS_BASE_URL}[/dim]")
    console.print(f"[dim]Iterations per function: {ITERATIONS}[/dim]\n")

    # Benchmark 1: get_sun_sign_from_date (fast, no LLM)
    console.print("[bold cyan]1️⃣  get_sun_sign_from_date[/bold cyan]")
    results_sun_sign = benchmark_function("get_sun_sign_from_date", {"birth_date": TEST_BIRTH_DATE})
    print_results("get_sun_sign_from_date", results_sun_sign)

    # Benchmark 2: create_user_profile (one-time, includes chart calc)
    console.print("[bold cyan]2️⃣  create_user_profile[/bold cyan]")
    results_create = benchmark_function(
        "create_user_profile",
        {
            "user_id": TEST_USER_ID,
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "birth_date": TEST_BIRTH_DATE,
        },
    )
    print_results("create_user_profile", results_create)

    # Benchmark 3: get_daily_horoscope (CRITICAL - main screen, LLM)
    console.print("[bold cyan]3️⃣  get_daily_horoscope (CRITICAL - main screen)[/bold cyan]")
    results_daily = benchmark_function(
        "get_daily_horoscope",
        {"user_id": TEST_USER_ID, "model_name": "gemini-2.5-flash-lite"},
    )
    print_results("get_daily_horoscope", results_daily)

    # Benchmark 4: get_detailed_horoscope (background load, LLM)
    console.print("[bold cyan]4️⃣  get_detailed_horoscope (background load)[/bold cyan]")

    # Get a fresh daily horoscope for detailed benchmark
    daily_result, _, _ = call_function(
        "get_daily_horoscope",
        {"user_id": TEST_USER_ID, "model_name": "gemini-2.5-flash-lite"},
    )


    if daily_result:
        results_detailed = benchmark_function(
            "get_detailed_horoscope",
            {
                "user_id": TEST_USER_ID,
                "daily_horoscope": daily_result,
                "model_name": "gemini-2.5-flash-lite",
            },
        )
        print_results("get_detailed_horoscope", results_detailed)
    else:
        console.print("[red]❌ Skipped - could not get daily horoscope[/red]\n")

    # Benchmark 5: add_journal_entry (fast, DB write)
    console.print("[bold cyan]5️⃣  add_journal_entry[/bold cyan]")
    results_journal = benchmark_function(
        "add_journal_entry",
        {
            "user_id": TEST_USER_ID,
            "date": "2025-10-19",
            "entry_type": "horoscope_reading",
            "summary_viewed": "Test summary",
            "categories_viewed": [{"category": "love_relationships", "text": "Test text"}],
            "time_spent_seconds": 60,
        },
    )
    print_results("add_journal_entry", results_journal)

    # Benchmark 6: get_memory (fast, DB read)
    console.print("[bold cyan]6️⃣  get_memory[/bold cyan]")
    results_memory = benchmark_function("get_memory", {"user_id": TEST_USER_ID})
    print_results("get_memory", results_memory)

    # Summary table
    console.print("\n[bold magenta]📈 SUMMARY[/bold magenta]\n")

    summary_table = Table(title="Performance Summary")
    summary_table.add_column("Function", style="cyan")
    summary_table.add_column("Median", justify="right", style="magenta")
    summary_table.add_column("P95", justify="right", style="yellow")
    summary_table.add_column("Success Rate", justify="right", style="green")
    summary_table.add_column("Status", justify="center")

    all_results = [
        ("get_sun_sign_from_date", results_sun_sign, 1000, "Fast"),
        ("create_user_profile", results_create, 2000, "One-time"),
        ("get_daily_horoscope", results_daily, 3000, "CRITICAL"),
        ("get_detailed_horoscope", results_detailed, 5000, "On demand"),
        ("add_journal_entry", results_journal, 1000, "Fast"),
        ("get_memory", results_memory, 1000, "Fast"),
    ]

    for name, results, target, note in all_results:
        stats = calculate_stats(results["times"])
        total = results["successes"] + results["failures"]
        success_rate = (results["successes"] / total * 100) if total > 0 else 0

        # Status indicator
        if results["successes"] == 0:
            status = "❌"
        elif stats["median"] > target * 5:
            status = "🔴"
        elif stats["median"] > target * 2:
            status = "🟡"
        else:
            status = "🟢"

        summary_table.add_row(
            f"{name}\n[dim]{note}[/dim]",
            f"{stats['median']:.0f}ms",
            f"{stats['p95']:.0f}ms",
            f"{success_rate:.0f}%",
            status,
        )

    console.print(summary_table)

    # Critical findings
    console.print("\n[bold yellow]⚠️  CRITICAL FINDINGS:[/bold yellow]")

    daily_stats = calculate_stats(results_daily["times"])
    if daily_stats["median"] > 2000:
        console.print(
            f"[red]• get_daily_horoscope median: {daily_stats['median']:.0f}ms "
            f"(target: <2000ms, {daily_stats['median']/2000:.1f}x slower)[/red]"
        )
        console.print("[yellow]  → Main screen will show 10+ second loading state[/yellow]")
        console.print("[yellow]  → MUST implement proper loading UX (skeleton, progressive messages)[/yellow]")

    console.print("\n[bold green]✅ Benchmark complete![/bold green]")
    console.print("[dim]These are real production measurements, not targets.[/dim]\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Benchmark interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ ERROR:[/red] {e}")
        import traceback
        console.print(traceback.format_exc())

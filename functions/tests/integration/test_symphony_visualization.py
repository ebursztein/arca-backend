"""
Symphony Visualization - Planetary Signal Over Time

Visualizes how different planetary tiers contribute to the overall
astrological "signal" over time, like viewing a musical composition.

- Trigger (Moon): The melody - high frequency, high amplitude spikes
- Event (Sun/Mercury/Venus/Mars): The mid-range - weekly rhythm
- Season (Jupiter/Saturn): The background - monthly context
- Era (Uranus/Neptune/Pluto): The bass - deep, constant hum

Usage:
    uv run python functions/tests/integration/test_symphony_visualization.py
    uv run python functions/tests/integration/test_symphony_visualization.py --days 90 --output symphony.png
"""

import sys
import os
import json
import random
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from astro import compute_birth_chart, find_natal_transit_aspects, Planet, AspectType
from astrometers.transit_power import calculate_velocity_score, calculate_gaussian_score
from astrometers.constants import TRANSIT_TIERS, PLANET_TO_TIER, get_transit_tier


CITIES = [
    ("New York", 40.7128, -74.0060, "America/New_York"),
    ("Los Angeles", 34.0522, -118.2437, "America/Los_Angeles"),
    ("Chicago", 41.8781, -87.6298, "America/Chicago"),
    ("London", 51.5074, -0.1278, "Europe/London"),
    ("Paris", 48.8566, 2.3522, "Europe/Paris"),
    ("Tokyo", 35.6762, 139.6503, "Asia/Tokyo"),
    ("Sydney", -33.8688, 151.2093, "Australia/Sydney"),
    ("Berlin", 52.5200, 13.4050, "Europe/Berlin"),
    ("Mumbai", 19.0760, 72.8777, "Asia/Kolkata"),
    ("Sao Paulo", -23.5505, -46.6333, "America/Sao_Paulo"),
]


def generate_random_birth_data() -> dict:
    """Generate random birth data."""
    start_date = datetime(1960, 1, 1)
    end_date = datetime(2005, 12, 31)
    days_range = (end_date - start_date).days
    random_date = start_date + timedelta(days=random.randint(0, days_range))

    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    city_name, lat, lon, tz = random.choice(CITIES)

    return {
        "birth_date": random_date.strftime("%Y-%m-%d"),
        "birth_time": f"{hour:02d}:{minute:02d}",
        "birth_lat": lat,
        "birth_lon": lon,
        "birth_timezone": tz,
    }


def get_planet_speed(chart: dict, planet_name: str) -> float:
    """Extract planet speed from chart data."""
    for p in chart.get('planets', []):
        if p['name'].lower() == planet_name.lower():
            return abs(p.get('speed', 1.0))
    return 1.0  # Default fallback


def calculate_daily_symphony(
    natal_chart: dict,
    transit_date: datetime,
) -> dict:
    """
    Calculate the symphony breakdown for a single day.

    Returns:
        dict with tier scores and aspect details
    """
    transit_chart, _ = compute_birth_chart(
        transit_date.strftime('%Y-%m-%d'),
        '12:00'
    )

    # Find all natal-transit aspects (use wide orb to catch everything)
    aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=15.0)

    tier_scores = {tier: 0.0 for tier in TRANSIT_TIERS.keys()}
    aspect_details = []

    for asp in aspects:
        transit_planet = Planet(asp.transit_planet)
        speed = get_planet_speed(transit_chart, asp.transit_planet)

        score, breakdown = calculate_velocity_score(
            transit_planet=transit_planet,
            deviation_deg=asp.orb,
            transit_speed=speed,
            aspect_type=asp.aspect_type,
        )

        if score > 0:
            tier = breakdown['tier']
            tier_scores[tier] += score

            aspect_details.append({
                'transit': asp.transit_planet,
                'natal': asp.natal_planet,
                'aspect': asp.aspect_type.value,
                'orb': asp.orb,
                'score': score,
                'tier': tier,
                'days_from_exact': breakdown['days_from_exact'],
            })

    return {
        'date': transit_date.strftime('%Y-%m-%d'),
        'tier_scores': tier_scores,
        'total': sum(tier_scores.values()),
        'aspects': aspect_details,
    }


def run_symphony_analysis(
    natal_birth_date: str = '1990-06-15',
    natal_birth_time: str = '14:30',
    start_date: Optional[str] = None,
    days: int = 60,
    output_file: Optional[str] = None,
    plot_file: Optional[str] = None,
) -> dict:
    """
    Run symphony analysis over a time period.

    Args:
        natal_birth_date: Birth date for natal chart
        natal_birth_time: Birth time for natal chart
        start_date: Start date for analysis (default: today - days/2)
        days: Number of days to analyze
        output_file: Optional JSON file to save data
        plot_file: Optional PNG file to save plot

    Returns:
        dict with full analysis results
    """
    print(f"\n{'='*80}")
    print("SYMPHONY VISUALIZATION - Planetary Signal Over Time")
    print(f"{'='*80}")

    # Generate natal chart
    print(f"\nNatal chart: {natal_birth_date} {natal_birth_time}")
    natal_chart, _ = compute_birth_chart(natal_birth_date, natal_birth_time)

    # Determine date range
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start = datetime.now() - timedelta(days=days // 2)

    print(f"Analyzing {days} days from {start.strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")

    # Collect daily data
    daily_data = []

    for i in range(days):
        current_date = start + timedelta(days=i)
        day_result = calculate_daily_symphony(natal_chart, current_date)
        daily_data.append(day_result)

        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{days} days...")

    # Calculate statistics
    tier_stats = {tier: [] for tier in TRANSIT_TIERS.keys()}
    totals = []

    for day in daily_data:
        for tier, score in day['tier_scores'].items():
            tier_stats[tier].append(score)
        totals.append(day['total'])

    print(f"\n{'='*80}")
    print("TIER CONTRIBUTION STATISTICS")
    print(f"{'='*80}")
    print(f"\n{'Tier':<12} {'Mean':>10} {'Min':>10} {'Max':>10} {'% of Total':>12}")
    print("-" * 60)

    total_mean = sum(totals) / len(totals) if totals else 1

    for tier in ['trigger', 'event', 'season', 'era']:
        scores = tier_stats[tier]
        if scores:
            mean = sum(scores) / len(scores)
            min_s = min(scores)
            max_s = max(scores)
            pct = (mean / total_mean * 100) if total_mean > 0 else 0
            print(f"{tier:<12} {mean:>10.1f} {min_s:>10.1f} {max_s:>10.1f} {pct:>11.1f}%")

    print("-" * 60)
    print(f"{'TOTAL':<12} {total_mean:>10.1f} {min(totals):>10.1f} {max(totals):>10.1f}")

    # Day-to-day variation analysis
    print(f"\n{'='*80}")
    print("DAY-TO-DAY VARIATION")
    print(f"{'='*80}")

    daily_deltas = []
    for i in range(1, len(totals)):
        daily_deltas.append(abs(totals[i] - totals[i-1]))

    if daily_deltas:
        avg_delta = sum(daily_deltas) / len(daily_deltas)
        max_delta = max(daily_deltas)
        print(f"\nAverage daily change: {avg_delta:.1f}")
        print(f"Maximum daily change: {max_delta:.1f}")
        print(f"Variation coefficient: {avg_delta / total_mean * 100:.1f}%")

    # Find peak days
    print(f"\n{'='*80}")
    print("NOTABLE DAYS")
    print(f"{'='*80}")

    # Sort by total score
    sorted_days = sorted(daily_data, key=lambda x: x['total'], reverse=True)

    print("\nTop 5 highest signal days:")
    for day in sorted_days[:5]:
        tiers = day['tier_scores']
        print(f"  {day['date']}: {day['total']:.1f} "
              f"(T:{tiers['trigger']:.0f} E:{tiers['event']:.0f} "
              f"S:{tiers['season']:.0f} R:{tiers['era']:.0f})")

    print("\nTop 5 lowest signal days:")
    for day in sorted_days[-5:]:
        tiers = day['tier_scores']
        print(f"  {day['date']}: {day['total']:.1f} "
              f"(T:{tiers['trigger']:.0f} E:{tiers['event']:.0f} "
              f"S:{tiers['season']:.0f} R:{tiers['era']:.0f})")

    # ASCII visualization
    print(f"\n{'='*80}")
    print("SIGNAL OVER TIME (ASCII)")
    print(f"{'='*80}")
    print("\nLegend: T=Trigger(Moon) E=Event(Inner) S=Season(Social) R=Era(Outer)")
    print()

    # Normalize for ASCII display
    max_total = max(totals) if totals else 1
    width = 60

    for i, day in enumerate(daily_data):
        if i % 3 == 0:  # Show every 3rd day for readability
            date_str = day['date'][5:]  # MM-DD
            total = day['total']
            bar_len = int((total / max_total) * width)

            # Build stacked bar
            t_len = int((day['tier_scores']['trigger'] / max_total) * width)
            e_len = int((day['tier_scores']['event'] / max_total) * width)
            s_len = int((day['tier_scores']['season'] / max_total) * width)
            r_len = int((day['tier_scores']['era'] / max_total) * width)

            bar = 'T' * t_len + 'E' * e_len + 'S' * s_len + 'R' * r_len
            bar = bar[:width]  # Truncate if needed

            print(f"{date_str} |{bar}")

    # Save data if requested
    if output_file:
        output_data = {
            'natal': {'birth_date': natal_birth_date, 'birth_time': natal_birth_time},
            'analysis_period': {'start': start.strftime('%Y-%m-%d'), 'days': days},
            'tier_config': {
                tier: {'window_days': t.window_days, 'weight': t.weight}
                for tier, t in TRANSIT_TIERS.items()
            },
            'daily_data': daily_data,
            'statistics': {
                'tier_means': {tier: sum(scores)/len(scores) if scores else 0
                              for tier, scores in tier_stats.items()},
                'total_mean': total_mean,
                'avg_daily_delta': avg_delta if daily_deltas else 0,
            }
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nData saved to: {output_file}")

    # Generate matplotlib plot if requested
    if plot_file:
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[3, 1])

            dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in daily_data]

            # Stacked area chart
            trigger = [d['tier_scores']['trigger'] for d in daily_data]
            event = [d['tier_scores']['event'] for d in daily_data]
            season = [d['tier_scores']['season'] for d in daily_data]
            era = [d['tier_scores']['era'] for d in daily_data]

            ax1.stackplot(dates, era, season, event, trigger,
                         labels=['Era (Outer)', 'Season (Social)', 'Event (Inner)', 'Trigger (Moon)'],
                         colors=['#2c3e50', '#3498db', '#e74c3c', '#f39c12'],
                         alpha=0.8)

            ax1.set_ylabel('Signal Strength')
            ax1.set_title(f'Planetary Symphony - {natal_birth_date}')
            ax1.legend(loc='upper right')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            ax1.grid(True, alpha=0.3)

            # Daily delta chart
            delta_dates = dates[1:]
            ax2.bar(delta_dates, daily_deltas, color='#9b59b6', alpha=0.7, width=0.8)
            ax2.set_ylabel('Daily Change')
            ax2.set_xlabel('Date')
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            ax2.axhline(y=avg_delta, color='red', linestyle='--', label=f'Avg: {avg_delta:.1f}')
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(plot_file, dpi=150)
            print(f"Plot saved to: {plot_file}")
            plt.close()

        except ImportError:
            print("\nNote: Install matplotlib for graphical plots: uv add matplotlib")

    return {
        'daily_data': daily_data,
        'tier_stats': tier_stats,
        'totals': totals,
    }


def compare_old_vs_new_scoring(
    natal_birth_date: str = '1990-06-15',
    natal_birth_time: str = '14:30',
    days: int = 30,
):
    """
    Compare old static orb scoring vs new velocity-based scoring.
    Shows how day-to-day variation changes.
    """
    from astrometers.transit_power import calculate_orb_factor
    from astrometers.constants import TRANSIT_PLANET_WEIGHTS, ASPECT_BASE_INTENSITY

    print(f"\n{'='*80}")
    print("OLD vs NEW SCORING COMPARISON")
    print(f"{'='*80}")

    natal_chart, _ = compute_birth_chart(natal_birth_date, natal_birth_time)
    start = datetime.now() - timedelta(days=days // 2)

    old_totals = []
    new_totals = []

    for i in range(days):
        current_date = start + timedelta(days=i)
        transit_chart, _ = compute_birth_chart(
            current_date.strftime('%Y-%m-%d'), '12:00'
        )

        aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=10.0)

        old_total = 0.0
        new_total = 0.0

        for asp in aspects:
            transit_planet = Planet(asp.transit_planet)
            speed = get_planet_speed(transit_chart, asp.transit_planet)

            # Old scoring (static orb)
            orb_factor = calculate_orb_factor(asp.orb, 8.0)
            old_weight = TRANSIT_PLANET_WEIGHTS.get(transit_planet, 1.0)
            aspect_base = ASPECT_BASE_INTENSITY[asp.aspect_type]
            old_score = orb_factor * old_weight * aspect_base
            old_total += old_score

            # New scoring (velocity-based)
            new_score, _ = calculate_velocity_score(
                transit_planet, asp.orb, speed, asp.aspect_type
            )
            new_total += new_score

        old_totals.append(old_total)
        new_totals.append(new_total)

    # Calculate day-to-day deltas
    old_deltas = [abs(old_totals[i] - old_totals[i-1]) for i in range(1, len(old_totals))]
    new_deltas = [abs(new_totals[i] - new_totals[i-1]) for i in range(1, len(new_totals))]

    old_mean = sum(old_totals) / len(old_totals)
    new_mean = sum(new_totals) / len(new_totals)
    old_delta_avg = sum(old_deltas) / len(old_deltas) if old_deltas else 0
    new_delta_avg = sum(new_deltas) / len(new_deltas) if new_deltas else 0

    print(f"\n{'Metric':<30} {'Old (Static)':>15} {'New (Velocity)':>15}")
    print("-" * 62)
    print(f"{'Mean total score':<30} {old_mean:>15.1f} {new_mean:>15.1f}")
    print(f"{'Avg daily delta':<30} {old_delta_avg:>15.1f} {new_delta_avg:>15.1f}")
    print(f"{'Variation coefficient':<30} {old_delta_avg/old_mean*100:>14.1f}% {new_delta_avg/new_mean*100:>14.1f}%")
    print(f"{'Max daily delta':<30} {max(old_deltas):>15.1f} {max(new_deltas):>15.1f}")

    improvement = ((new_delta_avg / new_mean) / (old_delta_avg / old_mean) - 1) * 100
    print(f"\nVariation improvement: {improvement:+.1f}%")

    return old_totals, new_totals


def compare_mixing_profiles(
    n_charts: int = 100,
    days_per_chart: int = 30,
    seed: int = 42,
):
    """
    Compare all three mixing profiles across many random charts.

    Aggregates results across n_charts to get statistically meaningful
    tier distributions and variation metrics.

    Profiles:
    - daily_pulse: Moon dominates (~50%), high daily variance
    - deep_current: Balanced (~30/30/20/20), psychological accuracy
    - forecast: Event-focused (~20/50/30), external happenings
    """
    from astrometers.constants import set_mixing_profile, MIXING_PROFILES

    random.seed(seed)

    print(f"\n{'='*80}")
    print("MIXING PROFILE COMPARISON (Aggregated)")
    print(f"{'='*80}")
    print(f"\nCharts: {n_charts}")
    print(f"Days per chart: {days_per_chart}")
    print(f"Total data points: {n_charts * days_per_chart}")

    # Generate random natal charts
    print(f"\nGenerating {n_charts} random natal charts...")
    natal_charts = []
    for i in range(n_charts):
        birth_data = generate_random_birth_data()
        try:
            natal_chart, _ = compute_birth_chart(
                birth_data['birth_date'],
                birth_data['birth_time'],
                birth_data['birth_timezone'],
                birth_data['birth_lat'],
                birth_data['birth_lon'],
            )
            natal_charts.append(natal_chart)
        except:
            pass

        if (i + 1) % 25 == 0:
            print(f"  Generated {i+1}/{n_charts} charts...")

    print(f"  Valid charts: {len(natal_charts)}")

    # Store aggregated results for each profile
    profile_results = {}

    for profile_name in MIXING_PROFILES.keys():
        print(f"\nAnalyzing profile: {profile_name}...")
        set_mixing_profile(profile_name)

        all_tier_totals = {'trigger': 0, 'event': 0, 'season': 0, 'era': 0}
        all_totals = []
        all_deltas = []
        var_coefs = []

        for chart_idx, natal_chart in enumerate(natal_charts):
            # Random start date for this chart
            start = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 365 * 4))

            chart_totals = []
            chart_tier_totals = {'trigger': 0, 'event': 0, 'season': 0, 'era': 0}

            for i in range(days_per_chart):
                current_date = start + timedelta(days=i)
                day_result = calculate_daily_symphony(natal_chart, current_date)

                chart_totals.append(day_result['total'])
                all_totals.append(day_result['total'])

                for tier, score in day_result['tier_scores'].items():
                    chart_tier_totals[tier] += score
                    all_tier_totals[tier] += score

            # Calculate variation for this chart
            if len(chart_totals) > 1:
                chart_deltas = [abs(chart_totals[i] - chart_totals[i-1])
                               for i in range(1, len(chart_totals))]
                all_deltas.extend(chart_deltas)

                chart_mean = sum(chart_totals) / len(chart_totals) if chart_totals else 0
                chart_delta_avg = sum(chart_deltas) / len(chart_deltas) if chart_deltas else 0
                if chart_mean > 0:
                    var_coefs.append(chart_delta_avg / chart_mean * 100)

            if (chart_idx + 1) % 25 == 0:
                print(f"    Progress: {chart_idx+1}/{len(natal_charts)} charts...")

        # Calculate aggregate stats
        mean_total = sum(all_totals) / len(all_totals) if all_totals else 0
        avg_delta = sum(all_deltas) / len(all_deltas) if all_deltas else 0
        avg_var_coef = sum(var_coefs) / len(var_coefs) if var_coefs else 0

        # Calculate tier percentages
        grand_total = sum(all_tier_totals.values())
        tier_pcts = {
            tier: (score / grand_total * 100) if grand_total > 0 else 0
            for tier, score in all_tier_totals.items()
        }

        profile_results[profile_name] = {
            'totals': all_totals,
            'mean': mean_total,
            'avg_delta': avg_delta,
            'var_coef': avg_var_coef,
            'tier_pcts': tier_pcts,
            'min': min(all_totals) if all_totals else 0,
            'max': max(all_totals) if all_totals else 0,
            'tier_totals': all_tier_totals,
        }

    # Print comparison table
    print(f"\n{'='*80}")
    print("TIER BREAKDOWN BY PROFILE (Aggregated across all charts)")
    print(f"{'='*80}")
    print(f"\n{'Profile':<15} {'Trigger':>10} {'Event':>10} {'Season':>10} {'Era':>10} {'Target'}")
    print("-" * 75)

    targets = {
        'daily_pulse': '~50/30/10/10',
        'deep_current': '~30/30/20/20',
        'forecast': '~20/50/10/20',
    }

    for name, results in profile_results.items():
        pcts = results['tier_pcts']
        target = targets.get(name, '')
        print(f"{name:<15} {pcts['trigger']:>9.1f}% {pcts['event']:>9.1f}% "
              f"{pcts['season']:>9.1f}% {pcts['era']:>9.1f}%  {target}")

    print(f"\n{'='*80}")
    print("VARIATION METRICS BY PROFILE")
    print(f"{'='*80}")
    print(f"\n{'Profile':<15} {'Mean':>10} {'Min':>10} {'Max':>10} {'Avg Delta':>12} {'Var Coef':>10}")
    print("-" * 70)

    for name, results in profile_results.items():
        print(f"{name:<15} {results['mean']:>10.1f} {results['min']:>10.1f} "
              f"{results['max']:>10.1f} {results['avg_delta']:>12.1f} {results['var_coef']:>9.1f}%")

    # Distribution analysis
    print(f"\n{'='*80}")
    print("SCORE DISTRIBUTION BY PROFILE")
    print(f"{'='*80}")

    for name, results in profile_results.items():
        totals = sorted(results['totals'])
        n = len(totals)
        if n > 0:
            p10 = totals[int(n * 0.10)]
            p25 = totals[int(n * 0.25)]
            p50 = totals[int(n * 0.50)]
            p75 = totals[int(n * 0.75)]
            p90 = totals[int(n * 0.90)]
            print(f"\n{name}:")
            print(f"  10th percentile: {p10:.1f}")
            print(f"  25th percentile: {p25:.1f}")
            print(f"  50th percentile: {p50:.1f} (median)")
            print(f"  75th percentile: {p75:.1f}")
            print(f"  90th percentile: {p90:.1f}")

    # Recommendation
    print(f"\n{'='*80}")
    print("ANALYSIS")
    print(f"{'='*80}")

    print("""
DAILY_PULSE:
  + Highest day-to-day variation (engagement)
  + Moon dominates = feels responsive to daily life
  - May ignore major life transits
  - Could feel superficial during crisis

DEEP_CURRENT:
  + Balanced between daily mood and life phase
  + Psychologically credible
  + "Challenging month, lighter day" narrative
  - Lower variation than daily_pulse

FORECAST:
  + Event-focused, good for predicting external happenings
  + Outer planets get more weight
  - Less about internal mood
  - May feel disconnected from daily experience

RECOMMENDATIONS:
  - If variation coefficient < 30%: may feel too stable
  - If variation coefficient > 60%: may feel erratic
  - Sweet spot: 35-50% variation for "meaningful daily change"
""")

    return profile_results


def compare_gaussian_sigma_divisors(
    n_charts: int = 50,
    days_per_chart: int = 30,
    seed: int = 42,
):
    """
    Test different sigma divisors to find optimal variation.

    sigma = window_days / divisor
    Higher divisor = narrower curve = more day-to-day variation
    """
    import astrometers.transit_power as tp
    from astrometers.constants import set_mixing_profile

    random.seed(seed)

    print(f"\n{'='*80}")
    print("GAUSSIAN SIGMA DIVISOR COMPARISON")
    print(f"{'='*80}")
    print(f"\nCharts: {n_charts}, Days: {days_per_chart}")
    print(f"Testing divisors: 3.0, 5.0, 7.0, 9.0, 12.0")

    set_mixing_profile('deep_current')

    # Generate charts once
    print(f"\nGenerating {n_charts} random natal charts...")
    natal_charts = []
    for i in range(n_charts):
        birth_data = generate_random_birth_data()
        try:
            natal_chart, _ = compute_birth_chart(
                birth_data['birth_date'],
                birth_data['birth_time'],
                birth_data['birth_timezone'],
                birth_data['birth_lat'],
                birth_data['birth_lon'],
            )
            natal_charts.append(natal_chart)
        except:
            pass

    print(f"  Valid charts: {len(natal_charts)}")

    results = {}
    divisors = [3.0, 5.0, 7.0, 9.0, 12.0]

    for divisor in divisors:
        print(f"\nTesting divisor {divisor}...")
        tp.GAUSSIAN_SIGMA_DIVISOR = divisor

        all_totals = []
        all_deltas = []

        for chart_idx, natal_chart in enumerate(natal_charts):
            start = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 365 * 4))
            chart_totals = []

            for i in range(days_per_chart):
                current_date = start + timedelta(days=i)
                transit_chart, _ = compute_birth_chart(
                    current_date.strftime('%Y-%m-%d'), '12:00'
                )

                aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=15.0)
                day_total = 0.0

                for asp in aspects:
                    transit_planet = Planet(asp.transit_planet)
                    speed = get_planet_speed(transit_chart, asp.transit_planet)

                    score, _ = calculate_gaussian_score(
                        transit_planet=transit_planet,
                        deviation_deg=asp.orb,
                        transit_speed=speed,
                        aspect_type=asp.aspect_type,
                    )
                    day_total += score

                chart_totals.append(day_total)
                all_totals.append(day_total)

            for i in range(1, len(chart_totals)):
                all_deltas.append(abs(chart_totals[i] - chart_totals[i-1]))

        mean = sum(all_totals) / len(all_totals) if all_totals else 0
        avg_delta = sum(all_deltas) / len(all_deltas) if all_deltas else 0
        var_coef = (avg_delta / mean * 100) if mean > 0 else 0

        sorted_totals = sorted(all_totals)
        n = len(sorted_totals)

        results[divisor] = {
            'mean': mean,
            'var_coef': var_coef,
            'avg_delta': avg_delta,
            'p10': sorted_totals[int(n * 0.10)] if n > 0 else 0,
            'p50': sorted_totals[int(n * 0.50)] if n > 0 else 0,
            'p90': sorted_totals[int(n * 0.90)] if n > 0 else 0,
        }

    # Reset to default
    tp.GAUSSIAN_SIGMA_DIVISOR = 3.0

    # Print comparison
    print(f"\n{'='*80}")
    print("RESULTS")
    print(f"{'='*80}")
    print(f"\n{'Divisor':<10} {'Mean':>10} {'Var Coef':>12} {'P10':>10} {'P50':>10} {'P90':>10} {'Assessment'}")
    print("-" * 80)

    for divisor, r in sorted(results.items()):
        if r['var_coef'] < 25:
            assessment = "Too smooth"
        elif r['var_coef'] < 35:
            assessment = "Low"
        elif r['var_coef'] <= 50:
            assessment = "SWEET SPOT"
        elif r['var_coef'] <= 60:
            assessment = "High"
        else:
            assessment = "Too erratic"

        print(f"{divisor:<10} {r['mean']:>10.1f} {r['var_coef']:>11.1f}% "
              f"{r['p10']:>10.1f} {r['p50']:>10.1f} {r['p90']:>10.1f} {assessment}")

    print(f"""
INTERPRETATION:
  - Divisor 2.0: Wide curve, smooth, fewer daily swings
  - Divisor 3.0: Standard (99% in window), moderate
  - Divisor 4.0-5.0: Narrower curve, more responsive
  - Divisor 6.0: Very narrow, high daily variance

TARGET: Variation coefficient 35-50% for meaningful daily change
""")

    return results


def compare_velocity_vs_gaussian(
    n_charts: int = 100,
    days_per_chart: int = 30,
    seed: int = 42,
):
    """
    Compare velocity (squared closeness) vs Gaussian scoring across many charts.

    Key metrics to compare:
    - Tier distribution: Does Gaussian change the balance?
    - Day-to-day variation: Is Gaussian smoother or spikier?
    - Score distribution: How do percentiles differ?
    - Edge behavior: How do scores differ at orb boundaries?
    """
    from astrometers.constants import set_mixing_profile

    random.seed(seed)

    print(f"\n{'='*80}")
    print("VELOCITY vs GAUSSIAN SCORING COMPARISON")
    print(f"{'='*80}")
    print(f"\nCharts: {n_charts}")
    print(f"Days per chart: {days_per_chart}")
    print(f"Total data points: {n_charts * days_per_chart}")

    # Use deep_current profile for consistency
    set_mixing_profile('deep_current')

    # Generate random natal charts
    print(f"\nGenerating {n_charts} random natal charts...")
    natal_charts = []
    for i in range(n_charts):
        birth_data = generate_random_birth_data()
        try:
            natal_chart, _ = compute_birth_chart(
                birth_data['birth_date'],
                birth_data['birth_time'],
                birth_data['birth_timezone'],
                birth_data['birth_lat'],
                birth_data['birth_lon'],
            )
            natal_charts.append(natal_chart)
        except:
            pass

        if (i + 1) % 25 == 0:
            print(f"  Generated {i+1}/{n_charts} charts...")

    print(f"  Valid charts: {len(natal_charts)}")

    # Collect data for both methods
    velocity_data = {
        'totals': [],
        'tier_totals': {'trigger': 0, 'event': 0, 'season': 0, 'era': 0},
        'deltas': [],
    }
    gaussian_data = {
        'totals': [],
        'tier_totals': {'trigger': 0, 'event': 0, 'season': 0, 'era': 0},
        'deltas': [],
    }

    print(f"\nAnalyzing {len(natal_charts)} charts x {days_per_chart} days...")

    for chart_idx, natal_chart in enumerate(natal_charts):
        # Random start date
        start = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 365 * 4))

        vel_chart_totals = []
        gauss_chart_totals = []

        for i in range(days_per_chart):
            current_date = start + timedelta(days=i)
            transit_chart, _ = compute_birth_chart(
                current_date.strftime('%Y-%m-%d'), '12:00'
            )

            aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=15.0)

            vel_tier_scores = {'trigger': 0.0, 'event': 0.0, 'season': 0.0, 'era': 0.0}
            gauss_tier_scores = {'trigger': 0.0, 'event': 0.0, 'season': 0.0, 'era': 0.0}

            for asp in aspects:
                transit_planet = Planet(asp.transit_planet)
                speed = get_planet_speed(transit_chart, asp.transit_planet)

                # Velocity scoring
                vel_score, vel_breakdown = calculate_velocity_score(
                    transit_planet=transit_planet,
                    deviation_deg=asp.orb,
                    transit_speed=speed,
                    aspect_type=asp.aspect_type,
                )
                if vel_score > 0:
                    vel_tier_scores[vel_breakdown['tier']] += vel_score

                # Gaussian scoring
                gauss_score, gauss_breakdown = calculate_gaussian_score(
                    transit_planet=transit_planet,
                    deviation_deg=asp.orb,
                    transit_speed=speed,
                    aspect_type=asp.aspect_type,
                )
                if gauss_score > 0:
                    gauss_tier_scores[gauss_breakdown['tier']] += gauss_score

            vel_total = sum(vel_tier_scores.values())
            gauss_total = sum(gauss_tier_scores.values())

            vel_chart_totals.append(vel_total)
            gauss_chart_totals.append(gauss_total)

            velocity_data['totals'].append(vel_total)
            gaussian_data['totals'].append(gauss_total)

            for tier in vel_tier_scores:
                velocity_data['tier_totals'][tier] += vel_tier_scores[tier]
                gaussian_data['tier_totals'][tier] += gauss_tier_scores[tier]

        # Calculate day-to-day deltas for this chart
        for i in range(1, len(vel_chart_totals)):
            velocity_data['deltas'].append(abs(vel_chart_totals[i] - vel_chart_totals[i-1]))
            gaussian_data['deltas'].append(abs(gauss_chart_totals[i] - gauss_chart_totals[i-1]))

        if (chart_idx + 1) % 25 == 0:
            print(f"  Progress: {chart_idx+1}/{len(natal_charts)} charts...")

    # Calculate statistics
    def calc_stats(data):
        totals = data['totals']
        deltas = data['deltas']
        tier_totals = data['tier_totals']

        mean = sum(totals) / len(totals) if totals else 0
        avg_delta = sum(deltas) / len(deltas) if deltas else 0
        var_coef = (avg_delta / mean * 100) if mean > 0 else 0

        grand_total = sum(tier_totals.values())
        tier_pcts = {
            tier: (score / grand_total * 100) if grand_total > 0 else 0
            for tier, score in tier_totals.items()
        }

        sorted_totals = sorted(totals)
        n = len(sorted_totals)

        return {
            'mean': mean,
            'min': min(totals) if totals else 0,
            'max': max(totals) if totals else 0,
            'avg_delta': avg_delta,
            'max_delta': max(deltas) if deltas else 0,
            'var_coef': var_coef,
            'tier_pcts': tier_pcts,
            'p10': sorted_totals[int(n * 0.10)] if n > 0 else 0,
            'p25': sorted_totals[int(n * 0.25)] if n > 0 else 0,
            'p50': sorted_totals[int(n * 0.50)] if n > 0 else 0,
            'p75': sorted_totals[int(n * 0.75)] if n > 0 else 0,
            'p90': sorted_totals[int(n * 0.90)] if n > 0 else 0,
        }

    vel_stats = calc_stats(velocity_data)
    gauss_stats = calc_stats(gaussian_data)

    # Print comparison
    print(f"\n{'='*80}")
    print("TIER DISTRIBUTION COMPARISON")
    print(f"{'='*80}")
    print(f"\n{'Tier':<12} {'Velocity':>12} {'Gaussian':>12} {'Delta':>10}")
    print("-" * 50)
    for tier in ['trigger', 'event', 'season', 'era']:
        v = vel_stats['tier_pcts'][tier]
        g = gauss_stats['tier_pcts'][tier]
        d = g - v
        print(f"{tier:<12} {v:>11.1f}% {g:>11.1f}% {d:>+9.1f}%")

    print(f"\n{'='*80}")
    print("VARIATION METRICS COMPARISON")
    print(f"{'='*80}")
    print(f"\n{'Metric':<25} {'Velocity':>15} {'Gaussian':>15} {'Delta':>12}")
    print("-" * 70)
    metrics = [
        ('Mean total score', 'mean', '.1f'),
        ('Min score', 'min', '.1f'),
        ('Max score', 'max', '.1f'),
        ('Avg daily delta', 'avg_delta', '.1f'),
        ('Max daily delta', 'max_delta', '.1f'),
        ('Variation coefficient', 'var_coef', '.1f'),
    ]
    for label, key, fmt in metrics:
        v = vel_stats[key]
        g = gauss_stats[key]
        d = g - v
        suffix = '%' if 'coef' in key else ''
        print(f"{label:<25} {v:>14{fmt}}{suffix} {g:>14{fmt}}{suffix} {d:>+11{fmt}}{suffix}")

    print(f"\n{'='*80}")
    print("SCORE DISTRIBUTION COMPARISON")
    print(f"{'='*80}")
    print(f"\n{'Percentile':<15} {'Velocity':>15} {'Gaussian':>15} {'Ratio':>12}")
    print("-" * 60)
    for pct in ['p10', 'p25', 'p50', 'p75', 'p90']:
        v = vel_stats[pct]
        g = gauss_stats[pct]
        ratio = g / v if v > 0 else 0
        label = pct.replace('p', '') + 'th'
        print(f"{label:<15} {v:>15.1f} {g:>15.1f} {ratio:>11.2f}x")

    print(f"\n{'='*80}")
    print("ANALYSIS")
    print(f"{'='*80}")

    var_improvement = gauss_stats['var_coef'] - vel_stats['var_coef']
    score_ratio = gauss_stats['mean'] / vel_stats['mean'] if vel_stats['mean'] > 0 else 0

    print(f"""
GAUSSIAN vs VELOCITY COMPARISON:

Score Magnitude:
  - Gaussian scores are {score_ratio:.2f}x the velocity scores on average
  - This is expected: Gaussian doesn't have the hard cutoff that zeroes out
    aspects at the edge of orb, so more aspects contribute

Variation:
  - Variation coefficient changed by {var_improvement:+.1f}%
  - Velocity: {vel_stats['var_coef']:.1f}%, Gaussian: {gauss_stats['var_coef']:.1f}%
  - {"Gaussian is smoother (less day-to-day change)" if var_improvement < 0 else "Gaussian has more variation"}

Edge Behavior:
  - Velocity: Hard cutoff at dynamic_limit (score instantly drops to 0)
  - Gaussian: Smooth asymptotic fade (influence > 3 sigma is < 1%)

Constructive Interference:
  - When multiple aspects approach exactitude simultaneously (stellium),
    Gaussian curves sum naturally creating "peak experiences"
  - Velocity scoring also sums, but the squared closeness doesn't
    capture the same smooth constructive interference pattern

RECOMMENDATION:
  - If var_coef is in sweet spot (35-50%): {"GAUSSIAN IS GOOD" if 35 <= gauss_stats['var_coef'] <= 50 else "May need tuning"}
  - Sweet spot target: 35-50% variation for meaningful daily change
""")

    return {
        'velocity': vel_stats,
        'gaussian': gauss_stats,
        'velocity_data': velocity_data,
        'gaussian_data': gaussian_data,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Symphony Visualization")
    parser.add_argument("--birth-date", default="1990-06-15", help="Natal birth date")
    parser.add_argument("--birth-time", default="14:30", help="Natal birth time")
    parser.add_argument("--start", default=None, help="Analysis start date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=60, help="Number of days to analyze")
    parser.add_argument("--output", default=None, help="JSON output file")
    parser.add_argument("--plot", default=None, help="PNG plot output file")
    parser.add_argument("--compare", action="store_true", help="Compare old vs new scoring")
    parser.add_argument("--profiles", action="store_true", help="Compare all mixing profiles")
    parser.add_argument("--gaussian", action="store_true", help="Compare velocity vs Gaussian scoring")
    parser.add_argument("--sigma", action="store_true", help="Test different Gaussian sigma divisors")
    parser.add_argument("-n", "--n-charts", type=int, default=100, help="Number of charts for comparison")

    args = parser.parse_args()

    if args.sigma:
        compare_gaussian_sigma_divisors(
            n_charts=args.n_charts,
            days_per_chart=args.days,
            seed=42,
        )
    elif args.gaussian:
        compare_velocity_vs_gaussian(
            n_charts=args.n_charts,
            days_per_chart=args.days,
            seed=42,
        )
    elif args.profiles:
        compare_mixing_profiles(
            n_charts=args.n_charts,
            days_per_chart=args.days,
            seed=42,
        )
    elif args.compare:
        compare_old_vs_new_scoring(
            natal_birth_date=args.birth_date,
            natal_birth_time=args.birth_time,
            days=args.days,
        )
    else:
        run_symphony_analysis(
            natal_birth_date=args.birth_date,
            natal_birth_time=args.birth_time,
            start_date=args.start,
            days=args.days,
            output_file=args.output,
            plot_file=args.plot,
        )

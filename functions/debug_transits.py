#!/usr/bin/env python3
"""Debug upcoming transits to understand why same transit appears multiple days."""

from datetime import datetime, timedelta
from astro import compute_birth_chart, get_upcoming_transits, find_natal_transit_aspects

# Use Elie's birth data from prototype
birth_date = "1987-06-02"
natal_chart, _ = compute_birth_chart(birth_date)

# Check today and next 7 days
today = datetime.now().strftime("%Y-%m-%d")
base_date = datetime.strptime(today, "%Y-%m-%d")

print(f"Checking transits from {today} for next 7 days\n")
print("=" * 80)

for day_offset in range(1, 8):
    future_date = base_date + timedelta(days=day_offset)
    future_date_str = future_date.strftime("%Y-%m-%d")

    future_chart, _ = compute_birth_chart(future_date_str, birth_time="12:00")
    aspects = find_natal_transit_aspects(natal_chart, future_chart, orb=1.0)

    print(f"\nDay {day_offset} ({future_date_str}):")
    print(f"  Found {len(aspects)} aspects within 1° orb")

    for i, aspect in enumerate(aspects[:5], 1):  # Show top 5
        print(f"  {i}. {aspect.transit_planet.value.title()} {aspect.aspect_type.value} natal {aspect.natal_planet.value.title()}")
        print(f"     Orb: {aspect.orb:.2f}° | Applying: {aspect.applying} | Meaning: {aspect.meaning}")

print("\n" + "=" * 80)
print("\nUsing get_upcoming_transits():")
upcoming = get_upcoming_transits(natal_chart, today, days_ahead=7)
for transit in upcoming:
    print(f"  Day {transit.days_away}: {transit.description} (orb: {transit.aspect.orb:.2f}°)")

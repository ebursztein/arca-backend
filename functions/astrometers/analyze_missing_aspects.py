"""
Analyze what aspects we're missing and why some meters have low counts.

Focus areas:
1. Innovation breakthrough - Should we add Mercury-Uranus?
2. Conflict risk - Are we missing Mars-Pluto, Mars-Saturn, Mars-Uranus?
3. Communication flow - Are we missing Mercury-Mercury?
4. Are chart angles being aspected?
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from astro import compute_birth_chart, find_natal_transit_aspects, Planet
from astrometers.meters import convert_to_transit_aspects, filter_aspects_by_natal_planet


def analyze_missing_aspects():
    """Check what aspects exist that we might not be capturing."""

    natal_chart, _ = compute_birth_chart(
        birth_date="1990-06-15",
        birth_time="14:30",
        birth_timezone="America/New_York",
        birth_lat=40.7128,
        birth_lon=-74.0060
    )

    transit_chart, _ = compute_birth_chart(birth_date="2025-10-26")

    # Get all aspects
    natal_transit_aspects = find_natal_transit_aspects(
        natal_chart,
        transit_chart,
        orb=8.0
    )

    all_aspects = convert_to_transit_aspects(
        natal_chart,
        transit_chart,
        natal_transit_aspects
    )

    print(f"\n{'='*100}")
    print("INNOVATION BREAKTHROUGH - Should we add Mercury?")
    print(f"{'='*100}\n")

    # Current: Only Uranus natal
    uranus_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.URANUS])
    print(f"Current filter (Uranus natal only): {len(uranus_aspects)} aspects")
    for a in uranus_aspects:
        print(f"  {a.label}")

    # Proposed: Uranus + Mercury natal
    uranus_mercury_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.URANUS, Planet.MERCURY])
    print(f"\nProposed filter (Uranus + Mercury natal): {len(uranus_mercury_aspects)} aspects")
    mercury_only = [a for a in uranus_mercury_aspects if a.natal_planet == Planet.MERCURY]
    print(f"  New Mercury aspects: {len(mercury_only)}")
    for a in mercury_only:
        print(f"  {a.label}")

    print(f"\n✅ Recommendation: ADD Mercury to innovation_breakthrough")
    print(f"   Rationale: Mercury-Uranus = innovative thinking, sudden insights, eureka moments")

    # =========================================================================
    print(f"\n{'='*100}")
    print("CONFLICT RISK - Should we expand Mars coverage?")
    print(f"{'='*100}\n")

    # Current: Mars natal, hard aspects only
    mars_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.MARS])
    print(f"All Mars natal aspects: {len(mars_aspects)}")
    for a in mars_aspects:
        print(f"  {a.label} ({a.aspect_type.value})")

    # Check for Mars-Pluto, Mars-Saturn, Mars-Uranus
    pluto_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.PLUTO])
    saturn_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.SATURN])
    uranus_aspects_2 = filter_aspects_by_natal_planet(all_aspects, [Planet.URANUS])

    print(f"\nAre there transiting Mars aspects to these planets?")
    mars_to_pluto = [a for a in pluto_aspects if a.transit_planet == Planet.MARS]
    mars_to_saturn = [a for a in saturn_aspects if a.transit_planet == Planet.MARS]
    mars_to_uranus = [a for a in uranus_aspects_2 if a.transit_planet == Planet.MARS]

    print(f"  Transit Mars to natal Pluto: {len(mars_to_pluto)} aspects")
    for a in mars_to_pluto:
        print(f"    {a.label} ({a.aspect_type.value})")

    print(f"  Transit Mars to natal Saturn: {len(mars_to_saturn)} aspects")
    for a in mars_to_saturn:
        print(f"    {a.label} ({a.aspect_type.value})")

    print(f"  Transit Mars to natal Uranus: {len(mars_to_uranus)} aspects")
    for a in mars_to_uranus:
        print(f"    {a.label} ({a.aspect_type.value})")

    # Proposed expansion
    conflict_planets = [Planet.MARS, Planet.PLUTO, Planet.SATURN, Planet.URANUS]
    expanded_aspects = filter_aspects_by_natal_planet(all_aspects, conflict_planets)
    print(f"\nProposed filter (Mars + Pluto + Saturn + Uranus natal, hard only): {len(expanded_aspects)} aspects (before hard filter)")

    if len(mars_to_saturn) > 0 or len(mars_to_pluto) > 0:
        print(f"\n✅ Recommendation: EXPAND conflict_risk to include Pluto, Saturn, Uranus")
        print(f"   Rationale: Mars-Saturn = frustration, Mars-Pluto = power struggles, Mars-Uranus = sudden aggression")
    else:
        print(f"\n⚠️  Note: In this chart, expansion wouldn't add aspects, but still recommended for general case")

    # =========================================================================
    print(f"\n{'='*100}")
    print("COMMUNICATION FLOW - Are we missing Mercury-Mercury?")
    print(f"{'='*100}\n")

    mercury_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.MERCURY])
    print(f"All Mercury natal aspects: {len(mercury_aspects)}")
    for a in mercury_aspects:
        print(f"  {a.label} ({a.aspect_type.value})")

    mercury_to_mercury = [a for a in mercury_aspects if a.transit_planet == Planet.MERCURY]
    print(f"\nTransit Mercury to natal Mercury: {len(mercury_to_mercury)} aspects")
    for a in mercury_to_mercury:
        print(f"  {a.label}")

    if len(mercury_to_mercury) > 0:
        print(f"\n✅ Recommendation: Mercury-Mercury IS already captured (communication_flow filters natal Mercury)")
    else:
        print(f"\n⚠️  Note: No Mercury-Mercury aspect in this chart on this day")

    # =========================================================================
    print(f"\n{'='*100}")
    print("CHART ANGLES - Are they being aspected?")
    print(f"{'='*100}\n")

    print(f"Natal chart angles:")
    print(f"  Ascendant: {natal_chart['angles']['ascendant']['sign'].value} {natal_chart['angles']['ascendant']['absolute_degree']:.2f}°")
    print(f"  MC: {natal_chart['angles']['midheaven']['sign'].value} {natal_chart['angles']['midheaven']['absolute_degree']:.2f}°")

    print(f"\n⚠️  Chart angles are NOT included in natal_transit_aspects")
    print(f"   Current implementation only finds planet-to-planet aspects")
    print(f"   To add: Would need to modify find_natal_transit_aspects() in astro.py")

    # =========================================================================
    print(f"\n{'='*100}")
    print("SUMMARY OF RECOMMENDATIONS")
    print(f"{'='*100}\n")

    print("1. ✅ ADD Mercury to innovation_breakthrough")
    print("   - Current: Uranus only")
    print("   - Proposed: Uranus + Mercury")
    print("   - Why: Mercury-Uranus = innovative thinking, breakthroughs in communication/ideas")

    print("\n2. ✅ EXPAND conflict_risk natal planets")
    print("   - Current: Mars only")
    print("   - Proposed: Mars + Pluto + Saturn + Uranus (all with hard aspects only)")
    print("   - Why: Mars-Pluto = power struggles, Mars-Saturn = frustration, Mars-Uranus = sudden conflicts")

    print("\n3. ✅ communication_flow already captures Mercury-Mercury")
    print("   - No change needed")

    print("\n4. ⚠️  Chart angles (Asc, MC) not included")
    print("   - Requires modification to astro.py")
    print("   - Consider as future enhancement")


if __name__ == "__main__":
    analyze_missing_aspects()

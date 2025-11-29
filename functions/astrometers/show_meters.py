"""
Display meter configurations for astrological review.

Shows natal planets and houses for all 17 meters, organized by group.

Usage:
    uv run python functions/astrometers/show_meters.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astrometers.meters import METER_CONFIGS
from astrometers.hierarchy import MeterGroupV2


def show_meter_configurations():
    """Display all meter configurations for astrological review."""

    house_meanings = {
        1: 'Self/Identity',
        2: 'Resources/Values',
        3: 'Communication/Learning',
        4: 'Home/Roots',
        5: 'Creativity/Joy',
        6: 'Work/Health',
        7: 'Partnerships',
        8: 'Intimacy/Transformation',
        9: 'Beliefs/Travel',
        10: 'Career/Status',
        11: 'Community/Friends',
        12: 'Spirituality/Unconscious'
    }

    print('=' * 90)
    print('METER CONFIGURATION REVIEW - FOR ASTROLOGICAL CRITIQUE')
    print('=' * 90)
    print()

    # Group by meter group
    for group in [MeterGroupV2.MIND, MeterGroupV2.HEART, MeterGroupV2.BODY,
                  MeterGroupV2.INSTINCTS, MeterGroupV2.GROWTH]:
        print('=' * 90)
        print(f'{group.value.upper()} GROUP')
        print('=' * 90)

        group_meters = [
            (name, config)
            for name, config in METER_CONFIGS.items()
            if config.group == group
        ]

        for meter_name, config in sorted(group_meters):
            print(f'\n{meter_name.upper()}:')

            # Natal planets
            if config.natal_planets:
                planets = [p.value.capitalize() for p in config.natal_planets]
                print(f'  Natal Planets: {", ".join(planets)}')
            else:
                print(f'  Natal Planets: (None - house-only meter)')

            # Natal houses
            if config.natal_houses:
                houses = [str(h) for h in config.natal_houses]
                print(f'  Natal Houses:  {", ".join(houses)}')

                # House meanings
                meanings = [f'{h}={house_meanings[h]}' for h in config.natal_houses]
                print(f'  House Meanings: {" | ".join(meanings)}')
            else:
                print(f'  Natal Houses:  (Any house)')

            # Retrograde modifiers
            if config.retrograde_modifiers:
                mods = [f'{p.value.capitalize()}={m}' for p, m in config.retrograde_modifiers.items()]
                print(f'  Retrograde Mods: {", ".join(mods)}')

        print()

    print('=' * 90)
    print('NOTES:')
    print('- All meters allow ALL transit planets (no transit filtering)')
    print('- All meters allow ALL aspect types')
    print('- Natal filters use OR logic: (natal_planets) OR (natal_houses)')
    print('- Retrograde modifiers reduce harmony score when transit planet is retrograde')
    print('=' * 90)


if __name__ == '__main__':
    show_meter_configurations()

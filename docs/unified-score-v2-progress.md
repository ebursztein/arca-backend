# Unified Score V2 Implementation Progress

Last updated: 2025-11-26

## Overview

Redesigning `unified_score` from 0-100 to -100 to +100 (polar-style where intensity is magnitude, harmony is direction). Adding programmatic curation for LLM prompts with word banks and featured meter rotation.

---

## Completed

### 1. Core Formula Changes
- `calculate_unified_score()` in `astrometers/meters.py` now returns -100 to +100
- Uses tanh sigmoid stretch for better distribution
- Empowering asymmetry: 1.2x positive boost, 0.7x negative dampen
- Result: 70% positive / 30% negative distribution, average +20.8
- Constants in `astrometers/constants.py`:
  - `UNIFIED_SCORE_BASE_WEIGHT = 0.3`
  - `UNIFIED_SCORE_INTENSITY_WEIGHT = 0.7`
  - `UNIFIED_SCORE_TANH_FACTOR = 50.0`
  - `UNIFIED_SCORE_POSITIVE_BOOST = 1.2`
  - `UNIFIED_SCORE_NEGATIVE_DAMPEN = 0.7`

### 2. Word Banks System
- Created `astrometers/labels/word_banks.json`
- Empirical thresholds from 102k data points (P33/P67):
  - Intensity: low < 19, high > 38
  - Harmony: low < 52, high > 65
- 5 quadrants: high_intensity_high_harmony, high_intensity_low_harmony, low_intensity_high_harmony, low_intensity_low_harmony, moderate
- Words per group: mind, emotions, body, spirit, growth, overall

### 3. Featured Meter Selection
- `select_featured_meters()` - weighted random by |unified_score|
- `select_state_words()` - picks 2 words from appropriate quadrant
- `get_quadrant()` - determines quadrant from intensity/harmony
- Currently configured: 2 groups, 1 meter per group = 2 featured meters per horoscope

### 4. LLM Prompt Restructure
**daily_dynamic.j2** now outputs:
```
TODAY'S ENERGY (2025-11-26)

[GROUPS]
MIND: -21 (rising) | Hazy, Dim
EMOTIONS: 10 | Shifting, In Flux
...

[FEATURED - emphasize in headline/overview]
• Inner Stability (-11) - Saturn square natal Uranus
• Intuition (-43) - Saturn square natal Uranus

[RELATIONSHIPS - for relationship_weather field]
SPOTLIGHT: Sarah [friend]
Notes: Best friend since college.
Partner: John (boyfriend)
Family: Mom (mother)
Friends: Sarah
Work: Mike (boss)

[MOON]
...

[NEXT 7 DAYS]
TODAY (Wednesday): Saturn square your natal Uranus (EXACT), Mars trine your natal Moon (EXACT)
Day +1 - Thursday: Saturn square your natal Uranus (EXACT), Mars trine your natal Moon
...
```

**daily_static.j2** updated with:
- Empowering, optimistic tone (NOT dark/snarky like Co-Star)
- Generational language support (age calculated, passed to LLM)
- Sun sign filter (acknowledge sign-specific challenges as opportunities)
- Void of Course override (rest/reflect advice during void moon)
- SPOTLIGHT rule (60-70% of relationship_weather on featured person)

### 5. Model Updates
Updated Pydantic constraints for -100 to +100:
- `MeterReading.unified_score`: ge=-100, le=100
- `MeterForIOS.unified_score`: ge=-100, le=100
- `MeterGroupForIOS.unified_score`: ge=-100, le=100
- `AstrometersForIOS.overall_unified_score`: ge=-100, le=100

### 6. Entity System Updates
Added `EntityCategory` enum in `models.py`:
- `partner` - Current romantic partner (only one allowed)
- `family` - Family members
- `friend` - Friends
- `coworker` - Work relationships
- `other` - Catch-all

Added fields to `Entity` model:
- `category: Optional[EntityCategory]` - dropdown selection
- `relationship_label: Optional[str]` - specific label (mother, boss, etc.)
- `notes: Optional[str]` - user-written notes

Added `RelationshipMention` model:
- `entity_id`, `entity_name`, `category`, `date`, `context`

Added to `MemoryCollection`:
- `relationship_mentions: list[RelationshipMention]` - capped at 20, tracks what was said

### 7. Bug Fixes
- `prototype.py`: Changed `memory.recent_readings` to `memory.total_conversations`
- `prototype.py`: Changed `async for` to `for` for sync generator in Ask the Stars
- `prototype.py`: Fixed Entity/EntityStatus/AttributeKV import shadowing

### 8. Cosmic Background Noise
- `calculate_cosmic_background()` in `meters.py`
- Adds reproducible randomness tied to user_id + date + meter_name
- Only applies when aspect_count > 0
- Intensity noise: -5 to +10 (slight positive bias)
- Harmony nudge: 0 to +3 (always positive - empowering)

### 9. Entity Wiring to Horoscope (2025-11-26)
- `group_entities_by_category()` in `llm.py` - groups entities for template
- `generate_daily_horoscope()` now accepts `entities` parameter
- All callers updated: `prototype.py`, `main.py`, `visualize_dailyhoroscope.py`, `test_llm_integration.py`
- Template shows relationships conditionally based on entity categories

### 10. Relationship Rotation (2025-11-26)
- `select_featured_relationship()` in `llm.py` - round-robin rotation
- Prioritizes entities NOT recently featured (checks last 10 mentions)
- Falls back to oldest mention if all recently featured
- Falls back to highest importance_score if no history
- SPOTLIGHT section in template highlights the featured person

### 11. Memory Tracking (2025-11-26)
- `update_memory_with_relationship_mention()` in `llm.py`
- Appends `RelationshipMention` after horoscope generation
- FIFO capped at 20 entries
- `main.py` saves updated memory to Firestore
- `generate_daily_horoscope()` now returns tuple: `(DailyHoroscope, Optional[Entity])`

### 12. Age & Generation Calculation (2025-11-26)
- Age calculated from birth_date in `llm.py`
- Generation determined: Gen Alpha, Gen Z, Millennial, Gen X, Baby Boomer, Silent Generation
- Passed to `personalization.j2` template
- LLM adjusts tone based on generation

### 13. Prompt Improvements (2025-11-26)
- Empowering, optimistic tone throughout
- Challenges framed as opportunities, not obstacles
- Removed dark/snarky language
- Simplified [NEXT 7 DAYS] output (max 2 transits per day, one line)
- Debug prompt saved to `debug_prompt.txt` only when `DEBUG_PROMPT=1` env var set

---

## Still TODO

### 1. iOS Integration (Waiting on iOS team)
- Add category dropdown to entity/contacts UI
- Add relationship_label dropdown (conditional options based on category)
- Add notes text field (user-editable)
- Enforce only one entity can have category=partner at a time
- Prompt to archive old partner if setting new one

### 2. Tests
- Unit tests for `group_entities_by_category()`
- Unit tests for `select_featured_relationship()`
- Unit tests for `update_memory_with_relationship_mention()`
- Tests for rotation logic (verify round-robin behavior)
- Integration test with prototype.py

### 3. Generational Language Guide
- Marketing team to provide generational tone guidelines
- Add conditional section to prompt based on generation

---

## Key Files Changed

| File | Changes |
|------|---------|
| `functions/astrometers/constants.py` | Added V2 unified score constants, cosmic noise constants |
| `functions/astrometers/meters.py` | New `calculate_unified_score()`, `calculate_cosmic_background()`, `select_featured_meters()`, `select_state_words()`, `get_quadrant()`, `load_word_banks()` |
| `functions/astrometers/labels/word_banks.json` | New file - word banks config with thresholds |
| `functions/astrometers/calibration/test_unified_score_v2.py` | Simulation script for validating distribution |
| `functions/templates/horoscope/daily_static.j2` | Empowering tone, generational language, SPOTLIGHT rule, void override |
| `functions/templates/horoscope/daily_dynamic.j2` | Groups table, featured meters, RELATIONSHIPS section, simplified transits |
| `functions/templates/horoscope/personalization.j2` | Added age and generation |
| `functions/llm.py` | `group_entities_by_category()`, `select_featured_relationship()`, `update_memory_with_relationship_mention()`, age calculation, tuple return |
| `functions/models.py` | `EntityCategory` enum, `Entity` fields, `RelationshipMention` model, `MemoryCollection.relationship_mentions` |
| `functions/main.py` | Fetch entities from Firestore, pass to horoscope, save updated memory |
| `functions/prototype.py` | Sample entities with categories, simulated relationship_mentions, DEBUG_PROMPT env var |

---

## Simulation Results (102k data points)

```
Unified Score V2 (-100 to +100):
  Min: -67.5, Max: 100.0
  P10: -21.7, P25: -3.7, P50: 17.9, P75: 42.1, P90: 72.4

  Positive (>0): 71536 (70.1%)
  Negative (<0): 30312 (29.7%)
  Neutral (=0): 152
  Average: +20.8

Bucket distribution:
    -100 to -60:   679 (  0.7%)
     -60 to -30:  5899 (  5.8%)
       -30 to 0: 23886 ( 23.4%)
       0 to +30: 35423 (  34.7%)
     +30 to +60: 21107 ( 20.7%)
    +60 to +100: 15006 ( 14.7%)

Quadrant distribution (P33/P67 thresholds):
  High Int + High Harm: 12.6%
  High Int + Low Harm:  13.2%
  Low Int + High Harm:  9.0%
  Low Int + Low Harm:   7.7%
  Moderate (middle):    57.5%
```

---

## Notes for Resume

1. Run `DEBUG_PROMPT=1 uv run python prototype.py` to test end-to-end (saves prompt to debug_prompt.txt)
2. Run `uv run python functions/astrometers/calibration/test_unified_score_v2.py` to verify distribution
3. The word banks are based on empirical data - if formula changes, re-run simulation to get new thresholds
4. iOS team has been emailed about entity UI changes - waiting on their timeline
5. Rotation logic tested: fresh memory picks highest importance, previous mentions cause rotation to next person

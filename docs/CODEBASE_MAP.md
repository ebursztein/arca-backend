# Arca Backend - Complete Codebase Map

This document provides a comprehensive map of every file and function in the arca-backend codebase, documenting what exists, how it's used, and how it's tested.

---

## Table of Contents

1. [Entry Points (Cloud Functions)](#1-entry-points-cloud-functions)
2. [Core Library Files](#2-core-library-files)
3. [Astrometers Module](#3-astrometers-module)
4. [Test Structure](#4-test-structure)
5. [Utility Scripts](#5-utility-scripts)
6. [Templates](#6-templates)
7. [Configuration Files](#7-configuration-files)
8. [Data Files](#8-data-files)

---

## 1. Entry Points (Cloud Functions)

### `functions/main.py`

The main Cloud Functions entry point. Contains all callable and HTTP functions exposed to iOS.

| Function | Type | Description | Secrets Used |
|----------|------|-------------|--------------|
| `get_daily_horoscope` | `@https_fn.on_call` | Main daily horoscope endpoint - generates personalized horoscope with astrometers, transits, and LLM interpretation | `GEMINI_API_KEY`, `POSTHOG_API_KEY` |
| `get_natal_chart` | `@https_fn.on_call` | Returns user's natal chart data | None |
| `get_transit_chart` | `@https_fn.on_call` | Returns current transit chart | None |
| `get_compatibility` | `@https_fn.on_call` | Calculates synastry compatibility between two charts | None |
| `get_connection_compatibility` | `@https_fn.on_call` | Gets compatibility for a specific connection | None |
| `create_connection` | `@https_fn.on_call` | Creates a new connection with birth data | None |
| `update_connection` | `@https_fn.on_call` | Updates an existing connection | None |
| `delete_connection` | `@https_fn.on_call` | Deletes a connection | None |
| `get_connections` | `@https_fn.on_call` | Lists all user connections | None |

**Key imports:**
- `astro` - Birth chart calculations
- `llm` - LLM generation functions
- `compatibility` - Synastry calculations
- `connections` - Connection management
- `models` - Pydantic models

---

### `functions/ask_the_stars.py`

HTTPS endpoint for conversational Q&A with SSE streaming.

| Function | Type | Description |
|----------|------|-------------|
| `ask_the_stars` | `@https_fn.on_request` | HTTPS endpoint with SSE streaming for Ask the Stars feature |
| `stream_ask_the_stars_response` | Internal | Synchronous generator that streams LLM responses |

**Flow:**
1. Authenticate user (Firebase ID token or dev token)
2. Fetch: user profile, horoscope, entities, connections, memory, conversation
3. Detect mentioned connections by name matching
4. Calculate synastry for mentioned connections (on-the-fly if not cached)
5. Stream LLM response via SSE
6. Save messages to conversation document

---

### `functions/triggers.py`

Firestore triggers for background processing.

| Function | Type | Trigger Document | Description |
|----------|------|------------------|-------------|
| `extract_entities_on_message` | `@firestore_fn.on_document_written` | `conversations/{conversationId}` | Extracts and merges entities when conversation is updated |

**Flow:**
1. Fire on conversation document write
2. Check if latest message is from user (skip assistant messages)
3. Run entity extraction (LLM call 1)
4. Merge with existing entities (LLM call 2)
5. Route person entities to Connection.arca_notes
6. Update memory collection

---

## 2. Core Library Files

### `functions/astro.py` (~900 lines)

Type-safe astrology module built on `natal` library.

**Enums:**

| Enum | Values | Description |
|------|--------|-------------|
| `ZodiacSign` | 12 signs | aries, taurus, ..., pisces |
| `Planet` | 11 bodies | sun, moon, mercury, ..., pluto, north_node |
| `CelestialBody` | 15 bodies | All planets + asc, ic, dsc, mc |
| `Element` | 4 elements | fire, earth, air, water |
| `Modality` | 3 modalities | cardinal, fixed, mutable |
| `AspectType` | 6 types | conjunction, opposition, trine, square, sextile, quincunx |
| `House` | 12 houses | Enum with `.meaning` and `.ordinal` properties |
| `ChartType` | 2 types | natal, transit |

**Pydantic Models:**

| Model | Description |
|-------|-------------|
| `PlanetPosition` | Planet with sign, house, retrograde, element, modality |
| `HouseCusp` | House cusp with sign, ruler, classic ruler |
| `AspectData` | Aspect between two celestial bodies |
| `AnglePosition` | Position of Asc/IC/Dsc/MC |
| `ChartAngles` | All 4 angles |
| `NatalChartData` | Complete chart with planets, houses, aspects, distributions |
| `ElementDistribution` | Planet counts by element |
| `ModalityDistribution` | Planet counts by modality |
| `QuadrantDistribution` | Planet counts by quadrant |
| `HemisphereDistribution` | Planet counts by hemisphere |
| `LunarPhase` | Lunar phase with emoji, energy, guidance |
| `NatalTransitAspect` | Aspect between natal and transit chart |
| `SunSignProfile` | Complete sun sign profile (40+ fields) |

**Key Functions:**

| Function | Description |
|----------|-------------|
| `get_sun_sign(birth_date)` | Calculate sun sign from birth date |
| `get_sun_sign_profile(sun_sign)` | Load sun sign profile from JSON |
| `get_astro_chart(utc_dt, lat, lon, chart_type)` | Generate complete chart |
| `compute_birth_chart(birth_date, birth_time, ...)` | User-friendly wrapper returning (chart_dict, is_exact) |
| `calculate_solar_house(sun_sign, transit_sign)` | Calculate house using whole sign system |
| `find_natal_transit_aspects(natal, transit, orb)` | Find aspects between natal and transit |
| `calculate_lunar_phase(sun_deg, moon_deg)` | Calculate lunar phase |
| `format_transit_summary_for_ui(natal, transit)` | Generate UI-ready transit summary |

**Constants:**
- `SIGN_RULERS` - Modern astrology rulerships

---

### `functions/llm.py` (~600 lines)

LLM integration for horoscope generation.

**Key Functions:**

| Function | Description |
|----------|-------------|
| `generate_daily_horoscope(...)` | Main horoscope generation with astrometers and transit summary |
| `select_featured_connection(connections, memory, date)` | Select one connection for relationship weather (rotation logic) |
| `update_memory_with_connection_mention(memory, connection, date, context)` | Track featured connections for rotation |

**Output Models:**

| Model | Description |
|-------|-------------|
| `DailyHoroscope` | Complete daily horoscope response |
| `ActionableAdvice` | do/don't/reflect_on guidance |
| `RelationshipWeather` | Featured connection insight |
| `MoonDetail` | Lunar interpretation |
| `AstrometersResponse` | All meter groups with interpretations |
| `MeterGroupResponse` | Single meter group data for iOS |

**Templates Used:**
- `templates/horoscope/daily_dynamic.j2`

---

### `functions/models.py` (~800 lines)

All Pydantic data models for the application.

**User & Profile Models:**

| Model | Description |
|-------|-------------|
| `UserProfile` | User with birth data, natal chart |
| `MemoryCollection` | Server-side personalization data |
| `CategoryEngagement` | Per-category engagement tracking |
| `RelationshipMention` | Tracked relationship mentions for rotation |

**Entity System Models:**

| Model | Description |
|-------|-------------|
| `Entity` | Tracked entity (person, place, topic) |
| `EntityStatus` | active, inactive, merged |
| `EntityCategory` | partner, family, friend, work, etc. |
| `AttributeKV` | Key-value attribute |
| `UserEntities` | User's entity collection |
| `ExtractedEntity` | Entity from extraction LLM |
| `ExtractedEntities` | Extraction result |
| `EntityMergeAction` | Merge action (create/merge/update/link) |
| `MergedEntities` | Merge result |

**Conversation Models:**

| Model | Description |
|-------|-------------|
| `Message` | Single message with role |
| `MessageRole` | user, assistant, system |
| `Conversation` | Full conversation with messages |

**Horoscope Models:**

| Model | Description |
|-------|-------------|
| `CompressedHoroscope` | Stored horoscope (compressed format) |
| `UserHoroscopes` | User's horoscope collection |

**Helper Functions:**

| Function | Description |
|----------|-------------|
| `create_empty_memory(user_id)` | Initialize empty memory collection |
| `calculate_entity_importance_score(entity, current_time)` | Calculate entity importance |

---

### `functions/entity_extraction.py` (~500 lines)

Entity extraction and merging for Ask the Stars.

**Functions:**

| Function | Description |
|----------|-------------|
| `extract_entities_from_message(user_message, current_date, ...)` | LLM call 1: Extract entities from message |
| `merge_entities_with_existing(extracted, existing, ...)` | LLM call 2: Determine merge actions |
| `execute_merge_actions(actions, existing_entities, current_time)` | Execute merge actions (pure function) |
| `get_top_entities_by_importance(entities, limit)` | Get top N entities by importance |
| `route_people_to_connections(entities, connections, date)` | Route person entities to Connection.arca_notes |
| `merge_attributes(existing, updates)` | Merge attribute lists |

**Templates Used:**
- `templates/conversation/extract_entities.j2`
- `templates/conversation/merge_entities.j2`

---

### `functions/compatibility.py` (~700 lines)

Synastry compatibility calculations.

**Constants:**
- `ASPECT_CONFIG` - Aspect angles, orbs, and nature
- `CHALLENGING_CONJUNCTIONS` - Planet pairs where conjunction is challenging
- `ROMANTIC_CATEGORIES` - Planet pairs for romantic categories
- `FRIENDSHIP_CATEGORIES` - Planet pairs for friendship categories
- `COWORKER_CATEGORIES` - Planet pairs for coworker categories

**Models:**

| Model | Description |
|-------|-------------|
| `SynastryAspect` | Single aspect between two charts |
| `CompatibilityCategory` | Score for one category |
| `ModeCompatibility` | Scores for one mode (romantic/friendship/coworker) |
| `CompatibilityResult` | Complete compatibility with all modes |
| `CompositeSummary` | Composite chart summary |

**Functions:**

| Function | Description |
|----------|-------------|
| `calculate_compatibility(user_chart, connection_chart)` | Main compatibility calculation |
| `get_compatibility_from_birth_data(...)` | Convenience wrapper with birth data |
| `calculate_synastry_aspects(chart1, chart2)` | Calculate all synastry aspects |
| `calculate_category_score(aspects, planet_pairs)` | Score for one category |
| `calculate_mode_compatibility(aspects, categories_config)` | Score for one mode |
| `calculate_composite_summary(chart1, chart2)` | Composite midpoints |
| `calculate_synastry_points(user_chart, connection_chart)` | Synastry midpoints for transit checking |
| `find_transits_to_synastry(transit_chart, synastry_points)` | Find transits hitting synastry points |
| `calculate_vibe_score(active_transits)` | Daily vibe score (0-100) |

---

### `functions/connections.py` (~150 lines)

Connection model and management.

**Models:**

| Model | Description |
|-------|-------------|
| `Connection` | Full connection with birth data and compatibility |
| `ArcaNote` | Note attached to connection |

**Functions:**

| Function | Description |
|----------|-------------|
| `create_connection(...)` | Create new connection |
| `update_connection(...)` | Update existing connection |

---

### `functions/moon.py` (~600 lines)

Enhanced Moon transit system.

**Models:**

| Model | Description |
|-------|-------------|
| `VoidOfCourseStatus` | active, not_void, unknown |
| `NextLunarEvent` | Upcoming lunar event |
| `MoonDispositor` | Moon's ruling planet chain |
| `MoonTransitDetail` | Complete Moon transit analysis |

**Functions:**

| Function | Description |
|----------|-------------|
| `get_moon_transit_detail(natal_chart, transit_chart, datetime)` | Main function for Moon analysis |
| `detect_void_of_course(moon, transit, natal, datetime)` | Void-of-course detection |
| `calculate_moon_dispositor(moon_sign, natal, transit)` | Dispositor chain calculation |
| `calculate_next_sign_change(moon, datetime)` | Next sign change timing |
| `find_next_moon_aspect(moon_aspects, datetime)` | Next significant aspect |
| `estimate_next_lunar_phase(phase, datetime)` | Next new/full moon |
| `format_moon_summary_for_llm(moon_detail)` | LLM-friendly formatting |

---

### `functions/posthog_utils.py` (~140 lines)

PostHog integration for LLM observability.

**Functions:**

| Function | Description |
|----------|-------------|
| `capture_llm_generation(...)` | Manually capture LLM event to PostHog |

**Notes:**
- Uses HTTP API directly (not SDK)
- Tracks: model, tokens, latency, generation_type
- Sends `$ai_generation` events

---

### `functions/firebase_secrets.py`

Centralized secret declarations to avoid duplicates.

```python
GEMINI_API_KEY = params.SecretParam("GEMINI_API_KEY")
POSTHOG_API_KEY = params.SecretParam("POSTHOG_API_KEY")
```

---

## 3. Astrometers Module

The astrometers module (`functions/astrometers/`) implements a quantified astrological analysis system with 17 specialized meters organized into 5 groups.

### Module Structure

```
functions/astrometers/
├── __init__.py           # Public API exports
├── hierarchy.py          # Meter/Group enums and mappings
├── core.py               # DTI/HQS calculation engine
├── meters.py             # All 17 meter calculations
├── meter_groups.py       # Group aggregation
├── normalization.py      # Percentile-based normalization
├── quality.py            # Quality factor calculations
├── weightage.py          # Planet weightage calculations
├── transit_power.py      # Transit power calculations
├── dignity.py            # Planetary dignity calculations
├── constants.py          # Threshold constants
├── summary.py            # LLM-ready summary tables
├── show_meters.py        # CLI tool to display configurations
├── labels/               # JSON labels for each meter
│   ├── clarity.json
│   ├── focus.json
│   ├── ... (17 meter files)
│   ├── word_banks.json
│   └── groups/           # Group-level labels
│       ├── mind.json
│       ├── heart.json
│       └── ...
└── calibration/          # Calibration data and scripts
    ├── calibration_constants.json
    ├── calculate_historical_v2.py
    ├── verify_percentile.py
    └── historical_scores_v2.csv
```

### `astrometers/hierarchy.py`

Single source of truth for meter organization.

**Enums:**

| Enum | Values |
|------|--------|
| `Meter` | 17 individual meters |
| `MeterGroupV2` | 5 groups: mind, heart, body, instincts, growth |

**Mappings:**
- `METER_TO_GROUP_V2` - Meter -> Group mapping
- `GROUP_V2_METERS` - Group -> List[Meter] reverse mapping
- `GROUP_V2_DISPLAY_NAMES` - Display names

**Meter Distribution:**
- Mind (3): clarity, focus, communication
- Heart (3): resilience, connections, vulnerability
- Body (3): energy, drive, strength
- Instincts (4): vision, flow, intuition, creativity
- Growth (4): momentum, ambition, evolution, circle

---

### `astrometers/core.py`

DTI and HQS calculation engine.

**Core Formulas:**
- **DTI** (Dual Transit Influence): `Sum(W_i * P_i)` - magnitude of activity
- **HQS** (Harmonic Quality Score): `Sum(W_i * P_i * Q_i)` - supportive vs challenging

**Classes:**

| Class | Description |
|-------|-------------|
| `TransitAspect` | Single aspect for calculation |
| `AspectContribution` | Breakdown of aspect's contribution |
| `AstrometerScore` | Complete DTI/HQS scores |

**Functions:**

| Function | Description |
|----------|-------------|
| `calculate_aspect_contribution(aspect)` | Calculate W_i, P_i, Q_i for one aspect |
| `calculate_astrometers(aspects)` | Sum all aspects to get DTI/HQS |
| `calculate_all_aspects(natal, transit, orb)` | Get all natal-transit aspects |
| `get_score_breakdown_text(score)` | Human-readable breakdown |

---

### `astrometers/meters.py` (~1200 lines)

All 17 meter calculations.

**Models:**

| Model | Description |
|-------|-------------|
| `QualityLabel` | harmonious, challenging, mixed, quiet, peaceful |
| `TrendData` | Day-over-day trend |
| `MeterTrends` | Trends for intensity, harmony, unified_score |
| `MeterReading` | Complete meter reading |
| `AllMetersReading` | All 17 meters + overall |
| `MeterConfig` | Configuration for a meter |

**Key Functions:**

| Function | Description |
|----------|-------------|
| `get_meters(natal, transit, date, ...)` | Calculate all 17 meters |
| `get_meter(name, natal, transit, date)` | Calculate single meter |
| `calculate_meter(name, config, aspects, ...)` | Core meter calculation |
| `calculate_unified_score(intensity, harmony)` | Polar-style score with sigmoid stretch |
| `filter_aspects(aspects, config, natal)` | Filter aspects by meter config |
| `select_featured_meters(all_meters, user_id, date)` | Weighted random selection |

**Unified Score Formula:**
```python
base_direction = (harmony - 50) * 2  # intermediate calc, final output is 0-100
magnitude = 0.3 + 0.7 * (intensity / 100)  # 0.3 to 1.0
raw_score = base_direction * magnitude
stretched = 100 * tanh(raw_score / 60)  # Sigmoid stretch
# Apply asymmetry: boost positive, dampen negative
```

---

### `astrometers/normalization.py`

Percentile-based normalization against calibration data.

**Functions:**

| Function | Description |
|----------|-------------|
| `normalize_intensity(dti, meter_name)` | DTI -> 0-100 intensity |
| `normalize_harmony(hqs, meter_name)` | HQS -> 0-100 harmony |
| `interpolate_percentile(value, percentiles)` | Linear interpolation in percentile range |
| `load_calibration_constants()` | Load from JSON |
| `get_intensity_label(intensity)` | Quiet/Mild/Moderate/High/Extreme |
| `get_harmony_label(harmony)` | Challenging/Mixed/Harmonious |
| `get_meter_interpretation(intensity, harmony)` | Combined interpretation |

**Intensity Thresholds:**
- Quiet: 0-30
- Mild: 31-50
- Moderate: 51-70
- High: 71-85
- Extreme: 86-100

---

### `astrometers/meter_groups.py`

Group aggregation module.

**Functions:**

| Function | Description |
|----------|-------------|
| `build_meter_group_data(group, meters, interpretation, yesterday)` | Build data for one group |
| `build_all_meter_groups(all_meters, interpretations, yesterday)` | Build all 5 groups |
| `get_group_state_label(group_name, intensity, harmony)` | Group-specific bucket label |
| `calculate_group_trends(today, yesterday)` | Calculate group trends |

**Group Bucket Labels:**
| Group | Buckets |
|-------|---------|
| Mind | Overloaded, Hazy, Clear, Sharp |
| Heart | Heavy, Tender, Grounded, Magnetic |
| Body | Depleted, Low Power Mode, Powering Through, Surging |
| Instincts | Disconnected, Noisy, Tuned In, Aligned |
| Growth | Uphill, Pacing, Climbing, Unstoppable |

---

### `astrometers/summary.py`

LLM-ready summary table generators.

**Functions:**

| Function | Description |
|----------|-------------|
| `daily_meters_summary(meters_today)` | All 17 meters in single table |
| `meter_groups_summary(meter_groups)` | 5 groups summary table |

**Table Features:**
- MA indicator (Most Active top 5)
- FC indicator (Fastest Changing top 6)
- Top aspect per meter
- Trend arrows and pace

---

### Other Astrometers Modules

| Module | Description |
|--------|-------------|
| `weightage.py` | Calculate W_i: planet base + dignity + ruler bonus * house multiplier |
| `transit_power.py` | Calculate P_i: aspect base * orb factor * direction * station * transit weight |
| `quality.py` | Calculate Q_i: aspect-dependent quality factor (-1 to +1) |
| `dignity.py` | Planetary dignity scoring |
| `constants.py` | All threshold constants |
| `show_meters.py` | CLI tool to display meter configurations |

---

## 4. Test Structure

```
functions/tests/
├── conftest.py           # Pytest configuration, path setup
├── __init__.py
├── unit/                 # Unit tests (no external deps)
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_entity_extraction.py
│   ├── test_compatibility.py
│   ├── test_sun_signs.py
│   ├── test_natal_charts.py
│   ├── test_moon.py
│   ├── test_transits.py
│   ├── test_enhanced_transits.py
│   └── test_data_validation.py
├── integration/          # Integration tests (require API keys)
│   ├── __init__.py
│   ├── test_ask_the_stars_e2e.py
│   ├── test_llm_integration.py
│   ├── test_entity_merge_conflicts.py
│   ├── test_compatibility_llm.py
│   └── test_compatibility_endpoints.py
└── adversarial/          # Edge case tests
    ├── __init__.py
    ├── test_bug_hunting.py
    ├── test_bug_hunting_part2.py
    ├── test_bug_hunting_part3.py
    ├── test_bug_hunting_part4.py
    ├── test_validation_fixes.py
    └── test_edge_cases.py
```

### Test Coverage by File

| Test File | Tests | Description |
|-----------|-------|-------------|
| `test_models.py` | Entity validation, Pydantic models | |
| `test_entity_extraction.py` | Entity extraction, merge actions | |
| `test_compatibility.py` | Synastry calculations | |
| `test_sun_signs.py` | 13 tests | Sun sign calculation |
| `test_natal_charts.py` | 5 tests | Birth chart computation |
| `test_moon.py` | Moon phase calculations | |
| `test_transits.py` | 10 tests | Transit summary |
| `test_enhanced_transits.py` | Enhanced transit features | |
| `test_bug_hunting*.py` | Adversarial edge cases | |

### Running Tests

```bash
# All tests
uv run pytest functions/tests/

# Unit tests only (fast)
uv run pytest functions/tests/unit/

# Integration tests (requires GEMINI_API_KEY)
GEMINI_API_KEY=xxx uv run pytest functions/tests/integration/

# Adversarial tests
uv run pytest functions/tests/adversarial/

# Single file
uv run pytest functions/tests/unit/test_models.py -v
```

---

## 5. Utility Scripts

### `functions/prototype.py` (~800 lines)

End-to-end prototype demonstrating complete user journey.

**Sections:**
1. User onboarding with birth date
2. Sun sign calculation and profile loading
3. Daily transit data generation
4. LLM-powered horoscope generation
5. Astrometers display
6. Meter groups display
7. Ask the Stars conversation test
8. Performance summary

**Usage:**
```bash
uv run python functions/prototype.py
```

**Output Files:**
- `debug_daily_horoscope.json` - Full horoscope response
- `debug_transit_summary.json` - Transit analysis
- `debug_prompt.txt` - LLM prompt (if DEBUG_PROMPT=1)

---

### Astrometers CLI Tools

| Script | Description |
|--------|-------------|
| `astrometers/show_meters.py` | Display all 17 meter configurations |
| `astrometers/calibration/calculate_historical_v2.py` | Run calibration (~5-10 min) |
| `astrometers/calibration/verify_percentile.py` | Verify distribution quality |
| `astrometers/test_charts_stats_v2.py` | Test meter overlap across 1000 charts |

---

## 6. Templates

### `functions/templates/horoscope/`

| Template | Description |
|----------|-------------|
| `daily_dynamic.j2` | Daily horoscope prompt (transits, meters, moon) |
| `daily_static.j2` | System instructions (cacheable) |
| `personalization.j2` | User profile and memory |

### `functions/templates/conversation/`

| Template | Description |
|----------|-------------|
| `ask_the_stars.j2` | Ask the Stars Q&A prompt |
| `extract_entities.j2` | Entity extraction prompt |
| `merge_entities.j2` | Entity merge decision prompt |

---

## 7. Configuration Files

| File | Description |
|------|-------------|
| `firebase.json` | Firebase project configuration |
| `firestore.rules` | Firestore security rules |
| `firestore.indexes.json` | Firestore indexes |
| `storage.rules` | Cloud Storage rules |
| `pyproject.toml` | Python dependencies (uv) |
| `uv.lock` | Locked dependencies |

---

## 8. Data Files

### `functions/signs/`

12 JSON files with complete sun sign profiles:
- `aries.json`, `taurus.json`, ..., `pisces.json`
- 40+ fields per sign covering 8 life domains

### `functions/astrometers/labels/`

17 JSON files with meter configurations and labels:
- Each meter has: metadata, configuration, state_labels, advice_templates

### `functions/astrometers/calibration/`

| File | Description |
|------|-------------|
| `calibration_constants.json` | P01-P99 percentiles per meter |
| `historical_scores_v2.csv` | Raw scores from calibration run |

---

## Function Dependencies Diagram

```
main.py (Cloud Functions)
├── astro.py (chart calculations)
│   └── natal library
├── llm.py (horoscope generation)
│   ├── astrometers/ (meter system)
│   └── templates/horoscope/
├── compatibility.py (synastry)
├── connections.py (connection management)
└── models.py (Pydantic models)

ask_the_stars.py (HTTP endpoint)
├── models.py
├── entity_extraction.py
│   └── templates/conversation/
└── compatibility.py

triggers.py (Firestore triggers)
├── models.py
└── entity_extraction.py
```

---

## Key Data Flows

### Daily Horoscope Generation

```
iOS Request
    ↓
get_daily_horoscope (main.py)
    ↓
compute_birth_chart (astro.py)
    ↓
get_meters (astrometers/meters.py)
    ↓
generate_daily_horoscope (llm.py)
    ├── Render daily_dynamic.j2
    ├── Build meter groups
    └── LLM generation
    ↓
DailyHoroscope response
```

### Ask the Stars

```
iOS Request (SSE)
    ↓
ask_the_stars (ask_the_stars.py)
    ├── Fetch user data
    ├── Match mentioned connections
    ├── Calculate synastry on-the-fly
    └── Stream response
    ↓
[Background Trigger]
extract_entities_on_message (triggers.py)
    ├── extract_entities_from_message
    ├── merge_entities_with_existing
    └── route_people_to_connections
```

---

*Document generated: 2025-11-28*
*Codebase version: c758b8f (main branch)*

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL RULES

**NEVER use theoretical/constant estimates for normalization:**
- DO NOT use `DTI_MAX_ESTIMATE`, `HQS_MAX_POSITIVE_ESTIMATE`, `HQS_MAX_NEGATIVE_ESTIMATE`
- ALWAYS use empirical calibration data from `calibration_constants.json`
- If calibration data is missing or wrong, re-run calibration scripts
- Theoretical constants are unreliable and produce bad meter readings

**Re-running calibration (when meter filters change):**
```bash
# From project root: /Users/elieb/git/arca-backend
uv run python functions/astrometers/calibration/calculate_historical_v2.py
```
- Calculates DTI/HQS scores across 1,000 diverse charts × 1,827 days × 17 meters = ~31M calculations
- Date range: 2020-01-01 to 2024-12-31 (5 years)
- Updates `functions/astrometers/calibration/calibration_constants.json`
- Outputs `functions/astrometers/calibration/historical_scores_v2.csv` (raw scores)
- Takes ~5-10 minutes to complete
- **MUST run this whenever you change meter configurations or filter logic**

**Verifying distribution quality (after calibration):**
```bash
# From project root: /Users/elieb/git/arca-backend
uv run python functions/astrometers/calibration/verify_percentile.py
```
- Verifies that normalized scores follow proper statistical distribution
- Checks that score 99 happens 1% of the time (P99)
- Checks that score above 90 happens 10% of the time (P90)
- Validates score 50 is the median (P50)
- Takes ~30 seconds
- **Run this after calibration to ensure normalization is working correctly**

**Testing meter overlap/collision (after changing filters):**
```bash
# From project root: /Users/elieb/git/arca-backend
uv run python functions/astrometers/test_charts_stats_v2.py
```
- Tests 1,000 random charts to detect unexpected meter overlaps
- Validates that meters are distinct and measuring different things
- Takes ~2-3 minutes to complete
- **Target: All overlaps < 6% (currently achieved)**
- Run this after calibration to ensure meters aren't too correlated

**Viewing meter configurations (for astrological review):**
```bash
# From project root: /Users/elieb/git/arca-backend
uv run python functions/astrometers/show_meters.py
```
- Displays all 17 meter configurations organized by group
- Shows natal planets, natal houses, and house meanings
- Use this to review meter definitions before making changes
- Takes <1 second

**Managing state labels (user-facing text):**
```bash
# View all state labels in formatted tables
uv run python functions/astrometers/show_all_labels.py

# Validate all labels are ≤2 words (iOS UI constraint)
uv run python functions/astrometers/test_label_word_counts.py
```
- 17 individual meters + 6 meter groups (mind, emotions, body, spirit, growth, overall)
- Each with 15 state labels (5 intensity × 3 quality levels)
- **Critical constraint**: All labels must be 2 words maximum
- Labels use empowering, energy-focused language
- NO clinical terms ("crisis," "burnout"), NO mystical jargon ("psychic," "soul")
- Labels describe cosmic energy available, not emotional states
- See `arca-design.md` for complete technical documentation

## Project Overview

arca-backend is the backend service for a daily tarot and astrology app that provides personalized spiritual guidance through AI-powered readings. The app helps users navigate real-life situations (relationships, career, life transitions) through the lens of ancient spiritual practices.

**Core Functionality:**
- LLM-driven personalized tarot and astrology readings
- Theme tracking and pattern recognition across user journeys
- Evolving insights that adapt to user patterns and growth
- Journey documentation and synthesized insights over time
- Birth chart calculations using astronomical data

**Backend Architecture:**
- **Firebase Cloud Functions** (Python 3.13) - Serverless functions for all backend logic
- **Firestore** - NoSQL database for user data, readings, themes, and journey history
- **Firebase Authentication** - User auth and session management
- **Firebase Hosting** - Static marketing site (Astro-based)
- **Firebase Storage** - Media and asset storage

**Key Technologies:**
- `natal` (v0.9.6+) - High-precision astrology calculations (birth charts, transits, aspects)
- `rich` (v14.2.0+) - Terminal output formatting for development
- `firebase-admin` (v7.1.0+) - Admin SDK for Firebase services
- `firebase-functions` (v0.4.3+) - Cloud Functions framework
- `google-genai` - Gemini API SDK for LLM integration
  - **Production model:** `gemini-2.5-flash` (best balance of speed/quality)
  - **Fast option:** `gemini-2.5-flash-lite` (lowest latency, cost-optimized)
  - **Complex reasoning:** `gemini-2.5-pro` (advanced tasks, slower)
  - **Context caching:** Available for cost optimization on repeated contexts
    - Minimum tokens: 1,024 (Flash), 2,048-4,096 (Pro)
    - Default TTL: 1 hour (configurable)
    - Use case: Cache sun sign profiles, natal chart data, static system instructions
    - Reduces costs by ~50-90% on cached input tokens
    - Requires explicit model version suffix (e.g., `gemini-2.0-flash-001`)
    - API methods:
      ```python
      # Create cache
      cache = client.caches.create(
          model='models/gemini-2.0-flash-001',
          config=types.CreateCachedContentConfig(
              display_name='cache-name',
              system_instruction='...',
              contents=[...],
              ttl="3600s"  # or expiration_time
          )
      )

      # Use cached content
      response = client.models.generate_content(
          model=model,
          contents='query',
          config=types.GenerateContentConfig(cached_content=cache.name)
      )

      # List/Get/Update/Delete
      client.caches.list()
      client.caches.get(name=cache_name)
      client.caches.update(name=cache_name, config=types.UpdateCachedContentConfig(ttl='300s'))
      client.caches.delete(cache.name)

      # Check cache hits in response
      print(response.usage_metadata.cached_content_token_count)
      ```
- `jinja2` - Prompt templating system
  - **Template architecture:** Modular design with static/dynamic/personalization split
  - **Location:** `functions/templates/horoscope/`
  - **Daily Horoscope Templates (Single-Prompt Architecture):**
    - `daily_static.j2` - System instructions, task, style guidelines (cacheable, shared across all users)
    - `daily_dynamic.j2` - Today's transits, lunar data, astrometers, meter groups (changes daily, not cacheable)
    - `personalization.j2` - User profile, natal chart, memory (not cacheable - memory updates frequently)
  - **Composition:**
    ```
    Daily Horoscope Prompt = daily_static + daily_dynamic + personalization
    ```
  - **Caching strategy:**
    - Static templates: Cacheable (same for all users, changes infrequently)
    - Dynamic content: Not cacheable (transits change daily)
    - Personalization: Not cacheable (memory updates with each reading)
  - **Daily Horoscope Output Fields:**
    - Core fields: `technical_analysis`, `daily_theme_headline`, `daily_overview`, `actionable_advice`
    - Astrometers: Complete meter data with group/meter interpretations and explainability
    - Transit data: Enhanced transit summary with priority transits and critical degrees
    - Moon data: Lunar phase, aspects, void of course, with LLM interpretation
    - Phase 1 extensions:
      - `look_ahead_preview` - Upcoming significant transits (2-3 sentences)
      - `energy_rhythm` - Energy pattern throughout day based on intensity curve (1-2 sentences)
      - `relationship_weather` - Interpersonal dynamics from relationship meters (2-3 sentences)
      - `collective_energy` - Outer planet context showing collective mood (1-2 sentences)
- `pydantic` (v2.12.2+) - Data validation and type safety
- `posthog` - Analytics and LLM observability
  - **PostHog AI Gemini Integration:** `posthog.ai.gemini.Client`
  - **Critical: Async patterns required**
    - ALL Cloud Functions that use PostHog MUST be async
    - MUST use `await posthog.ashutdown()` (not `posthog.shutdown()`)
    - Synchronous functions will NOT send events (serverless functions exit too fast)
  - **Best practices:**
    ```python
    from posthog import Posthog
    from posthog.ai.gemini import Client as PHClient

    # Initialize with debug mode for development
    posthog = Posthog(
        project_api_key=posthog_api_key,
        host="https://us.i.posthog.com",
        debug=True,
        on_error=lambda err, batch: print(f"PostHog error: {err}")
    )
    client = PHClient(api_key=gemini_key, posthog_client=posthog)

    # Generate content with tracking (use client.aio for async)
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
        posthog_distinct_id=user_id,
        posthog_properties={"generation_type": "daily_horoscope"}
    )

    # CRITICAL: Must await shutdown in async functions
    await posthog.ashutdown()
    ```
  - **Why async is required:**
    - Firebase Cloud Functions are serverless - they terminate immediately after return
    - `posthog.shutdown()` is synchronous but doesn't block until events are sent
    - `await posthog.ashutdown()` ensures events are flushed before function exits
    - Without `await`, all PostHog events are lost
  - **Async API methods:**
    - `client.aio.models.generate_content()` - Async content generation
    - `await posthog.ashutdown()` - Async shutdown with event flushing
    - ALL LLM functions MUST be async: `async def generate_daily_horoscope(...)`
    - ALL Cloud Functions MUST be async: `async def get_daily_horoscope(req: ...)`

**Target Platform:** iOS app (this is the backend service)

## Project Structure

```
arca-backend/
├── functions/              # Firebase Cloud Functions (Python)
│   ├── main.py            # Cloud Functions entry point
│   ├── astro.py           # ⭐ Core astrology module with Pydantic models
│   ├── astro_test.py      # ⭐ Comprehensive test suite (60 tests)
│   ├── astrometers/       # ⭐ Quantified meter system (17 meters + 5 groups)
│   │   ├── core.py        # DTI/HQS calculation engine
│   │   ├── meters.py      # All 17 meter calculation functions
│   │   ├── calibration/   # Backtesting scripts and sample charts
│   │   ├── labels/        # JSON labels for LLM interpretation
│   │   └── tests/         # Comprehensive test suite
│   ├── signs/             # ⭐ Sun sign profile data (JSON)
│   │   ├── aries.json     # Complete Aries profile (8 life domains)
│   │   ├── taurus.json    # (etc. for all 12 signs)
│   │   └── ...
│   ├── models.py          # Pydantic data models (UserProfile, MemoryCollection, etc.)
│   ├── llm.py             # LLM integration (Gemini, PostHog)
│   ├── prototype.py       # End-to-end prototype/testing script
│   ├── templates/         # Jinja2 prompt templates
│   │   └── horoscope/     # Horoscope generation templates
│   ├── requirements.txt   # Functions runtime dependencies
│   └── venv/              # Local virtual environment
├── docs/                  # Documentation
│   ├── CLAUDE.md          # This file - complete backend technical guide
│   ├── MVP_PLAN.md        # Complete V1 product/architecture plan
│   ├── IMPLEMENTATION_PLAN.md  # Technical implementation roadmap
│   ├── TODO.md            # Sprint-based task list (current work)
│   ├── ios.md             # iOS integration guide (Firebase functions reference)
│   ├── ASTROLOGY_MODULE.md # Complete astrology API reference
│   ├── astrometers.md     # ⭐ Astrometers system documentation (meters, calibration, backtesting)
│   └── sunsign.json       # Sun sign profile JSON schema
├── public_site/           # Marketing/landing static site (Astro)
│   ├── src/               # Astro source files
│   ├── dist/              # Built static files (for hosting)
│   └── package.json       # Node dependencies
├── firebase.json          # Firebase project configuration
├── firestore.rules        # Firestore security rules
├── firestore.indexes.json # Firestore database indexes
├── storage.rules          # Cloud Storage security rules
├── pyproject.toml         # Python project dependencies (uv)
├── uv.lock               # Locked dependency versions
├── deploy-site.sh        # Site deployment script
└── CLAUDE.md             # Backend overview (see docs/CLAUDE.md for details)
```

## Documentation

**Primary technical reference:**
- **`arca-design.md`** - Complete technical design document (DTI/HQS algorithms, calibration, API reference)

**iOS Integration (in `docs/` directory):**
- **`docs/ios.md`** - Complete iOS integration guide with Swift examples
- **`docs/IOS_DAILY_HOROSCOPE_API.md`** - Detailed daily horoscope API specification
- **`docs/IOS_BREAKING_CHANGES.md`** - Breaking changes log for iOS
- **`docs/ios-super-group-meters.md`** - Super-group meters iOS integration
- **`docs/ios-ask-stars.md`** - Ask the Stars feature iOS guide

**Feature Specs:**
- **`docs/ask_the_stars_feature.md`** - Ask the Stars feature design document
- **`docs/backend-chart-api-spec.md`** - Chart visualization API (future)

**Reference:**
- **`docs/sunsign.json`** - Sun sign profile JSON schema
- **`docs/image_prompts.md`** - Background image generation prompts

## Development Environment

- **Package Manager**: Uses `uv` for Python dependency management (NOT pip)
- **Python Version**: 3.13+
- **Virtual Environment**: `.venv` directory (managed by uv)
- **Firebase CLI**: Required for deployment and emulator usage

## Firebase Configuration

### Firestore Database
- **Location**: nam5 (North America)
- **Collections Structure**:
  - `users/{userId}` - User profile with birth data, preferences
    - `entries/` (subcollection) - Journal entries with readings
    - `insights/` (subcollection) - Consolidated themes and patterns
  - `memory/{userId}` - Server-side only personalization data (NOT client-accessible)

### Cloud Functions
- **Runtime**: Python 3.13
- **Max Instances**: 50 (global default for cost control)
- **Types**:
  - **Callable functions** - Invoked via Firebase SDK from iOS
  - **Firestore triggers** - Automated background processing
- **Async/Await Support**:
  - **IMPORTANT: Firebase Cloud Functions must be synchronous** (firebase-functions SDK limitation)
  - **Internal async functions** (LLM, PostHog) use `async def` and are called via `asyncio.run()`
  - **Pattern:**
    ```python
    import asyncio

    # Cloud Function is SYNC
    @https_fn.on_call(secrets=[GEMINI_API_KEY, POSTHOG_API_KEY])
    def my_function(req: https_fn.CallableRequest) -> dict:
        # Call async LLM function using asyncio.run()
        result = asyncio.run(generate_daily_horoscope(...))
        return result.model_dump()

    # LLM function is ASYNC
    async def generate_daily_horoscope(...) -> DailyHoroscope:
        response = await client.aio.models.generate_content(...)
        await posthog.ashutdown()
        return DailyHoroscope(...)
    ```
  - **Why this pattern:**
    - Firebase Cloud Functions SDK doesn't support `async def` decorators
    - LLM and PostHog operations are async and MUST use `await`
    - `asyncio.run()` bridges sync Cloud Functions with async internal operations
    - PostHog events are properly flushed with `await posthog.ashutdown()`

### Firebase Hosting
- **Public Directory**: `public_site/dist`
- **Framework**: Astro with Tailwind CSS
- **Routing**: SPA mode (all routes → index.html)

### Local Emulators
Configured ports for local development:
- **Auth**: 9099
- **Functions**: 5001
- **Firestore**: 8080
- **Realtime Database**: 9000
- **Storage**: 9199
- **Emulator UI**: Enabled

## Common Commands

### Package Management
```bash
# Add a new package
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Sync dependencies
uv sync
```

### Firebase Development
```bash
# Start all emulators
firebase emulators:start

# Deploy functions only
firebase deploy --only functions

# Deploy hosting only
firebase deploy --only hosting

# Deploy everything
firebase deploy

# Deploy site (custom script)
./deploy-site.sh
```

### Testing
```bash
# Run tests directly with pytest
pytest

# Run a single test file
pytest path/to/test_file.py

# Run a specific test
pytest path/to/test_file.py::test_function_name
```

### Site Development
```bash
cd public_site

# Install dependencies
npm install

# Dev server
npm run dev

# Build
npm run build
```

## API Design

### Callable Functions (iOS → Backend)
Functions in `functions/main.py` decorated with `@https_fn.on_call()`:
- Generate tarot/astrology readings (using `natal` + LLM)
- Create journal entries
- Retrieve user profile and insights
- Query journal history

### Firestore Triggers (Background Processing)
Functions decorated with `@firestore_fn.on_document_created()` etc.:
- `onEntryCreate` - Extract themes when journal entry is created
- `onInsightUpdate` - Update memory collection with patterns
- Theme tracking and evolution analysis
- Journey synthesis for ongoing spiritual narrative

### Security Model
- iOS app calls functions directly via Firebase SDK (no REST endpoints)
- No real-time listeners - data fetched on demand
- Background triggers consolidate insights asynchronously
- Memory collection has strict security rules (server-side only)
- Firestore rules currently in dev mode (expires Nov 15, 2025) - **needs production rules**
- Storage rules locked down (all access denied by default)

## Current Implementation Status

### ✅ Completed - Astrology Core (Sprint 1.4-1.10)
- **Type-safe astrology module** (`functions/astro.py`)
  - 7 production-ready enums (ZodiacSign, Planet, CelestialBody, Element, Modality, AspectType, House, ChartType)
  - 20+ Pydantic models with full validation
  - CelestialBody enum includes planets AND chart angles (Asc, IC, Dsc, MC)
  - Automatic string-to-enum conversion with unicode symbol support
  - North Node included in planets list (11 celestial bodies total)
- **Complete sun sign profile system**
  - 12 JSON profiles with 8 life domains each (40+ fields per sign)
  - Domains: love, family, career, growth, finance, purpose, home, decisions
  - SunSignProfile Pydantic model with strict validation
  - Loaded from `functions/signs/` directory (deployed with Cloud Functions)
- **Astronomical calculations**
  - `get_astro_chart()` - Generate complete natal/transit charts
  - `compute_birth_chart()` - User-friendly wrapper with V1/V2 support
  - `calculate_solar_house()` - Whole sign house system (returns House enum)
  - `summarize_transits()` - Personalized transit summaries for LLM context
  - `get_sun_sign()` - Calculate sun sign from birth date
  - `get_sun_sign_profile()` - Load rich profile data
- **Astrometers system** (`functions/astrometers/`)
  - 17 specialized meters organized into 5 user-facing groups (Mind, Emotions, Body, Spirit, Growth)
  - Dual-metric scoring: Intensity (0-100) + Harmony (0-100)
  - Core algorithms: DTI (Σ W_i × P_i) and HQS (Σ W_i × P_i × Q_i)
  - Empirically calibrated using 2,500+ diverse birth charts
  - Automatic trend calculation (daily changes with STABLE/SLOW/MODERATE/RAPID classification)
  - Backtesting: Validated meter distinctiveness across 1,000 random charts
  - LLM-ready: JSON labels + markdown summary tables for prompt generation
  - See `docs/astrometers.md` for complete documentation
- **Comprehensive test coverage** (60 tests passing)
  - Sun sign calculation tests (13 tests)
  - Sun sign profile validation tests (12 tests with "HARD FAIL" messages)
  - Birth chart computation tests (5 tests)
  - Transit summary tests (10 tests)
  - Solar house calculation tests (17 tests including regression + boundary conditions)
  - Sign rulers tests (3 tests for modern astrology rulerships)
  - Astrometer overlap tests (1,000 random chart validation)
- **Infrastructure**
  - Firebase project setup and configuration
  - Local emulator configuration
  - Cloud Functions scaffolding with natal integration
  - Static marketing site (Astro-based)
  - JSON schema documentation (`docs/sunsign.json`, `docs/astrometers.md`)

### 🚧 In Progress
- LLM integration for personalized readings

### 📋 To Be Implemented
- User authentication and profile management
- Journal entry creation and storage
- Theme extraction and tracking system
- Insight synthesis and memory updates
- Tarot reading logic and interpretation
- Production Firestore security rules
- Production-ready Cloud Functions (error handling, logging)
- Rate limiting and abuse prevention

## Design Principles

### Brand Voice & Tone (CRITICAL)
**Target Audience:** 20-something women navigating relationships, career, life transitions

**Tone:** Direct, actionable, honest, relatable. Write like a wise friend, not a mystical guru.
- Warm, direct, conversational
- Talk like a wise friend over coffee (or texting)
- Use "you" voice throughout
- Encouraging and empowering, never fatalistic
- Don't oversell the mystical angle
- Be honest about challenges without being dramatic

**Language Level:**
- Write at 8th grade reading level
- Use short sentences (15-20 words ideal)
- Avoid academic/mystical words: "catalyze," "manifestation," "archetypal," "synthesize," "profound," "deeply"
- Say things directly and simply
- NO astrology jargon without explanation (for look_ahead: talk like texting a friend, not "Mars stations retrograde")

**Examples:**
- ❌ "This celestial configuration catalyzes a profound recalibration"
- ✅ "Today's planets are pushing you to rethink this area"

- ❌ "Your soul is undergoing profound alchemical transmutation"
- ✅ "You're going through a deep change in how you see yourself"

- ❌ "Transform your resource consciousness"
- ✅ "Rethink how you earn, spend, and value money"

**Prohibitions:**
- Never mention AI, algorithms, meters, or technology to users
- Never give medical, legal, or financial advice
- Never repeat exact phrasing across sections
- Don't use emojis in horoscope text

### Personalization Strategy
- Surface recurring themes organically (e.g., boundaries, self-worth, career courage)
- Connect dots across readings to show how situations relate
- Adapt guidance depth based on user's spiritual journey progression
- Use their name naturally (once in Daily Overview)
- Reference sun sign simply ("As a Gemini, you...")
- Weave in memory data without making it obvious

### User Experience Goals
- Users should feel understood and validated
- Reframe everyday concerns as opportunities for growth
- Be specific and actionable (not vague)
- Make it forward-looking and empowering
- Document and reflect spiritual evolution over time

## Astrology Module Architecture (`functions/astro.py`)

The `astro.py` module provides a type-safe, production-ready astrology API built on top of the `natal` library. It uses Pydantic for validation and enums for type safety.

### Core Enums

All enums inherit from `str` for JSON serialization compatibility:

```python
class ZodiacSign(str, Enum):
    """12 zodiac signs: aries, taurus, gemini, ..., pisces"""

class Planet(str, Enum):
    """11 celestial bodies: sun, moon, mercury, ..., pluto, north_node"""

class CelestialBody(str, Enum):
    """15 bodies: all planets + 4 chart angles (asc, ic, dsc, mc)"""

class Element(str, Enum):
    """4 elements: fire, earth, air, water"""

class Modality(str, Enum):
    """3 modalities: cardinal, fixed, mutable"""

class AspectType(str, Enum):
    """6 aspect types: conjunction, opposition, trine, square, sextile, quincunx"""

class House(int, Enum):
    """12 houses with .ordinal and .meaning properties"""
    FIRST = 1  # .ordinal="1st", .meaning="self, identity, appearance"

class ChartType(str, Enum):
    """Chart types: natal, transit"""
```

### Pydantic Models

**Chart Data Models:**
- `PlanetPosition` - Planet with sign, house, retrograde status, element, modality
- `HouseCusp` - House cusp with sign, ruler, classic ruler (all enums)
- `AspectData` - Aspect between two CelestialBody enums (includes angles!)
- `AnglePosition` - Position of Asc/IC/Dsc/MC
- `ChartAngles` - All 4 angles
- `NatalChartData` - Complete chart with planets, houses, aspects, distributions

**Profile Models:**
- `SunSignProfile` - Complete sun sign profile (40+ fields, 8 life domains)
- `DomainProfiles` - 8 life domains (love, family, career, growth, finance, purpose, home, decisions)
- `LoveAndRelationships`, `FamilyAndFriendships`, etc. - Individual domain models

**Distribution Models:**
- `ElementDistribution` - Planet counts in fire/earth/air/water
- `ModalityDistribution` - Planet counts in cardinal/fixed/mutable
- `QuadrantDistribution` - Planet counts in houses 1-3, 4-6, 7-9, 10-12
- `HemisphereDistribution` - Planet counts in northern/southern, eastern/western

### Key Functions

```python
def get_sun_sign(birth_date: str) -> ZodiacSign:
    """Calculate sun sign from birth date (fixed tropical dates)."""

def get_sun_sign_profile(sun_sign: ZodiacSign) -> SunSignProfile:
    """Load complete sun sign profile from JSON."""

def get_astro_chart(utc_dt: str, lat: float, lon: float,
                   chart_type: ChartType) -> NatalChartData:
    """Generate complete natal/transit chart with full Pydantic validation.
    Includes all 11 planets (10 physical + North Node) and all aspects
    (planet-to-planet AND planet-to-angle).
    """

def compute_birth_chart(birth_date: str, birth_time: str = None,
                       birth_timezone: str = None,
                       birth_lat: float = None,
                       birth_lon: float = None) -> Tuple[dict, bool]:
    """User-friendly wrapper that returns (chart_dict, is_exact).
    V1 mode: No birth time → noon UTC at 0,0 (sun sign accurate)
    V2 mode: Full info → precise chart with houses/angles
    """

def calculate_solar_house(sun_sign: str, transit_sign: str) -> House:
    """Calculate solar house using whole sign system.
    Returns House enum with .ordinal and .meaning properties.
    Example: calculate_solar_house("aries", "virgo") == House.SIXTH
    """

def summarize_transits(transit_chart: dict, sun_sign: str) -> str:
    """Generate personalized transit summary for LLM context.
    Includes: aspects to natal sun, house placements, ruling planet,
    personal/outer planets, retrogrades.
    """
```

### Automatic Validation Features

**Field Validators:**
- String-to-enum conversion (case-insensitive)
- Unicode zodiac symbol mapping (♈→Aries, ♉→Taurus, etc.)
- Mixed format parsing ("♓ pisces" → Pisces)
- Handles natal library's various output formats

**Data Integrity:**
- All planet names validated against Planet enum
- All zodiac signs validated against ZodiacSign enum
- All aspects validated against supported CelestialBody values
- North Node manually added from `data.asc_node` attribute

### Modern Astrology Rulerships

```python
SIGN_RULERS = {
    ZodiacSign.SCORPIO: Planet.PLUTO,      # Modern (traditional: Mars)
    ZodiacSign.AQUARIUS: Planet.URANUS,    # Modern (traditional: Saturn)
    ZodiacSign.PISCES: Planet.NEPTUNE      # Modern (traditional: Jupiter)
    # ... traditional rulers unchanged
}
```

### Sun Sign Profile System

**Data Structure:**
- 12 JSON files in `functions/signs/` (aries.json, taurus.json, etc.)
- 40+ fields per sign covering all life areas
- 8 life domains with detailed subsections
- Complete planetary dignities, correspondences, health patterns
- Compatibility analysis (most compatible, challenging, growth-oriented)

**Validation:**
- Strict tests ensure 100% data completeness
- "HARD FAIL" messages for any missing/incomplete data
- No placeholder text allowed (TBD, TODO, FIXME)
- Element/modality combinations validated (12 unique combos)

### House System

Uses **whole sign houses** for transit calculations:
- Sun sign always occupies 1st house
- Each subsequent sign = next house
- Simple, predictable, works without birth time
- House enum provides semantic meaning for each house

### Usage Example

```python
from astro import compute_birth_chart, get_sun_sign_profile, summarize_transits

# Get complete birth chart
chart_data, is_exact = compute_birth_chart(
    birth_date="1990-06-15",
    birth_time="14:30",
    birth_timezone="America/New_York",
    birth_lat=40.7128,
    birth_lon=-74.0060
)

# Access type-safe enum data
for planet in chart_data["planets"]:
    print(f"{planet['name']} in {planet['sign']}")  # Both are enums

# Get sun sign profile
from astro import ZodiacSign
profile = get_sun_sign_profile(ZodiacSign.GEMINI)
print(profile.domain_profiles.love_and_relationships.style)

# Generate transit summary
transit_chart, _ = compute_birth_chart("2025-10-17", birth_time="12:00")
summary = summarize_transits(transit_chart, "taurus")
# Returns: "Your Sun: Taurus. Transit Sun in Libra at 24.4° ..."
```

## Natal Library Usage

The `natal` library is a powerful Python package built on top of Swiss Ephemeris that automatically calculates ALL astrological data when you create a Data object. Understanding how it works is critical to using it effectively.

### Core Concept: Data Object Does Everything

When you instantiate a `Data` object, it **automatically calculates and stores**:
- Planet positions (sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto, north node)
- House cusps (12 houses using Placidus system by default)
- The 4 angles (Ascendant, IC, Descendant, MC)
- All aspects between bodies (with orbs and applying/separating status)
- Zodiac signs with rulers, elements, modalities
- Quadrant distributions
- Extra bodies (Chiron, Ceres, Pallas, Juno, Vesta) - optional

**Key insight**: You don't need to manually calculate anything. Just create the Data object and access its properties.

### Basic Usage

```python
from natal import Data

# Create chart data - this calculates EVERYTHING
data = Data(
    name="User",                  # Can be anything, we use "User"
    utc_dt="1980-04-20 06:30",   # UTC datetime string "YYYY-MM-DD HH:MM"
    lat=25.0531,                  # Latitude (decimal degrees)
    lon=121.526                   # Longitude (decimal degrees)
)

# Now you have access to all calculated data:
# data.planets - list of Planet objects with positions, speeds, signs
# data.houses - list of House objects with cusps, rulers
# data.aspects - list of Aspect objects between bodies
# data.signs - list of all 12 zodiac signs with metadata
# data.asc, data.ic, data.dsc, data.mc - the 4 angles
# data.quadrants - planet distribution in 4 quadrants
```

### Accessing Planet Data

Each planet in `data.planets` is an `Aspectable` object with rich properties:

```python
for planet in data.planets:
    planet.name          # "sun", "moon", "mercury", etc.
    planet.symbol        # Unicode symbol: ☉, ☽, ☿, etc.
    planet.degree        # Absolute degree position (0-360)
    planet.speed         # Daily motion (negative = retrograde)
    planet.sign          # SignMember object with sign info
    planet.sign.name     # "aries", "taurus", etc.
    planet.sign.symbol   # ♈, ♉, ♊, etc.
    planet.sign.element  # "fire", "earth", "air", "water"
    planet.sign.modality # "cardinal", "fixed", "mutable"
    planet.signed_deg    # Degree within sign (0-29)
    planet.minute        # Arc minutes (0-59)
    planet.retro         # Boolean: True if retrograde
    planet.rx            # String: "℞" if retrograde, "" otherwise
    planet.dms           # Formatted string: "15°23'"
    planet.signed_dms    # Formatted string with sign: "15° ♈ 23'"

    # Get house number for this planet
    house_num = data.house_of(planet)
```

### Accessing House Data

Each house in `data.houses` has:

```python
for house in data.houses:
    house.value              # House number (1-12)
    house.name               # "one", "two", "three", etc.
    house.degree             # Cusp position (0-360)
    house.sign               # SignMember of the cusp sign
    house.ruler              # Planet name that rules this house
    house.ruler_sign         # Sign symbol where ruler is located
    house.ruler_house        # House number where ruler is located
    house.classic_ruler      # Traditional ruler (before outer planets)
    house.classic_ruler_sign # Sign where classic ruler is located
    house.classic_ruler_house # House where classic ruler is located
```

### Accessing Aspects

Aspects are automatically calculated between all visible bodies:

```python
for aspect in data.aspects:
    aspect.body1              # First Aspectable object
    aspect.body2              # Second Aspectable object
    aspect.body1.name         # e.g., "sun"
    aspect.body2.name         # e.g., "moon"
    aspect.aspect_member      # AspectMember object
    aspect.aspect_member.name # "conjunction", "opposition", "trine", "square", "sextile"
    aspect.aspect_member.symbol # ☌, ☍, △, □, ⚹
    aspect.aspect_member.value  # Exact degree: 0, 180, 120, 90, 60
    aspect.orb                # How far from exact (in degrees)
    aspect.applying           # True if applying, False if separating
```

**Orb configuration**: Default orbs are configurable via Config object:
- Conjunction: 7°
- Opposition: 6°
- Trine: 6°
- Square: 6°
- Sextile: 5°
- Quincunx: 0° (disabled by default)

### The Four Angles

Always available as direct properties:

```python
data.asc    # Ascendant (1st house cusp)
data.ic     # Imum Coeli (4th house cusp)
data.dsc    # Descendant (7th house cusp)
data.mc     # Midheaven (10th house cusp)

# Each has degree, sign, symbol, etc. like planets
data.asc.degree
data.asc.sign.name
data.mc.signed_dms
```

### Quadrants

Planets are automatically distributed into quadrants:

```python
# data.quadrants is a list of 4 lists
first_quadrant = data.quadrants[0]   # Houses 1-3 (Self)
second_quadrant = data.quadrants[1]  # Houses 4-6 (Home/Foundation)
third_quadrant = data.quadrants[2]   # Houses 7-9 (Relationships)
fourth_quadrant = data.quadrants[3]  # Houses 10-12 (Social/Career)

# Each contains Aspectable objects (planets in that quadrant)
for planet in first_quadrant:
    print(f"{planet.name} in quadrant 1")
```

### Configuration Options

You can customize calculations with a Config object:

```python
from natal import Data, Config
from natal.const import HouseSys

config = Config(
    house_sys=HouseSys.Placidus,  # or Koch, Whole, etc.
    orb={"conjunction": 8, "trine": 7},  # Custom orbs
)

data = Data(
    name="User",
    utc_dt="1980-04-20 06:30",
    lat=25.0531,
    lon=121.526,
    config=config,
    moshier=True  # Use Moshier ephemeris (faster, no asteroids)
)
```

### Best Practices for LLM Integration

1. **Use the Data object directly** - Don't try to recalculate anything
2. **Access computed properties** - Use `.sign`, `.signed_dms`, `.retro` etc. instead of manual math
3. **Leverage house_of()** - Call `data.house_of(planet)` to get house placements
4. **Check retrograde via `.speed`** - Negative speed = retrograde
5. **Aspects are pre-calculated** - Just iterate through `data.aspects`
6. **Use `.signed_dms` for human-readable output** - Perfect for LLM context
7. **Quadrants tell stories** - Use quadrant distribution for personality insights

### Example: Complete Data Extraction

```python
from natal import Data

def get_chart_for_llm(utc_dt: str, lat: float, lon: float):
    """Extract all natal chart data for LLM interpretation."""
    data = Data(name="User", utc_dt=utc_dt, lat=lat, lon=lon)

    return {
        "planets": [
            {
                "name": p.name,
                "position": p.signed_dms,
                "sign": p.sign.name,
                "house": data.house_of(p),
                "retrograde": p.retro,
                "element": p.sign.element,
                "modality": p.sign.modality
            }
            for p in data.planets
        ],
        "houses": [
            {
                "number": h.value,
                "sign": h.sign.name,
                "ruler": h.ruler,
                "ruler_in": f"{h.ruler_sign} house {h.ruler_house}"
            }
            for h in data.houses
        ],
        "aspects": [
            {
                "aspect": f"{a.body1.name} {a.aspect_member.name} {a.body2.name}",
                "orb": round(a.orb, 1),
                "applying": a.applying
            }
            for a in data.aspects
        ],
        "angles": {
            "ascendant": f"{data.asc.signed_dms} {data.asc.sign.name}",
            "midheaven": f"{data.mc.signed_dms} {data.mc.sign.name}"
        }
    }
```

### Birth Chart vs Transit Chart

**Same function works for both!** The only difference is the datetime you pass:

- **Birth chart**: Use person's birth datetime
- **Transit chart**: Use current datetime (or any moment in time)
- **Synastry**: Create two Data objects and compare
- **Progressions**: Calculate progressed date and create Data object

The natal library handles all astronomical calculations regardless of the time period.

## Important Notes

- **Never commit changes to git** (user preference)
- Always use `uv` commands instead of `pip` for package management
- Call pytest directly rather than through other test runners
- Maintain mystical/sacred tone in all user-facing content
- Keep memory collection server-side only (critical for privacy)
- Cost control: Use max_instances to prevent unexpected scaling
- Firestore rules need hardening before production launch
- always use pytest to write unit test and tests
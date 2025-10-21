# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
  - **Fast Horoscope (Prompt 1):**
    - `daily_static.j2` - System instructions, task, style guidelines (cacheable, shared)
    - `daily_dynamic.j2` - Today's transits, lunar data (changes daily)
    - `personalization.j2` - User profile, natal chart, memory (cacheable per user)
  - **Detailed Horoscope (Prompt 2):**
    - `detailed_static.j2` - System instructions for detailed predictions (cacheable, shared)
    - `detailed_dynamic.j2` - Fast horoscope output + upcoming transits (changes per request)
    - `personalization.j2` - Same shared template (cacheable per user)
  - **Composition:**
    ```
    Fast = daily_static + daily_dynamic + personalization
    Detailed = detailed_static + detailed_dynamic + personalization
    ```
  - **Caching strategy:**
    - Static templates: Cache per model (same for all users)
    - Personalization: Cache per user (natal chart + sun sign profile)
    - Dynamic: Never cache (transits change daily)
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
│   ├── signs/             # ⭐ Sun sign profile data (JSON)
│   │   ├── aries.json     # Complete Aries profile (8 life domains)
│   │   ├── taurus.json    # (etc. for all 12 signs)
│   │   └── ...
│   ├── utils.py           # Core utilities (sun sign, transit summary, etc.)
│   ├── llm.py             # LLM integration (Gemini, PostHog)
│   ├── firestore_ops.py   # Firestore CRUD operations
│   ├── requirements.txt   # Functions runtime dependencies
│   └── venv/              # Local virtual environment
├── docs/                  # Documentation and schema
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
├── CLAUDE.md             # This file
├── MVP_PLAN.md           # Complete V1 product/architecture plan
├── IMPLEMENTATION_PLAN.md # Technical implementation roadmap
└── TODO.md               # Sprint-based task list (current work)
```

## Planning Documents

**Read these to understand the project:**

1. **MVP_PLAN.md** - The complete V1 vision:
   - Product scope (V1-V4 roadmap)
   - User flow and workflows
   - Data models (Firestore collections)
   - Architecture (journal → memory pattern)
   - All 8 interest categories
   - LLM prompt templates
   - Success criteria

2. **IMPLEMENTATION_PLAN.md** - Technical implementation guide:
   - 7 sprints with detailed tasks
   - Module structure (utils, llm, firestore_ops)
   - Test strategy (unit, integration, e2e)
   - Environment setup
   - Timeline estimates
   - Risk mitigation

3. **TODO.md** - Current work tracker:
   - Sprint 1: Core Utilities (sun sign, transit summary)
   - Sprint 2: LLM Integration (Gemini + prompts)
   - Sprint 3: Firestore Operations
   - Sprint 4: Callable Functions
   - Sprint 5: Triggers
   - Sprint 6: Prototype Validation
   - Progress tracking checkboxes

**Start here:** Check TODO.md to see current sprint and tasks.

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
- **Comprehensive test coverage** (60 tests passing)
  - Sun sign calculation tests (13 tests)
  - Sun sign profile validation tests (12 tests with "HARD FAIL" messages)
  - Birth chart computation tests (5 tests)
  - Transit summary tests (10 tests)
  - Solar house calculation tests (17 tests including regression + boundary conditions)
  - Sign rulers tests (3 tests for modern astrology rulerships)
- **Infrastructure**
  - Firebase project setup and configuration
  - Local emulator configuration
  - Cloud Functions scaffolding with natal integration
  - Static marketing site (Astro-based)
  - JSON schema documentation (`docs/sunsign.json`)

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

### Brand Voice & Positioning
- Elevated and sacred (not transactional or fortune-telling)
- Transformational framing (spiritual evolution, not problem-solving)
- Personal and intimate (tailored to individual journeys)
- Ancient wisdom meets modern life
- Accessible to everyone, not gatekept

### Personalization Strategy
- LLM responses must feel mystical and intuitive, like the app "knows" the user
- Surface recurring themes organically (e.g., boundaries, self-worth, career courage)
- Connect dots across readings to show how situations relate
- Adapt guidance depth based on user's spiritual journey progression
- Never explicitly mention AI/technology to users - maintain mystical framing

### User Experience Goals
- Users should feel understood and validated
- Reframe everyday concerns as opportunities for growth
- Create a sacred daily practice, not just an app check-in
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

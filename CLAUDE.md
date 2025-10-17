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
- LLM integration (to be implemented) for generating personalized readings

**Target Platform:** iOS app (this is the backend service)

## Project Structure

```
arca-backend/
├── functions/              # Firebase Cloud Functions (Python)
│   ├── main.py            # Cloud Functions entry point
│   ├── utils.py           # Core utilities (sun sign, transit summary, etc.)
│   ├── llm.py             # LLM integration (Gemini, PostHog)
│   ├── firestore_ops.py   # Firestore CRUD operations
│   ├── astro.py           # Pydantic models for astrology data
│   ├── test_*.py          # Unit and integration tests
│   ├── requirements.txt   # Functions runtime dependencies
│   └── venv/              # Local virtual environment
├── signs/                 # Sun sign data (markdown files)
│   ├── aries.md           # Aries metadata and onboarding fact
│   ├── taurus.md          # (etc. for all 12 signs)
│   └── ...
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
├── prototype.py           # End-to-end validation script
├── test.py                # Astrology functions test script
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
- **Max Instances**: 10 (global default for cost control)
- **Types**:
  - **Callable functions** - Invoked via Firebase SDK from iOS
  - **Firestore triggers** - Automated background processing

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

### Completed
- Firebase project setup and configuration
- Local emulator configuration
- Cloud Functions scaffolding with natal integration
- Static marketing site (Astro-based)
- Basic dependencies and project structure
- Example function using natal for chart calculations

### To Be Implemented
- LLM integration for personalized readings
- User authentication and profile management
- Journal entry creation and storage
- Theme extraction and tracking system
- Insight synthesis and memory updates
- Tarot reading logic and interpretation
- Transit and aspect analysis
- Production Firestore security rules
- Production-ready Cloud Functions
- Error handling and logging
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

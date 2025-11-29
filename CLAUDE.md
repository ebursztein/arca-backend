# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

**For detailed function-level documentation, see `docs/CODEBASE_MAP.md`**

**For iOS API reference (all endpoints + models), see `docs/PUBLIC_API_GENERATED.md`**

---

## Critical Rules

### Never Use Theoretical Constants for Normalization
- DO NOT use `DTI_MAX_ESTIMATE`, `HQS_MAX_POSITIVE_ESTIMATE`, `HQS_MAX_NEGATIVE_ESTIMATE`
- ALWAYS use empirical calibration data from `calibration_constants.json`
- If calibration data is missing, re-run calibration scripts

### Astrometers Calibration Commands

```bash
# Re-run calibration (when meter filters change) - ~5-10 min
uv run python functions/astrometers/calibration/calculate_historical_v2.py

# Verify distribution quality (after calibration) - ~30 sec
uv run python functions/astrometers/calibration/verify_percentile.py

# Test meter overlap (after changing filters) - ~2-3 min
uv run python functions/astrometers/test_charts_stats_v2.py

# View meter configurations
uv run python functions/astrometers/show_meters.py
```

---

## Project Overview

Backend service for a daily astrology app providing personalized guidance through AI-powered readings.

**Stack:**
- Firebase Cloud Functions (Python 3.13)
- Firestore database
- Gemini LLM (`gemini-2.5-flash` / `gemini-2.5-flash-lite`)
- `natal` library for astronomical calculations
- PostHog for LLM observability

**Target Platform:** iOS app

---

## Project Structure

```
arca-backend/
├── functions/
│   ├── main.py              # Cloud Functions entry point (23 callable functions)
│   ├── ask_the_stars.py     # HTTPS endpoint with SSE streaming
│   ├── triggers.py          # Firestore triggers (entity extraction)
│   ├── astro.py             # Chart calculations (~900 lines)
│   ├── llm.py               # Horoscope generation (~600 lines)
│   ├── models.py            # Pydantic models (~800 lines)
│   ├── entity_extraction.py # Entity extraction/merge (~500 lines)
│   ├── compatibility.py     # Synastry calculations (~700 lines)
│   ├── connections.py       # Connection CRUD (~150 lines)
│   ├── moon.py              # Lunar analysis (~600 lines)
│   ├── posthog_utils.py     # LLM observability
│   ├── prototype.py         # End-to-end demo script
│   ├── astrometers/         # 17 meters, 5 groups
│   │   ├── hierarchy.py     # Meter/group enums
│   │   ├── core.py          # DTI/HQS formulas
│   │   ├── meters.py        # Meter calculations
│   │   ├── normalization.py # Percentile normalization
│   │   ├── labels/          # JSON configs per meter
│   │   └── calibration/     # Calibration data
│   ├── templates/
│   │   ├── horoscope/       # daily_dynamic.j2, daily_static.j2
│   │   └── conversation/    # ask_the_stars.j2, extract_entities.j2
│   ├── signs/               # 12 sun sign profiles (JSON)
│   └── tests/
│       ├── unit/            # Fast tests, no deps
│       ├── integration/     # Requires API keys
│       └── adversarial/     # Edge cases
│   └── generate_api_docs.py # Auto-generates PUBLIC_API_GENERATED.md
├── docs/
│   ├── CODEBASE_MAP.md      # Complete function-level documentation
│   └── PUBLIC_API_GENERATED.md  # iOS API reference (auto-generated)
├── firebase.json
├── firestore.rules
└── pyproject.toml
```

---

## Common Commands

### Package Management
```bash
uv add <package>        # Add package
uv add --dev <package>  # Add dev dependency
uv sync                 # Sync dependencies
```

### Testing
```bash
# All tests
uv run pytest functions/tests/

# Unit tests only (fast)
uv run pytest functions/tests/unit/

# Integration tests (requires GEMINI_API_KEY)
GEMINI_API_KEY=xxx uv run pytest functions/tests/integration/

# Single file with verbose
uv run pytest functions/tests/unit/test_models.py -v
```

### Firebase
```bash
firebase emulators:start          # Local development
firebase deploy --only functions  # Deploy functions
firebase deploy                   # Deploy everything
```

### Prototype
```bash
uv run python functions/prototype.py  # Run end-to-end demo
```

### API Documentation
```bash
uv run python functions/generate_api_docs.py  # Regenerate docs/PUBLIC_API_GENERATED.md
```

---

## Key Architecture

### Cloud Functions (main.py)

See `docs/PUBLIC_API_GENERATED.md` for complete API reference with request/response schemas.

| Category | Functions |
|----------|-----------|
| Charts | `natal_chart`, `daily_transit`, `user_transit`, `get_synastry_chart`, `get_natal_chart_for_connection` |
| User | `create_user_profile`, `get_user_profile`, `get_memory`, `get_sun_sign_from_date`, `register_device_token` |
| Horoscope | `get_daily_horoscope`, `get_astrometers` |
| Connections | `create_connection`, `update_connection`, `delete_connection`, `list_connections` |
| Sharing | `get_share_link`, `get_public_profile`, `import_connection`, `update_share_mode`, `list_connection_requests`, `respond_to_request` |
| Compatibility | `get_compatibility` |

### HTTP Endpoints

| Endpoint | Description |
|----------|-------------|
| `ask_the_stars` | SSE streaming Q&A |

### Firestore Triggers

| Trigger | Description |
|---------|-------------|
| `extract_entities_on_message` | Entity extraction on conversation update |

### Astrometers System

17 meters organized into 5 groups:
- **Mind** (3): clarity, focus, communication
- **Heart** (3): resilience, connections, vulnerability
- **Body** (3): energy, drive, strength
- **Instincts** (4): vision, flow, intuition, creativity
- **Growth** (4): momentum, ambition, evolution, circle

**Core Formulas:**
- DTI (intensity): `Sum(W_i * P_i)`
- HQS (harmony): `Sum(W_i * P_i * Q_i)`
- Unified Score: Polar-style combination with sigmoid stretch

---

## Design Principles

### Brand Voice (Critical)

**Audience:** 20-something women navigating relationships, career, life transitions

**Tone:** Direct, actionable, honest. Write like a wise friend, not a mystical guru.

**Language:**
- 8th grade reading level
- Short sentences (15-20 words)
- NO: "catalyze," "manifestation," "archetypal," "synthesize," "profound"
- NO astrology jargon without explanation

**Examples:**
- Bad: "This celestial configuration catalyzes a profound recalibration"
- Good: "Today's planets are pushing you to rethink this area"

**Prohibitions:**
- Never mention AI, algorithms, meters to users
- Never give medical, legal, or financial advice
- No emojis in horoscope text

### Personalization
- Surface recurring themes organically
- Use their name once in Daily Overview
- Reference sun sign simply ("As a Gemini, you...")
- Weave in memory data subtly

---

## Firebase Configuration

**Project ID:** `arca-baf77`
**Region:** us-central1

**Collections:**
- `users/{userId}` - Profile with birth data
- `users/{userId}/horoscopes` - Stored horoscopes
- `users/{userId}/entities` - Tracked entities
- `users/{userId}/connections` - Relationships
- `conversations/{conversationId}` - Ask the Stars chats
- `memory/{userId}` - Server-side personalization (NOT client-accessible)

**Local Emulator Ports:**
- Functions: 5001
- Firestore: 8080
- Auth: 9099

---

## Key Patterns

### Cloud Function + Async LLM

```python
@https_fn.on_call(secrets=[GEMINI_API_KEY])
def my_function(req: https_fn.CallableRequest) -> dict:
    # Cloud Function is SYNC
    result = asyncio.run(generate_async_content(...))
    return result.model_dump()

async def generate_async_content(...):
    # LLM calls are ASYNC
    response = await client.aio.models.generate_content(...)
    await posthog.ashutdown()  # Critical: flush events
    return result
```

### PostHog LLM Tracking

Uses HTTP API via `posthog_utils.py`:
```python
capture_llm_generation(
    posthog_api_key=key,
    distinct_id=user_id,
    model="gemini-2.5-flash",
    provider="gemini",
    prompt=prompt,
    response=response,
    usage=usage_metadata,
    latency=latency_seconds,
    generation_type="daily_horoscope"
)
```

---

## Important Notes

- Use `uv` not pip
- Call pytest directly
- Never commit to git (user preference)
- Keep memory collection server-side only
- All labels must be 2 words max (iOS constraint)
- See `docs/CODEBASE_MAP.md` for complete function reference
- See `docs/PUBLIC_API_GENERATED.md` for iOS API reference (regenerate with `uv run python functions/generate_api_docs.py`)

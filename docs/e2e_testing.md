# E2E Integration Test Suite Plan

## Overview

Create a comprehensive E2E integration test suite covering all 11 user journeys across 29 endpoints.

**Approach:**
- Direct Python function calls for most tests + Firebase emulator for critical flows
- Real Gemini API calls (with markers to optionally skip)
- New `functions/tests/e2e/` directory
- Uses `python-dotenv` for environment variables (`.env` file)
- All 11 user journeys covered (including profile upgrade V1->V2)

---

## Directory Structure

```
functions/tests/e2e/
├── __init__.py
├── conftest.py              # Shared fixtures, markers, setup
├── factories.py             # Test data factories (UserProfile, Connection, Entity, etc.)
├── helpers.py               # Utility functions (mock requests, assertions)
├── ios_schemas.py           # iOS contract validation (required fields per endpoint)
├── emulator_helpers.py      # Firebase emulator interaction
├── test_01_onboarding.py    # Journey 1: create_user_profile, get_user_profile, get_sun_sign_from_date
├── test_02_profile_upgrade.py   # Journey 2: V1->V2 upgrade (add birth time/location, regenerate chart)
├── test_03_daily_horoscope.py   # Journey 3: get_daily_horoscope, get_astrometers
├── test_04_chart_viewing.py     # Journey 4: natal_chart, daily_transit, user_transit
├── test_05_connection_crud.py   # Journey 5: create/list/update/delete_connection
├── test_06_connection_sharing.py # Journey 6: sharing, requests, import
├── test_07_compatibility.py     # Journey 7: get_compatibility (all 3 modes + LLM interpretation)
├── test_08_synastry_chart.py    # Journey 8: get_synastry_chart, chart visualization data
├── test_09_ask_the_stars.py     # Journey 9: SSE streaming endpoint
├── test_10_entity_extraction.py # Journey 10: entity extraction trigger
├── test_11_personalized_horoscope.py # Journey 11: horoscope with memory
└── README.md                # Documentation
```

---

## Key Components

### 1. conftest.py - Shared Fixtures

```python
# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()  # Load from functions/.env or project root

# Core fixtures needed:
@pytest.fixture(scope="session")
def gemini_api_key()          # os.getenv("GEMINI_API_KEY"), skip if not set

@pytest.fixture(scope="module")
def firestore_emulator()      # Skip if emulator not running

@pytest.fixture
def test_user_id()            # Unique ID per test for isolation

@pytest.fixture
def sample_birth_data_minimal()  # V1: birth_date only
def sample_birth_data_full()     # V2: date + time + location

@pytest.fixture
def sample_user_profile()     # Pre-built UserProfile
def sample_natal_chart()      # Pre-computed chart
def sample_connections()      # List of 3 sample connections
def sample_memory()           # Empty memory collection
```

### 2. factories.py - Test Data Factories

- `UserProfileFactory.create()` - Create user profile with computed chart
- `ConnectionFactory.create()` - Create connection with sun sign
- `BirthDataFactory.for_sign(sign)` - Get birth date for specific sun sign
- `BirthDataFactory.ALL_SIGNS` - Dict of all 12 signs with dates
- `EntityFactory.create()` - Create test entity
- `MessageFactory.create_user_message()` / `create_assistant_message()`

### 3. helpers.py - Utilities

- `create_callable_request(data, auth_uid)` - Mock Firebase CallableRequest
- `assert_response_matches_model(response, model_class)` - Pydantic validation
- `assert_json_serializable(data)` - iOS compatibility check
- `parse_sse_stream(response_text)` - Parse SSE events
- `assert_response_size_under(response, max_kb)` - Mobile performance
- `assert_ios_fields_present(response, endpoint_name)` - Validate all iOS-expected fields exist
- `assert_no_extra_fields(response, model_class)` - No unexpected fields sent to iOS

### 4. ios_schemas.py - iOS Contract Validation

Define expected field sets per endpoint (from `docs/PUBLIC_API_GENERATED.md`):

```python
# Expected fields iOS relies on - validates no breaking changes

DAILY_HOROSCOPE_REQUIRED_FIELDS = {
    "date", "sun_sign", "technical_analysis", "daily_theme_headline",
    "daily_overview", "summary", "actionable_advice", "astrometers",
    "moon_detail", "look_ahead_preview", "meter_groups"
}

ACTIONABLE_ADVICE_REQUIRED_FIELDS = {"do", "dont", "reflect_on"}

COMPATIBILITY_REQUIRED_FIELDS = {
    "romantic", "friendship", "coworker", "aspects",
    "composite_summary", "interpretation", "calculated_at"
}

COMPATIBILITY_MODE_FIELDS = {"overall_score", "categories"}

SYNASTRY_CHART_REQUIRED_FIELDS = {
    "user_chart", "connection_chart", "synastry_aspects"
}

USER_PROFILE_REQUIRED_FIELDS = {
    "user_id", "name", "email", "birth_date", "sun_sign",
    "natal_chart", "exact_chart", "created_at", "last_active"
}

CONNECTION_REQUIRED_FIELDS = {
    "connection_id", "name", "birth_date", "sun_sign",
    "relationship_type", "created_at"
}

ASTROMETERS_REQUIRED_FIELDS = {
    "date", "overall_intensity", "overall_harmony",
    "overall_unified_score", "groups"
}

METER_GROUP_REQUIRED_FIELDS = {
    "group_name", "display_name", "unified_score",
    "intensity", "harmony", "meters"
}

# Validation function
def assert_ios_contract(response: dict, endpoint: str) -> None:
    """Validate response has all fields iOS expects."""
    expected = ENDPOINT_SCHEMAS.get(endpoint)
    missing = expected - set(response.keys())
    assert not missing, f"Missing iOS fields for {endpoint}: {missing}"
```

### 5. emulator_helpers.py - Firebase Emulator

- `is_emulator_running()` - Check if emulator available
- `get_emulator_client()` - Get Firestore client
- `clear_test_data(db, test_user_id)` - Cleanup after tests
- `seed_user_profile(db, user_data)` - Insert test user
- `seed_connection(db, user_id, conn_data)` - Insert test connection
- `seed_memory(db, user_id, memory_data)` - Insert memory

---

## Test Markers (pytest)

```python
@pytest.mark.slow      # Tests >30s (LLM generation)
@pytest.mark.llm       # Tests requiring Gemini API
@pytest.mark.emulator  # Tests requiring Firebase emulator
```

Auto-marking in conftest based on fixture usage.

---

## Key Test Cases by Journey

**Every journey includes iOS contract validation:**
- `test_*_ios_required_fields` - All fields iOS expects are present
- `test_*_response_json_serializable` - Response can serialize to JSON for iOS

### Journey 1: Onboarding
- `test_get_sun_sign_all_signs` - Parametrized for all 12 signs
- `test_get_sun_sign_invalid_date_format` - Error handling
- `test_create_user_profile_v1_minimal` - Birth date only (noon-estimated chart)
- `test_create_user_profile_v2_full` - With time/location (exact chart)
- `test_create_user_profile_creates_memory` - Memory initialized
- `test_get_user_profile_updates_last_active`

### Journey 2: Profile Upgrade (V1 -> V2)
- `test_update_profile_adds_birth_time` - Add birth_time triggers chart regeneration
- `test_update_profile_adds_location` - Add lat/lon/timezone
- `test_update_profile_exact_chart_flag` - exact_chart becomes True
- `test_update_profile_preserves_existing_data` - Name, email unchanged
- `test_update_profile_chart_has_accurate_houses` - Houses computed with location
- `test_update_profile_ascendant_changes` - Ascendant differs from V1

### Journey 3: Daily Horoscope
- `test_get_astrometers_returns_17_meters` - All meters present
- `test_get_astrometers_response_structure` - iOS format
- `test_get_daily_horoscope_complete_response` - All required fields
- `test_get_daily_horoscope_with_connections` - Relationship weather
- `test_horoscope_no_emoji_in_text` - Brand voice validation

### Journey 4: Chart Viewing
- `test_natal_chart_has_11_planets` - Sun through Pluto
- `test_natal_chart_has_12_houses` - All cusps with signs
- `test_natal_chart_has_aspects` - Aspects between planets
- `test_daily_transit_defaults_to_today`
- `test_user_transit_personalized_houses` - Houses based on birth location

### Journey 5: Connection CRUD
- `test_create_connection_calculates_sun_sign`
- `test_create_connection_with_full_birth_data` - Exact chart
- `test_list_connections_returns_all`
- `test_update_connection_recalculates_chart`
- `test_delete_connection_removes_from_firestore`

### Journey 6: Connection Sharing
- `test_get_share_link_creates_secret`
- `test_get_public_profile_public_mode` - Full data returned
- `test_get_public_profile_request_mode` - Limited data
- `test_import_connection_creates_connection`
- `test_import_connection_self_rejected` - Can't add yourself
- `test_respond_to_request_approve_creates_connection`
- `test_respond_to_request_reject_deletes_request`

### Journey 7: Compatibility Analysis
- `test_get_compatibility_all_three_modes` - romantic/friendship/coworker scores
- `test_compatibility_romantic_has_6_categories` - emotional, communication, passion, values, growth, stability
- `test_compatibility_friendship_has_5_categories`
- `test_compatibility_coworker_has_5_categories`
- `test_compatibility_scores_0_to_100` - All scores in valid range
- `test_compatibility_includes_llm_interpretation` - headline, summary, strengths, growth_areas, advice
- `test_compatibility_includes_synastry_aspects` - Raw aspect data for iOS
- `test_compatibility_composite_summary` - Composite sun, moon, etc.

### Journey 8: Synastry Chart Visualization
- `test_get_synastry_chart_returns_user_chart` - Inner ring data
- `test_get_synastry_chart_returns_connection_chart` - Outer ring data
- `test_get_synastry_chart_includes_aspects` - Lines between charts
- `test_synastry_aspects_have_orb` - Aspect tightness
- `test_synastry_aspects_have_harmony_flag` - is_harmonious for coloring
- `test_get_natal_chart_for_connection` - Single chart retrieval
- `test_synastry_works_without_exact_charts` - V1 charts work

### Journey 9: Ask the Stars (SSE)
- `test_ask_the_stars_streams_response` - SSE parsing
- `test_ask_the_stars_creates_conversation`
- `test_ask_the_stars_auth_required` - 401 without token
- `test_ask_the_stars_with_mentioned_connection` - Synastry included
- `test_ask_the_stars_continues_conversation` - Uses conversation_id

### Journey 10: Entity Extraction
- `test_entity_extraction_creates_entities` - Trigger fires
- `test_entity_merges_existing` - Deduplication
- `test_entity_routes_to_connection_arca_notes`
- `test_entity_importance_score_updates` - Recency + frequency

### Journey 11: Personalized Horoscope
- `test_horoscope_with_memory_context` - Memory influences output
- `test_horoscope_connection_rotation` - Featured connection cycles
- `test_horoscope_uses_user_name` - Personalization with name

---

## Implementation Order

### Phase 1: Foundation
1. Create `functions/tests/e2e/` directory structure
2. Implement `conftest.py` with fixtures, markers, dotenv loading
3. Implement `factories.py` with all factories
4. Implement `helpers.py` utilities
5. Implement `ios_schemas.py` with field definitions
6. Implement `emulator_helpers.py`

### Phase 2: Non-LLM Tests (fast iteration)
1. `test_04_chart_viewing.py` - Chart calculations only
2. `test_05_connection_crud.py` - Basic CRUD
3. `test_08_synastry_chart.py` - Chart combinations

### Phase 3: Profile & Onboarding
1. `test_01_onboarding.py` - Profile creation
2. `test_02_profile_upgrade.py` - V1 -> V2 upgrade flow

### Phase 4: Social Features
1. `test_06_connection_sharing.py` - Sharing flow
2. `test_07_compatibility.py` - Compatibility analysis (3 modes + LLM)

### Phase 5: Horoscope & Meters
1. `test_03_daily_horoscope.py` - Full horoscope generation
2. `test_11_personalized_horoscope.py` - Memory integration

### Phase 6: Streaming & Triggers
1. `test_09_ask_the_stars.py` - SSE streaming
2. `test_10_entity_extraction.py` - Firestore trigger

### Phase 7: Documentation
1. Write `README.md` with setup and usage
2. Update `CLAUDE.md` with test commands

---

## Running Tests

```bash
# All E2E tests
uv run pytest functions/tests/e2e/ -v

# Skip slow/LLM tests (fast iteration)
uv run pytest functions/tests/e2e/ -v -m "not slow and not llm"

# Only emulator tests
uv run pytest functions/tests/e2e/ -v -m emulator

# Specific journey
uv run pytest functions/tests/e2e/test_01_onboarding.py -v

# With coverage
uv run pytest functions/tests/e2e/ --cov=functions --cov-report=html
```

### Environment Setup
Tests use `python-dotenv` to load from `.env` file (already in project):
```bash
# functions/.env should have:
GEMINI_API_KEY=your-key
POSTHOG_API_KEY=optional

# Start emulator (separate terminal) for emulator tests
firebase emulators:start --only firestore
```

---

## Critical Files to Reference

| File | Purpose |
|------|---------|
| `docs/PUBLIC_API_GENERATED.md` | **iOS API contract - source of truth for required fields** |
| `functions/main.py` | All 23 callable functions - endpoint signatures |
| `functions/models.py` | Pydantic models for response validation |
| `functions/prototype.py` | Patterns for test data and flow |
| `functions/compatibility.py` | Synastry calculations, 3 modes, categories |
| `functions/astro.py` | Chart calculations, get_sun_sign |
| `functions/ask_the_stars.py` | SSE endpoint implementation |
| `functions/triggers.py` | Entity extraction trigger |
| `functions/tests/integration/` | Existing patterns to follow |

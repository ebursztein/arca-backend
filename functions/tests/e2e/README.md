# E2E Integration Test Suite

Comprehensive end-to-end tests covering user journeys across the Arca backend API.

## Quick Start

```bash
# Run all E2E tests (343 tests, ~0.6s)
uv run pytest functions/tests/e2e/ -v

# Run specific test file
uv run pytest functions/tests/e2e/test_04_chart_viewing.py -v

# Skip slow/LLM tests (fast iteration)
uv run pytest functions/tests/e2e/ -v -m "not slow and not llm"
```

## Test Coverage

| Test File | Tests | Description |
|-----------|-------|-------------|
| test_01_onboarding.py | 66 | User profile creation, sun sign calculation |
| test_02_profile_upgrade.py | 17 | V1 -> V2 profile upgrade flow |
| test_03_daily_horoscope.py | 31 | Astrometers: 17 meters, 5 groups |
| test_04_chart_viewing.py | 52 | Natal/transit chart calculations |
| test_05_connection_crud.py | 45 | Connection create/read/update/delete |
| test_06_connection_sharing.py | 28 | Share links, import, request flows |
| test_07_compatibility.py | 17 | Category structure, scores |
| test_08_synastry_chart.py | 30 | Synastry aspects, compatibility |
| test_09_ask_the_stars.py | 17 | SSE parsing, conversation model |
| test_10_entity_extraction.py | 24 | Entity model, categories |
| test_11_personalized_horoscope.py | 16 | Memory model structure |

**Total: 343 tests**

## Directory Structure

```
functions/tests/e2e/
├── conftest.py              # Shared fixtures, markers, setup
├── factories.py             # Test data factories
├── helpers.py               # Utility functions
├── ios_schemas.py           # iOS contract validation
├── emulator_helpers.py      # Firebase emulator utilities
├── test_01_onboarding.py    # Journey 1: User onboarding
├── test_02_profile_upgrade.py   # Journey 2: V1->V2 upgrade
├── test_04_chart_viewing.py     # Journey 4: Chart calculations
├── test_05_connection_crud.py   # Journey 5: Connection CRUD
├── test_06_connection_sharing.py # Journey 6: Sharing flow
├── test_08_synastry_chart.py    # Journey 8: Synastry/compatibility
└── README.md                # This file
```

## Test Categories

### Non-LLM Tests (Fast)
Tests that don't require Gemini API - pure astronomical calculations and business logic:
- Chart calculations (natal, transit, synastry)
- Sun sign determination
- Connection CRUD operations
- Compatibility score calculations
- Model validation

### LLM Tests (Marked with @pytest.mark.llm)
Tests requiring GEMINI_API_KEY:
- Horoscope generation
- Compatibility interpretation
- Ask the Stars streaming

### Emulator Tests (Marked with @pytest.mark.emulator)
Tests requiring Firebase emulator:
- Full Firestore integration
- Trigger testing

## Test Markers

```python
@pytest.mark.slow      # Tests >30s (LLM generation)
@pytest.mark.llm       # Tests requiring Gemini API
@pytest.mark.emulator  # Tests requiring Firebase emulator
```

Run without slow tests:
```bash
uv run pytest functions/tests/e2e/ -m "not slow"
```

## Fixtures

### Birth Data Fixtures
- `sample_birth_data_minimal` - V1 mode (birth_date only)
- `sample_birth_data_full` - V2 mode (date + time + location)
- `sample_connection_birth_data` - Connection birth data

### Chart Fixtures
- `sample_natal_chart` - Pre-computed natal chart
- `sample_transit_chart` - Today's transit chart

### User Fixtures
- `test_user_id` - Unique user ID per test
- `sample_user_profile` - Complete user profile
- `sample_connections` - List of sample connections

## Factories

### BirthDataFactory
```python
# Get birth data for specific sign
birth_data = BirthDataFactory.for_sign("leo")

# Get full birth data with location
birth_data = BirthDataFactory.for_sign_full("gemini", location="new_york")

# All 12 signs available
BirthDataFactory.ALL_SIGNS  # dict of sign -> birth_date
```

### UserProfileFactory
```python
# Create V1 profile (birth date only)
profile = UserProfileFactory.create_v1()

# Create V2 profile (full birth data)
profile = UserProfileFactory.create_v2(location="los_angeles")
```

### ConnectionFactory
```python
# Create connection by relationship type
conn = ConnectionFactory.create_romantic(name="Partner")
conn = ConnectionFactory.create_friend(name="Best Friend")
conn = ConnectionFactory.create_family(name="Mom")
conn = ConnectionFactory.create_coworker(name="Colleague")
```

## iOS Contract Validation

Tests validate responses match iOS-expected fields:

```python
from ios_schemas import (
    assert_user_profile_contract,
    assert_connection_contract,
    assert_compatibility_contract,
    assert_synastry_chart_contract,
)

# Validate response
assert_user_profile_contract(profile_dict)
```

## Environment Setup

Tests use `python-dotenv` to load from `.env`:

```bash
# functions/.env
GEMINI_API_KEY=your-key
POSTHOG_API_KEY=optional
```

For emulator tests:
```bash
# In separate terminal
firebase emulators:start --only firestore
```

## Running with Coverage

```bash
uv run pytest functions/tests/e2e/ --cov=functions --cov-report=html
```

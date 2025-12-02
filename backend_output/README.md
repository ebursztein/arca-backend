# Backend Output - iOS Mock Data

This directory contains real backend responses captured during e2e test runs.

**Use these as mock data for iOS development and testing.**

## How it works

When e2e tests run, each successful backend call is saved to a JSON file in this directory.

## File naming

- `{function_name}.json` - Latest response for each endpoint
- Files are overwritten on each test run to keep data fresh

## File format

Each JSON file contains:

```json
{
  "function_name": "get_daily_horoscope",
  "request": { ... },
  "response": { ... },
  "captured_at": "2024-01-15T10:30:00Z"
}
```

## Regenerating mocks

Run the e2e tests to regenerate all mock data:

```bash
uv run pytest functions/tests/e2e/ -v
```

Or run specific test files:

```bash
uv run pytest functions/tests/e2e/test_03_daily_horoscope.py -v
```

## Available endpoints

See `docs/PUBLIC_API_GENERATED.md` for full API documentation.

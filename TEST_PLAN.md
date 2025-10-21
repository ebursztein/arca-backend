# TEST PLAN - ARCA BACKEND

Complete testing strategy for the Arca backend Firebase Cloud Functions, now with full async/await support.

## Overview

This document describes the **test ladder** - a systematic approach to testing from unit tests through production deployment. Each level builds confidence before moving to the next.

## Recent Changes: Async/Await Migration

**CRITICAL UPDATE:** All Cloud Functions have been migrated to async/await to properly support PostHog analytics in serverless environments.

**What changed:**
- All Cloud Functions: `async def function_name(...)`
- All LLM functions: `async def generate_daily_horoscope(...)` / `async def generate_detailed_horoscope(...)`
- Gemini API calls: `await client.aio.models.generate_content(...)`
- PostHog shutdown: `await posthog.ashutdown()`

**Why this matters:**
- Serverless functions exit immediately after return
- Without `await`, PostHog events are never sent
- All async I/O operations now properly complete before function exits

## Test Ladder Structure

```
┌─────────────────────────────────────────────────────────┐
│ Level 6: Production Tests (prod_test.py)               │  ← You are here
│   • Tests deployed functions in production             │
│   • Real API keys, real billing                        │
│   • Full end-to-end user flow                          │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ Deploy with firebase deploy
                         │
┌─────────────────────────────────────────────────────────┐
│ Level 5: Deploy to Production                          │
│   • firebase deploy --only functions                   │
│   • Verify deployment succeeded                        │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ Integration tests pass
                         │
┌─────────────────────────────────────────────────────────┐
│ Level 4: Integration Tests (integration_test.py)       │
│   • Full user flow via emulator                        │
│   • Tests LLM generation (requires GEMINI_API_KEY)     │
│   • Tests PostHog analytics (requires POSTHOG_API_KEY) │
│   • Tests Firestore triggers                           │
│   • Requires: firebase emulators:start                 │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ Prototype passes
                         │
┌─────────────────────────────────────────────────────────┐
│ Level 3: Prototype Workflow (prototype.py)             │
│   • End-to-end user journey simulation                 │
│   • Tests personalization & memory continuity          │
│   • Validates architecture before production           │
│   • Requires: firebase emulators:start + API keys      │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ Basic emulator tests pass
                         │
┌─────────────────────────────────────────────────────────┐
│ Level 2: Emulator Tests (test.py)                      │
│   • Tests basic Cloud Functions via emulator           │
│   • No LLM calls (just astrology calculations)         │
│   • Tests: natal_chart, daily_transit, user_transit    │
│   • Requires: firebase emulators:start                 │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │ Unit tests pass
                         │
┌─────────────────────────────────────────────────────────┐
│ Level 1: Unit Tests (functions/astro_test.py)          │
│   • Pure Python unit tests (no Firebase)               │
│   • Tests astrology core functions                     │
│   • Fast feedback loop                                 │
│   • 60+ tests covering sun signs, charts, transits     │
└─────────────────────────────────────────────────────────┘
```

---

## Level 1: Unit Tests

**File:** `functions/astro_test.py`
**Purpose:** Test core astrology functions in isolation
**Duration:** ~5 seconds
**Requirements:** None (pure Python)

### What's Tested
- ✅ Sun sign calculation (13 tests)
- ✅ Sun sign profile validation (12 tests)
- ✅ Birth chart computation (5 tests)
- ✅ Transit summaries (10 tests)
- ✅ Solar house calculations (17 tests)
- ✅ Sign ruler mappings (3 tests)

### Run Command
```bash
pytest functions/astro_test.py -v
```

### Success Criteria
- All 60+ tests pass
- No hard failures (sun sign profiles complete)
- All enum validations pass

### When to Run
- Before every commit
- After modifying astro.py
- As part of CI/CD pipeline

---

## Level 2: Emulator Tests (Basic Functions)

**File:** `test.py`
**Purpose:** Test Cloud Functions via Firebase emulator (no LLM)
**Duration:** ~10 seconds
**Requirements:** Firebase emulator running

### What's Tested
- ✅ `natal_chart` - Birth chart calculation
- ✅ `daily_transit` - Universal daily transits (Tier 1)
- ✅ `user_transit` - Personalized transits (Tier 2)

### Setup
```bash
# Terminal 1: Start emulator
firebase emulators:start

# Terminal 2: Run tests
python test.py
```

### Success Criteria
- All 3 functions return valid chart data
- Response includes: planets, houses, aspects, distributions
- No HTTP errors (5xx, 4xx)

### When to Run
- After Level 1 passes
- Before testing LLM integration
- To verify function deployment works

---

## Level 3: Prototype Workflow Validation

**File:** `prototype.py`
**Purpose:** End-to-end user journey simulation with memory continuity
**Duration:** ~2-3 minutes (multiple LLM calls)
**Requirements:**
- Firebase emulator running
- `GEMINI_API_KEY` environment variable
- `POSTHOG_API_KEY` environment variable

### What's Tested

This simulates a **complete multi-day user journey** to validate:
- ✅ User onboarding flow
- ✅ First horoscope generation (fresh user)
- ✅ Journal entry tracking
- ✅ Memory accumulation
- ✅ Second horoscope (shows continuity/personalization)
- ✅ Multi-day pattern recognition

### User Journey Simulation

```
Day 1: New User
├─ Create profile (Gemini, June 15, 1990)
├─ Generate daily horoscope
├─ User reads "Love & Relationships" category
├─ Add journal entry
└─ Memory updated (trigger)

Day 2: Returning User
├─ Generate daily horoscope
│  └─ Should reference Day 1 themes
├─ User reads "Career & Purpose" category
├─ Add journal entry
└─ Memory shows 2 readings, category counts
```

### Why This Matters

The prototype validates the **core differentiation** of Arca:
1. **Personalization** - Not generic sun sign horoscopes
2. **Memory** - References past readings and patterns
3. **Continuity** - Multi-day narrative, not isolated predictions
4. **Architecture** - Journal → Memory → LLM context flow

### Setup
```bash
# Set environment variables
export GEMINI_API_KEY="your-key"
export POSTHOG_API_KEY="your-key"

# Terminal 1: Start emulator
firebase emulators:start

# Terminal 2: Run prototype
python prototype.py
```

### Success Criteria
- Day 1 horoscope generates successfully
- Memory collection created and populated
- Day 2 horoscope shows continuity (mentions or builds on Day 1)
- User can see personalization improving over time
- No "generic horoscope" vibes
- Memory correctly tracks categories viewed

### Sample Output
```
═══════════════════════════════════════════════════════════
                    DAY 1: NEW USER
═══════════════════════════════════════════════════════════

✓ Profile created: Alex (Gemini ♊)
✓ Daily horoscope generated (1,847ms)

╔══════════════════════════════════════════════════════════╗
║                    Daily Summary                         ║
╠══════════════════════════════════════════════════════════╣
║ Mercury's transit through your communication sector      ║
║ highlights intellectual connections today. The moon in   ║
║ Pisces softens your analytical edge...                   ║
╚══════════════════════════════════════════════════════════╝

User reads: Love & Relationships
✓ Journal entry added
✓ Memory updated

═══════════════════════════════════════════════════════════
                    DAY 2: RETURNING USER
═══════════════════════════════════════════════════════════

✓ Daily horoscope generated (1,923ms)

╔══════════════════════════════════════════════════════════╗
║                    Daily Summary                         ║
╠══════════════════════════════════════════════════════════╣
║ Building on yesterday's theme of communication, today    ║
║ brings opportunities to apply those insights in          ║
║ professional settings...                                 ║
╚══════════════════════════════════════════════════════════╝

✓ References previous day ✨
✓ Shows continuity ✨

Memory State:
  • Total readings: 2
  • Love & Relationships: 1 view
  • Last reading: 2025-10-18
```

### When to Run
- After Level 2 passes
- Before running full integration tests
- After modifying memory/personalization logic
- Before demoing to stakeholders
- To validate "mystical" experience

### Debugging
If personalization isn't working:
- Check memory collection exists in Firestore
- Verify `recent_readings` array has entries
- Check LLM prompt includes memory context
- Look for "generic horoscope" patterns (red flag)

---

## Level 4: Integration Tests (Full LLM Flow)

**File:** `integration_test.py`
**Purpose:** Test complete user flow with LLM generation
**Duration:** ~30-60 seconds (LLM calls)
**Requirements:**
- Firebase emulator running
- `GEMINI_API_KEY` environment variable
- `POSTHOG_API_KEY` environment variable

### What's Tested

#### Step 1: Onboarding
- ✅ `get_sun_sign_from_date` - Calculate sun sign from birth date
- Returns: Sun sign + complete profile (8 life domains)

#### Step 2: User Profile Creation
- ✅ `create_user_profile` - Create user with birth chart
- Creates: User document in Firestore
- Creates: Empty memory collection
- Supports: V1 (birth date only) and V2 (full birth info)

#### Step 3: Daily Horoscope (Prompt 1)
- ✅ `get_daily_horoscope` - Fast daily reading (<2s)
- **Uses async LLM calls:** `await client.aio.models.generate_content()`
- **PostHog tracking:** `await posthog.ashutdown()`
- Returns: 8 core fields (theme, overview, summary, advice, etc.)

#### Step 4: Detailed Horoscope (Prompt 2)
- ✅ `get_detailed_horoscope` - Deep predictions (~5s)
- **Uses async LLM calls:** `await client.aio.models.generate_content()`
- **PostHog tracking:** `await posthog.ashutdown()`
- Returns: 8 life categories (love, career, growth, etc.)

#### Step 5: Journal Entry
- ✅ `add_journal_entry` - Record what user read
- Creates: Journal entry in subcollection
- Triggers: `update_memory_on_journal_entry` (async trigger)

#### Step 6: Memory Verification
- ✅ `get_memory` - Verify trigger updated memory
- Checks: Category counts, recent readings
- Validates: Journal → Memory pattern

### Setup
```bash
# Set environment variables
export GEMINI_API_KEY="your-key"
export POSTHOG_API_KEY="your-key"

# Terminal 1: Start emulator
firebase emulators:start

# Terminal 2: Run integration tests
python integration_test.py
```

### Success Criteria
- All 6 test steps pass
- Daily horoscope generates in <2s
- Detailed horoscope generates in <5s
- PostHog events are sent (check debug output)
- Firestore trigger updates memory within 3s
- Memory collection has correct data

### When to Run
- After Level 2 passes
- Before deploying to production
- After modifying LLM prompts
- After changing async patterns

### Debug Output
The test prints:
- PostHog initialization messages
- LLM generation times
- Usage metadata (tokens, cache hits)
- Memory state after trigger

---

## Level 5: Deploy to Production

**Purpose:** Deploy functions to Firebase Cloud Functions
**Duration:** ~3-5 minutes
**Requirements:** Firebase CLI authenticated

### Deploy Commands
```bash
# Deploy everything (functions + hosting)
firebase deploy

# Deploy functions only (recommended)
firebase deploy --only functions

# Deploy specific function (for hotfixes)
firebase deploy --only functions:get_daily_horoscope
```

### What Gets Deployed
- All Cloud Functions from `functions/main.py`
- All dependencies from `functions/requirements.txt`
- Secret access configured: `GEMINI_API_KEY`, `POSTHOG_API_KEY`
- Runtime: Python 3.13
- Max instances: 50 (cost control)

### Verify Deployment
```bash
# Check function status
firebase functions:list

# View function logs
firebase functions:log
```

### Success Criteria
- All functions deploy without errors
- Functions appear in Firebase Console
- No cold start errors in logs
- Secrets are accessible

### When to Deploy
- After Level 3 integration tests pass
- After code review/approval
- During scheduled deployment windows
- For production hotfixes (after testing in emulator)

---

## Level 6: Production Tests

**File:** `prod_test.py`
**Purpose:** Verify deployed functions work in production
**Duration:** ~30-60 seconds
**Requirements:** Functions deployed to production

### What's Tested
Same 6-step flow as integration tests, but against production endpoints:
1. ✅ Get sun sign
2. ✅ Create user profile
3. ✅ Generate daily horoscope (with PostHog)
4. ✅ Generate detailed horoscope (with PostHog)
5. ✅ Add journal entry
6. ✅ Verify memory (trigger)

### Run Command
```bash
python prod_test.py
```

### Production Endpoint
```
https://us-central1-arca-baf77.cloudfunctions.net/{function_name}
```

### Success Criteria
- All 6 tests pass against production
- Response times match emulator performance
- PostHog events appear in PostHog dashboard
- Real billing charges are minimal (Flash-lite model)
- No errors in Firebase Functions logs

### When to Run
- Immediately after deploying to production
- Before announcing release to users
- As part of smoke testing
- After production hotfixes

### Monitoring
After tests pass, check:
- Firebase Console → Functions → Logs
- Firebase Console → Functions → Metrics (invocations, errors, latency)
- PostHog dashboard → Events (should see `ai_generation` events)
- Firestore → Verify test user data

---

## Environment Variables Required

### For Integration & Production Tests
```bash
# Gemini API (Google AI Studio)
export GEMINI_API_KEY="your-gemini-api-key"

# PostHog Analytics
export POSTHOG_API_KEY="phc_your-posthog-project-key"
```

### Firebase Secrets (Production)
Configured via Firebase CLI:
```bash
firebase functions:secrets:set GEMINI_API_KEY
firebase functions:secrets:set POSTHOG_API_KEY
```

---

## Test Data

All tests use consistent test data for easy filtering in analytics:

```python
TEST_USER_ID = "integration_test_user"
TEST_NAME = "Alex"
TEST_EMAIL = "alex@test.com"
TEST_BIRTH_DATE = "1990-06-15"  # Gemini
```

**Why consistent data?**
- Easy to filter test events in PostHog
- Can identify test users in Firestore
- Reproducible test results
- Easy to clean up test data

---

## Async Testing Notes

### Critical: Async Functions Are Now Default

All Cloud Functions and LLM functions are async. This affects testing:

**What changed:**
```python
# OLD (doesn't work with PostHog)
def get_daily_horoscope(req):
    result = generate_daily_horoscope(...)
    posthog.shutdown()  # Events lost!
    return result

# NEW (async/await)
async def get_daily_horoscope(req):
    result = await generate_daily_horoscope(...)
    await posthog.ashutdown()  # Events sent!
    return result
```

### Testing Async Functions

Firebase Cloud Functions natively support async:
- No special test setup needed
- Emulator handles async functions correctly
- Production handles async functions correctly

### Verifying PostHog Events

**During tests, look for:**
```
PostHog Initialized: phc_your-key... | host: https://us.i.posthog.com
[PostHog] Event: ai_generation
[PostHog] Flushing events...
[PostHog] Shutdown complete
```

**If you don't see these:**
- PostHog API key is missing
- `await posthog.ashutdown()` is missing
- Debug mode is disabled

---

## Troubleshooting

### Unit Tests Fail
- Check Python version: `python --version` (should be 3.13+)
- Check dependencies: `uv sync`
- Check working directory: should be repo root

### Emulator Tests Fail
- Is emulator running? Check `http://127.0.0.1:5001`
- Check emulator logs for errors
- Verify project ID matches: `arca-baf77`

### Integration Tests Fail
- Is `GEMINI_API_KEY` set? Check `echo $GEMINI_API_KEY`
- Is `POSTHOG_API_KEY` set? Check `echo $POSTHOG_API_KEY`
- Check API key quotas (Gemini rate limits)
- Check emulator logs for async errors

### Production Tests Fail
- Are functions deployed? Check `firebase functions:list`
- Check function logs: `firebase functions:log`
- Verify secrets: Firebase Console → Functions → Secrets
- Check cold start times (first call is slower)

### PostHog Events Not Appearing
- Verify `await posthog.ashutdown()` is called
- Check PostHog project key is correct
- Verify host: `https://us.i.posthog.com`
- Check debug mode is enabled during tests
- Look for flush messages in logs

---

## CI/CD Integration

### Recommended Pipeline

```yaml
# .github/workflows/test.yml (example)
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.13
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run unit tests
        run: pytest functions/astro_test.py -v

      - name: Install Firebase CLI
        run: npm install -g firebase-tools

      - name: Start Firebase emulator
        run: firebase emulators:start --only functions &

      - name: Wait for emulator
        run: sleep 10

      - name: Run emulator tests
        run: python test.py

      - name: Run integration tests
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          POSTHOG_API_KEY: ${{ secrets.POSTHOG_API_KEY }}
        run: python integration_test.py
```

---

## Quick Reference

```bash
# Level 1: Unit tests (5s)
pytest functions/astro_test.py -v

# Level 2: Emulator tests (10s)
firebase emulators:start &  # Terminal 1
python test.py              # Terminal 2

# Level 3: Prototype workflow (2-3 min)
export GEMINI_API_KEY="..."
export POSTHOG_API_KEY="..."
firebase emulators:start &  # Terminal 1
python prototype.py         # Terminal 2

# Level 4: Integration tests (60s)
export GEMINI_API_KEY="..."
export POSTHOG_API_KEY="..."
firebase emulators:start &  # Terminal 1
python integration_test.py  # Terminal 2

# Level 5: Deploy (3-5 min)
firebase deploy --only functions

# Level 6: Production tests (60s)
python prod_test.py
```

---

## Success Metrics

### Performance Targets
- Daily horoscope: <2s (Prompt 1)
- Detailed horoscope: <5s (Prompt 2)
- Unit tests: <10s total
- Emulator tests: <15s total
- Integration tests: <90s total

### Quality Targets
- Unit test coverage: 100% of astro.py
- Integration test coverage: All user-facing functions
- Production test success rate: 100%
- PostHog event delivery: 100%

### Cost Targets (Production)
- Model: `gemini-2.5-flash-lite` (lowest cost)
- Per horoscope: ~$0.001-0.002
- Daily active user cost: ~$0.002-0.004
- Context caching: 50-90% savings on repeated contexts

---

## Next Steps After Testing

Once all tests pass:
1. ✅ Merge to main branch
2. ✅ Tag release: `git tag v1.0.0`
3. ✅ Monitor production logs for 24 hours
4. ✅ Check PostHog dashboard for events
5. ✅ Verify billing is as expected
6. ✅ Begin iOS integration testing
7. ✅ Document any production issues
8. ✅ Update runbooks if needed

---

## Related Documentation

- `CLAUDE.md` - Full project architecture and async patterns
- `MVP_PLAN.md` - Product requirements and data models
- `IMPLEMENTATION_PLAN.md` - Technical implementation roadmap
- `TODO.md` - Current sprint tasks

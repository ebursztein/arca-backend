# V1 Implementation Plan

## Current State
- ✅ Astrology functions: `natal_chart`, `daily_transit`, `user_transit`
- ✅ Astro data models in `astro.py`
- ✅ Firebase emulator setup
- ✅ Test script for astro functions (`test.py`)
- ✅ Prototype validation script (`prototype.py`)
- ✅ Dependencies: `google-genai`, `posthog`, `natal`, `pydantic`, `rich`
- ⬜ Need to add: `pytz` (for timezone conversion in V2+)

## What We Need to Build

### Phase 1: Core Utilities (Pure Python, No Firebase)
**Location**: `functions/utils.py`

1. **Sun Sign Calculator**
   ```python
   def get_sun_sign(birth_date: str) -> str:
       """Convert birth date to sun sign."""
   ```

2. **Sun Sign Facts Database**
   ```python
   SUN_SIGN_FACTS: dict[str, str] = {
       "aries": "...",
       # ... all 12 signs
   }
   ```

3. **Transit Summarizer**
   ```python
   def summarize_transits(transit_chart: dict, sun_sign: str) -> str:
       """Extract key aspects relevant to sun sign for LLM context."""
   ```

4. **Memory Formatter**
   ```python
   def format_memory_for_llm(memory_data: dict) -> str:
       """Format memory collection data for LLM prompt."""
   ```

5. **Birth Chart Computer**
   ```python
   def compute_birth_chart(
       birth_date: str,
       birth_time: str = None,
       birth_timezone: str = None,
       birth_lat: float = None,
       birth_lon: float = None
   ) -> tuple[dict, bool]:
       """
       Compute natal chart from birth info.

       Returns:
           (chart_data, exact_chart)
           - chart_data: NatalChartData dict
           - exact_chart: True if time+location provided, False if approximate

       Approximate chart (V1, no birth time):
           - Use noon UTC (12:00)
           - Use coordinates (0.0, 0.0)
           - Sun sign and planetary positions accurate
           - Houses/angles not meaningful

       Exact chart (V2+, with birth time):
           - Convert local time to UTC using timezone
           - Use actual birth coordinates
           - All data accurate
       """
   ```

**Tests**: `functions/test_utils.py`
- ✓ Test sun sign for all 12 signs (boundary dates)
- ✓ Test transit summarizer with mock data
- ✓ Test memory formatter with various memory states
- ✓ Test birth chart computation (approximate vs exact)
- ✓ Test timezone conversion for exact charts

---

### Phase 2: LLM Integration
**Location**: `functions/llm.py`

1. **Gemini Client Setup**
   ```python
   from google import genai

   def get_gemini_client() -> genai.Client:
       """Initialize Gemini client with API key."""
   ```

2. **PostHog Setup**
   ```python
   from posthog import Posthog

   def get_posthog_client() -> Posthog:
       """Initialize PostHog for LLM analytics."""
   ```

3. **Horoscope Generator**
   ```python
   def generate_horoscope(
       sun_sign: str,
       transit_summary: str,
       memory_context: str,
       date: str
   ) -> dict:
       """
       Generate horoscope via Gemini with PostHog tracking.

       Returns:
       {
           "technical_analysis": str,
           "summary": str,
           "details": {
               "love_relationships": str,
               # ... 8 categories
           }
       }
       """
   ```

4. **Prompt Template**
   ```python
   HOROSCOPE_PROMPT = """
   You are a mystical astrologer...
   [Full prompt from MVP_PLAN.md]
   """
   ```

**Tests**: `functions/test_llm.py`
- ✓ Test with mock Gemini client
- ✓ Test prompt formatting
- ✓ Test PostHog tracking (mock)
- ✓ Test JSON parsing from LLM response
- ✓ Test error handling (API failures)

**Environment Variables Needed**:
- `GEMINI_API_KEY`
- `POSTHOG_API_KEY`
- `POSTHOG_PROJECT_ID`

---

### Phase 3: Firestore Operations
**Location**: `functions/firestore_ops.py`

1. **User Profile Operations**
   ```python
   def create_user_profile_doc(
       db,
       user_id: str,
       name: str,
       email: str,
       birth_date: str,
       birth_time: str = None,  # "HH:MM" if provided
       birth_timezone: str = None,  # e.g. "America/New_York"
       birth_lat: float = None,
       birth_lon: float = None
   ) -> dict:
       """
       Create user profile in Firestore with birth chart.

       Computes natal chart and stores:
       - If birth_time + timezone provided: exact_chart = True
       - If only date: approximate chart (noon UTC), exact_chart = False
       """

   def get_user_profile_doc(db, user_id: str) -> dict:
       """Get user profile from Firestore."""
   ```

2. **Memory Operations**
   ```python
   def get_memory_doc(db, user_id: str) -> dict:
       """Get memory collection for user."""

   def initialize_memory_doc(db, user_id: str) -> None:
       """Initialize empty memory collection."""

   def update_memory_from_journal(db, user_id: str, journal_entry: dict) -> None:
       """Update memory collection based on journal entry (for trigger)."""
   ```

3. **Journal Operations**
   ```python
   def create_journal_entry_doc(db, user_id: str, entry_data: dict) -> str:
       """Create journal entry, return entry_id."""

   def get_journal_entries(db, user_id: str, limit: int = 10) -> list[dict]:
       """Get recent journal entries."""
   ```

**Tests**: `functions/test_firestore_ops.py`
- ✓ Test with Firestore emulator
- ✓ Test CRUD operations for all collections
- ✓ Test user creation with approximate chart (V1)
- ✓ Test user creation with exact chart (V2)
- ✓ Test memory FIFO logic (recent_readings)
- ✓ Test Timestamp handling
- ✓ Test error cases (missing docs, invalid data)

---

### Phase 4: Firebase Callable Functions
**Location**: `functions/main.py` (add to existing file)

1. **create_user_profile**
   ```python
   @https_fn.on_call()
   def create_user_profile(req: https_fn.CallableRequest) -> dict:
       """
       Create user profile and compute birth chart.

       Args:
           user_id: str
           name: str
           email: str
           birth_date: str  # "YYYY-MM-DD"
           birth_time: str (optional)  # "HH:MM" in local time
           birth_timezone: str (optional)  # IANA timezone, e.g. "America/New_York"
           birth_lat: float (optional)  # Birth location latitude
           birth_lon: float (optional)  # Birth location longitude

       Process:
           1. Calculate sun sign from birth_date
           2. If birth_time + timezone + location provided:
              - Compute exact natal chart
              - Store with exact_chart = True
           3. If only date provided:
              - Compute approximate chart (noon UTC at 0,0)
              - Store with exact_chart = False
           4. Store chart data in user profile
           5. Initialize empty memory collection

       Returns:
           {
               "success": bool,
               "user_id": str,
               "sun_sign": str,
               "sun_sign_fact": str,
               "exact_chart": bool,  # True if we have full birth info
               "chart_computed": bool
           }
       """
   ```

2. **get_daily_horoscope**
   ```python
   @https_fn.on_call()
   def get_daily_horoscope(req: https_fn.CallableRequest) -> dict:
       """
       Args:
           user_id: str
           date: str (optional)  # "YYYY-MM-DD"

       Returns:
           {
               "date": str,
               "sun_sign": str,
               "technical_analysis": str,
               "summary": str,
               "details": {...}  # 8 categories
           }

       Process:
           1. Get user profile (sun_sign, birth_date)
           2. Get memory collection
           3. Get daily_transit data
           4. Format memory for LLM
           5. Generate horoscope via LLM
           6. Return (no storage)
       """
   ```

3. **add_journal_entry**
   ```python
   @https_fn.on_call()
   def add_journal_entry(req: https_fn.CallableRequest) -> dict:
       """
       Args:
           user_id: str
           date: str  # "YYYY-MM-DD"
           entry_type: str  # "horoscope_reading"
           summary: str
           categories_viewed: list[dict]  # [{"category": str, "text": str}]
           time_spent_seconds: int

       Returns:
           {
               "success": bool,
               "entry_id": str
           }

       Process:
           1. Validate input
           2. Create journal entry in Firestore
           3. Return entry_id
           4. [Trigger fires automatically]
       """
   ```

**Integration Tests**: `functions/test_integration.py`
- ✓ Test full flow with emulator:
  1. Create user profile
  2. Generate horoscope (no memory)
  3. Add journal entry
  4. Generate horoscope (with memory)
- ✓ Test error cases (missing user, invalid dates)
- ✓ Test with real Gemini API (separate flag)

---

### Phase 5: Firestore Triggers
**Location**: `functions/main.py`

1. **update_memory_on_journal_entry**
   ```python
   @firestore_fn.on_document_created(document="users/{userId}/journal/{entryId}")
   def update_memory_on_journal_entry(event: firestore_fn.Event[firestore_fn.DocumentSnapshot]) -> None:
       """
       Triggered when journal entry is created.

       Process:
           1. Read journal entry from event.data
           2. Get user_id from path
           3. Update memory/{userId}:
              - Increment category counts
              - Update last_mentioned timestamps
              - Add to recent_readings (FIFO, max 10)
       """
   ```

**Tests**: `functions/test_triggers.py`
- ✓ Test trigger firing with emulator
- ✓ Test memory updates are correct
- ✓ Test FIFO queue behavior (11th item removes 1st)
- ✓ Test with multiple journal entries

---

### Phase 6: End-to-End Validation

1. **Run prototype.py**
   - Validates complete workflow
   - Tests with Firebase emulators
   - Visual validation of output

2. **Create integration test suite**
   ```bash
   pytest functions/test_integration.py -v
   ```

3. **Manual testing checklist**
   - [ ] Create user with each sun sign (12 signs)
   - [ ] Generate horoscopes for 7 consecutive days
   - [ ] Verify memory builds correctly
   - [ ] Verify personalization improves over time
   - [ ] Test with real Gemini API
   - [ ] Check PostHog analytics dashboard
   - [ ] Verify LLM token usage is reasonable
   - [ ] Check streaming works (if implemented)

---

## Implementation Order

### Sprint 1: Foundation (No LLM, No Firebase)
1. ✅ Setup complete (already done)
2. ⬜ Write `functions/utils.py` with all utilities
3. ⬜ Write `functions/test_utils.py` and validate
4. ⬜ Run: `pytest functions/test_utils.py -v`

**Deliverable**: Pure Python utilities working and tested

---

### Sprint 2: LLM Integration (No Firebase yet)
1. ⬜ Get Gemini API key and PostHog credentials
2. ⬜ Write `functions/llm.py` with horoscope generator
3. ⬜ Write `functions/test_llm.py` with mocks
4. ⬜ Test with real Gemini API (manual script)
5. ⬜ Validate output quality, adjust prompt

**Deliverable**: LLM generating horoscopes with good quality

---

### Sprint 3: Firestore Operations
1. ⬜ Write `functions/firestore_ops.py`
2. ⬜ Write `functions/test_firestore_ops.py`
3. ⬜ Start emulator: `firebase emulators:start`
4. ⬜ Run: `pytest functions/test_firestore_ops.py -v`

**Deliverable**: Firestore CRUD operations working with emulator

---

### Sprint 4: Callable Functions
1. ⬜ Add 3 callable functions to `functions/main.py`
2. ⬜ Start emulator
3. ⬜ Test with `test.py` (expand it)
4. ⬜ Verify in Emulator UI (http://127.0.0.1:4000)

**Deliverable**: Callable functions working in emulator

---

### Sprint 5: Triggers
1. ⬜ Add trigger to `functions/main.py`
2. ⬜ Write `functions/test_triggers.py`
3. ⬜ Test: Create journal entry → verify memory updates
4. ⬜ Run: `pytest functions/test_triggers.py -v`

**Deliverable**: Trigger automatically updating memory

---

### Sprint 6: End-to-End Validation
1. ⬜ Run: `python prototype.py`
2. ⬜ Fix any issues found
3. ⬜ Write `functions/test_integration.py`
4. ⬜ Run full test suite: `pytest functions/ -v`

**Deliverable**: Complete V1 workflow validated locally

---

### Sprint 7: Production Deployment
1. ⬜ Set environment variables in Firebase:
   ```bash
   firebase functions:secrets:set GEMINI_API_KEY
   firebase functions:secrets:set POSTHOG_API_KEY
   ```
2. ⬜ Deploy functions:
   ```bash
   firebase deploy --only functions
   ```
3. ⬜ Update `prototype.py` to use production URLs
4. ⬜ Test with production functions
5. ⬜ Monitor PostHog dashboard
6. ⬜ Check Firebase logs

**Deliverable**: V1 deployed and working in production

---

## Test Structure

```
functions/
├── main.py                    # All Firebase functions
├── astro.py                   # ✅ Astrology data models
├── utils.py                   # ⬜ Utilities (sun sign, transit summary)
├── llm.py                     # ⬜ LLM integration
├── firestore_ops.py          # ⬜ Firestore CRUD operations
│
├── test_utils.py             # ⬜ Unit tests for utils
├── test_llm.py               # ⬜ Unit tests for LLM (mocked)
├── test_firestore_ops.py     # ⬜ Unit tests for Firestore (emulator)
├── test_triggers.py          # ⬜ Tests for triggers (emulator)
├── test_integration.py       # ⬜ End-to-end tests (emulator)
│
└── conftest.py               # ⬜ Pytest fixtures (db connections, mocks)
```

---

## Environment Setup

**Required Environment Variables**:
```bash
# .env (for local development, don't commit)
GEMINI_API_KEY=your_key_here
POSTHOG_API_KEY=your_key_here
POSTHOG_PROJECT_ID=your_project_id
```

**Firebase Secrets** (for production):
```bash
firebase functions:secrets:set GEMINI_API_KEY
firebase functions:secrets:set POSTHOG_API_KEY
firebase functions:secrets:set POSTHOG_PROJECT_ID
```

---

## Success Criteria

### Unit Tests
- [ ] All utilities tested and passing
- [ ] LLM integration tested with mocks
- [ ] Firestore operations tested with emulator
- [ ] Test coverage > 80%

### Integration Tests
- [ ] Full workflow works in emulator
- [ ] Trigger updates memory correctly
- [ ] Personalization builds over multiple days
- [ ] Error handling works correctly

### Prototype Validation
- [ ] `prototype.py` runs successfully
- [ ] Output quality is good (mystical, personalized)
- [ ] Memory/continuity works as expected
- [ ] Performance is acceptable (< 5s per horoscope)

### Production Validation
- [ ] Functions deployed successfully
- [ ] iOS app can call functions
- [ ] PostHog showing LLM metrics
- [ ] No errors in Firebase logs
- [ ] User feedback is positive

---

## Estimated Timeline

- **Sprint 1 (Utils)**: 1 day
- **Sprint 2 (LLM)**: 2 days (includes prompt tuning)
- **Sprint 3 (Firestore)**: 1 day
- **Sprint 4 (Callables)**: 1 day
- **Sprint 5 (Triggers)**: 1 day
- **Sprint 6 (E2E)**: 1 day
- **Sprint 7 (Deploy)**: 0.5 days

**Total**: ~7.5 days of focused development

---

## Risk Mitigation

### Risk: LLM output quality is poor
- **Mitigation**: Iterate on prompt in Sprint 2 before integrating
- **Backup**: Use multiple example outputs to tune prompt

### Risk: Gemini API rate limits
- **Mitigation**: Monitor PostHog, implement exponential backoff
- **Backup**: Switch to faster model (gemini-1.5-flash)

### Risk: Firestore trigger delays
- **Mitigation**: Triggers are usually <1s, acceptable for V1
- **Backup**: Memory updates are non-blocking, doesn't affect UX

### Risk: Token costs too high
- **Mitigation**: Track in PostHog, optimize prompt length
- **Backup**: Cache transit summaries, reduce context size

---

## Next Steps

1. **Start Sprint 1**: Create `functions/utils.py`
2. **Get API Keys**: Set up Gemini and PostHog accounts
3. **Run tests continuously**: `pytest --watch functions/`

Ready to begin implementation?

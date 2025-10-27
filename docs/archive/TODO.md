# ARCA V1 Implementation TODO

## Sprint 1: Core Astrology Module 🔧 ✅ COMPLETE

- [x] **1.1** ✅ Implement `astro.py`: `get_sun_sign(birth_date)` with ZodiacSign enum
- [x] **1.2** ✅ Write `astro_test.py`: `test_get_sun_sign()` for all 12 signs (13 tests)
- [x] **1.3** ✅ Implement sun sign profile system (12 JSON files with 8 life domains)
- [x] **1.4** ✅ Implement `astro.py`: `compute_birth_chart()` with approximate/exact logic (V1/V2)
- [x] **1.5** ✅ Write `astro_test.py`: `test_compute_birth_chart()` for both modes (5 tests)
- [x] **1.6** ✅ Implement `astro.py`: `summarize_transits()` for basic transit summaries
- [x] **1.7** ✅ Write `astro_test.py`: `test_summarize_transits()` with mock data (10 tests)
- [x] **1.8** ✅ Implement `models.py`: MemoryCollection with `format_for_llm()` method
- [x] **1.9** ✅ Write `astro_test.py`: Test sun sign profiles validation (12 tests)
- [x] **1.10** ✅ Implement `astro.py`: `calculate_solar_house()` with House enum (17 tests)
- [x] **1.11** ✅ Implement ENHANCED transit analysis: `summarize_transits_with_natal()`
- [x] **1.12** ✅ Implement natal-transit aspect analysis (NatalTransitAspect model)
- [x] **1.13** ✅ Implement lunar phase calculations (LunarPhaseInfo model)
- [x] **1.14** ✅ Implement `get_upcoming_transits()` for look-ahead preview
- [x] **1.15** ✅ Implement helper functions: `describe_chart_emphasis()`, `lunar_house_interpretation()`, `format_primary_aspect_details()`
- [x] **1.16** ✅ Run `pytest functions/astro_test.py -v` (60 tests passing, 100% coverage)
- [x] **1.17** ✅ Write complete documentation: `docs/ASTROLOGY_MODULE.md`

**Status**: ✅ Production-ready astrology engine with TRUE personalization via natal-transit aspects

---

## Sprint 2: LLM Integration 🤖 ✅ COMPLETE

- [x] **2.1** ✅ Add `GEMINI_API_KEY` to `.env` file (user-managed)
- [x] **2.2** ✅ Implement `models.py`: Complete Pydantic data models
  - UserProfile, MemoryCollection, JournalEntry
  - DailyHoroscope with enhanced fields (daily_theme_headline, key_active_transit, actionable_advice, etc.)
  - HoroscopeDetails (8 life categories)
  - ActionableAdvice (do/don't/reflect structure)
  - CategoryEngagement, CategoryViewed, RecentReading
  - Helper functions: `create_empty_memory()`, `update_memory_from_journal()`
- [x] **2.3** ✅ Implement `llm.py`: Gemini client initialization with structured output
- [x] **2.4** ✅ Create `templates/horoscope_prompt.j2`: Comprehensive Jinja2 template (350+ lines)
  - User profile section with natal chart overview
  - Enhanced transit analysis with natal-transit aspects
  - Lunar cycle guidance with Moon phase + house interpretation
  - Memory/personalization context
  - All 8 life categories with detailed requirements
  - Style guidelines and output format
- [x] **2.5** ✅ Implement `llm.py`: `generate_horoscope()` with Jinja2 rendering
  - Renders template with user_profile, sun_sign_profile, transit_data, memory
  - Calls Gemini API with `response_schema` for validated output
  - Tracks token usage (input/output/total) and generation time
  - Returns validated DailyHoroscope Pydantic model
- [x] **2.6** ✅ Create `prototype.py`: End-to-end working simulation
  - Complete user journey from onboarding → horoscope → journal entry
  - Rich console output with panels
  - Demonstrates natal-transit aspect analysis (TRUE PERSONALIZATION!)
  - Validates memory update logic
  - Ready for manual testing with real Gemini API
- [ ] **2.7** ⚠️ PostHog analytics integration (deferred - installed but not integrated)
- [ ] **2.8** Write `test_llm.py`: Unit tests with mocked Gemini client (optional, can test with prototype)

**Status**: ✅ LLM generating deeply personalized horoscopes ready for Firebase integration

---

## Sprint 3: Firestore Operations 🔥

- [ ] **3.1** Implement `firestore_ops.py`: `create_user_profile_doc()` with chart storage
- [ ] **3.2** Implement `firestore_ops.py`: `get_user_profile_doc()`
- [ ] **3.3** Write `test_firestore_ops.py`: test user CRUD with emulator
- [ ] **3.4** Implement `firestore_ops.py`: `initialize_memory_doc()` and `get_memory_doc()`
- [ ] **3.5** Write `test_firestore_ops.py`: test memory operations with emulator
- [ ] **3.6** Implement `firestore_ops.py`: `create_journal_entry_doc()`
- [ ] **3.7** Write `test_firestore_ops.py`: test journal operations with emulator
- [ ] **3.8** Implement `firestore_ops.py`: `update_memory_from_journal()` for trigger
- [ ] **3.9** Write `test_firestore_ops.py`: test memory FIFO logic (recent_readings)
- [ ] **3.10** Run `pytest functions/test_firestore_ops.py -v` with emulator

---

## Sprint 4: Callable Functions 📞

- [ ] **4.1** Implement `main.py`: `create_user_profile()` callable function
- [ ] **4.2** Test `create_user_profile` with emulator manually
- [ ] **4.3** Implement `main.py`: `get_daily_horoscope()` callable function
- [ ] **4.4** Test `get_daily_horoscope` with emulator manually
- [ ] **4.5** Implement `main.py`: `add_journal_entry()` callable function
- [ ] **4.6** Test `add_journal_entry` with emulator manually
- [ ] **4.7** Write `test_integration.py`: test full callable flow
- [ ] **4.8** Run `pytest functions/test_integration.py -v`

---

## Sprint 5: Triggers ⚡

- [ ] **5.1** Implement `main.py`: `update_memory_on_journal_entry()` trigger
- [ ] **5.2** Test trigger fires correctly with emulator
- [ ] **5.3** Verify memory updates correctly after journal creation

---

## Sprint 6: Prototype Validation ✅

- [ ] **6.1** Run `python prototype.py` (full end-to-end validation)
- [ ] **6.2** Fix any issues found in prototype
- [ ] **6.3** Validate output quality (mystical, personalized, continuity)

---

## Sprint 7: PostHog (Deferred) 📊

- [ ] **7.1** Add `POSTHOG_API_KEY` and `POSTHOG_PROJECT_ID` to `.env`
- [ ] **7.2** Implement `llm.py`: `get_posthog_client()`
- [ ] **7.3** Add PostHog tracking to `generate_horoscope()`
- [ ] **7.4** Verify metrics in PostHog dashboard

---

## Quick Commands

```bash
# Run all tests
pytest functions/ -v

# Run specific sprint tests
pytest functions/test_utils.py -v
pytest functions/test_llm.py -v
pytest functions/test_firestore_ops.py -v
pytest functions/test_integration.py -v

# Start Firebase emulator (for Sprints 3-6)
firebase emulators:start

# Run prototype
python prototype.py
```

---

## Progress Tracker

- Sprint 1: ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅ (17/17) ✅ COMPLETE
- Sprint 2: ✅✅✅✅✅✅⚠️⬜ (6/8, 2 optional/deferred) ✅ COMPLETE
- Sprint 3: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ (0/10) ← NEXT
- Sprint 4: ⬜⬜⬜⬜⬜⬜⬜⬜ (0/8)
- Sprint 5: ⬜⬜⬜ (0/3)
- Sprint 6: ⬜⬜⬜ (0/3)

**Total: 23/49 tasks complete (47%)**
**Current Status**: Ready for Sprint 3 (Firestore Operations)

---

Let's crush it! 🚀

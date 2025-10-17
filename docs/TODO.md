# ARCA V1 Implementation TODO

## Sprint 1: Core Utilities (Pure Python) 🔧

- [ ] **1.1** Implement `utils.py`: `get_sun_sign(birth_date) -> str`
- [ ] **1.2** Write `test_utils.py`: `test_get_sun_sign()` for all 12 signs
- [ ] **1.3** Implement `utils.py`: `SUN_SIGN_FACTS` dict with 12 facts
- [ ] **1.4** Implement `utils.py`: `compute_birth_chart()` with approximate/exact logic
- [ ] **1.5** Write `test_utils.py`: `test_compute_birth_chart()` for both modes
- [ ] **1.6** Implement `utils.py`: `summarize_transits()` to extract key aspects
- [ ] **1.7** Write `test_utils.py`: `test_summarize_transits()` with mock data
- [ ] **1.8** Implement `utils.py`: `format_memory_for_llm()` for prompt context
- [ ] **1.9** Write `test_utils.py`: `test_format_memory_for_llm()` with various states
- [ ] **1.10** Run `pytest functions/test_utils.py -v` (all utils tests passing)

---

## Sprint 2: LLM Integration 🤖

- [ ] **2.1** Add `GEMINI_API_KEY` to `.env` file
- [ ] **2.2** Implement `llm.py`: `get_gemini_client()` with API key from env
- [ ] **2.3** Implement `llm.py`: `HOROSCOPE_PROMPT` template from MVP_PLAN.md
- [ ] **2.4** Implement `llm.py`: `generate_horoscope()` with technical_analysis + 8 categories
- [ ] **2.5** Write `test_llm.py`: test with mocked Gemini client
- [ ] **2.6** Test manually with real Gemini API (validate output quality)
- [ ] **2.7** Run `pytest functions/test_llm.py -v` (LLM tests passing)

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

- Sprint 1: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ (0/10)
- Sprint 2: ⬜⬜⬜⬜⬜⬜⬜ (0/7)
- Sprint 3: ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ (0/10)
- Sprint 4: ⬜⬜⬜⬜⬜⬜⬜⬜ (0/8)
- Sprint 5: ⬜⬜⬜ (0/3)
- Sprint 6: ⬜⬜⬜ (0/3)

**Total: 0/41 tasks complete**

---

Let's crush it! 🚀

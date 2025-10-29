# Extended Prompt Optimization - Sprint TODO

## Current Status (Sprint 1 Complete ✅)

### Completed Work
- ✅ Smart meter summary integration (71% token reduction in meters section)
- ✅ Zero duplication across tables
- ✅ Dynamic meter descriptions from objects
- ✅ Quality control checklist (20+ verification points)
- ✅ Edge case handling (7 scenarios)
- ✅ Example consolidation (removed 58 redundant lines)
- ✅ Terminology standardization (unified_score consistency)
- ✅ User profile integration in dynamic prompt

### Current Metrics
- **Daily Prompt (Prompt 1)**: ~7,500 tokens (down from ~10,000)
- **Template Length**: 489 lines (static) + 27 lines (dynamic)
- **Generation Time**: ~3.2 seconds

---

## Sprint 2: Detailed Horoscope Prompt Optimization

### Priority 1: Apply Same Optimizations to Prompt 2

**File**: `templates/horoscope/detailed_static.j2` and `detailed_dynamic.j2`

**Tasks**:
1. [ ] Audit current detailed prompt structure and token count
2. [ ] Add TERMINOLOGY section (unified_score, intensity, harmony)
3. [ ] Add METER REFERENCE (if not already using domain_meters efficiently)
4. [ ] Consolidate examples (1-2 per section, remove redundant)
5. [ ] Add QUALITY CONTROL checklist specific to detailed horoscope
6. [ ] Add EDGE CASES for detailed scenarios:
   - What if fast horoscope was QUIET but detailed needs depth?
   - How to expand without being redundant?
   - What if no upcoming transits worth highlighting?

**Expected Impact**: 20-30% token reduction

---

## Sprint 3: Cross-Prompt Consistency

### Priority 2: Ensure Prompt 1 and Prompt 2 Alignment

**Issues to Address**:
1. [ ] **Vocabulary consistency**: Both prompts should use same house synonyms bank
2. [ ] **Tone consistency**: Verify "wise friend" tone is identical across both
3. [ ] **Data format consistency**: Ensure meter data presented identically
4. [ ] **Quality standards**: Same verification checklist structure

**Tasks**:
1. [ ] Create shared vocabulary file (house synonyms, quality labels)
2. [ ] Extract common sections (TERMINOLOGY, METER REFERENCE) into separate template
3. [ ] Use Jinja2 `{% include %}` to reduce duplication
4. [ ] Create unified quality checklist that both prompts reference

**Files to Create**:
- `templates/horoscope/_shared_terminology.j2`
- `templates/horoscope/_shared_meter_reference.j2`
- `templates/horoscope/_shared_quality_checklist.j2`

---

## Sprint 4: Testing & Validation

### Priority 3: Systematic Prompt Testing

**Test Categories**:

**A. Edge Case Testing**
1. [ ] Test all quiet day (overall_intensity < 30)
2. [ ] Test extreme intensity (overall_intensity > 80)
3. [ ] Test score ties (multiple meters at same unified_score)
4. [ ] Test contradictory aspects (HARMONIOUS + CHALLENGING)
5. [ ] Test no active meters scenario
6. [ ] Test fast changing meters (↑↑ or ↓↓)
7. [ ] Test conflicting meter qualities

**B. Quality Metrics**
1. [ ] Measure: Are all claims traced to meter data? (spot check 20 horoscopes)
2. [ ] Measure: House synonym repetition rate (should be 0%)
3. [ ] Measure: User name usage (should be exactly 1x)
4. [ ] Measure: Jargon without explanation (should be 0%)
5. [ ] Measure: Specificity of advice (timing present in 100% of DO actions?)
6. [ ] Measure: Word counts per section (within limits?)

**C. Output Validation Script**
Create `validate_horoscope_output.py`:
```python
def validate_horoscope(horoscope: DailyHoroscope, meters: AllMetersReading) -> ValidationReport:
    """
    Validate horoscope output against quality checklist.

    Returns:
        ValidationReport with pass/fail for each criterion
    """
    checks = {
        'name_used_once': count_name_usage(horoscope),
        'house_synonyms_unique': check_house_repetition(horoscope),
        'actions_have_timing': check_action_specificity(horoscope.actionable_advice),
        'word_counts_valid': check_section_lengths(horoscope),
        'no_forbidden_words': check_banned_words(horoscope),
    }
    return ValidationReport(checks)
```

**Tasks**:
1. [ ] Create validation script
2. [ ] Generate 100 test horoscopes across different scenarios
3. [ ] Run validation suite
4. [ ] Document failure patterns
5. [ ] Iterate on prompt to fix common issues

---

## Sprint 5: Performance & Caching

### Priority 4: Optimize Token Usage and Costs

**Current Costs** (estimated):
- Daily prompt: 7,500 input tokens
- Average output: ~500 tokens
- Cost per generation: ~$0.003 (with Gemini Flash)

**Optimization Opportunities**:

**A. Context Caching**
1. [ ] Identify cacheable vs non-cacheable sections:
   - **Cacheable** (24 hours): Static prompt, meter reference, user natal chart, sun sign profile
   - **Not cacheable**: Today's meters summary, transits, date-specific data
2. [ ] Restructure prompts to group cacheable content first
3. [ ] Implement Gemini context caching:
   ```python
   cache = client.caches.create(
       model='gemini-2.0-flash-001',
       config=types.CreateCachedContentConfig(
           contents=[static_prompt, meter_reference, user_profile],
           ttl="86400s"  # 24 hours
       )
   )
   ```
4. [ ] Measure cache hit rate and cost reduction

**Expected Impact**: 50-70% cost reduction with high cache hit rate

**B. Dynamic Prompt Compression**
1. [ ] Can we compress meters_summary further without losing quality?
2. [ ] Are all trend arrows necessary or can we show only significant changes?
3. [ ] Can KEY ASPECTS table be condensed?

**Tasks**:
1. [ ] Implement caching for static content
2. [ ] A/B test compressed vs full meters summary
3. [ ] Monitor generation quality with reduced context

---

## Sprint 6: Advanced Features

### Priority 5: Smarter Prompt Construction

**A. Adaptive Prompt Depth**
- **Concept**: Adjust prompt detail based on day intensity
- **High intensity day** (>70): Include all edge cases, full meter reference
- **Quiet day** (<30): Simplified prompt focused on integration themes
- **Medium day** (30-70): Standard prompt

**Tasks**:
1. [ ] Create prompt templates for each intensity tier
2. [ ] Implement selection logic in `llm.py`
3. [ ] Test quality across intensity ranges

**B. Few-Shot Learning from Best Outputs**
- **Concept**: Identify highest-rated horoscopes and use as examples
- **Implementation**:
  1. [ ] Create rating system for horoscope quality
  2. [ ] Store top-rated examples
  3. [ ] Dynamically inject best example matching current scenario

**C. Memory-Aware Personalization**
- **Concept**: If user has reading history, adjust prompt
- **First-time user**: Full explanatory style
- **Returning user**: Assume familiarity, more direct
- **Long-term user**: Reference past patterns

**Tasks**:
1. [ ] Add memory_context awareness to prompt
2. [ ] Create user journey stages (new/returning/long-term)
3. [ ] Adjust prompt verbosity based on stage

---

## Sprint 7: Monitoring & Iteration

### Priority 6: Production Observability

**Metrics to Track**:
1. [ ] Generation time (p50, p95, p99)
2. [ ] Token usage (input/output/cached)
3. [ ] Cost per generation
4. [ ] Quality checklist pass rate
5. [ ] Edge case frequency
6. [ ] User engagement metrics (reading completion rate)

**Tools**:
1. [ ] PostHog LLM tracking (already integrated, expand metrics)
2. [ ] Custom validation dashboard
3. [ ] Alert on quality degradation

**Tasks**:
1. [ ] Expand PostHog logging with validation results
2. [ ] Create dashboard in PostHog for prompt performance
3. [ ] Set up alerts for:
   - Generation time >5s
   - Token usage spikes
   - Validation failure rate >5%

---

## Sprint 8: Documentation & Governance

### Priority 7: Prompt Management Best Practices

**A. Prompt Versioning**
1. [ ] Create semantic versioning for prompts (v1.0.0, v1.1.0)
2. [ ] Track changes in CHANGELOG.md
3. [ ] A/B test prompt versions before promoting

**B. Example Bank**
1. [ ] Create separate file: `templates/horoscope/_example_bank.md`
2. [ ] Move removed examples there for reference
3. [ ] Organize by category (intensity, quality, meter type)

**C. Prompt Testing Guidelines**
1. [ ] Document: "How to test a prompt change"
2. [ ] Create regression test suite
3. [ ] Define rollback criteria

**Files to Create**:
- `docs/PROMPT_VERSIONING.md`
- `templates/horoscope/_example_bank.md`
- `docs/PROMPT_TESTING_GUIDE.md`

---

## Quick Wins (Can be done anytime)

1. [ ] Remove "massive", "huge", "profound", "deeply", "incredibly" from any remaining examples
2. [ ] Add "never say" section for common LLM mistakes
3. [ ] Create house synonym exhaustion test (ensure we have enough synonyms)
4. [ ] Add meter state_label glossary for LLM reference
5. [ ] Document DayOfWeek-specific patterns (Monday = new week, Friday = completion)

---

## Measurement Framework

### Before Starting Sprint N, Measure:
- [ ] Current token count (input/output)
- [ ] Current generation time
- [ ] Current cost per horoscope
- [ ] Baseline quality score (manual review of 10 outputs)

### After Completing Sprint N, Measure:
- [ ] New token count (% change)
- [ ] New generation time (% change)
- [ ] New cost per horoscope (% change)
- [ ] New quality score (improvement?)
- [ ] User feedback metrics (if available)

---

## Notes

### Design Principles to Maintain
- **Clarity over cleverness**: Direct language always wins
- **Data-driven**: Every claim traces to meter + aspect
- **Specific over generic**: Timing, quantities, exact actions
- **Empowering over mystical**: Wise friend, not guru
- **Quality over speed**: Better to take 5s and be accurate

### Red Flags to Watch For
- ⚠️ Token count creeping back up (prompt bloat)
- ⚠️ Examples multiplying again (example bloat)
- ⚠️ Quality checklist getting ignored by LLM
- ⚠️ Edge cases not being handled despite instructions
- ⚠️ Generic astrology creeping into outputs

### Success Criteria for "Done"
- ✅ Token usage optimized to <6,000 for daily prompt
- ✅ Caching reduces costs by >50%
- ✅ Quality validation passes >95% of the time
- ✅ Generation time <3 seconds p95
- ✅ User comprehension scores high (subjective, needs user feedback)
- ✅ Zero duplication in outputs (house synonyms, meter references)
- ✅ All 7 edge cases handled gracefully in production

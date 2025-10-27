# Sprint 3: Astrometers Integration with Horoscope Generation

**Status**: Planning
**Duration**: 1-2 weeks
**Dependencies**: Sprint 1 (V1 implementation), Sprint 2 (V2 enhancements), Empirical calibration complete

## Overview

### What Are Astrometers?

**Astrometers** are a quantitative astrological measurement system that replaces subjective "feelings" with data-driven insights. Think of them as the "vital signs" of a person's astrological weather.

**The Problem They Solve**:
- Traditional astrology: "Mars opposite your Sun... that could mean intensity, maybe conflict, depends on context..."
- Astrometers: "Overall Intensity: 87/100 (top 13% of days), Harmony: 23/100 (challenging)"

**Core Philosophy**:
1. **Quantification**: Every transit aspect is weighted and scored
2. **Normalization**: Raw scores are normalized to 0-100 scales using empirical data
3. **Specialization**: 23 different meters measure specific dimensions of experience
4. **Percentile-Based**: Score 85 = 85th percentile (top 15% of days)

**The 23 Meters** (see `v2-sprint.md` for full taxonomy):
- **2 Primary Meters**: Overall Intensity, Overall Harmony
- **4 Element Meters**: Fire, Earth, Air, Water Energy
- **8 Life Domain Meters**: Personal, Relationships, Work, Growth, Finance, Purpose, Home, Decisions
- **9 Planetary Influence Meters**: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto Influence

### Why This Sprint?

Currently, horoscope generation does its own ad-hoc analysis of transits. This creates:
- **Duplication**: Logic scattered across LLM prompts and Python code
- **Inconsistency**: Different calculations for same concepts
- **Subjectivity**: LLM interprets raw aspects without quantitative grounding
- **Missed Opportunity**: We have sophisticated astrometer system that's underutilized

**Solution**: Make astrometers the **single source of truth** for all quantitative astrological measurements. The LLM's job becomes interpretation and storytelling, not calculation.

---

## Current State

### Existing Horoscope Flow

```python
# In llm.py or similar
def generate_daily_horoscope(user_profile: UserProfile, date: datetime):
    natal_chart = user_profile.natal_chart
    transit_chart = compute_birth_chart(date, birth_time="12:00")

    # Raw aspects are passed to LLM
    aspects = find_natal_transit_aspects(natal_chart, transit_chart, orb=8.0)

    # LLM prompt does its own "analysis"
    prompt = f"""
    Today's transits:
    {format_aspects(aspects)}

    Analyze the intensity and quality...
    """

    response = llm.generate(prompt)
    return response
```

### Problems

1. **LLM does math**: Prompt asks LLM to "analyze intensity" - but LLMs are bad at counting/weighting
2. **No standardization**: One prompt might emphasize Mars, another ignores it
3. **Can't track trends**: No way to say "this is your most intense week in 3 months" without historical data
4. **Redundant calculation**: Astrometers already calculated everything, but we recalculate in prompts

---

## Proposed Architecture

### New Horoscope Flow

```python
# Step 1: Calculate astrometers (single source of truth)
def generate_daily_horoscope_v3(user_profile: UserProfile, date: datetime):
    natal_chart = user_profile.natal_chart
    transit_chart = compute_birth_chart(date, birth_time="12:00")

    # NEW: Get all 23 astrometer readings
    astrometers = get_meters(natal_chart, transit_chart, date)

    # Step 2: Fast horoscope uses astrometers for quantitative grounding
    fast_horoscope = generate_fast_horoscope(
        user_profile=user_profile,
        astrometers=astrometers,  # Pass structured data
        date=date
    )

    # Step 3: Detailed horoscope builds on astrometers + fast analysis
    detailed_horoscope = generate_detailed_horoscope(
        user_profile=user_profile,
        astrometers=astrometers,  # Same structured data
        fast_horoscope=fast_horoscope,
        date=date
    )

    return fast_horoscope, detailed_horoscope
```

### Data Flow

```
User Request
    ↓
Get Natal Chart (from UserProfile)
    ↓
Get Transit Chart (for target date)
    ↓
Calculate Astrometers (get_meters)
    ↓
    ├─→ Fast Horoscope (Prompt 1)
    │   - Astrometers provide quantitative summary
    │   - LLM focuses on interpretation/themes
    │   - Returns: core analysis, key transits, daily theme
    │
    └─→ Detailed Horoscope (Prompt 2)
        - Same astrometers data
        - Plus fast horoscope context
        - LLM expands into 8 life domains
        - Returns: detailed predictions per category
```

---

## Template Changes

### Current Template Structure

```
templates/horoscope/
├── daily_static.j2         # System instructions (cacheable)
├── daily_dynamic.j2        # Transit data (changes daily)
├── personalization.j2      # User profile (cacheable per user)
├── detailed_static.j2      # System instructions for detailed
├── detailed_dynamic.j2     # Fast output + transits
└── (shared) personalization.j2
```

### Required Changes

#### 1. Add Astrometers to Dynamic Templates

**`daily_dynamic.j2`** - ADD astrometers section:
```jinja2
## Astrological Vital Signs (Today: {{ date }})

### Overall Measurements
- **Intensity Meter**: {{ astrometers.overall_intensity.intensity_meter }}/100
  - Label: {{ astrometers.overall_intensity.label }}
  - Percentile: This is a {{ astrometers.overall_intensity.percentile_description }} day

- **Harmony Meter**: {{ astrometers.overall_harmony.harmony_meter }}/100
  - Label: {{ astrometers.overall_harmony.label }}
  - Interpretation: {{ astrometers.overall_harmony.interpretation }}

### Element Distribution
- Fire Energy: {{ astrometers.fire_energy.meter }}/100 ({{ astrometers.fire_energy.label }})
- Earth Energy: {{ astrometers.earth_energy.meter }}/100 ({{ astrometers.earth_energy.label }})
- Air Energy: {{ astrometers.air_energy.meter }}/100 ({{ astrometers.air_energy.label }})
- Water Energy: {{ astrometers.water_energy.meter }}/100 ({{ astrometers.water_energy.label }})

### Life Domain Meters (for your awareness)
{% for domain in ['personal', 'relationships', 'work', 'growth', 'finance', 'purpose', 'home', 'decisions'] %}
- {{ domain.title() }}: {{ astrometers[domain + '_meter'].meter }}/100
{% endfor %}

### Top Planetary Influences
{% for planet_reading in astrometers.top_planet_influences[:3] %}
- {{ planet_reading.planet.title() }}: {{ planet_reading.meter }}/100 ({{ planet_reading.active_aspects }} aspects)
{% endfor %}

---

## Current Transits (for reference)
{{ transit_summary }}
```

**REMOVE from `daily_dynamic.j2`**:
- Manual "analyze intensity" instructions
- "Count the aspects and assess..." type language
- Any prompt asking LLM to calculate/quantify

#### 2. Update Static Instructions

**`daily_static.j2`** - UPDATE instructions:
```jinja2
# Task

You are generating a fast daily horoscope (Prompt 1).

## Your Role

You are a STORYTELLER and INTERPRETER, not a calculator.

The astrological calculations have already been done for you. Your job:
1. **Interpret** the quantitative measurements (astrometers)
2. **Synthesize** a coherent narrative from the data
3. **Ground** your analysis in the specific numbers provided
4. **Humanize** the technical measurements into relatable guidance

## What You're Given

- **Astrometers**: 23 quantitative measurements (0-100 scales)
  - Overall Intensity/Harmony (primary meters)
  - Element distribution (fire/earth/air/water)
  - Life domain meters (personal, relationships, work, etc.)
  - Planetary influence meters (which planets dominate today)

- **Transit Details**: Raw astrological data for reference
  - Specific aspects (Mars trine Sun, etc.)
  - Degrees and orbs
  - Applying/exact/separating status

## What You Should Do

✓ Reference specific meter values: "With intensity at 87/100 (top 13% of days)..."
✓ Weave in element balance: "Fire energy is peaking at 92/100..."
✓ Highlight domain focuses: "Your work meter (78/100) shows significant activity..."
✓ Use percentiles to calibrate tone: "This is a top 5% harmony day - rare alignment"

✗ DO NOT recalculate or re-analyze: "Let me count the aspects..." (already done!)
✗ DO NOT contradict meters: If harmony is 23/100, don't say "harmonious day"
✗ DO NOT ignore meters: They are your quantitative foundation
✗ DO NOT invent numbers: Use the provided meter values

## Output Format

Generate a ~200 word core analysis that:
1. Opens with intensity/harmony summary (with numbers!)
2. Explores elemental patterns
3. Names 2-3 key transits from the raw data
4. Ends with a single-sentence daily theme

Remember: You're translating data into wisdom, not analyzing raw transits from scratch.
```

#### 3. Detailed Template Updates

**`detailed_dynamic.j2`** - ADD astrometers context:
```jinja2
## Quantitative Summary (Use These as Anchors)

{{ fast_horoscope }}

## Life Domain Meters (For Category Expansion)

{% for domain, meter_name in [
    ('Love & Relationships', 'relationships_meter'),
    ('Family & Friendships', 'personal_meter'),
    ('Career & Ambition', 'work_meter'),
    ('Personal Growth', 'growth_meter'),
    ('Money & Resources', 'finance_meter'),
    ('Life Purpose', 'purpose_meter'),
    ('Home & Environment', 'home_meter'),
    ('Decisions & Timing', 'decisions_meter')
] %}

### {{ domain }}
- Meter: {{ astrometers[meter_name].meter }}/100
- Label: {{ astrometers[meter_name].label }}
- Percentile: {{ astrometers[meter_name].percentile_description }}
- Key Aspects: {{ astrometers[meter_name].aspect_count }} active
{% endfor %}
```

**`detailed_static.j2`** - UPDATE to reference meters:
```jinja2
## Your Task

Expand the fast horoscope into detailed predictions for 8 life categories.

## Approach

For each category:
1. **Start with the meter**: "With your work meter at 78/100..."
2. **Reference specific aspects**: Use the raw transit data to explain WHY
3. **Calibrate depth**: Higher meter = more to say, lower meter = acknowledge but brief
4. **Connect to fast analysis**: Reference themes from Prompt 1

Example:
"Your relationships meter is at 34/100 today - below average activity. Venus in your 7th house sextile Jupiter suggests small pleasant moments, but the low overall reading means this isn't a relationship-defining day. Focus elsewhere and enjoy the subtle harmony without forcing connection."

## Important

- DO use meter values to prioritize (high meters get more words)
- DO ground predictions in numbers ("top 10% day for finance decisions")
- DO acknowledge when meters are LOW ("quiet day for this area")
- DON'T contradict meter readings
- DON'T write long predictions for low-meter categories
```

---

## Implementation Plan

### Phase 1: Core Integration (3 days)

**Task 1.1: Update LLM function signatures**
- [ ] Add `astrometers: AllMetersReading` parameter to `generate_fast_horoscope()`
- [ ] Add `astrometers: AllMetersReading` parameter to `generate_detailed_horoscope()`
- [ ] Update docstrings to reflect new data flow

**Task 1.2: Update horoscope Cloud Function**
- [ ] Modify `get_daily_horoscope()` in `main.py`:
  ```python
  # Before calling LLM:
  from astrometers import get_meters
  astrometers = get_meters(natal_chart, transit_chart, target_date)

  # Pass to LLM functions:
  fast = generate_fast_horoscope(..., astrometers=astrometers)
  detailed = generate_detailed_horoscope(..., astrometers=astrometers)
  ```
- [ ] Ensure astrometers data is serialized correctly (Pydantic → dict)

**Task 1.3: Create astrometer formatting helpers**
- [ ] Add `functions/astrometers/formatting.py`:
  ```python
  def format_astrometers_for_prompt(astrometers: AllMetersReading) -> dict:
      """Format astrometers for Jinja2 template rendering."""
      return {
          'overall_intensity': {
              'meter': astrometers.overall_intensity.intensity_meter,
              'label': astrometers.overall_intensity.label,
              'percentile': get_percentile_description(...)
          },
          # ... format all 23 meters
      }
  ```
- [ ] Add percentile description helper: `get_percentile_description(meter_value: float) -> str`
  - 99-100: "exceptional - top 1%"
  - 95-98: "very high - top 2-5%"
  - 90-94: "high - top 6-10%"
  - 75-89: "above average - top 11-25%"
  - 50-74: "moderate"
  - 25-49: "below average"
  - 10-24: "low"
  - 1-9: "very low"

### Phase 2: Template Updates (2 days)

**Task 2.1: Update `daily_dynamic.j2`**
- [ ] Add "Astrological Vital Signs" section at top
- [ ] Include overall intensity/harmony with percentile context
- [ ] Show element distribution (4 meters)
- [ ] List top 3 planetary influences
- [ ] Move raw transit summary to bottom (de-emphasize)

**Task 2.2: Update `daily_static.j2`**
- [ ] Reframe LLM role as "interpreter" not "calculator"
- [ ] Add "What You're Given" section explaining astrometers
- [ ] Add "What You Should Do" with specific meter-usage examples
- [ ] Remove any "count the aspects" or "analyze intensity" language

**Task 2.3: Update `detailed_dynamic.j2`**
- [ ] Add life domain meters section with all 8 categories
- [ ] Include meter value, label, and percentile for each
- [ ] Keep fast horoscope context at top

**Task 2.4: Update `detailed_static.j2`**
- [ ] Add instructions to start each category with meter value
- [ ] Emphasize calibrating depth based on meter (high = more words)
- [ ] Add example showing low-meter category (brief acknowledgment)

### Phase 3: Testing & Validation (2 days)

**Task 3.1: Unit tests for formatting helpers**
- [ ] Test `format_astrometers_for_prompt()` with mock AllMetersReading
- [ ] Test `get_percentile_description()` for all ranges
- [ ] Verify Jinja2 templates render without errors

**Task 3.2: Integration testing**
- [ ] Generate horoscopes for 5 test users with different chart types
- [ ] Verify astrometers are correctly passed through pipeline
- [ ] Check that LLM responses reference meter values
- [ ] Confirm no "analyzing intensity" or recalculation language in outputs

**Task 3.3: Prompt quality validation**
- [ ] Read 10+ generated horoscopes
- [ ] Verify LLM grounds analysis in specific meter values
- [ ] Check that high-meter domains get more detail
- [ ] Ensure percentile language is used ("top 15% day")

**Task 3.4: Compare old vs new**
- [ ] Generate same horoscope with old flow (no astrometers) and new flow
- [ ] Qualitative assessment: Which is more grounded? Consistent? Useful?

### Phase 4: Cleanup (1 day)

**Task 4.1: Remove deprecated code**
- [ ] Remove any manual aspect-counting logic from LLM module
- [ ] Remove redundant "intensity analysis" helpers if they exist
- [ ] Update comments/docstrings to reflect new architecture

**Task 4.2: Documentation**
- [ ] Update `docs/CLAUDE.md` with new horoscope generation flow
- [ ] Document astrometer → LLM data flow
- [ ] Add example showing how to use astrometers in prompts

**Task 4.3: Update TODO.md**
- [ ] Mark Sprint 3 tasks complete
- [ ] Note any follow-up items (prompt refinement, A/B testing, etc.)

---

## Success Criteria

### Functional Requirements
- ✅ All horoscope generation calls `get_meters()` first
- ✅ Astrometers data is passed to both fast and detailed prompts
- ✅ Templates render astrometer values correctly
- ✅ LLM responses reference specific meter values (not vague "intensity")

### Quality Requirements
- ✅ LLM output is more quantitatively grounded (uses numbers)
- ✅ High-meter domains receive more attention in detailed horoscope
- ✅ Percentile language makes scores intuitive ("top 10% day")
- ✅ No redundant calculation or "let me analyze..." language

### Code Quality
- ✅ Clean separation: Astrometers calculate, LLM interprets
- ✅ No duplication between astrometer logic and LLM prompts
- ✅ Type-safe data flow (Pydantic models throughout)
- ✅ Helper functions for formatting are well-tested

---

## Example Output (Before vs After)

### Before (No Astrometers)

**Prompt to LLM**:
```
Today's transits for Gemini Sun:
- Mars opposite Sun (6° orb, applying)
- Venus trine Moon (3° orb, exact)
- Saturn square Mercury (7° orb, separating)

Analyze the intensity and quality of this day. What themes emerge?
```

**LLM Response** (guessing):
```
Today brings intense energy with Mars opposing your Sun. There's
also some harmonious Venus-Moon energy. Overall, it's a mixed day
with both challenges and ease...
```

**Problem**: LLM is counting aspects mentally, guessing at intensity, no quantitative grounding.

### After (With Astrometers)

**Prompt to LLM**:
```
## Astrological Vital Signs (Today: 2025-10-26)

### Overall Measurements
- Intensity Meter: 87/100 (top 13% of days - very high activity)
- Harmony Meter: 34/100 (challenging - growth through friction)

### Element Distribution
- Fire Energy: 92/100 (Very High - passion, action, urgency)
- Earth Energy: 41/100 (Moderate)
- Air Energy: 38/100 (Moderate)
- Water Energy: 29/100 (Low)

### Life Domain Meters
- Personal: 89/100
- Relationships: 67/100
- Work: 81/100
...

## Current Transits (for reference)
- Mars opposite Sun (6° orb, applying)
- Venus trine Moon (3° orb, exact)
- Saturn square Mercury (7° orb, separating)
```

**LLM Response** (interpreting data):
```
Today is an 87/100 intensity day - placing you in the top 13%
of astrological activity. However, with harmony at just 34/100,
this is growth-through-friction energy.

Fire energy peaks at 92/100, explaining the urgency and drive you'll
feel. Mars opposing your Sun is the primary driver here, creating
tension in your personal sphere (89/100 on personal meter - very high).

Your work meter (81/100) suggests this intensity channels productively
into career matters, while relationships (67/100) show moderate but
not critical activity. The Venus-Moon trine provides moments of ease
amidst the push.

Daily theme: Channel high-intensity fire into focused action, knowing
friction creates the diamond.
```

**Improvement**: LLM uses exact numbers, explains WHY (element distribution), calibrates tone based on quantitative data.

---

## Future Enhancements (Post-Sprint 3)

### Sprint 4+: Historical Context
Once astrometers are integrated:
- [ ] Store daily astrometer readings in Firestore
- [ ] Enable "This is your most intense week in 3 months" type insights
- [ ] Add trend detection ("harmony has been declining for 5 days")

### Sprint 5+: Personalized Thresholds
- [ ] Track user's typical intensity range (their "normal")
- [ ] Calibrate labels: 75/100 might be "high" for one person, "typical" for another
- [ ] "This is intense FOR YOU" vs "objectively intense"

### Sprint 6+: Predictive Meters
- [ ] "Tomorrow's intensity will be 15 points higher"
- [ ] "Your work meter peaks Thursday at 94/100"
- [ ] Help users plan around astrological weather

---

## Questions & Decisions

### Q1: How much detail in prompts?
**Decision**: Include all 23 meters, but emphasize top-level (intensity/harmony) and domain-specific ones. LLM can skim what's not relevant.

### Q2: Should we show raw transits at all?
**Decision**: Yes, but de-emphasize. Put astrometers first, raw transits at bottom as "reference." LLM needs specifics for storytelling (e.g., "Mars opposite Sun" is more narrative than "personal meter at 89").

### Q3: What if meters are all medium (40-60)?
**Decision**: Prompt should instruct LLM to acknowledge quiet/balanced days. "Today is a 52/100 intensity day - right at the median. Use this balanced energy for integration and routine."

### Q4: Do we cache astrometer calculations?
**Decision**: Not yet. They're fast (<100ms) and change daily. If performance becomes issue, cache per user per date.

---

## Dependencies

### External
- ✅ Empirical calibration complete (historical_scores.parquet)
- ✅ `get_meters()` function implemented
- ✅ All 23 meters calculated correctly
- ✅ Percentile-based normalization working

### Internal
- Existing horoscope generation (`llm.py`)
- Existing templates (`templates/horoscope/`)
- Cloud Functions for horoscope delivery (`main.py`)

---

## Risks & Mitigation

### Risk 1: Prompt becomes too long
**Impact**: Token costs increase, context caching less effective
**Mitigation**: Keep astrometer section concise. Most meters only need 1 line. Consider abbreviated format for low-value meters.

### Risk 2: LLM ignores meter values
**Impact**: Defeats the purpose, LLM goes back to vague "intensity" language
**Mitigation**: Strong prompt engineering ("DO reference meter values", "DON'T recalculate"). Test iteratively. Consider few-shot examples.

### Risk 3: Users don't understand percentiles
**Impact**: "What does 85/100 mean?"
**Mitigation**: Always include description: "85/100 (top 15% of days)". Consider emoji/icons in UI: 🔥 for high, 🌱 for low.

### Risk 4: Breaking existing functionality
**Impact**: Horoscopes stop generating or degrade in quality
**Mitigation**: Thorough testing. Keep old flow available during transition. A/B test if possible.

---

## Timeline

**Week 1**:
- Day 1-3: Phase 1 (Core Integration)
- Day 4-5: Phase 2 (Template Updates)

**Week 2**:
- Day 6-7: Phase 3 (Testing & Validation)
- Day 8: Phase 4 (Cleanup & Documentation)

**Total**: 8 days (1-2 weeks with buffer)

---

## Appendix A: Astrometer Data Structure

```python
class AllMetersReading(BaseModel):
    date: datetime
    natal_chart_summary: dict

    # Primary meters
    overall_intensity: IntensityReading
    overall_harmony: HarmonyReading

    # Element meters
    fire_energy: ElementReading
    earth_energy: ElementReading
    air_energy: ElementReading
    water_energy: ElementReading

    # Life domain meters
    personal_meter: DomainReading
    relationships_meter: DomainReading
    work_meter: DomainReading
    growth_meter: DomainReading
    finance_meter: DomainReading
    purpose_meter: DomainReading
    home_meter: DomainReading
    decisions_meter: DomainReading

    # Planetary influence meters
    sun_influence: PlanetReading
    moon_influence: PlanetReading
    mercury_influence: PlanetReading
    venus_influence: PlanetReading
    mars_influence: PlanetReading
    jupiter_influence: PlanetReading
    saturn_influence: PlanetReading
    uranus_influence: PlanetReading
    neptune_influence: PlanetReading
    pluto_influence: PlanetReading
```

Each reading type has:
- `meter: float` (0-100)
- `label: str` ("Quiet", "Moderate", "High", etc.)
- `aspect_count: int`
- Additional metadata (which aspects, planets, etc.)

---

## Appendix B: Template Variable Reference

Variables available in Jinja2 templates after Sprint 3:

```jinja2
{# Primary meters #}
{{ astrometers.overall_intensity.intensity_meter }}  # 0-100
{{ astrometers.overall_intensity.label }}           # "High", "Moderate", etc.
{{ astrometers.overall_intensity.percentile }}      # "top 15%"

{# Element meters (same structure x4) #}
{{ astrometers.fire_energy.meter }}
{{ astrometers.earth_energy.meter }}
{{ astrometers.air_energy.meter }}
{{ astrometers.water_energy.meter }}

{# Domain meters (same structure x8) #}
{{ astrometers.personal_meter.meter }}
{{ astrometers.relationships_meter.meter }}
{{ astrometers.work_meter.meter }}
{{ astrometers.growth_meter.meter }}
{{ astrometers.finance_meter.meter }}
{{ astrometers.purpose_meter.meter }}
{{ astrometers.home_meter.meter }}
{{ astrometers.decisions_meter.meter }}

{# Planet meters (same structure x10) #}
{{ astrometers.sun_influence.meter }}
{{ astrometers.moon_influence.meter }}
{# etc. for all planets #}

{# Existing variables (unchanged) #}
{{ user_profile.sun_sign }}
{{ user_profile.name }}
{{ date }}
{{ transit_summary }}
```

---

## Appendix C: Prompt Engineering Examples

### Example 1: High Intensity, Low Harmony

**Astrometers**:
- Intensity: 91/100 (top 9%)
- Harmony: 19/100 (challenging)

**Good LLM Response**:
> "Today ranks at 91/100 for intensity - placing you in the top 9% of astrological activity. However, harmony sits at just 19/100, indicating this is friction-based growth. Expect powerful moments that require navigation, not ease."

**Bad LLM Response**:
> "There's a lot happening today. Some challenging aspects, but also opportunities..."

### Example 2: Medium Everything

**Astrometers**:
- Intensity: 52/100 (median)
- Harmony: 48/100 (neutral)

**Good LLM Response**:
> "Today is a 52/100 intensity day - right at the median. This balanced, unremarkable energy is perfect for consolidation. No major highs or lows, just steady progress."

**Bad LLM Response**:
> "The stars are aligned today! Lots of energy and opportunities await!"

### Example 3: Element Imbalance

**Astrometers**:
- Fire: 94/100
- Earth: 12/100
- Air: 41/100
- Water: 23/100

**Good LLM Response**:
> "Fire energy dominates at 94/100 - passion, urgency, action. But earth is depleted at 12/100, meaning grounding and practical follow-through may suffer. Channel the fire into quick wins, not long-term projects."

**Bad LLM Response**:
> "You'll feel energetic and motivated today!"

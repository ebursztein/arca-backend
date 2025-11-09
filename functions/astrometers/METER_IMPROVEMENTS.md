# Meter System Improvements Plan

## Context
We're enhancing the astrometers system to provide LLM-generated per-meter interpretations and clean iOS-optimized data structures. This work builds on the newly regenerated meter JSON files (v2.0).

---

## ✅ COMPLETED: Tasks 1-2 (JSON Regeneration)

### Task 1: Regenerated All 17 Individual Meter JSON Files ✅
**Location:** `functions/astrometers/labels/*.json`

**Meters regenerated:**
- **MIND (3):** mental_clarity, focus, communication
- **EMOTIONS (3):** love, inner_stability, sensitivity
- **BODY (3):** vitality, drive, wellness
- **SPIRIT (4):** purpose, connection, intuition, creativity
- **GROWTH (4):** opportunities, career, growth, social_life

**What was added/improved:**
- ✅ Clean `overview` (one sentence, user-facing: "X represents...")
- ✅ Enhanced `detailed` (how it's measured, user-facing)
- ✅ New `astrological_foundation` section:
  - `primary_planets`: Main planetary influences
  - `secondary_planets`: Supporting influences
  - `natal_planets_tracked`: From config (what code monitors)
  - `transit_planets_tracked`: Which transiting planets affect this
  - `key_houses`: House meanings and relevance
  - `aspect_weights`: How different aspects impact this meter
  - `planetary_dignities`: Signs where planets are strong/weak
  - `critical_degrees`: Amplifying degrees (0, 15, 29, etc.)
- ✅ Improved `experience_labels.combined`: More actionable, removed duplicates
- ✅ New `interpretation_guidelines` section:
  - `tone`: How to talk about this meter
  - `focus_when_high/low/challenging`: What to emphasize
  - `avoid`: Common pitfalls
  - `phrasing_examples`: 3 concrete examples for LLM
- ✅ Preserved original `configuration` (natal_planets, natal_houses, retrograde_modifiers)
- ✅ Removed unused sections: `advice_templates` (not used in code)

### Task 2: Regenerated All 5 Group JSON Files ✅
**Location:** `functions/astrometers/labels/groups/*.json`

**Groups regenerated:** mind, emotions, body, spirit, growth

**What was added/improved:**
- ✅ Enhanced `overview` (what the group represents)
- ✅ Enhanced `detailed` (which meters it combines + what it shows)
- ✅ Improved `experience_labels.combined`: More descriptive labels
- ✅ Consistent structure across all groups

---

## 🚧 TODO: Tasks 3-8 (Code Changes)

### Task 3: Create Clean iOS Pydantic Models
**Location:** `functions/models.py`

**Goal:** Create simplified models that return only essential fields to iOS, replacing the verbose `AllMetersReading` structure.

**New models to create:**

```python
class MeterForIOS(BaseModel):
    """Simplified meter data for iOS client - only essential fields."""
    meter_name: str
    display_name: str
    group: str  # "mind", "emotions", "body", "spirit", "growth"

    # Scores (0-100)
    unified_score: float
    intensity: float
    harmony: float

    # Labels
    unified_quality: str  # "harmonious", "challenging", "mixed", "quiet"
    state_label: str  # From JSON experience_labels.combined

    # LLM-generated interpretation (1-2 sentences, 80-150 chars)
    interpretation: str

    # Trend (optional)
    trend_delta: Optional[float] = None
    trend_direction: Optional[str] = None  # "improving", "worsening", "stable"

    # User-facing description
    overview: str  # From JSON description.overview
    detailed: str  # From JSON description.detailed

class MeterGroupForIOS(BaseModel):
    """Simplified meter group for iOS - only essential fields."""
    group_name: str
    display_name: str

    # Aggregated scores
    unified_score: float
    intensity: float
    harmony: float

    # State
    state_label: str
    quality: str

    # LLM interpretation (2-3 sentences, from existing flow)
    interpretation: str

    # Member meters (simplified)
    meters: list[MeterForIOS]

    # Trend (optional)
    trend_delta: Optional[float] = None
    trend_direction: Optional[str] = None

    # Group description
    overview: str  # From group JSON description.overview
    detailed: str  # From group JSON description.detailed

class AstrometersForIOS(BaseModel):
    """Complete astrometers data for iOS - clean and minimal."""
    date: str

    # Overall stats
    overall_intensity: float
    overall_harmony: float
    overall_quality: str

    # 5 meter groups with their member meters nested
    groups: list[MeterGroupForIOS]  # Contains all 17 meters

    # Top insights (for quick scanning)
    top_active_meters: list[str]  # Top 3-5 meter names
    top_challenging_meters: list[str]
    top_flowing_meters: list[str]
```

**Implementation notes:**
- These models live alongside existing models in `functions/models.py`
- They are built FROM the existing `AllMetersReading` + LLM interpretations
- The DailyHoroscope response will use `AstrometersForIOS` instead of `AllMetersReading`

---

### Task 4: Update LLM Response Schema
**Location:** `functions/llm.py`

**Current state:**
```python
class DailyHoroscopeResponse(BaseModel):
    # ... existing fields ...

    # Group interpretations (5 fields - ALREADY WORKING)
    mind_interpretation: str
    emotions_interpretation: str
    body_interpretation: str
    spirit_interpretation: str
    growth_interpretation: str
```

**Add 17 new fields for individual meter interpretations:**
```python
class DailyHoroscopeResponse(BaseModel):
    # ... existing fields ...

    # Group interpretations (existing - keep these)
    mind_interpretation: str
    emotions_interpretation: str
    body_interpretation: str
    spirit_interpretation: str
    growth_interpretation: str

    # NEW: Individual meter interpretations (17 fields)
    mental_clarity_interpretation: str
    focus_interpretation: str
    communication_interpretation: str
    love_interpretation: str
    inner_stability_interpretation: str
    sensitivity_interpretation: str
    vitality_interpretation: str
    drive_interpretation: str
    wellness_interpretation: str
    purpose_interpretation: str
    connection_interpretation: str
    intuition_interpretation: str
    creativity_interpretation: str
    opportunities_interpretation: str
    career_interpretation: str
    growth_meter_interpretation: str  # Renamed to avoid conflict with group
    social_life_interpretation: str
```

**Why 17 new fields:**
- LLM will generate unique 1-2 sentence interpretation for each meter
- Replaces static JSON interpretations with personalized daily context
- Enables deeper per-meter guidance

---

### Task 5: Add Section 13 to Prompt Template
**Location:** `functions/templates/horoscope/daily_static.j2`

**Add after existing section 12 (Group Interpretations):**

```jinja2
### 13. INDIVIDUAL METER INTERPRETATIONS (17 fields)

**Data Source:** Use **individual meter data** from daily_dynamic.j2 summary tables + each meter's **top_aspects** + **state_label** + **interpretation_guidelines** from JSON

You must generate a **1-2 sentence interpretation** for EACH of the 17 individual meters.

**Output fields (must match exactly):**
- mental_clarity_interpretation
- focus_interpretation
- communication_interpretation
- love_interpretation
- inner_stability_interpretation
- sensitivity_interpretation
- vitality_interpretation
- drive_interpretation
- wellness_interpretation
- purpose_interpretation
- connection_interpretation
- intuition_interpretation
- creativity_interpretation
- opportunities_interpretation
- career_interpretation
- growth_meter_interpretation
- social_life_interpretation

**Requirements:**
1. **Length:** 1-2 sentences, 80-150 characters each
2. **Use actual scores:** Reference unified_score, harmony, intensity from the data
3. **Use state_label naturally:** Weave in the meter's state_label from experience_labels
4. **Connect to transits:** Reference specific transits from the meter's top_aspects
5. **Follow tone guidelines:** Use the interpretation_guidelines from each meter's JSON
6. **Be ultra-specific:** Not vague - actionable and concrete

**Tone (from guidelines):**
- Use the meter's specific `tone` from interpretation_guidelines
- Follow `focus_when_high/low/challenging` guidance
- Avoid the items listed in `avoid`
- Reference `phrasing_examples` for style

**Example (VITALITY meter with unified=82, harmony=75, intensity=89, state="Strong Flow"):**
"Your physical energy is strong and flowing today with Mars supporting your Sun at 23°—this is your window for intense workouts or demanding projects."

**Example (LOVE meter with unified=38, harmony=32, intensity=54, state="Relationship Friction"):**
"Romantic energy feels tense with Venus square Mars creating friction between independence and connection—expect misunderstandings but stay patient."

**Example (MENTAL_CLARITY meter with unified=91, harmony=88, intensity=94, state="Brilliant Clarity"):**
"Your mind is razor-sharp today with Mercury trine your natal Sun—this is perfect timing for important decisions or complex problem-solving."

**CRITICAL:**
- Generate ALL 17 interpretations (no skipping)
- Match field names exactly as listed above
- Reference real data from today's transit summary
- Use each meter's unique interpretation_guidelines tone
```

---

### Task 6: Implement Post-Processing Logic
**Location:** `functions/llm.py` in `generate_daily_horoscope()` function

**Current flow:**
1. Build prompt with astrometer data
2. Call LLM → get `DailyHoroscopeResponse`
3. Inject group interpretations into `meter_groups`
4. Return `DailyHoroscope` with `astrometers: AllMetersReading`

**New flow:**
1. Build prompt with astrometer data
2. Call LLM → get `DailyHoroscopeResponse` (now with 17 meter interpretations)
3. Build meter interpretations dict:
   ```python
   meter_interpretations = {
       "mental_clarity": parsed.mental_clarity_interpretation,
       "focus": parsed.focus_interpretation,
       # ... all 17 ...
   }
   ```
4. **Load meter JSON descriptions:**
   ```python
   meter_descriptions = {}
   for meter_name in METER_NAMES:
       with open(f"functions/astrometers/labels/{meter_name}.json") as f:
           data = json.load(f)
           meter_descriptions[meter_name] = {
               "overview": data["description"]["overview"],
               "detailed": data["description"]["detailed"]
           }
   ```
5. **Load group JSON descriptions:**
   ```python
   group_descriptions = {}
   for group_name in ["mind", "emotions", "body", "spirit", "growth"]:
       with open(f"functions/astrometers/labels/groups/{group_name}.json") as f:
           data = json.load(f)
           group_descriptions[group_name] = {
               "overview": data["description"]["overview"],
               "detailed": data["description"]["detailed"]
           }
   ```
6. **Build `AstrometersForIOS` from `AllMetersReading`:**
   ```python
   def build_astrometers_for_ios(
       all_meters: AllMetersReading,
       meter_interpretations: dict[str, str],
       meter_descriptions: dict[str, dict],
       group_interpretations: dict[str, str],
       group_descriptions: dict[str, dict]
   ) -> AstrometersForIOS:
       """Convert AllMetersReading to clean iOS structure."""

       groups = []
       for group_name in ["mind", "emotions", "body", "spirit", "growth"]:
           # Get meters for this group
           meter_names = get_meters_for_group(group_name)

           # Build MeterForIOS for each meter
           meters_for_ios = []
           for meter_name in meter_names:
               meter_reading = getattr(all_meters, meter_name)
               meters_for_ios.append(MeterForIOS(
                   meter_name=meter_name,
                   display_name=meter_reading.meter_name.replace('_', ' ').title(),
                   group=group_name,
                   unified_score=meter_reading.unified_score,
                   intensity=meter_reading.intensity,
                   harmony=meter_reading.harmony,
                   unified_quality=meter_reading.unified_quality,
                   state_label=meter_reading.state_label,
                   interpretation=meter_interpretations[meter_name],
                   trend_delta=meter_reading.trend.unified_score.delta if meter_reading.trend else None,
                   trend_direction=meter_reading.trend.unified_score.direction if meter_reading.trend else None,
                   overview=meter_descriptions[meter_name]["overview"],
                   detailed=meter_descriptions[meter_name]["detailed"]
               ))

           # Build MeterGroupForIOS
           # (Calculate aggregated scores from meters)
           avg_unified = sum(m.unified_score for m in meters_for_ios) / len(meters_for_ios)
           avg_intensity = sum(m.intensity for m in meters_for_ios) / len(meters_for_ios)
           avg_harmony = sum(m.harmony for m in meters_for_ios) / len(meters_for_ios)

           groups.append(MeterGroupForIOS(
               group_name=group_name,
               display_name=group_name.title(),
               unified_score=avg_unified,
               intensity=avg_intensity,
               harmony=avg_harmony,
               state_label="...",  # Calculate from scores
               quality="...",  # Calculate from scores
               interpretation=group_interpretations[group_name],
               meters=meters_for_ios,
               overview=group_descriptions[group_name]["overview"],
               detailed=group_descriptions[group_name]["detailed"]
           ))

       return AstrometersForIOS(
           date=all_meters.date.isoformat(),
           overall_intensity=all_meters.overall_intensity.unified_score,
           overall_harmony=all_meters.overall_harmony.unified_score,
           overall_quality=all_meters.overall_unified_quality,
           groups=groups,
           top_active_meters=[...],  # Extract top 5 by intensity
           top_challenging_meters=[...],  # Extract top 5 by low harmony
           top_flowing_meters=[...]  # Extract top 5 by high unified_score
       )
   ```
7. Return `DailyHoroscope` with `astrometers: AstrometersForIOS`

**Helper function needed:**
```python
METER_NAMES = [
    "mental_clarity", "focus", "communication",
    "love", "inner_stability", "sensitivity",
    "vitality", "drive", "wellness",
    "purpose", "connection", "intuition", "creativity",
    "opportunities", "career", "growth", "social_life"
]

def get_meters_for_group(group_name: str) -> list[str]:
    """Return meter names for a given group."""
    mapping = {
        "mind": ["mental_clarity", "focus", "communication"],
        "emotions": ["love", "inner_stability", "sensitivity"],
        "body": ["vitality", "drive", "wellness"],
        "spirit": ["purpose", "connection", "intuition", "creativity"],
        "growth": ["opportunities", "career", "growth", "social_life"]
    }
    return mapping[group_name]
```

---

### Task 7: Update DailyHoroscope Model
**Location:** `functions/models.py`

**Current:**
```python
class DailyHoroscope(BaseModel):
    # ...
    astrometers: Any  # AllMetersReading object (verbose!)
    meter_groups: Optional[dict[str, MeterGroupData]] = None
```

**Change to:**
```python
class DailyHoroscope(BaseModel):
    # ...
    astrometers: AstrometersForIOS  # Clean iOS-optimized structure
    # Remove: meter_groups (now nested in astrometers.groups)
```

**Impact:**
- iOS will receive cleaner, simpler data structure
- All meter data nested logically: groups → meters
- Interpretations are LLM-generated, not static
- Descriptions included for each meter and group

---

### Task 8: Test Complete Flow
**Location:** Create test file or use prototype

**Test checklist:**
1. ✅ Generate daily horoscope for test user
2. ✅ Verify LLM returns all 17 meter interpretations
3. ✅ Verify `AstrometersForIOS` structure is correct
4. ✅ Verify meter descriptions loaded from JSON
5. ✅ Verify group descriptions loaded from JSON
6. ✅ Verify interpretations are unique per meter (not generic)
7. ✅ Verify token count increase (~1,500 output tokens)
8. ✅ Verify iOS receives clean data (no verbose AllMetersReading)

**Test command:**
```bash
uv run python functions/prototype.py
# Or create new test:
uv run python functions/test_meter_interpretations.py
```

---

## Token Impact Analysis

**Before (current):**
- LLM generates: 5 group interpretations (~500 output tokens)
- Total output: ~3,000-4,000 tokens

**After (with per-meter interpretations):**
- LLM generates: 5 group interpretations + 17 meter interpretations
- Meter interpretations: 17 × ~90 tokens = ~1,530 tokens
- Total output: ~4,500-5,500 tokens

**Cost increase:**
- Additional ~1,500 output tokens per horoscope
- At Gemini Flash-Lite pricing: ~$0.003 per horoscope
- Worth it for highly personalized per-meter guidance

---

## File Summary

**Files modified in this plan:**
1. ✅ `functions/astrometers/labels/*.json` (17 files) - DONE
2. ✅ `functions/astrometers/labels/groups/*.json` (5 files) - DONE
3. `functions/models.py` - Add iOS models, update DailyHoroscope
4. `functions/llm.py` - Add 17 fields to response, implement post-processing
5. `functions/templates/horoscope/daily_static.j2` - Add section 13

**Total:** 24 files (22 JSON + 2 Python + 1 template)

---

## Next Steps to Resume

When resuming this work:

1. **Start with Task 3:** Create iOS Pydantic models in `functions/models.py`
2. **Then Task 4:** Update LLM response schema in `functions/llm.py`
3. **Then Task 5:** Add prompt section in `daily_static.j2`
4. **Then Task 6:** Implement post-processing logic in `llm.py`
5. **Then Task 7:** Update DailyHoroscope model
6. **Finally Task 8:** Test the complete flow

Each task is independent enough to work on separately but they build on each other.

---

## Questions to Resolve

1. Should meter `overview` and `detailed` be included in iOS response? (Currently: YES)
2. Should we cache meter/group descriptions or load on every request? (Currently: load on request)
3. Should `top_active_meters` etc. be meter names or full objects? (Currently: names)
4. Should we keep backward compatibility or break iOS? (Decision: NO backward compatibility)

---

**Status:** Tasks 1-2 complete (JSON regeneration). Tasks 3-8 pending (code implementation).

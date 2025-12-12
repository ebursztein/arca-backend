# Implementation Plan: Overall Energy & Relationship Sections

Apply pattern-based writing formulas to overall energy and relationship sections, extending what's working at the meter group level.

---

## Files to Modify

| File | Changes |
|------|---------|
| `functions/astrometers/meter_groups.py` | Add `get_overall_writing_guidance()` function |
| `functions/llm.py` | Calculate overall pattern, pass to template context |
| `functions/templates/horoscope/daily_dynamic.j2` | Add groups configuration + formula to OVERVIEW and RELATIONSHIP sections |
| `functions/templates/horoscope/daily_static.j2` | Add examples per pattern for daily_overview and relationship_weather |
| `functions/tests/unit/test_group_score_formula.py` | Add unit tests for `get_overall_writing_guidance()` |

---

## Phase 1: Overall Energy

### 1.1 Create `get_overall_writing_guidance()` in `meter_groups.py`

**Function signature:**
```python
def get_overall_writing_guidance(
    all_groups: list[dict],  # List of 5 group dicts with unified_score, name
    user_name: str = "",
) -> dict:
```

**Threshold zones:**
- **Strong:** >= 60 (flowing, lean into it)
- **Neutral:** 40-60 (not highlighted - unremarkable)
- **Challenging:** < 40 (acknowledge obstacle, show path through)

**Pattern detection (explicit and exhaustive):**
- `all_flowing`: All 5 groups >= 60
- `all_challenging`: All 5 groups < 40
- `one_challenging`: Exactly 1 group < 40, others >= 50 (clear outlier)
- `one_shining`: Exactly 1 group >= 60, others < 50 (bright spot)
- `mixed_day`: Some strong (>=60), some challenging (<40)
- `neutral_day`: All groups in 40-60 range (unremarkable - keep it simple)

**Tie-breaking for strongest/weakest:** Use priority order: `heart > mind > body > instincts > growth` (deterministic, prioritizes emotional/relational areas)

**Return structure:**
```python
{
    "pattern": str,                    # Pattern name
    "formula": str,                    # Step-by-step writing instructions (genuine optimism voice)
    "strongest_group": str,            # Name of highest scoring group
    "strongest_score": int,            # Score of highest group
    "challenging_group": str | None,   # Name of lowest group IF < 40, else None
    "challenging_score": int | None,   # Score IF < 40, else None
    "flowing_groups": list[str],       # Groups >= 60
    "challenging_groups": list[str],   # Groups < 40
    "shining_group": str | None,       # For one_shining pattern
}
```

### 1.2 Pattern Formulas (Genuine Optimism Voice)

Core formula from voice.md: "The stars show this challenge" + "They also show you have what it takes" + "Here's the move."

**`all_flowing`:** (All 5 groups >= 60)
```
Pattern: all_flowing. Structure:
1) Address user by name.
2) Name the strongest group leading the day.
3) Describe 2-3 specific feelings (mental clarity, emotional warmth, physical energy).
4) If key transit provided, cite it. If no transit, skip.
5) End with 1-2 concrete actions to capitalize on the flow (e.g., 'Schedule the important meeting,' 'Have that conversation you've been putting off').
```

**`all_challenging`:** (All 5 groups < 40)
```
Pattern: all_challenging. Structure:
1) Name the challenge directly - what feels hard today.
2) If key transit provided, cite it ('This is Saturn doing its thing').
3) Show their strength: "Your chart shows resilience - you've weathered harder."
4) Give 1-2 concrete actions that work WITH the energy (simplify, protect energy, delay demanding tasks).
Do NOT doom-and-gloom. Acknowledge the obstacle, then show the path through.
```

**`one_challenging`:** (1 group < 40, others >= 50)
```
Pattern: one_challenging. Structure:
1) Name the ONE area that's challenging and what they'll feel ('Your mind feels scattered,' 'Your body is dragging').
2) If key transit provided, cite it.
3) Acknowledge the rest is working - they have resources.
4) Give 1-2 concrete actions that work AROUND the challenge (if mind is low, lean on body or heart instead).
```

**`one_shining`:** (1 group >= 60, others < 50)
```
Pattern: one_shining. Structure:
1) Lead with the bright spot - the ONE area that's flowing.
2) If key transit provided, cite it.
3) Acknowledge other areas feel heavier, but they have this strength to lean on.
4) Give 1-2 concrete actions that USE the shining group ('Let your body lead - go for a walk instead of forcing focus').
```

**`mixed_day`:** (Some >= 60, some < 40)
```
Pattern: mixed_day. Structure:
1) Name what's flowing (specific groups).
2) Name what's challenging (specific groups).
3) If key transit provided, cite it.
4) Give 1-2 actions that play to strengths and work around challenges.
```

**`neutral_day`:** (All groups 40-60)
```
Pattern: neutral_day. Structure:
1) Keep it simple - nothing dramatic to highlight.
2) Name the strongest area briefly.
3) Give 1 concrete, grounded action for the day.
Don't oversell or undersell. Unremarkable days are fine.
```

### 1.3 Update `llm.py` Template Context

In `generate_daily_horoscope()`, after building `all_groups`:

```python
from astrometers.meter_groups import get_overall_writing_guidance

# Build overall guidance from the 5 groups
overall_guidance = get_overall_writing_guidance(
    all_groups=[
        {"name": g["name"], "unified_score": g["unified_score"]}
        for g in all_groups
    ],
    user_name=user_profile.name,
)
```

Add to template context:
```python
overall_guidance=overall_guidance,
```

### 1.4 Update `daily_dynamic.j2`

Replace current OVERVIEW GUIDANCE section with:

```jinja2
================================================================================
OVERVIEW GUIDANCE (for daily_overview)
================================================================================
OVERALL ENERGY: {{ overall_unified_score|round(0)|int }}/100
Pattern: {{ overall_guidance.pattern }}
Groups: mind={{ mind_score }}, heart={{ heart_score }}, body={{ body_score }}, instincts={{ instincts_score }}, growth={{ growth_score }}
Strongest: {{ overall_guidance.strongest_group }} ({{ overall_guidance.strongest_score }}/100)
{% if overall_guidance.challenging_group %}Challenging: {{ overall_guidance.challenging_group }} ({{ overall_guidance.challenging_score }}/100){% endif %}
{% if overall_guidance.shining_group %}Shining: {{ overall_guidance.shining_group }}{% endif %}
{% if overall_guidance.flowing_groups %}Flowing: {{ overall_guidance.flowing_groups|join(', ') }}{% endif %}
{% if overall_guidance.challenging_groups %}Challenging: {{ overall_guidance.challenging_groups|join(', ') }}{% endif %}
{% if key_transit %}Key transit: {{ key_transit }}{% endif %}

WRITING FORMULA:
{{ overall_guidance.formula }}
```

### 1.5 Update `daily_static.j2`

Add section with examples per pattern, including:
- Configuration line example
- 2-3 "good output" examples
- 1 "bad output" example marked as what NOT to do

---

## Phase 2: Relationship Weather

### 2.1 Verify HEART Group Writing Guidance

The HEART group already has `writing_guidance` with patterns: `all_positive`, `all_negative`, `one_negative_outlier`, `one_positive_outlier`, `split`, `all_neutral`.

Ensure `heart_group` in template context includes:
- `writing_guidance.pattern`
- `writing_guidance.formula`
- `driver` (meter name like "connections", "resilience", "vulnerability")
- `driver_score`
- `driver_aspect`

### 2.2 Update `daily_dynamic.j2` RELATIONSHIP WEATHER Section

```jinja2
================================================================================
RELATIONSHIP WEATHER (for relationship_weather.overview)
================================================================================
This is about {{ user_name }}'s general energy for connecting with others today.
Do NOT mention any specific person by name here.

HEART METER: {{ heart_group.unified_score|round(0)|int }}/100
Meters configuration: {{ heart_group.writing_guidance.pattern }} (connections={{ heart_group.meter_scores.connections|round(0)|int }}, resilience={{ heart_group.meter_scores.resilience|round(0)|int }}, vulnerability={{ heart_group.meter_scores.vulnerability|round(0)|int }})
Main energy driver: {{ heart_group.driver }} ({{ heart_group.driver_score }}/100)
Key transit: {{ heart_group.driver_aspect or 'multiple transits' }}

WRITING FORMULA:
{{ heart_group.writing_guidance.formula }}
```

### 2.3 Update `daily_static.j2` with Relationship Examples

Add examples per HEART pattern:
- `all_positive`: Strong relationship day, concrete relational actions
- `one_negative_outlier`: Name the off meter, cite transit, acknowledge others holding
- `all_negative`: Low across the board, normalize, protective actions

---

## Phase 3: Connection Vibe

### 3.1 Add Vibe Score Band Mapping

In `llm.py` or template, map vibe_score to qualitative bands:

| Score | Band | Description |
|-------|------|-------------|
| 80-100 | excellent | "deeply in sync", "unusually patient and generous" |
| 60-79 | good | "flowing", "easy to connect", "supportive" |
| 40-59 | neutral | "everyday", "fine but not charged" |
| 20-39 | edgy | "sensitive", "easily misunderstood" |
| 0-19 | tense | "high tension", "volatile", "likely to trigger old patterns" |

### 3.2 Update `daily_dynamic.j2` CONNECTION VIBE Section

Add explicit formula based on score band:

```jinja2
WRITING FORMULA:
{% if featured_connection.vibe_score >= 80 %}
High score ({{ featured_connection.vibe_score }}). Structure:
1) Address user by name and connection name.
2) Describe feeling: "unusually patient", "deeply in sync", "extra warm".
3) Cite the synastry transit.
4) Action: lean in, deepen, have important talk, do something fun together.
{% elif featured_connection.vibe_score >= 60 %}
Good score ({{ featured_connection.vibe_score }}). Structure:
1) Address user and connection.
2) Describe: "flowing", "easy connection", "supportive energy".
3) Cite transit.
4) Action: reach out, make plans, have that conversation.
{% elif featured_connection.vibe_score >= 40 %}
Neutral score ({{ featured_connection.vibe_score }}). Structure:
1) Keep it simple: everyday energy, nothing charged.
2) Cite transit briefly.
3) Action: keep things authentic but simple.
{% elif featured_connection.vibe_score >= 20 %}
Edgy score ({{ featured_connection.vibe_score }}). Structure:
1) Name potential friction: "sensitive", "easily misunderstood".
2) Cite tense transit.
3) Action: create space, delay big topics, communicate gently.
{% else %}
Tense score ({{ featured_connection.vibe_score }}). Structure:
1) Name tension: "volatile", "likely to trigger old patterns".
2) Cite transit.
3) Action: avoid heavy talks, use clear boundaries, give each other room.
{% endif %}
```

### 3.3 Update `daily_static.j2` with Connection Vibe Examples

Document score bands and example outputs for each.

---

## Phase 4: Testing

### 4.1 Unit Tests for `get_overall_writing_guidance()`

Add to `functions/tests/unit/test_group_score_formula.py`:

```python
def test_overall_all_flowing():
    """All groups >= 60"""
    groups = [
        {"name": "mind", "unified_score": 65},
        {"name": "heart", "unified_score": 70},
        {"name": "body", "unified_score": 75},
        {"name": "instincts", "unified_score": 62},
        {"name": "growth", "unified_score": 68},
    ]
    result = get_overall_writing_guidance(groups, "Sarah")
    assert result["pattern"] == "all_flowing"
    assert result["strongest_group"] == "body"  # highest
    assert result["strongest_score"] == 75

def test_overall_all_challenging():
    """All groups < 40"""
    groups = [
        {"name": "mind", "unified_score": 35},
        {"name": "heart", "unified_score": 25},
        {"name": "body", "unified_score": 38},
        {"name": "instincts", "unified_score": 30},
        {"name": "growth", "unified_score": 32},
    ]
    result = get_overall_writing_guidance(groups, "Sarah")
    assert result["pattern"] == "all_challenging"
    assert result["challenging_group"] == "heart"  # lowest
    assert result["challenging_score"] == 25

def test_overall_one_challenging():
    """1 group < 40, others >= 50"""
    groups = [
        {"name": "mind", "unified_score": 65},
        {"name": "heart", "unified_score": 35},  # challenging
        {"name": "body", "unified_score": 70},
        {"name": "instincts", "unified_score": 52},
        {"name": "growth", "unified_score": 60},
    ]
    result = get_overall_writing_guidance(groups, "Sarah")
    assert result["pattern"] == "one_challenging"
    assert result["challenging_group"] == "heart"
    assert result["challenging_groups"] == ["heart"]

def test_overall_one_shining():
    """1 group >= 60, others < 50"""
    groups = [
        {"name": "mind", "unified_score": 45},
        {"name": "heart", "unified_score": 70},  # shining
        {"name": "body", "unified_score": 42},
        {"name": "instincts", "unified_score": 48},
        {"name": "growth", "unified_score": 44},
    ]
    result = get_overall_writing_guidance(groups, "Sarah")
    assert result["pattern"] == "one_shining"
    assert result["shining_group"] == "heart"

def test_overall_mixed_day():
    """Some >= 60, some < 40"""
    groups = [
        {"name": "mind", "unified_score": 65},
        {"name": "heart", "unified_score": 35},
        {"name": "body", "unified_score": 70},
        {"name": "instincts", "unified_score": 30},
        {"name": "growth", "unified_score": 50},
    ]
    result = get_overall_writing_guidance(groups, "Sarah")
    assert result["pattern"] == "mixed_day"
    assert set(result["flowing_groups"]) == {"mind", "body"}
    assert set(result["challenging_groups"]) == {"heart", "instincts"}

def test_overall_neutral_day():
    """All groups in 40-60 range"""
    groups = [
        {"name": "mind", "unified_score": 52},
        {"name": "heart", "unified_score": 48},
        {"name": "body", "unified_score": 55},
        {"name": "instincts", "unified_score": 45},
        {"name": "growth", "unified_score": 50},
    ]
    result = get_overall_writing_guidance(groups, "Sarah")
    assert result["pattern"] == "neutral_day"
    assert result["challenging_group"] is None  # nothing < 40
```

### 4.2 Integration Testing

After each phase:
1. Run `uv run python functions/prototype.py` to see prompt output
2. Check LLM response follows the formula
3. Verify:
   - User name appears naturally
   - Specific areas named (not vague)
   - Transit cited (if provided)
   - Concrete action included

### 4.3 Edge Case Tests

- Test with `key_transit` missing/empty - ensure LLM omits transit citation entirely (no hallucination)
- Test boundary scores (exactly 40, exactly 60) - document behavior
- Test tie-breaking when multiple groups have same score

---

## Implementation Order

1. **Phase 1.1-1.2**: Create `get_overall_writing_guidance()` with tests
2. **Phase 1.3**: Update `llm.py` to call function and pass to context
3. **Phase 1.4**: Update `daily_dynamic.j2` OVERVIEW section
4. **Phase 1.5**: Update `daily_static.j2` with examples
5. **Phase 2.1-2.3**: Update RELATIONSHIP WEATHER section (reuse HEART guidance)
6. **Phase 3.1-3.3**: Update CONNECTION VIBE with score bands
7. Run all tests: `uv run pytest functions/tests/ -v`
8. Run mypy: `uv run mypy functions/ --ignore-missing-imports --exclude venv`

---

## Key Design Decisions

- **Threshold zones:** >= 60 (flowing), 40-60 (neutral/unremarkable), < 40 (challenging)
- **"Challenging" not "struggling/negative"** - genuine optimism voice per voice.md
- **Neutral groups (40-60) are not highlighted** - only call out clear outliers
- **Tie-breaking:** priority order `heart > mind > body > instincts > growth`
- **Missing transit:** omit citation entirely (no hallucination)
- **Formula:** "The stars show this challenge" + "They also show you have what it takes" + "Here's the move"

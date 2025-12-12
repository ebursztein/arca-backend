# Improvement Plan: Overall Energy & Relationship Sections

Apply the same learnings from meter group writing to overall energy and relationship sections.

---

## What We Learned from Meter Groups

1. **Meter configuration matters** - The pattern (all_positive, one_negative_outlier, split, etc.) determines how to write
2. **Name specific areas** - Not "today feels heavy" but "your body and heart are struggling"
3. **User's name naturally** - "Sarah, your..." or "Your... Sarah, you..."
4. **Cite the transit** - "This is Saturn pressing on your Sun"
5. **Concrete action** - "Skip the gym" not "lean into the energy"
6. **Structure matters** - Outliers explained first, then the rest

---

## 1. Overall Energy (daily_overview)

### Current State
- Generic guidance based on overall score
- No pattern-based writing formula
- Missing configuration of the 5 groups

### Improvement

#### 1.1 Add Groups Configuration to Dynamic Prompt

In `llm.py`, calculate the pattern across all 5 groups:

```python
def get_overall_writing_guidance(all_groups: list, user_name: str) -> dict:
    """
    Determine overall day pattern based on 5 group scores.
    """
    positive_groups = [g for g in all_groups if g['unified_score'] >= 50]
    negative_groups = [g for g in all_groups if g['unified_score'] < 50]

    # Similar logic to meter groups:
    # - all_groups_up: all 5 >= 50
    # - all_groups_down: all 5 < 50
    # - one_group_dragging: 4 up, 1 down
    # - one_group_shining: 1 up, 4 down
    # - split_day: mixed
```

#### 1.2 Add to Dynamic Template

```
OVERALL ENERGY: {{ overall_score }}/100
  Groups configuration: {{ overall_guidance.pattern }} (mind={{ mind_score }}, heart={{ heart_score }}, body={{ body_score }}, instincts={{ instincts_score }}, growth={{ growth_score }})
  Main driver: {{ overall_guidance.driver_group }} ({{ driver_score }}/100)
  Key transit: {{ key_transit }}

  WRITING FORMULA: {{ overall_guidance.formula }}
```

#### 1.3 Patterns & Formulas

| Pattern | Configuration | Formula |
|---------|---------------|---------|
| `all_groups_up` | All 5 groups >=50 | "Everything's working. [Strongest group] is leading - use it. [User name], [concrete action]." |
| `all_groups_down` | All 5 groups <50 | "[Weakest group] and [second weakest] are both low. [User name], keep it simple today - [concrete action]." |
| `one_group_dragging` | 4 up, 1 down | "[Dragging group] is off - [cite transit]. The rest is fine. [User name], work around [dragging group] - [concrete action]." |
| `one_group_shining` | 1 up, 4 down | "Only [shining group] is working - [cite transit]. [User name], lean on that - [concrete action]. Avoid [list weak groups]." |
| `split_day` | Mixed | "[Strong groups] are up, [weak groups] are down. [User name], play to strengths - [concrete action]." |

#### 1.4 Update Static Prompt

Add section for daily_overview explaining the pattern-based approach with examples.

---

## 2. Relationship Weather

### Current State
- `relationship_weather.overview`: Generic based on HEART group
- `relationship_weather.connection_vibe`: Based on synastry, but may be generic

### Improvement

#### 2.1 Use HEART Group Configuration

The HEART group already has meter configuration (connections, resilience, vulnerability). Use it directly:

```
RELATIONSHIP WEATHER:
  Meters configuration: {{ heart_group.writing_guidance.pattern }} (connections={{ connections_score }}, resilience={{ resilience_score }}, vulnerability={{ vulnerability_score }})
  Main energy driver: {{ heart_group.driver }} ({{ heart_group.driver_score }}/100)
  Key transit: {{ heart_group.driver_aspect }}

  WRITING FORMULA: {{ heart_group.writing_guidance.formula }}
```

#### 2.2 Patterns for Relationship Overview

Same patterns apply:

| Pattern | Example | Formula |
|---------|---------|---------|
| `all_positive` | conn=65, res=58, vuln=55 | "[User name], your relationship energy is strong. Connections and resilience are aligned. Good day to reach out - [concrete action]." |
| `one_negative_outlier` | conn=22, res=58, vuln=55 | "Your connections are off, [user name]. [Cite transit]. Your resilience and vulnerability are holding - [concrete action around connections]." |
| `all_negative` | conn=35, res=28, vuln=40 | "[User name], relationship energy is low across the board. [Cite transit]. Keep conversations light - [concrete action]." |

#### 2.3 Connection Vibe

Already has:
- vibe_score
- active_transits
- connection name

Apply same rules:
- Name what user feels with this person (concrete)
- Cite the synastry transit
- Concrete action

Example formula:
```
"[User name], you and [connection name] are [vibe description based on score]. This is [transit] affecting your [synastry point]. [Concrete action]."
```

---

## 3. Implementation Steps

### Phase 1: Overall Energy
1. [ ] Create `get_overall_writing_guidance()` in `meter_groups.py`
2. [ ] Update `llm.py` to calculate overall pattern and add to template context
3. [ ] Update `daily_dynamic.j2` to show groups configuration and formula
4. [ ] Update `daily_static.j2` with daily_overview examples per pattern

### Phase 2: Relationship Weather
1. [ ] Verify HEART group writing_guidance is already passed to template
2. [ ] Update relationship section in `daily_dynamic.j2` to show formula
3. [ ] Update `daily_static.j2` with relationship_weather examples per pattern

### Phase 3: Connection Vibe
1. [ ] Review current connection_vibe template section
2. [ ] Add writing formula based on vibe_score ranges
3. [ ] Update examples in static prompt

---

## 4. Testing

After each phase:
1. Run prototype.py to see prompt output
2. Check LLM response follows the formula
3. Verify:
   - User name appears naturally
   - Specific areas named (not vague)
   - Transit cited
   - Concrete action included

---

## 5. Files to Modify

- `functions/astrometers/meter_groups.py` - Add overall guidance function
- `functions/llm.py` - Calculate and pass overall/relationship guidance
- `functions/templates/horoscope/daily_dynamic.j2` - Add configuration sections
- `functions/templates/horoscope/daily_static.j2` - Add examples per pattern
- `functions/templates/voice.md` - Already updated with concrete rules

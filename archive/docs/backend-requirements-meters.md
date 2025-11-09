# Backend Requirements: Meter Groups Data

## Overview

This document specifies the backend changes needed to support the simplified meter groups UI in the iOS app. The goal is to provide group-level aggregated data and interpretations for each of the 9 meter groups.

**Target Endpoint**: `/daily-horoscope` (or consider merging `/detailed-horoscope` into this)

**Last Updated**: 2025-11-02

## Current State

### Existing Data Structure

The `/daily-horoscope` endpoint currently returns:

```json
{
  "date": "2025-11-02",
  "sun_sign": "Aries",
  "technical_analysis": "...",
  "lunar_cycle_update": "...",
  "daily_theme_headline": "...",
  "daily_overview": "...",
  "summary": "...",
  "actionable_advice": {
    "do": "...",
    "dont": "...",
    "reflect_on": "..."
  },
  "astrometers": {
    "overview_super_group": { ... },
    "overall_intensity": { ... },
    "overall_harmony": { ... },
    "mental_clarity": { ... },
    "decision_quality": { ... },
    // ... 20 more individual meters
  }
}
```

### What's Missing

1. **Group-level aggregations**: No averaged scores per meter group (mind, emotions, body, etc.)
2. **Group-level interpretations**: No narrative text explaining what each group means today
3. **Group-level state labels**: No quality labels (Optimal, Challenging, etc.) per group
4. **Group-level trends**: No trend data aggregated at group level
5. **Explicit group structure**: No clear mapping of which meters belong to which group

## Required Changes

### 1. Add `meter_groups` Object

Add a new top-level field to the daily horoscope response containing data for each of the 9 meter groups.

```json
{
  "date": "2025-11-02",
  "sun_sign": "Aries",
  // ... existing fields ...
  "astrometers": { ... },

  "meter_groups": {
    "mind": { ... },
    "emotions": { ... },
    "body": { ... },
    "career": { ... },
    "evolution": { ... },
    "elements": { ... },
    "spiritual": { ... },
    "collective": { ... },
    "overview": { ... }
  }
}
```

### 2. MeterGroup Data Structure

Each meter group object should contain:

```json
{
  "group_name": "mind",
  "display_name": "Mind",

  "scores": {
    "unified_score": 72.5,
    "harmony": 78.0,
    "intensity": 67.0
  },

  "state": {
    "label": "Supportive",
    "quality": "supportive"
  },

  "interpretation": "Your mental faculties are sharp and clear today. Communication flows easily, and you're able to process information quickly. Decision-making feels intuitive and well-grounded. This is an excellent time for important conversations or strategic planning.",

  "trend": {
    "unified_score": {
      "previous": 68.0,
      "delta": 4.5,
      "direction": "improving",
      "change_rate": "moderate"
    },
    "harmony": {
      "previous": 75.0,
      "delta": 3.0,
      "direction": "improving",
      "change_rate": "slow"
    },
    "intensity": {
      "previous": 61.0,
      "delta": 6.0,
      "direction": "increasing",
      "change_rate": "moderate"
    }
  },

  "meter_ids": [
    "mental_clarity",
    "decision_quality",
    "communication_flow"
  ]
}
```

### 3. Field Specifications

#### `group_name` (string, required)
- One of: `"mind"`, `"emotions"`, `"body"`, `"career"`, `"evolution"`, `"elements"`, `"spiritual"`, `"collective"`, `"overview"`
- Matches the MeterGroup enum in iOS app

#### `display_name` (string, required)
- Human-readable name: `"Mind"`, `"Emotions"`, `"Body"`, etc.
- Used for card headers

#### `scores` (object, required)
Aggregated scores across all meters in this group:

- `unified_score` (float, 0-100): Average of unified scores from all meters in group
- `harmony` (float, 0-100): Average of harmony scores
- `intensity` (float, 0-100): Average of intensity scores

**Calculation**: Simple arithmetic mean of all meters in the group.

Example:
```
Group "mind" contains: mental_clarity (75), decision_quality (70), communication_flow (73)
unified_score = (75 + 70 + 73) / 3 = 72.67
```

#### `state` (object, required)
Overall quality assessment for this group:

- `label` (string): Human-readable state like `"Optimal"`, `"Supportive"`, `"Challenging"`, `"Mixed"`, `"Intense"`
- `quality` (string): One of the QualityLabel enum values: `"excellent"`, `"supportive"`, `"harmonious"`, `"peaceful"`, `"mixed"`, `"quiet"`, `"challenging"`, `"intense"`

**Calculation**: Use the same logic as individual meters - map average harmony + intensity to a quality label.

#### `interpretation` (string, required)
2-4 sentence narrative explaining what this group means today:

- Should be written in second person ("You", "Your")
- Contextual to today's astrological influences
- Explains the overall energy/feeling for this life area
- Actionable or insightful
- Length: 150-300 characters ideally

**Example - Mind (Harmonious)**:
> "Your mental faculties are sharp and clear today. Communication flows easily, and you're able to process information quickly. This is an excellent time for important conversations or strategic planning."

**Example - Emotions (Challenging)**:
> "Emotions may feel intense or overwhelming today. Relationships might require extra patience and understanding. Take time for self-care and avoid making important decisions when feelings are running high."

**Example - Career (Mixed)**:
> "Your professional energy is moderate today. While ambition is present, opportunities may take time to materialize. Focus on steady progress rather than breakthrough moments."

#### `trend` (object, optional)
Trend data for the group (aggregated from individual meter trends):

Structure matches existing `TrendData` in individual meters:
```json
{
  "unified_score": {
    "previous": 68.0,
    "delta": 4.5,
    "direction": "improving",
    "change_rate": "moderate"
  }
}
```

- `previous` (float): Yesterday's average score
- `delta` (float): Change amount (can be negative)
- `direction` (string): One of `"improving"`, `"worsening"`, `"stable"`, `"increasing"`, `"decreasing"`
- `change_rate` (string): One of `"rapid"`, `"moderate"`, `"slow"`

**Note**: Only include if yesterday's data is available. Can be null/omitted initially.

#### `meter_ids` (array of strings, required)
List of meter IDs that belong to this group:

```json
["mental_clarity", "decision_quality", "communication_flow"]
```

This allows the app to:
1. Verify the grouping logic
2. Display individual meters when card is expanded
3. Link to detailed meter views

## Meter Group Definitions

### Group-to-Meter Mapping

Based on the current 23 meters, here's the proposed grouping:

#### **overview** (2 meters)
- `overall_intensity`
- `overall_harmony`

**Purpose**: Global cosmic weather snapshot

#### **mind** (3 meters)
- `mental_clarity`
- `decision_quality`
- `communication_flow`

**Purpose**: Cognitive functions, thinking, communication

#### **emotions** (3 meters)
- `emotional_intensity`
- `relationship_harmony`
- `emotional_resilience`

**Purpose**: Feelings, relationships, emotional well-being

#### **body** (3 meters)
- `physical_energy`
- `conflict_risk`
- `motivation_drive`

**Purpose**: Physical energy, action, vitality

#### **career** (4 meters)
- `career_ambition`
- `opportunity_window`
- `challenge_intensity`
- `transformation_pressure`

**Purpose**: Professional life, ambition, career opportunities

#### **evolution** (1 meter)
- `karmic_lessons`

**Purpose**: Personal growth, life lessons, transformation

**Note**: This group only has 1 meter currently. Consider if `transformation_pressure` should move here.

#### **elements** (4 meters)
- `fire_energy`
- `earth_energy`
- `air_energy`
- `water_energy`

**Purpose**: Elemental balance and energies

#### **spiritual** (1 meter)
- `intuition_spirituality`

**Purpose**: Spiritual connection, intuition, inner wisdom

**Note**: Could potentially merge with evolution or expand with more spiritual meters.

#### **collective** (2 meters)
- `innovation_breakthrough`
- `social_collective`

**Purpose**: Social energies, innovation, collective consciousness

### Group Display Order

Suggested order in the UI (most relevant to least):

1. **overview** - Start here
2. **mind** - Daily cognitive function
3. **emotions** - Emotional well-being
4. **body** - Physical energy
5. **career** - Professional life
6. **evolution** - Personal growth
7. **elements** - Elemental balance
8. **spiritual** - Inner wisdom
9. **collective** - Social energies

## Implementation Approach

### Option A: Add to Existing Endpoint (Recommended)

Extend the `/daily-horoscope` endpoint to include `meter_groups`:

**Pros**:
- Single API call gets all data
- Backwards compatible (existing clients ignore new field)
- Simpler for iOS app

**Cons**:
- Larger response payload
- More computation in one endpoint

### Option B: Separate Endpoint

Create new `/meter-groups` endpoint:

**Pros**:
- Modular, focused responsibility
- Can be cached separately

**Cons**:
- Requires two API calls
- More complexity in iOS app
- Redundant data (meters already in daily horoscope)

**Recommendation**: Option A - add to existing endpoint.

### Option C: Merge Detailed Horoscope (Future Enhancement)

Consider merging `/detailed-horoscope` into `/daily-horoscope`:

**Current**: Two separate calls
1. `/daily-horoscope` - basic info + astrometers
2. `/detailed-horoscope` - deeper interpretations

**Proposed**: Single comprehensive call
1. `/daily-horoscope` - includes basic info, astrometers, meter groups, AND detailed interpretations

**Benefits**:
- Simplifies iOS app data fetching
- Reduces API calls
- All data available immediately
- Better UX (no loading states)

**Trade-off**:
- Larger payload (but modern devices can handle it)
- Longer generation time (can optimize with caching)

## Generation Logic

### Calculating Group Scores

```python
def calculate_group_scores(meters: List[MeterReading]) -> Dict[str, float]:
    """Calculate average scores for a group of meters."""
    unified_scores = [m.unified_score for m in meters]
    harmony_scores = [m.harmony for m in meters]
    intensity_scores = [m.intensity for m in meters]

    return {
        "unified_score": sum(unified_scores) / len(unified_scores),
        "harmony": sum(harmony_scores) / len(harmony_scores),
        "intensity": sum(intensity_scores) / len(intensity_scores)
    }
```

### Generating Group Interpretations

**Approach 1: LLM Generation**
- Use GPT-4/Claude to generate group interpretation
- Context: Individual meter interpretations + astrological data
- Prompt: "Synthesize the following meter readings into a cohesive 2-3 sentence interpretation for the [GROUP] area of life today..."

**Approach 2: Template-Based**
- Pre-written templates with variable sections
- Fill in based on score ranges and aspects
- Faster, more consistent, but less dynamic

**Approach 3: Hybrid**
- Templates for common patterns
- LLM for edge cases or more nuanced situations
- Balance between speed and quality

**Recommendation**: Start with Approach 1 (LLM), optimize later if needed.

### Determining Group State

Map average harmony to state label:

```python
def get_quality_label(harmony: float, intensity: float) -> Dict[str, str]:
    """Determine quality label based on harmony and intensity."""
    if harmony >= 75:
        if intensity >= 75:
            return {"label": "Excellent", "quality": "excellent"}
        elif intensity >= 40:
            return {"label": "Supportive", "quality": "supportive"}
        else:
            return {"label": "Peaceful", "quality": "peaceful"}
    elif harmony >= 50:
        if intensity >= 60:
            return {"label": "Mixed", "quality": "mixed"}
        else:
            return {"label": "Quiet", "quality": "quiet"}
    else:
        if intensity >= 60:
            return {"label": "Intense", "quality": "intense"}
        else:
            return {"label": "Challenging", "quality": "challenging"}
```

## Example Response

### Complete meter_groups Object

```json
{
  "meter_groups": {
    "mind": {
      "group_name": "mind",
      "display_name": "Mind",
      "scores": {
        "unified_score": 72.5,
        "harmony": 78.0,
        "intensity": 67.0
      },
      "state": {
        "label": "Supportive",
        "quality": "supportive"
      },
      "interpretation": "Your mental faculties are sharp and clear today. Communication flows easily, and you're able to process information quickly. This is an excellent time for important conversations or strategic planning.",
      "trend": {
        "unified_score": {
          "previous": 68.0,
          "delta": 4.5,
          "direction": "improving",
          "change_rate": "moderate"
        }
      },
      "meter_ids": [
        "mental_clarity",
        "decision_quality",
        "communication_flow"
      ]
    },
    "emotions": {
      "group_name": "emotions",
      "display_name": "Emotions",
      "scores": {
        "unified_score": 45.0,
        "harmony": 38.0,
        "intensity": 72.0
      },
      "state": {
        "label": "Challenging",
        "quality": "challenging"
      },
      "interpretation": "Emotions may feel intense or overwhelming today. Relationships might require extra patience and understanding. Take time for self-care and avoid making important decisions when feelings are running high.",
      "trend": {
        "unified_score": {
          "previous": 58.0,
          "delta": -13.0,
          "direction": "worsening",
          "change_rate": "moderate"
        }
      },
      "meter_ids": [
        "emotional_intensity",
        "relationship_harmony",
        "emotional_resilience"
      ]
    }
    // ... remaining 7 groups
  }
}
```

## Testing Requirements

### Validation Checklist

- [ ] All 9 groups present in response
- [ ] Each group has all required fields
- [ ] Scores are valid floats between 0-100
- [ ] State labels match predefined options
- [ ] Quality enums match iOS app expectations
- [ ] Interpretations are 150-300 characters
- [ ] Meter IDs reference valid existing meters
- [ ] Trend data structure matches individual meters
- [ ] Group scores are mathematical averages of meter scores
- [ ] Response size is reasonable (< 100KB)

### Test Cases

1. **All Harmonious**: All groups show high harmony (75+)
2. **All Challenging**: All groups show low harmony (< 40)
3. **Mixed**: Some groups harmonious, some challenging
4. **Edge Cases**: Single-meter groups (evolution, spiritual)
5. **No Trends**: Response valid when trend data unavailable
6. **Extreme Scores**: Groups at 0, 50, 100 boundaries

## Timeline

### Phase 1: Minimum Viable (Week 1)
- [ ] Add `meter_groups` object with 9 groups
- [ ] Calculate aggregated scores
- [ ] Generate basic state labels
- [ ] Return meter IDs for each group
- [ ] Template-based interpretations (if LLM too slow)

### Phase 2: Enhanced (Week 2)
- [ ] LLM-generated interpretations
- [ ] Trend data for groups
- [ ] Optimize generation time
- [ ] Add caching for generated group data

### Phase 3: Merge (Week 3+)
- [ ] Consider merging detailed horoscope into daily endpoint
- [ ] Optimize payload size
- [ ] Add compression if needed

## Questions for Backend Team

1. **Generation Time**: How long does LLM interpretation generation add? Target < 2s total.
2. **Caching Strategy**: Can we cache group interpretations similarly to individual meters?
3. **Backwards Compatibility**: Do older iOS app versions handle extra fields gracefully?
4. **Payload Size**: What's current response size? Acceptable to add ~5-10KB?
5. **Grouping Logic**: Agreement on meter-to-group mapping above?
6. **Trend Calculation**: Should group trends be averages, or derived from aggregated scores?
7. **Merge Timeline**: Feasibility of merging detailed horoscope into daily endpoint?

## iOS App Integration

Once backend is ready, iOS app will:

1. Update `DailyHoroscope` model to include optional `meterGroups: [String: MeterGroupData]?`
2. Create `MeterGroupData` struct matching JSON structure
3. Parse and display in new `MeterGroupCard` component
4. Fall back to existing UI if `meterGroups` is null (backwards compatibility)
5. Gradually deprecate old super-group based UI

## Success Metrics

- Response time < 3s for complete daily horoscope with meter groups
- Interpretation quality rated by users (in-app feedback)
- Reduction in taps to valuable information (analytics)
- User engagement with expanded meter details (analytics)

---

**Document Version**: 1.0
**Author**: Backend Requirements for Meter Groups
**Status**: Ready for Backend Team Review
**Priority**: High

# Compatibility System

**Last Updated:** December 2025

---

## Overview

The compatibility system calculates relationship compatibility between two people based on their natal charts. It supports three relationship modes (romantic, friendship, coworker) with different category breakdowns for each.

**Key Files:**
- `functions/compatibility.py` - Core calculations and models
- `functions/compatibility_labels/` - JSON-based labels and LLM guidance
- `functions/llm.py` - LLM prompt generation (`generate_compatibility_result()`)

---

## API Response Structure

### `get_compatibility` Endpoint

Returns a `CompatibilityResult` with:

```json
{
  "headline": "Gemini meets Sagittarius: Electric opposites",
  "summary": "You and Mike share a magnetic connection...",
  "strengths": "Your emotional bond runs deep...",
  "growth_areas": "Communication needs work...",
  "advice": "Lead with curiosity, not criticism.",
  "mode": {
    "type": "romantic",
    "overall_score": 64,
    "overall_label": "Solid",
    "vibe_phrase": "Magnetic Pull",
    "categories": [...]
  },
  "aspects": [...],
  "composite": {...},
  "karmic": {...}
}
```

### ModeCompatibility

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | "romantic", "friendship", or "coworker" |
| `overall_score` | int | 0-100, where 50 is neutral |
| `overall_label` | string | Band label: "Volatile", "Rocky", "Mixed", "Solid", "Seamless" |
| `vibe_phrase` | string | LLM-generated 1-3 word vibe (e.g., "Slow Burn", "Ride or Die") |
| `categories` | array | Category breakdowns |

### CompatibilityCategory

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Category ID (e.g., "emotional", "longTerm") |
| `name` | string | Display name (e.g., "Emotional Connection") |
| `score` | int | 0-100, where 50 is neutral |
| `label` | string | Band label from JSON (e.g., "Soul-Level", "Combustible") |
| `description` | string | What this category measures |
| `insight` | string | LLM-generated 1-2 sentence insight |
| `aspect_ids` | array | Top 3-5 aspect IDs driving this score |
| `driving_aspects` | array | DrivingAspect objects with human-readable summaries |

### DrivingAspect

| Field | Type | Description |
|-------|------|-------------|
| `aspect_id` | string | Reference to full aspect (e.g., "asp_001") |
| `user_planet` | string | User's planet (e.g., "Moon") |
| `their_planet` | string | Connection's planet (e.g., "Venus") |
| `aspect_type` | string | trine, square, conjunction, etc. |
| `is_harmonious` | bool | True if supportive, False if challenging |
| `summary` | string | Human-readable (e.g., "Your emotional needs flow easily with their love style") |

---

## Categories by Mode

### Romantic (6 categories)
| ID | Name | What It Measures |
|----|------|------------------|
| `emotional` | Emotional Connection | Moon-Moon, Moon-Venus, Neptune aspects |
| `communication` | Communication | Mercury aspects, mental compatibility |
| `attraction` | Attraction | Venus-Mars, Pluto aspects, physical chemistry |
| `values` | Shared Values | Saturn, Jupiter, Sun alignment on life goals |
| `longTerm` | Long-term Potential | Saturn aspects, Juno, commitment indicators |
| `growth` | Growth Together | Pluto, North Node, transformation potential |

### Friendship (5 categories)
| ID | Name | What It Measures |
|----|------|------------------|
| `emotional` | Emotional | Emotional understanding and vulnerability |
| `communication` | Communication | How easily conversation flows |
| `fun` | Fun & Adventure | Joy, spontaneity, shared adventures |
| `loyalty` | Loyalty & Support | Dependability and trust |
| `sharedInterests` | Shared Interests | Hobby and interest overlap |

### Coworker (5 categories)
| ID | Name | What It Measures |
|----|------|------------------|
| `communication` | Communication | Professional information exchange |
| `collaboration` | Collaboration | Working together on shared tasks |
| `reliability` | Reliability | Professional dependability |
| `ambition` | Ambition Alignment | Career drive alignment |
| `powerDynamics` | Power Dynamics | Authority and influence balance |

---

## Labels System

### File Structure

```
functions/compatibility_labels/
├── __init__.py
├── labels.py                    # Loading & lookup functions
└── labels/
    ├── overall.json             # Overall compatibility labels
    ├── romantic/
    │   ├── romantic_emotional.json
    │   ├── romantic_communication.json
    │   ├── romantic_attraction.json
    │   ├── romantic_values.json
    │   ├── romantic_long_term.json
    │   └── romantic_growth.json
    ├── friendship/
    │   ├── friendship_emotional.json
    │   ├── friendship_communication.json
    │   ├── friendship_fun.json
    │   ├── friendship_loyalty.json
    │   └── friendship_shared_interests.json
    └── coworker/
        ├── coworker_communication.json
        ├── coworker_collaboration.json
        ├── coworker_reliability.json
        ├── coworker_ambition.json
        └── coworker_power_dynamics.json
```

### Band System

All categories use 5 bands:

| Band ID | Score Range | Overall | Romantic Emotional | Friendship Loyalty |
|---------|-------------|---------|-------------------|-------------------|
| `very_high` | 80-100 | Seamless | Soul-Level | Ride-or-Die |
| `high` | 60-80 | Solid | Warm | Steady |
| `mid` | 40-60 | Mixed | Surface-Deep | Decent |
| `low` | 20-40 | Rocky | Mismatched | Patchy |
| `very_low` | 0-20 | Volatile | Shut Off | Flimsy |

### JSON File Structure

```json
{
  "_schema_version": "1.0",
  "_category": "emotional",
  "_mode": "romantic",
  "metadata": {
    "category_id": "emotional",
    "display_name": "Emotional Connection",
    "description": "How deeply you connect emotionally",
    "sentence_template": "Emotionally, this bond feels ___."
  },
  "bands": [
    { "id": "very_low", "min": 0, "max": 20 },
    { "id": "low", "min": 20, "max": 40 },
    { "id": "mid", "min": 40, "max": 60 },
    { "id": "high", "min": 60, "max": 80 },
    { "id": "very_high", "min": 80, "max": 100 }
  ],
  "astrological_basis": {
    "primary_planets": ["Moon", "Venus", "Neptune"],
    "what_it_measures": "Moon-Moon aspects show emotional rhythm...",
    "planet_meanings": {
      "Moon": "emotional needs and instincts",
      "Venus": "love style and what you value",
      "Neptune": "dreams, idealization, and intuition"
    }
  },
  "bucket_labels": {
    "very_low": {
      "label": "Shut Off",
      "guidance": "They struggle to reach each other emotionally; validate the loneliness..."
    },
    "low": {
      "label": "Mismatched",
      "guidance": "Feel things on different wavelengths; talk about understanding..."
    },
    "mid": {
      "label": "Surface-Deep",
      "guidance": "Some depth but not automatic; emotional closeness grows if both make effort."
    },
    "high": {
      "label": "Warm",
      "guidance": "Generally 'get' each other's feelings; encourage honest sharing."
    },
    "very_high": {
      "label": "Soul-Level",
      "guidance": "Strong emotional resonance; describe feeling deeply seen..."
    }
  }
}
```

### Key Functions

```python
from compatibility_labels.labels import (
    get_category_label,           # Get label for score
    get_category_description,     # Get category description
    get_category_guidance,        # Get LLM guidance for score band
    get_overall_label,            # Get overall label
    get_overall_guidance,         # Get overall LLM guidance
    generate_driving_aspect_summary,      # Human-readable aspect summary
    generate_compat_headline_guidance,    # 25-case headline matrix
)

# Examples
get_category_label("romantic", "emotional", 85)  # "Soul-Level"
get_overall_label(65)  # "Solid"
```

---

## Scoring Algorithm

### Category Score Calculation

```python
for each aspect matching category's planet pairs:
    orb_weight = get_orb_weight(aspect.orb)      # 1.0 to 0.25
    aspect_weight = ASPECT_TYPE_WEIGHTS[type]    # 0.6 to 1.2
    harmony = +1 if harmonious else -1
    contribution = harmony * aspect_weight * orb_weight
    total_score += contribution
    total_weight += aspect_weight * orb_weight

# Element bonus for emotional/attraction/values
if category uses elements:
    element_score = get_element_score(chart1, chart2)
    total_score += element_score
    total_weight += 0.3

# Normalize and smooth
normalized = (total_score / total_weight) * 100
variation = chart_variation(chart1, chart2, category)
adjusted = normalized + variation
final = sigmoid_compress(adjusted, steepness)  # Bounded ~0-100
```

### Aspect Type Weights

```python
ASPECT_TYPE_WEIGHTS = {
    "conjunction": 1.2,   # Strongest
    "trine": 1.0,
    "opposition": 0.9,
    "square": 0.8,
    "sextile": 0.7,
    "quincunx": 0.6,      # Weakest
}
```

### Element Compatibility

Applied to: emotional, attraction, values

```python
ELEMENT_COMPATIBILITY = {
    ("fire", "fire"): 0.3,      # Same element
    ("fire", "air"): 0.2,       # Complementary
    ("fire", "earth"): -0.1,    # Neutral-challenging
    ("fire", "water"): -0.2,    # Challenging
    # ... etc
}
```

---

## Karmic Detection

Identifies "fated" connections based on North/South Node aspects.

### Configuration

```python
KARMIC_TIER1_PLANETS = {"sun", "moon", "saturn", "pluto"}  # Badge-level
KARMIC_TIER2_PLANETS = {"venus", "mars", "mercury"}        # Flavor only

KARMIC_TIER1_ORB = 1.0    # Sun, Moon, Saturn
KARMIC_PLUTO_ORB = 0.75   # Pluto (tighter)
KARMIC_TIER2_ORB = 0.75   # Venus, Mars, Mercury

KARMIC_PRIMARY_ASPECTS = {"conjunction", "opposition"}  # Count toward badge
KARMIC_SECONDARY_ASPECTS = {"square"}  # Saturn/Pluto only

KARMIC_BADGE_THRESHOLD = 2  # Need 2+ Tier-1 primary aspects
```

### What's Checked

- Both nodes: North Node AND South Node
- Both directions: User's planets to Connection's nodes AND vice versa
- 4 total checks: user_north, user_south, conn_north, conn_south

### Karmic Themes

```python
KARMIC_NORTH_HINTS = {
    "sun": "This relationship pulls you toward your future identity",
    "moon": "Destined emotional growth",
    "saturn": "Karmic lessons around commitment",
    "pluto": "Transformative destiny bond",
}

KARMIC_SOUTH_HINTS = {
    "sun": "Deep past-life recognition",
    "moon": "Uncanny emotional safety - feels like you've always known each other",
    "saturn": "Unfinished karmic business",
    "pluto": "Intense past-life entanglement",
}
```

### Result

```json
{
  "karmic": {
    "is_karmic": true,
    "theme": "Fated growth through Moon",
    "destiny_note": "Your connection feels written in the stars..."
  }
}
```

---

## LLM Prompt Structure

The `generate_compatibility_result()` function builds a prompt with:

1. **Voice guidelines** - From `templates/voice.md`
2. **Chart data** - Both people's Sun, Moon, Rising
3. **Relationship context** - Mode, category, label (crush/partner/etc.)
4. **Score data** with labels and guidance:
   ```
   Overall Score: 64/100
   Overall Label: "Solid"
   Overall Guidance: Generally healthy, dependable bond...
   ```
5. **25-case headline matrix**:
   ```
   HEADLINE GUIDANCE:
   Pattern: strong_contrast
   Conjunction: "but"
   Tone: celebrate the win, honestly name the gap
   Instruction: Lead with Shared Values (label: "Same Page")
   but acknowledge Long-term Potential (label: "Fragile").
   ```
6. **Per-category context**:
   ```
   - emotional (Emotional Connection): 91, Label: "Soul-Level"
     Description: How deeply you connect emotionally
     LLM Guidance: Use the label "Soul-Level" in your insight.
       - Your dreams (Neptune) flows easily with their emotional needs (Moon)
   ```
7. **Key aspects** - Top 8 aspects with orbs
8. **Composite chart** - Relationship's own Sun/Moon/Rising
9. **Karmic section** - Only if `is_karmic=True`
10. **Output rules** - What to generate

---

## Test Commands

```bash
# Unit tests
uv run pytest tests/unit/test_compatibility.py -v

# Integration tests (requires API key)
uv run pytest tests/integration/test_compatibility_llm.py -v

# Debug prompt output
DEBUG_LLM=1 uv run python -c "
from compatibility import get_compatibility_from_birth_data
from llm import generate_compatibility_result
data = get_compatibility_from_birth_data(...)
result = generate_compatibility_result(data, 'love', 'partner')
"
# Writes to: backend_output/prompts/compatibility_love.json
```

---

## Distribution Stats

From 25,000 random pair tests:

```
+----------------------+------------+------------+
| Metric               | Value      | Target     |
+----------------------+------------+------------+
| Overall Mean         |       54.0 | 45-55      |
| Overall StdDev       |       11.0 | 10-20      |
| Karmic Rate          |       7.8% | 5-10%      |
| Extreme Rate         |       <15% | <25%       |
| Category Correlation |      0.129 | <0.30      |
+----------------------+------------+------------+
```

---

## Tuning Guide

### If karmic rate too high:
- Decrease `KARMIC_TIER1_ORB` (currently 1.0)
- Increase `KARMIC_BADGE_THRESHOLD` (currently 2)

### If karmic rate too low:
- Increase `KARMIC_TIER1_ORB`
- Decrease `KARMIC_BADGE_THRESHOLD` to 1

### If category scores too extreme:
- Add more planet pairs to that category
- Adjust sigmoid steepness in `CATEGORY_SMOOTHING_CONFIG`

### If overall scores too clustered:
- Adjust `ASPECT_TYPE_WEIGHTS` spread
- Modify element compatibility values

### To change labels:
- Edit JSON files in `compatibility_labels/labels/`
- Clear LRU cache or restart server

---

## Key Constants Location

| Constant | File | Line | Purpose |
|----------|------|------|---------|
| `ASPECT_TYPE_WEIGHTS` | compatibility.py | ~65 | Aspect strength weights |
| `ELEMENT_COMPATIBILITY` | compatibility.py | ~85 | Element pairing scores |
| `ROMANTIC_CATEGORIES` | compatibility.py | ~160 | Planet pairs per category |
| `KARMIC_TIER1_PLANETS` | compatibility.py | ~816 | Badge-level planets |
| `KARMIC_TIER1_ORB` | compatibility.py | ~820 | Orb thresholds |
| `CATEGORY_FILE_MAP` | labels.py | ~75 | camelCase to snake_case mapping |

# Meter Rename V2 - Implementation Summary

## Overview

Renamed 17 meters and 2 groups to Gen Z-friendly names. Simplified state labels from 15-state matrix to 4-bucket system computed by backend.

## Group Renames

| Old | New |
|-----|-----|
| emotions | heart |
| spirit | instincts |

## Meter Renames (17 total)

### MIND (3 meters)
| Old | New |
|-----|-----|
| mental_clarity | clarity |
| focus | focus |
| communication | communication |

### HEART (was EMOTIONS, 3 meters)
| Old | New |
|-----|-----|
| inner_stability | resilience |
| love | connections |
| sensitivity | vulnerability |

### BODY (3 meters)
| Old | New |
|-----|-----|
| vitality | energy |
| wellness | strength |
| drive | drive |

### INSTINCTS (was SPIRIT, 4 meters)
| Old | New |
|-----|-----|
| purpose | vision |
| connection | flow |
| intuition | intuition |
| creativity | creativity |

### GROWTH (4 meters)
| Old | New |
|-----|-----|
| opportunities | momentum |
| career | ambition |
| growth | evolution |
| social_life | circle |

## State Labels - New 4-Bucket System

### How It Works
- Backend computes `unified_score` from intensity + harmony
- Backend maps `unified_score` to one of 4 bucket labels
- iOS displays the bucket label directly
- **LLM does NOT generate state labels**

### Bucket Thresholds (Quartile-based)
```
unified_score < -25  → Bucket 1 (Challenge)
-25 <= score < 10    → Bucket 2 (Mixed)
10 <= score < 50     → Bucket 3 (Good)
score >= 50          → Bucket 4 (Peak)
```

### Bucket Labels by Group
```
mind:      Overloaded → Hazy → Clear → Sharp
heart:     Heavy → Tender → Grounded → Magnetic
body:      Depleted → Low Power Mode → Powering Through → Surging
instincts: Disconnected → Noisy → Tuned In → Aligned
growth:    Uphill → Pacing → Climbing → Unstoppable
overall:   Challenging → Chaotic → Peaceful → Flowing
```

## LLM Changes

### What LLM Generates
- 5 group interpretations (mind, heart, body, instincts, growth)
- Other horoscope content (headline, overview, advice, etc.)

### What LLM Does NOT Generate
- State labels (computed by backend)
- Individual meter interpretations (empty strings)

### Response Schema (DailyHoroscopeResponse)
```python
# Group interpretations only
mind_interpretation: str
heart_interpretation: str
body_interpretation: str
instincts_interpretation: str
growth_interpretation: str

# NO state_label fields
# NO individual meter interpretations
```

## Files Modified

### Core Logic
- `functions/astrometers/hierarchy.py` - Meter and MeterGroupV2 enums
- `functions/astrometers/meters.py` - get_state_label() with bucket logic
- `functions/astrometers/meter_groups.py` - get_group_state_label() with bucket logic
- `functions/astrometers/constants.py` - Meter references

### Labels (JSON files renamed + content updated)
- `functions/astrometers/labels/*.json` - 17 meter files
- `functions/astrometers/labels/groups/*.json` - 5 group files
- `functions/astrometers/labels/word_banks.json` - Group name references

### Models & API
- `functions/models.py` - Pydantic models
- `functions/llm.py` - METER_NAMES, METER_GROUP_MAPPING, response schema
- `functions/main.py` - If any references

### Calibration
- `functions/astrometers/calibration/calibration_constants.json` - Meter keys

### Templates
- `functions/templates/horoscope/daily_static.j2` - Removed state label section

---

# TODO: Review & Cleanup

## 1. Review JSON Files - Names & Descriptions

Each meter JSON needs review to ensure:
- `metadata.display_name` matches new name
- `description.overview` makes sense for new name
- `description.detailed` makes sense for new name
- `description.keywords` are relevant

### Files to Review
```
functions/astrometers/labels/
├── clarity.json        # was mental_clarity
├── resilience.json     # was inner_stability
├── connections.json    # was love
├── vulnerability.json  # was sensitivity
├── energy.json         # was vitality
├── strength.json       # was wellness
├── vision.json         # was purpose
├── flow.json           # was connection
├── ambition.json       # was career
├── evolution.json      # was growth
├── momentum.json       # was opportunities
├── circle.json         # was social_life
├── focus.json          # unchanged - still review
├── communication.json  # unchanged - still review
├── drive.json          # unchanged - still review
├── intuition.json      # unchanged - still review
└── creativity.json     # unchanged - still review

functions/astrometers/labels/groups/
├── mind.json
├── heart.json          # was emotions
├── body.json
├── instincts.json      # was spirit
└── growth.json
```

## 2. Clean Up JSON - Remove Useless Fields

Fields that can likely be removed from meter JSONs:
- `experience_labels` - REMOVED (iOS handles buckets)
- `advice_templates` - Check if still used
- `_schema_version` - May not be needed
- `_last_updated` - May not be needed

### Target JSON Structure (minimal)
```json
{
  "_meter": "clarity",
  "metadata": {
    "meter_id": "clarity",
    "display_name": "Clarity",
    "group": "mind"
  },
  "description": {
    "overview": "...",
    "detailed": "...",
    "keywords": ["...", "...", "..."]
  },
  "astrological_foundation": {
    "primary_planets": {...},
    "natal_planets_tracked": [...],
    "transit_planets_tracked": [...]
  }
}
```

## 3. Clean Up Dynamic Prompt (daily_dynamic.j2)

Review `functions/templates/horoscope/daily_dynamic.j2` for:
- Old meter/group name references
- Unnecessary data being passed to LLM
- Optimization opportunities (reduce token count)

### Check for:
- References to "emotions" or "spirit" → should be "heart" or "instincts"
- State label instructions → should be removed
- Individual meter data → may not be needed if LLM only interprets groups

---

## Breaking Changes for iOS

iOS needs to update:
1. Hardcoded meter names (17 renames)
2. Hardcoded group names (2 renames: emotions→heart, spirit→instincts)
3. State label display - use `state_label` field from API response
4. Any saved preferences referencing old meter names

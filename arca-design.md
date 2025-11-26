# Arca Backend - Technical Design Document

This document provides the complete technical reference for the Arca astrology backend. It consolidates all design decisions, algorithms, and implementation details into a single source of truth.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Astrometers System](#astrometers-system)
3. [Core Algorithms](#core-algorithms)
4. [Calibration System](#calibration-system)
5. [API Reference](#api-reference)
6. [Development Commands](#development-commands)

---

## Project Overview

Arca is a daily astrology app backend providing personalized readings through AI-powered interpretations of astrological transits.

### Architecture

```
iOS App <-> Firebase Cloud Functions (Python 3.13) <-> Firestore + Gemini LLM
```

### Key Technologies

| Technology | Purpose |
|------------|---------|
| `natal` | Swiss Ephemeris wrapper for astronomical calculations |
| `google-genai` | Gemini LLM for personalized interpretations |
| `pydantic` | Type-safe data models |
| `firebase-functions` | Serverless function framework |

---

## Astrometers System

The astrometers system quantifies daily astrological energy into measurable meters.

### Structure

```
17 Individual Meters
    |
    v
5 User-Facing Groups (Mind, Emotions, Body, Spirit, Growth)
    |
    v
2 Overall Aggregates (Overall Intensity, Overall Harmony)
```

### 17 Meters by Group

| Group | Meters | Natal Planets/Houses |
|-------|--------|---------------------|
| **Mind** | mental_clarity, focus, communication | Sun, Mercury; House 9 |
| **Emotions** | love, inner_stability, sensitivity | Venus, Moon; House 7 |
| **Body** | vitality, drive, wellness | Sun, Mars; House 6 |
| **Spirit** | purpose, connection, intuition, creativity | Sun, Neptune, Moon, Venus |
| **Growth** | opportunities, career, growth, social_life | Jupiter, Saturn; Houses 10, 11 |

### Dual-Metric Scoring

Each meter produces two scores:

| Metric | Question Answered | Range | Calculation |
|--------|-------------------|-------|-------------|
| **Intensity** | "How much is happening?" | 0-100 | Normalized DTI |
| **Harmony** | "What type of energy?" | 0-100 | Normalized HQS (50=neutral) |

### State Labels (5x3 Matrix)

Each meter has 15 state labels based on intensity level and harmony level:

**Intensity Levels:**
- Quiet: 0-30
- Mild: 31-50
- Moderate: 51-70
- High: 71-85
- Extreme: 86-100

**Harmony Levels:**
- Challenging: 0-30
- Mixed: 31-69
- Harmonious: 70-100

---

## Core Algorithms

### DTI (Dual Transit Influence) - Intensity

**Formula:** `DTI = Sum(W_i * P_i)` for all active transit aspects

DTI measures the total magnitude of astrological activity affecting a meter.

### HQS (Harmonic Quality Score) - Harmony

**Formula:** `HQS = Sum(W_i * P_i * Q_i)` for all active transit aspects

HQS measures the supportive vs challenging nature of transits.

### Component Calculations

#### W_i: Weightage Factor

**Formula:** `W_i = (Planet_Base + Dignity_Score + Ruler_Bonus) * House_Multiplier * Sensitivity`

| Component | Values |
|-----------|--------|
| **Planet Base** | Sun/Moon=10, Mercury/Venus/Mars=7, Jupiter/Saturn=5, Outer planets=3 |
| **Dignity Score** | Domicile=+5, Exaltation=+4, Neutral=0, Detriment=-5, Fall=-4 |
| **Ruler Bonus** | +5 if natal planet rules the Ascendant |
| **House Multiplier** | Angular(1,4,7,10)=3x, Succedent(2,5,8,11)=2x, Cadent(3,6,9,12)=1x |
| **Sensitivity** | User-configurable 0.5-2.0, default=1.0 |

**Example:**
```
Natal Sun in Leo (domicile) in 10th house (angular), chart ruler:
W_i = (10 + 5 + 5) * 3 * 1.0 = 60
```

#### P_i: Transit Power

**Formula:** `P_i = Aspect_Base * Orb_Factor * Direction_Mod * Station_Mod * Transit_Weight`

| Component | Values |
|-----------|--------|
| **Aspect Base** | Conjunction=10, Opposition=9, Square=8, Trine=6, Sextile=4 |
| **Orb Factor** | Linear: `1.0 - (deviation / max_orb)`, range 0-1 |
| **Direction Mod** | Exact(<0.5deg)=1.5, Applying=1.3, Separating=0.7 |
| **Station Mod** | At station=1.8, linear decay to 1.2 over 5 days |
| **Transit Weight** | Outer(Uranus/Neptune/Pluto)=1.5, Social(Jupiter/Saturn)=1.2, Inner=1.0, Moon=0.8 |

**Max Orbs by Aspect and Planet:**

| Aspect Type | Luminary Involved | Outer Transit | Standard |
|-------------|-------------------|---------------|----------|
| Conjunction/Opposition | 10 deg | 6 deg | 8 deg |
| Square/Trine | 8 deg | 5 deg | 7 deg |
| Sextile | 6 deg | 4 deg | 5 deg |

**Example:**
```
Transit Saturn square Natal Sun, orb 2deg (max 8deg), applying:
P_i = 8 * (1 - 2/8) * 1.3 * 1.0 * 1.2 = 8 * 0.75 * 1.3 * 1.2 = 9.36
```

#### Q_i: Quality Factor

**Fixed Values:**
| Aspect | Quality | Meaning |
|--------|---------|---------|
| Trine | +1.0 | Flow, ease, natural expression |
| Sextile | +1.0 | Opportunity, requires initiative |
| Square | -1.0 | Friction, growth through challenge |
| Opposition | -1.0 | Tension, awareness through polarity |

**Dynamic Conjunction Values:**
| Planet Combination | Quality | Example |
|-------------------|---------|---------|
| Double benefic | +0.8 | Venus conjunct Jupiter |
| Double malefic | -0.8 | Mars conjunct Saturn |
| Benefic + Malefic | +0.2 | Venus conjunct Saturn |
| Transformational | -0.3 | Any with Uranus/Neptune/Pluto |
| Default | 0.0 | Luminaries, Mercury |

**Benefic planets:** Venus, Jupiter
**Malefic planets:** Mars, Saturn
**Transformational planets:** Uranus, Neptune, Pluto

### Harmonic Boost (Post-Processing)

Applied after raw DTI/HQS calculation, before normalization:

```python
for each contribution:
    if transit_planet in BENEFIC and quality > 0:
        multiplier = 2.0  # Enhance positive
    elif transit_planet in MALEFIC and quality < 0:
        multiplier = 0.5  # Soften negative
    else:
        multiplier = 1.0

    boosted_hqs += hqs_contribution * multiplier
```

### Normalization

Raw scores are converted to 0-100 using percentile-based normalization:

```python
def interpolate_percentile(value, percentiles):
    # Linear mapping from p01-p99 range to 0-100
    p01 = percentiles["p01"]
    p99 = percentiles["p99"]

    score = ((value - p01) / (p99 - p01)) * 100
    return clamp(score, 0, 100)
```

**Intensity:** Direct percentile mapping of DTI
**Harmony:** Percentile mapping of HQS (HQS=0 typically maps near 50)

### Unified Score

Combines intensity and harmony using harmonic mean:

```python
unified_score = 2 * intensity * harmony / (intensity + harmony)
```

The harmonic mean ensures both metrics must be reasonably high for a high unified score.

### Trend Calculation

Compares today vs yesterday:

| Delta | Change Rate |
|-------|-------------|
| < 2 | stable |
| 2-5.5 | slow |
| 5.5-10.5 | moderate |
| > 10.5 | rapid |

**Direction:**
- Harmony: positive delta = "improving", negative = "worsening"
- Intensity: positive delta = "increasing", negative = "decreasing"

---

## Calibration System

### Purpose

Converts raw DTI/HQS scores (which vary wildly) into meaningful 0-100 percentiles.

### Empirical Calibration Process

1. **Sample:** 1,000 diverse natal charts (varied birth dates, locations, times)
2. **Date Range:** 2020-01-01 to 2024-12-31 (1,827 days)
3. **Calculations:** 1,000 charts * 1,827 days * 17 meters = ~31M data points
4. **Output:** Percentile distribution (p01-p99) for each meter's DTI and HQS

### Calibration Data Structure

```json
{
  "version": "4.0",
  "meters": {
    "mental_clarity": {
      "dti_percentiles": {
        "p01": 0.0,
        "p50": 450.5,
        "p99": 2100.3
      },
      "hqs_percentiles": {
        "p01": -800.2,
        "p50": -30.5,
        "p99": 600.1
      }
    }
  }
}
```

### Critical Rule

**NEVER use theoretical constants for normalization.** The values `DTI_MAX_ESTIMATE`, `HQS_MAX_POSITIVE_ESTIMATE`, `HQS_MAX_NEGATIVE_ESTIMATE` in `constants.py` are placeholders only. Always use empirical calibration data.

### Re-Calibration Required When

- Meter filter configurations change
- Aspect orb settings change
- Transit power formula changes
- Quality factor values change

---

## API Reference

### Main Entry Points

```python
from astrometers.meters import get_meters, get_meter

# Calculate all 17 meters
all_readings = get_meters(natal_chart, transit_chart)

# Access individual meter
print(all_readings.love.intensity)      # 75.3
print(all_readings.love.harmony)        # 62.1
print(all_readings.love.unified_score)  # 68.2
print(all_readings.love.state_label)    # "Flowing love"

# Calculate single meter
love = get_meter("love", natal_chart, transit_chart)
```

### Data Models

```python
class MeterReading:
    meter_name: str
    date: datetime
    group: MeterGroupV2

    # Scores (all 0-100)
    intensity: float
    harmony: float
    unified_score: float

    # Labels
    unified_quality: QualityLabel  # harmonious/challenging/mixed/quiet
    state_label: str               # "Crystal clear", "Flowing love", etc.

    # Details
    interpretation: str
    advice: List[str]
    top_aspects: List[AspectContribution]
    raw_scores: {"dti": float, "hqs": float}
    trend: Optional[MeterTrends]

class AllMetersReading:
    # Overall
    overall_intensity: MeterReading
    overall_harmony: MeterReading
    overall_unified_quality: QualityLabel
    aspect_count: int
    key_aspects: List[AspectContribution]

    # Individual meters (17 total)
    mental_clarity: MeterReading
    focus: MeterReading
    communication: MeterReading
    # ... etc
```

### Meter Configuration (JSON)

Each meter is configured in `functions/astrometers/labels/{meter_name}.json`:

```json
{
  "configuration": {
    "natal_planets": ["venus", "moon"],
    "natal_houses": [7],
    "retrograde_modifiers": {
      "venus": 0.7
    }
  },
  "experience_labels": {
    "combined": {
      "quiet": {
        "challenging": "Protecting heart",
        "mixed": "Reserved feelings",
        "harmonious": "Peaceful connection"
      }
    }
  }
}
```

**Filter Logic:** `(natal_planet in config.natal_planets) OR (planet_house in config.natal_houses)`

---

## Development Commands

### Calibration

```bash
# Re-run calibration (required when meter filters change)
uv run python functions/astrometers/calibration/calculate_historical_v2.py
# ~5-10 minutes, updates calibration_constants.json

# Verify distribution quality
uv run python functions/astrometers/calibration/verify_percentile.py
# ~30 seconds, checks P50/P90/P99 accuracy
```

### Testing

```bash
# Run all tests
pytest

# Test meter overlap (meters should be distinct)
uv run python functions/astrometers/test_charts_stats_v2.py
# Target: all overlaps < 6%
```

### Inspection

```bash
# View meter configurations
uv run python functions/astrometers/show_meters.py

# View all state labels
uv run python functions/astrometers/show_all_labels.py

# Validate label word counts (max 2 words)
uv run python functions/astrometers/test_label_word_counts.py
```

---

## File Reference

| File | Purpose |
|------|---------|
| `astrometers/core.py` | DTI/HQS calculation engine |
| `astrometers/meters.py` | Meter calculation and configuration loading |
| `astrometers/meter_groups.py` | Group aggregation functions |
| `astrometers/hierarchy.py` | Meter/Group enums and mappings |
| `astrometers/weightage.py` | W_i calculation |
| `astrometers/transit_power.py` | P_i calculation |
| `astrometers/quality.py` | Q_i calculation and harmonic boost |
| `astrometers/dignity.py` | Essential dignity calculations |
| `astrometers/normalization.py` | Percentile-based normalization |
| `astrometers/constants.py` | All constant values |
| `astrometers/labels/*.json` | Meter configurations and state labels |
| `astrometers/calibration/calibration_constants.json` | Empirical percentile data |

---

## Calculation Flow Summary

```
1. Get natal chart and transit chart
2. Find all natal-transit aspects within orb
3. For each meter:
   a. Filter aspects by meter configuration (natal planets/houses)
   b. Calculate W_i for each aspect's natal planet
   c. Calculate P_i for each aspect's transit
   d. Calculate Q_i for each aspect type
   e. Sum DTI = Sum(W_i * P_i)
   f. Sum HQS = Sum(W_i * P_i * Q_i)
   g. Apply harmonic boost to HQS
   h. Normalize DTI -> Intensity (0-100)
   i. Normalize HQS -> Harmony (0-100)
   j. Calculate unified_score = harmonic_mean(intensity, harmony)
   k. Look up state_label from 5x3 matrix
4. Aggregate group scores (simple average of member meters)
5. Calculate overall (weighted average favoring active/changing meters)
6. Calculate trends vs yesterday
```

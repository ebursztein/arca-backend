# Astrometers System Documentation

**Last Updated:** November 2025
**Version:** 3.0 (per-meter calibration with empirical backtesting)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [The 23 Meters](#the-23-meters)
3. [Core Calculation Algorithms](#core-calculation-algorithms)
4. [Normalization and Calibration](#normalization-and-calibration)
5. [Backtesting and Overlap Analysis](#backtesting-and-overlap-analysis)
6. [File-by-File Breakdown](#file-by-file-breakdown)
7. [Integration Guide](#integration-guide)

---

## System Overview

The **Astrometers System** converts astrological transits into quantified, actionable metrics for daily horoscope generation. It answers two fundamental questions:

1. **"How much is happening?"** → **Intensity** (0-100 scale)
2. **"What type of intensity?"** → **Harmony** (0-100 scale, where 50 = neutral)

### Key Design Principles

- **Type-safe**: All planetary/sign/aspect enums use Pydantic validation
- **Empirically calibrated**: Normalization constants derived from 2,500+ diverse birth charts over 855,000+ daily transitions
- **Explainable**: Every score includes aspect-by-aspect breakdown (W_i, P_i, Q_i contributions)
- **Trend-aware**: Automatic calculation of daily changes with quantile-based thresholds
- **Distinct meters**: Each meter tracks different planets/houses to avoid overlap
- **LLM-ready**: JSON labels provide contextual interpretation for language model generation

### Core Workflow

```
Transit Aspects → DTI/HQS Calculation → Normalization → 23 Meters → Trend Analysis → LLM Summary
```

1. **Input**: Natal chart + Transit chart + Date
2. **Find Aspects**: Calculate all natal-transit aspects within orb (8° default)
3. **Calculate DTI/HQS**: For each meter, filter relevant aspects and compute:
   - DTI (Dual Transit Influence) = Σ(W_i × P_i)
   - HQS (Harmonic Quality Score) = Σ(W_i × P_i × Q_i)
4. **Normalize**: Convert raw scores to 0-100 scales using empirical percentiles
5. **Trends**: Compare with yesterday's scores to determine direction/pace
6. **Output**: 23 individual meters + 5 super-group aggregates + trend data

---

## The 23 Meters

### OVERVIEW (2 meters)

**`overall_intensity`**
- Measures: Total astrological activity
- Formula: All transit aspects (no filtering)
- Use case: High-level "how busy is my chart?" gauge

**`overall_harmony`**
- Measures: Net supportive vs challenging quality
- Scale: 0-100 where 50 = neutral, <30 = challenging, >70 = harmonious

### MIND (3 meters)

**`mental_clarity`**
- Planets: Mercury (natal), 3rd house
- Transit filter: Fast-moving only (Mercury/Venus/Mars)
- Rationale: Daily thinking speed/focus vs breakthrough insights
- Modifier: Mercury retrograde (×0.6 to harmony)

**`decision_quality`**
- Planets: Jupiter (wisdom), Saturn (discernment), Neptune (intuition)
- Rationale: Strategic judgment, not thinking speed

**`communication_flow`**
- Planets: Mercury (words), Venus (diplomacy), Mars (directness)

### EMOTIONS (3 meters)

**`emotional_intensity`**
- Planets: Moon, Venus, Pluto
- Note: Neptune removed (spiritual, not emotional)

**`relationship_harmony`**
- Planets: Venus (natal), 7th house
- Modifier: Venus retrograde (×0.7 to harmony)

**`emotional_resilience`**
- Planets: Moon, Saturn, 4th house (foundation)

### BODY (3 meters)

**`physical_energy`**
- Planets: Sun, Mars
- Modifier: Mars retrograde (×0.65 to harmony)

**`conflict_risk`**
- Planets: Mars/Pluto natal, Mars/Pluto/Saturn transits
- Aspect filter: OPPOSITIONS ONLY
- Rationale: External confrontations

**`motivation_drive`**
- Planets: Mars, Jupiter
- Modifier: Mars retrograde (×0.65 to harmony)

### CAREER (2 meters)

**`career_ambition`**
- Houses: 10th house
- Transit filter: Saturn/Mars/Sun ONLY

**`opportunity_window`**
- Planets: Jupiter
- Modifier: Jupiter retrograde (×0.7 to harmony)

### EVOLUTION (3 meters)

**`challenge_intensity`**
- Planets: Saturn/Mars natal, Saturn/Uranus/Pluto transits
- Aspect filter: SQUARES ONLY
- Rationale: Internal friction requiring action

**`transformation_pressure`**
- Planets: Pluto, Uranus, Neptune

**`innovation_breakthrough`**
- Planets: Uranus/Mercury natal
- Transit filter: Uranus ONLY

### ELEMENTS (4 meters)

**`fire_energy`** - Sun, Mars, Jupiter transits
**`earth_energy`** - Venus, Saturn transits
**`air_energy`** - Mercury, Uranus transits
**`water_energy`** - Moon, Pluto, Neptune transits

All use element distribution (70% natal + 30% current transits) for context.

### SPIRITUAL (2 meters)

**`intuition_spirituality`**
- Planets: Neptune, Moon
- Houses: 12th house

**`karmic_lessons`**
- Planets: Saturn, North Node
- Houses: 12th house

### COLLECTIVE (1 meter)

**`social_collective`**
- Planets: Uranus, Neptune, Pluto
- Houses: 11th house

---

## Core Calculation Algorithms

### DTI (Dual Transit Influence)

**Formula**: `DTI = Σ(W_i × P_i)`

Measures the total magnitude of astrological activity.

### HQS (Harmonic Quality Score)

**Formula**: `HQS = Σ(W_i × P_i × Q_i)`

Measures supportive vs challenging nature.

### W_i: Weightage Factor

```python
W_i = (Planet_Base + Dignity + Ruler_Bonus) × House_Mult × Sensitivity
```

**Components**:
- Planet_Base: 10 (Sun/Moon), 8 (Mercury/Venus/Mars), 5 (Jupiter/Saturn), 3 (Uranus/Neptune/Pluto)
- Dignity: +5 (domicile), +3 (exaltation), -3 (detriment), -5 (fall)
- Ruler_Bonus: +3 if planet rules ascendant
- House_Mult: 3× (angular: 1,4,7,10), 2× (succedent: 2,5,8,11), 1× (cadent: 3,6,9,12)

**Example**: Sun in Leo (domicile) in 10th house (angular)
```
W_i = (10 + 5 + 0) × 3 × 1.0 = 45
```

### P_i: Transit Power

```python
P_i = Aspect_Base × Orb_Factor × Direction_Mod × Station_Mod × Transit_Weight
```

**Components**:
- Aspect_Base: 10 (conjunction), 8 (opposition/square), 6 (trine/sextile)
- Orb_Factor: `1 - (orb_deviation / max_orb)` (tighter = stronger)
- Direction_Mod: 1.3× (applying), 0.7× (separating)
- Station_Mod: 1.5× if within 5 days of retrograde station
- Transit_Weight: Moon: 1.8×, Saturn: 1.2×, etc.

**Example**: Transit Saturn square Natal Sun (2.25° orb, applying)
```
P_i = 8 × 0.72 × 1.3 × 1.0 × 1.2 = 8.98
```

### Q_i: Quality Factor

```python
Q_i = Base_Quality × Planet_Modifier
```

- Trine/Sextile: +1.0
- Square/Opposition: -1.0
- Conjunction: 0 (neutral)
- Modifiers: Jupiter/Venus: +0.2, Mars/Saturn/Pluto: -0.2 (capped at ±1.0)

---

## Normalization and Calibration

Raw DTI/HQS scores are normalized to 0-100 scales using **empirical percentiles**.

### The Calibration Process

#### Step 1: Generate Sample Charts
**Script**: `calibration/generate_charts.py`

```bash
uv run python -m functions.astrometers.calibration.generate_charts --count 2500
```

Generates 2,500 diverse birth charts:
- Birth years: 1950-2020 (70-year span)
- Locations: 32 global cities across all continents
- Random times and dates
- Output: `natal_charts.json` (~14 MB)

**Why diversity matters**: Different chart configurations produce vastly different DTI/HQS ranges. A chart with many angular planets will score higher than one with cadent planets. We need a representative sample.

#### Step 2: Calculate Historical Scores
**Script**: `calibration/calculate_historical.py`

```bash
uv run python -m functions.astrometers.calibration.calculate_historical
```

For each of the 2,500 charts:
- Calculate meters for 20-30 years of daily transits
- ~9,125 days per chart = 22.8 million data points
- Store DTI/HQS for all 23 meters
- Output: `historical_scores.parquet` or `calibration_constants.json`

**What this does**: Creates a statistical distribution of what "typical" scores look like across diverse charts over many years. This answers: "What's a normal Monday for someone with Sun in Leo in the 10th? What's an extreme day?"

#### Step 3: Calculate Percentiles
**Script**: `calibration/analyze_distributions.py`

Calculates 1st, 5th, 25th, 50th, 75th, 95th, 99th percentiles for:
- DTI (intensity)
- HQS positive (harmonious)
- HQS negative (challenging)

**Per-meter calibration**: Each of the 23 meters has its own distribution because they track different numbers of planets/aspects:
- `overall_intensity` (all aspects): DTI can reach 5,000+
- `mental_clarity` (Mercury only): DTI rarely exceeds 300

Output: `calibration_constants.json` with per-meter p99 values

### Normalization Functions

#### Intensity Normalization

```python
# Uses per-meter 99th percentile as max
dti_max = calibration["meters"][meter_name]["dti_percentiles"]["p99"]

# Linear scaling within expected range (0-99th percentile)
if dti <= dti_max:
    intensity = (dti / dti_max) × 100

# Logarithmic compression for outliers (>99th percentile)
else:
    excess = dti - dti_max
    compressed = 10 × log₁₀(1 + excess / dti_max)
    intensity = min(100, 100 + compressed)
```

**Result**: A score of 75 means "75th percentile" (top 25% of days across all charts/times)

#### Harmony Normalization

```python
# HQS=0 always maps to 50 (neutral)

if hqs >= 0:
    # Positive: harmonious (50-100)
    hqs_max_pos = calibration["meters"][meter_name]["hqs_percentiles"]["p99"]
    normalized = (hqs / hqs_max_pos) × 50
    harmony = 50 + normalized
else:
    # Negative: challenging (0-50)
    hqs_max_neg = abs(calibration["meters"][meter_name]["hqs_percentiles"]["p01"])
    normalized = (abs(hqs) / hqs_max_neg) × 50
    harmony = 50 - normalized
```

**Result**:
- Harmony = 85 → "Top 15% harmonious days"
- Harmony = 25 → "Bottom 25% challenging days"
- Harmony = 50 → "Neutral (no net quality)"

---

## Backtesting and Overlap Analysis

### Why Overlap Testing?

**Problem**: If two meters (e.g., `mental_clarity` and `decision_quality`) track the exact same aspects, they'll always show identical readings. This provides no additional information to users.

**Solution**: Each meter must filter aspects differently (different planets, houses, or aspect types) to ensure distinct signals.

### The Overlap Test
**Script**: `test_charts_stats.py`

```bash
# Test 1,000 random charts for meter overlaps
uv run python -m functions.astrometers.test_charts_stats
```

**Process**:

1. **Generate 1,000 random birth charts**
   - Diverse locations, dates, times
   - Same distribution as calibration sample

2. **For each chart**:
   - Calculate all 23 meters using a test transit date (2025-10-26)
   - Extract `top_aspects` from each meter (list of contributing aspects)
   - Build aspect sets: `{(natal_planet, transit_planet, aspect_type), ...}`

3. **Compare aspect sets pairwise**:
   ```python
   for meter1 in meters:
       for meter2 in meters:
           if meter1.top_aspects == meter2.top_aspects:
               # OVERLAP DETECTED
               print(f"❌ {meter1.name} == {meter2.name}")
   ```

4. **Aggregate results**:
   - Count how many charts show each overlap pair
   - Calculate overlap frequency as percentage
   - Flag any consistent overlaps (>5% of charts)

**Success criteria**: 0 unexpected overlaps across 1,000 diverse charts

**Example output**:
```
✅ SUCCESS: No unexpected overlaps in any of the 1,000 charts!
   All meters are robustly distinct across diverse natal configurations
```

### Trend Threshold Analysis
**Script**: `test_charts_stats.py trends`

```bash
# Analyze 855,000+ daily transitions to determine trend thresholds
uv run python -m functions.astrometers.test_charts_stats trends
```

**Purpose**: Determine what constitutes a "significant" change in meter scores.

**Process**:

1. **Generate 2,500 random birth charts**

2. **For each chart**:
   - Calculate meters for 15 consecutive days
   - Store yesterday's scores and today's scores
   - Compute daily deltas: `today.harmony - yesterday.harmony`

3. **Collect all deltas**:
   - 2,500 charts × 15 days × 23 meters = 862,500 transitions
   - Separate collections for harmony, intensity, unified_score

4. **Calculate quantiles**:
   ```python
   50th percentile = median change (half of days change more)
   75th percentile = noticeable change
   90th percentile = significant change
   95th+ percentile = dramatic change
   ```

5. **Derive thresholds**:
   ```python
   HARMONY_THRESHOLDS = {
       'stable': 2.0,     # < 2 points (50% of changes)
       'slow': 5.5,       # 2-5.5 points (50th-75th)
       'moderate': 10.5   # 5.5-10.5 points (75th-90th)
       # rapid: > 10.5 points (top 10%)
   }
   ```

**Why this matters**: Users need context for trends. "Your mental clarity improved by 3 points" means nothing without knowing if that's typical (happens daily) or significant (top 20% of changes).

**Example output**:
```
HARMONY deltas:
  50th percentile: 2.1
  75th percentile: 5.7
  90th percentile: 10.8

RECOMMENDED THRESHOLDS:
  stable   : < 2.1 points  (50% of daily changes)
  slow     : 2.1 - 5.7 points
  moderate : 5.7 - 10.8 points
  rapid    : > 10.8 points  (top 10% of changes)
```

### How Backtesting Informs The System

**Calibration** (Step 2 above):
- Defines what scores are "typical" vs "extreme"
- Sets normalization constants (99th percentile max)
- Ensures meters scale consistently across different chart types

**Overlap testing**:
- Validates that each meter provides unique information
- Catches design errors (e.g., two meters accidentally using same filter)
- Ensures 23 distinct readings, not 10 unique + 13 duplicates

**Trend analysis**:
- Calibrates change detection thresholds
- Provides semantic meaning to delta values
- Powers the TrendData model (STABLE, SLOW, MODERATE, RAPID labels)

---

## File-by-File Breakdown

### Core Directory: `functions/astrometers/`

```
astrometers/
├── __init__.py                 # Package exports
├── core.py                     # DTI/HQS calculation engine
├── weightage.py                # W_i calculation
├── transit_power.py            # P_i calculation
├── quality.py                  # Q_i calculation
├── dignity.py                  # Planetary dignities
├── normalization.py            # Raw→0-100 conversion
├── constants.py                # All system constants
├── meters.py                   # 23 meter functions (2,234 lines)
├── meter_groups.py             # 5-group aggregation
├── hierarchy.py                # Taxonomy definitions
├── summary.py                  # LLM markdown tables
├── show_meters.py              # Debug pretty-printer
├── generate_meter_labels.py    # Auto-generate JSON labels
├── generate_meter_group_labels.py
├── test_charts_stats.py        # Overlap/trend analysis
├── test_meter_validation.py    # Unit tests
├── calibration/                # Backtesting scripts
│   ├── generate_charts.py
│   ├── calculate_historical.py
│   ├── analyze_distributions.py
│   ├── natal_charts.json       # 2,500 sample charts (14 MB)
│   └── calibration_constants.json
├── labels/                     # JSON labels for meters
│   ├── mental_clarity.json
│   ├── physical_energy.json
│   └── ... (23 meter labels)
└── tests/
    ├── test_meters.py
    └── test_meter_groups_agg.py
```

---

### Core Algorithm Files

#### `core.py` (252 lines)
**Purpose**: DTI and HQS calculation engine

**Key functions**:
- `calculate_aspect_contribution(aspect)` → `AspectContribution`
  - Calculates W_i, P_i, Q_i for a single transit aspect
  - Returns DTI contribution (W_i × P_i) and HQS contribution (W_i × P_i × Q_i)
- `calculate_astrometers(aspects)` → `AstrometerScore`
  - Main entry point: sums all aspect contributions
  - Returns total DTI, HQS, and detailed breakdown

**Data models**:
- `TransitAspect` - Input: natal planet, transit planet, aspect type, orb
- `AspectContribution` - Output: W_i, P_i, Q_i, DTI, HQS per aspect
- `AstrometerScore` - Complete score with all contributions

**Example**:
```python
aspect = TransitAspect(
    natal_planet=Planet.SUN,
    natal_sign=ZodiacSign.LEO,
    natal_house=10,
    transit_planet=Planet.SATURN,
    aspect_type=AspectType.SQUARE,
    orb_deviation=2.25,
    max_orb=8.0
)

contribution = calculate_aspect_contribution(aspect)
# contribution.weightage = 45 (Sun in Leo in 10th)
# contribution.transit_power = 8.98 (tight applying square)
# contribution.quality_factor = -1.0 (square)
# contribution.dti_contribution = 404.1
# contribution.hqs_contribution = -404.1
```

#### `weightage.py` (155 lines)
**Purpose**: Calculate W_i (natal planet importance)

**Formula**: `(Planet_Base + Dignity + Ruler_Bonus) × House_Mult × Sensitivity`

**Key constants**:
```python
PLANET_BASE_WEIGHTS = {
    Planet.SUN: 10, Planet.MOON: 10,
    Planet.MERCURY: 8, Planet.VENUS: 8, Planet.MARS: 8,
    Planet.JUPITER: 5, Planet.SATURN: 5,
    Planet.URANUS: 3, Planet.NEPTUNE: 3, Planet.PLUTO: 3
}

DIGNITY_BONUS = {
    'domicile': 5, 'exaltation': 3, 'detriment': -3, 'fall': -5
}

HOUSE_MULTIPLIERS = {
    'angular': 3,    # Houses 1, 4, 7, 10
    'succedent': 2,  # Houses 2, 5, 8, 11
    'cadent': 1      # Houses 3, 6, 9, 12
}
```

#### `transit_power.py` (385 lines)
**Purpose**: Calculate P_i (transit aspect strength)

**Formula**: `Aspect_Base × Orb_Factor × Direction_Mod × Station_Mod × Transit_Weight`

**Key functions**:
- `calculate_transit_power_complete()` - Full P_i calculation
- `calculate_orb_factor()` - Tighter orb = stronger (linear decay to 0 at max orb)
- `calculate_direction_modifier()` - 1.3× applying, 0.7× separating
- `calculate_station_modifier()` - 1.5× if within 5 days of retrograde station
- `get_transit_weight()` - Moon: 1.8×, Saturn: 1.2×, based on planetary speed

**Planetary motion tracking**: Uses actual daily motion in degrees:
```python
PLANET_DAILY_MOTION = {
    Planet.MOON: 13.0,     # Fast
    Planet.SUN: 1.0,
    Planet.MERCURY: 1.5,
    Planet.MARS: 0.5,
    Planet.SATURN: 0.03,   # Slow
    Planet.PLUTO: 0.004    # Very slow
}
```

Used to calculate tomorrow's expected orb deviation for direction modifier.

#### `quality.py` (154 lines)
**Purpose**: Calculate Q_i (quality factor)

**Formula**: `Base_Quality × Planet_Modifier`

```python
BASE_QUALITY_FACTORS = {
    AspectType.TRINE: 1.0,
    AspectType.SEXTILE: 1.0,
    AspectType.CONJUNCTION: 0.0,  # Neutral by default
    AspectType.SQUARE: -1.0,
    AspectType.OPPOSITION: -1.0
}

PLANET_MODIFIERS = {
    Planet.JUPITER: 0.2,  # Adds positivity
    Planet.VENUS: 0.2,
    Planet.MARS: -0.2,    # Adds negativity
    Planet.SATURN: -0.2,
    Planet.PLUTO: -0.2
}
```

**Special cases**:
- Conjunction quality varies by planets involved
- Final Q_i capped at ±1.0

#### `dignity.py` (178 lines)
**Purpose**: Classical planetary dignities

**Tables**:
```python
DOMICILES = {
    Planet.SUN: ZodiacSign.LEO,
    Planet.MOON: ZodiacSign.CANCER,
    # ... etc
}

EXALTATIONS = {
    Planet.SUN: ZodiacSign.ARIES,
    Planet.MOON: ZodiacSign.TAURUS,
    # ... etc
}
```

**Functions**:
- `get_dignity_score()` - Returns +5, +3, -3, -5, or 0
- `is_in_domicile()`, `is_in_exaltation()`, etc.

---

### Normalization and Calibration Files

#### `normalization.py` (514 lines)
**Purpose**: Convert raw DTI/HQS to 0-100 scales

**Key functions**:
- `normalize_intensity(dti, meter_name)` → 0-100 (percentile-based)
- `normalize_harmony(hqs, meter_name)` → 0-100 (50 = neutral)
- `normalize_with_soft_ceiling()` - Handles outliers with log compression
- `load_calibration_constants()` - Load empirical percentiles from JSON

**Soft ceiling math**:
```python
if raw_score <= max_value:
    # Linear scaling (0-99th percentile)
    result = (raw_score / max_value) × target_scale
else:
    # Log compression for outliers
    excess = raw_score - max_value
    compressed = 10 × log₁₀(1 + excess / max_value)
    result = min(target_scale, target_scale + compressed)
```

This allows rare extreme days to reach ~105 while keeping most scores linear.

#### `constants.py` (147 lines)
**Purpose**: All system constants

**Key constants**:
```python
# Theoretical max estimates (fallback if no calibration)
DTI_MAX_ESTIMATE = 3000.0
HQS_MAX_POSITIVE_ESTIMATE = 1500.0
HQS_MAX_NEGATIVE_ESTIMATE = -2000.0

# Scale
METER_SCALE = 100
HARMONY_NEUTRAL = 50

# Interpretation thresholds
INTENSITY_QUIET_THRESHOLD = 25
INTENSITY_MILD_THRESHOLD = 40
INTENSITY_MODERATE_THRESHOLD = 60
INTENSITY_HIGH_THRESHOLD = 75

HARMONY_CHALLENGING_THRESHOLD = 30
HARMONY_HARMONIOUS_THRESHOLD = 70

# Trend thresholds (from backtesting)
HARMONY_THRESHOLDS = {'stable': 2.0, 'slow': 5.5, 'moderate': 10.5}
INTENSITY_THRESHOLDS = {'stable': 2.0, 'slow': 5.0, 'moderate': 9.5}
UNIFIED_THRESHOLDS = {'stable': 0.5, 'slow': 2.5, 'moderate': 5.5}
```

#### `calibration/generate_charts.py` (178 lines)
**Purpose**: Generate diverse natal chart sample

```bash
uv run python -m functions.astrometers.calibration.generate_charts --count 2500
```

**What it does**:
1. Randomly selects birth date (1950-2020)
2. Randomly selects birth time (00:00-23:59)
3. Randomly selects location from 32 global cities
4. Calculates natal chart using `compute_birth_chart()`
5. Saves to `natal_charts.json`

**Output format**:
```json
{
  "chart_id": "chart_00001",
  "birth_date": "1987-03-15",
  "birth_time": "14:23",
  "location": "Tokyo",
  "lat": 35.6762,
  "lon": 139.6503,
  "sun_sign": "pisces",
  "ascendant_sign": "cancer",
  "natal_chart": { /* full chart data */ }
}
```

#### `calibration/calculate_historical.py` (~200 lines, estimated)
**Purpose**: Calculate meters for 20-30 years per chart

**Process**:
1. Load `natal_charts.json`
2. For each chart:
   - Loop through dates (e.g., 2000-01-01 to 2025-12-31)
   - Calculate transit chart for each date
   - Calculate all 23 meters
   - Store raw DTI/HQS values
3. Calculate percentiles (1st, 5th, 25th, 50th, 75th, 95th, 99th)
4. Save to `calibration_constants.json`

**Output format**:
```json
{
  "version": "3.0",
  "generated": "2025-10-26T12:00:00Z",
  "sample_size": 2500,
  "days_per_chart": 9125,
  "total_data_points": 22812500,
  "meters": {
    "mental_clarity": {
      "dti_percentiles": {
        "p01": 12.3,
        "p50": 85.2,
        "p99": 287.4
      },
      "hqs_percentiles": {
        "p01": -142.1,
        "p50": 2.3,
        "p99": 154.8
      }
    }
    // ... 22 more meters
  }
}
```

#### `test_charts_stats.py` (429 lines)
**Purpose**: Stress test meters across diverse charts

**Mode 1: Overlap testing**
```bash
uv run python -m functions.astrometers.test_charts_stats
```

Functions:
- `test_many_charts()` - Run overlap analysis on 1,000 random charts
- `analyze_chart_overlaps(chart)` - Compare aspect sets across meters
- `generate_random_chart()` - Create random birth chart for testing

Output:
```
STRESS TEST: 1,000 RANDOM BIRTH CHARTS
Processed 1000/1000 charts...

RESULTS SUMMARY
Total charts tested: 1000
Successful analyses: 1000
Charts with UNEXPECTED identical pairs: 0

✅ SUCCESS: No unexpected overlaps in any of the 1,000 charts!
```

**Mode 2: Trend analysis**
```bash
uv run python -m functions.astrometers.test_charts_stats trends
```

Functions:
- `analyze_daily_change_distribution()` - Analyze 2,500 charts × 15 days
- Collects 862,500 daily transitions
- Calculates quantiles for harmony, intensity, unified_score deltas
- Outputs recommended thresholds

Output:
```
DAILY CHANGE DISTRIBUTION ANALYSIS
Analyzing 2,500 charts × 15 days = 37,500 data points

QUANTILE ANALYSIS (Absolute Changes)
HARMONY deltas:
  50th percentile:  2.03
  75th percentile:  5.52
  90th percentile: 10.48

RECOMMENDED THRESHOLDS
Based on HARMONY changes:
  stable   : < 2.0 points  (50% of daily changes)
  slow     : 2.0 - 5.5 points  (50th-75th percentile)
  moderate : 5.5 - 10.5 points  (75th-90th percentile)
  rapid    : > 10.5 points  (top 10% of changes)
```

---

### Meter Implementation Files

#### `meters.py` (2,234 lines)
**Purpose**: All 23 meter calculation functions + super-group aggregation

**Structure**:
- Lines 1-513: Imports, models, label loading
- Lines 514-662: Helper functions (filtering, retrograde modifiers)
- Lines 665-1520: 23 individual meter functions
- Lines 1522-1660: `AllMetersReading` model and key aspects extraction
- Lines 1662-2004: Super-group aggregation functions
- Lines 2006-2234: Master `get_meters()` function with trend calculation

**Each meter function follows this pattern**:
```python
def calculate_mental_clarity_meter(
    all_aspects: List[TransitAspect],
    date: datetime,
    transit_chart: dict
) -> MeterReading:
    # 1. Filter aspects to relevant planets/houses
    mercury_aspects = filter_aspects_by_natal_planet(all_aspects, [Planet.MERCURY])
    third_house = filter_aspects_by_natal_house(all_aspects, [3])
    combined = mercury_aspects + third_house

    # 2. Filter by transit planets (fast-moving only)
    fast_transits = [Planet.MERCURY, Planet.VENUS, Planet.MARS]
    filtered = filter_aspects_by_transit_planet(combined, fast_transits)

    # 3. Calculate score
    reading = calculate_meter_score(filtered, "mental_clarity", date, MeterGroup.MIND)

    # 4. Apply retrograde modifier
    apply_retrograde_modifier(reading, transit_chart, Planet.MERCURY, 0.6)

    # 5. Apply JSON labels
    apply_labels_to_reading(reading, "mental_clarity")

    return reading
```

**Key models**:
```python
class MeterReading(BaseModel):
    meter_name: str
    date: datetime
    group: MeterGroup

    # Unified display (primary)
    unified_score: float  # 0-100 (equals intensity)
    unified_quality: QualityLabel  # quiet, peaceful, harmonious, mixed, challenging

    # Detailed breakdown
    intensity: float  # 0-100
    harmony: float  # 0-100
    state_label: str  # From JSON (e.g., "Clear Insight")
    interpretation: str
    advice: List[str]
    top_aspects: List[AspectContribution]
    raw_scores: Dict[str, float]  # DTI, HQS

    # Trend (optional, calculated by get_meters)
    trend: Optional[TrendData] = None

class TrendData(BaseModel):
    """Complete trend analysis comparing today vs yesterday."""
    harmony: MetricTrend
    intensity: MetricTrend
    unified_score: MetricTrend

class MetricTrend(BaseModel):
    previous: float  # Yesterday's value
    delta: float  # Change from yesterday
    direction: TrendDirection  # IMPROVING, STABLE, WORSENING, etc.
    change_rate: ChangeRate  # STABLE, SLOW, MODERATE, RAPID
```

**Master function: `get_meters()`**

```python
def get_meters(
    natal_chart: dict,
    transit_chart: dict,
    date: Optional[datetime] = None
) -> AllMetersReading:
    """
    Calculate all 28 meters (23 individual + 5 super-group) with automatic trend analysis.

    This function automatically calculates yesterday's transits and populates trend fields.
    """
    # 1. Calculate today's meters (without trends)
    all_meters = _calculate_meters_no_trends(natal_chart, transit_chart, date)

    # 2. Calculate yesterday's meters for comparison
    yesterday_date = date - timedelta(days=1)
    yesterday_transit_chart, _ = compute_birth_chart(...)
    yesterday_meters = _calculate_meters_no_trends(natal_chart, yesterday_transit_chart, yesterday_date)

    # 3. Populate trend fields for all 28 meters
    for meter_name in meter_names:
        today_meter = getattr(all_meters, meter_name)
        yesterday_meter = getattr(yesterday_meters, meter_name)
        today_meter.trend = today_meter.calculate_trend(yesterday_meter)

    return all_meters
```

#### `meter_groups.py` (333 lines)
**Purpose**: Aggregate 21 meters into 5 life-area groups

**MeterGroupV2 Structure**:
1. **MIND** (3 meters): mental_clarity, decision_quality, communication_flow
2. **EMOTIONS** (3 meters): emotional_intensity, relationship_harmony, emotional_resilience
3. **BODY** (3 meters): physical_energy, conflict_risk, motivation_drive
4. **SPIRIT** (6 meters): intuition_spirituality, karmic_lessons, 4 elements
5. **GROWTH** (6 meters): career, evolution, collective

**Key functions**:
```python
def build_meter_group_data(
    group: MeterGroupV2,
    today_meters: List[MeterReading],
    llm_interpretation: Optional[str],
    yesterday_meters: Optional[List[MeterReading]] = None
) -> Dict:
    """
    Build complete MeterGroupData for a single group.

    Returns:
        {
            "group_name": "mind",
            "display_name": "Mind",
            "scores": {
                "unified_score": 75.3,
                "harmony": 78.0,
                "intensity": 72.7
            },
            "state": {
                "label": "Supportive",  # From JSON labels
                "quality": "supportive"  # Generic enum
            },
            "interpretation": "LLM-generated text or fallback",
            "trend": {
                "unified_score": {...},
                "harmony": {...},
                "intensity": {...}
            },
            "meter_ids": ["mental_clarity", "decision_quality", "communication_flow"]
        }
    """
```

#### `hierarchy.py` (563 lines)
**Purpose**: Single source of truth for taxonomy

**Three-tier structure**:
```
SuperGroup (5) → MeterGroup (9) → Meters (23)
```

**Key mappings**:
```python
# Flat mapping: Meter → (MeterGroup, SuperGroup)
METER_TO_GROUP: Dict[Meter, tuple[MeterGroup, SuperGroup]]

# Reverse mapping
GROUP_TO_SUPER: Dict[MeterGroup, SuperGroup]
GROUP_METERS: Dict[MeterGroup, List[Meter]]
SUPER_GROUPS: Dict[SuperGroup, List[MeterGroup]]

# MeterGroupV2 (5-group UI structure)
METER_TO_GROUP_V2: Dict[Meter, MeterGroupV2]
GROUP_V2_METERS: Dict[MeterGroupV2, List[Meter]]
```

**Validation on import**:
```python
assert validate_hierarchy_complete()  # 23 individual + 5 super-group = 28 total
assert validate_group_v2_complete()   # 21 non-overview meters in MeterGroupV2
```

---

### Label and Summary Files

#### `labels/` directory
**Purpose**: JSON labels for all 23 meters + 5 groups

**Structure per meter** (e.g., `mental_clarity.json`):
```json
{
  "_schema_version": "1.0",
  "_meter": "mental_clarity",
  "metadata": {
    "meter_id": "mental_clarity",
    "display_name": "Mental Clarity",
    "group": "mind",
    "super_group": "inner_world"
  },
  "description": {
    "overview": "This meter tracks your mental sharpness...",
    "detailed": "This meter focuses on how Mercury transits...",
    "keywords": ["Thinking", "Communication", "Focus"]
  },
  "experience_labels": {
    "combined": {
      "quiet": {
        "challenging": "Confused Stillness",
        "mixed": "Quiet Reflection",
        "harmonious": "Calm Clarity"
      },
      "moderate": {
        "challenging": "Moderate Struggle",
        "mixed": "Deliberate Thought",
        "harmonious": "Clear Insight"
      }
      // 5 intensity × 3 harmony = 15 labels
    }
  },
  "advice_templates": {
    "quiet": {
      "challenging": "Pause/Review",
      "harmonious": "Restful Reflection"
    }
    // 15 advice categories
  }
}
```

**Label application**:
```python
# Get contextual state label based on intensity + harmony
state_label = get_state_label_from_json("mental_clarity", intensity=65, harmony=45)
# Returns: "Deliberate Thought"

# Get advice category
advice = get_advice_category_from_json("mental_clarity", 65, 45)
# Returns: "Focused Analysis"
```

#### `summary.py` (572 lines)
**Purpose**: Generate LLM-ready markdown tables

**Key function**: `daily_meters_summary(meters_today)`

Creates 7 ranked tables:
1. **OVERALL SCORE** - 2 meta-meters
2. **MOST ACTIVE** - Top 5 by intensity
3. **MOST CHALLENGING** - Top 5 by lowest harmony (active only, intensity ≥ 20)
4. **TOP FLOWING** - Top 3 high intensity + high harmony
5. **FASTEST CHANGING** - Top 6 biggest intensity deltas
6. **QUIET METERS** - List of meters with intensity < 20
7. **KEY ASPECTS** - Top 5 transits affecting multiple meters

**Table format** (hierarchical headers with merged cells):
```
┌──────┬────────────────────────┬────────────────────┬─────── OVERALL ───────┬───── INTENSITY ─────┬────── HARMONY ──────┐
│ Rank │ Meter                  │ State              │ Val │ Trend          │ Val │ Trend         │ Val │ Trend         │
├──────┼────────────────────────┼────────────────────┼─────┼────────────────┼─────┼───────────────┼─────┼───────────────┤
│  #1  │ physical_energy        │ Sharp Focus        │ 78.5│ +5.2 moderate  │ 78.5│ +5.2 moderate │ 82.3│ +2.1 slow     │
```

**Deduplication**: Tracks `shown_meters` set to avoid showing same meter in multiple tables

**Key aspects extraction**:
```python
def extract_key_aspects(
    all_meters: AllMetersReading,
    top_n: int = 5,
    min_dti_threshold: float = 100.0
) -> List[KeyAspect]:
    """
    Deduplicate aspects across all meters.

    If "Transit Saturn square Natal Sun" appears in 8 different meters,
    show it once with meter_count=8.
    """
```

---

### Utility Files

#### `generate_meter_labels.py` (~200 lines)
**Purpose**: Auto-generate JSON labels using Gemini LLM

```bash
uv run python -m functions.astrometers.generate_meter_labels
```

**Process**:
1. Read meter metadata from `meters.py` (planets, houses, description)
2. Generate prompt for Gemini:
   ```
   Generate experience labels for the "mental_clarity" meter.
   This meter tracks: Mercury, 3rd house, fast transits.

   Create 15 state labels (5 intensity × 3 harmony).
   Format: JSON with intensity_only, harmony_only, combined.
   ```
3. Parse JSON response
4. Save to `labels/mental_clarity.json`

#### `show_meters.py` (~180 lines)
**Purpose**: Pretty-print meter readings for debugging

```bash
uv run python -m functions.astrometers.show_meters
```

Outputs Rich console tables showing:
- All 23 meters with scores
- Top aspects per meter
- Trend data (if available)
- Color-coded by quality (green = harmonious, red = challenging)

---

## Integration Guide

### Basic Usage

```python
from datetime import datetime
from astro import compute_birth_chart
from astrometers import get_meters
from astrometers.summary import daily_meters_summary

# 1. Get user's natal chart
natal_chart, _ = compute_birth_chart(
    birth_date="1990-06-15",
    birth_time="14:30",
    birth_timezone="America/New_York",
    birth_lat=40.7128,
    birth_lon=-74.0060
)

# 2. Get today's transits
transit_chart, _ = compute_birth_chart(
    birth_date="2025-11-03",
    birth_time="12:00"  # Noon for transits
)

# 3. Calculate all meters with automatic trends
meters = get_meters(natal_chart, transit_chart, datetime(2025, 11, 3))

# 4. Access individual meters
print(f"Overall Intensity: {meters.overall_intensity.intensity:.1f}/100")
print(f"Mental Clarity: {meters.mental_clarity.unified_score:.1f}/100")
print(f"State: {meters.mental_clarity.state_label}")

# 5. Check trends
if meters.mental_clarity.trend:
    trend = meters.mental_clarity.trend.harmony
    print(f"Trend: {trend.direction.value} ({trend.change_rate.value})")
    print(f"Change: {trend.delta:+.1f} points")

# 6. Generate LLM summary
summary = daily_meters_summary(meters)
# Use summary in Gemini prompt for personalized horoscope
```

### Access Meter Groups

```python
from astrometers.meter_groups import build_all_meter_groups

# Build 5 life-area groups
groups = build_all_meter_groups(meters)

# Access Mind group
mind = groups['mind']
print(f"Mind score: {mind['scores']['unified_score']:.1f}/100")
print(f"Mind state: {mind['state']['label']}")
print(f"Mind meters: {', '.join(mind['meter_ids'])}")

# Check trend
if mind['trend']:
    print(f"Harmony trend: {mind['trend']['harmony']['direction']} ({mind['trend']['harmony']['change_rate']})")
```

### Debugging: Inspect Top Aspects

```python
# See what's driving a meter
mc = meters.mental_clarity

for aspect in mc.top_aspects[:3]:
    print(f"{aspect.label}")
    print(f"  W_i: {aspect.weightage:.1f}")
    print(f"  P_i: {aspect.transit_power:.1f}")
    print(f"  Q_i: {aspect.quality_factor:.1f}")
    print(f"  DTI: {aspect.dti_contribution:.1f}")
    print(f"  HQS: {aspect.hqs_contribution:.1f}")
```

---

## Key Design Decisions

### Why per-meter calibration?

Different meters track different numbers of planets/houses:
- `overall_intensity` (all aspects): DTI can reach 5,000+
- `mental_clarity` (Mercury only): DTI rarely exceeds 300

**Solution**: Each meter has its own 99th percentile max derived from empirical data.

### Why deduplication in summary tables?

Users don't want the same meter shown 3 times. The summary tracks `shown_meters` and excludes already-shown meters from subsequent tables.

### Why logarithmic compression for outliers?

Extremely rare days (>99th percentile) shouldn't break the 0-100 scale. Log compression allows scores to reach ~105 for true outliers while keeping most scores linear.

### Why separate intensity/harmony scales?

Astrological intensity is multiplicative (10 soft aspects vs 1 hard aspect), but quality is additive (net supportive vs challenging). Separating them provides more nuanced information.

### Why filter by transit planet type?

To prevent meter overlap. Example:
- `mental_clarity`: Fast transits (Mercury/Venus/Mars) = daily thinking
- `innovation_breakthrough`: Uranus transits only = breakthrough moments

This ensures they track different phenomena.

---

## Running the Backtesting Scripts

### Generate Sample Charts

```bash
# Generate 2,500 diverse birth charts
cd /Users/elieb/git/arca-backend
uv run python -m functions.astrometers.calibration.generate_charts --count 2500

# Output: functions/astrometers/calibration/natal_charts.json (14 MB)
```

### Calculate Historical Scores

```bash
# Calculate meters for 20-30 years per chart
uv run python -m functions.astrometers.calibration.calculate_historical

# Output: functions/astrometers/calibration/calibration_constants.json
# Or: functions/astrometers/calibration/historical_scores.parquet
```

### Test for Overlaps

```bash
# Test 1,000 random charts
uv run python -m functions.astrometers.test_charts_stats

# Expected output:
# ✅ SUCCESS: No unexpected overlaps in any of the 1,000 charts!
```

### Analyze Trend Thresholds

```bash
# Analyze 855K daily transitions
uv run python -m functions.astrometers.test_charts_stats trends

# Output: Recommended thresholds for STABLE, SLOW, MODERATE, RAPID
```

---

**End of Documentation**

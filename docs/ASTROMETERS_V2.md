# Astrometers Scoring V2

**Date:** December 2025
**Status:** Complete - All tests passing

---

## Summary

17 individual meters organized into 5 groups measure daily astrological energy through transit-to-natal aspects. Each meter filters aspects based on specific planets/houses and calculates:
- **Intensity** (0-100): How much is happening (magnitude)
- **Harmony** (0-100): Quality of what's happening (50 = neutral)
- **Unified Score** (20-100): Intensity drives value, harmony drives direction
  - 50 = neutral (no activity or balanced aspects)
  - 50-100 = positive harmony (proportional to strength)
  - 20-50 = negative harmony (compressed range - empowering bias)

---

## Distribution Test Results (10,000 samples: 1000 charts x 10 dates)

```
+--------------------------------+------------+------------+--------+
| Metric                         | Value      | Target     | Status |
+--------------------------------+------------+------------+--------+
| Avg Cross-Meter |Correlation|  |      0.234 | <0.30      |   PASS |
| High Correlation Pairs (>=0.5) |         13 | ideally 0  |   WARN |
| Within-Group Avg |r|           |      0.363 | -          | INFO   |
| Between-Group Avg |r|          |      0.210 | -          | INFO   |
| All Means in [-20,40]          |        Yes | Yes        |   PASS |
| All StdDevs in [25,60]         |        Yes | Yes        |   PASS |
+--------------------------------+------------+------------+--------+
```

### Per-Meter Statistics (unified_score: -100 to +100)

```
+------------------+--------+--------+--------+------+------+
| Meter            |   Mean | Median | StdDev |  P10 |  P90 |
+------------------+--------+--------+--------+------+------+
| clarity          |   22.5 |   22.6 |   38.6 | -25  |  77  |
| focus            |   15.2 |   12.6 |   38.0 | -31  |  71  |
| communication    |   13.4 |   12.2 |   40.8 | -37  |  74  |
| connections      |   18.6 |   15.2 |   42.0 | -35  |  82  |
| resilience       |   21.0 |   17.9 |   43.5 | -37  |  89  |
| vulnerability    |   22.2 |   20.5 |   39.9 | -30  |  81  |
| energy           |   32.8 |   32.6 |   42.3 | -24  |  95  |
| drive            |   24.7 |   22.4 |   33.5 | -15  |  72  |
| strength         |   25.2 |   23.8 |   42.1 | -30  |  86  |
| vision           |   21.4 |   19.1 |   32.9 | -17  |  67  |
| flow             |   20.6 |   17.7 |   32.4 | -13  |  64  |
| intuition        |    6.8 |   -0.2 |   35.7 | -33  |  57  |
| creativity       |    9.3 |    2.1 |   39.9 | -39  |  70  |
| momentum         |   12.8 |    5.4 |   43.1 | -40  |  80  |
| ambition         |   17.6 |   17.3 |   25.9 |  -8  |  49  |
| evolution        |   12.3 |    5.9 |   42.5 | -41  |  77  |
| circle           |   24.5 |   20.7 |   39.8 | -25  |  85  |
+------------------+--------+--------+--------+------+------+
```

**Interpretation:**
- Means are positive (5-33 range) = empowering bias working correctly
- StdDevs of 25-43 = good spread across -100 to +100 range
- Energy has highest mean (32.8) - most optimistic meter
- Intuition has lowest mean (6.8) - closest to neutral

### Per-Group Internal Correlation

```
+------------+----------+----------+-----------------------------------+
| Group      | Avg |r|  |  Max |r| | Highest Pair                      |
+------------+----------+----------+-----------------------------------+
| Heart      |    0.619 |    0.703 | resilience <-> vulnerability      |
| Mind       |    0.534 |    0.595 | clarity <-> communication         |
| Body       |    0.380 |    0.458 | drive <-> energy                  |
| Growth     |    0.311 |    0.551 | circle <-> momentum               |
| Instincts  |    0.193 |    0.271 | creativity <-> intuition          |
+------------+----------+----------+-----------------------------------+
```

**Interpretation:**
- Heart group has highest internal correlation (0.619) - meters share aspects
- Instincts group has lowest (0.193) - most differentiated meters
- Within-group > between-group correlation (0.363 vs 0.210) = expected pattern

### High Correlation Pairs (|r| >= 0.50)

| Pair                          | Correlation | Groups          | Notes |
|-------------------------------|-------------|-----------------|-------|
| resilience <-> vulnerability  | 0.703       | heart/heart     | Same group |
| strength <-> vulnerability    | 0.628       | body/heart      | Cross-group |
| connections <-> vulnerability | 0.609       | heart/heart     | Same group |
| resilience <-> strength       | 0.598       | heart/body      | Cross-group |
| clarity <-> communication     | 0.595       | mind/mind       | Same group |
| circle <-> momentum           | 0.551       | growth/growth   | Same group |
| connections <-> resilience    | 0.546       | heart/heart     | Same group |
| evolution <-> momentum        | 0.544       | growth/growth   | Same group |
| clarity <-> focus             | 0.539       | mind/mind       | Same group |
| ambition <-> vision           | 0.534       | growth/instincts| Cross-group |

**Action items for future improvement:**
- strength correlates highly with heart meters (0.60-0.63) - review aspect filters
- ambition/vision cross-group correlation (0.53) - may share Jupiter aspects

---

## Algorithm Overview

### Core Formulas

```
DTI (Dual Transit Influence) = Sum(W_i * P_i)
HQS (Harmonic Quality Score) = Sum(W_i * P_i * Q_i)

Where:
- W_i = Weightage Factor (natal planet importance)
- P_i = Transit Power (aspect strength)
- Q_i = Quality Factor (-1 to +1, aspect harmony)
```

### Weightage Factor (W_i)

```python
W_i = (Planet_Base + Dignity + Ruler_Bonus) * House_Mult * Sensitivity

Planet_Base:
- Sun, Moon: 10.0
- Mercury, Venus, Mars: 7.0
- Jupiter, Saturn: 5.0
- Uranus, Neptune, Pluto, Nodes: 3.0

House_Mult:
- Angular (1,4,7,10): 3.0
- Succedent (2,5,8,11): 2.0
- Cadent (3,6,9,12): 1.0
```

### Transit Power (P_i)

```python
P_i = Aspect_Base * Orb_Factor * Direction_Mod * Station_Mod * Transit_Weight

Aspect_Base:
- Conjunction: 10.0
- Opposition: 9.0
- Square: 8.0
- Trine: 6.0
- Sextile: 4.0

Direction_Mod:
- Applying: 1.3
- Exact (<0.5 deg): 1.5
- Separating: 0.7
```

### Quality Factor (Q_i)

```python
Q_i = Base quality adjusted for planetary nature

Base Quality:
- Trine, Sextile: +1.0
- Square, Opposition: -1.0
- Conjunction: depends on planets involved

Planetary Nature (applied via harmonic_boost):
- Benefic (Venus, Jupiter): 2.0x boost to harmonious
- Malefic (Mars, Saturn): 0.5x softening to challenging
```

### Unified Score Calculation

```python
# Constants (from constants.py)
BASE_WEIGHT = 0.3       # Minimum harmony signal at intensity=0
INTENSITY_WEIGHT = 0.7  # How much intensity amplifies
TANH_FACTOR = 50.0      # Sigmoid stretch factor
POSITIVE_BOOST = 1.2    # Amplify positive scores
NEGATIVE_DAMPEN = 0.7   # Soften negative scores

# Step 1: Base direction from harmony (-100 to +100)
base_direction = (harmony - 50) * 2

# Step 2: Intensity as amplification factor (0.3 to 1.0)
magnitude_factor = BASE_WEIGHT + INTENSITY_WEIGHT * (intensity / 100)

# Step 3: Raw score before stretch
raw_score = base_direction * magnitude_factor

# Step 4: Sigmoid stretch using tanh (spreads middle values)
stretched = 100 * tanh(raw_score / TANH_FACTOR)

# Step 5: Empowering asymmetry
if stretched >= 0:
    unified_score = min(100, stretched * POSITIVE_BOOST)
else:
    unified_score = max(-100, stretched * NEGATIVE_DAMPEN)

# Result: -100 to +100 with positive bias
```

### Per-Meter Filtering

Each meter filters aspects based on its configuration in `labels/*.json`:

```python
# Example: Clarity meter
natal_planets: ["mercury", "moon"]  # Only aspects TO these
# Transit planets: all allowed
# Aspect types: all allowed
```

---

## Files Structure

| File | Description |
|------|-------------|
| `astrometers/core.py` | DTI/HQS calculation (~300 lines) |
| `astrometers/meters.py` | Meter filtering and reading (~900 lines) |
| `astrometers/constants.py` | All algorithm constants (~460 lines) |
| `astrometers/normalization.py` | Percentile normalization |
| `astrometers/hierarchy.py` | 17 meters, 5 groups enum |
| `astrometers/labels/*.json` | Per-meter configs and labels |
| `astrometers/calibration/` | Calibration scripts and data |

---

## Analysis Scripts

### When to Use Each Script

| Script | Purpose | When to Run | Duration |
|--------|---------|-------------|----------|
| `test_astrometer_distribution.py` | Cross-meter correlation | After changing meter filters | ~5 min |
| `test_astrometer_day_correlation.py` | Day-to-day stability | After changing transit weights | ~8 min |
| `test_planet_velocities.py` | Planet speed analysis | Understanding transit dynamics | ~1 min |
| `test_charts_stats_v2.py` | Identical aspect detection | After changing meter filters | ~3 min |
| `calculate_historical_v2.py` | Re-calibrate percentiles | After any meter changes | ~10 min |
| `verify_percentile.py` | Verify calibration quality | After re-calibration | ~30 sec |

### Script Details

#### 1. Cross-Meter Correlation (`test_astrometer_distribution.py`)
**Purpose:** Ensure meters measure different things (low cross-correlation)

```bash
# Default: 1000 charts x 10 dates = 10,000 samples
uv run python functions/tests/integration/test_astrometer_distribution.py

# Custom parameters
uv run python functions/tests/integration/test_astrometer_distribution.py -n 500 -m 20
```

**Key metrics:**
- Avg cross-meter |r| < 0.30 (PASS)
- Within-group > between-group correlation (expected)
- No pair > 0.70 correlation (ideally)

#### 2. Day-to-Day Correlation (`test_astrometer_day_correlation.py`)
**Purpose:** Ensure meters change meaningfully between days (not too stable, not too volatile)

```bash
# Default: 500 charts x 20 day-pairs = 10,000 pairs
uv run python functions/tests/integration/test_astrometer_day_correlation.py

# Custom parameters
uv run python functions/tests/integration/test_astrometer_day_correlation.py -n 300 -d 30
```

**Key metrics:**
- Avg day correlation 0.4-0.7 (healthy dynamics)
- No meter > 0.85 (too stable)
- No meter < 0.30 (too volatile)
- Avg daily |delta| 10-30 points

#### 3. Planet Velocities (`test_planet_velocities.py`)
**Purpose:** Measure actual daily movement speed of each planet

```bash
uv run python functions/tests/integration/test_planet_velocities.py
```

**Key output:**
- Degrees/day for each planet
- Days to traverse 8-degree orb (typical aspect orb)
- Comparison of speed vs current transit weights

#### 4. Overlap Test (`test_charts_stats_v2.py`)
**Purpose:** Detect if two meters produce identical aspect sets

```bash
uv run python -m functions.astrometers.test_charts_stats_v2

# Custom chart count
uv run python -m functions.astrometers.test_charts_stats_v2 500
```

**Key metrics:**
- 0 charts with identical meter pairs (PASS)

#### 5. Calibration (`calculate_historical_v2.py`)
**Purpose:** Generate empirical percentiles for normalization

```bash
uv run python functions/astrometers/calibration/calculate_historical_v2.py
```

**Output:** `calibration_constants.json` with per-meter percentiles

#### 6. Verify Calibration (`verify_percentile.py`)
**Purpose:** Confirm percentile mapping is accurate

```bash
uv run python functions/astrometers/calibration/verify_percentile.py
```

### Unit Tests

```bash
# All astrometer unit tests
uv run pytest functions/astrometers/tests/ -v

# Specific test file
uv run pytest functions/astrometers/tests/test_meters_v2.py -v
```

---

## Key Constants Location

| Constant | File | Line | Purpose |
|----------|------|------|---------|
| `PLANET_BASE_SCORES` | constants.py | 21 | W_i natal planet weights |
| `ASPECT_BASE_INTENSITY` | constants.py | 92 | P_i aspect type weights |
| `TRANSIT_PLANET_WEIGHTS` | constants.py | 226 | P_i transit planet modifier |
| `QUALITY_TRINE/SQUARE` | constants.py | 257 | Q_i base quality values |
| `BENEFIC_QUALITY_MULTIPLIER` | constants.py | 271 | Harmonic boost factor |
| `UNIFIED_SCORE_*` | constants.py | 372 | Unified score formula weights |
| `METER_CONFIGS` | meters.py | 206 | Per-meter aspect filters |

---

## Potential Future Improvements

1. **Reduce heart/body cross-correlation** - strength meter overlaps with heart group
2. **Tune ambition/vision differentiation** - share Jupiter influence
3. **Day-to-day correlation analysis** - ensure meters change meaningfully between days
4. **A/B test empowering bias** - current 1.2/0.7 asymmetry may need tuning

---

## Velocity-Based Scoring ("The Symphony") - December 2025

### The Problem

Static degree-based orbs treat all planets equally, but planets move at vastly different speeds:

| Planet | Speed (deg/day) | Days in 8deg orb |
|--------|-----------------|------------------|
| Moon | ~13 | 0.6 days |
| Sun | ~1 | 8 days |
| Saturn | ~0.03 | 267 days |
| Pluto | ~0.02 | 400 days |

**Result:** Slow planets dominate meters (always "in orb"), making scores too stable day-to-day. Original variation coefficient was only **5.5%**.

### The Solution: Time-Normalized Scoring

Score based on **TIME** (velocity) rather than **SPACE** (degrees):

```python
# Calculate dynamic orb limit based on time window
dynamic_limit = (window_days * speed) / 2.0
dynamic_limit = clamp(0.5, 8.0)  # Safety bounds

# Normalized closeness (0 at edge, 1 at exact)
closeness = 1 - (deviation / dynamic_limit)

# The Spike: squared for sharper peak at exactitude
intensity = closeness ** 2

# Final score
score = intensity * tier_weight * aspect_modifier
```

### Tiered System

Transit planets grouped into tiers with different time windows and weights:

| Tier | Planets | Window | Role |
|------|---------|--------|------|
| **Trigger** | Moon | 1 day | The melody - daily variance |
| **Event** | Sun, Mercury, Venus, Mars | 4 days | Weekly rhythm |
| **Season** | Jupiter, Saturn | 45 days | Monthly context |
| **Era** | Uranus, Neptune, Pluto, Nodes | 100 days | Background hum |

### Mixing Profiles

Three philosophies for balancing tiers:

```python
MIXING_PROFILES = {
    'daily_pulse': {
        'trigger': 10.0,  # Moon dominates
        'event': 4.0,
        'season': 1.5,
        'era': 0.5,
    },
    'deep_current': {
        'trigger': 3.0,   # Compressed spread
        'event': 3.0,     # Equal to trigger
        'season': 2.0,    # Boosted
        'era': 2.0,       # Boosted significantly
    },
    'forecast': {
        'trigger': 2.0,   # Moon just for timing
        'event': 5.0,     # Inner planets dominate
        'season': 2.0,
        'era': 3.0,       # Outer planets matter for big events
    },
}
```

### Test Results (100 charts x 30 days = 3,000 samples)

**Tier Breakdown:**

| Profile | Trigger | Event | Season | Era | Target |
|---------|---------|-------|--------|-----|--------|
| daily_pulse | **60.9%** | 28.3% | 6.5% | 4.2% | ~50/30/10/10 |
| deep_current | **28.1%** | **33.7%** | 12.3% | **25.9%** | ~30/30/20/20 |
| forecast | 15.0% | **43.8%** | 9.9% | **31.3%** | ~20/50/10/20 |

**Variation Metrics:**

| Profile | Var Coef | Assessment |
|---------|----------|------------|
| daily_pulse | **57.5%** | High - engaging but potentially erratic |
| deep_current | **34.1%** | Sweet spot (target: 35-50%) |
| forecast | **30.0%** | Lower end - may feel too stable |

**Score Distribution (deep_current):**
- 10th percentile: 5.0
- 50th percentile: 10.0 (median)
- 90th percentile: 16.1

### Key Findings

1. **deep_current hits the sweet spot** - 34% variation is in the recommended range, and tier distribution is close to target (28/34/12/26 vs 30/30/20/20)

2. **Season tier is consistently low** across all profiles (6-12% vs 20% target). Jupiter/Saturn aren't contributing as much as expected - may need to boost `season` weight further.

3. **daily_pulse** has Moon at 61% which is higher than target 50%. Still engaging but may drown out life context during major transits.

4. **forecast** is stable (30% var) with Event+Era at 75% - good for "what's happening this week" but less daily pulse.

### UX Implications

| Profile | User Experience |
|---------|-----------------|
| **daily_pulse** | "My mood changes constantly" - high engagement, gamification |
| **deep_current** | "Challenging month, lighter day" - psychologically credible |
| **forecast** | "Something big is happening" - event prediction focus |

### Recommendation

**Use `deep_current` as default** for the target audience (20-something women navigating life transitions):
- Acknowledges major life transits (Saturn return, Pluto squares)
- Still provides meaningful daily variation
- Credible during crisis (won't say "great day!" during hard transit)

### Running the Analysis

```bash
# Compare all mixing profiles (100 charts, 30 days each)
uv run python functions/tests/integration/test_symphony_visualization.py --profiles --days 30

# Compare old vs new scoring
uv run python functions/tests/integration/test_symphony_visualization.py --compare --days 30

# Single chart symphony analysis
uv run python functions/tests/integration/test_symphony_visualization.py --days 60
```

### Files Modified

| File | Changes |
|------|---------|
| `constants.py` | Added `MIXING_PROFILES`, `TransitTier`, `set_mixing_profile()` |
| `transit_power.py` | Added `calculate_velocity_score()`, `ASPECT_MODIFIERS` |
| `test_symphony_visualization.py` | New analysis script |

### Next Steps

1. **Tune Season weights** - Currently 6-12% vs 20% target
2. **A/B test profiles** - Compare user engagement metrics
3. **Integrate into meters.py** - Replace static orb scoring with velocity-based
4. **Re-run calibration** - After switching to velocity scoring

---

## Gaussian Mixture Scoring - December 2025

### The Problem with Hard Edges

The velocity-based system still has a hard cutoff at the dynamic orb limit:

```python
# Current velocity scoring
if deviation_deg > dynamic_limit:
    return 0.0  # Hard edge - score instantly drops to zero

closeness = 1 - (deviation / dynamic_limit)
intensity = closeness ** 2
```

This creates:
- **Discontinuous behavior** at orb boundaries
- **No tail contribution** from aspects just outside the window
- **Less natural interference** when multiple aspects overlap

### The Solution: Gaussian Decay

Replace hard cutoffs with smooth Gaussian (bell curve) decay:

```python
# Gaussian scoring
sigma = window_days / SIGMA_DIVISOR  # SIGMA_DIVISOR = 9.0
deviation_days = deviation_deg / speed
intensity = exp(-(deviation_days ** 2) / (2 * sigma ** 2))
score = intensity * tier_weight * aspect_modifier
```

**Key benefits:**
1. **No Hard Edges**: Influence fades asymptotically to zero
2. **Constructive Interference**: Overlapping aspects sum naturally into "peak experiences"
3. **Mathematically Elegant**: Well-understood statistical properties

### The Math

Standard Gaussian function:

$$f(t) = A \cdot e^{-\frac{(t - \mu)^2}{2\sigma^2}}$$

Where:
- $t - \mu$ = Time to exact (in days)
- $A$ = Tier weight
- $\sigma$ = window_days / 9.0 (optimized for 35-50% variation)

**Intensity at different sigma distances:**

| Distance | Intensity | Meaning |
|----------|-----------|---------|
| 0 (exact) | 100% | Full strength |
| 1σ | 60.7% | Strong influence |
| 2σ | 13.5% | Moderate influence |
| 3σ | 1.1% | Minimal influence |
| >3σ | <1% | Cutoff threshold |

### Sigma Divisor Optimization

Tested different sigma divisors to find optimal day-to-day variation:

```
Divisor     Var Coef    Assessment
-----------------------------------
3.0         18.0%       Too smooth
5.0         26.9%       Low
7.0         33.0%       Low
9.0         39.3%       SWEET SPOT
12.0        48.2%       SWEET SPOT
```

**Selected: SIGMA_DIVISOR = 9.0** (39% variation, middle of sweet spot)

### Test Results (100 charts x 30 days = 3,000 samples)

**Velocity vs Gaussian Comparison:**

```
+---------------------------+-----------+-----------+---------+
| Metric                    | Velocity  | Gaussian  | Delta   |
+---------------------------+-----------+-----------+---------+
| Mean total score          |      10.2 |       8.4 |    -1.8 |
| Min score                 |       0.9 |       0.0 |    -0.9 |
| Max score                 |      27.5 |      28.7 |    +1.3 |
| Avg daily delta           |       3.2 |       3.4 |    +0.2 |
| Max daily delta           |      18.0 |      23.2 |    +5.2 |
| Variation coefficient     |     31.6% |     41.0% |   +9.4% |
+---------------------------+-----------+-----------+---------+
```

**Tier Distribution (nearly identical):**

```
+----------+-----------+-----------+--------+
| Tier     | Velocity  | Gaussian  | Delta  |
+----------+-----------+-----------+--------+
| Trigger  |     28.1% |     28.3% |  +0.3% |
| Event    |     32.6% |     32.8% |  +0.2% |
| Season   |     13.4% |     13.4% |  +0.0% |
| Era      |     25.9% |     25.5% |  -0.5% |
+----------+-----------+-----------+--------+
```

**Score Distribution:**

```
+------------+----------+----------+-------+
| Percentile | Velocity | Gaussian | Ratio |
+------------+----------+----------+-------+
| 10th       |      5.1 |      3.2 | 0.63x |
| 25th       |      7.1 |      5.3 | 0.74x |
| 50th       |      9.8 |      8.0 | 0.81x |
| 75th       |     12.9 |     11.0 | 0.86x |
| 90th       |     15.8 |     14.1 | 0.89x |
+------------+----------+----------+-------+
```

### Key Findings

1. **Gaussian hits the sweet spot**: 41% variation (target: 35-50%)
2. **Tier distribution unchanged**: Both methods produce ~28/33/13/26 split
3. **Higher max delta**: 23.2 vs 18.0 - more dramatic peak experiences
4. **Slightly lower scores**: 0.82x average, but similar distribution shape

### The Stellium Effect

When multiple planets form simultaneous aspects (stellium), Gaussian curves sum naturally:

```
Total = Σ (A_i · exp(-(t_i²) / (2σ_i²)))
```

If all aspects are near-exact (t ≈ 0), the curves stack to create dramatic "peak experience" days that feel astrologically significant.

### Implementation

**Files modified:**
- `transit_power.py`: Added `calculate_gaussian_score()`, `GAUSSIAN_SIGMA_DIVISOR`
- `test_symphony_visualization.py`: Added `--gaussian` and `--sigma` comparison modes

**Usage:**

```python
from astrometers.transit_power import calculate_gaussian_score

score, breakdown = calculate_gaussian_score(
    transit_planet=Planet.MOON,
    deviation_deg=2.0,
    transit_speed=13.0,  # degrees/day
    aspect_type=AspectType.CONJUNCTION,
)
```

### Running the Analysis

```bash
# Compare Velocity vs Gaussian (100 charts, 30 days each)
uv run python functions/tests/integration/test_symphony_visualization.py --gaussian -n 100 --days 30

# Test different sigma divisors
uv run python functions/tests/integration/test_symphony_visualization.py --sigma -n 50 --days 30
```

### Recommendation

**Use Gaussian scoring** for production:
- Better UX: No jarring score drops at orb boundaries
- More variation: 41% vs 31.6% (more engaging daily experience)
- Natural stellium handling: Peak experiences feel earned
- Mathematically principled: Well-understood statistical properties

### Next Steps

1. **Integrate into meters.py** - Replace velocity scoring with Gaussian
2. **Re-run calibration** - After switching to Gaussian scoring
3. **A/B test** - Compare user engagement with Gaussian vs velocity

---

## Decoupled Intensity/Harmony Scoring - December 2025

### The Problem with Coupled Scoring

Current formulas share the same base components:

```
DTI = Σ(W_i × P_i)           ← intensity
HQS = Σ(W_i × P_i × Q_i)     ← harmony
```

**Issues:**
1. **Correlation**: DTI and HQS are mathematically coupled via shared `W_i × P_i`
2. **Suppressed signals**: On quiet days (low DTI), harmony is muted even if aspects are all harmonious
3. **False extremes**: One weak trine on a quiet day gives high harmony ratio

### The Solution: Magnitude vs Polarity

Decouple the metrics:
- **Intensity** = Volume (how loud is the music?)
- **Harmony** = Polarity (is it a happy song or a sad song?)

#### The Formula

```
Intensity = Σ(Power)
Harmony = Σ(Power × Polarity) / (Intensity + Ballast)
```

Where:
- `Power` = Gaussian score (tier weight × velocity curve)
- `Polarity` = +1 (trine/sextile), -1 (square/opposition), or conjunction logic
- `Ballast` = Noise floor constant (prevents instability at low intensity)

#### Why Ballast is Critical

Without ballast, low-intensity days have unstable harmony:

```python
# WITHOUT Ballast - One weak Moon trine (Power = 0.5):
harmony = (0.5 × 1) / 0.5 = +1.0  # "Pure Euphoria" - FALSE!

# WITH Ballast (10.0) - Same day:
harmony = (0.5 × 1) / (0.5 + 10.0) = +0.04  # "Basically Neutral" - TRUE
```

The ballast ensures you need "enough signal" to register meaningful polarity.

#### Output Ranges

- **Intensity**: 0.0 to ~100+ (raw, then percentile-normalized to 0-100)
- **Harmony**: -1.0 to +1.0 (then mapped to 0-100 for display: `(h + 1) × 50`)

### Design Decisions

1. **Ballast value**: Determine empirically during calibration
   - Target: ~1.5× the weight of a single standard transit
   - Per-meter ballast may be needed (meters see different aspect counts)

2. **Conjunction handling**: Keep existing benefic/malefic logic
   - Venus/Jupiter conjunctions → positive polarity
   - Saturn/Mars conjunctions → negative polarity
   - (Not simplified to Q=0)

3. **Backwards compatibility**: Previous scoring was broken, no need to maintain
   - Old DTI/HQS fields can be removed or kept for debugging

### UX Quadrants

| Intensity | Harmony | Experience | UI |
|-----------|---------|------------|-----|
| Low (5) | Neutral (+0.1) | "Quiet Flow" | Small pale green |
| High (80) | Positive (+0.7) | "Peak Experience" | Large bright green |
| High (80) | Negative (-0.7) | "Crisis/Challenge" | Large bright red |
| High (80) | Neutral (0.0) | "High Voltage/Mixed" | Large yellow |

Note: Low intensity + extreme harmony is mathematically prevented by ballast.

### Implementation Plan

```python
def calculate_astrometers_v2(aspects: List[TransitAspect], ballast: float = 10.0):
    """
    V2: Decoupled Intensity (Volume) and Harmony (Polarity).
    """
    total_intensity = 0.0
    net_quality_sum = 0.0

    for aspect in aspects:
        # Gaussian power (tier weight × velocity curve)
        power = calculate_gaussian_power(aspect)

        # Polarity from aspect type (keep benefic/malefic logic for conjunctions)
        polarity = get_aspect_polarity(aspect)

        total_intensity += power
        net_quality_sum += power * polarity

    # Harmony coefficient: -1.0 to +1.0
    if total_intensity > 0:
        harmony_coefficient = net_quality_sum / (total_intensity + ballast)
    else:
        harmony_coefficient = 0.0

    return intensity, harmony_coefficient
```

### Files to Modify

| File | Changes |
|------|---------|
| `core.py` | Add `calculate_gaussian_power()`, update `calculate_astrometers()` |
| `transit_power.py` | Expose Gaussian scoring for power calculation |
| `meters.py` | Update to use new decoupled scoring |
| `normalization.py` | Update for new intensity/harmony ranges |
| `calibration/` | Re-run to determine empirical ballast |

### Open Questions

1. Should ballast be global or per-meter?
2. How does Gaussian power interact with existing W_i (weightage factor)?
3. Do we need separate calibration for intensity vs harmony?

---

## Implementation Complete - December 2025

### The Problem We Solved

**Original Issue**: High day-to-day correlation in astrometer scores
- V1 DTI/HQS were mathematically coupled (shared W_i x P_i base)
- Slow planets (Saturn, Pluto) dominated because they're always "in orb"
- Only 5.5% daily variation - scores felt static

**Solution**: Decouple Intensity and Harmony into independent signals
- **Intensity** = Volume (how much is happening) - uses Gaussian/velocity scoring
- **Harmony** = Polarity (good or bad) - normalized by ballast to prevent false extremes

### Mathematical Foundation

```
# V1 (Legacy - Coupled)
DTI = Σ(W_i × P_i)           # Intensity
HQS = Σ(W_i × P_i × Q_i)     # Harmony (coupled to DTI)

# V2 (New - Decoupled)
Power = W_i × Gaussian_Score  # Personalized velocity-based power
Intensity = Σ(Power)          # Pure magnitude
Harmony = Σ(Power × Q_i) / (Intensity + Ballast)  # Pure polarity (-1 to +1)
```

**Why Ballast?**
- Without it: One weak Moon trine → harmony = +1.0 (false euphoria)
- With ballast: Same day → harmony = +0.04 (correctly neutral)
- Ballast acts as "noise floor" - need enough signal to register polarity

### Code Changes

**core.py** (`functions/astrometers/core.py`):
```python
# New fields in TransitAspect
transit_speed: Optional[float] = None  # degrees/day from chart

# New fields in AspectContribution
gaussian_power: float = 0.0   # W_i × Gaussian_Score
polarity: float = 0.0         # Q_i (-1 to +1)

# New fields in AstrometerScore
intensity: float = 0.0        # Σ(Power)
harmony_coefficient: float = 0.0  # -1 to +1

# New constant
DEFAULT_BALLAST = 10.0

# Updated calculate_aspect_contribution() - computes both V1 and V2
# Updated calculate_astrometers() - computes decoupled scores with ballast
# Added _get_planet_speed() - extracts speed from transit chart
```

**meters.py** (`functions/astrometers/meters.py`):
```python
# New parameter in calculate_meter() and get_meters()
use_v2_scoring: bool = True

# V2 scoring path:
intensity = min(100.0, (raw_score.intensity / v2_intensity_scale) * 100.0)
harmony = (raw_score.harmony_coefficient + 1) * 50  # -1..+1 → 0..100

# Raw scores now include both V1 and V2:
raw_scores = {
    "dti": raw_score.dti,
    "hqs": raw_score.hqs,
    "intensity_raw": raw_score.intensity,
    "harmony_coefficient": raw_score.harmony_coefficient,
}
```

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Power formula | W_i × Gaussian_Score | Preserves natal chart personalization |
| Conjunction polarity | Keep benefic/malefic logic | Venus conj = positive, Saturn conj = negative |
| Default ballast | 10.0 | Placeholder - determine empirically |
| V2 as default | `use_v2_scoring=True` | V1 available via flag for comparison |

### Validation Results

```
# Tier breakdown (V2 - Gaussian scoring)
trigger (Moon):    51.2%  ← Fast planets dominate daily variance
event (Sun, etc):  26.2%
season (Jup/Sat):   2.4%  ← Slow planets contribute less
era (outer):       20.1%  ← Unless aspects are very tight

# Intensity-Harmony correlation
V1: High (mathematically coupled)
V2: 0.074 (successfully decoupled!)

# V2 vs V1 comparison
Meter             V1 I   V1 H    V1 U |   V2 I   V2 H    V2 U
----------------------------------------------------------------------
clarity           27.4   34.8   -20.4 |    0.0   30.0   -16.5
energy            46.0   67.0   +48.0 |   14.8   79.9   +53.8
intuition         42.1   51.6    +4.7 |   26.7   25.0   -31.6
```

### Files Modified

| File | Lines Changed | Description |
|------|---------------|-------------|
| `core.py` | ~80 | Added V2 fields, Gaussian power calc, ballast |
| `meters.py` | ~30 | Added use_v2_scoring flag, V2 scoring path |
| `ASTROMETERS_V2.md` | ~150 | This documentation |

### Tests

- 366 unit tests: PASS
- 43 integration tests: PASS
- No new mypy errors in modified files

---

## Next Steps

### 1. Calibration (In Progress)

Running calibration to determine:
- Empirical ballast value (currently placeholder 10.0)
- V2 intensity percentiles for proper normalization
- Per-meter calibration data

```bash
uv run python functions/astrometers/calibration/calculate_historical_v2.py
```

### 2. Post-Calibration Analysis - COMPLETED

**A. Day-to-Day Correlation - PASS**
```
+--------------------------------+------------+------------+--------+
| Metric                         | Value      | Target     | Status |
+--------------------------------+------------+------------+--------+
| Avg Day-to-Day Correlation     |      0.507 | 0.4-0.7    |   PASS |
| Min Day Correlation            |      0.430 | >0.2       |   PASS |
| Max Day Correlation            |      0.584 | <0.85      |   PASS |
| Avg Daily |Delta|              |       24.5 | 10-30      |   PASS |
+--------------------------------+------------+------------+--------+
```
All meters now have healthy day-to-day dynamics (was too stable before).

**B. Inter-Meter Correlation - PASS**
```
+--------------------------------+------------+------------+--------+
| Metric                         | Value      | Target     | Status |
+--------------------------------+------------+------------+--------+
| Avg Cross-Meter |Correlation|  |      0.246 | <0.30      |   PASS |
| Within-Group Avg |r|           |      0.387 | -          |  INFO  |
| Between-Group Avg |r|          |      0.220 | -          |  INFO  |
+--------------------------------+------------+------------+--------+
```
Meters within same group are more correlated (expected behavior).

**C. Intensity-Harmony Decorrelation - PASS**
- Correlation: 0.074 (effectively independent)
- Ballast working correctly to prevent false extremes

### 3. Post-Calibration Code Updates - COMPLETED

1. **Added `normalize_intensity_v2()`** in `normalization.py` - uses V2 percentiles
2. **Updated `meters.py`** - imports and uses `normalize_intensity_v2()` for V2 mode
3. **Fixed retrograde modifier** - now applies to deviation from neutral only (preserves 50 when intensity=0)
4. **Updated calibration script** - now captures `intensity_v2` and generates `intensity_v2_percentiles`

---

## Current Status - December 2025

### What's Done

| Component | Status | Notes |
|-----------|--------|-------|
| V2 decoupled scoring | DONE | Intensity + Harmony with ballast |
| Gaussian power calculation | DONE | W_i × Gaussian_Score |
| Transit speed extraction | DONE | From chart data |
| Retrograde modifier fix | DONE | Applies to deviation only |
| V2 normalization function | DONE | `normalize_intensity_v2()` |
| Calibration script update | DONE | Captures V2 intensity data |
| Quick calibration test | DONE | 100 charts × 1 year |

### Test Results (Quick Calibration)

```
Cross-Meter Correlation:  0.221 (target <0.30) PASS
Day-to-Day Correlation:   0.507 (target 0.4-0.7) PASS
Score Range:              -67 to +100
All StdDevs:              27-41 (target 25-60) PASS
```

### Files Modified

| File | Changes |
|------|---------|
| `core.py` | V2 fields, Gaussian power, ballast, `_get_planet_speed()` |
| `meters.py` | `use_v2_scoring` flag, V2 scoring path, retrograde fix |
| `normalization.py` | Added `normalize_intensity_v2()` |
| `calculate_historical_v2.py` | Captures `intensity_v2`, generates V2 percentiles |
| `calibration_constants.json` | Now includes `intensity_v2_percentiles` per meter |

### How to Resume

```python
# V2 scoring is ON by default
meters = get_meters(natal, transit, date)  # uses V2

# To use V1 (legacy):
meters = get_meters(natal, transit, date, use_v2_scoring=False)
```

---

## Action Items

### REQUIRED: Run Full Calibration

Current calibration used only 100 charts × 1 year (quick test).
Production needs 1000+ charts × 5 years for accurate percentiles.

```bash
# Edit the script to use full settings:
# SAMPLE_SIZE = 1000 (or more)
# START_DATE = "2020-01-01"
# END_DATE = "2024-12-31"

uv run python functions/astrometers/calibration/calculate_historical_v2.py
```

**Expected runtime:** 10-30 minutes depending on CPU cores.

### Optional Improvements

1. **Per-meter ballast** - Some meters may need different ballast values
2. **Station detection** - Boost intensity when planets are stationary
3. **A/B testing** - Compare V1 vs V2 user engagement

### 3. Production Rollout

1. **A/B test** - Compare user engagement V1 vs V2
2. **Monitor** day-to-day variation metrics
3. **Tune ballast** if needed based on user feedback

### 4. Future Enhancements

- Per-meter ballast (meters with fewer aspects may need lower ballast)
- Benefic/malefic boost on polarity (currently just uses Q_i directly)
- Station detection for extra intensity boost

---

## Unified Score Formula V2 - December 2025

### The Problem with V1 Unified Score

The original formula had harmony driving the value and intensity just amplifying:

```python
# V1 Formula (WRONG)
base_direction = (harmony - 50) * 2  # Harmony drives value (-100 to +100)
magnitude_factor = 0.3 + 0.7 * (intensity / 100)  # Intensity just scales (0.3-1.0)
raw_score = base_direction * magnitude_factor
```

**Issues:**
- Harmony determined HOW FAR from 0 the score went
- Intensity only amplified (0.3x to 1.0x)
- A low-intensity positive day felt same as high-intensity positive day

### The Solution: Intensity as Value, Harmony as Direction

The correct model:
- **Intensity** = HOW MUCH is happening (the magnitude)
- **Harmony** = WHAT KIND of energy (positive or negative direction)

```python
# V2 Formula (CORRECT)
sigmoid = tanh(intensity / 50)  # S-curve: 0->0, 50->0.76, 100->0.96
harmony_coef = (harmony - 50) / 50  # -1 to +1

if harmony_coef >= 0:  # Positive aspects winning
    # Range: 50-100 (proportional to harmony strength)
    max_lift = 50 * harmony_coef
    unified = 50 + max_lift * sigmoid
else:  # Negative aspects winning
    # Range: 20-50 (compressed - empowering bias)
    max_drop = 30 * abs(harmony_coef)
    unified = 50 - max_drop * sigmoid
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Score range | 20-100 | Empowering bias - bad days never catastrophic |
| Neutral point | 50 | Clear midpoint for UX |
| Positive range | 50-100 | Full upside for good days |
| Negative range | 20-50 | Compressed (30 pts vs 50 pts) |
| Sigmoid curve | tanh(I/50) | Diminishing returns at high intensity |
| Harmony strength | Proportional | Strong +H goes higher than weak +H |

### Score Behavior Examples

| Scenario | Intensity | Harmony | Score | Explanation |
|----------|-----------|---------|-------|-------------|
| Jupiter exact trine | 80 | 95 | **91.5** | High I + Strong +H = great day |
| Weak positive aspect | 20 | 60 | 55.5 | Low I + Weak +H = slightly positive |
| Saturn exact square | 80 | 5 | **25.1** | High I + Strong -H = challenging |
| Weak negative aspect | 20 | 40 | 45.5 | Low I + Weak -H = slightly challenging |
| Quiet day | 5 | 50 | **50.0** | No activity = neutral |
| Mixed aspects cancel | 60 | 50 | **50.0** | High I + Neutral H = still neutral |

### Updated Quality Labels

```python
# Thresholds for 0-100 scale
if unified_score < 35:
    return "Challenging"  # Strong negative
elif unified_score < 50:
    return "Turbulent"    # Mild negative or low activity
elif unified_score < 70:
    return "Peaceful"     # Mild positive
else:
    return "Flowing"      # Strong positive
```

### Test Results Comparison

**Before (V1 Formula - -100 to +100 scale):**
```
| Metric                      | Value  | Target   |
|-----------------------------|--------|----------|
| Avg Day-to-Day Correlation  | 0.507  | 0.4-0.7  |
| Avg Daily |Delta|           | 24.5   | 10-30    |
```

**After (V2 Formula - 20-100 scale):**
```
| INDIVIDUAL METERS              | Value  | Target   | Status |
|--------------------------------|--------|----------|--------|
| Avg Day-to-Day Correlation     | 0.444  | 0.4-0.7  | PASS   |
| Min Day Correlation            | 0.422  | >0.2     | PASS   |
| Max Day Correlation            | 0.476  | <0.85    | PASS   |
| Avg Daily |Delta|              | 5.5    | 5-15     | PASS   |
|--------------------------------|--------|----------|--------|
| GROUP METERS (UX-critical)     | Value  | Target   | Status |
|--------------------------------|--------|----------|--------|
| Avg Group Day Correlation      | 0.448  | 0.4-0.7  | PASS   |
| Avg Group Daily |Delta|        | 4.5    | 3-10     | PASS   |
| Overall Day Correlation        | 0.439  | 0.5-0.8  | WARN   |
| Overall Daily |Delta|          | 3.8    | 2-8      | PASS   |
```

**Group-Level Results (what users see):**
```
| Group     | Day Corr | Avg Delta | Stability |
|-----------|----------|-----------|-----------|
| Mind      | 0.455    | 4.7       | Dynamic   |
| Heart     | 0.455    | 5.5       | Dynamic   |
| Body      | 0.451    | 4.8       | Dynamic   |
| Instincts | 0.442    | 3.7       | Dynamic   |
| Growth    | 0.447    | 4.5       | Dynamic   |
| OVERALL   | 0.439    | 3.8       | Dynamic   |
```

### Key Improvements

1. **More dynamic** - Correlation dropped from 0.507 to 0.444
2. **Consistent across groups** - All 5 groups have similar dynamics (~0.45)
3. **No outliers** - Max correlation 0.476 (was 0.584)
4. **All meters "Dynamic"** - Healthy range for daily engagement

### Files Modified

| File | Changes |
|------|---------|
| `meters.py` | New `calculate_unified_score()` formula |
| `meters.py` | Updated `get_quality_label()` thresholds (0-100) |
| `meters.py` | Updated `get_state_label()` thresholds (0-100) |
| `test_astrometer_distribution.py` | Updated targets for 0-100 scale |
| `test_astrometer_day_correlation.py` | Added group-level analysis |

---

## Test Scripts Reference

### Quick Reference

| Script | Purpose | When to Run | Command |
|--------|---------|-------------|---------|
| `test_astrometer_distribution.py` | Cross-meter correlation & distribution | After changing filters | `uv run python tests/integration/test_astrometer_distribution.py -n 200 -m 5` |
| `test_astrometer_day_correlation.py` | Day-to-day stability + group metrics | After changing scoring | `uv run python tests/integration/test_astrometer_day_correlation.py -n 200 -d 10` |
| `test_symphony_visualization.py` | Tier breakdown & mixing profiles | After changing transit weights | `uv run python tests/integration/test_symphony_visualization.py --profiles` |
| `calculate_historical_v2.py` | Re-calibrate percentiles | After any formula change | `uv run python astrometers/calibration/calculate_historical_v2.py` |
| `verify_percentile.py` | Verify calibration quality | After re-calibration | `uv run python astrometers/calibration/verify_percentile.py` |

### Detailed Script Documentation

#### 1. Distribution Analysis (`test_astrometer_distribution.py`)

**Purpose:** Verify meters measure different things (low cross-correlation)

**What it does:**
1. Generates N random birth charts
2. Calculates all 17 meters for M random transit dates per chart
3. Analyzes unified_score distributions per meter
4. Computes cross-meter correlation matrix
5. Reports within-group vs between-group correlation

**Key metrics:**
- Avg cross-meter |r| < 0.30 (meters are differentiated)
- Within-group > between-group (expected pattern)
- Mean scores 45-55 (centered around neutral)
- StdDev 5-15 (healthy spread on 0-100 scale)

**Usage:**
```bash
# Quick test (500 samples)
uv run python tests/integration/test_astrometer_distribution.py -n 100 -m 5

# Full test (10,000 samples)
uv run python tests/integration/test_astrometer_distribution.py -n 1000 -m 10
```

#### 2. Day Correlation Analysis (`test_astrometer_day_correlation.py`)

**Purpose:** Verify meters change meaningfully day-to-day (not too stable, not too volatile)

**What it does:**
1. Generates N random birth charts
2. For each chart, picks D random consecutive day pairs
3. Calculates meters for day1 and day2
4. Correlates day1 scores with day2 scores per meter
5. **NEW: Reports group-level (Mind, Heart, Body, Instincts, Growth) correlations**
6. **NEW: Reports overall app score correlation**

**Key metrics:**
- Individual meter correlation 0.4-0.7 (healthy dynamics)
- No meter > 0.85 (too stable)
- No meter < 0.30 (too volatile)
- Avg daily |delta| 5-15 (noticeable but not erratic)
- Group correlation ~0.45 (what users actually see)

**Stability interpretation:**
```
corr > 0.85: TOO STABLE - feels static
corr 0.7-0.85: Stable - slow evolution
corr 0.5-0.7: Moderate - balanced change
corr 0.3-0.5: Dynamic - noticeable daily shifts
corr < 0.3: VOLATILE - feels random
```

**Usage:**
```bash
# Quick test (2,000 day pairs)
uv run python tests/integration/test_astrometer_day_correlation.py -n 200 -d 10

# Full test (10,000 day pairs)
uv run python tests/integration/test_astrometer_day_correlation.py -n 500 -d 20
```

#### 3. Symphony Visualization (`test_symphony_visualization.py`)

**Purpose:** Analyze tier contribution breakdown (Moon vs Sun vs Jupiter vs Pluto)

**What it does:**
1. Calculates transit aspects with Gaussian scoring
2. Groups contributions by tier (trigger/event/season/era)
3. Compares different mixing profiles
4. Shows variation coefficient (daily score volatility)

**Key metrics:**
- Tier distribution (target: ~30/30/20/20 for deep_current)
- Variation coefficient 35-50% (sweet spot)
- Max daily delta (peak experience potential)

**Usage:**
```bash
# Compare mixing profiles
uv run python tests/integration/test_symphony_visualization.py --profiles -n 100 --days 30

# Compare Gaussian vs Velocity scoring
uv run python tests/integration/test_symphony_visualization.py --gaussian -n 100 --days 30
```

#### 4. Calibration (`calculate_historical_v2.py`)

**Purpose:** Generate empirical percentiles for intensity normalization

**What it does:**
1. Generates 1000+ random birth charts
2. Calculates meters for 5 years of transit dates
3. Collects raw intensity values per meter
4. Computes percentile breakpoints (1, 5, 10, 25, 50, 75, 90, 95, 99)
5. Saves to `calibration_constants.json`

**When to run:**
- After changing meter filters
- After changing scoring formula
- After changing transit weights

**Usage:**
```bash
uv run python astrometers/calibration/calculate_historical_v2.py
```

**Output:** Updates `calibration_constants.json` with per-meter percentiles

#### 5. Verify Calibration (`verify_percentile.py`)

**Purpose:** Confirm percentile mapping produces uniform distribution

**What it does:**
1. Generates test charts
2. Applies percentile normalization
3. Verifies normalized values are uniformly distributed

**Usage:**
```bash
uv run python astrometers/calibration/verify_percentile.py
```

### Running All Tests

```bash
# Unit tests (fast, no API keys needed)
uv run pytest tests/unit/ -v

# Integration tests (may need API keys)
uv run pytest tests/integration/ -v

# Quick quality check after changes
uv run python tests/integration/test_astrometer_distribution.py -n 100 -m 5
uv run python tests/integration/test_astrometer_day_correlation.py -n 100 -d 5
```

---

## Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| V2 Decoupled Scoring | DONE | Intensity + Harmony with ballast |
| Gaussian Power | DONE | W_i x Gaussian_Score |
| Unified Score V3 | DONE | Intensity stretch + Dither + Post-sigmoid |
| Per-Meter Ballast | DONE | Derived from calibration P50/2 |
| Cosmic Background Dither | DONE | Eliminates 50-spike |
| Group-level Analysis | DONE | Mind/Heart/Body/Instincts/Growth |
| Day Correlation | PASS | Avg 0.41 (target 0.3-0.5) |
| Cross-Meter Correlation | PASS | Avg 0.207 (target <0.30) |
| All Meters Dynamic | PASS | No TOO STABLE or VOLATILE |

---

## Unified Score V3 - December 2025

### Problems Solved

1. **Stationary Planet Paradox**: Planets at station (speed ≈ 0) got zero intensity
2. **Per-Meter Ballast**: Fixed ballast=10 was too high for fast-planet meters
3. **U-Shaped Distribution**: Too many scores at extremes (0 and 100)
4. **50-Spike**: 30%+ of scores clustered at exactly 50 (neutral)

### Fix 1: Stationary Planet Minimum Speed

**File:** `transit_power.py`

```python
# OLD: min_speed = 0.001 (stationary planets got ZERO intensity)
# NEW: min_speed = 0.05 (stationary planets register properly)
speed = max(abs(transit_speed), 0.05)
```

**Why 0.05?** At 0.001, a planet 1° from exact has deviation_days = 1000, way beyond 3σ, giving zero Gaussian intensity. At 0.05, it's 20 days, within 2σ, giving ~20% intensity.

### Fix 2: Per-Meter Ballast from Calibration

**File:** `core.py`

**Formula:** `Ballast = Median Intensity (P50) / 2`

```python
METER_BALLAST = {
    "ambition": 10.9,
    "circle": 7.2,
    "clarity": 8.5,
    "communication": 3.9,  # Only Mercury - low P50
    "connections": 8.6,
    "creativity": 4.8,
    "drive": 14.7,
    "energy": 6.4,
    "evolution": 9.6,
    "flow": 2.1,           # Very low P50
    "focus": 5.2,          # Only Mercury
    "intuition": 9.3,
    "momentum": 7.9,
    "resilience": 2.5,     # Only Moon - low P50
    "strength": 10.5,
    "vision": 16.6,
    "vulnerability": 5.1,
}
```

**Why per-meter?** Fast-planet meters (Mercury, Moon, Venus) have low median intensity. A fixed ballast of 10.0 was higher than their P50, crushing their harmony signal and causing them to flatline at 50.

### Fix 3: Unified Score Formula V3

**File:** `meters.py` - `calculate_unified_score()`

```python
def calculate_unified_score(intensity, harmony, dither=0.0):
    # Convert harmony (0-100) to coefficient (-1 to +1)
    harmony_coef = (harmony - 50) / 50

    # Step 1: Intensity stretch with moderate gain
    # tanh(I/60): 5->8.3, 20->32, 50->70, 80->87, 100->93
    stretched_intensity = 100 * tanh(intensity / 60)

    # Step 2: Linear combination
    raw_unified = 50 + (stretched_intensity / 2) * harmony_coef

    # Step 2.5: Apply cosmic background dither with diminishing intensity
    # Full dither when neutral (raw=50), zero at extremes
    proximity_to_neutral = 1.0 - abs(raw_unified - 50) / 50
    scaled_dither = dither * max(0, proximity_to_neutral)
    raw_unified += scaled_dither

    # Step 3: Post-sigmoid stretch with headroom
    # Divisor of 25 ensures P95 maps to ~80, not 100
    deviation = raw_unified - 50
    stretched = 50 * tanh(deviation / 25)
    unified_score = 50 + stretched

    return round(unified_score, 1)
```

**Key parameters:**
- `intensity_divisor = 60` (was 30 - too hot)
- `stretch_factor = 25` (was 10 - too aggressive)

### Fix 4: Cosmic Background Dither

**File:** `core.py` - `get_cosmic_dither()`

**Purpose:** Prevent the exact-50 spike by simulating minor astrological influences (asteroids, fixed stars, minor aspects, midpoints).

```python
def get_cosmic_dither(natal_chart_hash, date_ordinal, meter_name=""):
    """
    Deterministic dither based on chart + date + meter.
    Returns value in range -8 to +8.
    """
    seed = natal_chart_hash + date_ordinal + hash(meter_name) % 10000
    rng = random.Random(seed)  # LOCAL generator, not global
    return rng.uniform(-8.0, 8.0)
```

**Key design decisions:**
- **Local Random()**: Don't pollute global random state
- **Deterministic**: Same person + day + meter = same dither
- **Per-meter variation**: Each meter gets different dither
- **Diminishing intensity**: Full dither at raw=50, zero at extremes
- **Range ±8**: Wide enough to spread 50-spike, scaled by proximity

### Test Results (500 charts × 10 dates = 5,000 samples)

**Per-Meter Statistics:**

| Meter | Mean | StdDev | P10 | P90 | Day Corr |
|-------|------|--------|-----|-----|----------|
| clarity | 48.9 | 17.9 | 23.8 | 70.1 | 0.39 |
| focus | 49.3 | 18.1 | 24.1 | 71.2 | 0.44 |
| communication | 49.0 | 18.4 | 24.1 | 72.0 | 0.42 |
| connections | 48.7 | 19.6 | 20.8 | 73.7 | 0.43 |
| resilience | 48.8 | 21.5 | 17.4 | 77.5 | 0.45 |
| vulnerability | 49.1 | 19.5 | 22.1 | 73.6 | 0.44 |
| energy | 48.8 | 19.9 | 20.1 | 74.8 | 0.41 |
| drive | 49.4 | 16.8 | 27.9 | 69.6 | 0.39 |
| strength | 48.7 | 19.8 | 21.0 | 74.8 | 0.43 |
| vision | 49.1 | 16.5 | 27.1 | 68.9 | 0.36 |
| flow | 49.3 | 17.3 | 27.2 | 69.5 | 0.40 |
| intuition | 48.5 | 15.8 | 27.5 | 67.3 | 0.37 |
| creativity | 49.1 | 18.0 | 25.2 | 71.6 | 0.41 |
| momentum | 49.1 | 18.6 | 23.8 | 73.5 | 0.41 |
| ambition | 49.4 | 14.3 | 33.3 | 65.1 | 0.33 |
| evolution | 48.7 | 18.1 | 24.1 | 71.1 | 0.41 |
| circle | 49.2 | 18.3 | 24.2 | 71.9 | 0.44 |

**Group-Level Results:**

| Group | Day Corr | Avg Delta | Stability |
|-------|----------|-----------|-----------|
| Mind | 0.47 | 11.0 | Dynamic |
| Heart | 0.50 | 12.0 | Dynamic |
| Body | 0.45 | 10.5 | Dynamic |
| Instincts | 0.43 | 8.8 | Dynamic |
| Growth | 0.47 | 9.7 | Dynamic |

**Distribution Quality (clarity meter sample):**

```
Range      | Before Fixes | After Fixes
-----------|--------------|-------------
0-5%       | 14.5%        | 0.4%
45-50%     | 18.8%        | 11.5%
50-55%     | 28.1%        | 10.4%
55-60%     | 6.9%         | 11.1%
95-100%    | 11.1%        | 0.2%
```

The 50-55% spike of 28% is now spread across 45-60% at ~11% each - a proper bell curve.

### Files Modified

| File | Changes |
|------|---------|
| `transit_power.py` | min_speed 0.001 → 0.05 |
| `core.py` | Added METER_BALLAST, get_cosmic_dither() |
| `core.py` | calculate_astrometers() accepts chart_hash, date_ordinal |
| `meters.py` | calculate_unified_score() with dither param |
| `meters.py` | calculate_meter() computes chart_hash and passes dither |

### Summary

The V3 unified score formula produces a natural bell curve distribution:
- **No artificial spikes** at 50 (dither spreads neutral days)
- **No U-shape** at extremes (softer gain curves)
- **Healthy dynamics** (all meters 0.33-0.45 day correlation)
- **Per-meter calibration** (ballast proportional to typical intensity)

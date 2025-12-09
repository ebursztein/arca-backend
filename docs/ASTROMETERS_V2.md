# Astrometers Scoring

**Status:** Complete - All tests passing

---

## Summary

17 individual meters organized into 5 groups measure daily astrological energy through transit-to-natal aspects. Each meter filters aspects based on specific planets/houses and calculates:

- **Intensity** (0-100): How much is happening (magnitude)
- **Harmony** (0-100): Quality of what's happening (50 = neutral)
- **Unified Score** (0-100): Combined score where 50 = neutral, >50 = positive, <50 = challenging

---

## Score Ranges

| Metric | Range | Neutral | Notes |
|--------|-------|---------|-------|
| Intensity | 0-100 | N/A | Higher = more activity |
| Harmony | 0-100 | 50 | >50 = harmonious, <50 = challenging |
| Unified Score | 0-100 | 50 | >50 = positive day, <50 = challenging day |

---

## Algorithm Overview

### Core Formulas

```
DTI (Dual Transit Influence) = Sum(W_i * P_i)
HQS (Harmonic Quality Score) = Sum(W_i * P_i * Q_i)

Where:
- W_i = Weightage Factor (natal planet importance)
- P_i = Transit Power (aspect strength via Gaussian scoring)
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

### Transit Power (P_i) - Gaussian Scoring

Transit power uses time-normalized Gaussian decay based on planet velocity:

```python
# Gaussian scoring formula
sigma = window_days / 9.0  # SIGMA_DIVISOR = 9.0
deviation_days = deviation_deg / speed
intensity = exp(-(deviation_days ** 2) / (2 * sigma ** 2))
score = intensity * tier_weight * aspect_modifier
```

**Transit Tiers:**

| Tier | Planets | Window | Role |
|------|---------|--------|------|
| Trigger | Moon | 1 day | Daily variance |
| Event | Sun, Mercury, Venus, Mars | 4 days | Weekly rhythm |
| Season | Jupiter, Saturn | 45 days | Monthly context |
| Era | Uranus, Neptune, Pluto, Nodes | 100 days | Background influence |

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
def calculate_unified_score(intensity, harmony, dither=0.0):
    # Convert harmony (0-100) to coefficient (-1 to +1)
    harmony_coef = (harmony - 50) / 50

    # Step 1: Intensity stretch with moderate gain
    stretched_intensity = 100 * tanh(intensity / 60)

    # Step 2: Linear combination
    raw_unified = 50 + (stretched_intensity / 2) * harmony_coef

    # Step 2.5: Apply cosmic background dither
    # Full dither when neutral (raw=50), zero at extremes
    proximity_to_neutral = 1.0 - abs(raw_unified - 50) / 50
    scaled_dither = dither * max(0, proximity_to_neutral)
    raw_unified += scaled_dither

    # Step 3: Post-sigmoid stretch with headroom
    deviation = raw_unified - 50
    stretched = 50 * tanh(deviation / 25)
    unified_score = 50 + stretched

    return round(unified_score, 1)
    # Result: 0-100 with 50=neutral, >50=positive, <50=challenging
```

### Quality Labels

```python
if unified_score < 35:
    return "Challenging"  # Strong negative
elif unified_score < 50:
    return "Turbulent"    # Mild negative
elif unified_score < 70:
    return "Peaceful"     # Mild positive
else:
    return "Flowing"      # Strong positive
```

---

## Files Structure

| File | Description |
|------|-------------|
| `astrometers/core.py` | DTI/HQS calculation, Gaussian power |
| `astrometers/meters.py` | Meter filtering and reading |
| `astrometers/constants.py` | All algorithm constants |
| `astrometers/normalization.py` | Percentile normalization |
| `astrometers/hierarchy.py` | 17 meters, 5 groups enum |
| `astrometers/transit_power.py` | Gaussian/velocity scoring |
| `astrometers/labels/*.json` | Per-meter configs and labels |
| `astrometers/calibration/` | Calibration scripts and data |

---

## Key Constants Location

| Constant | File | Purpose |
|----------|------|---------|
| `PLANET_BASE_SCORES` | constants.py | W_i natal planet weights |
| `ASPECT_BASE_INTENSITY` | constants.py | P_i aspect type weights |
| `TRANSIT_PLANET_WEIGHTS` | constants.py | P_i transit planet modifier |
| `QUALITY_TRINE/SQUARE` | constants.py | Q_i base quality values |
| `BENEFIC_QUALITY_MULTIPLIER` | constants.py | Harmonic boost factor |
| `METER_BALLAST` | core.py | Per-meter ballast values |
| `GAUSSIAN_SIGMA_DIVISOR` | transit_power.py | Gaussian decay rate |

---

## Calibration Commands

```bash
# Re-run calibration (when meter filters change) - ~5-10 min
uv run python functions/astrometers/calibration/calculate_historical_v2.py

# Verify distribution quality (after calibration) - ~30 sec
uv run python functions/astrometers/calibration/verify_percentile.py

# Test meter overlap (after changing filters) - ~2-3 min
uv run python functions/astrometers/test_charts_stats_v2.py

# View meter configurations
uv run python functions/astrometers/show_meters.py
```

---

## Test Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `test_astrometer_distribution.py` | Cross-meter correlation | `uv run python tests/integration/test_astrometer_distribution.py -n 200 -m 5` |
| `test_astrometer_day_correlation.py` | Day-to-day stability | `uv run python tests/integration/test_astrometer_day_correlation.py -n 200 -d 10` |
| `calculate_historical_v2.py` | Re-calibrate percentiles | `uv run python astrometers/calibration/calculate_historical_v2.py` |
| `verify_percentile.py` | Verify calibration | `uv run python astrometers/calibration/verify_percentile.py` |

### Test Targets

**Cross-Meter Correlation:**
- Avg cross-meter |r| < 0.30 (meters are differentiated)
- Within-group > between-group correlation

**Day-to-Day Correlation:**
- Individual meter correlation 0.3-0.5 (healthy dynamics)
- No meter > 0.85 (too stable) or < 0.20 (too volatile)
- Avg daily |delta| 5-15 points

---

## Distribution Test Results

```
+--------------------------------+------------+------------+--------+
| Metric                         | Value      | Target     | Status |
+--------------------------------+------------+------------+--------+
| Avg Cross-Meter |Correlation|  |      0.207 | <0.30      |   PASS |
| Day-to-Day Correlation         |      0.41  | 0.3-0.5    |   PASS |
| Within-Group Avg |r|           |      0.387 | -          |  INFO  |
| Between-Group Avg |r|          |      0.220 | -          |  INFO  |
+--------------------------------+------------+------------+--------+
```

**Group-Level Results:**

| Group | Day Corr | Avg Delta | Stability |
|-------|----------|-----------|-----------|
| Mind | 0.47 | 11.0 | Dynamic |
| Heart | 0.50 | 12.0 | Dynamic |
| Body | 0.45 | 10.5 | Dynamic |
| Instincts | 0.43 | 8.8 | Dynamic |
| Growth | 0.47 | 9.7 | Dynamic |

---

## Per-Meter Filtering

Each meter filters aspects based on its configuration in `labels/*.json`:

```python
# Example: Clarity meter
natal_planets: ["mercury", "moon"]  # Only aspects TO these
# Transit planets: all allowed
# Aspect types: all allowed
```

---

## Per-Meter Ballast

Ballast prevents false harmony extremes on low-intensity days. Each meter has calibrated ballast based on its median intensity:

```python
METER_BALLAST = {
    "ambition": 10.9,
    "circle": 7.2,
    "clarity": 8.5,
    "communication": 3.9,
    "connections": 8.6,
    "creativity": 4.8,
    "drive": 14.7,
    "energy": 6.4,
    "evolution": 9.6,
    "flow": 2.1,
    "focus": 5.2,
    "intuition": 9.3,
    "momentum": 7.9,
    "resilience": 2.5,
    "strength": 10.5,
    "vision": 16.6,
    "vulnerability": 5.1,
}
```

---

## Cosmic Background Dither

Prevents exact-50 spike by simulating minor astrological influences:

```python
def get_cosmic_dither(natal_chart_hash, date_ordinal, meter_name=""):
    """
    Deterministic dither based on chart + date + meter.
    Returns value in range -8 to +8.
    """
    seed = natal_chart_hash + date_ordinal + hash(meter_name) % 10000
    rng = random.Random(seed)  # Local generator
    return rng.uniform(-8.0, 8.0)
```

- **Deterministic**: Same person + day + meter = same dither
- **Per-meter variation**: Each meter gets different dither
- **Diminishing intensity**: Full dither at raw=50, zero at extremes

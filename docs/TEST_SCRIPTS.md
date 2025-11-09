# Test Scripts Documentation

## Available Test Scripts

### 1. `test_v2_variation.py`
**What it does:**
- Runs 100 random charts × 7 days = 700 calculations
- Calls `get_meters()` twice for each: with `apply_harmonic_boost=False` and `apply_harmonic_boost=True`
- Collects harmony scores from all meters
- Reports harmony distribution in three categories: Challenging (< 30), Mixed (30-70), Harmonious (≥ 70)
- Shows percentage difference between the two scenarios

**Output:**
```
Category             NO Boost        WITH Boost      Change
Challenging (< 30)      34.5%          33.3%          -1.2%
Mixed (30-70)           40.1%          39.9%          -0.2%
Harmonious (≥ 70)       25.4%          26.7%          +1.4%
```

**Run:** `uv run python test_v2_variation.py`

---

### 2. `test_boost_raw_data.py`
**What it does:**
- Collects 500 chart-meter combinations
- Calls `calculate_meter()` twice on each: with `apply_harmonic_boost=False` and `apply_harmonic_boost=True`
- Calculates percentiles (P0, P5, P10... P100) for both distributions
- Shows difference at each percentile
- Counts exact values at boundaries (0.0 and 100.0)

**Output:**
```
Percentile | NO_BOOST | WITH_BOOST | DIFF
P  0       |     0.00 |       0.00 |   +0.00
P 50       |    49.41 |      51.25 |   +1.84
P100       |   100.00 |     100.00 |   +0.00

BOUNDARY COUNTS:
NO_BOOST  at 0.0:   93
NO_BOOST  at 100.0: 50
```

**Run:** `uv run python test_boost_raw_data.py`

---

### 3. `test_normalization_clamping.py`
**What it does:**
- Collects 1000 harmony scores (with boost enabled)
- Counts how many values are exactly 0.0 or 100.0
- Shows distribution in 10-point buckets
- Shows percentile table with floor/ceiling markers
- Reports total clamping percentage

**Output:**
```
Values at floor (0.0):     186 (18.6%)
Values at ceiling (100.0):  100 (10.0%)
TOTAL CLAMPED:             286 (28.6%)
```

**Run:** `uv run python test_normalization_clamping.py`

---

## What Each Script Tests

| Script | Tests | Use Case |
|--------|-------|----------|
| `test_v2_variation.py` | Harmony distribution shift | Compare boost ON vs OFF across categories |
| `test_boost_raw_data.py` | Percentile-level changes | See exact boost effect at every percentile |
| `test_normalization_clamping.py` | Boundary clamping | Check how much data hits 0 or 100 |

---

## Current Observations (2025-11-06)

**From `test_boost_raw_data.py`:**
- P0-P15: Values at 0.00 (floor)
- P20-P85: Boost shows +1 to +3 point increase
- P90-P100: Values at or near 100.00 (ceiling)
- 18.6% of values at 0.0
- 10% of values at 100.0
- Total clamping: 28.6%

**From `test_v2_variation.py`:**
- Boost reduces challenging from 34.5% → 33.3% (-1.2%)
- Boost increases harmonious from 25.4% → 26.7% (+1.4%)

**Clamping with p15-p85 window:**
- Expected: ~30% (15% each side)
- Observed: ~28-30%
- Question: Is this acceptable or should window be widened?

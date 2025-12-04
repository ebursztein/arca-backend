# Compatibility Scoring V2

**Date:** December 2025
**Status:** Complete - All tests passing

---

## Summary

Rewrote compatibility scoring to fix two major issues:
1. **Bimodal category scores** - 56% of scores were at extremes (-100 or +100)
2. **Karmic rate too high** - 50% of pairs flagged as karmic (should be ~5-10%)

---

## Final Test Results (25,000 pairs with Phase 2 smoothing)

```
+----------------------+------------+------------+--------+
| Metric               | Value      | Target     | Status |
+----------------------+------------+------------+--------+
| Overall Mean         |       54.0 | 45-55      |   PASS |
| Overall StdDev       |       11.0 | 10-20      |   PASS |
| Karmic Rate          |       7.8% | 5-10%      |   PASS |
| All Bimodality       |       <15% | <25%       |   PASS |
| Avg Correlation      |      0.129 | <0.30      |   PASS |
+----------------------+------------+------------+--------+

+------------------+--------+--------+---------+
| Category         |   Mean | Aspects| Extreme%|
+------------------+--------+--------+---------+
| attraction       |   10.4 |    4.3 |    7.6% |
| communication    |   12.8 |    4.7 |   11.0% |
| emotional        |    6.8 |    4.6 |    0.5% |
| growth           |    3.2 |    4.9 |    4.6% |
| longTerm         |    0.5 |    3.8 |    0.0% |
| values           |    8.9 |    4.7 |    3.5% |
+------------------+--------+--------+---------+
```

**Phase 2 improvements:**
- `longTerm` extremes fixed: 23.0% → 0.0%
- All categories under 12% extreme (was up to 23%)
- Low correlation (0.129) confirms categories measure different things

---

## What Was Changed

### 1. Category Scoring

**Problem:** Only 2-4 aspects per category caused extreme scores.

**Solution:**

#### A. Expanded planet pairs (`compatibility.py:159-238`)
- emotional: 14 pairs (was 5)
- communication: 15 pairs (was 5)
- attraction: 12 pairs (was 4)
- values: 15 pairs (was 7)
- longTerm: 10 pairs (was 7)
- growth: 18 pairs (was 10) - includes North AND South Node

#### B. Added aspect-type weights (`compatibility.py:63-72`)
```python
ASPECT_TYPE_WEIGHTS = {
    "conjunction": 1.2,  # Strongest
    "trine": 1.0,
    "opposition": 0.9,
    "square": 0.8,
    "sextile": 0.7,
    "quincunx": 0.6,     # Weakest
}
```

#### C. Added element compatibility (`compatibility.py:75-149`)
```python
# Applied to: emotional, attraction, values
ELEMENT_COMPATIBILITY = {
    ("fire", "fire"): 0.3,    # Same element
    ("fire", "air"): 0.2,     # Complementary
    ("fire", "water"): -0.2,  # Challenging
    # ... etc
}
```

#### D. Score Smoothing (Phase 2) (`compatibility.py:152-313`)

Replaced hard clamping with sigmoid smoothing + chart-based variation:

**Problem:** Hard clamp at [-85, +85] created distribution spikes at extremes.

**Solution:** Each category uses:
1. **Chart-based variation** - deterministic offset based on category-relevant planets
2. **Sigmoid compression** - smooth mapping to bounded range (no hard edges)

```python
CATEGORY_SMOOTHING_CONFIG = {
    "attraction": {"planets": ["venus", "mars"], "steepness": 0.028, "max_var": 12},
    "communication": {"planets": ["mercury"], "steepness": 0.030, "max_var": 8},
    "emotional": {"planets": ["moon"], "steepness": 0.025, "max_var": 10},
    "longTerm": {"planets": ["saturn"], "steepness": 0.022, "max_var": 15},
    "growth": {"planets": ["jupiter", "north node"], "steepness": 0.030, "max_var": 8},
    "values": {"planets": ["sun", "venus"], "steepness": 0.028, "max_var": 10},
}

# Order: variation first, then sigmoid
adjusted = raw_score + chart_variation(user_chart, conn_chart, category)
smoothed = sigmoid_compress(adjusted, steepness)
```

**Results:**
- Extreme bucket (top/bottom 5%) reduced from 12-15% to <2%
- `longTerm` bimodality fixed (23.5% extremes → 5%)
- Correlations maintained at 0.13 (categories stay independent)

### 2. Karmic Detection

**Problem:** 50% karmic rate - too common to feel special.

**Solution:** Complete rewrite (`compatibility.py:883-1015`)

#### Final Configuration
```python
# Planets
KARMIC_TIER1_PLANETS = {"sun", "moon", "saturn", "pluto"}  # Badge-level
KARMIC_TIER2_PLANETS = {"venus", "mars", "mercury"}        # Flavor only

# Orbs (very tight)
KARMIC_TIER1_ORB = 1.0   # Sun, Moon, Saturn
KARMIC_PLUTO_ORB = 0.75  # Pluto
KARMIC_TIER2_ORB = 0.75  # Venus, Mars, Mercury

# Badge requirement
KARMIC_BADGE_THRESHOLD = 2  # Need 2+ Tier-1 primary aspects

# Aspects
KARMIC_PRIMARY_ASPECTS = {"conjunction", "opposition"}  # Count toward badge
KARMIC_SECONDARY_ASPECTS = {"square"}  # Saturn/Pluto only, flavor
```

#### What's Checked
- **Both nodes:** North Node AND South Node
- **Both directions:** User's planets → Connection's nodes AND Connection's planets → User's nodes
- **4 total checks:** user_north, user_south, conn_north, conn_south

#### Karmic Themes
```python
KARMIC_NORTH_HINTS = {
    "sun": "This relationship pulls you toward your future identity",
    "moon": "Destined emotional growth",
    # ...
}

KARMIC_SOUTH_HINTS = {
    "sun": "Deep past-life recognition",
    "moon": "Uncanny emotional safety - feels like you've always known each other",
    # ...
}
```

Theme generation:
- North Node aspect → "Fated growth through {planet}"
- South Node aspect → "Past-life bond through {planet}"
- Square aspect → "Karmic tension through {planet}"

---

## Algorithm Details

### Category Score Calculation

```python
for each aspect matching category's planet pairs:
    orb_weight = get_orb_weight(aspect.orb)  # 1.0 to 0.25
    aspect_weight = ASPECT_TYPE_WEIGHTS[aspect.aspect_type]
    base_harmony = +1 if harmonious else -1
    contribution = base_harmony * aspect_weight * orb_weight
    total_score += contribution
    total_weight += aspect_weight * orb_weight

# Element bonus for emotional/attraction/values
if category uses elements:
    element_score = get_element_score(chart1, chart2, element_pairs)
    total_score += element_score
    total_weight += 0.3  # Always add for stability

# Normalize and apply Phase 2 smoothing
normalized = (total_score / total_weight) * 100
variation = chart_variation(chart1, chart2, category)  # Based on category planets
adjusted = normalized + variation
smoothed = sigmoid_compress(adjusted, steepness=category_config["steepness"])
# Result is naturally bounded to ~[-85, +85] by sigmoid
```

### Karmic Detection

```python
for each of 4 node combinations (user_north, user_south, conn_north, conn_south):
    for each planet in TIER1 + TIER2:
        check conjunction and opposition
        if orb <= threshold:
            add to primary_aspects (if Tier1) or secondary_aspects

tier1_count = count aspects where planet in TIER1
is_karmic = (tier1_count >= 2)
```

---

## Files Changed

| File | Description |
|------|-------------|
| `compatibility.py` | Main implementation (~200 lines changed) |
| `tests/unit/test_compatibility.py` | Updated tests for new constants |
| `tests/integration/test_compatibility_distribution.py` | Statistical test script |

---

## Test Commands

```bash
# Quick distribution test (2 min)
uv run python tests/integration/test_compatibility_distribution.py -n 100 -m 25

# Full distribution test (10 min)
uv run python tests/integration/test_compatibility_distribution.py -n 500 -m 20

# Unit tests
uv run pytest tests/unit/test_compatibility.py -v

# All unit tests
uv run pytest tests/unit/ -v
```

---

## Key Constants Location

| Constant | Line | Purpose |
|----------|------|---------|
| `ASPECT_TYPE_WEIGHTS` | 65 | Aspect strength weights |
| `ELEMENT_COMPATIBILITY` | 85 | Element pairing scores |
| `CATEGORY_ELEMENT_PAIRS` | 108 | Which categories use elements |
| `ROMANTIC_CATEGORIES` | 160 | Planet pairs per category |
| `KARMIC_TIER1_PLANETS` | 816 | Badge-level planets |
| `KARMIC_TIER1_ORB` | 820 | Orb thresholds |
| `KARMIC_BADGE_THRESHOLD` | 833 | Aspects needed for badge |
| `KARMIC_NORTH_HINTS` | 836 | North Node interpretations |
| `KARMIC_SOUTH_HINTS` | 847 | South Node interpretations |

---

## Potential Future Improvements

1. **House overlays** - Venus in partner's 7th house bonus
2. **Weighted planet pairs** - Sun-Moon more important than Mercury-Uranus
3. **Aspect pattern detection** - Grand trines, T-squares
4. **A/B testing** - Tune weights based on user feedback

---

## How to Adjust Rates

### If karmic rate too high:
- Decrease `KARMIC_TIER1_ORB` (currently 1.0°)
- Increase `KARMIC_BADGE_THRESHOLD` (currently 2)

### If karmic rate too low:
- Increase `KARMIC_TIER1_ORB`
- Decrease `KARMIC_BADGE_THRESHOLD` to 1

### If category too bimodal:
- Add more planet pairs to that category
- Check aspect count is 4.5+ average

### If overall scores too clustered:
- Adjust `ASPECT_TYPE_WEIGHTS` spread
- Modify element compatibility values

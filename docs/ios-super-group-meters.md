# iOS Integration Guide: Super-Group Astrometers

**Version:** 1.1
**Date:** October 30, 2025
**Status:** ✅ Production Ready

## 🆕 What's New in v1.1 (October 30, 2025)

**Rich Trend Analysis with Empirical Thresholds!**

All 28 meters (23 individual + 5 super-groups) now include comprehensive trend analysis tracking **harmony, intensity, and unified_score** separately with scientifically-derived thresholds.

**Key Changes:**
- ✅ `trend` field is now a **rich object** (was previously simple string or null)
- ✅ Tracks **3 metrics separately**: harmony (quality), intensity (activity), unified_score (combined)
- ✅ Each metric has: `previous`, `delta`, `direction`, `change_rate`
- ✅ **Empirically-derived thresholds** based on 855,000 daily transitions across 2,500 birth charts
- ✅ Four granular change rates: `stable`, `slow`, `moderate`, `rapid` (based on quantiles)
- ✅ Automatic calculation - no additional API calls needed
- ✅ Available in all responses: `get_daily_horoscope()`, `get_detailed_horoscope()`, `get_astrometers()`

**Migration Impact:**
- **Breaking Change** - `trend` is now an object, not a string
- Previously: `trend: "worsening"` (simple)
- Now: `trend: { harmony: {...}, intensity: {...}, unified_score: {...} }` (rich)
- **Required Action:** Update Swift models to parse new `TrendData` structure

---

## Overview

The backend now returns **28 astrometers** (previously 23) in all horoscope responses. This document explains the 5 new **super-group aggregate meters** designed specifically for high-level iOS dashboard display.

### What Are Super-Group Meters?

Super-group meters are **aggregate scores** that combine multiple individual meters into a single metric for each major life domain. They provide a simplified, high-level view of the user's astrological landscape.

**Purpose:**
- Simplify complex astrological data for dashboard views
- Provide quick, at-a-glance insights for 5 major life areas
- Maintain full detail through underlying individual meters

---

## The 5 Super-Groups

### 1. Overview Super-Group
**Meter ID:** `overview_super_group`
**Aggregates:** 2 meters (overall_intensity, overall_harmony)
**Description:** Highest-level dashboard summary of total cosmic activity and quality

**Use Case:** Main dashboard hero section - "How is your day overall?"

**Member Meters:**
- `overall_intensity` (weight: 2.0)
- `overall_harmony` (weight: 2.0)

---

### 2. Inner World Super-Group
**Meter ID:** `inner_world_super_group`
**Aggregates:** 6 meters (3 Mind + 3 Emotions)
**Description:** Internal subjective experience—thoughts, feelings, psychological state

**Use Case:** Dashboard card for mental/emotional wellness - "How clear is your mind and how are you feeling?"

**Member Meters:**
- **Mind Group:**
  - `mental_clarity` (weight: 2.0)
  - `decision_quality` (weight: 1.5)
  - `communication_flow` (weight: 1.5)
- **Emotions Group:**
  - `emotional_intensity` (weight: 2.0)
  - `relationship_harmony` (weight: 1.5)
  - `emotional_resilience` (weight: 1.5)

---

### 3. Outer World Super-Group
**Meter ID:** `outer_world_super_group`
**Aggregates:** 5 meters (3 Body + 2 Career)
**Description:** Engagement with external reality—action, physical vitality, professional drive, opportunities

**Use Case:** Dashboard card for action/career - "What can you DO in the world right now?"

**Member Meters:**
- **Body Group:**
  - `physical_energy` (weight: 2.0)
  - `conflict_risk` (weight: 1.0)
  - `motivation_drive` (weight: 1.5)
- **Career Group:**
  - `career_ambition` (weight: 2.0)
  - `opportunity_window` (weight: 1.5)

---

### 4. Evolution Super-Group
**Meter ID:** `evolution_super_group`
**Aggregates:** 3 meters
**Description:** Growth through difficulty—friction that creates diamonds, forced transformation, breakthroughs

**Use Case:** Dashboard card for personal growth - "Where is pressure catalyzing your evolution?"

**Member Meters:**
- `challenge_intensity` (weight: 1.5)
- `transformation_pressure` (weight: 1.5)
- `innovation_breakthrough` (weight: 1.0)

---

### 5. Deeper Dimensions Super-Group
**Meter ID:** `deeper_dimensions_super_group`
**Aggregates:** 7 meters (4 Elements + 2 Spiritual + 1 Collective)
**Description:** Foundational energies—elemental temperament, spiritual awareness, karmic themes, collective currents

**Use Case:** Dashboard card for spiritual depth - "What deeper energies are at play?"

**Member Meters:**
- **Elements Group:**
  - `fire_energy` (weight: 0.7)
  - `earth_energy` (weight: 0.7)
  - `air_energy` (weight: 0.7)
  - `water_energy` (weight: 0.7)
- **Spiritual Group:**
  - `intuition_spirituality` (weight: 1.0)
  - `karmic_lessons` (weight: 1.0)
- **Collective Group:**
  - `social_collective` (weight: 0.5)

---

## Data Structure

### Complete Super-Group Meter Object

```json
{
  "meter_name": "inner_world_super_group",
  "date": "2025-10-30T17:39:09.827533",
  "group": "overview",

  "unified_score": 49.2,
  "unified_quality": "mixed",

  "intensity": 49.2,
  "harmony": 47.1,
  "state_label": "Quiet Blend",

  "interpretation": "This meter shows how clear your thinking is and how you're feeling inside, indicating your overall inner state. This aggregate meter reflects the activity of inner planets like Mercury (for mind) and the Moon/Venus (for emotions)...",

  "advice": [
    "Advice type: Quiet observation"
  ],

  "top_aspects": [
    {
      "transit_planet": "jupiter",
      "natal_planet": "saturn",
      "aspect_type": "opposition",
      "orb": 0.8,
      "applying": true,
      "exact_date": "2025-10-28",
      "weightage": 20.0,
      "transit_power": 12.5,
      "quality_factor": -1.0,
      "dti_contribution": 249.9,
      "hqs_contribution": -249.9,
      "label": "Transit Jupiter Opposition Natal Saturn"
    }
  ],

  "raw_scores": {
    "dti": 663.66,
    "hqs": -19.26,
    "member_count": 6
  },

  "additional_context": {
    "super_group": "inner_world",
    "member_meters": [
      "mental_clarity",
      "decision_quality",
      "communication_flow",
      "emotional_intensity",
      "relationship_harmony",
      "emotional_resilience"
    ],
    "aggregation_method": "weighted_average"
  },

  "trend": {
    "harmony": {
      "previous": 60.3,
      "delta": -11.1,
      "direction": "worsening",
      "change_rate": "rapid"
    },
    "intensity": {
      "previous": 51.7,
      "delta": 4.6,
      "direction": "increasing",
      "change_rate": "slow"
    },
    "unified_score": {
      "previous": 54.8,
      "delta": -5.8,
      "direction": "decreasing",
      "change_rate": "rapid"
    }
  }
}
```

---

## Field Descriptions

### Core Display Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `unified_score` | Float | -100 to +100 | **Primary display value** - Bipolar scale (positive = harmonious, negative = challenging). See unified-score-guide.md |
| `unified_quality` | String | enum | Quality label: "quiet", "peaceful", "harmonious", "mixed", "challenging" |
| `intensity` | Float | 0-100 | How much is happening (activity level) |
| `harmony` | Float | 0-100 | Quality of what's happening (supportive vs challenging) |
| `state_label` | String | - | Human-readable state: "Quiet Blend", "Gentle Flow", etc. |

### Content Fields

| Field | Type | Description |
|-------|------|-------------|
| `interpretation` | String | 2-3 sentence explanation of what this super-group measures |
| `advice` | Array[String] | Actionable guidance (currently shows advice type) |
| `top_aspects` | Array[AspectContribution] | Top 5 transit aspects affecting this super-group |

### Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `raw_scores.member_count` | Int | Number of individual meters aggregated (2, 3, 5, 6, or 7) |
| `additional_context.super_group` | String | Super-group identifier |
| `additional_context.member_meters` | Array[String] | List of aggregated meter IDs |
| `additional_context.aggregation_method` | String | Always "weighted_average" |

---

## Trend Data Structure

### Overview

Each meter now includes a `trend` object that tracks changes for all three key scores separately. This allows for nuanced analysis - for example, a meter might have increasing activity (intensity ↑) but worsening quality (harmony ↓).

### TrendData Object

```typescript
{
  "harmony": MetricTrend,       // Quality: How good/bad things are
  "intensity": MetricTrend,     // Activity: How much is happening
  "unified_score": MetricTrend  // Combined: Overall meter value
}
```

### MetricTrend Object

Each metric trend has:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `previous` | Float | Yesterday's value (0-100) | `60.3` |
| `delta` | Float | Change from yesterday (+ = increase, - = decrease) | `-11.1` |
| `direction` | String | Direction of change (see below) | `"worsening"` |
| `change_rate` | String | Magnitude classification (see below) | `"rapid"` |

### Direction Values

**For Harmony:**
- `"improving"` - Quality getting better (δ >= 2.0)
- `"stable"` - No significant change (-2.0 < δ < 2.0)
- `"worsening"` - Quality getting worse (δ <= -2.0)

**For Intensity & Unified Score:**
- `"increasing"` - Value going up (δ >= 2.0 or 0.5)
- `"stable"` - No significant change
- `"decreasing"` - Value going down (δ <= -2.0 or -0.5)

### Change Rate Values (Empirically-Derived)

Based on quantile analysis of 855,000 daily transitions:

| Rate | Harmony | Intensity | Unified | Frequency | UI Suggestion |
|------|---------|-----------|---------|-----------|---------------|
| `stable` | < 2.0 | < 2.0 | < 0.5 | 50% | → (neutral) |
| `slow` | 2.0-5.5 | 2.0-5.0 | 0.5-2.5 | 25% | ⟶ (slight arrow) |
| `moderate` | 5.5-10.5 | 5.0-9.5 | 2.5-5.5 | 15% | ↑/↓ (clear arrow) |
| `rapid` | > 10.5 | > 9.5 | > 5.5 | 10% | ↑↑/↓↓ (double arrow) |

**Why different thresholds?**
Each metric changes at different rates. Unified score is a combined metric so it changes less dramatically. Using metric-specific thresholds ensures consistent user experience - a "moderate" change feels significant regardless of which metric.

### Usage Examples

**Example 1: Challenging but Improving**
```json
"trend": {
  "harmony": {
    "previous": 35.2,
    "delta": 8.3,
    "direction": "improving",
    "change_rate": "moderate"
  }
}
```
→ UI: Show green ↑ with "+8.3" or "Improving moderately"

**Example 2: Active but Quality Dropping**
```json
"trend": {
  "harmony": {"delta": -12.1, "direction": "worsening", "change_rate": "rapid"},
  "intensity": {"delta": 6.2, "direction": "increasing", "change_rate": "moderate"}
}
```
→ UI: Warn user - high activity but difficult conditions

**Example 3: Stable Day**
```json
"trend": {
  "harmony": {"delta": 0.8, "direction": "stable", "change_rate": "stable"},
  "intensity": {"delta": -1.2, "direction": "stable", "change_rate": "stable"}
}
```
→ UI: Show → (similar to yesterday)

---

## Firebase Integration

### Response Location

Super-group meters are included in **all horoscope responses**:

#### 1. `get_daily_horoscope()`
```swift
let response = try await functions.httpsCallable("get_daily_horoscope").call([
    "user_id": userId,
    "date": "2025-10-30"
])

let horoscope = // Parse DailyHoroscope
let innerWorld = horoscope.astrometers.inner_world_super_group
```

#### 2. `get_detailed_horoscope()`
```swift
let response = try await functions.httpsCallable("get_detailed_horoscope").call([
    "user_id": userId,
    "date": "2025-10-30"
])

let horoscope = // Parse DetailedHoroscope
let evolution = horoscope.astrometers.evolution_super_group
```

#### 3. `get_astrometers()`
```swift
let response = try await functions.httpsCallable("get_astrometers").call([
    "user_id": userId,
    "date": "2025-10-30"
])

let astrometers = // Parse AllMetersReading
let overview = astrometers.overview_super_group
```

---

## Swift Model Example

```swift
// Super-group meter model
struct SuperGroupMeter: Codable {
    let meterName: String
    let date: Date
    let group: String

    // Core display values
    let unifiedScore: Double
    let unifiedQuality: QualityLabel
    let intensity: Double
    let harmony: Double
    let stateLabel: String

    // Content
    let interpretation: String
    let advice: [String]
    let topAspects: [AspectContribution]

    // Metadata
    let rawScores: RawScores
    let additionalContext: AdditionalContext
    let trend: TrendData?  // NEW: Rich trend object

    enum CodingKeys: String, CodingKey {
        case meterName = "meter_name"
        case date
        case group
        case unifiedScore = "unified_score"
        case unifiedQuality = "unified_quality"
        case intensity
        case harmony
        case stateLabel = "state_label"
        case interpretation
        case advice
        case topAspects = "top_aspects"
        case rawScores = "raw_scores"
        case additionalContext = "additional_context"
        case trend
    }
}

// NEW: Trend data models
struct TrendData: Codable {
    let harmony: MetricTrend
    let intensity: MetricTrend
    let unifiedScore: MetricTrend

    enum CodingKeys: String, CodingKey {
        case harmony
        case intensity
        case unifiedScore = "unified_score"
    }
}

struct MetricTrend: Codable {
    let previous: Double
    let delta: Double
    let direction: TrendDirection
    let changeRate: ChangeRate

    enum CodingKeys: String, CodingKey {
        case previous
        case delta
        case direction
        case changeRate = "change_rate"
    }
}

enum TrendDirection: String, Codable {
    case improving      // Harmony: getting better
    case stable         // No significant change
    case worsening      // Harmony: getting worse
    case increasing     // Intensity/Unified: going up
    case decreasing     // Intensity/Unified: going down
}

enum ChangeRate: String, Codable {
    case stable     // < 50th percentile (most common)
    case slow       // 50th-75th percentile (typical)
    case moderate   // 75th-90th percentile (significant)
    case rapid      // > 90th percentile (dramatic, top 10%)
}

struct RawScores: Codable {
    let dti: Double
    let hqs: Double
    let memberCount: Int

    enum CodingKeys: String, CodingKey {
        case dti
        case hqs
        case memberCount = "member_count"
    }
}

struct AdditionalContext: Codable {
    let superGroup: String
    let memberMeters: [String]
    let aggregationMethod: String

    enum CodingKeys: String, CodingKey {
        case superGroup = "super_group"
        case memberMeters = "member_meters"
        case aggregationMethod = "aggregation_method"
    }
}

enum QualityLabel: String, Codable {
    case quiet
    case peaceful
    case harmonious
    case mixed
    case challenging
}

// Extend existing astrometers model
struct AllMetersReading: Codable {
    // ... existing 23 individual meters

    // NEW: Super-group meters (optional for backward compatibility)
    let overviewSuperGroup: SuperGroupMeter?
    let innerWorldSuperGroup: SuperGroupMeter?
    let outerWorldSuperGroup: SuperGroupMeter?
    let evolutionSuperGroup: SuperGroupMeter?
    let deeperDimensionsSuperGroup: SuperGroupMeter?

    enum CodingKeys: String, CodingKey {
        // ... existing keys
        case overviewSuperGroup = "overview_super_group"
        case innerWorldSuperGroup = "inner_world_super_group"
        case outerWorldSuperGroup = "outer_world_super_group"
        case evolutionSuperGroup = "evolution_super_group"
        case deeperDimensionsSuperGroup = "deeper_dimensions_super_group"
    }
}
```

---

## UI Display Recommendations

### NEW: Trend Indicators


func trendIcon(_ trend: MetricTrend) -> String {
    switch (trend.direction, trend.changeRate) {
    case (.improving, .rapid), (.increasing, .rapid):
        return "arrow.up.circle.fill"  // ↑↑
    case (.improving, .moderate), (.increasing, .moderate):
        return "arrow.up.circle"       // ↑
    case (.worsening, .rapid), (.decreasing, .rapid):
        return "arrow.down.circle.fill" // ↓↓
    case (.worsening, .moderate), (.decreasing, .moderate):
        return "arrow.down.circle"      // ↓
    default:
        return "arrow.left.arrow.right" // →
    }
}


---

## FAQ

### Q: Are super-group meters replacing individual meters?
**A:** No. Super-groups are **additions** for simplified dashboard display. All 23 individual meters remain available for detailed analysis.

### Q: How are super-group scores calculated?
**A:** Weighted average of member meters using importance weights:
- High importance meters (2.0): mental_clarity, emotional_intensity, physical_energy, career_ambition
- Medium importance (1.0-1.5): Most other meters
- Low importance (0.5-0.7): Element meters, collective meter

### Q: Can I drill down from super-groups to individual meters?
**A:** Yes! The `additional_context.member_meters` array lists all individual meters that compose each super-group.

### Q: What's the difference between `intensity` and `unified_score`?
**A:**
- `intensity`: How much activity (0-100, always positive)
- `harmony`: Quality of activity (0-100, where 50 is neutral)
- `unified_score`: Combined metric (uses intensity as magnitude, harmony as quality)

**For UI:** Use `unified_score` as the primary display value.

### Q: Do super-groups have trends like individual meters?
**A:** Yes! As of v1.1 (Oct 2025), all 28 meters (23 individual + 5 super-groups) include full trend analysis automatically.

### Q: What changed with trends in v1.1?
**A:** Major upgrade:
- **Before:** Simple string (`"improving"`, `"stable"`, `"worsening"`) or `null`
- **Now:** Rich object tracking harmony, intensity, and unified_score separately with empirical thresholds
- **Why:** Allows nuanced analysis - e.g., "Activity increasing but quality dropping"
- **Thresholds:** Based on real data (855K daily transitions), not arbitrary numbers



### Q: What do the change_rate values mean?
**A:** Empirically-derived from 2,500 birth charts:
- `stable` (50%): < 2 points - typical background fluctuation
- `slow` (25%): 2-6 points - gentle noticeable shift
- `moderate` (15%): 6-11 points - clear significant change
- `rapid` (10%): > 11 points - dramatic shift, use double arrows (↑↑/↓↓)

---

## Testing

### Local Testing with Emulator

```bash
# Backend
cd functions
uv run python astrometers/show_meters.py

# You'll see all 28 meters displayed, including the 5 super-groups at the end
```

### Firebase Functions Testing

```swift
// Test in Xcode with Firebase emulator
let functions = Functions.functions(region: "us-central1")
functions.useEmulator(withHost: "localhost", port: 5001)

let result = try await functions.httpsCallable("get_daily_horoscope").call([
    "user_id": "test_user_id",
    "date": "2025-10-30"
])

// Verify super-group meters exist
let data = result.data as? [String: Any]
let astrometers = data?["astrometers"] as? [String: Any]
let innerWorld = astrometers?["inner_world_super_group"] as? [String: Any]

print("Inner World Unified Score: \(innerWorld?["unified_score"])")
```

---

## Summary

### What Changed
✅ Backend now calculates 28 meters (23 individual + 5 super-group)
✅ All Firebase functions automatically include super-group meters
✅ Backward compatible - existing code continues to work
✅ Super-groups use weighted averaging for intelligent aggregation
✅ Each super-group has complete interpretation, advice, and top aspects

### Next Steps for iOS
1. Update Swift models to include optional super-group fields
2. Create dashboard views using super-group meters
3. Implement drill-down navigation to individual meters
4. Test with Firebase emulator and production

### Questions?
Contact the backend team or refer to:
- `docs/astrometers.md` - Complete astrometer specification
- `functions/astrometers/hierarchy.py` - Super-group definitions
- `functions/astrometers/meters.py` - Calculation logic

---

**Document Version:** 1.0
**Last Updated:** October 30, 2025
**Status:** ✅ Production Ready

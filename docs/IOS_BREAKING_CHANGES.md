# iOS Breaking Changes - Astrometers API

**Date**: 2025-01-08
**Impact**: Breaking - Type changes in `AstrometersForIOS`

## Changes Required

### 1. `overall_intensity` and `overall_harmony` type change

**Before:**
```swift
struct AstrometersForIOS {
    let overallIntensity: Double
    let overallHarmony: Double
}
```

**After:**
```swift
struct AstrometersForIOS {
    let overallIntensity: MeterReading
    let overallHarmony: MeterReading
}
```

### 2. Code Migration

**Old code (breaks):**
```swift
let intensity = horoscope.astrometers.overallIntensity
let harmony = horoscope.astrometers.overallHarmony
```

**New code:**
```swift
let intensity = horoscope.astrometers.overallIntensity.intensity
let harmony = horoscope.astrometers.overallHarmony.harmony
```

### 3. Additional fields now available

```swift
// State labels (new)
let intensityLabel = horoscope.astrometers.overallIntensity.stateLabel
let harmonyLabel = horoscope.astrometers.overallHarmony.stateLabel

// Unified scores
let intensityUnified = horoscope.astrometers.overallIntensity.unifiedScore
let harmonyUnified = horoscope.astrometers.overallHarmony.unifiedScore
```

## Sample JSON

**Before:**
```json
{
  "overall_intensity": 75.3,
  "overall_harmony": 82.1
}
```

**After:**
```json
{
  "overall_intensity": {
    "meter_name": "overall_intensity",
    "intensity": 75.3,
    "harmony": 82.1,
    "state_label": "Intense activity",
    "unified_score": 78.7,
    "unified_quality": "harmonious"
  },
  "overall_harmony": {
    "meter_name": "overall_harmony",
    "intensity": 75.3,
    "harmony": 82.1,
    "state_label": "Strong support",
    "unified_score": 78.7,
    "unified_quality": "harmonious"
  }
}
```

## Search & Replace

Find all occurrences of:
- `.overallIntensity` → `.overallIntensity.intensity`
- `.overallHarmony` → `.overallHarmony.harmony`

Except when accessing other fields like `.stateLabel`, `.unifiedScore`, etc.

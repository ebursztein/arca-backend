# Unified Score Guide for iOS

**Last Updated:** 2025-11-27

## TL;DR

| Field | Range | What It Means |
|-------|-------|---------------|
| `unified_score` | **-100 to +100** | Bipolar scale: positive = good day, negative = challenging day |
| `intensity` | 0 to 100 | How much is happening (activity level) |
| `harmony` | 0 to 100 | Quality of what's happening (50 = neutral) |

**Key Point:** `unified_score` is NOT 0-100. It's a signed value from -100 to +100.

---

## Why Can't We Use a Circle?

A circle (0-360 degrees or 0-100%) represents a **unipolar scale** - values go from zero to maximum.

`unified_score` is a **bipolar scale** - values can be positive or negative:
- **+100** = Extremely harmonious/supportive energy
- **0** = Neutral/mixed energy
- **-100** = Extremely challenging energy

Think of it like a **thermometer** or **gauge**, not a pie chart or progress ring.

---

## Visual Representation Options

### Option 1: Horizontal Bar (Recommended)
```
Challenging          Neutral          Harmonious
    |-------------------|-------------------|
   -100                 0                 +100
                        ^
                   [unified_score]
```

### Option 2: Vertical Gauge
```
    +100  Harmonious
      |
      |   [indicator]
      |
       0  Neutral
      |
      |
   -100  Challenging
```

### Option 3: Color Gradient
Map the score to a color gradient:
- -100 to -25: Red/Orange tones (Challenging)
- -25 to +25: Yellow/Neutral tones (Turbulent/Mixed)
- +25 to +75: Light green tones (Peaceful)
- +75 to +100: Bright green tones (Flowing)

### Option 4: Two Separate Bars
Display `intensity` and `harmony` as two separate 0-100 bars if you prefer unipolar scales.

---

## The Three Scores Explained

### 1. Intensity (0-100)
**What:** How much astrological activity is happening.
**Range:** 0 (quiet) to 100 (very active)
**UI:** Can use a simple progress bar or circle

```
Low Activity                    High Activity
    |===========================|
    0                          100
```

### 2. Harmony (0-100)
**What:** The quality of what's happening - supportive vs challenging.
**Range:** 0 (challenging) to 100 (supportive), with 50 being neutral
**UI:** Can use a progress bar, but note that 50 is the "neutral" midpoint

```
Challenging        Neutral        Supportive
    |===============|===============|
    0               50             100
```

### 3. Unified Score (-100 to +100)
**What:** A combined metric that factors in both intensity and harmony.
**Range:** -100 (intensely challenging) to +100 (intensely supportive)
**Formula:** Harmony sets the direction, intensity amplifies it

```
Intensely         Neutral        Intensely
Challenging                      Supportive
    |===============|===============|
  -100              0             +100
```

---

## How Unified Score is Calculated

```
1. Harmony determines direction:
   - Harmony > 50 = positive direction
   - Harmony < 50 = negative direction
   - Harmony = 50 = neutral (near zero)

2. Intensity amplifies the signal:
   - High intensity = stronger positive or negative
   - Low intensity = closer to zero regardless of harmony

3. Result is stretched using sigmoid (tanh) for better distribution

4. Empowering asymmetry applied:
   - Positive values boosted by 1.2x
   - Negative values dampened by 0.7x
   - Results in ~70% positive / ~30% negative distribution
```

### Example Values

| Intensity | Harmony | Unified Score | Meaning |
|-----------|---------|---------------|---------|
| 80 | 85 | +72 | Very active, very harmonious |
| 80 | 15 | -35 | Very active, very challenging |
| 20 | 85 | +21 | Quiet, but harmonious |
| 20 | 15 | -8 | Quiet, slightly challenging |
| 50 | 50 | 0 | Neutral activity, neutral quality |

---

## State Labels (Buckets)

The `state_label` field maps unified_score to human-readable text:

| Unified Score Range | State Label | Meaning |
|---------------------|-------------|---------|
| < -25 | "Challenging" | Push through it |
| -25 to +10 | "Turbulent" | Mixed energy, stay flexible |
| +10 to +50 | "Peaceful" | Supportive energy |
| >= +50 | "Flowing" | Excellent energy |

---

## Swift Model

```swift
struct MeterScores {
    /// Bipolar scale: -100 (challenging) to +100 (harmonious)
    /// NOT 0-100! Use for gauge/thermometer visualization
    let unifiedScore: Double  // Range: -100 to +100

    /// Activity level - how much is happening
    /// Standard 0-100 scale, can use progress bar
    let intensity: Double     // Range: 0 to 100

    /// Quality of energy - supportive vs challenging
    /// 0-100 scale where 50 is neutral
    let harmony: Double       // Range: 0 to 100
}

// Example: Map unified_score to color
func colorForUnifiedScore(_ score: Double) -> Color {
    switch score {
    case ..<(-25):
        return .orange  // Challenging
    case -25..<10:
        return .yellow  // Turbulent
    case 10..<50:
        return .mint    // Peaceful
    default:
        return .green   // Flowing
    }
}

// Example: Position on horizontal bar (normalized to 0-1)
func normalizedPosition(_ score: Double) -> Double {
    // Convert -100...+100 to 0...1
    return (score + 100) / 200
}
```

---

## FAQ

### Q: Why not just use 0-100?
**A:** We need to distinguish between "challenging" and "harmonious" energy. A score of 30 on a 0-100 scale is ambiguous - is it low-good or low-bad? With -100 to +100, negative = challenging, positive = harmonious.

### Q: Can I just add 100 to make it 0-200?
**A:** You could for positioning math, but preserve the signed semantics in your UI. Users should understand that negative means challenging energy.

### Q: What's the typical distribution?
**A:** Due to empowering asymmetry:
- ~70% of scores are positive (0 to +100)
- ~30% of scores are negative (-100 to 0)
- Average is around +20

### Q: Should I show the raw number to users?
**A:** Use the `state_label` ("Flowing", "Peaceful", "Turbulent", "Challenging") for user-facing text. The number is for visualization (bar position, color intensity).

---

## Summary

| Don't Do | Do Instead |
|----------|------------|
| Display unified_score in a circle/pie | Use a horizontal bar, gauge, or color gradient |
| Treat it as 0-100 | Treat it as -100 to +100 (signed) |
| Show raw number to users | Show `state_label` with visual indicator |

**Questions?** Reach out to the backend team.

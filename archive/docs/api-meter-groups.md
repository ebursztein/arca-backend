# API Specification: Meter Groups

**Version**: 1.0
**Last Updated**: 2025-11-02
**Status**: done

## Overview

This document specifies the updated `/daily-horoscope` endpoint that includes 5 meter groups aggregating the 21 individual astrometers. This replaces the previous `/detailed-horoscope` endpoint.

## Meter Groups

The system provides 5 life area groups:

1. **Mind** - Cognitive function, thinking, communication (3 meters)
2. **Emotions** - Feelings, relationships, emotional well-being (3 meters)
3. **Body** - Physical energy, action, vitality (3 meters)
4. **Spirit** - Inner wisdom, soul path, elemental balance (6 meters)
5. **Growth** - Career, expansion, transformation, breakthroughs (6 meters)

**Note**: The 2 overview meters (overall_intensity, overall_harmony) are displayed in a separate tab and not included in these groups.

## Endpoint

### `GET /daily-horoscope`

**Request Parameters**:
- `date` (string, required): Date in YYYY-MM-DD format
- `user_id` (string, required): User identifier
- `include_trends` (boolean, optional): Include trend data (default: true)

**Response**: DailyHoroscope object

## Data Structures

### DailyHoroscope

Complete daily horoscope with basic fields, detailed content, astrometers, and meter groups.

```json
{
  "date": "2025-11-02",
  "sun_sign": "aries",
  "technical_analysis": "...",
  "lunar_cycle_update": "...",
  "daily_theme_headline": "...",
  "daily_overview": "...",
  "summary": "...",
  "actionable_advice": {
    "do": "...",
    "dont": "...",
    "reflect_on": "..."
  },
  "general_transits_overview": "...",
  "look_ahead_preview": "...",
  "details": {
    "love_and_relationships": "...",
    "career_and_ambition": "...",
    "...": "..."
  },
  "astrometers": {
    "overall_intensity": { /* MeterReading */ },
    "overall_harmony": { /* MeterReading */ },
    "mental_clarity": { /* MeterReading */ },
    "...": "... (all 21 individual meters)"
  },
  "meter_groups": {
    "mind": { /* MeterGroupData */ },
    "emotions": { /* MeterGroupData */ },
    "body": { /* MeterGroupData */ },
    "spirit": { /* MeterGroupData */ },
    "growth": { /* MeterGroupData */ }
  }
}
```

### MeterGroupData

Complete data for a single meter group.

```typescript
interface MeterGroupData {
  group_name: string;           // "mind" | "emotions" | "body" | "spirit" | "growth"
  display_name: string;         // "Mind" | "Emotions" | "Body" | "Spirit" | "Growth"
  scores: MeterGroupScores;
  state: MeterGroupState;
  interpretation: string;       // 2-3 sentences, 150-300 chars, LLM-generated
  trend: MeterGroupTrend | null;
  meter_ids: string[];          // IDs of meters in this group
}
```

### MeterGroupScores

Aggregated scores (arithmetic mean of all meters in group).

```typescript
interface MeterGroupScores {
  unified_score: number;  // 0-100, primary display value
  harmony: number;        // 0-100, supportive vs challenging
  intensity: number;      // 0-100, activity level
}
```

### MeterGroupState

Quality assessment based on harmony and intensity.

```typescript
interface MeterGroupState {
  label: string;    // Human-readable: "Excellent", "Supportive", "Challenging", etc.
  quality: string;  // Enum: "excellent" | "supportive" | "harmonious" | "peaceful" | "mixed" | "quiet" | "challenging" | "intense"
}
```

**Quality Label Mapping**:
- harmony >= 75, intensity >= 75: "excellent"
- harmony >= 75, intensity >= 40: "supportive"
- harmony >= 75, intensity < 40: "peaceful"
- harmony >= 50, intensity >= 60: "mixed"
- harmony >= 50, intensity < 60: "quiet"
- harmony < 50, intensity >= 60: "intense"
- harmony < 50, intensity < 60: "challenging"

### MeterGroupTrend

Trend data comparing today vs yesterday (optional, null if yesterday data unavailable).

```typescript
interface MeterGroupTrend {
  unified_score: TrendMetric;
  harmony: TrendMetric;
  intensity: TrendMetric;
}

interface TrendMetric {
  previous: number;      // Yesterday's value
  delta: number;         // Change amount (can be negative)
  direction: string;     // "improving" | "worsening" | "stable" | "increasing" | "decreasing"
  change_rate: string;   // "rapid" | "moderate" | "slow"
}
```

**Direction Logic**:
- For unified_score/harmony: "improving" (positive), "worsening" (negative), "stable" (near zero)
- For intensity: "increasing" (positive), "decreasing" (negative), "stable" (near zero)

**Change Rate**:
- rapid: |delta| >= 15
- moderate: 5 <= |delta| < 15
- slow: |delta| < 5

## Meter Group Mappings

### Mind (3 meters)
- `mental_clarity`
- `decision_quality`
- `communication_flow`

**Cognitive functions, thinking, communication**

### Emotions (3 meters)
- `emotional_intensity`
- `relationship_harmony`
- `emotional_resilience`

**Feelings, connections, emotional well-being**

### Body (3 meters)
- `physical_energy`
- `conflict_risk`
- `motivation_drive`

**Physical vitality, action, drive**

### Spirit (6 meters)
- `intuition_spirituality`
- `karmic_lessons`
- `fire_energy`
- `earth_energy`
- `air_energy`
- `water_energy`

**Inner wisdom, soul path, elemental balance**

### Growth (6 meters)
- `career_ambition`
- `opportunity_window`
- `challenge_intensity`
- `transformation_pressure`
- `innovation_breakthrough`
- `social_collective`

**Career expansion, evolution, challenges, breakthroughs, collective progress**

## Example Response

### Complete Response (Abbreviated)

```json
{
  "date": "2025-11-02",
  "sun_sign": "aries",
  "technical_analysis": "Sun in Scorpio trines Saturn in Pisces...",
  "lunar_cycle_update": "Waxing crescent in Sagittarius...",
  "daily_theme_headline": "Deep Reflection Meets Bold Action",
  "daily_overview": "Today brings a powerful blend of introspection and momentum...",
  "summary": "Your mental clarity is sharp while emotions run deep...",
  "actionable_advice": {
    "do": "Trust your intuition on important decisions",
    "dont": "Avoid rushing into conflict when tensions arise",
    "reflect_on": "How can you balance depth with forward motion?"
  },
  "general_transits_overview": "The Sun's trine to Saturn provides...",
  "look_ahead_preview": "This weekend brings Venus into harmonious aspect...",
  "details": {
    "love_and_relationships": "Your emotional depth is especially strong today...",
    "career_and_ambition": "Professional momentum builds with Saturn's support...",
    "personal_growth": "This is a powerful day for self-reflection..."
  },
  "astrometers": {
    "overall_intensity": { "unified_score": 68.0, "...": "..." },
    "overall_harmony": { "unified_score": 72.0, "...": "..." },
    "mental_clarity": { "unified_score": 78.0, "...": "..." }
  },
  "meter_groups": {
    "mind": {
      "group_name": "mind",
      "display_name": "Mind",
      "scores": {
        "unified_score": 75.3,
        "harmony": 78.0,
        "intensity": 72.7
      },
      "state": {
        "label": "Supportive",
        "quality": "supportive"
      },
      "interpretation": "Your mental faculties are sharp and clear today. Communication flows easily and you're able to process information quickly. This is an excellent time for important conversations or strategic planning.",
      "trend": {
        "unified_score": {
          "previous": 68.5,
          "delta": 6.8,
          "direction": "improving",
          "change_rate": "moderate"
        },
        "harmony": {
          "previous": 75.0,
          "delta": 3.0,
          "direction": "improving",
          "change_rate": "slow"
        },
        "intensity": {
          "previous": 62.0,
          "delta": 10.7,
          "direction": "increasing",
          "change_rate": "moderate"
        }
      },
      "meter_ids": ["mental_clarity", "decision_quality", "communication_flow"]
    },
    "emotions": {
      "group_name": "emotions",
      "display_name": "Emotions",
      "scores": {
        "unified_score": 58.2,
        "harmony": 52.0,
        "intensity": 64.3
      },
      "state": {
        "label": "Mixed",
        "quality": "mixed"
      },
      "interpretation": "Your emotions are running high today with a mix of supportive and challenging influences. Relationships may require extra patience and understanding. Take time to process your feelings before making important decisions.",
      "trend": {
        "unified_score": {
          "previous": 62.0,
          "delta": -3.8,
          "direction": "worsening",
          "change_rate": "slow"
        },
        "harmony": {
          "previous": 58.0,
          "delta": -6.0,
          "direction": "worsening",
          "change_rate": "moderate"
        },
        "intensity": {
          "previous": 66.0,
          "delta": -1.7,
          "direction": "decreasing",
          "change_rate": "slow"
        }
      },
      "meter_ids": ["emotional_intensity", "relationship_harmony", "emotional_resilience"]
    },
    "body": {
      "group_name": "body",
      "display_name": "Body",
      "scores": {
        "unified_score": 71.5,
        "harmony": 68.0,
        "intensity": 75.0
      },
      "state": {
        "label": "Mixed",
        "quality": "mixed"
      },
      "interpretation": "Your physical energy is strong and you feel motivated to take action. Watch for potential conflicts or impatience. Channel this drive into productive activities and physical exercise.",
      "trend": null,
      "meter_ids": ["physical_energy", "conflict_risk", "motivation_drive"]
    },
    "spirit": {
      "group_name": "spirit",
      "display_name": "Spirit",
      "scores": {
        "unified_score": 62.0,
        "harmony": 65.5,
        "intensity": 58.5
      },
      "state": {
        "label": "Quiet",
        "quality": "quiet"
      },
      "interpretation": "Your spiritual awareness is gentle today with balanced elemental energies. Your intuition is accessible but subtle. This is a good time for quiet reflection and connecting with your inner wisdom.",
      "trend": null,
      "meter_ids": ["intuition_spirituality", "karmic_lessons", "fire_energy", "earth_energy", "air_energy", "water_energy"]
    },
    "growth": {
      "group_name": "growth",
      "display_name": "Growth",
      "scores": {
        "unified_score": 66.8,
        "harmony": 58.0,
        "intensity": 75.7
      },
      "state": {
        "label": "Mixed",
        "quality": "mixed"
      },
      "interpretation": "Your professional ambition is strong and opportunities are present, though some challenges require navigation. This is a powerful time for breakthrough thinking and transformation. Stay focused on your long-term vision while handling immediate obstacles.",
      "trend": null,
      "meter_ids": ["career_ambition", "opportunity_window", "challenge_intensity", "transformation_pressure", "innovation_breakthrough", "social_collective"]
    }
  }
}
```

## Backwards Compatibility

- `meter_groups` field is **optional** in the response
- Older iOS clients can ignore this field
- All existing fields remain unchanged
- Individual astrometers still present in `astrometers` field

## Migration Notes

### For iOS Developers

1. **Update DailyHoroscope model**:
   ```swift
   struct DailyHoroscope: Codable {
       // ... existing fields ...
       let meterGroups: [String: MeterGroupData]?  // NEW
       let generalTransitsOverview: String?        // NEW (merged from detailed)
       let lookAheadPreview: String?              // NEW (merged from detailed)
       let details: HoroscopeDetails?             // NEW (merged from detailed)
   }
   ```

2. **Add new models**:
   - `MeterGroupData`
   - `MeterGroupScores`
   - `MeterGroupState`
   - `MeterGroupTrend`

3. **UI Implementation**:
   - Display 5 group cards on main screen
   - Each card shows: display_name, unified_score, state.label, interpretation
   - Tap to expand: show individual meters via meter_ids
   - Use trend arrows/indicators if trend data present

4. **Deprecation**:
   - Stop calling `/detailed-horoscope` endpoint
   - Use merged fields from `/daily-horoscope` instead

## Testing Checklist

- [ ] All 5 groups present in response
- [ ] Each group has all required fields
- [ ] Scores are valid floats 0-100
- [ ] State labels match quality enum
- [ ] Interpretations are 150-300 chars
- [ ] meter_ids reference valid existing meters
- [ ] All 21 non-overview meters assigned to exactly one group
- [ ] Trend data structure correct (when present)
- [ ] Response validates against schema
- [ ] Backwards compatible (older clients don't break)

## Questions or Issues

Contact backend team or file issue in repository.

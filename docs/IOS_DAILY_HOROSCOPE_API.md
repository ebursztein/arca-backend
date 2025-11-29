# Daily Horoscope API - iOS Integration Guide

**Status:** ✅ STABLE - Frozen until release
**Last Updated:** 2025-01-06
**Backend Version:** V2 (Single-Prompt Architecture)

## Overview

This document provides the complete technical specification for the `get_daily_horoscope` Cloud Function endpoint. This API will **not change** until the initial release, ensuring stable iOS integration.

## Endpoint

### Function Name
```
get_daily_horoscope
```

### Type
Firebase Callable Function (HTTPS)

### Authentication
Requires Firebase Authentication. The `user_id` is automatically extracted from the authenticated request context.

### Request

```typescript
interface DailyHoroscopeRequest {
  date: string;  // ISO date string (e.g., "2025-01-06")
}
```

**Example:**
```swift
// Swift
let functions = Functions.functions()
let getDailyHoroscope = functions.httpsCallable("get_daily_horoscope")

getDailyHoroscope(["date": "2025-01-06"]) { result, error in
    if let error = error as NSError? {
        // Handle error
        return
    }

    if let data = result?.data as? [String: Any] {
        // Parse horoscope data
    }
}
```

### Response

Returns a `DailyHoroscope` object with the following structure:

## Response Schema

### Top-Level Structure

```json
{
  "date": "2025-01-06",
  "sun_sign": "gemini",

  "technical_analysis": "...",
  "daily_theme_headline": "...",
  "daily_overview": "...",
  "actionable_advice": { ... },

  "astrometers": { ... },
  "transit_summary": { ... },
  "moon_detail": { ... },

  "look_ahead_preview": "...",
  "energy_rhythm": "...",
  "relationship_weather": "...",
  "collective_energy": "...",

  "model_used": "gemini-2.5-flash-lite",
  "generation_time_ms": 2450,
  "usage": { ... }
}
```

---

## Core Fields

### `date`
- **Type:** `string`
- **Format:** ISO date (e.g., `"2025-01-06"`)
- **Description:** The date this horoscope is for

### `sun_sign`
- **Type:** `string`
- **Enum:** `aries | taurus | gemini | cancer | leo | virgo | libra | scorpio | sagittarius | capricorn | aquarius | pisces`
- **Description:** User's sun sign (lowercase)

### `technical_analysis`
- **Type:** `string`
- **Length:** 3-5 sentences
- **Description:** Technical explanation of today's astronomical alignments (transits, aspects, lunar phase). Written in accessible language without jargon.
- **Example:** "Today the Sun in Capricorn forms a supportive trine to your natal Mars, energizing your drive and confidence. Meanwhile, Venus is moving through your 7th house of partnerships, bringing harmony to relationships. The Moon in Pisces heightens your intuition and emotional receptivity."

### `daily_theme_headline`
- **Type:** `string`
- **Max Length:** 15 words
- **Description:** A shareable, inspirational wisdom sentence that captures the day's energy. Actionable and empowering.
- **Example:** "Trust your instincts today — they're aligned with the universe's flow."

### `daily_overview`
- **Type:** `string`
- **Length:** 3-4 sentences, 60-80 words
- **Description:** Opening overview combining emotional tone, key transit explanations, and sun sign connection. Sets the day's narrative.
- **Example:** "Good morning, Gemini! Today brings a beautiful harmony between your mental clarity and emotional intuition. With Mercury forming a supportive sextile to your natal Moon, communication flows naturally and you're able to express your feelings with ease. This is an excellent day for heart-to-heart conversations and creative self-expression."

### `actionable_advice`
- **Type:** `ActionableAdvice` object
- **Description:** Structured DO/DON'T/REFLECT guidance

```json
{
  "do": "Schedule that difficult conversation you've been avoiding — today's transits support honest communication without drama.",
  "dont": "Don't overthink your partner's words or read hidden meanings where there aren't any.",
  "reflect_on": "What am I afraid to say out loud? How can I express this with kindness?"
}
```

**Fields:**
- `do` (string): Ultra-specific action with timing
- `dont` (string): Shadow/pitfall to avoid today
- `reflect_on` (string): Journaling question for self-reflection

---

## Astrometers

### `astrometers`
- **Type:** `AstrometersForIOS` object
- **Description:** Complete quantified meter system with 17 individual meters organized into 5 user-facing groups, with full explainability

```json
{
  "date": "2025-01-06T00:00:00",

  "overall_unified_score": 68.5,
  "overall_intensity": 72.3,
  "overall_harmony": 64.8,
  "overall_quality": "harmonious",
  "overall_state": "Balanced Flow",

  "groups": [ ... ],

  "top_active_meters": ["drive", "communication", "vitality"],
  "top_challenging_meters": ["inner_stability", "sensitivity"],
  "top_flowing_meters": ["love", "creativity", "focus"]
}
```

#### Overall Metrics

- `overall_unified_score` (float, -100 to +100): Primary overall value - bipolar scale (positive = harmonious, negative = challenging)
- `overall_intensity` (float, 0-100): Overall astrological activity level across all meters
- `overall_harmony` (float, 0-100): Overall supportive vs challenging quality
- `overall_quality` (string): Simple category - `harmonious | challenging | mixed | quiet | peaceful`
- `overall_state` (string): Rich contextual label - `"Quiet Reflection" | "Peak Energy" | "Balanced Flow"`, etc.

#### Top Insights

- `top_active_meters` (string[]): Top 3-5 meters by intensity (most happening)
- `top_challenging_meters` (string[]): Top 3-5 meters by low harmony (most friction)
- `top_flowing_meters` (string[]): Top 3-5 meters by high unified score (most supportive)

#### Groups Structure

The `groups` array contains 5 `MeterGroupForIOS` objects:

```json
{
  "group_name": "mind",
  "display_name": "Mind",

  "unified_score": 71.2,
  "intensity": 68.5,
  "harmony": 73.8,
  "state_label": "Sharp Focus",
  "quality": "harmonious",

  "interpretation": "Your mental energy is strong today with clear thinking and excellent concentration. Communication flows naturally and ideas come quickly.",

  "trend_delta": 5.3,
  "trend_direction": "improving",
  "trend_change_rate": "moderate",

  "overview": "Mind tracks your cognitive energy, mental clarity, focus, and communication.",
  "detailed": "Combines Mental Clarity, Focus, and Communication meters to show your overall intellectual and expressive state.",

  "meters": [
    { ... },  // MeterForIOS objects
    { ... },
    { ... }
  ]
}
```

**Group Names:** `mind | emotions | body | spirit | growth`

**Group Display Names:** `Mind | Emotions | Body | Spirit | Growth`

#### Individual Meter Structure

Each `meters` array contains 3-4 `MeterForIOS` objects:

```json
{
  "meter_name": "mental_clarity",
  "display_name": "Mental Clarity",
  "group": "mind",

  "unified_score": 74.5,
  "intensity": 68.2,
  "harmony": 80.8,
  "unified_quality": "harmonious",
  "state_label": "Crystal Clear",

  "interpretation": "Mercury trine your natal Sun brings sharp mental focus and excellent decision-making ability today.",

  "trend_delta": 8.3,
  "trend_direction": "improving",
  "trend_change_rate": "moderate",

  "overview": "Mental Clarity represents your ability to think clearly, make decisions, and process information.",
  "detailed": "This meter tracks Mercury and Jupiter transits to your natal Sun, Mercury, and 3rd house (communication). When supportive, you experience sharp focus and quick comprehension. Challenging aspects create mental fog or overthinking.",

  "astrological_foundation": {
    "natal_planets_tracked": ["sun", "mercury"],
    "transit_planets_tracked": ["mercury", "jupiter", "saturn"],
    "key_houses": {
      "3": "Communication, thinking, learning"
    },
    "primary_planets": {
      "mercury": "Governs thinking, processing, and mental clarity",
      "sun": "Core consciousness and mental vitality"
    },
    "secondary_planets": {
      "jupiter": "Expands understanding and optimism",
      "saturn": "Can create mental blocks or focused concentration"
    }
  },

  "top_aspects": [
    {
      "label": "Transit Mercury trine Natal Sun",
      "natal_planet": "sun",
      "transit_planet": "mercury",
      "aspect_type": "trine",
      "orb": 1.2,
      "orb_percentage": 17.1,
      "phase": "applying",
      "days_to_exact": 0.8,
      "contribution": 25.6,
      "quality_factor": 1.0,
      "natal_planet_house": 1,
      "natal_planet_sign": "gemini",
      "houses_involved": [1, 5],
      "natal_aspect_echo": null
    },
    {
      "label": "Transit Jupiter sextile Natal Mercury",
      "natal_planet": "mercury",
      "transit_planet": "jupiter",
      "aspect_type": "sextile",
      "orb": 2.5,
      "orb_percentage": 50.0,
      "phase": "separating",
      "days_to_exact": -1.5,
      "contribution": 18.3,
      "quality_factor": 1.0,
      "natal_planet_house": 3,
      "natal_planet_sign": "leo",
      "houses_involved": [3, 7],
      "natal_aspect_echo": "Echoes natal Mercury-Jupiter trine"
    }
  ]
}
```

##### Meter Scores
- `unified_score` (float, -100 to +100): Primary display value - bipolar scale (positive = harmonious, negative = challenging). NOT 0-100, see unified-score-guide.md
- `intensity` (float, 0-100): Activity level - how much is happening
- `harmony` (float, 0-100): Quality - supportive (high) vs challenging (low), where 50 is neutral

##### Meter Labels
- `unified_quality` (string): Simple category - `harmonious | challenging | mixed | quiet | peaceful`
- `state_label` (string): Rich contextual state from JSON labels - `"Crystal Clear" | "Foggy Thinking" | "Breakthrough Insights"`, etc. (max 2 words per iOS UI constraint)

##### LLM Interpretation
- `interpretation` (string, 80-150 chars): Personalized 1-2 sentence interpretation referencing today's specific transits

##### Trend Data (Optional)
Only present if yesterday's data is available:
- `trend_delta` (float): Change in unified_score from yesterday (can be negative)
- `trend_direction` (string): `improving | worsening | stable | increasing | decreasing`
- `trend_change_rate` (string): `rapid | moderate | slow | stable`

##### Explainability - Static
- `overview` (string): What this meter represents (1 sentence, user-facing)
- `detailed` (string): How it's measured (2-3 sentences, explains calculation methodology)
- `astrological_foundation` (object): Complete astrological explanation

##### Explainability - Dynamic
- `top_aspects` (MeterAspect[]): Top 3-5 transit aspects driving today's score (sorted by contribution)

**MeterAspect Fields:**
- `label` (string): Human-readable aspect description
- `natal_planet` (string): Natal planet name (lowercase)
- `transit_planet` (string): Transit planet name (lowercase)
- `aspect_type` (string): `conjunction | opposition | trine | square | sextile`
- `orb` (float): Exact orb in degrees (e.g., 2.5)
- `orb_percentage` (float, 0-100): Percentage of maximum orb (tighter = stronger)
- `phase` (string): `applying | exact | separating`
- `days_to_exact` (float, nullable): Days until exact (negative = past exact)
- `contribution` (float): DTI contribution to this meter's score
- `quality_factor` (float, -1 to 1): Harmonic quality (-1 = very challenging, +1 = very harmonious)
- `natal_planet_house` (int, 1-12): House containing natal planet
- `natal_planet_sign` (string): Sign of natal planet
- `houses_involved` (int[]): All houses involved in this transit
- `natal_aspect_echo` (string, nullable): If this transit echoes a natal aspect (e.g., "Echoes natal Mars-Saturn square")

---

## Transit Summary

### `transit_summary`
- **Type:** `object`
- **Description:** Enhanced natal-transit analysis with priority transits, critical degrees, retrograde data, and theme synthesis
- **Source:** Generated by `format_transit_summary_for_ui()` in `astro.py`

```json
{
  "priority_transits": [
    {
      "transit_planet": "saturn",
      "natal_planet": "sun",
      "aspect": "square",
      "orb": 0.8,
      "phase": "applying",
      "interpretation": "Major growth edge: Saturn challenges your identity",
      "houses": [1, 10]
    }
  ],
  "theme_synthesis": {
    "primary_theme": "Relationship harmony with creative flow",
    "secondary_theme": "Mental clarity and focused action"
  },
  "critical_degree_alerts": [
    {
      "planet": "mars",
      "degree": 0,
      "sign": "aries",
      "meaning": "Fresh start in drive and ambition"
    }
  ],
  "retrograde_planets": [
    {
      "planet": "mercury",
      "sign": "capricorn",
      "station_date": "2025-01-15",
      "days_to_station": 9
    }
  ]
}
```

---

## Moon Detail

### `moon_detail`
- **Type:** `object`
- **Description:** Comprehensive moon transit detail including aspects to natal chart, void-of-course periods, dispositor, and next events
- **Source:** Generated by `get_moon_transit_detail()` in `moon.py`

```json
{
  "moon_sign": "pisces",
  "moon_house": 4,
  "lunar_phase": {
    "name": "Waxing Crescent",
    "illumination": 23.5,
    "days_to_full": 10.2,
    "days_to_new": 24.8
  },
  "moon_aspects": [
    {
      "aspect_type": "trine",
      "natal_planet": "venus",
      "orb": 1.5,
      "interpretation": "Emotional harmony in relationships"
    }
  ],
  "void_of_course": "Not void of course",
  "dispositor": {
    "planet": "neptune",
    "sign": "pisces",
    "house": 4,
    "dignity": "domicile"
  },
  "interpretation": "The Moon in Pisces heightens your emotional sensitivity and intuition today. With Neptune as dispositor in its home sign, your dreams and inner knowing are especially potent. This is ideal for creative work and spiritual practices."
}
```

**Key Fields:**
- `interpretation` (string): LLM-generated interpretation of moon's influence (2-3 sentences)
- `void_of_course` (string): Either "Not void of course" or "Void until [time] UTC"
- `lunar_phase.name` (string): `New Moon | Waxing Crescent | First Quarter | Waxing Gibbous | Full Moon | Waning Gibbous | Last Quarter | Waning Crescent`

---

## Phase 1 Extensions

These fields leverage astrometer data to provide additional lifestyle guidance:

### `look_ahead_preview`
- **Type:** `string` (optional)
- **Length:** 2-3 sentences
- **Description:** Preview of upcoming significant transits over the next 7 days
- **Example:** "Venus enters your 5th house on Thursday, bringing a playful and creative energy to romance. The weekend brings a powerful Mars-Jupiter conjunction that boosts confidence and opportunities."

### `energy_rhythm`
- **Type:** `string` (optional)
- **Length:** 1-2 sentences
- **Description:** Energy pattern throughout the day based on intensity curve and Moon movement
- **Example:** "Your energy peaks in the morning with Moon in Aries, perfect for tackling challenging tasks before noon. Afternoon may feel slower — use that time for reflection rather than action."

### `relationship_weather`
- **Type:** `string` (optional)
- **Length:** 2-3 sentences
- **Description:** Interpersonal dynamics across romantic, platonic, and professional relationships based on relationship meters (Love, Communication, Social Life)
- **Example:** "Romantic energy is flowing beautifully today — your heart is open and vulnerable conversations come naturally. Friendships may need a bit more patience as communication can feel slightly off. Professional partnerships benefit from your clear thinking and diplomatic approach."

### `collective_energy`
- **Type:** `string` (optional)
- **Length:** 1-2 sentences
- **Description:** What the collective/everyone is feeling based on outer planet transits and lunar context
- **Example:** "Everyone's feeling the intensity of Pluto's shift into Aquarius — there's a collective desire for transformation and breaking old patterns. The Moon in Pisces softens this energy with compassion and intuition."

---

## Metadata

### `model_used`
- **Type:** `string`
- **Default:** `"gemini-2.5-flash-lite"`
- **Description:** The LLM model used to generate this horoscope

### `generation_time_ms`
- **Type:** `integer`
- **Description:** Time taken to generate the horoscope in milliseconds
- **Example:** `2450`

### `usage`
- **Type:** `object`
- **Description:** Token usage metadata from Gemini API

```json
{
  "prompt_token_count": 12543,
  "candidates_token_count": 1876,
  "cached_content_token_count": 0
}
```

---

## Complete Example Response

```json
{
  "date": "2025-01-06",
  "sun_sign": "gemini",

  "technical_analysis": "Today the Sun in Capricorn forms a supportive trine to your natal Mars, energizing your drive and confidence. Meanwhile, Venus is moving through your 7th house of partnerships, bringing harmony to relationships. The Moon in Pisces heightens your intuition and emotional receptivity throughout the day.",

  "daily_theme_headline": "Trust your instincts — they're aligned with the universe's flow today.",

  "daily_overview": "Good morning, Gemini! Today brings a beautiful harmony between your mental clarity and emotional intuition. With Mercury forming a supportive sextile to your natal Moon, communication flows naturally and you're able to express your feelings with ease. This is an excellent day for heart-to-heart conversations and creative self-expression.",

  "actionable_advice": {
    "do": "Schedule that difficult conversation you've been avoiding — today's transits support honest communication without drama.",
    "dont": "Don't overthink your partner's words or read hidden meanings where there aren't any.",
    "reflect_on": "What am I afraid to say out loud? How can I express this with kindness?"
  },

  "astrometers": {
    "date": "2025-01-06T00:00:00",
    "overall_unified_score": 68.5,
    "overall_intensity": 72.3,
    "overall_harmony": 64.8,
    "overall_quality": "harmonious",
    "overall_state": "Balanced Flow",
    "groups": [
      {
        "group_name": "mind",
        "display_name": "Mind",
        "unified_score": 71.2,
        "intensity": 68.5,
        "harmony": 73.8,
        "state_label": "Sharp Focus",
        "quality": "harmonious",
        "interpretation": "Your mental energy is strong today with clear thinking and excellent concentration.",
        "trend_delta": 5.3,
        "trend_direction": "improving",
        "trend_change_rate": "moderate",
        "overview": "Mind tracks your cognitive energy, mental clarity, focus, and communication.",
        "detailed": "Combines Mental Clarity, Focus, and Communication meters.",
        "meters": [
          {
            "meter_name": "mental_clarity",
            "display_name": "Mental Clarity",
            "group": "mind",
            "unified_score": 74.5,
            "intensity": 68.2,
            "harmony": 80.8,
            "unified_quality": "harmonious",
            "state_label": "Crystal Clear",
            "interpretation": "Mercury trine your natal Sun brings sharp mental focus today.",
            "trend_delta": 8.3,
            "trend_direction": "improving",
            "trend_change_rate": "moderate",
            "overview": "Mental Clarity represents your ability to think clearly and make decisions.",
            "detailed": "Tracks Mercury and Jupiter transits to your natal Sun, Mercury, and 3rd house.",
            "astrological_foundation": {
              "natal_planets_tracked": ["sun", "mercury"],
              "transit_planets_tracked": ["mercury", "jupiter", "saturn"],
              "key_houses": {
                "3": "Communication, thinking, learning"
              },
              "primary_planets": {
                "mercury": "Governs thinking and mental clarity",
                "sun": "Core consciousness and mental vitality"
              },
              "secondary_planets": {
                "jupiter": "Expands understanding",
                "saturn": "Can create mental blocks or focus"
              }
            },
            "top_aspects": [
              {
                "label": "Transit Mercury trine Natal Sun",
                "natal_planet": "sun",
                "transit_planet": "mercury",
                "aspect_type": "trine",
                "orb": 1.2,
                "orb_percentage": 17.1,
                "phase": "applying",
                "days_to_exact": 0.8,
                "contribution": 25.6,
                "quality_factor": 1.0,
                "natal_planet_house": 1,
                "natal_planet_sign": "gemini",
                "houses_involved": [1, 5],
                "natal_aspect_echo": null
              }
            ]
          }
        ]
      }
    ],
    "top_active_meters": ["drive", "communication", "vitality"],
    "top_challenging_meters": ["inner_stability"],
    "top_flowing_meters": ["love", "creativity", "focus"]
  },

  "transit_summary": {
    "priority_transits": [],
    "theme_synthesis": {
      "primary_theme": "Mental clarity with emotional harmony"
    },
    "critical_degree_alerts": [],
    "retrograde_planets": []
  },

  "moon_detail": {
    "moon_sign": "pisces",
    "moon_house": 4,
    "lunar_phase": {
      "name": "Waxing Crescent",
      "illumination": 23.5
    },
    "void_of_course": "Not void of course",
    "interpretation": "The Moon in Pisces heightens your emotional sensitivity and intuition today."
  },

  "look_ahead_preview": "Venus enters your 5th house on Thursday, bringing playful energy to romance.",
  "energy_rhythm": "Your energy peaks in the morning — tackle challenging tasks before noon.",
  "relationship_weather": "Romantic energy flows beautifully today with open, vulnerable communication.",
  "collective_energy": "Everyone's feeling the intensity of Pluto's shift into Aquarius.",

  "model_used": "gemini-2.5-flash-lite",
  "generation_time_ms": 2450,
  "usage": {
    "prompt_token_count": 12543,
    "candidates_token_count": 1876,
    "cached_content_token_count": 0
  }
}
```

---

## Error Handling

### Error Codes

The function may return Firebase Callable Function errors with these codes:

- `UNAUTHENTICATED` - User is not authenticated
- `NOT_FOUND` - User profile not found in Firestore
- `INVALID_ARGUMENT` - Invalid date format or missing required fields
- `INTERNAL` - Server error during generation

### Error Response Format

```json
{
  "code": "not-found",
  "message": "User profile not found for user: abc123",
  "details": null
}
```

### Swift Error Handling Example

```swift
getDailyHoroscope(["date": "2025-01-06"]) { result, error in
    if let error = error as NSError? {
        let code = FunctionsErrorCode(rawValue: error.code)

        switch code {
        case .unauthenticated:
            // Prompt user to sign in
        case .notFound:
            // Show onboarding to create profile
        case .invalidArgument:
            // Show error message
        case .internal:
            // Show generic error, retry later
        default:
            // Handle unexpected error
        }
        return
    }

    // Success - parse result
}
```

---

## Data Model Notes

### Meter Names (17 Total)

**Mind (3):**
- `mental_clarity` - Mental Clarity
- `focus` - Focus
- `communication` - Communication

**Emotions (3):**
- `love` - Love
- `inner_stability` - Inner Stability
- `sensitivity` - Sensitivity

**Body (3):**
- `vitality` - Vitality
- `drive` - Drive
- `wellness` - Wellness

**Spirit (4):**
- `purpose` - Purpose
- `connection` - Connection
- `intuition` - Intuition
- `creativity` - Creativity

**Growth (4):**
- `opportunities` - Opportunities
- `career` - Career
- `growth` - Growth
- `social_life` - Social Life

### Planet Names

All planet names are lowercase strings:
```
sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto, north_node
```

### Sign Names

All sign names are lowercase strings:
```
aries, taurus, gemini, cancer, leo, virgo, libra, scorpio, sagittarius, capricorn, aquarius, pisces
```

### Aspect Types

```
conjunction, opposition, trine, square, sextile
```

---

## Performance Expectations

- **Average Response Time:** 2-4 seconds
- **Token Usage:** ~12,000-15,000 prompt tokens, ~1,500-2,000 completion tokens
- **Caching:** Static template caching planned (50-90% cost reduction)
- **Rate Limiting:** No explicit limits currently (will add before production)

---

## Changelog

### 2025-01-06
- Initial stable API documentation
- 17 meters + 5 groups structure
- Single-prompt architecture
- Phase 1 extensions included
- Complete explainability with `top_aspects`

---

## Support

For questions or issues with this API, contact the backend team or file an issue in the repository.

**This API specification is frozen until release. Any breaking changes will be communicated with a major version bump.**

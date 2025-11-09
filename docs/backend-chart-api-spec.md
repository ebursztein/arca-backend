# Backend API Specification: Natal & Transit Chart Endpoints

**Version:** 1.1
**Date:** 2025-11-05
**Status:** Specification for Backend Team - Updated with Kerykeion Implementation Details

## Overview

This document specifies the API endpoints required for the natal chart visualization feature in the ARCA iOS app. The backend will use the Kerykeion Python library to perform astrological calculations and return structured JSON data with geometric coordinates for rendering charts on iOS.

**Update (v1.1):** Added detailed implementation guidance based on Kerykeion source code analysis. Backend can use built-in coordinate functions (`sliceToX`, `sliceToY`) and optional planet overlap detection from Kerykeion's `draw_planets.py` module.

## Table of Contents

1. [General Requirements](#general-requirements)
2. [Endpoint: get_natal_chart](#endpoint-get_natal_chart)
3. [Endpoint: get_transit_chart](#endpoint-get_transit_chart)
4. [Endpoint: get_transit_analysis](#endpoint-get_transit_analysis)
5. [Data Structures](#data-structures)
6. [Coordinate Calculation](#coordinate-calculation)
7. [Interpretation Text Guidelines](#interpretation-text-guidelines)
8. [Error Handling](#error-handling)
9. [Implementation Notes](#implementation-notes)

---

## General Requirements

### Technology Stack

- **Platform**: Firebase Cloud Functions (Python)
- **Region**: us-central1 (existing)
- **Library**: Kerykeion v5.1.7+
- **Authentication**: Firebase Auth (same as existing endpoints)

### Common Headers

All requests must include:
```
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
```

### Response Format

All responses return JSON with the following structure:

```json
{
  "success": true|false,
  "data": { ... },
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

### Rate Limiting

- Natal chart: No strict rate limit (cached per user, rarely regenerated)
- Transit chart: 1 request per minute per user (daily updates only)

---

## Endpoint: get_natal_chart

### Purpose

Generate or retrieve a user's natal (birth) chart with complete astrological data, geometric coordinates for visualization, and interpretation text.

### HTTP Method

POST (Firebase Callable Function)

### Request Parameters

```json
{
  "user_id": "firebase_user_id_string",
  "force_regenerate": false,
  "chart_size": 600,
  "include_minor_planets": false
}
```

#### Parameter Details

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | string | Yes | - | Firebase user ID |
| `force_regenerate` | boolean | No | false | Force recalculation even if cached |
| `chart_size` | number | No | 600 | Canvas size in points (for coordinate scaling) |
| `include_minor_planets` | boolean | No | false | Include Chiron, asteroids (future) |

### Response Structure

```json
{
  "success": true,
  "data": {
    "user_id": "abc123",
    "chart_type": "natal",
    "birth_data": {
      "date": "1990-06-15",
      "time": "14:30",
      "timezone": "America/New_York",
      "location": {
        "city": "New York",
        "country": "US",
        "latitude": 40.7128,
        "longitude": -74.0060
      }
    },
    "viewport": {
      "center_x": 300,
      "center_y": 300,
      "outer_radius": 280,
      "inner_radius": 200,
      "planet_ring_radius": 240
    },
    "planets": [
      {
        "name": "sun",
        "sign": "gemini",
        "sign_symbol": "♊",
        "degree": 83.45,
        "signed_degree": 23.45,
        "house": 10,
        "retrograde": false,
        "element": "air",
        "modality": "mutable",
        "dms": "23°27'",
        "position": {
          "x": 315.5,
          "y": 185.3,
          "angle": 83.45
        },
        "interpretation": {
          "placement": "Your Sun in Gemini in the 10th house suggests a career focused on communication, teaching, or intellectual pursuits. You shine brightest when sharing ideas and connecting people through words.",
          "keywords": ["communicative", "versatile", "intellectual", "social"]
        }
      }
      // ... more planets
    ],
    "houses": [
      {
        "number": 1,
        "cusp_degree": 12.5,
        "sign": "leo",
        "sign_symbol": "♌",
        "ruler": "sun",
        "start_angle": 12.5,
        "end_angle": 42.3,
        "position": {
          "label_x": 290,
          "label_y": 260,
          "line_start_x": 300,
          "line_start_y": 300,
          "line_end_x": 450,
          "line_end_y": 380
        }
      }
      // ... 11 more houses
    ],
    "aspects": [
      {
        "body1": "sun",
        "body2": "moon",
        "aspect_type": "trine",
        "aspect_symbol": "△",
        "orb": 2.3,
        "exact_degree": 120,
        "applying": true,
        "strength": "strong",
        "coords": {
          "x1": 315.5,
          "y1": 185.3,
          "x2": 245.8,
          "y2": 420.7
        },
        "interpretation": {
          "meaning": "Sun trine Moon creates natural harmony between your conscious will and emotional needs. You feel at ease with yourself and can balance personal desires with emotional fulfillment.",
          "keywords": ["harmony", "emotional balance", "ease", "confidence"],
          "orb_quality": "strong"
        }
      }
      // ... more aspects
    ],
    "angles": {
      "ascendant": {
        "degree": 12.5,
        "sign": "leo",
        "sign_symbol": "♌",
        "dms": "12°30'",
        "position": {"x": 580, "y": 300}
      },
      "midheaven": {
        "degree": 102.3,
        "sign": "taurus",
        "sign_symbol": "♉",
        "dms": "12°18'",
        "position": {"x": 300, "y": 20}
      },
      "descendant": {
        "degree": 192.5,
        "sign": "aquarius",
        "sign_symbol": "♒",
        "dms": "12°30'",
        "position": {"x": 20, "y": 300}
      },
      "ic": {
        "degree": 282.3,
        "sign": "scorpio",
        "sign_symbol": "♏",
        "dms": "12°18'",
        "position": {"x": 300, "y": 580}
      }
    },
    "distributions": {
      "elements": {
        "fire": 3,
        "earth": 2,
        "air": 4,
        "water": 1,
        "fire_percentage": 30,
        "earth_percentage": 20,
        "air_percentage": 40,
        "water_percentage": 10
      },
      "modalities": {
        "cardinal": 2,
        "fixed": 4,
        "mutable": 4,
        "cardinal_percentage": 20,
        "fixed_percentage": 40,
        "mutable_percentage": 40
      },
      "hemispheres": {
        "eastern": 6,
        "western": 4,
        "northern": 5,
        "southern": 5
      },
      "quadrants": {
        "first": 2,
        "second": 3,
        "third": 2,
        "fourth": 3
      }
    },
    "metadata": {
      "zodiac_type": "tropical",
      "house_system": "placidus",
      "calculation_date": "2025-11-05T10:30:00Z",
      "cached": false,
      "kerykeion_version": "5.1.7"
    }
  }
}
```

### Caching Strategy

**Backend should cache natal charts per user** since birth data doesn't change:
- Store in Firestore: `users/{user_id}/natal_chart`
- Regenerate only if:
  - User updates birth time/location
  - `force_regenerate` parameter is true
  - Chart calculation failed previously

---

## Endpoint: get_transit_chart

### Purpose

Generate current transit chart showing where planets are positioned today, with geometric coordinates for visualization.

### HTTP Method

POST (Firebase Callable Function)

### Request Parameters

```json
{
  "user_id": "firebase_user_id_string",
  "date": "2025-11-05",
  "time": "14:30",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "timezone": "America/New_York"
  },
  "chart_size": 600,
  "include_minor_planets": false
}
```

#### Parameter Details

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | string | Yes | - | Firebase user ID (for context) |
| `date` | string | No | Today | Date for transit (YYYY-MM-DD) |
| `time` | string | No | Now | Time for transit (HH:MM) |
| `location` | object | No | User's current | Location for transit chart |
| `chart_size` | number | No | 600 | Canvas size in points |
| `include_minor_planets` | boolean | No | false | Include Chiron, asteroids |

### Response Structure

**Same structure as `get_natal_chart`**, but:
- `chart_type` is `"transit"`
- `birth_data` replaced with `transit_data`:
  ```json
  "transit_data": {
    "date": "2025-11-05",
    "time": "14:30",
    "timezone": "America/New_York",
    "location": { ... }
  }
  ```

### Caching Strategy

**Cache transit charts with date-based validation**:
- Store in Firestore: `transit_charts/{date}` (global, not per-user)
- Recalculate if:
  - Date has changed (new day)
  - More than 6 hours old (for time accuracy)
  - Different location requested

---

## Endpoint: get_transit_analysis

### Purpose

Analyze how current transits interact with a user's natal chart. Used for "Dig Deeper" feature to explain daily horoscope generation.

### HTTP Method

POST (Firebase Callable Function)

### Request Parameters

```json
{
  "user_id": "firebase_user_id_string",
  "date": "2025-11-05",
  "include_interpretation": true
}
```

### Response Structure

```json
{
  "success": true,
  "data": {
    "user_id": "abc123",
    "date": "2025-11-05",
    "transit_natal_aspects": [
      {
        "transit_planet": "mars",
        "natal_planet": "sun",
        "aspect_type": "square",
        "aspect_symbol": "□",
        "orb": 1.8,
        "exact_degree": 90,
        "transit_position": {"x": 315.5, "y": 185.3},
        "natal_position": {"x": 245.8, "y": 420.7},
        "coords": {
          "x1": 315.5,
          "y1": 185.3,
          "x2": 245.8,
          "y2": 420.7
        },
        "interpretation": {
          "meaning": "Transiting Mars square your natal Sun brings increased energy but also potential friction. This is a time to channel assertiveness constructively and avoid impulsive conflicts.",
          "keywords": ["active", "friction", "assertive", "challenging"],
          "impact_level": "high",
          "duration": "2-3 days"
        }
      }
      // ... more transit-natal aspects
    ],
    "active_house_transits": [
      {
        "planet": "jupiter",
        "house": 5,
        "interpretation": "Jupiter transiting your 5th house expands creativity, romance, and self-expression. This is a fortunate time for artistic projects and enjoying life's pleasures."
      }
    ],
    "interpretation_summary": {
      "overall_theme": "Today's energy combines Mars challenging your sense of self with Jupiter expanding your creative expression. Channel intensity into artistic or playful outlets.",
      "primary_influences": ["mars_square_sun", "jupiter_in_5th"],
      "intensity_score": 72,
      "harmony_score": 58
    },
    "metadata": {
      "calculation_date": "2025-11-05T10:30:00Z",
      "significant_aspects_count": 12,
      "exact_aspects_count": 2
    }
  }
}
```

### Notes

This endpoint focuses on **transit-to-natal interactions** rather than transit-to-transit aspects. It's specifically for explaining how today's sky affects the user's birth chart.

---

## Data Structures

### ChartGeometry

Position data for visualization:

```typescript
interface Position {
  x: number;           // X coordinate (pixels)
  y: number;           // Y coordinate (pixels)
  angle?: number;      // Angle in degrees (0-360, 0=East)
}

interface Viewport {
  center_x: number;
  center_y: number;
  outer_radius: number;      // Zodiac circle radius
  inner_radius: number;      // Inner boundary
  planet_ring_radius: number; // Where planets are positioned
}
```

### PlanetData

```typescript
interface PlanetData {
  name: string;              // "sun", "moon", "mercury", etc.
  sign: string;              // "aries", "taurus", etc.
  sign_symbol: string;       // "♈", "♉", etc.
  degree: number;            // 0-360 (absolute zodiac position)
  signed_degree: number;     // 0-29.99 (position within sign)
  house: number;             // 1-12
  retrograde: boolean;
  element: string;           // "fire", "earth", "air", "water"
  modality: string;          // "cardinal", "fixed", "mutable"
  dms: string;               // "15°23'12\"" (degree/minute/second)
  position: Position;
  interpretation: PlanetInterpretation;
}

interface PlanetInterpretation {
  placement: string;         // Full interpretation paragraph
  keywords: string[];        // 3-5 keywords
}
```

### AspectData

```typescript
interface AspectData {
  body1: string;
  body2: string;
  aspect_type: string;       // "conjunction", "trine", "square", etc.
  aspect_symbol: string;     // "☌", "△", "□", etc.
  orb: number;               // Degrees from exact
  exact_degree: number;      // 0, 60, 90, 120, 180, etc.
  applying: boolean;         // true = applying, false = separating
  strength: string;          // "strong", "moderate", "weak"
  coords: {
    x1: number,
    y1: number,
    x2: number,
    y2: number
  };
  interpretation: AspectInterpretation;
}

interface AspectInterpretation {
  meaning: string;           // Full interpretation paragraph
  keywords: string[];        // 3-5 keywords
  orb_quality: string;       // "exact", "strong", "moderate", "weak"
}
```

### HouseData

```typescript
interface HouseData {
  number: number;            // 1-12
  cusp_degree: number;       // 0-360
  sign: string;
  sign_symbol: string;
  ruler: string;             // Ruling planet
  start_angle: number;       // Start of house (degrees)
  end_angle: number;         // End of house (degrees)
  position: {
    label_x: number,         // Position for house number label
    label_y: number,
    line_start_x: number,    // House cusp line start (center)
    line_start_y: number,
    line_end_x: number,      // House cusp line end (outer circle)
    line_end_y: number
  };
}
```

### AngleData

```typescript
interface AngleData {
  degree: number;
  sign: string;
  sign_symbol: string;
  dms: string;
  position: Position;
}

interface Angles {
  ascendant: AngleData;
  midheaven: AngleData;
  descendant: AngleData;
  ic: AngleData;
}
```

---

## Coordinate Calculation

### Overview

Backend must calculate **x/y coordinates** for all chart elements based on astrological degrees and a circular zodiac wheel layout.

**IMPORTANT:** Kerykeion provides built-in coordinate calculation functions. Use these instead of implementing from scratch.

### Coordinate System

- **Origin**: Center of chart (center_x, center_y)
- **0° Angle**: Varies based on chart orientation (typically Ascendant)
- **Angle Progression**: Counter-clockwise (standard astrological chart)
- **Coordinate Range**: 0 to 2*radius (functions return values relative to center)

### Use Kerykeion's Built-in Functions ✅ RECOMMENDED

Kerykeion provides proven coordinate functions in `kerykeion/charts/charts_utils.py`:

```python
from kerykeion.charts.charts_utils import sliceToX, sliceToY
import math

# Kerykeion's coordinate functions (already in the library)
def sliceToX(slice: float, radius: float, offset: float) -> float:
    """Calculate x-coordinate on circle.

    Args:
        slice: Not used for planets (set to 0)
        radius: Distance from center
        offset: Angle in degrees (0-360)

    Returns:
        x-coordinate (0 to 2*radius range)
    """
    plus = (math.pi * offset) / 180
    radial = ((math.pi / 6) * slice) + plus
    return radius * (math.cos(radial) + 1)

def sliceToY(slice: float, r: float, offset: float) -> float:
    """Calculate y-coordinate on circle.

    Args:
        slice: Not used for planets (set to 0)
        r: Radius distance from center
        offset: Angle in degrees (0-360)

    Returns:
        y-coordinate (0 to 2*r range)
    """
    plus = (math.pi * offset) / 180
    radial = ((math.pi / 6) * slice) + plus
    return r * ((math.sin(radial) / -1) + 1)
```

### Implementation Example

#### Calculate Planet Positions

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.charts_utils import sliceToX, sliceToY

# Create subject and chart data
subject = AstrologicalSubjectFactory.from_birth_data(
    name="User",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    lng=-74.0060, lat=40.7128,
    tz_str="America/New_York",
    online=False
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Chart parameters
chart_size = 600
center = chart_size / 2
planet_ring_radius = chart_size * 0.4  # 40% of chart size

# Calculate offset based on Ascendant (to orient chart correctly)
ascendant_degree = subject.first_house.abs_pos
offset_adjustment = 180 - ascendant_degree  # Orient Ascendant to left (9 o'clock)

# Calculate coordinates for each planet
planets_with_coords = []
for planet in subject.planets():
    # Calculate offset for this planet
    planet_offset = (planet.abs_pos + offset_adjustment) % 360

    # Use Kerykeion's functions (slice=0 for planets)
    x = sliceToX(0, planet_ring_radius, planet_offset)
    y = sliceToY(0, planet_ring_radius, planet_offset)

    planets_with_coords.append({
        "name": planet.name,
        "sign": planet.sign,
        "degree": planet.abs_pos,
        "house": planet.house,
        "x": x,
        "y": y,
        "retrograde": planet.retrograde
    })
```

#### House Cusp Lines

For each house cusp:
```python
# Calculate house cusp coordinates
houses_with_coords = []
for house in subject.houses():
    house_offset = (house.abs_pos + offset_adjustment) % 360

    # Line from center to outer circle
    line_end_x = sliceToX(0, outer_radius, house_offset)
    line_end_y = sliceToY(0, outer_radius, house_offset)

    houses_with_coords.append({
        "number": house.house,
        "cusp_degree": house.abs_pos,
        "sign": house.sign,
        "line_coords": {
            "x1": center,  # Center point
            "y1": center,
            "x2": line_end_x,
            "y2": line_end_y
        }
    })
```

#### Aspect Lines

Connect two planet positions (already calculated above):
```python
aspects_with_coords = []
for aspect in chart_data.aspects:
    # Find the two planets
    planet1 = next(p for p in planets_with_coords if p["name"] == aspect.p1_name)
    planet2 = next(p for p in planets_with_coords if p["name"] == aspect.p2_name)

    aspects_with_coords.append({
        "body1": aspect.p1_name,
        "body2": aspect.p2_name,
        "aspect_type": aspect.aspect,
        "orb": aspect.orbit,
        "coords": {
            "x1": planet1["x"],
            "y1": planet1["y"],
            "x2": planet2["x"],
            "y2": planet2["y"]
        }
    })
```

### Planet Overlap Detection (Optional but Recommended) ✅

Kerykeion includes sophisticated planet overlap detection in `kerykeion/charts/draw_planets.py`. When planets are closer than 3.4° apart, they are grouped and their positions are adjusted to prevent visual overlap.

**Reference from Kerykeion source (lines 94-163):**
```python
PLANET_GROUPING_THRESHOLD = 3.4  # Degrees

# Kerykeion automatically:
# 1. Sorts planets by degree
# 2. Groups planets within 3.4° of each other
# 3. Calculates position adjustments to spread them visually
# 4. Returns adjusted positions
```

**Recommendation**: Implement similar logic or use Kerykeion's approach:
- Detect planets within 3.4° of each other
- Adjust their x/y positions slightly (±2-5 pixels) to prevent overlap
- Return both raw and adjusted coordinates in response

**Example with adjustment:**
```python
{
    "name": "sun",
    "x": 315.5,
    "y": 185.3,
    "x_adjusted": 318.0,  # Slightly moved to avoid overlap
    "y_adjusted": 183.0,
    "overlapping_with": ["mercury"],  # Optional: list of nearby planets
    "adjustment_applied": true
}
```

### Coordinate Scaling

**Recommendation**: Use fixed base size of 600x600 for calculations. iOS will handle scaling to actual device dimensions.

```python
# Constants
BASE_CHART_SIZE = 600
CENTER = BASE_CHART_SIZE / 2
OUTER_RADIUS = BASE_CHART_SIZE * 0.47  # 47% of size
PLANET_RING_RADIUS = BASE_CHART_SIZE * 0.40  # 40% of size
INNER_RADIUS = BASE_CHART_SIZE * 0.33  # 33% of size
```

iOS will receive these coordinates and scale them:
```swift
// iOS side (for reference)
let scale = actualCanvasSize / 600.0
let scaledX = backendX * scale
let scaledY = backendY * scale
```

---

## Interpretation Text Guidelines

### Planet Interpretations

Format: **"Your [Planet] in [Sign] in the [House] house [interpretation]."**

Example:
```
"Your Sun in Gemini in the 10th house suggests a career focused on communication, teaching, or intellectual pursuits. You shine brightest when sharing ideas and connecting people through words."
```

Length: 2-3 sentences, ~100-150 characters

### Aspect Interpretations

Format: **"[Planet1] [aspect] [Planet2] [interpretation]. [Effect/advice]."**

Example:
```
"Sun trine Moon creates natural harmony between your conscious will and emotional needs. You feel at ease with yourself and can balance personal desires with emotional fulfillment."
```

Length: 2-3 sentences, ~100-150 characters

### Keywords

Provide 3-5 single-word or short-phrase keywords:
- Positive aspects: Uplifting words ("harmony", "ease", "flow")
- Challenging aspects: Growth-oriented words ("friction", "tension", "lesson")
- Neutral: Descriptive words ("intense", "active", "transformative")

### Content Source

**Phase 1**: Use pre-written astrological interpretation database
- Store in JSON file or Firestore collection
- Key: `{planet}_{sign}_{house}` or `{body1}_{aspect}_{body2}`

**Future Phase**: Generate with LLM (Claude/GPT) for personalized interpretations

---

## Error Handling

### Error Codes

| Code | HTTP Status | Description | User Message |
|------|-------------|-------------|--------------|
| `MISSING_BIRTH_DATA` | 400 | User has no birth data on file | "Please complete your birth information in settings" |
| `INVALID_DATE` | 400 | Date format invalid | "Invalid date format. Use YYYY-MM-DD" |
| `INVALID_LOCATION` | 400 | Location coordinates invalid | "Invalid location coordinates" |
| `CALCULATION_ERROR` | 500 | Kerykeion calculation failed | "Unable to calculate chart. Please try again" |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | "Please wait before requesting another chart" |
| `NOT_AUTHENTICATED` | 401 | Missing or invalid auth token | "Authentication required" |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "MISSING_BIRTH_DATA",
    "message": "User has not provided birth time/location",
    "details": {
      "user_id": "abc123",
      "has_birth_date": true,
      "has_birth_time": false,
      "has_birth_location": false
    }
  }
}
```

### Graceful Degradation

If certain data is unavailable:
- **No birth time**: Calculate chart for 12:00 PM (noon) and note `hasExactChart: false`
- **No birth location**: Use sun sign only (already have this data)
- **Interpretation missing**: Return empty string, iOS will hide interpretation section

---

## Implementation Notes

### Kerykeion Setup

#### Installation

```bash
pip install kerykeion>=5.1.7
```

#### Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

# Create subject (natal chart)
subject = AstrologicalSubjectFactory.from_birth_data(
    name="User",
    year=1990,
    month=6,
    day=15,
    hour=14,
    minute=30,
    lng=-74.0060,  # Longitude (negative = West)
    lat=40.7128,   # Latitude (positive = North)
    tz_str="America/New_York",
    online=False,  # Use provided coordinates (not GeoNames API)
    zodiac_type="Tropical",
    houses_system_identifier="P"  # Placidus
)

# Generate chart data
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Access planets
for planet in chart_data.first_subject.planets():
    print(f"{planet.name}: {planet.sign} {planet.position}° House {planet.house}")

# Access aspects
for aspect in chart_data.aspects:
    print(f"{aspect.p1_name} {aspect.aspect} {aspect.p2_name}, orb: {aspect.orbit}°")
```

#### Transit Chart

```python
from datetime import datetime

# Create transit subject for today
transit = AstrologicalSubjectFactory.from_birth_data(
    name="Transit",
    year=2025,
    month=11,
    day=5,
    hour=14,
    minute=30,
    lng=-74.0060,
    lat=40.7128,
    tz_str="America/New_York",
    online=False,
    zodiac_type="Tropical",
    houses_system_identifier="P"
)

transit_chart = ChartDataFactory.create_natal_chart_data(transit)
```

#### Transit-Natal Aspects

```python
from kerykeion import AspectsFactory

# Calculate aspects between transit and natal chart
synastry_aspects = AspectsFactory.dual_chart_aspects(
    natal_subject,
    transit_subject
)

for aspect in synastry_aspects.aspects:
    print(f"Transit {aspect.p1_name} {aspect.aspect} Natal {aspect.p2_name}")
```

### Performance Optimization

1. **Cache natal charts**: Store in Firestore, only recalculate when birth data changes
2. **Cache transit charts**: One transit chart per day (global), shared across users at same location
3. **Pre-calculate interpretations**: Don't generate interpretation text on-the-fly with LLM (too slow)
4. **Index Firestore**: Index `users/{user_id}/natal_chart` for fast retrieval

### Testing

Create test cases with known birth data:
```python
# Example: Steve Jobs
test_subject = AstrologicalSubjectFactory.from_birth_data(
    name="Steve Jobs",
    year=1955,
    month=2,
    day=24,
    hour=19,
    minute=15,
    lng=-122.4194,
    lat=37.7749,
    tz_str="America/Los_Angeles",
    online=False
)
```

Verify against known astrological software (Astro.com, etc.)

---

## Example Request/Response

### Example Request: get_natal_chart

```json
{
  "user_id": "abc123xyz",
  "force_regenerate": false,
  "chart_size": 600,
  "include_minor_planets": false
}
```

### Example Response (Abbreviated)

```json
{
  "success": true,
  "data": {
    "user_id": "abc123xyz",
    "chart_type": "natal",
    "birth_data": {
      "date": "1990-06-15",
      "time": "14:30",
      "timezone": "America/New_York",
      "location": {
        "city": "New York",
        "country": "US",
        "latitude": 40.7128,
        "longitude": -74.0060
      }
    },
    "viewport": {
      "center_x": 300,
      "center_y": 300,
      "outer_radius": 280,
      "inner_radius": 200,
      "planet_ring_radius": 240
    },
    "planets": [
      {
        "name": "sun",
        "sign": "gemini",
        "sign_symbol": "♊",
        "degree": 83.45,
        "signed_degree": 23.45,
        "house": 10,
        "retrograde": false,
        "element": "air",
        "modality": "mutable",
        "dms": "23°27'",
        "position": {
          "x": 315.5,
          "y": 185.3,
          "angle": 83.45
        },
        "interpretation": {
          "placement": "Your Sun in Gemini in the 10th house suggests a career focused on communication, teaching, or intellectual pursuits. You shine brightest when sharing ideas and connecting people through words.",
          "keywords": ["communicative", "versatile", "intellectual", "social"]
        }
      },
      {
        "name": "moon",
        "sign": "pisces",
        "sign_symbol": "♓",
        "degree": 343.2,
        "signed_degree": 13.2,
        "house": 7,
        "retrograde": false,
        "element": "water",
        "modality": "mutable",
        "dms": "13°12'",
        "position": {
          "x": 245.8,
          "y": 420.7,
          "angle": 343.2
        },
        "interpretation": {
          "placement": "Your Moon in Pisces in the 7th house makes you deeply empathetic in relationships. You intuitively understand others' emotions and seek spiritual or artistic connections with partners.",
          "keywords": ["empathetic", "intuitive", "romantic", "sensitive"]
        }
      }
    ],
    "aspects": [
      {
        "body1": "sun",
        "body2": "moon",
        "aspect_type": "trine",
        "aspect_symbol": "△",
        "orb": 2.3,
        "exact_degree": 120,
        "applying": true,
        "strength": "strong",
        "coords": {
          "x1": 315.5,
          "y1": 185.3,
          "x2": 245.8,
          "y2": 420.7
        },
        "interpretation": {
          "meaning": "Sun trine Moon creates natural harmony between your conscious will and emotional needs. You feel at ease with yourself and can balance personal desires with emotional fulfillment.",
          "keywords": ["harmony", "emotional balance", "ease", "confidence"],
          "orb_quality": "strong"
        }
      }
    ],
    "metadata": {
      "zodiac_type": "tropical",
      "house_system": "placidus",
      "calculation_date": "2025-11-05T10:30:00Z",
      "cached": false,
      "kerykeion_version": "5.1.7"
    }
  }
}
```

---

## Questions for Backend Team

1. **Timeline**: What is the estimated timeline for implementing these endpoints?
   - **Note**: Implementation should be simpler now - Kerykeion provides all coordinate functions

2. **Interpretation Content**: Who will create the planet/aspect interpretation text database? Do you need astrological content from iOS team?

3. **Caching**: Should natal charts be cached in Firestore or in-memory cache (Redis)? What's the cache invalidation strategy?

4. **Coordinate Calculation**: ✅ RESOLVED - Use Kerykeion's `sliceToX`/`sliceToY` functions from `charts_utils.py`

5. **Planet Overlap**: Should backend use Kerykeion's automatic overlap detection logic (from `draw_planets.py`)?
   - **Recommendation**: Yes, implement it to provide adjusted coordinates

6. **Testing**: What test birth data should we use for QA? Should we use famous people with known charts?
   - **Suggestion**: Use Johnny Depp (June 9, 1963) - Kerykeion's own test data

7. **Rate Limiting**: What rate limits should we enforce? Firebase Functions have cold start times - how to handle?

8. **Error Monitoring**: What error monitoring/logging is in place for chart calculation failures?

9. **AGPL License**: Kerykeion is AGPL-3.0. Does this require backend source code to be open-source? Do we need alternative library or commercial license?

---

## Next Steps

1. **Backend Review**: Backend team reviews this spec and provides feedback
   - ✅ **Advantage**: Kerykeion provides working reference code for all calculations

2. **Prototype**: Backend team creates simple prototype with 1-2 planets to verify coordinate system
   - **Simplified**: Just call `sliceToX`/`sliceToY` with planet degrees
   - **Test**: Use Johnny Depp's birth data (Kerykeion's test case)

3. **Content Creation**: Create or source interpretation text database
   - Static text initially, can upgrade to LLM later

4. **iOS Mock Data**: iOS team creates mock JSON for UI development in parallel
   - Can use Kerykeion's coordinate formulas to generate realistic test data

5. **Integration Testing**: Test API with real iOS app once endpoints are deployed
   - Verify coordinates render correctly
   - Test with multiple birth charts

6. **Documentation**: Backend team documents any deviations from this spec
   - Note which features from Kerykeion were used (overlap detection, etc.)

---

## Implementation Simplifications (v1.1)

After analyzing Kerykeion source code, the following simplifications were identified:

### ✅ What's Easier Now:

1. **Coordinate Calculation**: Built-in functions (`sliceToX`, `sliceToY`) - no need to derive formulas
2. **Planet Overlap**: Reference implementation in `draw_planets.py` (lines 94-163)
3. **JSON Export**: All Kerykeion models use Pydantic with `.model_dump_json()`
4. **Testing**: Existing test data and expected outputs in Kerykeion test suite
5. **Proven System**: Coordinate functions already used for SVG generation

### 📚 Reference Code Locations:

- **Coordinate functions**: `kerykeion/charts/charts_utils.py` (lines 332-378)
- **Planet overlap logic**: `kerykeion/charts/draw_planets.py` (lines 94-163)
- **Chart drawing reference**: `kerykeion/charts/chart_drawer.py`
- **Test data**: `kerykeion/tests/test_astrological_subject.py`

### ⏱️ Estimated Time Savings:

- **Backend**: 30-40% reduction in implementation time
- **iOS**: 15-20% reduction (less debugging of coordinate issues)
- **Overall**: ~1 week saved from original 4-6 week timeline

---

**Document Owner**: iOS Team
**Backend Team Contact**: [TBD]
**Questions/Feedback**: [Email/Slack channel]

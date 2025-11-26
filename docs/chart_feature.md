# Natal Chart Visualization Feature - Implementation Plan

**Version:** 1.2
**Date:** 2025-11-24
**Status:** Ready for Backend Handoff
**Owner:** iOS Team

---

## Related Documentation

**This feature works alongside the Compatibility feature.** Backend team should implement both:

| Doc | Feature | Endpoints |
|-----|---------|-----------|
| `docs/natal-chart-visualization-plan.md` (this doc) | Charts Tab - user's own natal/transit charts | `get_natal_chart`, `get_transit_chart` |
| `docs/compatibility-backend-prd.md` | Connections Tab - compare with others | `get_compatibility`, `get_natal_chart_for_connection`, invite flow |

Both features share Kerykeion infrastructure and coordinate system.

---

## Executive Summary

This document outlines the implementation plan for adding interactive natal chart visualization to the ARCA astrology app. The feature includes:
- New "Charts" tab with natal chart visualization, sun sign details, and compatibility charts
- Enhancement to "Dig Deeper" feature showing transit charts with natal overlays
- Fully interactive SwiftUI components with tap gestures, zoom/pan, and filtering
- Backend integration using Kerykeion Python library for astrological calculations

**Update (v1.2):** Converted open questions to decisions. Added Backend API specification. Ready for handoff.

**Update (v1.1):** After analyzing the Kerykeion library source code, we've confirmed that backend can easily calculate x/y coordinates using built-in functions (`sliceToX`, `sliceToY`). This significantly simplifies implementation and reduces risk.

## Table of Contents

1. [Feature Overview](#feature-overview)
2. [Current State](#current-state)
3. [Architecture Decisions](#architecture-decisions)
4. [Backend API Specification](#backend-api-specification)
5. [Implementation Phases](#implementation-phases)
6. [Technical Specifications](#technical-specifications)
7. [Dependencies](#dependencies)
8. [Testing Strategy](#testing-strategy)

---

## Feature Overview

### Charts Tab (New)

The Charts tab will be the 4th tab in the main navigation, containing:

1. **Natal Chart View**
   - Interactive circular zodiac wheel showing birth chart
   - Displays planets, houses, aspects with full astrological data
   - Tap planets to see placement interpretations
   - Tap aspect lines to see aspect meanings
   - Pinch to zoom, pan gestures
   - Filter controls to toggle visibility of elements

2. **Sun Sign Detail View**
   - Deep dive into user's sun sign
   - Uses existing `SunSignProfile` data from backend
   - Traits, keywords, dignities, element, polarity

3. **Compatibility Charts View**
   - Placeholder for future synastry/composite charts
   - Will compare user's chart with partners/friends

### Dig Deeper Enhancement

Enhancement to existing "Today" view's Dig Deeper feature:

- **Transit Chart** - Shows today's planetary positions in zodiac wheel
- **Natal Overlay** - Toggle to overlay user's natal chart on transits
- **Intersection Analysis** - Visual explanation of how transits affect natal positions
- **Horoscope Connection** - Shows how today's horoscope was generated from transit-natal aspects

---

## Current State

### Existing Data Models

#### BirthChart (Complete)
Location: `arca/arca/Models/BirthChart.swift`

Already contains all necessary astrological data:
```swift
struct BirthChart: Codable {
    let planets: [PlanetPosition]      // All 10 planets with positions
    let houses: [HouseCusp]            // 12 houses with rulers
    let aspects: [AspectData]          // Planetary aspects with orbs
    let angles: ChartAngles            // ASC, IC, DSC, MC
    let distributions: ChartDistributions  // Elements, modalities, etc.
}

struct PlanetPosition: Codable {
    let name: String                   // "sun", "moon", "mercury"...
    let sign: String                   // "aries", "taurus"...
    let signSymbol: String             // ♈, ♉, ♊
    let degree: Double                 // 0-360
    let signedDegree: Double           // 0-29 (within sign)
    let house: Int                     // 1-12
    let retrograde: Bool
    let element: String
    let modality: String
    let dms: String                    // "15°23'"
}

struct AspectData: Codable {
    let body1: String
    let body2: String
    let aspectType: String             // "conjunction", "trine", "square"...
    let aspectSymbol: String           // ☌, △, □
    let orb: Double
    let applying: Bool
    let exactDegree: Int
}
```

#### UserProfile
Location: `arca/arca/Models/UserProfile.swift`

Already stores natal chart:
```swift
struct UserProfile: Codable {
    let sunSignProfile: SunSignProfile  // Complete sun sign data
    var natalChart: BirthChart?         // Natal chart (if available)
    var hasExactChart: Bool             // true if birth time provided
    // ... other fields
}
```

#### SunSignProfile (Complete)
Location: `arca/arca/Models/SunSignProfile.swift`

Already contains all sun sign detail data:
```swift
struct SunSignProfile: Codable {
    let sign: String
    let dates: String
    let glyph: String
    let element: String
    let summary: String
    let keywords: [String]
    let polarity: String
    let ruling_planet: String
    let planetary_dignities: PlanetaryDignities
    let positive_traits: [String]
    let shadow_traits: [String]
}
```

### Existing Architecture Patterns

- **MVVM-inspired**: Views + Managers (singleton services)
- **Local-first caching**: UserDefaults with date validation
- **Firebase Functions**: Python backend for all API calls
- **Navigation**: `NavigationStack` with tab-based navigation
- **iOS 17+**: Modern SwiftUI APIs
- **Theme system**: Semantic colors in `Theme/Colors.swift`

---

## Architecture Decisions

### 1. Backend Returns: JSON + Geometric Coordinates (Option A - Selected ✅)

**Decision**: Backend calculates both astrological data AND geometric positions for UI elements using Kerykeion's built-in coordinate functions.

**Rationale**:
- Kerykeion includes proven coordinate calculation functions (`sliceToX`, `sliceToY` in `charts_utils.py`)
- Backend already uses these functions for SVG generation
- Coordinate system is well-tested and handles edge cases (planet overlap, grouping)
- Sending x/y coordinates reduces iOS computation and ensures consistency with Kerykeion's proven algorithms
- iOS focuses purely on rendering and interactivity
- Backend can handle planet overlap adjustments (Kerykeion has sophisticated grouping logic for planets < 3.4° apart)

**What Backend Sends**:
- Planet positions (astrological degrees: `abs_pos`)
- Geometric coordinates (x, y) calculated using Kerykeion's functions
- Optional: Adjusted positions for overlapping planets
- Aspect line coordinates (x1, y1, x2, y2)
- Chart viewport parameters (center, radius)

**Kerykeion Reference Code**:
```python
# From kerykeion/charts/charts_utils.py
def sliceToX(slice, radius, offset):
    plus = (math.pi * offset) / 180
    radial = ((math.pi / 6) * slice) + plus
    return radius * (math.cos(radial) + 1)

def sliceToY(slice, r, offset):
    plus = (math.pi * offset) / 180
    radial = ((math.pi / 6) * slice) + plus
    return r * ((math.sin(radial) / -1) + 1)
```

Backend can directly use these functions with planet degrees as input.

### 2. Interpretations from Backend

**Decision**: All interpretation text comes from backend, not hardcoded in iOS.

**Rationale**:
- Backend can update interpretations without requiring app updates
- Centralized content management
- Can start with static text, upgrade to LLM-generated later
- iOS app size stays smaller

**What Backend Sends**:
- Planet placement interpretations (e.g., "Sun in Scorpio 8th house...")
- Aspect interpretations (e.g., "Sun trine Moon creates harmony...")
- Keywords for quick reference

### 3. Native SwiftUI Rendering (Not SVG)

**Decision**: iOS renders charts natively using SwiftUI Canvas, not pre-rendered SVGs.

**Rationale**:
- Full interactivity (tap, zoom, pan, filter)
- Better performance for gestures
- Smooth animations and transitions
- Native look and feel
- Backend can still generate SVG for other purposes if needed

### 4. Reusable Chart Component

**Decision**: Build single `AstroChartWheel` component that works for both natal and transit charts.

**Rationale**:
- Code reusability
- Consistent UI/UX across features
- Easier maintenance
- Same component used in Charts tab and Dig Deeper

### 5. House System

**Decision**: Default to Placidus. Accept `house_system` parameter for alternatives.

**Supported values**: `placidus` (default), `whole_sign`, `equal_house`, `koch`, `regiomontanus`

### 6. Planet Overlap Handling

**Decision**: Backend handles overlap adjustment using Kerykeion's built-in grouping logic (planets < 3.4 degrees apart).

**Response includes**:
- `degree`: Actual astrological position (for display text)
- `displayX` / `displayY`: Adjusted coordinates for rendering (may differ from raw position when planets overlap)

### 7. Minor Planets

**Decision**: Major planets only for v1. No asteroids (Chiron, Juno, etc.).

**Included**: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto

### 8. Interpretation Delivery

**Decision**: Interpretations included in chart response (not separate endpoint).

Each planet and aspect includes a `summary` field (1-2 sentences) for display on tap. Full interpretations can be added in a future version.

---

## Backend API Specification

### Endpoint: `get_natal_chart`

**Request:**
```json
{
  "user_id": "string",
  "house_system": "placidus"  // optional, defaults to placidus
}
```

**Response:**
```json
{
  "success": true,
  "chart": {
    "planets": [
      {
        "name": "sun",
        "sign": "scorpio",
        "signSymbol": "\u264f",
        "degree": 215.5,
        "signedDegree": 5.5,
        "house": 8,
        "retrograde": false,
        "element": "water",
        "modality": "fixed",
        "dms": "5\u00b030'",
        "displayX": 0.35,
        "displayY": 0.72,
        "summary": "Sun in Scorpio in the 8th house indicates intensity and transformative power in matters of shared resources and deep emotional bonds."
      }
    ],
    "houses": [
      {
        "number": 1,
        "sign": "aries",
        "degree": 0.0,
        "startX": 0.5,
        "startY": 0.0,
        "endX": 0.5,
        "endY": 0.15
      }
    ],
    "aspects": [
      {
        "body1": "sun",
        "body2": "moon",
        "aspectType": "trine",
        "aspectSymbol": "\u25b3",
        "orb": 2.5,
        "applying": true,
        "x1": 0.35,
        "y1": 0.72,
        "x2": 0.65,
        "y2": 0.28,
        "summary": "Sun trine Moon creates harmony between your core identity and emotional nature."
      }
    ],
    "angles": {
      "ascendant": { "degree": 0.0, "sign": "aries" },
      "midheaven": { "degree": 270.0, "sign": "capricorn" },
      "descendant": { "degree": 180.0, "sign": "libra" },
      "imumCoeli": { "degree": 90.0, "sign": "cancer" }
    }
  }
}
```

### Endpoint: `get_transit_chart`

**Request:**
```json
{
  "user_id": "string",
  "date": "2025-11-24",  // optional, defaults to today
  "include_natal_overlay": true  // optional, include natal positions for comparison
}
```

**Response:** Same structure as `get_natal_chart`, plus optional `natal_aspects` array showing transit-to-natal aspects when `include_natal_overlay` is true.

### Coordinate System

All coordinates are **normalized 0.0 to 1.0**:
- `(0.0, 0.0)` = top-left of chart bounding box
- `(1.0, 1.0)` = bottom-right of chart bounding box
- `(0.5, 0.5)` = center of chart

iOS multiplies by actual view dimensions to get pixel positions.

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "MISSING_BIRTH_DATA",
    "message": "User profile does not contain birth time required for natal chart"
  }
}
```

**Error codes**: `MISSING_BIRTH_DATA`, `INVALID_USER`, `CALCULATION_ERROR`, `RATE_LIMITED`

---

## Implementation Phases

### Phase 1: Backend Integration (Kerykeion)

**Goal**: Backend can generate natal and transit chart data with geometric coordinates and interpretations.

**Tasks**:
1. Install Kerykeion library in Firebase Functions environment
2. Implement `get_natal_chart` endpoint (see Backend API spec)
3. Implement `get_transit_chart` endpoint
4. Create interpretation text database or service
5. Test coordinate calculation algorithm
6. Document API responses

**Dependencies**: Backend team, Kerykeion library setup

**Deliverable**: Working API endpoints returning JSON with all required data

---

### Phase 2: iOS Data Models & Service Layer

**Goal**: iOS can fetch, parse, and cache chart data from backend.

**Tasks**:

1. **Create new models**:
   - `ChartGeometry.swift` - Position data structures
   - `PlanetInterpretation.swift` - Interpretation text
   - `AspectInterpretation.swift` - Aspect meanings
   - `TransitChart.swift` - Transit chart data

2. **Extend existing models**:
   - Add `geometry` field to `BirthChart`
   - Add `interpretation` field to `PlanetPosition`
   - Add `interpretation` field to `AspectData`

3. **Create service manager**:
   - `ChartService.swift` - Fetch/cache charts
   - Methods: `fetchNatalChart()`, `fetchTransitChart()`
   - Cache natal chart in UserDefaults (static data)
   - Transit chart with date-based validation

**Files to Create**:
```
arca/arca/Models/
├── ChartGeometry.swift          (NEW)
├── PlanetInterpretation.swift   (NEW)
├── AspectInterpretation.swift   (NEW)
├── TransitChart.swift           (NEW)

arca/arca/Managers/
├── ChartService.swift           (NEW)
```

**Dependencies**: Phase 1 (backend API)

**Deliverable**: Data models and service layer ready for UI integration

---

### Phase 3: Core Chart Component

**Goal**: Build reusable interactive chart wheel component.

**Tasks**:

1. **AstroChartWheel.swift** - Main chart component
   - Canvas-based rendering
   - Draw zodiac circle with 12 signs
   - Draw 12 house divisions
   - Position planets using backend coordinates
   - Draw aspect lines between planets
   - Color coding by aspect type

2. **PlanetGlyph.swift** - Tappable planet symbol
   - Unicode planet symbols (☉☽☿♀♂♃♄♅♆♇)
   - Retrograde indicator (Rx)
   - Tap gesture → detail sheet
   - Highlight on selection

3. **AspectLine.swift** - Tappable aspect line
   - Geometric line between planets
   - Color by aspect type (trine=blue, square=red, etc.)
   - Line style (solid/dashed for applying/separating)
   - Tap gesture → aspect info sheet

4. **ChartLegend.swift** - Filter controls
   - Toggle aspects visibility
   - Toggle houses visibility
   - Toggle minor planets
   - Show/hide different aspect types

5. **Gesture Support**:
   - Pinch to zoom (scale factor)
   - Pan gesture (drag to explore)
   - Tap gestures for planets and aspects
   - Double-tap to reset zoom

**Files to Create**:
```
arca/arca/Views/Components/
├── AstroChartWheel.swift        (NEW)
├── PlanetGlyph.swift            (NEW)
├── AspectLine.swift             (NEW)
├── ChartLegend.swift            (NEW)
├── PlanetDetailSheet.swift      (NEW)
├── AspectDetailSheet.swift      (NEW)
```

**Dependencies**: Phase 2 (data models)

**Deliverable**: Fully interactive chart component ready for integration

---

### Phase 4: Charts Tab

**Goal**: New tab in main navigation with natal chart and sun sign detail.

**Tasks**:

1. **Update MainNavigationView.swift**:
   - Add 4th tab: "Charts"
   - Tab bar icon (chart.xyaxis.line or similar)
   - Navigation routing

2. **ChartsTabView.swift** - Container view
   - Section navigation (Natal Chart, Sun Sign, Compatibility)
   - ScrollView layout
   - Header with user's sun sign

3. **NatalChartView.swift** - Natal chart page
   - Use `AstroChartWheel` component
   - Load natal chart from UserProfile
   - Full-screen chart with controls
   - Loading states and error handling

4. **SunSignDetailView.swift** - Sun sign deep dive
   - Reuse existing `SunSignProfile` data
   - Display traits, keywords, dignities
   - Element, polarity, ruling planet
   - Can reuse/refactor existing `SunSignDetailSheet` from onboarding

5. **CompatibilityPlaceholderView.swift** - Future feature
   - Coming soon message
   - Placeholder for synastry charts

**Files to Create**:
```
arca/arca/Views/Main/
├── ChartsTabView.swift          (NEW)
├── NatalChartView.swift         (NEW)
├── SunSignDetailView.swift      (NEW - or refactor existing)
├── CompatibilityPlaceholderView.swift (NEW)
```

**Files to Modify**:
```
arca/arca/Views/Main/
├── MainNavigationView.swift     (ADD 4th tab)
```

**Dependencies**: Phase 3 (chart component)

**Deliverable**: Working Charts tab with natal chart and sun sign detail

---

### Phase 5: Dig Deeper Enhancement

**Goal**: Add transit chart with natal overlay to Dig Deeper feature.

**Tasks**:

1. **DigDeeperView.swift** - New view for transit analysis
   - Use `AstroChartWheel` for transit chart
   - Toggle button to overlay natal chart
   - Show transit-natal aspects
   - Connect to LLM interpretation explaining daily horoscope

2. **Transit Overlay Logic**:
   - Render two layers (transit outer, natal inner)
   - Different visual styling (colors, sizes)
   - Highlight transit-natal aspects
   - Legend explaining colors

3. **Integration with Today View**:
   - Add "Dig Deeper" button/section in MainView
   - Navigation to DigDeeperView
   - Pass daily horoscope data

**Files to Create**:
```
arca/arca/Views/Main/
├── DigDeeperView.swift          (NEW)
├── TransitAnalysisCard.swift    (NEW)
```

**Files to Modify**:
```
arca/arca/Views/Main/
├── MainView.swift               (ADD Dig Deeper navigation)
```

**Dependencies**: Phase 3 (chart component), Backend transit analysis endpoint

**Deliverable**: Dig Deeper feature showing how transits create daily horoscope

---

## Technical Specifications

### Chart Rendering Details

#### Canvas-Based Drawing

Using SwiftUI `Canvas` for high-performance rendering:

```swift
Canvas { context, size in
    let center = CGPoint(x: size.width / 2, y: size.height / 2)
    let radius = min(size.width, size.height) / 2 - padding

    // Draw zodiac circle
    drawZodiacCircle(context, center, radius)

    // Draw houses
    drawHouses(context, center, radius, houses)

    // Draw aspect lines (behind planets)
    drawAspects(context, center, radius, aspects)

    // Draw planets
    drawPlanets(context, center, radius, planets)
}
.gesture(zoomGesture)
.gesture(panGesture)
```

#### Coordinate System

- **Backend**: Returns x/y coordinates relative to chart center and radius
- **iOS**: Scales coordinates to actual Canvas size
- **Angle**: 0° = East (Ascendant), increases counterclockwise

#### Color Scheme

Using existing ARCA theme colors:

- **Harmonious aspects** (trine, sextile): `.arcaSuccess` (green)
- **Challenging aspects** (square, opposition): `.arcaWarning` (orange/red)
- **Neutral aspects** (conjunction): `.arcaMystical` (purple)
- **Background**: `.arcaBackground`
- **Text**: `.arcaText`

#### Planet Symbols

Unicode glyphs:
- Sun: ☉
- Moon: ☽
- Mercury: ☿
- Venus: ♀
- Mars: ♂
- Jupiter: ♃
- Saturn: ♄
- Uranus: ♅
- Neptune: ♆
- Pluto: ♇

#### Aspect Symbols

Unicode glyphs:
- Conjunction: ☌
- Opposition: ☍
- Trine: △
- Square: □
- Sextile: ⚹
- Quincunx: ⚻

### Performance Considerations

1. **Caching**:
   - Natal chart: Cache permanently (doesn't change)
   - Transit chart: Cache with date validation (refresh daily)
   - Sun sign data: Already cached in UserProfile

2. **Rendering Optimization**:
   - Use `.drawingGroup()` for complex Canvas drawings
   - Lazy loading of interpretation text
   - Debounce zoom/pan gestures

3. **Network**:
   - Fetch natal chart only once on first Charts tab visit
   - Background refresh of transit chart
   - Graceful degradation if network unavailable

### Accessibility

1. **VoiceOver Support**:
   - Meaningful labels for all planets and aspects
   - Announce planet placements (e.g., "Sun in Scorpio, 8th house")
   - Aspect descriptions

2. **Dynamic Type**:
   - Scalable text in detail sheets
   - Adjust glyph sizes based on accessibility settings

3. **High Contrast Mode**:
   - Ensure aspect lines visible in high contrast
   - Thicker lines for better visibility

---

## Dependencies

### External Libraries

1. **Kerykeion** (Backend, Python)
   - Version: 5.1.7+
   - License: AGPL-3.0 (requires compliance)
   - Purpose: Astrological calculations

### Internal Dependencies

1. **Existing Models**:
   - `BirthChart.swift`
   - `UserProfile.swift`
   - `SunSignProfile.swift`

2. **Existing Services**:
   - `AuthManager.swift` - User authentication
   - Firebase Functions client

3. **Existing Components**:
   - `Colors.swift` - Theme system
   - `GaugeView.swift` - Reference for Canvas drawing patterns

---

## Testing Strategy

### Unit Tests

1. **Data Models**:
   - Test JSON decoding of chart data
   - Test coordinate scaling calculations
   - Test interpretation text parsing

2. **Chart Service**:
   - Test API call success/failure
   - Test caching logic
   - Test date validation for transits

### Integration Tests

1. **Backend Integration**:
   - Test natal chart fetch
   - Test transit chart fetch
   - Test error handling

### UI Tests

1. **Chart Interaction**:
   - Test tap gestures on planets
   - Test tap gestures on aspects
   - Test zoom and pan
   - Test filter toggles

2. **Navigation**:
   - Test Charts tab navigation
   - Test Dig Deeper navigation
   - Test detail sheet presentation

### Manual Testing Checklist

- [ ] Natal chart renders correctly for various birth dates
- [ ] Transit chart shows accurate current positions
- [ ] All planets are tappable and show correct information
- [ ] Aspect lines render correctly and are tappable
- [ ] Zoom and pan work smoothly
- [ ] Filters toggle visibility correctly
- [ ] Works on different device sizes (iPhone SE to Pro Max)
- [ ] Dark mode support
- [ ] VoiceOver navigation works
- [ ] Performance is smooth (60fps)

---

## Milestones

| Phase | Milestone | Blocked By |
|-------|-----------|------------|
| 1 | Backend APIs working, returning chart JSON with coordinates | - |
| 2 | iOS can fetch, parse, and cache chart data | Phase 1 |
| 3 | Interactive chart component working in isolation | Phase 2 |
| 4 | Charts tab functional in app | Phase 3 |
| 5 | Dig Deeper feature complete, ready for QA | Phase 3 |

### Critical Path

1. Backend API (Phase 1) - BLOCKING all other work
   - **Simplified**: Backend team has Kerykeion reference code for all calculations
   - Use `sliceToX`/`sliceToY` from `charts_utils.py`
   - Optionally use planet grouping logic from `draw_planets.py` (lines 94-163)
2. Data models (Phase 2) - BLOCKING UI work
   - **Simplified**: Just add geometry fields to existing models
3. Core chart component (Phase 3) - BLOCKING both Charts tab and Dig Deeper
   - **Simplified**: Render at provided coordinates, no calculation needed
4. Charts tab and Dig Deeper can proceed in parallel after Phase 3

---

## Resolved Decisions

| Question | Decision |
|----------|----------|
| **Licensing** | AGPL-3.0 approved for backend use |
| **Interpretation Content** | Static text for v1, LLM-generated in future |
| **Compatibility Charts** | Deferred to Phase 6, Charts tab designed to accommodate |
| **Minor Planets** | Major planets only for v1 (10 bodies) |
| **House Systems** | Placidus default, parameter for alternatives |
| **Planet Overlap** | Backend handles using Kerykeion's grouping logic |

---

## Success Metrics

1. **User Engagement**:
   - Charts tab visit rate (target: 60%+ of users within first week)
   - Average time spent on natal chart (target: 2+ minutes)
   - Dig Deeper feature usage (target: 30%+ of daily horoscope views)

2. **Technical Performance**:
   - Chart render time < 500ms
   - API response time < 2s
   - 60fps during zoom/pan interactions

3. **User Satisfaction**:
   - Feature rating via in-app feedback
   - Support ticket volume related to charts
   - App Store review mentions

---

## Future Enhancements

1. **Compatibility Charts** (Phase 6):
   - Synastry: Compare two natal charts
   - Composite: Create midpoint chart between two people
   - Social features: Share compatibility with friends

2. **Advanced Transits** (Phase 7):
   - Show future transits (next week, month, year)
   - Transit timeline view
   - Notifications for important transits

3. **Chart Variations** (Phase 8):
   - Solar return chart (birthday chart for current year)
   - Lunar return chart
   - Progressed chart
   - Relocation chart

4. **Export & Sharing** (Phase 9):
   - Export chart as image
   - Share on social media
   - Print-friendly version

---

## Resources

### Documentation
- Kerykeion Documentation: https://github.com/g-battaglia/kerykeion
- SwiftUI Canvas: https://developer.apple.com/documentation/swiftui/canvas
- Astrological Symbols Unicode: https://en.wikipedia.org/wiki/Astrological_symbols

### Team Contacts
- Backend Lead: [TBD]
- iOS Lead: [TBD]
- Design: [TBD]
- Content/Astrology Expert: [TBD]

---

**Document Status**: APPROVED - Ready for implementation
**Next Steps**:
1. Backend team implements `get_natal_chart` and `get_transit_chart` endpoints
2. iOS team begins Phase 2 (data models) once backend API is available
3. Design team provides mockups for Charts tab UI

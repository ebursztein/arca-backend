# Unified Connections & Charts Feature Plan

**Version:** 2.0
**Date:** 2025-11-26
**Status:** Ready for Backend Review
**Supersedes:** `compatibility_v1.md`, `ios_charts_implementation_guide.md`

---

## Executive Summary

This plan unifies the Connections tab redesign with chart visualization and compatibility features. The goal is a cohesive experience where users can:

1. Manage connections with a modern UI (pinned partner, request notifications)
2. View compatibility analysis (synastry) with each connection
3. View their own natal/transit charts
4. View synastry charts overlaying two natal charts

---

## Backend API Requirements

### Endpoints Checklist

Please confirm status of each endpoint:

| Endpoint | iOS Needs | Purpose |
|----------|-----------|---------|
| `get_natal_chart` | Geometry + interpretations | User's natal chart with x/y coordinates |
| `get_transit_chart` | Geometry + natal overlay | Today's transits with optional natal overlay |
| `get_compatibility` | All 3 modes in one call | Romantic/friendship/coworker scores + categories |
| `get_synastry_chart` | Overlay geometry | Two charts overlaid with cross-aspects |
| `create_connection` | Exists | Add connection manually |
| `list_connections` | Firestore query | Get user's connections |
| `delete_connection` | Exists | Remove connection |
| `get_share_link` | Exists | Generate share URL |
| `get_public_profile` | Exists | Preview profile from share link |
| `import_connection` | Exists | Add from share link |
| `list_connection_requests` | Exists | Get pending requests for user |
| `respond_to_request` | Exists | Approve/reject with action param |
| `update_share_mode` | Exists | Toggle public/request mode |

### Questions for Backend

1. **Synastry chart**: Is this a separate endpoint or part of `get_compatibility`?
2. **Chart geometry**: Does `get_compatibility` already include synastry aspect x/y coordinates?
3. **Rate limits**: What are the limits on chart generation endpoints?
4. **FCM push**: Is push notification sent when someone requests to connect?

---

## Chart Geometry Format

All chart endpoints should return normalized 0.0-1.0 coordinates:

```json
{
  "planets": [{
    "name": "sun",
    "sign": "scorpio",
    "signSymbol": "\u264f",
    "degree": 215.5,
    "signedDegree": 5.5,
    "house": 8,
    "retrograde": false,
    "displayX": 0.35,
    "displayY": 0.72,
    "interpretation": "Sun in Scorpio in the 8th house..."
  }],
  "houses": [{
    "number": 1,
    "sign": "aries",
    "degree": 0.0,
    "startX": 0.5,
    "startY": 0.0,
    "endX": 0.5,
    "endY": 0.15
  }],
  "aspects": [{
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
    "interpretation": "Sun trine Moon creates harmony..."
  }]
}
```

Coordinates are normalized so iOS multiplies by view dimensions.

---

## Synastry Chart Response

**Request:**
```json
{
  "user_id": "string",
  "connection_id": "string"
}
```

**Response:**
```json
{
  "userChart": { /* ChartGeometry - inner ring */ },
  "connectionChart": { /* ChartGeometry - outer ring */ },
  "synastryAspects": [{
    "userPlanet": "sun",
    "connectionPlanet": "moon",
    "aspectType": "conjunction",
    "orb": 1.5,
    "x1": 0.35,
    "y1": 0.72,
    "x2": 0.38,
    "y2": 0.70,
    "interpretation": "Your Sun conjunct their Moon..."
  }]
}
```

---

## Connection Request Flow

### Existing Backend (confirm these work):

1. **Privacy modes**: Users set `share_mode` to "public" or "request"
2. **Request creation**: When importing a user in request mode, `ConnectionRequest` created
3. **Request model**:
   ```json
   {
     "request_id": "string",
     "from_user_id": "string",
     "from_name": "string",
     "status": "pending|approved|rejected",
     "created_at": "string"
   }
   ```

### iOS Integration:

- `list_connection_requests` - Fetch pending requests on tab appear
- `respond_to_request` - Call with `action: "approve"` or `action: "reject"`
- FCM push - Handle `type: "connection_request"` payload

---

## Compatibility Response

### Categories by Mode

Each mode returns **different categories** (not just different weights):

**Romantic (6 categories):**
| ID | Name |
|----|------|
| `emotional` | Emotional Connection |
| `communication` | Communication |
| `attraction` | Attraction |
| `values` | Shared Values |
| `longTerm` | Long-term Potential |
| `growth` | Growth Together |

**Friendship (5 categories):**
| ID | Name |
|----|------|
| `emotional` | Emotional Bond |
| `communication` | Communication |
| `fun` | Fun & Adventure |
| `loyalty` | Loyalty & Support |
| `sharedInterests` | Shared Interests |

**Coworker (5 categories):**
| ID | Name |
|----|------|
| `communication` | Communication |
| `collaboration` | Collaboration |
| `reliability` | Reliability |
| `ambition` | Ambition Alignment |
| `powerDynamics` | Power Dynamics |

### Response Format

```json
{
  "romantic": {
    "overallScore": 78,
    "relationshipVerb": "You spark each other",
    "categories": [
      {
        "id": "emotional",
        "name": "Emotional Connection",
        "score": 65,
        "summary": "Strong emotional understanding...",
        "aspectIds": ["sun_moon_trine", "venus_mars_square"]
      }
    ],
    "missingDataPrompts": ["Add birth time for more accurate results"]
  },
  "friendship": { /* same structure */ },
  "coworker": { /* same structure */ },
  "aspects": [
    {
      "id": "sun_moon_trine",
      "userPlanet": "sun",
      "theirPlanet": "moon",
      "aspectType": "trine",
      "orb": 2.5,
      "interpretation": "Your Sun trine their Moon...",
      "isHarmonious": true
    }
  ],
  "compositeSummary": {
    "compositeSun": "Sagittarius",
    "compositeMoon": "Cancer",
    "summary": "Together you create...",
    "strengths": ["Communication", "Shared values"],
    "challenges": ["Different pace", "Independence needs"]
  }
}
```

---

## Entity Model Fields

### Connection Categories

```
partner   - Only ONE allowed per user
family    - Family members
friend    - Friends
coworker  - Work relationships
other     - Everything else
```

### Relationship Labels (by category)

**Partner:** partner, spouse, boyfriend, girlfriend
**Family:** mother, father, sister, brother, son, daughter, grandmother, grandfather, aunt, uncle, cousin
**Friend:** friend, bestFriend
**Coworker:** boss, manager, colleague, mentor, employee

### Mode Mapping

| Category | Compatibility Mode Used |
|----------|------------------------|
| Partner | Romantic |
| Family | Friendship |
| Friend | Friendship |
| Coworker | Coworker |

---

## iOS Implementation Summary

### New UI Layout (Connections Tab)

```
+--------------------------------------------------+
|              GlassHeader (blue accent)           |
|  [icon] CONNECTIONS           [Add] [Share]     |
+--------------------------------------------------+
|                                                  |
|  [avatar] [avatar] [avatar]   <- Connection      |
|   Anna     Mike    +3          Requests (if any) |
|                                                  |
+--------------------------------------------------+
|  Pinned                                          |
|  +---------------------+  +-------------------+  |
|  |    [large initial]  |  |  (empty slot)    |  |
|  |       Sarah         |  |                  |  |
|  |      Partner        |  |                  |  |
|  |          85         |  |                  |  |
|  +---------------------+  +-------------------+  |
+--------------------------------------------------+
|  Filter: [All] [Friends] [Family] [Work]         |
+--------------------------------------------------+
|  All Connections                                 |
|  +----------------------------------------------+|
|  | [J]  John Smith                         92  ||
|  |      Best Friend                            ||
|  +----------------------------------------------+|
```

### Key Changes

1. **Connection requests** - Horizontal scroll at top when pending
2. **Pinned partner** - Half-width card, auto-pinned for partner category
3. **Simplified rows** - Initial letter avatar, score badge (no gauge)
4. **Filter tabs** - Removed "Partner" (now in pinned section)

### Connection Detail Additions

- Charts section with options:
  - Their Natal Chart
  - Synastry Chart (overlay)
  - Composite Chart (future)

---

## Caching Strategy (iOS)

| Data | Duration | Notes |
|------|----------|-------|
| User's natal chart | Forever | Birth data doesn't change |
| Connection's natal chart | Forever | Invalidate if birth data updated |
| Transit chart | 24 hours | Refresh daily |
| Compatibility result | 7 days | All 3 modes cached together |
| Synastry chart | 7 days | Invalidate if birth data updated |
| Connection requests | On-demand | Fetched on tab appear |

---

## Backend Team Checklist

Please confirm availability:

- [ ] `get_natal_chart` - Chart geometry with normalized coordinates
- [ ] `get_transit_chart` - Transit positions + natal overlay option
- [ ] `get_compatibility` - All 3 modes in single response
- [ ] `get_synastry_chart` - Overlay geometry for two charts
- [ ] `list_connection_requests` - Pending requests list
- [ ] `respond_to_request` - Approve/reject action
- [ ] `update_share_mode` - Toggle public/request
- [ ] FCM push for connection requests

---

## Document History

- **v2.0** (2025-11-26): Unified plan combining UI redesign + charts + compatibility
- Supersedes: `compatibility_v1.md`, `ios_charts_implementation_guide.md`

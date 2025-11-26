# Backend API: Charts, Connections & Compatibility

**Version:** 1.0
**Date:** 2025-11-25
**Status:** Ready for Implementation

---

## Quick Reference

### Implementation Phases
1. **Phase 1: Chart Visualization** - `get_natal_chart`, `get_transit_chart` endpoints + coordinates
2. **Phase 2: Connections** - Share links, `import_connection`, `create_connection`, CRUD
3. **Phase 3: Compatibility** - `get_compatibility` with synastry scoring + LLM interpretations
4. **Phase 4: Daily Horoscope Integration** - Relationship weather with connection vibes

### New Files to Create
- `functions/charts.py` - Chart visualization + coordinate calculation
- `functions/compatibility.py` - Synastry calculation + scoring + LLM
- `functions/connections.py` - Connection CRUD + share links

### Files to Modify
- `functions/models.py` - Connection, RelationshipWeather, CompatibilityResult models
- `functions/main.py` - New Cloud Function endpoints
- `functions/astro.py` - Coordinate helpers
- `functions/templates/horoscope/daily_static.j2` - Relationship weather instructions
- `functions/templates/horoscope/daily_dynamic.j2` - Connection data for LLM

### Table of Contents
1. [Executive Summary](#executive-summary) - Architecture overview
2. [Firestore Collections](#firestore-collections) - Data structure
3. [Chart Visualization APIs](#chart-visualization) - `get_natal_chart`, `get_transit_chart`
4. [Compatibility APIs](#compatibility) - `get_compatibility`, categories, scoring
5. [Connection APIs](#connections) - Share links, CRUD, privacy modes
6. [Rate Limits](#rate-limits)
7. [Security](#security-considerations)
8. [Daily Horoscope Integration](#integration-with-daily-horoscope) - Relationship weather
9. [INTERNAL: Implementation Details](#internal-implementation-changes-required) - Code examples, prompts, edge cases

---

## Executive Summary

Unified backend API for Chart Visualization and Compatibility features.

**Key Architecture Decisions:**

1. **"Add Me on Arca" Model**: Each user has a shareable profile link. Connections are independent copies in each user's world.
2. **Privacy Controls**: Public vs Request-Only modes for profile sharing
3. **Notification Loop**: Adding someone triggers notification to prompt reciprocal connection
4. **Stateless Computation**: Charts computed fresh (fast), LLM interpretations generated per-request, iOS caches everything
5. **Memory Integration**: Compatibility usage stats feed into user memory

**Design Principles:**
- Minimize Firebase reads (batch operations)
- Minimize LLM calls (single call per compatibility request)
- No backend caching of charts/interpretations (iOS handles caching)
- Compute everything fresh (natal library is fast)

---

## Firestore Collections

```
root/
├── users/{userId}/
│   ├── [existing UserProfile fields]
│   ├── share_secret: "abc123xyz"           # Random URL token for profile sharing
│   ├── share_mode: "public" | "request"    # Privacy control
│   ├── connections/
│   │   └── {connectionId}/
│   │       ├── name: "Sarah"
│   │       ├── birth_date: "1990-05-15"
│   │       ├── birth_time: "14:30"         # Optional
│   │       ├── birth_lat: 40.7128          # Optional
│   │       ├── birth_lon: -74.0060         # Optional
│   │       ├── birth_timezone: "America/New_York"  # Optional
│   │       ├── relationship_type: "friend" | "romantic" | "family" | "coworker"
│   │       ├── source_user_id: "xyz789"    # Who they imported from (if via link)
│   │       └── created_at: timestamp
│   └── connection_requests/                # For "request" mode users
│       └── {requestId}/
│           ├── from_user_id: "abc123"
│           ├── from_name: "John"
│           ├── status: "pending" | "approved" | "rejected"
│           └── created_at: timestamp

├── share_links/{share_secret}/             # Reverse lookup for share URLs
│   ├── user_id: "abc123"
│   └── created_at: timestamp

└── memory/{userId}/
    └── compatibility_summary: {
          total_checks: 5,
          relationship_types: {"romantic": 3, "friend": 2},
          last_check_date: "2025-11-25"
        }
```

---

## API Endpoints

### Chart Visualization

#### `get_natal_chart`

Returns user's natal chart with geometric coordinates for iOS visualization.

**Request:**
```json
{
  "user_id": "firebase_uid",
  "house_system": "placidus"
}
```

**Response:**
```json
{
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
        "interpretation": "Sun in Scorpio in the 8th house..."
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
        "interpretation": "Sun trine Moon creates harmony..."
      }
    ],
    "angles": {
      "ascendant": {"degree": 0.0, "sign": "aries", "x": 1.0, "y": 0.5},
      "midheaven": {"degree": 270.0, "sign": "capricorn", "x": 0.5, "y": 0.0},
      "descendant": {"degree": 180.0, "sign": "libra", "x": 0.0, "y": 0.5},
      "imumCoeli": {"degree": 90.0, "sign": "cancer", "x": 0.5, "y": 1.0}
    }
  },
  "has_exact_chart": true
}
```

**Coordinate System:**
- All coordinates normalized 0.0 to 1.0
- (0.5, 0.5) = center of chart
- iOS multiplies by view dimensions

---

#### `get_transit_chart`

Returns current transit positions with optional natal overlay.

**Request:**
```json
{
  "user_id": "firebase_uid",
  "date": "2025-11-25",
  "include_natal_overlay": true
}
```

**Response:**
Same structure as `get_natal_chart`, plus:
```json
{
  "transit_to_natal_aspects": [
    {
      "transit_planet": "mars",
      "natal_planet": "sun",
      "aspectType": "square",
      "orb": 1.2,
      "interpretation": "Transit Mars square your natal Sun..."
    }
  ]
}
```

---

#### `get_natal_chart_for_connection`

Returns chart for a connection (arbitrary birth data).

**Request:**
```json
{
  "birth_date": "1990-05-15",
  "birth_time": "14:30",
  "birth_lat": 40.7128,
  "birth_lon": -74.0060,
  "birth_timezone": "America/New_York"
}
```

**Response:** Same structure as `get_natal_chart`

---

### Compatibility

#### `get_compatibility`

Compares user's chart with a connection. Returns all three modes in single response.

**Request:**
```json
{
  "user_id": "firebase_uid",
  "connection_id": "conn_abc123"
}
```

**Response:**
```json
{
  "romantic": {
    "overall_score": 78,
    "relationship_verb": "You spark each other",
    "categories": [
      {"id": "emotional", "name": "Emotional Connection", "score": 65, "summary": "You feel safe with each other...", "aspect_ids": ["asp_001", "asp_002"]},
      {"id": "communication", "name": "Communication", "score": 82, "summary": "You get each other without trying...", "aspect_ids": ["asp_003"]},
      {"id": "attraction", "name": "Attraction", "score": 45, "summary": "Chemistry builds slowly...", "aspect_ids": ["asp_004"]},
      {"id": "values", "name": "Shared Values", "score": -20, "summary": "You want different things...", "aspect_ids": ["asp_005"]},
      {"id": "longTerm", "name": "Long-term Potential", "score": 70, "summary": "Built to last if you work at it...", "aspect_ids": ["asp_006"]},
      {"id": "growth", "name": "Growth Together", "score": 55, "summary": "You push each other to evolve...", "aspect_ids": ["asp_007"]}
    ],
    "missing_data_prompts": []
  },
  "friendship": {
    "overall_score": 85,
    "relationship_verb": "You click",
    "categories": [
      {"id": "emotional", "name": "Emotional Bond", "score": 72, "summary": "You get each other on a deep level...", "aspect_ids": ["asp_001"]},
      {"id": "communication", "name": "Communication", "score": 88, "summary": "Conversations flow naturally...", "aspect_ids": ["asp_003"]},
      {"id": "fun", "name": "Fun & Adventure", "score": 90, "summary": "You have a blast together...", "aspect_ids": ["asp_008"]},
      {"id": "loyalty", "name": "Loyalty & Support", "score": 75, "summary": "You can count on each other...", "aspect_ids": ["asp_006"]},
      {"id": "sharedInterests", "name": "Shared Interests", "score": 68, "summary": "Plenty of common ground...", "aspect_ids": ["asp_009"]}
    ],
    "missing_data_prompts": []
  },
  "coworker": {
    "overall_score": 72,
    "relationship_verb": "You balance each other",
    "categories": [
      {"id": "communication", "name": "Communication", "score": 78, "summary": "Clear professional communication...", "aspect_ids": ["asp_003"]},
      {"id": "collaboration", "name": "Collaboration", "score": 65, "summary": "Different styles that complement...", "aspect_ids": ["asp_010"]},
      {"id": "reliability", "name": "Reliability", "score": 82, "summary": "You can depend on each other...", "aspect_ids": ["asp_006"]},
      {"id": "ambition", "name": "Ambition Alignment", "score": 60, "summary": "Similar drive levels...", "aspect_ids": ["asp_011"]},
      {"id": "powerDynamics", "name": "Power Dynamics", "score": -15, "summary": "Watch for control issues...", "aspect_ids": ["asp_012"]}
    ],
    "missing_data_prompts": []
  },
  "aspects": [
    {
      "id": "asp_001",
      "user_planet": "moon",
      "their_planet": "venus",
      "aspect_type": "trine",
      "orb": 3.5,
      "interpretation": "Your emotional needs align with how they show love.",
      "is_harmonious": true
    }
  ],
  "composite_summary": {
    "composite_sun": "Libra",
    "composite_moon": "Cancer",
    "summary": "Together you act like a Libra couple...",
    "strengths": ["Natural diplomacy", "Shared aesthetics"],
    "challenges": ["Decision paralysis", "Conflict avoidance"]
  },
  "calculated_at": "2025-11-25T14:30:00Z"
}
```

**Category Scoring:**
- Category scores: -100 to +100 (negative = challenging)
- Overall score: 0 to 100
- **Each mode has DIFFERENT categories** (see below)

---

### Compatibility Categories by Mode

Each mode returns different categories with different underlying planet aspects.

#### Romantic Mode (6 categories)

| Category ID | Name | Driving Aspects | Notes |
|-------------|------|-----------------|-------|
| `emotional` | Emotional Connection | Moon-Moon, Moon-Venus, Moon-Neptune, Moon-IC | Requires birth time |
| `communication` | Communication | Mercury-Mercury, Mercury-Moon, Mercury-Venus | |
| `attraction` | Attraction | Venus-Mars, Mars-Mars, Venus-ASC, Mars-ASC | Requires birth time for ASC |
| `values` | Shared Values | Venus-Venus, Jupiter-Jupiter, Sun-Jupiter, Venus-Jupiter | |
| `longTerm` | Long-term Potential | Saturn-Sun, Saturn-Moon, Saturn-Venus, Sun-Sun | |
| `growth` | Growth Together | Pluto aspects, Node aspects, Saturn-Pluto | Transformation potential |

#### Friendship Mode (5 categories)

| Category ID | Name | Driving Aspects | Notes |
|-------------|------|-----------------|-------|
| `emotional` | Emotional Bond | Moon-Moon, Moon-Venus, Sun-Moon | |
| `communication` | Communication | Mercury-Mercury, Mercury-Jupiter, Mercury-Sun | Includes humor |
| `fun` | Fun & Adventure | Jupiter-Jupiter, Sun-Sun, Mars-Jupiter, Venus-Jupiter | |
| `loyalty` | Loyalty & Support | Saturn-Moon, Saturn-Sun, Sun-Saturn | |
| `sharedInterests` | Shared Interests | Venus-Venus, Mercury-Venus, Moon-Venus | |

#### Coworker Mode (5 categories)

| Category ID | Name | Driving Aspects | Notes |
|-------------|------|-----------------|-------|
| `communication` | Communication | Mercury-Mercury, Mercury-Saturn, Mercury-Mars | Professional style |
| `collaboration` | Collaboration | Sun-Sun, Mars-Mars, Sun-Mars | Working together |
| `reliability` | Reliability | Saturn-Sun, Saturn-Moon, Saturn-Saturn | Dependability |
| `ambition` | Ambition Alignment | Mars-Saturn, Jupiter-Saturn, Mars-Jupiter | Drive compatibility |
| `powerDynamics` | Power Dynamics | Pluto-Sun, Pluto-Mars, Mars-Pluto | Conflict/leadership |

---

### Aspect Scoring Logic

**Aspect Quality:**
- Harmonious (trine, sextile, conjunction*): Positive score contribution
- Challenging (square, opposition): Negative score contribution
- *Conjunction: Depends on planets involved (Venus-Mars = positive, Saturn-Mars = challenging)

**Aspect Weight by Orb:**
- 0-2 degrees: 100% weight (tight aspect)
- 2-5 degrees: 75% weight
- 5-8 degrees: 50% weight
- 8-10 degrees: 25% weight (wide aspect)

**Category Score Calculation:**
```
category_score = sum(aspect_score * aspect_weight) / max_possible_score * 100
```
Normalized to -100 to +100 range.

**Overall Score Calculation:**
```
overall_score = (sum(category_scores) + 600) / 12
```
Normalized to 0-100 range (50 = neutral).

---

**Missing Data Handling:**
- If birth time missing: Omit Emotional category, Moon/ASC aspects, set composite_moon to null
- If birth location missing: Omit house-dependent data, planet signs still accurate

---

### Connections

#### `get_share_link`

Returns user's permanent share link.

**Request:**
```json
{
  "user_id": "firebase_uid"
}
```

**Response:**
```json
{
  "share_url": "https://arca-app.com/u/abc123xyz",
  "share_mode": "public",
  "qr_code_data": "https://arca-app.com/u/abc123xyz"
}
```

---

#### `get_public_profile`

Fetches public profile data from share link (for import).

**Request:**
```json
{
  "share_secret": "abc123xyz"
}
```

**Response (public mode):**
```json
{
  "profile": {
    "name": "John",
    "birth_date": "1990-06-15",
    "birth_time": "14:30",
    "birth_lat": 40.7128,
    "birth_lon": -74.0060,
    "birth_timezone": "America/New_York",
    "sun_sign": "gemini"
  },
  "share_mode": "public",
  "can_add": true
}
```

**Response (request mode):**
```json
{
  "profile": {
    "name": "John",
    "sun_sign": "gemini"
  },
  "share_mode": "request",
  "can_add": false,
  "message": "John requires approval to share compatibility data"
}
```

---

#### `import_connection`

Adds a connection from a share link.

**Request:**
```json
{
  "user_id": "firebase_uid",
  "share_secret": "abc123xyz",
  "relationship_type": "friend"
}
```

**Response (public mode - instant):**
```json
{
  "success": true,
  "connection_id": "conn_xyz789",
  "connection": {
    "name": "John",
    "sun_sign": "gemini"
  },
  "notification_sent": true
}
```

**Side Effects:**
- Creates connection in user's `connections/` subcollection
- Sends push notification to profile owner: "Sarah added you! Add her back to see compatibility"
- If request mode: Creates entry in owner's `connection_requests/`

---

#### `create_connection`

Manually create a connection (not via share link).

**Request:**
```json
{
  "user_id": "firebase_uid",
  "connection": {
    "name": "Sarah",
    "birth_date": "1990-05-15",
    "birth_time": "14:30",
    "birth_lat": 40.7128,
    "birth_lon": -74.0060,
    "birth_timezone": "America/New_York",
    "relationship_type": "romantic"
  }
}
```

---

#### `update_connection`

Update connection details (name, relationship type, etc).

---

#### `delete_connection`

Remove a connection from user's list.

---

#### `list_connections`

List all user's connections.

**Response:**
```json
{
  "connections": [...],
  "total_count": 5
}
```

---

#### `update_share_mode`

Toggle between public and request-only modes.

**Request:**
```json
{
  "user_id": "firebase_uid",
  "share_mode": "request"
}
```

---

#### `respond_to_request`

Approve or reject a connection request (for request-mode users).

**Request:**
```json
{
  "user_id": "firebase_uid",
  "request_id": "req_abc123",
  "action": "approve"
}
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `get_compatibility` | 10 | per day |
| `import_connection` | 20 | per day |
| `create_connection` | 20 | per day |

Returns HTTP 429 with `Retry-After` header when exceeded.

---

## API Summary

| Endpoint | Auth | Description |
|----------|------|-------------|
| `get_natal_chart` | Yes | User's natal chart with coordinates |
| `get_transit_chart` | Yes | Transit chart with natal overlay |
| `get_natal_chart_for_connection` | Yes | Chart for connection's birth data |
| `get_compatibility` | Yes | Synastry analysis (all 3 modes) |
| `get_share_link` | Yes | User's shareable profile link |
| `get_public_profile` | No* | Fetch profile from share link |
| `import_connection` | Yes | Add connection from share link |
| `create_connection` | Yes | Manually add connection |
| `update_connection` | Yes | Edit connection details |
| `delete_connection` | Yes | Remove connection |
| `list_connections` | Yes | List all connections |
| `update_share_mode` | Yes | Toggle public/request mode |
| `respond_to_request` | Yes | Approve/reject connection request |

*Rate-limited by IP

---

## Integration with Daily Horoscope

### Relationship Weather Enhancement

The daily horoscope's `relationship_weather` field is enhanced to include connection-specific vibes.

**New Structure in DailyHoroscope:**
```json
{
  "relationship_weather": {
    "overview": "Venus trine Jupiter today brings warmth to all your connections. Romantic relationships feel easy and flowy. Friendships are energizing. Even work relationships have a collaborative spirit.",
    "connection_vibes": [
      {
        "connection_id": "conn_123",
        "name": "Sarah",
        "relationship_type": "romantic",
        "vibe": "Today's a great day to connect with Sarah - harmony flows easily between you two.",
        "vibe_score": 75,
        "key_transit": "Transit Venus trine your Venus-Mars midpoint"
      },
      {
        "connection_id": "conn_456",
        "name": "John",
        "relationship_type": "coworker",
        "vibe": "Good day to collaborate with John - ideas will click.",
        "vibe_score": 60,
        "key_transit": "Transit Mercury sextile your Mercury-Mercury conjunction"
      }
    ]
  }
}
```

### Which Connections to Include

Top 10 connections selected by recency:
1. Most recently viewed (compatibility checked)
2. Most recently added
3. Up to 10 total

### Transit-to-Synastry Calculation

For each connection, check today's transits against synastry points:
- Transit planets aspecting synastry midpoints
- Transit planets activating natal-to-natal aspects
- Focus on Venus, Mars, Mercury, Moon transits (fast-moving, daily relevance)

### LLM Generation

Single LLM call generates:
- Overview paragraph (covers all relationship types)
- Individual vibe sentence for each connection (max 10)
- Key transit explanation (technical, for "why?" tap)

### Fallback

If user has no connections:
```json
{
  "relationship_weather": {
    "overview": "Venus trine Jupiter today brings warmth to relationships...",
    "connection_vibes": []
  }
}
```

---

## INTERNAL: Implementation Changes Required

### 1. Modify DailyHoroscope Model (`functions/models.py`)

Add new Pydantic models:
```python
class ConnectionVibe(BaseModel):
    connection_id: str
    name: str
    relationship_type: Literal["friend", "romantic", "family", "coworker"]
    vibe: str  # Personalized: "Good day to collaborate with John..."
    vibe_score: int  # 0-100
    key_transit: str  # Technical explanation

class RelationshipWeather(BaseModel):
    overview: str  # General paragraph covering all relationship types
    connection_vibes: list[ConnectionVibe] = []  # Top 10 connections

# Update DailyHoroscope model:
class DailyHoroscope(BaseModel):
    # ... existing fields ...
    relationship_weather: RelationshipWeather  # Replace old str field
```

### 2. Update Prompt Templates (`functions/templates/horoscope/`)

**Modify `daily_dynamic.j2`** to include connection data:
```jinja
## User's Connections (for relationship weather)
{% if connections %}
{% for conn in connections %}
- {{ conn.name }} ({{ conn.relationship_type }}): Synastry points at {{ conn.synastry_degrees }}
{% endfor %}
{% else %}
No connections added yet.
{% endif %}
```

**Modify `daily_static.j2`** to add instructions:
```jinja
## Relationship Weather Instructions

Generate relationship_weather with:
1. overview: One paragraph covering romantic, friendship, and coworker relationship vibes today (2-3 sentences)
2. connection_vibes: For each connection provided, generate:
   - vibe: Personalized sentence WITH THEIR NAME, e.g. "Good day to collaborate with John - ideas will click."
   - vibe_score: 0-100 based on transit harmony
   - key_transit: Technical explanation of the transit hitting their synastry

Keep vibes actionable and specific to the relationship type.
```

### 3. Update `get_daily_horoscope` Function (`functions/main.py`)

```python
# In get_daily_horoscope():

# 1. Fetch user's connections (top 10 by recency)
connections_ref = db.collection("users").document(user_id).collection("connections")
connections_docs = connections_ref.order_by("created_at", direction=firestore.Query.DESCENDING).limit(10).get()

# 2. For each connection, calculate synastry points being hit by today's transits
connection_data = []
for doc in connections_docs:
    conn = doc.to_dict()
    # Calculate which synastry degrees are active today
    synastry_degrees = calculate_synastry_points(user_chart, conn)
    active_transits = find_transits_to_synastry(transit_chart, synastry_degrees)
    connection_data.append({
        "connection_id": doc.id,
        "name": conn["name"],
        "relationship_type": conn["relationship_type"],
        "synastry_degrees": synastry_degrees,
        "active_transits": active_transits
    })

# 3. Pass to LLM prompt
daily_horoscope = await generate_daily_horoscope(
    # ... existing params ...
    connections=connection_data  # NEW
)
```

### 4. New Helper Functions (`functions/compatibility.py`)

```python
def calculate_synastry_points(user_chart: dict, connection: dict) -> list[float]:
    """Calculate key synastry midpoints/conjunctions between two charts."""
    # Venus-Mars midpoints, Moon-Moon, etc.
    pass

def find_transits_to_synastry(transit_chart: dict, synastry_degrees: list[float], orb: float = 3.0) -> list[dict]:
    """Find today's transits aspecting synastry points."""
    # Check Venus, Mars, Mercury, Moon transits
    pass
```

### 5. Files to Modify

| File | Changes |
|------|---------|
| `functions/models.py` | Add ConnectionVibe, RelationshipWeather models; update DailyHoroscope |
| `functions/templates/horoscope/daily_static.j2` | Add relationship weather generation instructions |
| `functions/templates/horoscope/daily_dynamic.j2` | Add connections data section |
| `functions/main.py` | Fetch connections in get_daily_horoscope, pass to LLM |
| `functions/compatibility.py` | Add synastry point calculation helpers |

---

### 6. Example Vibe Strings by Scenario

**Positive vibes (vibe_score 60-100):**
```
Romantic:
- "Today's a great day to connect with Sarah - harmony flows easily between you two."
- "Plan something special with Sarah tonight - the stars are aligned for romance."
- "Sarah's on your wavelength today - deep conversations will feel effortless."

Friendship:
- "Perfect day to hang out with Mike - you'll have a blast together."
- "Reach out to Mike today - your friendship energy is strong."
- "Adventures with Mike will be extra fun today - say yes to spontaneity."

Coworker:
- "Good day to collaborate with John - ideas will click."
- "John's your best ally in meetings today - team up."
- "Brainstorming with John will be productive - schedule that sync."

Family:
- "Great day to call Mom - she'll appreciate hearing from you."
- "Family time with Dad feels warm today - lean into it."
```

**Neutral vibes (vibe_score 40-60):**
```
- "Steady energy with Sarah today - nothing dramatic, just comfortable."
- "Normal day with John - no friction, no fireworks."
- "Mike's around but not a priority today - catch up later."
```

**Challenging vibes (vibe_score 0-40):**
```
- "Give Sarah some space today - tension is in the air."
- "Not the best day to push John on deadlines - patience needed."
- "Mike might be in a mood - don't take it personally."
- "Avoid heavy conversations with Mom today - keep it light."
- "Power struggles possible with John - pick your battles."
- "Miscommunications likely with Sarah - double-check assumptions."
```

---

### 7. Synastry Point Calculation Details

**Key synastry points to track (degrees 0-360):**

```python
def calculate_synastry_points(user_chart: dict, connection_chart: dict) -> list[dict]:
    """
    Calculate key synastry points between two charts.
    Returns list of {degree, type, planets} for transit checking.
    """
    points = []

    # 1. Conjunctions (same degree, orb 8)
    # User Venus conjunct Connection Mars = attraction point
    user_venus = user_chart["planets"]["venus"]["degree"]
    conn_mars = connection_chart["planets"]["mars"]["degree"]
    if abs(user_venus - conn_mars) <= 8:
        midpoint = (user_venus + conn_mars) / 2
        points.append({
            "degree": midpoint,
            "type": "venus_mars_conjunction",
            "label": "attraction point",
            "planets": ["venus", "mars"]
        })

    # 2. Moon-Moon midpoint (emotional connection)
    user_moon = user_chart["planets"]["moon"]["degree"]
    conn_moon = connection_chart["planets"]["moon"]["degree"]
    moon_midpoint = (user_moon + conn_moon) / 2
    points.append({
        "degree": moon_midpoint,
        "type": "moon_moon_midpoint",
        "label": "emotional connection point",
        "planets": ["moon", "moon"]
    })

    # 3. Sun-Sun midpoint (identity/ego connection)
    user_sun = user_chart["planets"]["sun"]["degree"]
    conn_sun = connection_chart["planets"]["sun"]["degree"]
    sun_midpoint = (user_sun + conn_sun) / 2
    points.append({
        "degree": sun_midpoint,
        "type": "sun_sun_midpoint",
        "label": "core identity point",
        "planets": ["sun", "sun"]
    })

    # 4. Mercury-Mercury midpoint (communication)
    user_mercury = user_chart["planets"]["mercury"]["degree"]
    conn_mercury = connection_chart["planets"]["mercury"]["degree"]
    mercury_midpoint = (user_mercury + conn_mercury) / 2
    points.append({
        "degree": mercury_midpoint,
        "type": "mercury_mercury_midpoint",
        "label": "communication point",
        "planets": ["mercury", "mercury"]
    })

    # 5. Venus-Venus midpoint (values/affection)
    user_venus = user_chart["planets"]["venus"]["degree"]
    conn_venus = connection_chart["planets"]["venus"]["degree"]
    venus_midpoint = (user_venus + conn_venus) / 2
    points.append({
        "degree": venus_midpoint,
        "type": "venus_venus_midpoint",
        "label": "affection point",
        "planets": ["venus", "venus"]
    })

    return points
```

---

### 8. Transit-to-Synastry Detection

```python
def find_transits_to_synastry(
    transit_chart: dict,
    synastry_points: list[dict],
    orb: float = 3.0
) -> list[dict]:
    """
    Find today's transits that aspect synastry points.
    Focus on fast-moving planets for daily relevance.
    """
    active_transits = []

    # Fast-moving planets to check (daily relevance)
    transit_planets = ["moon", "mercury", "venus", "mars", "sun"]

    # Aspects to check
    aspects = {
        "conjunction": 0,
        "opposition": 180,
        "trine": 120,
        "square": 90,
        "sextile": 60
    }

    for planet in transit_planets:
        transit_degree = transit_chart["planets"][planet]["degree"]

        for point in synastry_points:
            for aspect_name, aspect_angle in aspects.items():
                # Check if transit is aspecting synastry point
                diff = abs(transit_degree - point["degree"])
                if diff > 180:
                    diff = 360 - diff

                aspect_diff = abs(diff - aspect_angle)

                if aspect_diff <= orb:
                    is_harmonious = aspect_name in ["trine", "sextile", "conjunction"]

                    active_transits.append({
                        "transit_planet": planet,
                        "aspect": aspect_name,
                        "synastry_point": point["type"],
                        "synastry_label": point["label"],
                        "orb": round(aspect_diff, 1),
                        "is_harmonious": is_harmonious,
                        "description": f"Transit {planet.title()} {aspect_name} your {point['label']}"
                    })

    # Sort by orb (tightest aspects first)
    active_transits.sort(key=lambda x: x["orb"])

    return active_transits
```

---

### 9. Full Prompt Template Example

**In `daily_dynamic.j2`:**
```jinja
## User's Connections for Relationship Weather

{% if connections and connections|length > 0 %}
You have {{ connections|length }} connection(s) to generate vibes for:

{% for conn in connections %}
### {{ conn.name }} ({{ conn.relationship_type }})
Synastry points:
{% for point in conn.synastry_points %}
- {{ point.label }}: {{ point.degree|round(1) }}°
{% endfor %}

Active transits hitting this connection today:
{% if conn.active_transits %}
{% for transit in conn.active_transits %}
- {{ transit.description }} (orb {{ transit.orb }}°) - {{ "harmonious" if transit.is_harmonious else "challenging" }}
{% endfor %}
{% else %}
- No major transits activating this connection today
{% endif %}

{% endfor %}
{% else %}
No connections added yet. Generate overview only, leave connection_vibes as empty array.
{% endif %}
```

**In `daily_static.j2`:**
```jinja
## Relationship Weather Output Format

Generate the relationship_weather field with this structure:

{
  "relationship_weather": {
    "overview": "2-3 sentences covering the general vibe for ALL relationship types today (romantic, friendships, work relationships). Base this on Venus, Mars, Mercury positions and aspects.",
    "connection_vibes": [
      // For EACH connection provided above, generate:
      {
        "connection_id": "the connection_id from the data",
        "name": "their name",
        "relationship_type": "their relationship type",
        "vibe": "A personalized 1-sentence vibe INCLUDING THEIR NAME. Examples:
                 - 'Today's a great day to connect with Sarah - harmony flows easily.'
                 - 'Give Mike some space today - tension is in the air.'
                 - 'Good day to collaborate with John - ideas will click.'
                 Make it actionable and specific to the relationship type.",
        "vibe_score": 0-100 based on how harmonious the active transits are,
        "key_transit": "The most significant transit, e.g. 'Transit Venus trine your emotional connection point'"
      }
    ]
  }
}

IMPORTANT:
- vibe MUST include the person's name naturally in the sentence
- vibe_score: 70-100 = positive, 40-70 = neutral, 0-40 = challenging
- If no active transits, vibe_score should be 50 (neutral) with a "steady energy" type vibe
- key_transit should be the tightest orb transit, or "No major transits today" if none
```

---

### 10. Edge Cases to Handle

| Scenario | Handling |
|----------|----------|
| User has 0 connections | `connection_vibes: []`, overview still generated |
| User has 50 connections | Only fetch top 10 by recency |
| Connection missing birth time | Still calculate Sun/Mercury/Venus/Mars synastry (skip Moon) |
| Connection missing birth location | Calculate all planet synastry (skip houses) |
| No transits hitting synastry | vibe_score = 50, vibe = "Steady day with {name}" |
| Multiple strong transits | Pick the tightest orb for key_transit, vibe reflects overall |
| All transits challenging | Don't be doom-and-gloom, frame constructively |

---

### 11. Vibe Score Calculation

```python
def calculate_vibe_score(active_transits: list[dict]) -> int:
    """
    Calculate vibe score (0-100) from active transits.
    """
    if not active_transits:
        return 50  # Neutral if no transits

    # Weight by orb (tighter = more impact)
    total_score = 0
    total_weight = 0

    for transit in active_transits:
        # Orb weight: 0° = 1.0, 3° = 0.0
        orb_weight = max(0, 1 - (transit["orb"] / 3.0))

        # Aspect score: harmonious = +1, challenging = -1
        aspect_score = 1 if transit["is_harmonious"] else -1

        total_score += aspect_score * orb_weight
        total_weight += orb_weight

    if total_weight == 0:
        return 50

    # Normalize to 0-100 (where -1 to +1 maps to 0 to 100)
    normalized = (total_score / total_weight + 1) / 2  # 0 to 1
    return int(normalized * 100)
```

---

### 12. Breaking Change for iOS

**Old `relationship_weather` format:**
```json
"relationship_weather": "Venus trine Jupiter brings warmth to relationships today..."
```

**New `relationship_weather` format:**
```json
"relationship_weather": {
  "overview": "Venus trine Jupiter brings warmth...",
  "connection_vibes": [...]
}
```

**iOS must update:**
- Change `relationshipWeather: String?` to `relationshipWeather: RelationshipWeather`
- Handle backward compatibility during rollout (check if it's string vs object)
- Update UI to show connection vibe cards

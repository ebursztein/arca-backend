# iOS Integration Guide

**Last Updated:** 2025-11-29

For complete API reference (all endpoints, request/response schemas), see **`PUBLIC_API_GENERATED.md`**.

---

## Core Endpoints for iOS

| Feature | Endpoint | Notes |
|---------|----------|-------|
| **Onboarding** | `create_user_profile` | Creates profile + natal chart + LLM summary |
| **Profile Update** | `update_user_profile` | Update birth time/location, regenerates chart |
| **Sun Sign** | `get_sun_sign_from_date` | Quick lookup without full profile |
| **Daily Reading** | `get_daily_horoscope` | Full horoscope with astrometers embedded |
| **Chat** | `ask_the_stars` | SSE streaming HTTP endpoint |
| **Connections** | `create_connection`, `list_connections`, `update_connection`, `delete_connection` | |
| **Compatibility** | `get_compatibility` | Synastry analysis |
| **Sharing** | `get_share_link`, `get_public_profile`, `import_connection` | |
| **Requests** | `list_connection_requests`, `respond_to_request`, `update_share_mode` | |

---

## Connection Vibes (Auto-Updated)

When `get_daily_horoscope` runs, if a connection is featured in the relationship weather:
1. A vibe is generated for that connection
2. The vibe is **automatically stored** on the connection document
3. FIFO limit of 10 vibes per connection

**iOS gets vibes via `list_connections`** - each connection includes:

```json
{
  "connection_id": "abc123",
  "name": "Sarah",
  "vibes": [
    {
      "date": "2025-11-29",
      "vibe": "Great energy for deep conversations today",
      "vibe_score": 85,
      "key_transit": "Transit Venus trine their Moon"
    }
  ]
}
```

No separate endpoint needed - vibes come with connection data.

---

## Brand Voice

**Audience:** Women navigating relationships, career, life transitions (Gen Z, Millennials, Gen Alpha)

**Tone:** Direct, actionable, honest. Like a wise friend, not a mystical guru.

**Rules:**
- 8th grade reading level
- Short sentences (15-20 words max)
- NO: "catalyze," "manifestation," "archetypal," "synthesize," "profound"
- NO astrology jargon without explanation
- Never mention AI, algorithms, or meters to users

---

## Quality Labels (4 Quadrants)

`unified_score` is **-100 to +100** (bipolar), NOT 0-100.

| Range | Quality | State Examples |
|-------|---------|----------------|
| >= +50 | `flowing` | Peak energy, everything clicks |
| +10 to +50 | `peaceful` | Calm, positive |
| -25 to +10 | `turbulent` | Mixed, stay flexible |
| < -25 | `challenging` | Friction, push through |

Use `state_label` for display (max 2 words). Don't show raw numbers to users.

---

## Meter Structure

17 meters in 5 groups (embedded in `get_daily_horoscope` response):

| Group | Meters |
|-------|--------|
| Mind | clarity, focus, communication |
| Heart | resilience, connections, vulnerability |
| Body | energy, drive, strength |
| Instincts | vision, flow, intuition, creativity |
| Growth | momentum, ambition, evolution, circle |

---

## Ask the Stars (SSE)

`POST /ask_the_stars` - HTTP endpoint, NOT Firebase Callable.

```
Headers:
  Authorization: Bearer <firebase_id_token>
  Content-Type: application/json

Body:
{
  "user_id": "...",
  "horoscope_date": "YYYY-MM-DD",
  "message": "..."
}
```

Returns Server-Sent Events stream.

---

## Firebase

- **Project:** `arca-baf77`
- **Region:** `us-central1`
- **Emulators:** Functions: 5001, Firestore: 8080, Auth: 9099

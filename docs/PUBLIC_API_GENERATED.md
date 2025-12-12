# Arca Backend API Reference

> Auto-generated on 2025-12-12 12:57:49
> 
> DO NOT EDIT MANUALLY. Run `uv run python functions/generate_api_docs.py` to regenerate.

## Table of Contents

- [Authentication](#authentication)
- [Callable Functions](#callable-functions)
- [Model Definitions](#model-definitions)
- [Enum Definitions](#enum-definitions)
- [Astrometer State Labels](#astrometer-state-labels)

---

## Authentication

All callable functions require Firebase Authentication. The backend verifies the auth token
and uses `req.auth.uid` as the user ID - clients do NOT need to pass `user_id`.

### How It Works

1. iOS client signs in via Firebase Auth
2. `httpsCallable()` automatically attaches the auth token
3. Backend extracts user ID from the verified token

### Dev Account Override

For testing connection sharing flows, dev accounts can pass `user_id` in the request
to impersonate other users. This is restricted to the following Firebase Auth UIDs:

| Dev Account | Firebase UID |
|-------------|--------------|
| Dev A | `test_user_a` |
| Dev B | `test_user_b` |
| Dev C | `test_user_c` |
| Dev D | `test_user_d` |
| Dev E | `test_user_e` |

**Usage (dev accounts only):**
```swift
// Normal user - no user_id needed
let result = try await callable.call(["date": "2025-01-15"])

// Dev account impersonating another user
let result = try await callable.call(["user_id": "target_user_uid", "date": "2025-01-15"])
```

---

## Callable Functions

### Charts

#### `natal_chart`

Generate a natal (birth) chart.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `utc_dt` | string | Yes | UTC datetime string |
| `lat` | float | Yes | Latitude |
| `lon` | float | Yes | Longitude |

**Response:** `Complete natal chart data as a dictionary`

---

#### `daily_transit`

TIER 1: Generate daily transit chart (universal, no location).

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `utc_dt` | string | No | Optional, defaults to today midnight UTC |

**Response:** `NatalChartData`

---

#### `user_transit`

TIER 2: Generate user-specific transit chart overlay.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `utc_dt` | string | No | Optional, defaults to now |
| `birth_lat` | float | Yes | User's birth latitude |
| `birth_lon` | float | Yes | User's birth longitude |

**Response:** `NatalChartData`

---

#### `get_natal_chart_for_connection`

Get natal chart for a connection.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connection_id` | string | Yes | - |

**Response:** `{ "chart": ..., "has_exact_chart": ..., "connection_name": ..., "sun_sign": ... }`

---

#### `get_synastry_chart`

*Memory: 512MB*

Get both natal charts and synastry aspects in a single call.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connection_id` | string | Yes | - |

**Response:** `NatalChartData`

---

### User Management

#### `create_user_profile`

*Requires: GEMINI_API_KEY, POSTHOG_API_KEY*

Create user profile with birth chart computation and LLM-generated summary.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | - |
| `email` | string | Yes | - |
| `birth_date` | string | Yes | YYYY-MM-DD (REQUIRED) |
| `birth_time` | string | No | HH:MM (optional) |
| `birth_timezone` | string | Yes | - |
| `birth_lat` | float | No | Latitude (optional) |
| `birth_lon` | float | No | Longitude (optional) |
| `birth_country` | string | No | Country name for display (optional) |
| `birth_city` | string | Yes | - |

**Response:** `{ "success": ..., "user_id": ..., "sun_sign": ..., "exact_chart": ..., "mode": ... }`

---

#### `get_user_profile`

Get user profile from Firestore.

**Response:** `Complete user profile dictionary or error if not found`

---

#### `update_user_profile`

*Requires: GEMINI_API_KEY, POSTHOG_API_KEY*

Update user profile with optional natal chart regeneration.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `photo_path` | str | No | Firebase Storage path for profile photo |
| `birth_time` | str | No | Birth time HH:MM - triggers chart regeneration |
| `birth_timezone` | str | No | IANA timezone for birth time |
| `birth_lat` | float | No | Birth latitude |
| `birth_lon` | float | No | Birth longitude |
| `birth_country` | str | No | Country name for display (e.g., 'USA') |
| `birth_city` | str | No | City with state/country for display (e.g., 'New York, NY, USA') |

**Response:** `UserProfile`

---

#### `get_memory`

Get memory collection for a user (for LLM personalization).

**Response:** `Memory collection dictionary`

---

#### `get_sun_sign_from_date`

Get sun sign from birth date.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `birth_date` | string | Yes | YYYY-MM-DD |

**Response:** `{ "sun_sign": ..., "element": ..., "modality": ..., "ruling_planet": ..., "keywords": ..., "summary": ... }`

---

#### `register_device_token`

Register device token for push notifications.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `device_token` | string | Yes | - |

**Response:** `{ "success": true }`

---

#### `delete_user`

Delete all user data for GDPR compliance.

**Response:** `{"success": true}`

---

### Horoscope

#### `get_daily_horoscope`

*Memory: 512MB | Requires: GEMINI_API_KEY, POSTHOG_API_KEY*

Generate daily horoscope - complete reading with meter groups.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | No | Optional, defaults to today |

**Response:** `DailyHoroscope`

---

#### `get_astrometers`

Calculate all 17 astrological meters for a user on a given date.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | No | Optional, defaults to today |

**Response:** `AstrometersForIOS`

---

### Conversations

#### `get_conversation_history`

Get full conversation with all messages.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conversation_id` | str | Yes | Conversation ID to fetch |

**Response:** `{ "conversation": Conversation }`

---

#### `get_user_entities`

Get user's entities with optional filtering.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | str | No | Filter by status: "active", "archived", "resolved" |
| `limit` | int | No | Max entities to return (default 50) |

**Response:** `{ "entities": Entity[], "total_count": int }`

---

#### `update_entity`

Update an entity (status, aliases, context).

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | str | Yes | Entity ID to update |
| `status` | str | No | New status: "active", "archived", "resolved" |
| `add_aliases` | str[] | No | Aliases to add |
| `add_context` | str | No | Context snippet to add |

**Response:** `{ "success": true, "entity": Entity }`

---

#### `delete_entity`

Delete an entity permanently.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_id` | str | Yes | Entity ID to delete |

**Response:** `{ "success": true }`

---

#### `ask_the_stars`

**Type:** HTTP Endpoint (SSE streaming)

*Memory: 512MB | Requires: GEMINI_API_KEY*

HTTPS endpoint: Ask the Stars with SSE streaming.

**Authentication:**
- Production: `Authorization: Bearer <firebase_id_token>`
- Dev mode: `Authorization: Bearer dev_arca_2025` (requires `user_id` in body)

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | The user's question (required) |
| `conversation_id` | string | No | Optional - continue existing conversation |
| `user_id` | string | No | Optional - required only with dev token |

**SSE Response Events:**

Content-Type: `text/event-stream`

**`type="chunk"`**
```json
{"type": "chunk", "text": "partial response text..."}
```

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | - |

**`type="done"`**
```json
{"type": "done", "conversation_id": "conv_abc123", "message_id": "msg_xyz789"}
```

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | string | - |
| `message_id` | string | - |

---

### Connections

#### `create_connection`

Manually create a connection (not via share link).

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connection` | object | Yes | - |

**Response:** `Created connection data`

---

#### `update_connection`

Update a connection's details.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connection_id` | string | Yes | - |
| `updates` | object | Yes | - |

**Response:** `Updated connection data`

---

#### `delete_connection`

Delete a connection.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connection_id` | string | Yes | - |

**Response:** `{ "success": true }`

---

#### `list_connections`

List all user's connections.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | int | No | Optional, default 50 |

**Response:** `{ "connections": ..., "total_count": ... }`

---

### Sharing

#### `get_share_link`

Get user's shareable profile link for "Add me on Arca".

**Response:** `{ "share_url": ..., "share_mode": ..., "qr_code_data": ... }`

---

#### `get_public_profile`

Fetch public profile data from a share link.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `share_secret` | string | Yes | - |

**Response:** `object`

---

#### `import_connection`

Add a connection from a share link.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `share_secret` | string | Yes | - |
| `relationship_category` | string | Yes | - |
| `relationship_label` | string | Yes | - |

**Response:** `{ "success": ..., "connection_id": ..., "connection": ..., "name": ..., "sun_sign": ..., "notification_sent": ... }`

---

#### `list_connection_requests`

List pending connection requests for a user.

**Response:** `{ "requests": ... }`

---

#### `update_share_mode`

Toggle between public and request-only share modes.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `share_mode` | string | Yes | "request" or "public" |

**Response:** `{ "share_mode": "request" }`

---

#### `respond_to_request`

Approve or reject a connection request.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string | Yes | - |
| `action` | string | Yes | "approve" or "reject" |

**Response:** `{ "success": ..., "action": ..., "connection_id": ... }`

---

### Compatibility

#### `get_compatibility`

*Memory: 512MB | Requires: GEMINI_API_KEY, POSTHOG_API_KEY*

Get compatibility analysis between user and a connection.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connection_id` | string | Yes | - |

**Response:** `CompatibilityResult`

---

---

## Model Definitions

### User & Profile

#### `UserProfile`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `user_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 128 | Firebase Auth user ID |
| `name` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | User's name from auth provider |
| `email` | string | Yes | PydanticUndefined | pattern: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ | User's email from auth provider |
| `is_premium` | boolean | No | False | - | True if user has premium subscription |
| `premium_expiry` | string | null | No | null | - | ISO date of premium subscription expiry (None if non-prem... |
| `is_trial_active` | boolean | No | False | - | Whether user is currently in trial |
| `trial_end_date` | string | null | No | null | - | ISO date when trial ends (YYYY-MM-DD) |
| `birth_date` | string | Yes | PydanticUndefined | pattern: ^\d{4}-\d{2}-\d{2}$ | Birth date in YYYY-MM-DD format |
| `birth_time` | string | null | No | null | pattern: ^\d{2}:\d{2}$ | Birth time in HH:MM format (optional, V2+) |
| `birth_timezone` | string | null | No | null | max_length: 64 | IANA timezone (optional, V2+) |
| `birth_lat` | float | null | No | null | >= -90, <= 90 | Birth latitude (optional) |
| `birth_lon` | float | null | No | null | >= -180, <= 180 | Birth longitude (optional) |
| `birth_country` | string | null | No | null | max_length: 100 | Birth country (e.g., 'USA') |
| `birth_city` | string | null | No | null | max_length: 200 | Birth city with state/country (e.g., 'New York, NY, USA') |
| `device_timezone` | string | null | No | null | max_length: 64 | User's device timezone (IANA format) |
| `device_language` | string | null | No | null | max_length: 10 | User's device language code (e.g., 'en') |
| `device_country` | string | null | No | null | max_length: 2 | User's device country code (e.g., 'US') |
| `device_currency` | string | null | No | null | max_length: 3 | User's device currency code (e.g., 'USD') |
| `sun_sign` | string | Yes | PydanticUndefined | - | Sun sign (e.g., 'taurus') |
| `natal_chart` | object | Yes | PydanticUndefined | - | Complete NatalChartData from get_astro_chart() |
| `exact_chart` | boolean | Yes | PydanticUndefined | - | True if birth_time + timezone provided |
| `photo_path` | string | null | No | null | max_length: 500 | Firebase Storage path for user photo |
| `created_at` | string | Yes | PydanticUndefined | - | ISO datetime of profile creation |
| `last_active` | string | Yes | PydanticUndefined | - | ISO datetime of last activity |

#### `MemoryCollection`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `user_id` | string | Yes | PydanticUndefined | - | Firebase Auth user ID |
| `categories` | object<string (enum: MeterGroupV2), CategoryEngagement> | Yes | PydanticUndefined | - | Engagement counts per meter group |
| `entity_summary` | object<string, int> | No | PydanticUndefined | - | Entity type counts (e.g., {'relationship': 5, 'career_goa... |
| `last_conversation_date` | string | null | No | null | - | ISO date of last conversation |
| `total_conversations` | int | No | 0 | >= 0 | Total number of Ask the Stars conversations |
| `question_categories` | object<string, int> | No | PydanticUndefined | - | Question category counts for analytics |
| `relationship_mentions` | RelationshipMention[] | No | PydanticUndefined | - | Last 20 relationship mentions in horoscopes for rotation ... |
| `connection_mentions` | ConnectionMention[] | No | PydanticUndefined | - | Last 20 connection mentions in horoscopes for rotation tr... |
| `updated_at` | string | Yes | PydanticUndefined | - | ISO datetime of last update |

#### `CategoryEngagement`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `count` | int | No | 0 | >= 0 | Total times viewed |
| `last_mentioned` | string | null | No | null | - | ISO date of last view |

#### `ConnectionMention`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `connection_id` | string | Yes | PydanticUndefined | - | Connection ID |
| `connection_name` | string | Yes | PydanticUndefined | - | Connection's name |
| `relationship_category` | string | Yes | PydanticUndefined | - | love/friend/family/coworker/other |
| `relationship_label` | string | Yes | PydanticUndefined | - | crush/partner/best_friend/boss/etc |
| `date` | string | Yes | PydanticUndefined | - | ISO date when featured |
| `context` | string | Yes | PydanticUndefined | - | What was said about this connection |

#### `RelationshipMention`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `entity_id` | string | Yes | PydanticUndefined | - | ID of the entity |
| `entity_name` | string | Yes | PydanticUndefined | - | Name of the entity |
| `category` | string (enum: EntityCategory) | Yes | PydanticUndefined | - | Category: partner, family, friend, coworker |
| `date` | string | Yes | PydanticUndefined | - | ISO date when featured |
| `context` | string | Yes | PydanticUndefined | - | What was said about this relationship |

### Horoscope

#### `DailyHoroscope`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `date` | string | Yes | PydanticUndefined | - | ISO date of horoscope |
| `sun_sign` | string | Yes | PydanticUndefined | - | Sun sign (e.g., 'taurus') |
| `technical_analysis` | string | Yes | PydanticUndefined | - | Astronomical explanation (3-5 sentences) |
| `daily_theme_headline` | string | Yes | PydanticUndefined | - | Shareable wisdom sentence (max 15 words, actionable) |
| `daily_overview` | string | Yes | PydanticUndefined | - | Opening overview combining emotional tone, key transits e... |
| `actionable_advice` | ActionableAdvice | Yes | PydanticUndefined | - | Structured DO/DON'T/REFLECT guidance |
| `astrometers` | AstrometersForIOS | Yes | PydanticUndefined | - | Complete astrometers: 17 meters nested in 5 groups with L... |
| `transit_summary` | object | null | No | null | - | Enhanced transit summary with priority transits, critical... |
| `moon_detail` | any | null | No | null | - | Comprehensive moon transit detail: aspects to natal, void... |
| `look_ahead_preview` | string | null | No | null | - | Upcoming significant transits (2-3 sentences) |
| `energy_rhythm` | string | null | No | null | - | Energy pattern throughout day based on intensity curve an... |
| `relationship_weather` | RelationshipWeather | null | No | null | - | Relationship weather with overview + connection-specific ... |
| `collective_energy` | string | null | No | null | - | What everyone is feeling from outer planet context (1-2 s... |
| `follow_up_questions` | string[] | null | No | null | - | 5 thought-provoking questions to help user reflect on the... |
| `model_used` | string | null | No | null | - | LLM model used |
| `generation_time_ms` | int | null | No | null | - | Generation time in milliseconds |
| `usage` | object | No | PydanticUndefined | - | Raw usage metadata from LLM API |
| `featured_meters` | string[] | null | No | null | - | Names of meters featured in headline |

#### `ActionableAdvice`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `do` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Specific action aligned with transit energy |
| `dont` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Specific thing to avoid (shadow/pitfall) |
| `reflect_on` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Powerful journaling question for self-awareness |

#### `RelationshipWeather`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `overview` | string | Yes | PydanticUndefined | min_length: 1, max_length: 1000 | 2-3 sentences covering general vibe for all relationship ... |
| `connection_vibes` | ConnectionVibe[] | No | PydanticUndefined | max_length: 20 | Personalized vibes for top 10 connections (empty if no co... |

#### `ConnectionVibe`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `connection_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 64 | Connection ID from user's connections |
| `name` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Connection's name |
| `relationship_category` | string (enum: RelationshipCategory) | Yes | PydanticUndefined | - | Main category (love/friend/family/coworker/other) |
| `relationship_label` | string (enum: RelationshipLabel) | Yes | PydanticUndefined | - | Specific label (crush/partner/best_friend/boss/etc) |
| `vibe` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Personalized vibe sentence with their name, e.g., 'Great ... |
| `vibe_score` | int | Yes | PydanticUndefined | >= 0, <= 100 | 0-100 score (70-100=positive, 40-70=neutral, 0-40=challen... |
| `key_transit` | string | null | No | null | max_length: 500 | Most significant transit, e.g., 'Transit Venus trine your... |

### Astrometers

#### `AstrometersForIOS`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `date` | string | Yes | PydanticUndefined | - | ISO date of reading |
| `overall_unified_score` | float | Yes | PydanticUndefined | >= 0, <= 100 | Overall unified score across all meters (0-100, 50=neutral) |
| `overall_intensity` | MeterReading | Yes | PydanticUndefined | - | Overall intensity meter with state_label |
| `overall_harmony` | MeterReading | Yes | PydanticUndefined | - | Overall harmony meter with state_label |
| `overall_quality` | string | Yes | PydanticUndefined | - | Overall quality from unified_score quadrant: challenging,... |
| `overall_state` | string | Yes | PydanticUndefined | - | Overall state label for the day (e.g., 'Quiet Reflection'... |
| `groups` | MeterGroupForIOS[] | Yes | PydanticUndefined | - | All 5 groups containing 17 total meters |
| `top_active_meters` | string[] | Yes | PydanticUndefined | - | Top 3-5 meter names by intensity (e.g., ['vitality', 'dri... |
| `top_challenging_meters` | string[] | Yes | PydanticUndefined | - | Top 3-5 meter names by low harmony (need attention) |
| `top_flowing_meters` | string[] | Yes | PydanticUndefined | - | Top 3-5 meter names by high unified_score (leverage these) |

#### `MeterGroupForIOS`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `group_name` | string | Yes | PydanticUndefined | - | Group ID: mind, heart, body, instincts, growth |
| `display_name` | string | Yes | PydanticUndefined | - | User-facing name: Mind, Heart, Body, Instincts, Growth |
| `unified_score` | float | Yes | PydanticUndefined | >= 0, <= 100 | Average unified score of member meters (0-100, 50=neutral) |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | Average intensity (internal use) |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | Average harmony (internal use) |
| `state_label` | string | Yes | PydanticUndefined | - | State label from unified_score: 'Sharp', 'Clear', 'Hazy',... |
| `quality` | string | Yes | PydanticUndefined | - | Quality: challenging (<25), turbulent (25-50), peaceful (... |
| `interpretation` | string | Yes | PydanticUndefined | - | Group-level interpretation from existing LLM flow |
| `meters` | MeterForIOS[] | Yes | PydanticUndefined | - | Individual meters in this group (3-4 meters) |
| `trend_delta` | float | null | No | null | - | Change in group unified_score from yesterday |
| `trend_direction` | string | null | No | null | - | improving, worsening, stable |
| `trend_change_rate` | string | null | No | null | - | rapid, moderate, slow, stable |
| `overview` | string | Yes | PydanticUndefined | - | What this group represents |
| `detailed` | string | Yes | PydanticUndefined | - | Which meters it combines + what it shows holistically |

#### `MeterForIOS`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `meter_name` | string | Yes | PydanticUndefined | - | Internal meter ID (e.g., 'clarity') |
| `display_name` | string | Yes | PydanticUndefined | - | User-facing name (e.g., 'Clarity') |
| `group` | string | Yes | PydanticUndefined | - | Group ID: mind, heart, body, instincts, growth |
| `unified_score` | float | Yes | PydanticUndefined | >= 0, <= 100 | Primary display value (0-100, 50=neutral) |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | Activity level (internal use) |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | Quality indicator (internal use) |
| `unified_quality` | string | Yes | PydanticUndefined | - | Quality: challenging (<25), turbulent (25-50), peaceful (... |
| `state_label` | string | Yes | PydanticUndefined | - | Rich contextual state: 'Sharp', 'Clear', 'Hazy', 'Overloa... |
| `interpretation` | string | Yes | PydanticUndefined | - | Personalized daily interpretation referencing today's tra... |
| `trend_delta` | float | null | No | null | - | Change in unified_score from yesterday |
| `trend_direction` | string | null | No | null | - | improving, worsening, stable, increasing, decreasing |
| `trend_change_rate` | string | null | No | null | - | rapid, moderate, slow, stable |
| `overview` | string | Yes | PydanticUndefined | - | What this meter represents (1 sentence, user-facing) |
| `detailed` | string | Yes | PydanticUndefined | - | How it's measured (2-3 sentences, explains calculation) |
| `astrological_foundation` | AstrologicalFoundation | Yes | PydanticUndefined | - | Planets, houses, and meanings |
| `top_aspects` | MeterAspect[] | Yes | PydanticUndefined | - | Top 3-5 transit aspects driving today's score (sorted by ... |

#### `MeterAspect`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `label` | string | Yes | PydanticUndefined | - | Human-readable: 'Transit Saturn square Natal Sun' |
| `natal_planet` | string | Yes | PydanticUndefined | - | Natal planet name (e.g., 'sun', 'mars') |
| `transit_planet` | string | Yes | PydanticUndefined | - | Transit planet name |
| `aspect_type` | string | Yes | PydanticUndefined | - | Aspect type: conjunction, opposition, trine, square, sext... |
| `orb` | float | Yes | PydanticUndefined | - | Exact orb in degrees (e.g., 2.5°) |
| `orb_percentage` | float | Yes | PydanticUndefined | >= 0, <= 100 | % of max orb - tighter = stronger (e.g., 31.25% if 2.5° o... |
| `phase` | string | Yes | PydanticUndefined | - | applying, exact, or separating |
| `days_to_exact` | float | null | No | null | - | Days until exact (negative = past exact) |
| `contribution` | float | Yes | PydanticUndefined | - | DTI contribution (W_i × P_i) |
| `quality_factor` | float | Yes | PydanticUndefined | >= -1, <= 1 | -1 (very challenging) to +1 (very harmonious) |
| `natal_planet_house` | int | Yes | PydanticUndefined | >= 1, <= 12 | House containing natal planet |
| `natal_planet_sign` | string | Yes | PydanticUndefined | - | Sign of natal planet (for dignity assessment) |
| `houses_involved` | int[] | Yes | PydanticUndefined | - | Houses involved in this transit |
| `natal_aspect_echo` | string | null | No | null | - | If echoes natal aspect: 'Echoes natal Mars-Saturn square' |

#### `AstrologicalFoundation`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `natal_planets_tracked` | string[] | Yes | PydanticUndefined | - | Natal planets monitored (e.g., ['sun', 'mars']) |
| `transit_planets_tracked` | string[] | Yes | PydanticUndefined | - | Transit planets that affect this (e.g., ['sun', 'mars', '... |
| `key_houses` | object<string, string> | Yes | PydanticUndefined | - | House numbers and their meanings for this meter (e.g., {'... |
| `primary_planets` | object<string, string> | Yes | PydanticUndefined | - | Primary planetary influences with explanations (e.g., {'s... |
| `secondary_planets` | object<string, string> | null | No | null | - | Secondary influences (e.g., {'saturn': 'Can temporarily d... |

#### `MeterReading`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `meter_name` | string | Yes | PydanticUndefined | - | - |
| `date` | datetime | Yes | PydanticUndefined | - | - |
| `group` | string (enum: MeterGroupV2) | Yes | PydanticUndefined | - | - |
| `unified_score` | float | Yes | PydanticUndefined | >= 0, <= 100 | - |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | - |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | - |
| `unified_quality` | "challenging" | "turbulent" | "peaceful" | "flowing" | Yes | PydanticUndefined | - | - |
| `state_label` | string | Yes | PydanticUndefined | - | - |
| `interpretation` | string | Yes | PydanticUndefined | - | - |
| `advice` | string[] | Yes | PydanticUndefined | - | - |
| `top_aspects` | AspectContribution[] | Yes | PydanticUndefined | - | - |
| `raw_scores` | object<string, float> | Yes | PydanticUndefined | - | - |
| `trend` | MeterTrends | null | No | null | - | - |

### Charts

#### `NatalChartData`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `chart_type` | "natal" | "transit" | Yes | PydanticUndefined | - | - |
| `datetime_utc` | string | Yes | PydanticUndefined | - | UTC datetime in format 'YYYY-MM-DD HH:MM' |
| `location_lat` | float | Yes | PydanticUndefined | >= -90, <= 90 | - |
| `location_lon` | float | Yes | PydanticUndefined | >= -180, <= 180 | - |
| `angles` | ChartAngles | Yes | PydanticUndefined | - | - |
| `planets` | PlanetPosition[] | Yes | PydanticUndefined | - | - |
| `houses` | HouseCusp[] | Yes | PydanticUndefined | min_length: 12, max_length: 12 | - |
| `aspects` | AspectData[] | Yes | PydanticUndefined | - | - |
| `distributions` | ChartDistributions | Yes | PydanticUndefined | - | - |
| `summary` | string | null | No | null | - | LLM-generated chart interpretation (3-4 sentences) |

#### `ChartAngles`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `ascendant` | AnglePosition | Yes | PydanticUndefined | - | - |
| `imum_coeli` | AnglePosition | Yes | PydanticUndefined | - | - |
| `descendant` | AnglePosition | Yes | PydanticUndefined | - | - |
| `midheaven` | AnglePosition | Yes | PydanticUndefined | - | - |

#### `AnglePosition`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `sign` | string (enum: ZodiacSign) | Yes | PydanticUndefined | - | - |
| `degree_in_sign` | float | Yes | PydanticUndefined | >= 0, < 30 | - |
| `absolute_degree` | float | Yes | PydanticUndefined | >= 0, < 360 | - |
| `position_dms` | string | Yes | PydanticUndefined | - | Formatted position like '15° ♈ 23' |

#### `PlanetPosition`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `name` | string (enum: Planet) | Yes | PydanticUndefined | - | - |
| `symbol` | string | Yes | PydanticUndefined | - | - |
| `position_dms` | string | Yes | PydanticUndefined | - | Formatted position like '15° ♈ 23' |
| `sign` | string (enum: ZodiacSign) | Yes | PydanticUndefined | - | - |
| `degree_in_sign` | float | Yes | PydanticUndefined | >= 0, < 30 | - |
| `absolute_degree` | float | Yes | PydanticUndefined | >= 0, < 360 | - |
| `house` | int | Yes | PydanticUndefined | >= 1, <= 12 | - |
| `speed` | float | Yes | PydanticUndefined | - | - |
| `retrograde` | boolean | Yes | PydanticUndefined | - | - |
| `element` | "fire" | "earth" | "air" | "water" | Yes | PydanticUndefined | - | - |
| `modality` | "cardinal" | "fixed" | "mutable" | Yes | PydanticUndefined | - | - |

#### `HouseCusp`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `number` | int | Yes | PydanticUndefined | >= 1, <= 12 | - |
| `sign` | string (enum: ZodiacSign) | Yes | PydanticUndefined | - | - |
| `degree_in_sign` | float | Yes | PydanticUndefined | >= 0, < 30 | - |
| `absolute_degree` | float | Yes | PydanticUndefined | >= 0, < 360 | - |
| `ruler` | string (enum: Planet) | Yes | PydanticUndefined | - | - |
| `ruler_sign` | string (enum: ZodiacSign) | Yes | PydanticUndefined | - | - |
| `ruler_house` | int | Yes | PydanticUndefined | >= 1, <= 12 | - |
| `classic_ruler` | string (enum: Planet) | Yes | PydanticUndefined | - | - |
| `classic_ruler_sign` | string (enum: ZodiacSign) | Yes | PydanticUndefined | - | - |
| `classic_ruler_house` | int | Yes | PydanticUndefined | >= 1, <= 12 | - |

#### `AspectData`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `body1` | string (enum: CelestialBody) | Yes | PydanticUndefined | - | - |
| `body2` | string (enum: CelestialBody) | Yes | PydanticUndefined | - | - |
| `aspect_type` | string (enum: AspectType) | Yes | PydanticUndefined | - | - |
| `aspect_symbol` | string | Yes | PydanticUndefined | - | - |
| `exact_degree` | int | Yes | PydanticUndefined | - | Exact degree of aspect (0, 60, 90, 120, 180) |
| `orb` | float | Yes | PydanticUndefined | >= 0 | Orb in degrees from exact |
| `applying` | boolean | Yes | PydanticUndefined | - | True if applying, False if separating |

#### `ChartDistributions`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `elements` | ElementDistribution | Yes | PydanticUndefined | - | - |
| `modalities` | ModalityDistribution | Yes | PydanticUndefined | - | - |
| `quadrants` | QuadrantDistribution | Yes | PydanticUndefined | - | - |
| `hemispheres` | HemisphereDistribution | Yes | PydanticUndefined | - | - |

#### `ElementDistribution`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `fire` | int | Yes | PydanticUndefined | >= 0, <= 11 | - |
| `earth` | int | Yes | PydanticUndefined | >= 0, <= 11 | - |
| `air` | int | Yes | PydanticUndefined | >= 0, <= 11 | - |
| `water` | int | Yes | PydanticUndefined | >= 0, <= 11 | - |

#### `ModalityDistribution`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `cardinal` | int | Yes | PydanticUndefined | >= 0, <= 11 | - |
| `fixed` | int | Yes | PydanticUndefined | >= 0, <= 11 | - |
| `mutable` | int | Yes | PydanticUndefined | >= 0, <= 11 | - |

#### `QuadrantDistribution`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `first` | int | Yes | PydanticUndefined | >= 0, <= 11 | Houses 1-3 (Self) |
| `second` | int | Yes | PydanticUndefined | >= 0, <= 11 | Houses 4-6 (Foundation) |
| `third` | int | Yes | PydanticUndefined | >= 0, <= 11 | Houses 7-9 (Relationships) |
| `fourth` | int | Yes | PydanticUndefined | >= 0, <= 11 | Houses 10-12 (Social/Career) |

#### `HemisphereDistribution`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `northern` | int | Yes | PydanticUndefined | >= 0, <= 11 | Houses 1-6 |
| `southern` | int | Yes | PydanticUndefined | >= 0, <= 11 | Houses 7-12 |
| `eastern` | int | Yes | PydanticUndefined | >= 0, <= 11 | Houses 10-3 |
| `western` | int | Yes | PydanticUndefined | >= 0, <= 11 | Houses 4-9 |

### Connections

#### `Connection`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `connection_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 64, pattern: ^[a-zA-Z0-9_-]+$ | Unique connection ID |
| `name` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Connection's name |
| `birth_date` | string | Yes | PydanticUndefined | pattern: ^\d{4}-\d{2}-\d{2}$ | Birth date YYYY-MM-DD |
| `birth_time` | string | null | No | null | pattern: ^\d{2}:\d{2}$ | Birth time HH:MM |
| `birth_lat` | float | null | No | null | >= -90, <= 90 | - |
| `birth_lon` | float | null | No | null | >= -180, <= 180 | - |
| `birth_timezone` | string | null | No | null | max_length: 64 | IANA timezone |
| `relationship_category` | string (enum: RelationshipCategory) | Yes | PydanticUndefined | - | Main category (love/friend/family/coworker/other) |
| `relationship_label` | string (enum: RelationshipLabel) | Yes | PydanticUndefined | - | Specific label (crush/partner/best_friend/boss/etc) |
| `source_user_id` | string | null | No | null | max_length: 128 | User ID if imported via share link |
| `sun_sign` | string | null | No | null | - | Calculated sun sign |
| `photo_path` | string | null | No | null | max_length: 500 | Firebase Storage path for connection photo |
| `created_at` | string | Yes | PydanticUndefined | - | ISO timestamp |
| `updated_at` | string | Yes | PydanticUndefined | - | ISO timestamp |
| `synastry_points` | object[] | null | No | null | - | Cached synastry midpoints for daily transit checking |
| `arca_notes` | object[] | No | PydanticUndefined | max_length: 100 | Notes extracted from conversations: [{date, note, context}] |
| `vibes` | StoredVibe[] | No | PydanticUndefined | max_length: 10 | Last 10 daily vibes for this connection |

#### `StoredVibe`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `date` | string | Yes | PydanticUndefined | - | ISO date YYYY-MM-DD |
| `vibe` | string | Yes | PydanticUndefined | max_length: 500 | Vibe text, e.g., 'Great energy today' |
| `vibe_score` | int | Yes | PydanticUndefined | >= 0, <= 100 | 0-100 score |
| `key_transit` | string | null | No | null | max_length: 500 | Transit that triggered this vibe |

#### `ShareLink`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `user_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 128, pattern: ^[a-zA-Z0-9_-]+$ | Owner's user ID |
| `created_at` | string | Yes | PydanticUndefined | - | ISO timestamp |

#### `ConnectionRequest`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `request_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 64 | Unique request ID |
| `from_user_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 128 | Requester's user ID |
| `from_name` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Requester's name |
| `status` | "pending" | "approved" | "rejected" | No | 'pending' | - | - |
| `created_at` | string | Yes | PydanticUndefined | - | ISO timestamp |

#### `ShareLinkResponse`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `share_url` | string | Yes | PydanticUndefined | - | - |
| `share_mode` | "public" | "request" | Yes | PydanticUndefined | - | - |
| `qr_code_data` | string | Yes | PydanticUndefined | - | - |

#### `PublicProfileResponse`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `profile` | object | Yes | PydanticUndefined | - | Public profile data |
| `share_mode` | "public" | "request" | Yes | PydanticUndefined | - | - |
| `can_add` | boolean | Yes | PydanticUndefined | - | - |
| `message` | string | null | No | null | - | - |

#### `ImportConnectionResponse`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `success` | boolean | Yes | PydanticUndefined | - | - |
| `connection_id` | string | null | No | null | - | - |
| `connection` | object | null | No | null | - | - |
| `notification_sent` | boolean | No | False | - | - |
| `message` | string | null | No | null | - | - |

#### `ConnectionListResponse`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `connections` | object[] | Yes | PydanticUndefined | - | - |
| `total_count` | int | Yes | PydanticUndefined | - | - |

### Compatibility

#### `CompatibilityResult`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `headline` | string | Yes | PydanticUndefined | - | 5-8 word viral-worthy summary (e.g., 'Deep Waters, Shared... |
| `summary` | string | Yes | PydanticUndefined | - | 2-3 sentence elevator pitch of the relationship |
| `strengths` | string | Yes | PydanticUndefined | - | 2-3 sentences about natural flows (trines/sextiles) |
| `growth_areas` | string | Yes | PydanticUndefined | - | 1-2 sentences about challenges/opportunities (squares/opp... |
| `advice` | string | Yes | PydanticUndefined | - | One concrete, actionable step they can take today |
| `mode` | ModeCompatibility | Yes | PydanticUndefined | - | Scores and insights for the relationship type (romantic/f... |
| `aspects` | SynastryAspect[] | Yes | PydanticUndefined | - | All synastry aspects for chart rendering |
| `composite` | Composite | Yes | PydanticUndefined | - | Composite chart data - the 'Us' chart |
| `karmic` | Karmic | Yes | PydanticUndefined | - | Karmic/destiny analysis based on Node aspects |
| `calculated_at` | string | Yes | PydanticUndefined | - | ISO timestamp of calculation |
| `generation_time_ms` | int | No | 0 | - | LLM generation time in milliseconds |
| `model_used` | string | No | '' | - | LLM model used for generation |

#### `ModeCompatibility`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `type` | "romantic" | "friendship" | "coworker" | Yes | PydanticUndefined | - | The relationship type: romantic, friendship, or coworker |
| `overall_score` | int | Yes | PydanticUndefined | >= 0, <= 100 | Overall compatibility score (0-100) |
| `overall_label` | string | No | '' | - | Overall band label (e.g., 'Solid', 'Seamless', 'Volatile') |
| `vibe_phrase` | string | null | No | null | - | Short energy label. Romantic: 'Slow Burn', 'Electric'. Fr... |
| `categories` | CompatibilityCategory[] | Yes | PydanticUndefined | - | Category breakdowns with scores and insights |

#### `CompatibilityCategory`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `id` | string | Yes | PydanticUndefined | - | Category ID for iOS state management |
| `name` | string | Yes | PydanticUndefined | - | Display name (e.g., 'Emotional Connection') |
| `score` | int | Yes | PydanticUndefined | >= 0, <= 100 | Category score: 0 (challenging) to 100 (flowing), 50 is n... |
| `insight` | string | null | No | null | - | LLM-generated 1-2 sentence insight for this category |
| `aspect_ids` | string[] | No | PydanticUndefined | - | Top 3-5 aspect IDs driving this score, ordered by tightes... |
| `label` | string | No | '' | - | Band label from JSON config (e.g., 'Warm', 'Soul-Level', ... |
| `description` | string | No | '' | - | What this category measures (for iOS display) |
| `driving_aspects` | DrivingAspect[] | No | PydanticUndefined | - | Top aspects with human-readable meanings explaining WHY t... |

#### `DrivingAspect`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `aspect_id` | string | Yes | PydanticUndefined | - | Reference to full aspect in aspects list (e.g., 'asp_001') |
| `user_planet` | string | Yes | PydanticUndefined | - | Your planet (e.g., 'Moon') |
| `their_planet` | string | Yes | PydanticUndefined | - | Their planet (e.g., 'Venus') |
| `aspect_type` | string | Yes | PydanticUndefined | - | trine, square, conjunction, etc. |
| `is_harmonious` | boolean | Yes | PydanticUndefined | - | True if supportive, False if challenging |
| `summary` | string | Yes | PydanticUndefined | - | Human-readable summary (e.g., 'Your emotional needs flow ... |

#### `SynastryAspect`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 32 | Unique aspect ID (e.g., 'asp_001') |
| `user_planet` | string | Yes | PydanticUndefined | min_length: 1, max_length: 32 | Planet from user's chart (e.g., 'venus') |
| `their_planet` | string | Yes | PydanticUndefined | min_length: 1, max_length: 32 | Planet from connection's chart (e.g., 'mars') |
| `aspect_type` | string | Yes | PydanticUndefined | min_length: 1, max_length: 32 | Aspect type: conjunction, trine, square, sextile, opposit... |
| `orb` | float | Yes | PydanticUndefined | >= 0, <= 20 | Orb in degrees (tighter = stronger) |
| `is_harmonious` | boolean | Yes | PydanticUndefined | - | True if supportive (trine/sextile), False if challenging ... |

### Entities

#### `Entity`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `entity_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 64, pattern: ^[a-zA-Z0-9_-]+$ | UUID for this entity |
| `name` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Entity name (e.g., 'John', 'Job Search', 'Meditation Prac... |
| `entity_type` | string | Yes | PydanticUndefined | min_length: 1, max_length: 64 | Open string: 'relationship', 'career_goal', 'challenge', ... |
| `status` | "active" | "archived" | "resolved" | No | <EntityStatus.ACT... | - | Entity status |
| `aliases` | string[] | No | PydanticUndefined | max_length: 100 | Alternative names for deduplication |
| `category` | string (enum: EntityCategory) | null | No | null | - | Entity category: partner, family, friend, coworker, other |
| `relationship_label` | string | null | No | null | max_length: 64 | Specific relationship label from iOS dropdown: mother, si... |
| `notes` | string | null | No | null | max_length: 10000 | User-written notes about this entity |
| `attributes` | AttributeKV[] | No | PydanticUndefined | max_length: 100 | Entity attributes: birthday_season, works_at, role, relat... |
| `related_entities` | string[] | No | PydanticUndefined | max_length: 100 | Entity IDs this entity is related to (e.g., 'Bob' -> ['en... |
| `first_seen` | string | Yes | PydanticUndefined | - | ISO timestamp of first mention |
| `last_seen` | string | Yes | PydanticUndefined | - | ISO timestamp of last mention |
| `mention_count` | int | No | 1 | >= 1 | Number of times mentioned |
| `context_snippets` | string[] | No | PydanticUndefined | max_length: 10 | Last 10 context snippets where entity was mentioned |
| `importance_score` | float | No | 0.0 | >= 0.0, <= 1.0 | Calculated: recency (0.6) + frequency (0.4) |
| `connection_id` | string | null | No | null | max_length: 64 | Links to Connection with birth data for compatibility |
| `created_at` | string | Yes | PydanticUndefined | - | ISO timestamp of creation |
| `updated_at` | string | Yes | PydanticUndefined | - | ISO timestamp of last update |

#### `UserEntities`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `user_id` | string | Yes | PydanticUndefined | - | Firebase Auth user ID |
| `entities` | Entity[] | No | PydanticUndefined | - | All entities in single array |
| `updated_at` | string | Yes | PydanticUndefined | - | ISO timestamp of last update |

#### `ExtractedEntity`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `name` | string | Yes | PydanticUndefined | - | Entity name |
| `entity_type` | string | Yes | PydanticUndefined | - | Entity type (open string) |
| `context` | string | Yes | PydanticUndefined | - | Context snippet from message |
| `confidence` | float | Yes | PydanticUndefined | >= 0.0, <= 1.0 | Extraction confidence |
| `attributes` | AttributeKV[] | No | PydanticUndefined | - | Extracted attributes (e.g., birthday_season, role, works_at) |
| `related_to` | string | null | No | null | - | Name of related entity mentioned in same context (e.g., '... |

#### `ExtractedEntities`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `entities` | ExtractedEntity[] | No | PydanticUndefined | - | Extracted entities |

#### `EntityMergeAction`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `action` | "create" | "update" | "merge" | "link" | Yes | PydanticUndefined | - | Action type: 'create', 'update', 'merge', 'link' |
| `entity_name` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Entity name |
| `entity_type` | string | Yes | PydanticUndefined | min_length: 1, max_length: 64 | Entity type |
| `merge_with_id` | string | null | No | null | max_length: 64 | Entity ID to merge with (if action='merge') |
| `new_alias` | string | null | No | null | max_length: 500 | Alias to add (if action='merge') |
| `context_update` | string | null | No | null | max_length: 10000 | Context snippet to add |
| `attribute_updates` | AttributeKV[] | No | PydanticUndefined | - | Attributes to add/update (e.g., [{'key': 'birthday_season... |
| `link_to_entity_id` | string | null | No | null | max_length: 200 | Entity ID to link/relate to (if action='link' or creating... |

#### `MergedEntities`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `actions` | EntityMergeAction[] | No | PydanticUndefined | - | List of merge actions to execute |

#### `AttributeKV`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `key` | string | Yes | PydanticUndefined | - | Attribute key |
| `value` | string | Yes | PydanticUndefined | - | Attribute value |

### Conversations

#### `Conversation`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `conversation_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 64 | UUID for this conversation |
| `user_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 128 | Firebase Auth user ID |
| `horoscope_date` | string | Yes | PydanticUndefined | pattern: ^\d{4}-\d{2}-\d{2}$ | ISO date (e.g., '2025-01-20') |
| `messages` | Message[] | No | PydanticUndefined | max_length: 1000 | All messages in conversation |
| `created_at` | string | Yes | PydanticUndefined | - | ISO timestamp of creation |
| `updated_at` | string | Yes | PydanticUndefined | - | ISO timestamp of last update |

#### `Message`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `message_id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 64 | UUID for this message |
| `role` | "user" | "assistant" | Yes | PydanticUndefined | - | Message role |
| `content` | string | Yes | PydanticUndefined | min_length: 1, max_length: 50000 | Message text content |
| `timestamp` | string | Yes | PydanticUndefined | - | ISO timestamp |

### Compressed Storage

#### `CompressedHoroscope`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `date` | string | Yes | PydanticUndefined | - | ISO date |
| `sun_sign` | string | Yes | PydanticUndefined | - | Sun sign |
| `technical_analysis` | string | Yes | PydanticUndefined | - | - |
| `daily_theme_headline` | string | Yes | PydanticUndefined | - | - |
| `daily_overview` | string | Yes | PydanticUndefined | - | - |
| `actionable_advice` | ActionableAdvice | Yes | PydanticUndefined | - | - |
| `look_ahead_preview` | string | null | No | null | - | - |
| `energy_rhythm` | string | null | No | null | - | - |
| `relationship_weather` | RelationshipWeather | null | No | null | - | - |
| `collective_energy` | string | null | No | null | - | - |
| `follow_up_questions` | string[] | null | No | null | - | - |
| `meter_groups` | CompressedMeterGroup[] | Yes | PydanticUndefined | - | 5 groups with scores and member meters |
| `astrometers` | CompressedAstrometers | Yes | PydanticUndefined | - | Summary of astrometers: overall state and top meters |
| `transit_summary` | CompressedTransitSummary | Yes | PydanticUndefined | - | Top priority transits with interpretations |
| `created_at` | string | Yes | PydanticUndefined | - | ISO datetime of generation |
| `featured_meters` | string[] | null | No | null | - | Names of meters featured in headline |

#### `CompressedMeterGroup`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `name` | string | Yes | PydanticUndefined | - | Group name: mind, heart, body, instincts, growth |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | Group intensity 0-100 |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | Group harmony 0-100 |
| `meters` | CompressedMeter[] | Yes | PydanticUndefined | - | Member meters with scores only |

#### `CompressedMeter`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `name` | string | Yes | PydanticUndefined | - | Meter name |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | Intensity score 0-100 |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | Harmony score 0-100 |

#### `CompressedAstrometers`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `overall_state` | string | Yes | PydanticUndefined | - | Overall state label (e.g., 'Quiet Reflection') |
| `top_active_meters` | string[] | Yes | PydanticUndefined | - | Top 3-5 most active meters |
| `top_flowing_meters` | string[] | Yes | PydanticUndefined | - | Top 3-5 meters with high harmony |
| `top_challenging_meters` | string[] | Yes | PydanticUndefined | - | Top 3-5 meters needing attention |

#### `CompressedTransitSummary`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `priority_transits` | CompressedTransit[] | No | PydanticUndefined | - | Top priority transits with interpretations |

#### `CompressedTransit`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `interpretation` | string | Yes | PydanticUndefined | - | Human-readable transit interpretation |

#### `UserHoroscopes`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `user_id` | string | Yes | PydanticUndefined | - | Firebase Auth user ID |
| `horoscopes` | object<string, object> | Yes | PydanticUndefined | - | Date-keyed horoscopes (max 10, FIFO) |
| `updated_at` | string | Yes | PydanticUndefined | - | ISO datetime of last update |

### Sun Sign Profiles

#### `SunSignProfile`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `sign` | string | Yes | PydanticUndefined | - | Name of the zodiac sign |
| `dates` | string | Yes | PydanticUndefined | - | Date range when the Sun transits this sign |
| `symbol` | string | Yes | PydanticUndefined | - | Traditional symbol representing the sign |
| `glyph` | string | Yes | PydanticUndefined | - | Unicode astrological glyph for the sign |
| `element` | "fire" | "earth" | "air" | "water" | Yes | PydanticUndefined | - | Elemental classification of the sign |
| `modality` | "cardinal" | "fixed" | "mutable" | Yes | PydanticUndefined | - | The sign's mode of expression and action style |
| `polarity` | string | Yes | PydanticUndefined | - | Energetic polarity - extroverted or introverted orientation |
| `ruling_planet` | string | Yes | PydanticUndefined | - | The planet that governs this sign |
| `ruling_planet_glyph` | string | Yes | PydanticUndefined | - | Unicode glyph for the ruling planet |
| `planetary_dignities` | PlanetaryDignities | Yes | PydanticUndefined | - | - |
| `body_parts_ruled` | string[] | Yes | PydanticUndefined | - | Physical body areas associated with and governed by this ... |
| `correspondences` | Correspondences | Yes | PydanticUndefined | - | - |
| `keywords` | string[] | Yes | PydanticUndefined | - | Core descriptive keywords capturing the sign's essence |
| `positive_traits` | string[] | Yes | PydanticUndefined | - | Constructive qualities and strengths naturally expressed ... |
| `shadow_traits` | string[] | Yes | PydanticUndefined | - | Challenging patterns and underdeveloped expressions of th... |
| `life_lesson` | string | Yes | PydanticUndefined | - | Primary evolutionary lesson this sign is here to learn |
| `evolutionary_goal` | string | Yes | PydanticUndefined | - | Highest expression and developmental aim for this sign |
| `mythology` | string | Yes | PydanticUndefined | - | Mythological stories and archetypes connected to this sign |
| `seasonal_association` | string | Yes | PydanticUndefined | - | Connection to natural cycles and seasonal energies in the... |
| `archetypal_roles` | string[] | Yes | PydanticUndefined | - | Universal archetypal patterns embodied by this sign |
| `health_tendencies` | HealthTendencies | Yes | PydanticUndefined | - | - |
| `compatibility_overview` | CompatibilityOverview | Yes | PydanticUndefined | - | - |
| `summary` | string | Yes | PydanticUndefined | - | Concise overview capturing the essence of the sign |
| `domain_profiles` | DomainProfiles | Yes | PydanticUndefined | - | - |

#### `PlanetaryDignities`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `exaltation` | string | Yes | PydanticUndefined | - | Planet that expresses most powerfully in this sign |
| `detriment` | string | Yes | PydanticUndefined | - | Planet that faces challenges in this sign |
| `fall` | string | Yes | PydanticUndefined | - | Planet at its weakest expression in this sign |

#### `Correspondences`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `tarot` | string | Yes | PydanticUndefined | - | Major Arcana tarot card correspondence |
| `colors` | string[] | Yes | PydanticUndefined | - | Colors that resonate with this sign's energy |
| `gemstones` | string[] | Yes | PydanticUndefined | - | Crystals and stones aligned with the sign |
| `metal` | string | Yes | PydanticUndefined | - | Metal associated with the sign's energy |
| `day_of_week` | string | Yes | PydanticUndefined | - | Day of the week ruled by this sign's planet |
| `lucky_numbers` | int[] | Yes | PydanticUndefined | - | Numbers that carry favorable energy for this sign |

#### `HealthTendencies`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `strengths` | string | Yes | PydanticUndefined | - | Natural health advantages for this sign |
| `vulnerabilities` | string | Yes | PydanticUndefined | - | Physical areas requiring attention and care |
| `wellness_advice` | string | Yes | PydanticUndefined | - | Guidance for maintaining optimal health (informational on... |

#### `CompatibilityEntry`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `sign` | string | Yes | PydanticUndefined | - | - |
| `reason` | string | Yes | PydanticUndefined | - | - |

### Other Models

#### `Composite`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `sun_sign` | string | Yes | PydanticUndefined | - | Composite Sun sign - the relationship's core purpose (e.g... |
| `moon_sign` | string | Yes | PydanticUndefined | - | Composite Moon sign - the relationship's emotional center... |
| `rising_sign` | string | null | No | null | - | Composite Rising sign - how others perceive the relations... |
| `dominant_element` | string | Yes | PydanticUndefined | - | Dominant element (fire/earth/air/water). Use as fallback ... |
| `purpose` | string | null | No | null | - | LLM-generated 1-2 sentences on why this relationship exists |

#### `Karmic`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `is_karmic` | boolean | Yes | PydanticUndefined | - | True if tight Node aspects exist (orb < 3 deg for Sun/Moo... |
| `theme` | string | null | No | null | - | Primary karmic theme if applicable (e.g., 'Past-life conn... |
| `destiny_note` | string | null | No | null | - | LLM-generated 1-2 sentences about the fated nature of thi... |

#### `MeterGroupData`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `group_name` | string | Yes | PydanticUndefined | - | Group ID: mind, heart, body, instincts, growth |
| `display_name` | string | Yes | PydanticUndefined | - | Display name: Mind, Heart, Body, Instincts, Growth |
| `scores` | MeterGroupScores | Yes | PydanticUndefined | - | - |
| `state` | MeterGroupState | Yes | PydanticUndefined | - | - |
| `interpretation` | string | Yes | PydanticUndefined | - | LLM-generated 2-3 sentence interpretation (150-300 chars) |
| `trend` | MeterGroupTrend | null | No | null | - | Trend data if yesterday available |
| `meter_ids` | string[] | Yes | PydanticUndefined | - | IDs of meters in this group |

#### `MeterGroupScores`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `unified_score` | float | Yes | PydanticUndefined | >= 0, <= 100 | Primary display value (0-100, 50=neutral), average of mem... |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | Supportive vs challenging quality (0-100) |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | Activity level (0-100) |

#### `MeterGroupState`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `label` | string | Yes | PydanticUndefined | min_length: 1, max_length: 50 | Human-readable state: Excellent, Supportive, Challenging,... |
| `quality` | "challenging" | "turbulent" | "peaceful" | "flowing" | Yes | PydanticUndefined | - | Quality type based on unified_score: challenging, turbule... |

#### `MeterGroupTrend`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `unified_score` | TrendMetric | Yes | PydanticUndefined | - | - |
| `harmony` | TrendMetric | Yes | PydanticUndefined | - | - |
| `intensity` | TrendMetric | Yes | PydanticUndefined | - | - |

#### `TrendMetric`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `previous` | float | Yes | PydanticUndefined | - | Yesterday's value |
| `delta` | float | Yes | PydanticUndefined | - | Change amount (can be negative) |
| `direction` | string (enum: DirectionType) | Yes | PydanticUndefined | - | Trend direction: improving, worsening, stable, increasing... |
| `change_rate` | "rapid" | "moderate" | "slow" | Yes | PydanticUndefined | - | Change rate: rapid, moderate, or slow |

---

## Enum Definitions

#### `ActionType`

| Name | Value |
|------|-------|
| `CREATE` | `"create"` |
| `UPDATE` | `"update"` |
| `MERGE` | `"merge"` |
| `LINK` | `"link"` |

#### `AspectType`

| Name | Value |
|------|-------|
| `CONJUNCTION` | `"conjunction"` |
| `OPPOSITION` | `"opposition"` |
| `TRINE` | `"trine"` |
| `SQUARE` | `"square"` |
| `SEXTILE` | `"sextile"` |
| `QUINCUNX` | `"quincunx"` |

#### `CelestialBody`

| Name | Value |
|------|-------|
| `SUN` | `"sun"` |
| `MOON` | `"moon"` |
| `MERCURY` | `"mercury"` |
| `VENUS` | `"venus"` |
| `MARS` | `"mars"` |
| `JUPITER` | `"jupiter"` |
| `SATURN` | `"saturn"` |
| `URANUS` | `"uranus"` |
| `NEPTUNE` | `"neptune"` |
| `PLUTO` | `"pluto"` |
| `NORTH_NODE` | `"north node"` |
| `SOUTH_NODE` | `"south node"` |
| `ASCENDANT` | `"asc"` |
| `IMUM_COELI` | `"ic"` |
| `DESCENDANT` | `"dsc"` |
| `MIDHEAVEN` | `"mc"` |

#### `ChangeRateType`

| Name | Value |
|------|-------|
| `RAPID` | `"rapid"` |
| `MODERATE` | `"moderate"` |
| `SLOW` | `"slow"` |

#### `ChartType`

| Name | Value |
|------|-------|
| `NATAL` | `"natal"` |
| `TRANSIT` | `"transit"` |

#### `DirectionType`

| Name | Value |
|------|-------|
| `IMPROVING` | `"improving"` |
| `WORSENING` | `"worsening"` |
| `STABLE` | `"stable"` |
| `INCREASING` | `"increasing"` |
| `DECREASING` | `"decreasing"` |

#### `Element`

| Name | Value |
|------|-------|
| `FIRE` | `"fire"` |
| `EARTH` | `"earth"` |
| `AIR` | `"air"` |
| `WATER` | `"water"` |

#### `EntityCategory`

| Name | Value |
|------|-------|
| `PARTNER` | `"partner"` |
| `FAMILY` | `"family"` |
| `FRIEND` | `"friend"` |
| `COWORKER` | `"coworker"` |
| `OTHER` | `"other"` |

#### `EntityStatus`

| Name | Value |
|------|-------|
| `ACTIVE` | `"active"` |
| `ARCHIVED` | `"archived"` |
| `RESOLVED` | `"resolved"` |

#### `House`

| Name | Value |
|------|-------|
| `FIRST` | `"1"` |
| `SECOND` | `"2"` |
| `THIRD` | `"3"` |
| `FOURTH` | `"4"` |
| `FIFTH` | `"5"` |
| `SIXTH` | `"6"` |
| `SEVENTH` | `"7"` |
| `EIGHTH` | `"8"` |
| `NINTH` | `"9"` |
| `TENTH` | `"10"` |
| `ELEVENTH` | `"11"` |
| `TWELFTH` | `"12"` |

#### `MessageRole`

| Name | Value |
|------|-------|
| `USER` | `"user"` |
| `ASSISTANT` | `"assistant"` |

#### `Meter`

| Name | Value |
|------|-------|
| `CLARITY` | `"clarity"` |
| `FOCUS` | `"focus"` |
| `COMMUNICATION` | `"communication"` |
| `RESILIENCE` | `"resilience"` |
| `CONNECTIONS` | `"connections"` |
| `VULNERABILITY` | `"vulnerability"` |
| `ENERGY` | `"energy"` |
| `DRIVE` | `"drive"` |
| `STRENGTH` | `"strength"` |
| `VISION` | `"vision"` |
| `FLOW` | `"flow"` |
| `INTUITION` | `"intuition"` |
| `CREATIVITY` | `"creativity"` |
| `MOMENTUM` | `"momentum"` |
| `AMBITION` | `"ambition"` |
| `EVOLUTION` | `"evolution"` |
| `CIRCLE` | `"circle"` |

#### `MeterGroupV2`

| Name | Value |
|------|-------|
| `MIND` | `"mind"` |
| `HEART` | `"heart"` |
| `BODY` | `"body"` |
| `INSTINCTS` | `"instincts"` |
| `GROWTH` | `"growth"` |

#### `Modality`

| Name | Value |
|------|-------|
| `CARDINAL` | `"cardinal"` |
| `FIXED` | `"fixed"` |
| `MUTABLE` | `"mutable"` |

#### `Planet`

| Name | Value |
|------|-------|
| `SUN` | `"sun"` |
| `MOON` | `"moon"` |
| `MERCURY` | `"mercury"` |
| `VENUS` | `"venus"` |
| `MARS` | `"mars"` |
| `JUPITER` | `"jupiter"` |
| `SATURN` | `"saturn"` |
| `URANUS` | `"uranus"` |
| `NEPTUNE` | `"neptune"` |
| `PLUTO` | `"pluto"` |
| `NORTH_NODE` | `"north node"` |
| `SOUTH_NODE` | `"south node"` |

#### `QualityType`

| Name | Value |
|------|-------|
| `CHALLENGING` | `"challenging"` |
| `TURBULENT` | `"turbulent"` |
| `PEACEFUL` | `"peaceful"` |
| `FLOWING` | `"flowing"` |

#### `RelationshipCategory`

| Name | Value |
|------|-------|
| `LOVE` | `"love"` |
| `FRIEND` | `"friend"` |
| `FAMILY` | `"family"` |
| `COWORKER` | `"coworker"` |
| `OTHER` | `"other"` |

#### `RelationshipLabel`

| Name | Value |
|------|-------|
| `CRUSH` | `"crush"` |
| `DATING` | `"dating"` |
| `SITUATIONSHIP` | `"situationship"` |
| `PARTNER` | `"partner"` |
| `BOYFRIEND` | `"boyfriend"` |
| `GIRLFRIEND` | `"girlfriend"` |
| `SPOUSE` | `"spouse"` |
| `EX` | `"ex"` |
| `FRIEND` | `"friend"` |
| `CLOSE_FRIEND` | `"close_friend"` |
| `NEW_FRIEND` | `"new_friend"` |
| `MOTHER` | `"mother"` |
| `FATHER` | `"father"` |
| `SISTER` | `"sister"` |
| `BROTHER` | `"brother"` |
| `DAUGHTER` | `"daughter"` |
| `SON` | `"son"` |
| `GRANDPARENT` | `"grandparent"` |
| `EXTENDED` | `"extended"` |
| `MANAGER` | `"manager"` |
| `COLLEAGUE` | `"colleague"` |
| `MENTOR` | `"mentor"` |
| `MENTEE` | `"mentee"` |
| `CLIENT` | `"client"` |
| `BUSINESS_PARTNER` | `"business_partner"` |
| `ACQUAINTANCE` | `"acquaintance"` |
| `NEIGHBOR` | `"neighbor"` |
| `EX_FRIEND` | `"ex_friend"` |
| `COMPLICATED` | `"complicated"` |

#### `ZodiacSign`

| Name | Value |
|------|-------|
| `ARIES` | `"aries"` |
| `TAURUS` | `"taurus"` |
| `GEMINI` | `"gemini"` |
| `CANCER` | `"cancer"` |
| `LEO` | `"leo"` |
| `VIRGO` | `"virgo"` |
| `LIBRA` | `"libra"` |
| `SCORPIO` | `"scorpio"` |
| `SAGITTARIUS` | `"sagittarius"` |
| `CAPRICORN` | `"capricorn"` |
| `AQUARIUS` | `"aquarius"` |
| `PISCES` | `"pisces"` |

---

## Astrometer State Labels

Each meter group has 4 state labels based on the unified score quartile.

**Quartile Thresholds:**
- `score < 25` -> bucket 0 (challenging)
- `score >= 25 && < 50` -> bucket 1 (turbulent)
- `score >= 50 && < 75` -> bucket 2 (peaceful)
- `score >= 75` -> bucket 3 (flowing)

### Labels by Group

| Group | 0-25 | 25-50 | 50-75 | 75-100 |
|-------|------|-------|-------|--------|
| **Overall** | Overwhelmed | Turbulent | Peaceful | Flowing |
| **Mind** | Offline | Distracted | On Point | Crystal Clear |
| **Heart** | Heavy | Tender | Grounded | Radiant |
| **Body** | Drained | Running Low | Steady | Fired Up |
| **Instincts** | Off | Noisy | Tuned In | Razor Sharp |
| **Growth** | Stuck | Uphill | Moving | Taking Off |

### iOS Implementation

```swift
// Map unified_score to bucket index
func bucketIndex(score: Double) -> Int {
    if score < 25 { return 0 }
    else if score < 50 { return 1 }
    else if score < 75 { return 2 }
    else { return 3 }
}
```

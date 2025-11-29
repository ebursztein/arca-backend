# Arca Backend API Reference

> Auto-generated on 2025-11-29 13:46:52
> 
> DO NOT EDIT MANUALLY. Run `uv run python functions/generate_api_docs.py` to regenerate.

## Table of Contents

- [Callable Functions](#callable-functions)
- [Model Definitions](#model-definitions)
- [Enum Definitions](#enum-definitions)

---

## Callable Functions

### Charts

#### `natal_chart`

Generate a natal (birth) chart.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `utc_dt` | string | Yes | UTC datetime string |
| `lat` | float | Yes | Latitude |
| `lon` | float | Yes | Longitude |

**Response:** `Complete natal chart data as a dictionary`

---

#### `daily_transit`

TIER 1: Generate daily transit chart (universal, no location).

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `utc_dt` | string | No | Optional, defaults to today midnight UTC |

**Response:** `Transit chart data with planets and aspects (houses will be at 0,0)`

---

#### `user_transit`

TIER 2: Generate user-specific transit chart overlay.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `utc_dt` | string | No | Optional, defaults to now |
| `birth_lat` | float | Yes | User's birth latitude |
| `birth_lon` | float | Yes | User's birth longitude |

**Response:** `Transit chart data with houses relative to user's natal chart location`

---

#### `get_natal_chart_for_connection`

Get natal chart for a connection.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `connection_id` | string | Yes | - |

**Response:** `Natal chart data for the connection`

---

#### `get_synastry_chart`

*Memory: 512MB*

Get both natal charts and synastry aspects in a single call.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `connection_id` | string | Yes | - |

**Response:** `NatalChartData`

---

### User Management

#### `create_user_profile`

*Requires: GEMINI_API_KEY, POSTHOG_API_KEY*

Create user profile with birth chart computation and LLM-generated summary.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `name` | string | Yes | - |
| `email` | string | Yes | - |
| `birth_date` | string | Yes | YYYY-MM-DD (REQUIRED) |
| `birth_time` | string | No | HH:MM (optional) |
| `birth_timezone` | string | Yes | - |
| `birth_lat` | float | No | Latitude (optional) |
| `birth_lon` | float | No | Longitude (optional) |

**Response:** `{`

---

#### `get_user_profile`

Get user profile from Firestore.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |

**Response:** `Complete user profile dictionary or error if not found`

---

#### `get_memory`

Get memory collection for a user (for LLM personalization).

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |

**Response:** `Memory collection dictionary`

---

#### `get_sun_sign_from_date`

Get sun sign from birth date.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `birth_date` | string | Yes | YYYY-MM-DD |

**Response:** `{`

---

#### `register_device_token`

Register device token for push notifications.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `device_token` | string | Yes | - |

**Response:** `{ "success": true }`

---

### Horoscope

#### `get_daily_horoscope`

*Memory: 512MB | Requires: GEMINI_API_KEY, POSTHOG_API_KEY*

Generate daily horoscope - complete reading with meter groups.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `date` | string | No | Optional, defaults to today |

**Response:** `DailyHoroscope`

---

#### `get_astrometers`

Calculate all 17 astrological meters for a user on a given date.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `date` | string | No | Optional, defaults to today |

**Response:** `{`

---

### Connections

#### `create_connection`

Manually create a connection (not via share link).

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `connection` | string | Yes | - |
| `name` | string | Yes | - |
| `birth_date` | string | Yes | - |
| `birth_time` | string | No | Optional |
| `birth_lat` | float | No | Optional |
| `birth_lon` | float | No | Optional |
| `birth_timezone` | string | Yes | - |
| `relationship_type` | string | Yes | - |

**Response:** `Created connection data`

---

#### `update_connection`

Update a connection's details.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `connection_id` | string | Yes | - |
| `updates` | string | Yes | - |
| `name` | string | Yes | - |
| `relationship_type` | string | Yes | - |

**Response:** `Updated connection data`

---

#### `delete_connection`

Delete a connection.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `connection_id` | string | Yes | - |

**Response:** `{ "success": true }`

---

#### `list_connections`

List all user's connections.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `limit` | int | No | Optional, default 50 |

**Response:** `{`

---

### Sharing

#### `get_share_link`

Get user's shareable profile link for "Add me on Arca".

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |

**Response:** `{`

---

#### `get_public_profile`

Fetch public profile data from a share link.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `share_secret` | string | Yes | - |

**Response:** `object`

---

#### `import_connection`

Add a connection from a share link.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `share_secret` | string | Yes | - |
| `relationship_type` | string | Yes | - |

**Response:** `{`

---

#### `list_connection_requests`

List pending connection requests for a user.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |

**Response:** `{`

---

#### `update_share_mode`

Toggle between public and request-only share modes.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `share_mode` | string | Yes | or "public" |

**Response:** `{ "share_mode": "request" }`

---

#### `respond_to_request`

Approve or reject a connection request.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `request_id` | string | Yes | - |
| `action` | string | Yes | or "reject" |

**Response:** `{ "success": true, "action": "approved", "connection_id": "..." }`

---

### Compatibility

#### `get_compatibility`

*Memory: 512MB | Requires: GEMINI_API_KEY, POSTHOG_API_KEY*

Get compatibility analysis between user and a connection.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `connection_id` | string | Yes | - |

**Response:** `{`

---

### Other

#### `update_user_profile`

*Requires: GEMINI_API_KEY, POSTHOG_API_KEY*

Update user profile with optional natal chart regeneration.

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | - |
| `photo_path` | string | Yes | - |
| `birth_time` | string | Yes | - |
| `birth_timezone` | string | Yes | - |
| `birth_lat` | float | Yes | - |
| `birth_lon` | float | Yes | - |

**Response:** `{`

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
| `relationship_type` | string | Yes | PydanticUndefined | - | friend/romantic/family/coworker |
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
| `relationship_type` | "friend" | "romantic" | "family" | "coworker" | Yes | PydanticUndefined | - | Relationship category |
| `vibe` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Personalized vibe sentence with their name, e.g., 'Great ... |
| `vibe_score` | int | Yes | PydanticUndefined | >= 0, <= 100 | 0-100 score (70-100=positive, 40-70=neutral, 0-40=challen... |
| `key_transit` | string | Yes | PydanticUndefined | min_length: 1, max_length: 500 | Most significant transit, e.g., 'Transit Venus trine your... |

### Astrometers

#### `AstrometersForIOS`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `date` | string | Yes | PydanticUndefined | - | ISO date of reading |
| `overall_unified_score` | float | Yes | PydanticUndefined | >= -100, <= 100 | Overall unified score across all meters (-100 to +100) |
| `overall_intensity` | MeterReading | Yes | PydanticUndefined | - | Overall intensity meter with state_label |
| `overall_harmony` | MeterReading | Yes | PydanticUndefined | - | Overall harmony meter with state_label |
| `overall_quality` | string | Yes | PydanticUndefined | - | Overall quality: harmonious, challenging, mixed, quiet, p... |
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
| `unified_score` | float | Yes | PydanticUndefined | >= -100, <= 100 | Average unified score of member meters (-100 to +100) |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | Average intensity of member meters |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | Average harmony of member meters |
| `state_label` | string | Yes | PydanticUndefined | - | Aggregated state label from group JSON (contextual to group) |
| `quality` | string | Yes | PydanticUndefined | - | Generic enum: excellent, supportive, harmonious, peaceful... |
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
| `unified_score` | float | Yes | PydanticUndefined | >= -100, <= 100 | Primary display value (-100 to +100, polar-style from int... |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | Activity level - how much is happening |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | Quality - supportive (high) vs challenging (low) |
| `unified_quality` | string | Yes | PydanticUndefined | - | Simple category: harmonious, challenging, mixed, quiet, p... |
| `state_label` | string | Yes | PydanticUndefined | - | Rich contextual state from JSON: 'Peak Performance', 'Pus... |
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
| `unified_score` | float | Yes | PydanticUndefined | >= -100, <= 100 | - |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | - |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | - |
| `unified_quality` | string (enum: QualityLabel) | Yes | PydanticUndefined | - | - |
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
| `relationship_type` | "friend" | "romantic" | "family" | "coworker" | Yes | PydanticUndefined | - | Relationship category |
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
| `status` | Literal | No | 'pending' | - | - |
| `created_at` | string | Yes | PydanticUndefined | - | ISO timestamp |

#### `ShareLinkResponse`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `share_url` | string | Yes | PydanticUndefined | - | - |
| `share_mode` | Literal | Yes | PydanticUndefined | - | - |
| `qr_code_data` | string | Yes | PydanticUndefined | - | - |

#### `PublicProfileResponse`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `profile` | object | Yes | PydanticUndefined | - | Public profile data |
| `share_mode` | Literal | Yes | PydanticUndefined | - | - |
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
| `romantic` | ModeCompatibility | Yes | PydanticUndefined | - | - |
| `friendship` | ModeCompatibility | Yes | PydanticUndefined | - | - |
| `coworker` | ModeCompatibility | Yes | PydanticUndefined | - | - |
| `aspects` | SynastryAspect[] | Yes | PydanticUndefined | - | All synastry aspects found |
| `composite_summary` | CompositeSummary | null | No | null | - | - |
| `calculated_at` | string | Yes | PydanticUndefined | - | ISO timestamp |

#### `ModeCompatibility`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `overall_score` | int | Yes | PydanticUndefined | >= 0, <= 100 | Overall score (0-100) |
| `relationship_verb` | string | null | No | null | - | e.g., 'You spark each other' |
| `categories` | CompatibilityCategory[] | Yes | PydanticUndefined | - | - |
| `missing_data_prompts` | string[] | No | PydanticUndefined | - | - |

#### `CompatibilityCategory`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `id` | string | Yes | PydanticUndefined | - | Category ID: emotional, communication, etc. |
| `name` | string | Yes | PydanticUndefined | - | Display name |
| `score` | int | Yes | PydanticUndefined | >= -100, <= 100 | Category score (-100 to +100) |
| `summary` | string | null | No | null | - | LLM-generated summary |
| `aspect_ids` | string[] | No | PydanticUndefined | - | Contributing aspect IDs |

#### `SynastryAspect`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `id` | string | Yes | PydanticUndefined | min_length: 1, max_length: 32 | Unique aspect ID |
| `user_planet` | string | Yes | PydanticUndefined | min_length: 1, max_length: 32 | Planet from user's chart |
| `their_planet` | string | Yes | PydanticUndefined | min_length: 1, max_length: 32 | Planet from connection's chart |
| `aspect_type` | string | Yes | PydanticUndefined | min_length: 1, max_length: 32 | conjunction, trine, square, etc. |
| `orb` | float | Yes | PydanticUndefined | >= 0, <= 20 | Orb in degrees |
| `is_harmonious` | boolean | Yes | PydanticUndefined | - | True if supportive aspect |
| `interpretation` | string | null | No | null | max_length: 2000 | LLM-generated meaning |

#### `CompositeSummary`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `composite_sun` | string | null | No | null | - | Composite Sun sign |
| `composite_moon` | string | null | No | null | - | Composite Moon sign |
| `summary` | string | null | No | null | - | LLM-generated composite summary |
| `strengths` | string[] | No | PydanticUndefined | - | - |
| `challenges` | string[] | No | PydanticUndefined | - | - |

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
| `attribute_updates` | AttributeKV[] | No | PydanticUndefined | max_length: 50 | Attributes to add/update (e.g., [{'key': 'birthday_season... |
| `link_to_entity_id` | string | null | No | null | max_length: 64 | Entity ID to link/relate to (if action='link' or creating... |

#### `MergedEntities`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `actions` | EntityMergeAction[] | No | PydanticUndefined | max_length: 100 | List of merge actions to execute |

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
| `unified_score` | float | Yes | PydanticUndefined | >= -100, <= 100 | Primary display value (-100 to +100), average of member m... |
| `harmony` | float | Yes | PydanticUndefined | >= 0, <= 100 | Supportive vs challenging quality (0-100) |
| `intensity` | float | Yes | PydanticUndefined | >= 0, <= 100 | Activity level (0-100) |

#### `MeterGroupState`

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `label` | string | Yes | PydanticUndefined | min_length: 1, max_length: 50 | Human-readable state: Excellent, Supportive, Challenging,... |
| `quality` | string (enum: QualityType) | Yes | PydanticUndefined | - | Quality type: excellent, supportive, harmonious, peaceful... |

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

#### `QualityType`

| Name | Value |
|------|-------|
| `EXCELLENT` | `"excellent"` |
| `SUPPORTIVE` | `"supportive"` |
| `HARMONIOUS` | `"harmonious"` |
| `PEACEFUL` | `"peaceful"` |
| `MIXED` | `"mixed"` |
| `QUIET` | `"quiet"` |
| `CHALLENGING` | `"challenging"` |
| `INTENSE` | `"intense"` |

#### `RelationshipType`

| Name | Value |
|------|-------|
| `FRIEND` | `"friend"` |
| `ROMANTIC` | `"romantic"` |
| `FAMILY` | `"family"` |
| `COWORKER` | `"coworker"` |

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

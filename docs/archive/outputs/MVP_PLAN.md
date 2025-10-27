# MVP Plan: Daily Personalized Horoscope App

## Product Vision

**V1 (MVP)**: Sun sign + transits horoscope with 8 categories, personalized per user, no storage
**V2**: Full natal chart integration (exact birth time)
**V3**: Q&A with tarot readings → journal storage begins
**V4**: Insights about cards drawn and themes encountered

---

## V1 MVP Scope (What We're Building Now)

### User Flow

```
┌─────────────────────────────────────────────────────────┐
│  AUTHENTICATION                                          │
│  • Sign in with Apple                                   │
│  • Sign in with Google                                  │
│  • Capture: user_id, name, email                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  ONBOARDING (One-time)                                   │
│  1. Collect birth date (MM-DD-YYYY)                     │
│  2. Calculate sun sign                                   │
│  3. Show interesting fact about their sign              │
│  4. Select interests from 8 categories                  │
│  5. Store user profile in Firestore                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  MAIN SCREEN (Daily)                                     │
│  • Date header                                           │
│  • Sun sign icon                                        │
│  • Short summary (2-3 sentences)                        │
│  • "Read more" button                                    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  EXPANDED VIEW (On demand)                               │
│  • Full prediction by selected categories               │
│  • Each category gets detailed section                  │
│  • Track which sections user reads                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  JOURNAL ENTRY (Background)                              │
│  • Create journal entry with full text of what they read│
│  • Update memory: category interests + recent readings  │
│  • Build personalization for future predictions         │
│  • Foundation for V3+ tarot/reflection journal          │
└─────────────────────────────────────────────────────────┘
```

---

## The 8 Interest Categories

| Category | Icon | Description | LLM Definition |
|----------|------|-------------|----------------|
| **Love & Relationships** | 💕 | Romance, dating, partnerships | Questions concerning romantic partnerships, dating, and emotional state related to a significant other. Includes finding a partner, improving relationships, healing from breakups, compatibility, communication, and commitment. Excludes family/friends. |
| **Family & Friendships** | 👥 | Platonic and familial relationships | Interpersonal dynamics with family and friends. Includes healing rifts, improving communication, family patterns, navigating friendships, boundaries, parenting, sibling dynamics. Excludes romantic partnerships. |
| **Path & Profession** | 💼 | Career, work, education, life path | Career, work, education, and professional life path. Includes job changes, career direction, professional development, workplace dynamics, finding fulfilling vocation, educational pursuits, entrepreneurship. Distinct from finance. |
| **Personal Growth & Well-being** | 🌱 | Self-improvement, healing, wellness | Self-improvement, self-awareness, emotional healing, mental health, physical well-being, shadow work, habits, overcoming obstacles. Focuses on internal state and personal development. Excludes explicitly spiritual questions. |
| **Finance & Abundance** | 💰 | Money, wealth, material resources | Money, wealth, financial stability, investments, material resources, money mindset. Includes improving financial situation, managing debt, financial decisions, overcoming blocks, relationship with money. |
| **Life Purpose & Spirituality** | ✨ | Deeper meaning, destiny, spiritual connection | Deeper meaning, destiny, soul's journey, spiritual gifts, karmic lessons, ancestral wisdom, psychic development, connection to universe/higher power. Existential inquiries beyond day-to-day growth. |
| **Home & Environment** | 🏡 | Living spaces, relocation, surroundings | Living situations, moving, relocating, home purchases, creating harmonious spaces, roommate dynamics, impact of physical environment on wellbeing. |
| **Decisions & Crossroads** | 🔀 | Choice-making, turning points | Making choices between options, understanding outcomes, clarity at major turning points, determining timing. Functional category applying to any life area emphasizing discernment. |

---

## Data Models

### 1. User Profile (Firestore: `users/{userId}`)
**Client-accessible data:**
```typescript
{
  user_id: string,          // From Firebase Auth
  name: string,             // From Apple/Google
  email: string,            // From Apple/Google

  // Birth information
  birth_date: Timestamp,    // Firebase Timestamp (midnight UTC of birth date)
  birth_time: string,       // "HH:MM" in local time (optional, V2+)
  birth_timezone: string,   // IANA timezone (optional, V2+)
  birth_lat: float,         // Birth location latitude (optional)
  birth_lon: float,         // Birth location longitude (optional)

  sun_sign: string,         // "taurus"

  // Birth chart data (computed at init)
  natal_chart: object,      // Complete NatalChartData from get_astro_chart()
  exact_chart: boolean,     // True if birth_time + timezone provided, False if approximate

  created_at: Timestamp,    // Firebase Timestamp
  last_active: Timestamp    // Firebase Timestamp
}
```

**Chart Computation:**
- **V1 (no birth time)**: Approximate chart using noon UTC at (0, 0)
  - Accurate: Sun sign, planetary positions, aspects
  - Approximate: Houses, angles (not meaningful without location/time)
  - `exact_chart = false`

- **V2+ (with birth time)**: Exact chart using provided time/location
  - Accurate: Everything including houses and angles
  - `exact_chart = true`

### 2. Memory Collection (Firestore: `memory/{userId}`)
**Server-side only - NOT accessible to client via security rules:**
```typescript
{
  user_id: string,

  // Category engagement tracking
  categories: {
    love_relationships: {
      count: number,              // Total times viewed
      last_mentioned: Timestamp   // Firebase Timestamp of last view
    },
    family_friendships: {
      count: number,
      last_mentioned: Timestamp
    },
    path_profession: {
      count: number,
      last_mentioned: Timestamp
    },
    personal_growth: {
      count: number,
      last_mentioned: Timestamp
    },
    finance_abundance: {
      count: number,
      last_mentioned: Timestamp
    },
    purpose_spirituality: {
      count: number,
      last_mentioned: Timestamp
    },
    home_environment: {
      count: number,
      last_mentioned: Timestamp
    },
    decisions_crossroads: {
      count: number,
      last_mentioned: Timestamp
    }
  },

  // Last 10 readings with full text (FIFO queue)
  recent_readings: [
    {
      date: Timestamp,              // Firebase Timestamp of reading
      summary: string,              // Summary they saw on main screen
      categories_viewed: [
        {
          category: string,         // "love_relationships"
          text: string              // FULL TEXT of what they read
        }
      ]
    }
    // ... up to 10 readings (oldest removed when adding 11th)
  ],

  updated_at: Timestamp               // Firebase Timestamp
}
```

### 3. Journal Entries (Firestore: `users/{userId}/journal/{entryId}`)
Track readings and build user's spiritual journey. In V1: horoscope readings. In V3+: includes tarot, reflections, Q&A.
```typescript
{
  entry_id: string,             // Auto-generated
  date: Timestamp,              // Firebase Timestamp of reading
  entry_type: string,           // V1: "horoscope_reading", V3+: "tarot_reading", "reflection"

  // V1: Horoscope reading data
  summary_viewed: string,       // The summary text they saw
  categories_viewed: [          // Which categories they expanded
    {
      category: string,         // "love_relationships"
      text: string              // FULL TEXT of what they read
    }
  ],

  // V3+: Additional fields for tarot/reflections
  // tarot_cards: [...],        // Cards drawn
  // user_question: string,     // Their question
  // user_notes: string,        // Their own reflections

  time_spent_seconds: number,
  created_at: Timestamp         // Firebase Timestamp
}
```

---

## Architecture: Journal → Memory Flow

**Single Source of Truth Pattern:**

```
┌─────────────────────────────────────────────────────────────┐
│  iOS APP                                                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ add_journal_entry()
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  CALLABLE FUNCTION: add_journal_entry()                      │
│  • Validate input                                           │
│  • Write to journal collection                              │
│  • Return entry_id                                          │
│  • DOES NOT touch memory collection                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Document created
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  FIRESTORE TRIGGER: on_document_created                      │
│  Path: users/{userId}/journal/{entryId}                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Automatically fires
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  BACKGROUND FUNCTION: update_memory_on_journal_entry()       │
│  • Read journal entry from event.data                       │
│  • Extract categories_viewed, date, summary                 │
│  • Update memory/{userId} atomically:                       │
│    - Increment category counts                              │
│    - Update last_mentioned timestamps                       │
│    - Add to recent_readings (FIFO, max 10)                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  MEMORY COLLECTION                                           │
│  • Derivative cache (not source of truth)                   │
│  • Used for personalization                                 │
│  • Can be rebuilt from journal at any time                  │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
- **Decoupled**: add_journal_entry has one job, trigger has one job
- **Single source of truth**: Journal is immutable log
- **Rebuildable**: Can regenerate memory from journal history
- **Scalable**: Easy to add more triggers (analytics, insights, etc.)
- **Testable**: Each function independently testable
- **Debuggable**: Clear data flow, easy to trace issues

---

## Working with Firebase Timestamps

**Python Implementation:**
```python
from firebase_admin import firestore
from datetime import datetime

# Get server timestamp (recommended)
firestore.SERVER_TIMESTAMP  # Use for created_at, updated_at

# Convert datetime to Timestamp
birth_datetime = datetime(1980, 4, 20, 0, 0, 0)  # Midnight UTC
birth_timestamp = firestore.Timestamp.from_datetime(birth_datetime)

# Convert Timestamp to datetime (for calculations)
birth_dt = timestamp.to_datetime()

# Query with timestamp ranges
query = db.collection('journal').where('date', '>=', start_timestamp).where('date', '<=', end_timestamp)
```

**Benefits:**
- Efficient indexing and querying
- Built-in timezone handling
- Consistent across all Firebase SDKs
- Automatic sorting in queries

---

## Backend Functions to Build

### Phase 1: Core Logic (Python functions)

#### Sun Sign Calculator
```python
def get_sun_sign(birth_date: str) -> str:
    """
    Convert birth date to sun sign.

    Args:
        birth_date: "YYYY-MM-DD" format

    Returns:
        Sun sign: "aries", "taurus", "gemini", etc.
    """
```

#### Sun Sign Facts
```python
SUN_SIGN_FACTS = {
    "aries": "As an Aries, you're a cosmic pioneer...",
    "taurus": "Taurus energy is all about building beauty...",
    # ... all 12 signs
}

def get_sun_sign_fact(sun_sign: str) -> str:
    """Return interesting fact about a sun sign."""
```

#### Transit Summarizer
```python
def summarize_daily_transits(transit_data: dict, sun_sign: str) -> str:
    """
    Extract key transit aspects relevant to a sun sign.

    Focuses on:
    - Sun aspects (everyone feels these)
    - Moon aspects (emotional tone)
    - Mercury/Venus/Mars aspects (daily affairs)
    - Aspects involving user's sun sign ruler

    Returns human-readable summary for LLM context.
    """
```

#### LLM Horoscope Generator
```python
from google import genai
from posthog import Posthog

def generate_horoscope_with_llm(
    date: str,
    sun_sign: str,
    transit_summary: str,
    memory_data: dict  # NEW: personalization context
) -> dict:
    """
    Generate personalized horoscope via Google Gemini.

    Uses memory_data to personalize:
    - category_engagement: Which categories they view most
    - recent_readings: Last 10 readings with full text for continuity

    Uses PostHog to track:
    - Token usage (input/output)
    - Generation latency
    - Cost estimation
    - Model version (gemini-1.5-pro, gemini-1.5-flash, etc.)
    - Success/failure rates

    References:
    - Gemini SDK: https://googleapis.github.io/python-genai/
    - PostHog LLM tracking: https://posthog.com/docs/llm-analytics

    Args:
        date: "2025-10-17"
        sun_sign: "taurus"
        transit_summary: Key aspects for the day
        memory_data: {
            "categories": {...},      // Engagement counts
            "recent_readings": [...]  // Last 10 with full text
        }

    Returns (streaming):
    {
        "technical_analysis": str,  // How insights derived (planets, aspects, transits)
        "summary": str,             // 2-3 sentences for main screen
        "details": {
            "love_relationships": str,
            "family_friendships": str,
            "path_profession": str,
            "personal_growth": str,
            "finance_abundance": str,
            "purpose_spirituality": str,
            "home_environment": str,
            "decisions_crossroads": str
        }
    }

    Note: Uses streaming response for perceived speed.

    Implementation with Google Gemini:
    ```python
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Enable streaming for faster perceived performance
    response = client.models.generate_content_stream(
        model='gemini-1.5-flash',  # Fast model for streaming
        contents=[prompt],
        config={
            'temperature': 0.7,
            'response_mime_type': 'application/json'
        }
    )

    # Stream chunks as they arrive
    for chunk in response:
        # Send chunk to client via Firebase callable streaming
        # (or collect and return full response)
        yield chunk.text
    ```

    References:
    - Gemini Streaming: https://googleapis.github.io/python-genai/
    - Firebase Callable Streaming: May need HTTP streaming endpoint
    """
```

### Phase 2: Firebase Callable Functions

```python
@https_fn.on_call()
def create_user_profile(req: https_fn.CallableRequest) -> dict:
    """
    Create user profile after onboarding.

    Args:
        birth_date: "1980-04-20"
        interests: {
            "love_relationships": true,
            "path_profession": true,
            ...
        }

    Returns:
        {
            "user_id": str,
            "sun_sign": str,
            "sun_sign_fact": str
        }
    """

@https_fn.on_call()
def get_daily_horoscope(req: https_fn.CallableRequest) -> dict:
    """
    Generate personalized daily horoscope for user with streaming.

    NO CACHING - Generated on-demand per user with personalization from memory.

    Args:
        user_id: str
        date: str (optional, defaults to today)
        stream: bool (optional, defaults to true for better UX)

    Process:
        1. Get user profile (sun_sign, birth_date)
        2. Get memory collection (category interests, last 10 readings)
        3. Get transit data for date
        4. Generate personalized horoscope via LLM with memory context (streaming)
        5. Return horoscope (NOT stored)

    Returns (streaming if requested):
        {
            "date": str,
            "sun_sign": str,
            "technical_analysis": str,  // NEW: The astronomical "why"
            "summary": str,
            "details": {...}  // All 8 categories
        }

    Note: Streaming provides better perceived performance. Chunks are sent as
    they're generated, making the app feel fast even with longer content.
    """

@https_fn.on_call()
def add_journal_entry(req: https_fn.CallableRequest) -> dict:
    """
    Create a journal entry when user reads their horoscope.

    SINGLE RESPONSIBILITY: Write to journal collection only.
    Memory updates happen automatically via Firestore trigger.

    This is the foundational journal entry logic. In V1, it tracks which
    categories they viewed. In V3+, this will expand to include:
    - User's own reflections/notes
    - Tarot readings from Q&A
    - Multi-card spreads
    - Conversational guidance

    Args:
        user_id: str
        date: Timestamp  // Firebase Timestamp of reading
        entry_type: str  // V1: "horoscope_reading", V3+: "tarot_reading", "reflection"
        summary: str  // The summary text shown on main screen (or tarot reading summary)
        categories_viewed: [  // V1: horoscope categories, V3+: could be tarot themes
            {
                "category": str,  // "love_relationships"
                "text": str       // FULL TEXT of what they read
            }
        ]
        time_spent_seconds: int  // How long they spent reading

    Process:
        1. Validate input data
        2. Create journal entry document in users/{userId}/journal/{entryId}
        3. Use firestore.SERVER_TIMESTAMP for created_at
        4. Return entry_id
        5. [AUTOMATIC] Firestore trigger updates memory collection

    Returns:
        {
            "success": true,
            "entry_id": str  // For future reference (V3+)
        }

    Note: Memory collection is updated AUTOMATICALLY by the
    update_memory_on_journal_entry trigger. This creates a clean
    separation: journal = immutable log, memory = derivative cache.
    """

@https_fn.on_call()
def get_user_profile(req: https_fn.CallableRequest) -> dict:
    """Get user profile by user_id."""
```

### Phase 3: Background Jobs

```python
@firestore_fn.on_document_created(document="users/{userId}/journal/{entryId}")
def update_memory_on_journal_entry(event):
    """
    Firestore trigger: Update memory collection when journal entry is created.

    SINGLE RESPONSIBILITY: Read journal entry, update memory collection.
    This creates a clean separation of concerns:
    - Journal = immutable log of user activity (source of truth)
    - Memory = derivative cache for personalization

    In V1: Triggered when user reads horoscope categories.
    In V3+: Also triggered by tarot readings, reflections, Q&A.

    Process:
        1. Read the newly created journal entry from event.data
        2. Extract entry_type, categories_viewed, date
        3. Update memory/{userId} atomically:
           - For each category: increment count, update last_mentioned
           - Add to recent_readings array (FIFO, max 10)
           - Set updated_at to firestore.SERVER_TIMESTAMP
        4. Handle errors gracefully (journal entry already exists)

    Benefits:
        - Decoupled: add_journal_entry doesn't need to know about memory logic
        - Single source of truth: journal is the canonical record
        - Rebuildable: Can regenerate entire memory collection from journal
        - Scalable: Can add more triggers for analytics, insights, etc.
        - Testable: Each function has one clear job

    Example Flow:
        1. iOS calls add_journal_entry() → writes to journal collection
        2. Trigger fires automatically → reads journal entry
        3. Trigger updates memory/{userId} → personalization ready
        4. Next horoscope request uses updated memory
    """
```

---

## LLM Prompt Template

```
You are a mystical astrologer providing personalized daily guidance.

Context:
- Date: {date}
- Sun Sign: {sun_sign}
- Today's Cosmic Energies: {transit_summary}

Personalization Data (from user's journey):
- Category Interests: {category_engagement}
  (Shows which categories they view most frequently and recently)

- Last 10 Readings: {recent_readings}
  (Their recent horoscope summaries and full text of categories they viewed)
  Use this to:
  • Build continuity across daily readings
  • Reference themes they've been exploring
  • Avoid repeating the same guidance
  • Create a sense of journey and progression
  • Show you "know" them intuitively

Generate a daily horoscope with the following structure:

1. TECHNICAL ANALYSIS (3-5 sentences):
   Explain the astronomical "why" behind today's energy. Reference specific planetary
   movements, aspects, and transits. Examples:
   - "Venus trines Neptune at 15° today, opening portals of divine love"
   - "Mars squares your sun sign ruler, activating your core identity"
   - "The Moon moves through Scorpio, deepening emotional currents"

   This provides credibility and grounds mystical insights in real celestial mechanics.
   Use accessible language but be specific about degrees, planets, and aspect types.

2. SUMMARY (2-3 sentences):
   Capture the essence of today's energy for {sun_sign}. Use mystical, elevated tone.
   Directly address them as "you". This appears on the main screen.

3. DETAILED PREDICTIONS (one paragraph each, ~80-120 words):

   LOVE & RELATIONSHIPS:
   How today's energy affects romantic partnerships, dating, and emotional connections
   with a significant other. Include guidance on communication, compatibility, and commitment.

   FAMILY & FRIENDSHIPS:
   Guidance for interpersonal dynamics with family and friends. Include insights on
   healing rifts, improving communication, understanding family patterns, and navigating friendships.

   PATH & PROFESSION:
   Career, work, and professional life path guidance. Include insights on job situations,
   career direction, workplace dynamics, and finding fulfilling vocation.

   PERSONAL GROWTH & WELL-BEING:
   Self-improvement, emotional healing, and wellness focus. Include guidance on self-awareness,
   overcoming obstacles, habits, and internal development.

   FINANCE & ABUNDANCE:
   Money, wealth, and material resources guidance. Include insights on financial decisions,
   improving financial situation, money mindset, and relationship with abundance.

   LIFE PURPOSE & SPIRITUALITY:
   Soul-level guidance on deeper meaning, destiny, spiritual gifts, and connection to
   higher purpose. Include karmic lessons and existential insights.

   HOME & ENVIRONMENT:
   Guidance for living situations, physical spaces, and how surroundings affect wellbeing.
   Include insights on creating harmony and environmental impact.

   DECISIONS & CROSSROADS:
   Guidance for making choices and navigating turning points. Include insights on
   discernment, timing, and clarity when facing options.

Style Guidelines:
- Elevated, mystical language (think sacred, not casual)
- Transformational framing (spiritual evolution, not problem-solving)
- Personal and intimate (use "you", feel knowing and intuitive)
- Ancient wisdom meets modern life
- Never mention AI, algorithms, or technology
- Each category should feel actionable yet mystical

Return as JSON:
{
  "technical_analysis": "Venus trines Neptune at 15° today...",
  "summary": "...",
  "details": {
    "love_relationships": "...",
    "family_friendships": "...",
    "path_profession": "...",
    "personal_growth": "...",
    "finance_abundance": "...",
    "purpose_spirituality": "...",
    "home_environment": "...",
    "decisions_crossroads": "..."
  }
}
```

---

## MVP Script (`mvp.py`)

Simulate the entire user journey end-to-end:

```python
#!/usr/bin/env python3
"""
MVP simulation of the complete user journey.

Tests the full flow:
1. User authentication (simulated)
2. Onboarding with interests
3. Daily horoscope generation
4. Category detail viewing
5. Engagement tracking
"""

def main():
    print("="*60)
    print("ARCA MVP SIMULATION")
    print("="*60)

    # 1. AUTHENTICATION (simulated)
    user = {
        "id": "user123",
        "name": "Alice",
        "email": "alice@example.com"
    }
    print(f"\n✓ User authenticated: {user['name']}")

    # 2. ONBOARDING
    print("\n--- ONBOARDING ---")
    birth_date = "1980-04-20"
    sun_sign = get_sun_sign(birth_date)
    print(f"Birth Date: {birth_date}")
    print(f"Sun Sign: {sun_sign.title()}")
    print(f"\n{get_sun_sign_fact(sun_sign)}")

    # Simulate interest selection
    interests = {
        "love_relationships": True,
        "family_friendships": False,
        "path_profession": True,
        "personal_growth": True,
        "finance_abundance": True,
        "purpose_spirituality": False,
        "home_environment": False,
        "decisions_crossroads": True
    }
    print(f"\nSelected interests: {[k for k, v in interests.items() if v]}")

    # 3. DAILY HOROSCOPE GENERATION
    print("\n--- GENERATING DAILY HOROSCOPE ---")
    today = datetime.now().strftime("%Y-%m-%d")

    # Get transit data
    transit_data = get_daily_transit_data(today)
    transit_summary = summarize_daily_transits(transit_data, sun_sign)
    print(f"Transit summary: {transit_summary}")

    # Get memory data for personalization (simulated as empty for first time)
    memory_data = {
        "categories": {
            "love_relationships": {"count": 0, "last_mentioned": None},
            # ... other categories
        },
        "recent_readings": []  # Empty for first-time user
    }

    # Generate personalized horoscope via LLM with memory context
    horoscope = generate_horoscope_with_llm(
        today, sun_sign, transit_summary, memory_data
    )

    # 4. MAIN SCREEN DISPLAY
    print("\n" + "="*60)
    print(f"DAILY HOROSCOPE FOR {sun_sign.upper()}")
    print(f"{today}")
    print("="*60)

    # Technical Analysis (the astronomical "why")
    print("\n### Technical Analysis ###")
    print(horoscope["technical_analysis"])

    # Summary
    print("\n### Summary ###")
    print(horoscope["summary"])
    print("\n[Read More ↓]")

    # 5. EXPANDED VIEW (simulate user clicking categories)
    print("\n--- DETAILED PREDICTIONS ---")
    user_views = ["love_relationships", "path_profession", "personal_growth"]

    for category in user_views:
        print(f"\n### {category.replace('_', ' ').title()} ###")
        print(horoscope["details"][category])

    # 6. CREATE JOURNAL ENTRY
    print("\n--- CREATING JOURNAL ENTRY ---")
    categories_with_text = [
        {
            "category": cat,
            "text": horoscope["details"][cat]  # Full text of what they read
        }
        for cat in user_views
    ]
    entry_id = add_journal_entry(
        user_id=user["id"],
        date=today,
        entry_type="horoscope_reading",  # V1: horoscope readings
        summary=horoscope["summary"],     # Summary shown on main screen
        categories_viewed=categories_with_text
    )
    print(f"✓ Journal entry created: {entry_id}")
    print(f"✓ Categories viewed: {user_views}")
    print("✓ Memory updated: category counts + recent_readings")
    print("✓ Full text stored for LLM continuity")
    print("\nNote: In V3+, this same function will handle tarot readings, reflections, Q&A")

    print("\n" + "="*60)
    print("MVP SIMULATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
```

---

## Implementation Checklist

### Phase 1: Core Logic (mvp.py simulation)
- [ ] Sun sign calculator function
- [ ] Sun sign facts database (12 facts)
- [ ] Transit summarizer (extract key aspects from daily_transit())
- [ ] Technical analysis formatter (convert transits to technical analysis text)
- [ ] Google Gemini API setup (API key, client initialization)
- [ ] PostHog SDK setup for LLM tracking
- [ ] LLM prompt template with technical analysis + memory/personalization context
- [ ] Horoscope generator function with:
  - Streaming support (generate_content_stream)
  - PostHog instrumentation
  - Memory integration
  - Technical analysis section
- [ ] Memory data formatter (prepare context for LLM)
- [ ] Complete mvp.py script with streaming demonstration
- [ ] Test until output feels right (check continuity, technical accuracy, streaming speed)

### Phase 2: Firebase Integration
- [ ] Firestore schema setup (collections: users, memory, journal)
- [ ] `create_user_profile()` callable function
- [ ] `get_user_profile()` callable function
- [ ] `get_daily_horoscope()` callable function
  - Get user profile and memory collection
  - Get transit data
  - Generate personalized horoscope with memory context
  - Return (NO storage of horoscope)
- [ ] `add_journal_entry()` callable function (foundational for V3+)
  - ONLY writes to journal collection
  - Accept full text of categories viewed
  - Return entry_id
  - Memory updates happen via trigger (decoupled)
- [ ] Test all functions with test.py

### Phase 3: Background Jobs
- [ ] `update_memory_on_journal_entry()` Firestore trigger
  - Trigger path: `users/{userId}/journal/{entryId}` (on_document_created)
  - Read journal entry from event.data
  - Update category counts and last_mentioned atomically
  - Add to recent_readings (FIFO, max 10)
  - Works for V1 horoscope readings AND V3+ tarot/reflections
  - This creates clean separation: journal = source of truth, memory = cache
- [ ] Error handling and retry logic
- [ ] Logging and monitoring
- [ ] (Future) Utility to rebuild memory collection from journal history

### Phase 4: iOS Integration
- [ ] iOS Firebase Auth setup (Apple/Google)
- [ ] iOS onboarding flow (call create_user_profile)
- [ ] iOS main screen (call get_daily_horoscope with streaming)
  - Display technical analysis first as it streams in
  - Then summary
  - Then category details
  - Show loading skeleton/animation while streaming
- [ ] iOS expanded view (show category details)
- [ ] iOS journal entry creation (call add_journal_entry)
  - V1: Track which horoscope categories they viewed
  - V3+: Will expand to tarot readings, reflections, Q&A
- [ ] UI/UX implementation with streaming support

**Streaming Implementation Options:**
1. **Server-Sent Events (SSE)**: HTTP streaming endpoint instead of callable
2. **Chunked Response**: Return full response but with fast model (gemini-1.5-flash)
3. **Progressive Loading**: Generate sections sequentially and return as available

---

## Dependencies to Add

```bash
# LLM provider - Google Gemini
uv add google-genai  # Google Gemini SDK
# Docs: https://googleapis.github.io/python-genai/

# Analytics - PostHog for LLM tracking
uv add posthog  # PostHog SDK
# Docs: https://posthog.com/docs/llm-analytics

# Utilities
uv add python-dateutil  # Date handling (if needed)
```

**✓ Already installed**: `google-genai`, `posthog`

---

## Success Criteria

- [x] Can calculate sun sign from birth date
- [x] Can get daily transit data (already have this)
- [ ] Can summarize transits for LLM context
- [ ] Can generate technical analysis section (astronomical "why")
- [ ] Can generate personalized horoscope (technical + summary + 8 details) via LLM with memory
- [ ] Horoscope feels personal, mystical, and transformational
- [ ] Streaming response works for perceived speed
- [ ] Can track engagement with full text of categories viewed
- [ ] Can update memory collection with last 10 readings (FIFO)
- [ ] LLM can build continuity across readings using memory
- [ ] User perceives response as fast (streaming chunks arrive quickly)
- [ ] Output quality matches brand voice

---

## V2 Scope (Future)
- Full natal chart (not just sun sign)
- House-based predictions
- Aspect interpretations
- Rising sign and Moon sign integration
- More personalized based on full chart

---

## V3 Scope (Future)
- User asks questions
- Tarot card readings in response
- Multi-card spreads
- Conversational interface
- Q&A with spiritual guidance
- **Journal evolution**: `add_journal_entry()` expands to handle:
  - `entry_type: "tarot_reading"` with cards drawn
  - `entry_type: "reflection"` with user's own notes
  - `entry_type: "question"` with conversational Q&A
  - Full text storage continues for LLM continuity
- **Insights begin**: Patterns across journal entries surface automatically

---

## Questions to Resolve Before Coding

1. ~~**LLM Provider**~~: ✓ Google Gemini (via google-genai SDK)
2. **Gemini Model**: Which model? (gemini-1.5-pro for quality, gemini-1.5-flash for speed/streaming?)
3. **Word Count**: How many words per technical analysis (3-5 sentences)? Per category detail (~80-120)?
4. ~~**Horoscope Generation**~~: ✓ On-demand per user with personalization (NO caching)
5. ~~**Interest Weights**~~: ✓ Using count + last_mentioned in memory collection (server-side only)
6. ~~**Memory Storage**~~: ✓ Last 10 readings with full text of categories viewed (FIFO)
7. ~~**Streaming**~~: ✓ Use generate_content_stream for perceived speed
8. **Streaming Implementation**: Firebase callable functions vs HTTP streaming endpoint?
9. **Brand Voice**: Can you share 2-3 example horoscope paragraphs to match tone?
10. **PostHog Setup**: PostHog project API key and configuration

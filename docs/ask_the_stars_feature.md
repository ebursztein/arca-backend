# Ask the Stars - Technical Design Document

**Status:** Design Phase
**Version:** 1.0
**Last Updated:** 2025-01-20
**Author:** Backend Team

## Table of Contents

1. [Overview](#overview)
2. [Goals](#goals)
3. [Architecture Decisions](#architecture-decisions)
4. [Data Models](#data-models)
5. [Firestore Collections](#firestore-collections)
6. [API Endpoints](#api-endpoints)
7. [Background Processing](#background-processing)
8. [Entity Extraction Flow](#entity-extraction-flow)
9. [Prompt Templates](#prompt-templates)
10. [Cost Optimization](#cost-optimization)
11. [Security](#security)
12. [Implementation Phases](#implementation-phases)
13. [Example Flows](#example-flows)

---

## Overview

"Ask the Stars" is a conversational Q&A feature that allows users to ask follow-up questions about their daily horoscope. The system uses streaming LLM responses, maintains long-term entity memory, and provides personalized guidance based on accumulated context.

**Key Features:**
- Streaming responses via Server-Sent Events (SSE)
- Long-term entity tracking (relationships, career, goals, challenges, etc.)
- Conversation history tied to daily horoscopes
- 2-step entity extraction with deduplication
- Cost-optimized single-document architecture

---

## Goals

### User Experience Goals
- Enable natural conversation about horoscope insights
- Maintain context across conversations
- Personalize guidance based on user's life situations
- Provide instant, streaming responses

### Technical Goals
- Minimize Firestore read/write costs
- Maintain data consistency and queryability
- Enable analytics on conversation patterns
- Support entity deduplication and merging
- Ensure privacy and security (user-only access)

### Product Goals
- Increase daily engagement
- Surface deeper insights from horoscope data
- Build comprehensive user context over time
- Enable pattern recognition across conversations

---

## Architecture Decisions

### 1. Single-Document Collections (Cost Optimization)

**Decision:** Store all entities, all messages, and all horoscopes in single documents per user.

**Rationale:**
- **Firestore pricing:** Charged per document read/write
- **Without optimization:** 15 entities = 15 reads, 10 messages = 10 reads = $$$
- **With single-doc:** 1 read for all entities, 1 read for entire conversation = $

**Implementation:**
```python
# BAD: 15+ reads
for entity_id in entity_ids:
    entity = firestore.collection('entities').document(entity_id).get()

# GOOD: 1 read
user_entities = firestore.collection('users').document(user_id)\
    .collection('entities').document('all').get()
all_entities = user_entities.data()['entities']  # Array
```

### 2. 2-Step Entity Extraction

**Decision:** Separate entity extraction from entity merging (2 LLM calls).

**Rationale:**
- **Extraction** and **deduplication** are different cognitive tasks
- Better accuracy with specialized prompts
- Easier to debug and improve each step independently
- Both use structured JSON output for reliability

**Flow:**
```
Message Created
  ↓
[LLM Call 1] Extract raw entities from message → structured JSON
  ↓
[LLM Call 2] Merge with existing entities → structured JSON
  ↓
Store merged result
```

### 3. Streaming via SSE (Server-Sent Events)

**Decision:** Use HTTPS function with SSE, not Callable Functions.

**Rationale:**
- Firebase Callable Functions don't support streaming
- SSE is simpler than WebSockets for serverless
- Native URLSession support in iOS
- One-way communication (server → client) is sufficient

### 4. Hybrid Conversation Scope

**Decision:** Conversations tied to horoscope dates, but entities persist across all time.

**Rationale:**
- Users ask about "today's horoscope" primarily
- Entity memory provides cross-conversation continuity
- Prevents context window bloat
- Enables date-based conversation retrieval

### 5. Open Entity Types (Strings, Not Enums)

**Decision:** Entity types are open strings, not predefined enums.

**Rationale:**
- Can't predict all entity types users will mention
- System learns new entity types dynamically
- LLM can categorize flexibly
- Examples: "relationship", "career_goal", "health_concern", "financial_situation"

---

## Data Models

### Entity

Represents a tracked person, situation, goal, or concept from user conversations.

```python
class Entity(BaseModel):
    entity_id: str  # UUID
    name: str  # "John", "Job Search", "Meditation Practice"
    entity_type: str  # Open string: "relationship", "career", "goal", etc.
    status: str  # "active" | "archived" | "resolved"
    aliases: list[str] = []  # ["boyfriend", "partner"] for deduplication
    first_seen: str  # ISO timestamp
    last_seen: str  # ISO timestamp
    mention_count: int = 1
    context_snippets: list[str] = []  # Last 10 contexts, FIFO
    importance_score: float = 0.0  # Calculated: recency (0.6) + frequency (0.4)
    created_at: str
    updated_at: str
```

**Importance Score Formula:**
```python
recency = max(0.0, 1.0 - (days_since_mention / 30))
frequency = min(1.0, mention_count / 10)
importance_score = (recency * 0.6) + (frequency * 0.4)
```

### Message

Represents a single message in a conversation (user or assistant).

```python
class Message(BaseModel):
    message_id: str  # UUID
    role: str  # "user" | "assistant"
    content: str  # Message text
    timestamp: str  # ISO timestamp
```

**Note:** Entities are NOT stored in messages. They're fetched from the separate entities collection.

### Conversation

Represents a conversation session tied to a horoscope date.

```python
class Conversation(BaseModel):
    conversation_id: str  # UUID
    user_id: str
    horoscope_date: str  # ISO date (e.g., "2025-01-20")
    messages: list[Message] = []  # All messages in array
    created_at: str
    updated_at: str
```

### UserEntities

Single document containing all entities for a user.

```python
class UserEntities(BaseModel):
    user_id: str
    entities: list[Entity] = []  # All entities in single array
    updated_at: str
```

### UserHoroscopes

Single document containing all cached horoscopes for a user.

```python
class UserHoroscopes(BaseModel):
    user_id: str
    horoscopes: dict[str, DailyHoroscope] = {}  # date -> horoscope
    updated_at: str
```

**Example:**
```json
{
  "user_id": "abc123",
  "horoscopes": {
    "2025-01-20": { /* DailyHoroscope object */ },
    "2025-01-21": { /* DailyHoroscope object */ }
  },
  "updated_at": "2025-01-20T10:30:00Z"
}
```

### ExtractedEntities (LLM Output Schema)

Structured output from entity extraction LLM call.

```python
class ExtractedEntity(BaseModel):
    name: str
    entity_type: str
    context: str  # Context snippet from message
    confidence: float  # 0-1

class ExtractedEntities(BaseModel):
    entities: list[ExtractedEntity]
```

### MergedEntities (LLM Output Schema)

Structured output from entity merging LLM call.

```python
class EntityMergeAction(BaseModel):
    action: str  # "create" | "update" | "merge"
    entity_name: str
    entity_type: str
    merge_with_id: Optional[str] = None  # If merging with existing
    new_alias: Optional[str] = None  # Alias to add
    context_update: Optional[str] = None

class MergedEntities(BaseModel):
    actions: list[EntityMergeAction]
```

---

## Firestore Collections

### Collection: `users/{userId}/entities` (SINGLE DOCUMENT)

**Document ID:** `all`
**Schema:** `UserEntities`
**Purpose:** All entities for user in one document
**Security:** `request.auth.uid == userId`

**Structure:**
```
users/
  abc123/
    entities/
      all  ← Single document with entities array
```

**Sample Document:**
```json
{
  "user_id": "abc123",
  "entities": [
    {
      "entity_id": "ent_001",
      "name": "John",
      "entity_type": "relationship",
      "status": "active",
      "aliases": ["boyfriend", "partner"],
      "mention_count": 5,
      "importance_score": 0.85,
      "context_snippets": [
        "Had a fight with John last week about communication"
      ]
    },
    {
      "entity_id": "ent_002",
      "name": "Job Search",
      "entity_type": "career_goal",
      "status": "active",
      "mention_count": 3,
      "importance_score": 0.72
    }
  ],
  "updated_at": "2025-01-20T10:30:00Z"
}
```

### Collection: `users/{userId}/horoscopes` (SINGLE DOCUMENT)

**Document ID:** `all`
**Schema:** `UserHoroscopes`
**Purpose:** Cache all horoscopes for conversation retrieval
**Security:** `request.auth.uid == userId`

**Structure:**
```
users/
  abc123/
    horoscopes/
      all  ← Single document with horoscopes dict
```

### Collection: `conversations/{conversationId}` (SINGLE DOCUMENT)

**Schema:** `Conversation`
**Purpose:** Conversation metadata + all messages
**Security:** `request.auth.uid == resource.data.user_id`

**Sample Document:**
```json
{
  "conversation_id": "conv_xyz",
  "user_id": "abc123",
  "horoscope_date": "2025-01-20",
  "messages": [
    {
      "message_id": "msg_001",
      "role": "user",
      "content": "Why am I feeling tension with John today?",
      "timestamp": "2025-01-20T10:15:00Z"
    },
    {
      "message_id": "msg_002",
      "role": "assistant",
      "content": "Today's Mars square to your Venus...",
      "timestamp": "2025-01-20T10:15:03Z"
    }
  ],
  "created_at": "2025-01-20T10:15:00Z",
  "updated_at": "2025-01-20T10:15:03Z"
}
```

### Collection: `memory/{userId}` (EXISTING)

**Schema:** `MemoryCollection` (enhanced)
**Purpose:** Server-side only personalization data
**Security:** Server-side only (no client access)

**New Fields:**
```python
class MemoryCollection(BaseModel):
    # Existing fields...
    categories: dict[str, CategoryEngagement]
    recent_readings: list[ReadingSummary]

    # NEW FIELDS for Ask the Stars
    entity_summary: dict[str, int] = {}  # entity_type -> count
    last_conversation_date: Optional[str] = None
    total_conversations: int = 0
    question_categories: dict[str, int] = {}  # category -> count
```

---

## API Endpoints

### 1. `ask_the_stars` (HTTPS Function with SSE)

**URL:** `https://us-central1-{project}.cloudfunctions.net/ask_the_stars`
**Method:** POST
**Auth:** Firebase Auth Token (Bearer)
**Response:** Server-Sent Events (SSE) stream

**Request Body:**
```json
{
  "question": "Why am I feeling tension with John today?",
  "horoscope_date": "2025-01-20",
  "conversation_id": "conv_xyz"  // Optional, for continuing conversation
}
```

**Response Stream:**
```
data: {"type": "chunk", "text": "Today's Mars square"}
data: {"type": "chunk", "text": " to your Venus is highlighting"}
data: {"type": "chunk", "text": " relationship dynamics..."}
data: {"type": "done", "conversation_id": "conv_xyz", "message_id": "msg_002"}
```

**Flow:**
1. Authenticate user from Bearer token
2. Fetch horoscope from `users/{userId}/horoscopes/all` (1 read)
3. Fetch memory from `memory/{userId}` (1 read)
4. Fetch entities from `users/{userId}/entities/all` (1 read)
5. If conversation_id provided, fetch conversation (1 read)
6. Filter top 15 active entities by importance_score
7. Build prompt with horoscope + entities + memory + messages
8. Stream LLM response via SSE
9. Save user + assistant messages to conversation (1 write)
10. Return conversation_id + message_id

**Total Cost:** 4 reads + 1 write (vs 30+ reads with per-document architecture)

### 2. `get_conversation_history` (Callable Function)

**Purpose:** Retrieve conversation with all messages

**Input:**
```json
{
  "conversation_id": "conv_xyz"
}
```

**Output:**
```json
{
  "conversation": {
    "conversation_id": "conv_xyz",
    "horoscope_date": "2025-01-20",
    "messages": [ /* all messages */ ]
  }
}
```

### 3. `get_user_entities` (Callable Function)

**Purpose:** Retrieve user's entities (for UI display)

**Input:**
```json
{
  "status": "active",  // Optional filter
  "limit": 50
}
```

**Output:**
```json
{
  "entities": [ /* filtered and sorted entities */ ]
}
```

### 4. `update_entity` (Callable Function)

**Purpose:** User can archive/update entities

**Input:**
```json
{
  "entity_id": "ent_001",
  "status": "archived",  // Optional
  "aliases": ["ex-boyfriend"],  // Optional
  "context_snippet": "We broke up"  // Optional
}
```

### 5. `delete_entity` (Callable Function)

**Purpose:** User can delete incorrect entities

**Input:**
```json
{
  "entity_id": "ent_001"
}
```

---

## Background Processing

### Firestore Trigger: `extract_entities_from_message`

**Trigger:** `@firestore_fn.on_document_written(document="conversations/{conversationId}")`
**Purpose:** Extract and merge entities from new messages

**Why `on_document_written` instead of `on_document_created`?**
- Conversations are updated (messages array appended), not newly created each time
- Trigger fires when conversation document is modified

**Flow:**

```python
@firestore_fn.on_document_written(document="conversations/{conversationId}")
def extract_entities_from_message(event):
    # 1. Get conversation data
    conv_data = event.data.after.to_dict()
    user_id = conv_data['user_id']
    messages = conv_data['messages']

    # Get latest message (just added)
    latest_message = messages[-1]

    # Skip if assistant message (only process user messages for extraction)
    if latest_message['role'] == 'assistant':
        return

    # 2. Fetch existing entities (1 read)
    entities_doc = firestore.collection('users').document(user_id)\
        .collection('entities').document('all').get()
    existing_entities = UserEntities(**entities_doc.to_dict()).entities

    # 3. LLM CALL 1: Extract raw entities (structured output)
    extracted = extract_entities_llm_call(
        user_message=latest_message['content'],
        existing_entities=existing_entities
    )
    # Returns: ExtractedEntities(entities=[...])

    # 4. LLM CALL 2: Merge with existing entities (structured output)
    merged = merge_entities_llm_call(
        extracted_entities=extracted.entities,
        existing_entities=existing_entities
    )
    # Returns: MergedEntities(actions=[...])

    # 5. Execute merge actions
    updated_entities = execute_merge_actions(
        actions=merged.actions,
        existing_entities=existing_entities
    )

    # 6. Update entities document (1 write)
    firestore.collection('users').document(user_id)\
        .collection('entities').document('all')\
        .update({
            'entities': [e.model_dump() for e in updated_entities],
            'updated_at': datetime.utcnow().isoformat()
        })

    # 7. Update memory collection (1 write)
    update_memory_with_entities(user_id, updated_entities)
```

---

## Entity Extraction Flow

### Step 1: Extract Raw Entities (LLM Call 1)

**Template:** `functions/templates/conversation/extract_entities.j2`

**Prompt Structure:**
```jinja
You are extracting entities from a user's conversation about astrology.

INSTRUCTIONS:
- Extract people, relationships, situations, goals, challenges, places, events
- Assign an entity_type (open string)
- Provide context snippet
- Assign confidence (0-1)

USER MESSAGE:
{{ user_message }}

Output structured JSON matching ExtractedEntities schema.
```

**LLM Config:**
```python
config = types.GenerateContentConfig(
    temperature=0.3,  # Low temperature for consistent extraction
    response_mime_type="application/json",
    response_schema=ExtractedEntities  # Pydantic schema
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=config
)

extracted = ExtractedEntities(**response.parsed)
```

**Example Output:**
```json
{
  "entities": [
    {
      "name": "John",
      "entity_type": "relationship",
      "context": "feeling tension with John today",
      "confidence": 0.9
    },
    {
      "name": "communication issues",
      "entity_type": "challenge",
      "context": "tension might be about communication",
      "confidence": 0.7
    }
  ]
}
```

### Step 2: Merge with Existing Entities (LLM Call 2)

**Template:** `functions/templates/conversation/merge_entities.j2`

**Prompt Structure:**
```jinja
You are merging newly extracted entities with existing tracked entities.

EXISTING ENTITIES:
{{ existing_entities_json }}

NEWLY EXTRACTED ENTITIES:
{{ extracted_entities_json }}

INSTRUCTIONS:
- Check if extracted entity already exists (same person/thing, different name)
- If duplicate: merge (provide merge_with_id and new_alias)
- If new: create
- If existing: update (provide context_update)

Output structured JSON matching MergedEntities schema.
```

**Example Output:**
```json
{
  "actions": [
    {
      "action": "merge",
      "entity_name": "John",
      "entity_type": "relationship",
      "merge_with_id": "ent_001",
      "new_alias": "John",
      "context_update": "feeling tension today"
    },
    {
      "action": "create",
      "entity_name": "communication issues",
      "entity_type": "challenge",
      "context_update": "ongoing challenge in relationship"
    }
  ]
}
```

### Step 3: Execute Merge Actions

**Logic:**
```python
def execute_merge_actions(actions, existing_entities):
    entities_dict = {e.entity_id: e for e in existing_entities}

    for action in actions:
        if action.action == "create":
            new_entity = Entity(
                entity_id=str(uuid.uuid4()),
                name=action.entity_name,
                entity_type=action.entity_type,
                status="active",
                first_seen=now(),
                last_seen=now(),
                context_snippets=[action.context_update],
                importance_score=0.5
            )
            entities_dict[new_entity.entity_id] = new_entity

        elif action.action == "merge":
            existing = entities_dict[action.merge_with_id]
            if action.new_alias and action.new_alias not in existing.aliases:
                existing.aliases.append(action.new_alias)
            existing.last_seen = now()
            existing.mention_count += 1
            existing.context_snippets.append(action.context_update)
            existing.importance_score = calculate_importance_score(existing)

        elif action.action == "update":
            # Similar to merge, but no alias changes
            pass

    return list(entities_dict.values())
```

---

## Prompt Templates

### 1. `ask_the_stars.j2` (Conversation Prompt)

**Location:** `functions/templates/conversation/ask_the_stars.j2`

**Structure:**
```jinja
SYSTEM INSTRUCTIONS:
You are an empathetic astrology guide providing personalized insights.

TODAY'S HOROSCOPE CONTEXT:
Date: {{ horoscope_date }}
Sun Sign: {{ sun_sign }}

Technical Analysis:
{{ horoscope.technical_analysis }}

Key Transits:
{% for transit in horoscope.transit_summary.priority_transits %}
- {{ transit.interpretation }}
{% endfor %}

Astrometers:
Overall Energy: {{ horoscope.astrometers.overall_state }}
Top Active: {{ horoscope.astrometers.top_active_meters }}

USER'S ACTIVE ENTITIES (Top 15 by Importance):
{% for entity in entities %}
- {{ entity.name }} ({{ entity.entity_type }}): {{ entity.context_snippets[-1] if entity.context_snippets else 'mentioned recently' }}
{% endfor %}

CONVERSATION HISTORY:
{% for msg in messages %}
{{ msg.role.upper() }}: {{ msg.content }}
{% endfor %}

USER QUESTION: {{ question }}

RESPONSE GUIDELINES:
- Reference specific transits and astrometer insights
- Connect to user's tracked entities when relevant
- Be empathetic, actionable, and direct
- 2-3 paragraphs maximum
- No astrology jargon
```

### 2. `extract_entities.j2` (Entity Extraction)

**Location:** `functions/templates/conversation/extract_entities.j2`

**Structure:**
```jinja
Extract entities from the user's message.

ENTITY TYPES (examples, not exhaustive):
- relationship, person, family_member
- career_goal, career_situation, job
- challenge, emotional_pattern, habit
- place, event, decision
- spiritual_practice, health_concern

USER MESSAGE:
{{ user_message }}

Extract all people, situations, goals, challenges mentioned.
Output JSON with entity name, type, context, confidence.
```

### 3. `merge_entities.j2` (Entity Merging)

**Location:** `functions/templates/conversation/merge_entities.j2`

**Structure:**
```jinja
Merge newly extracted entities with existing tracked entities.

EXISTING ENTITIES:
{{ existing_entities_json }}

NEWLY EXTRACTED:
{{ extracted_entities_json }}

RULES:
1. Check for duplicates (same person/thing, different name)
2. If "John" and user already tracks "boyfriend", merge if same person
3. If truly new, create
4. If existing but new context, update

Output JSON with merge actions (create/merge/update).
```

---

## Cost Optimization

### Single-Document Collections

**Before (Per-Document):**
```
Load 15 entities: 15 reads
Load 10 messages: 10 reads
Update 1 entity: 1 write
Add 1 message: 1 write
TOTAL: 25 reads + 2 writes
```

**After (Single-Document):**
```
Load all entities: 1 read
Load conversation: 1 read
Update entities doc: 1 write
Update conversation doc: 1 write
TOTAL: 2 reads + 2 writes
```

**Savings:** 92% reduction in reads

### Limits and Constraints

**Firestore Document Size Limit:** 1 MB

**Estimated Sizes:**
- 1 Entity: ~500 bytes
- 2,000 entities = 1 MB (limit)
- 1 Message: ~200 bytes
- 5,000 messages = 1 MB (limit)
- 1 DailyHoroscope: ~10 KB
- 100 horoscopes = 1 MB (limit)

**Mitigation:**
- Archive old entities (reduce active count)
- Prune old conversations (keep last 30 days)
- Paginate horoscopes (split by month if needed)

### Query Optimization

**Bad: Query subcollection**
```python
# 100+ reads if 100 messages
messages = db.collection('conversations/{id}/messages').get()
```

**Good: Single document with array**
```python
# 1 read for all messages
conv = db.collection('conversations').document(id).get()
messages = conv.data()['messages']
```

---

## Security

### Firestore Security Rules

**File:** `firestore.rules`

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // User entities - highly sensitive
    match /users/{userId}/entities/{document} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // User horoscopes - user-only access
    match /users/{userId}/horoscopes/{document} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Conversations - user can only access their own
    match /conversations/{conversationId} {
      allow read: if request.auth != null &&
        request.auth.uid == resource.data.user_id;
      allow create: if request.auth != null &&
        request.auth.uid == request.resource.data.user_id;
      allow update: if request.auth != null &&
        request.auth.uid == resource.data.user_id;
      allow delete: if false;  // No deletion via client
    }

    // Memory - server-side ONLY
    match /memory/{userId} {
      allow read, write: if false;  // No client access ever
    }
  }
}
```

### Privacy Considerations

**Sensitive Data:**
- Entity tracking creates detailed psychological profiles
- Relationship details, career situations, health concerns
- Long-term behavioral patterns

**Requirements:**
1. Update Privacy Policy to cover "Long Term Memory"
2. Update Terms of Service for entity tracking
3. Provide user controls:
   - View all tracked entities
   - Delete specific entities
   - Archive/bulk delete
   - Export conversation data

---

## Implementation Phases

### Phase 1: Data Models & Collections (Days 1-2)
- [ ] Create Pydantic models in `functions/models.py`
- [ ] Update Firestore security rules
- [ ] Create collection initialization helpers
- [ ] Write model validation tests

### Phase 2: Entity Extraction (Days 3-4)
- [ ] Create `extract_entities.j2` template
- [ ] Create `merge_entities.j2` template
- [ ] Implement extraction LLM calls with structured output
- [ ] Implement merge logic
- [ ] Create Firestore trigger
- [ ] Test deduplication with sample data

### Phase 3: Conversation API (Days 5-7)
- [ ] Implement `ask_the_stars` HTTPS function with SSE
- [ ] Create `ask_the_stars.j2` conversation prompt
- [ ] Implement streaming response handler
- [ ] Test with real horoscope + entity context
- [ ] Add error handling and timeouts

### Phase 4: Helper Functions (Day 8)
- [ ] Implement `get_conversation_history`
- [ ] Implement `get_user_entities`
- [ ] Implement `update_entity`
- [ ] Implement `delete_entity`
- [ ] Register all functions in `functions/main.py`

### Phase 5: Horoscope Storage (Day 9)
- [ ] Update `get_daily_horoscope` to store in UserHoroscopes
- [ ] Add horoscope retrieval helper
- [ ] Test horoscope caching and retrieval

### Phase 6: Testing (Day 10)
- [ ] Unit tests for entity extraction
- [ ] Unit tests for entity merging
- [ ] Integration test: full conversation flow
- [ ] Load test: concurrent conversations
- [ ] Security test: cross-user access prevention

### Phase 7: Documentation (Day 11)
- [ ] Write `docs/ASK_THE_STARS_API.md` for iOS
- [ ] Document SSE streaming in Swift
- [ ] Document entity management UI patterns
- [ ] Add code examples

### Phase 8: Deployment (Day 12)
- [ ] Deploy functions to staging
- [ ] Test with staging Firebase project
- [ ] Deploy to production
- [ ] Monitor PostHog analytics

---

## Example Flows

### Flow 1: First Conversation

**User:** "Why am I feeling tension with my partner today?"

**Backend Process:**
1. **Fetch horoscope** (users/abc123/horoscopes/all) → 1 read
2. **Fetch entities** (users/abc123/entities/all) → 1 read
   Result: Empty (first conversation)
3. **Fetch memory** (memory/abc123) → 1 read
4. **Create conversation** with empty entity context
5. **Stream LLM response** via SSE
6. **Save messages** to new conversation doc → 1 write
7. **Background trigger fires**:
   - Extract entities: "partner" (relationship)
   - No existing entities, create new
   - Update entities doc → 1 write
   - Update memory → 1 write

**Total Cost:** 3 reads + 3 writes

### Flow 2: Follow-Up Conversation (Same Day)

**User:** "Should I talk to him about this today or wait?"

**Backend Process:**
1. **Fetch horoscope** (cached from morning) → 1 read
2. **Fetch entities** (now has "partner") → 1 read
3. **Fetch conversation** (existing) → 1 read
4. **Build prompt** with:
   - Today's transits
   - Entity: "partner" (relationship)
   - Previous message context
5. **Stream response** referencing Venus transit + Mercury aspect
6. **Append messages** to conversation doc → 1 write
7. **Background trigger**:
   - Extract entities: "talk to him" (decision)
   - Merge: Update "partner" context
   - Update entities doc → 1 write

**Total Cost:** 3 reads + 2 writes

### Flow 3: New Day, Recurring Entity

**User:** "Things are better with my partner today!"

**Backend Process:**
1. **Fetch today's horoscope** → 1 read
2. **Fetch entities** (has "partner" from yesterday) → 1 read
3. **No existing conversation** (new day)
4. **Build prompt** with:
   - New day's transits
   - Entity: "partner" (last seen: yesterday, context: "tension")
   - No previous messages
5. **Stream response** noting improvement
6. **Create new conversation** for today → 1 write
7. **Background trigger**:
   - Extract: "things are better" (update)
   - Merge: Update "partner" status and context
   - Increment mention_count, update importance_score
   - Update entities doc → 1 write

**Total Cost:** 2 reads + 2 writes

---

## Success Metrics

### Technical Metrics
- Average reads per conversation < 5
- Average writes per conversation < 3
- Entity deduplication accuracy > 80%
- Streaming latency < 3s to first chunk
- Zero cross-user entity access (security)

### Product Metrics
- Daily active users using "Ask the Stars"
- Average questions per user per day
- Conversation continuation rate (multi-turn)
- Entity growth rate (new entities/day)
- User satisfaction with responses

### Cost Metrics
- Firestore cost per 1,000 conversations
- LLM cost per conversation (2 calls: answer + extraction)
- Storage cost for conversations + entities

---

## Future Enhancements

### V2 Features
- **Vector embeddings for entity retrieval:** Semantic search for relevant entities
- **Multi-day conversation threads:** "Remember what we discussed last week?"
- **Entity relationships:** Track connections between entities
- **Proactive insights:** "You mentioned job stress 3x this week..."

### V3 Features
- **Voice input/output:** Speech-to-text questions, text-to-speech responses
- **Entity timeline visualization:** See how entities evolve over time
- **Pattern detection:** "Your partner stress peaks on full moons"

---

## Appendix

### Firestore Collection Structure Summary

```
users/
  {userId}/
    entities/
      all  ← UserEntities (single doc)
    horoscopes/
      all  ← UserHoroscopes (single doc)

conversations/
  {conversationId}  ← Conversation (single doc with messages array)

memory/
  {userId}  ← MemoryCollection (enhanced with entity summary)
```

### Key File Locations

**Models:**
- `functions/models.py` - All Pydantic models

**Templates:**
- `functions/templates/conversation/ask_the_stars.j2` - Conversation prompt
- `functions/templates/conversation/extract_entities.j2` - Entity extraction
- `functions/templates/conversation/merge_entities.j2` - Entity merging

**Functions:**
- `functions/ask_the_stars.py` - Main conversation handler
- `functions/entity_extraction.py` - Background entity processing
- `functions/main.py` - Function registration

**Documentation:**
- `docs/ask_the_stars_feature.md` - This document
- `docs/ASK_THE_STARS_API.md` - iOS integration guide (TBD)

**Tests:**
- `functions/test_ask_the_stars.py` - Unit tests
- `functions/test_entity_extraction.py` - Entity extraction tests

---

**End of Design Document**

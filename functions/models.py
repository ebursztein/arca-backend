"""
Pydantic models for Arca Backend V1

All data structures used throughout the application for type safety and validation.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Any
from enum import Enum

# Import new 17-meter hierarchy system
from astrometers.hierarchy import MeterGroupV2

if TYPE_CHECKING:
    from astrometers.meters import MeterReading


# =============================================================================
# Enums
# =============================================================================

class EntityStatus(str, Enum):
    """Entity tracking status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    RESOLVED = "resolved"


class EntityCategory(str, Enum):
    """Entity category for relationship tracking."""
    PARTNER = "partner"  # Current committed relationship (only one allowed)
    FAMILY = "family"  # Mother, father, sister, brother, etc.
    FRIEND = "friend"  # Friends
    COWORKER = "coworker"  # Boss, colleague, etc.
    OTHER = "other"  # Catch-all for non-relationship entities (goals, challenges, etc.)


class MessageRole(str, Enum):
    """Conversation message role."""
    USER = "user"
    ASSISTANT = "assistant"


# =============================================================================
# User Profile Models
# =============================================================================

class UserProfile(BaseModel):
    """
    User profile stored in Firestore: users/{userId}

    Contains birth information, natal chart data, and preferences.
    """
    user_id: str = Field(description="Firebase Auth user ID")
    name: str = Field(description="User's name from auth provider")
    email: str = Field(description="User's email from auth provider")

    # subscription
    is_premium: bool = Field(False, description="True if user has premium subscription")
    premium_expiry: Optional[str] = Field(None,
        description="ISO date of premium subscription expiry (None if non-premium)")

    # Birth information
    birth_date: str = Field(description="Birth date in YYYY-MM-DD format")
    birth_time: Optional[str] = Field(None, description="Birth time in HH:MM format (optional, V2+)")
    birth_timezone: Optional[str] = Field(None, description="IANA timezone (optional, V2+)")
    birth_lat: Optional[float] = Field(None, ge=-90, le=90, description="Birth latitude (optional)")
    birth_lon: Optional[float] = Field(None, ge=-180, le=180, description="Birth longitude (optional)")

    # Computed data
    sun_sign: str = Field(description="Sun sign (e.g., 'taurus')")
    natal_chart: dict = Field(description="Complete NatalChartData from get_astro_chart()")
    exact_chart: bool = Field(description="True if birth_time + timezone provided")

    # Timestamps
    created_at: str = Field(description="ISO datetime of profile creation")
    last_active: str = Field(description="ISO datetime of last activity")


# =============================================================================
# Memory Collection Models
# =============================================================================

class CategoryEngagement(BaseModel):
    """
    Engagement tracking for a single category.
    """
    count: int = Field(default=0, ge=0, description="Total times viewed")
    last_mentioned: Optional[str] = Field(default=None, description="ISO date of last view")


class RelationshipMention(BaseModel):
    """Tracks when a relationship entity was featured in horoscope."""
    entity_id: str = Field(description="ID of the entity")
    entity_name: str = Field(description="Name of the entity")
    category: EntityCategory = Field(description="Category: partner, family, friend, coworker")
    date: str = Field(description="ISO date when featured")
    context: str = Field(description="What was said about this relationship")


class MemoryCollection(BaseModel):
    """
    Memory collection stored in Firestore: memory/{userId}

    Server-side only - NOT accessible to client.
    Used for personalization in Ask the Stars conversations.
    """
    user_id: str = Field(description="Firebase Auth user ID")

    # Category engagement tracking (using MeterGroupV2 hierarchy)
    categories: dict[MeterGroupV2, CategoryEngagement] = Field(
        description="Engagement counts per meter group"
    )

    # Ask the Stars - Conversation tracking
    entity_summary: dict[str, int] = Field(
        default_factory=dict,
        description="Entity type counts (e.g., {'relationship': 5, 'career_goal': 3})"
    )
    last_conversation_date: Optional[str] = Field(
        None,
        description="ISO date of last conversation"
    )
    total_conversations: int = Field(
        default=0,
        ge=0,
        description="Total number of Ask the Stars conversations"
    )
    question_categories: dict[str, int] = Field(
        default_factory=dict,
        description="Question category counts for analytics"
    )

    # Horoscope relationship rotation (capped at 20)
    relationship_mentions: list[RelationshipMention] = Field(
        default_factory=list,
        description="Last 20 relationship mentions in horoscopes for rotation tracking"
    )

    # Timestamp
    updated_at: str = Field(description="ISO datetime of last update")

    def format_for_llm(self) -> str:
        """
        Format memory data for LLM prompt context.

        Returns:
            Formatted string for LLM personalization
        """
        lines = []

        # Category engagement
        lines.append("Category Interests:")

        # Sort by count (most viewed first)
        sorted_cats = sorted(
            self.categories.items(),
            key=lambda x: x[1].count,
            reverse=True
        )

        has_engagement = False
        for cat_name, cat_data in sorted_cats:
            if cat_data.count > 0:
                has_engagement = True
                last = cat_data.last_mentioned or "never"
                lines.append(
                    f"  - {cat_name.value.replace('_', ' ').title()}: "
                    f"viewed {cat_data.count} times, last on {last}"
                )

        if not has_engagement:
            lines.append("  (First time user - no history yet)")

        return "\n".join(lines)


# =============================================================================
# Ask the Stars - Entity Tracking Models
# =============================================================================

class AttributeKV(BaseModel):
    """Key-value pair for entity attributes (Gemini API compatible)."""
    key: str = Field(description="Attribute key")
    value: str = Field(description="Attribute value")


class Entity(BaseModel):
    """
    Tracked entity from user conversations (person, relationship, goal, challenge, etc.).

    Stored in: users/{userId}/entities/all (single doc with entities array)
    """
    entity_id: str = Field(description="UUID for this entity")
    name: str = Field(description="Entity name (e.g., 'John', 'Job Search', 'Meditation Practice')")
    entity_type: str = Field(description="Open string: 'relationship', 'career_goal', 'challenge', etc.")
    status: EntityStatus = Field(default=EntityStatus.ACTIVE, description="Entity status")
    aliases: list[str] = Field(default_factory=list, description="Alternative names for deduplication")

    # Category for relationship tracking (iOS dropdown)
    category: Optional[EntityCategory] = Field(
        None,
        description="Entity category: partner, family, friend, coworker, other"
    )
    relationship_label: Optional[str] = Field(
        None,
        description="Specific relationship label from iOS dropdown: mother, sister, boss, etc."
    )

    # User notes (editable by user in iOS)
    notes: Optional[str] = Field(
        None,
        description="User-written notes about this entity"
    )

    # Rich metadata (flexible key-value pairs)
    attributes: list[AttributeKV] = Field(
        default_factory=list,
        description="Entity attributes: birthday_season, works_at, role, relationship_to_user, etc."
    )

    # Relationships between entities
    related_entities: list[str] = Field(
        default_factory=list,
        description="Entity IDs this entity is related to (e.g., 'Bob' → ['ent_005'] where ent_005 is TechCorp)"
    )

    # Tracking
    first_seen: str = Field(description="ISO timestamp of first mention")
    last_seen: str = Field(description="ISO timestamp of last mention")
    mention_count: int = Field(default=1, ge=1, description="Number of times mentioned")

    # Context (FIFO queue, max 10)
    context_snippets: list[str] = Field(
        default_factory=list,
        description="Last 10 context snippets where entity was mentioned"
    )

    # Importance scoring (for filtering top N entities)
    importance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Calculated: recency (0.6) + frequency (0.4)"
    )

    # Connection link (for compatibility feature)
    connection_id: Optional[str] = Field(
        None,
        description="Links to Connection with birth data for compatibility"
    )

    # Timestamps
    created_at: str = Field(description="ISO timestamp of creation")
    updated_at: str = Field(description="ISO timestamp of last update")


class Message(BaseModel):
    """
    Single message in a conversation (user or assistant).

    Stored in Conversation.messages array.
    """
    message_id: str = Field(description="UUID for this message")
    role: MessageRole = Field(description="Message role")
    content: str = Field(description="Message text content")
    timestamp: str = Field(description="ISO timestamp")


class Conversation(BaseModel):
    """
    Conversation session tied to a horoscope date.

    Stored in: conversations/{conversationId}
    All messages stored in single document (messages array).
    """
    conversation_id: str = Field(description="UUID for this conversation")
    user_id: str = Field(description="Firebase Auth user ID")
    horoscope_date: str = Field(description="ISO date (e.g., '2025-01-20')")

    # All messages in single array (cost optimization)
    messages: list[Message] = Field(default_factory=list, description="All messages in conversation")

    # Timestamps
    created_at: str = Field(description="ISO timestamp of creation")
    updated_at: str = Field(description="ISO timestamp of last update")


class UserEntities(BaseModel):
    """
    Single document containing all entities for a user (cost optimization).

    Stored in: users/{userId}/entities/all
    """
    user_id: str = Field(description="Firebase Auth user ID")
    entities: list[Entity] = Field(default_factory=list, description="All entities in single array")
    updated_at: str = Field(description="ISO timestamp of last update")


# =============================================================================
# Ask the Stars - LLM Structured Output Models
# =============================================================================

class ExtractedEntity(BaseModel):
    """
    Single entity extracted from user message (LLM output).
    """
    name: str = Field(description="Entity name")
    entity_type: str = Field(description="Entity type (open string)")
    context: str = Field(description="Context snippet from message")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")

    # Rich metadata
    attributes: list[AttributeKV] = Field(
        default_factory=list,
        description="Extracted attributes (e.g., birthday_season, role, works_at)"
    )
    related_to: Optional[str] = Field(
        None,
        description="Name of related entity mentioned in same context (e.g., 'Bob' related_to 'TechCorp')"
    )


class ExtractedEntities(BaseModel):
    """
    Structured output from entity extraction LLM call.
    """
    entities: list[ExtractedEntity] = Field(description="Extracted entities")


class EntityMergeAction(BaseModel):
    """
    Single merge action from entity merging LLM call.
    """
    action: str = Field(description="Action type: 'create', 'update', 'merge', 'link'")
    entity_name: str = Field(description="Entity name")
    entity_type: str = Field(description="Entity type")
    merge_with_id: Optional[str] = Field(None, description="Entity ID to merge with (if action='merge')")
    new_alias: Optional[str] = Field(None, description="Alias to add (if action='merge')")
    context_update: Optional[str] = Field(None, description="Context snippet to add")

    # Rich metadata updates
    attribute_updates: list[AttributeKV] = Field(
        default_factory=list,
        description="Attributes to add/update (e.g., [{'key': 'birthday_season', 'value': 'January'}])"
    )
    link_to_entity_id: Optional[str] = Field(
        None,
        description="Entity ID to link/relate to (if action='link' or creating relationship)"
    )


class MergedEntities(BaseModel):
    """
    Structured output from entity merging LLM call.
    """
    actions: list[EntityMergeAction] = Field(description="List of merge actions to execute")


# =============================================================================
# Horoscope Models
# =============================================================================

class ActionableAdvice(BaseModel):
    """
    Structured actionable guidance with do/don't/reflect format.
    """
    do: str = Field(description="Specific action aligned with transit energy")
    dont: str = Field(description="Specific thing to avoid (shadow/pitfall)")
    reflect_on: str = Field(description="Powerful journaling question for self-awareness")


# =============================================================================
# METER GROUPS MODELS (5-Group Simplified Structure)
# =============================================================================

class MeterGroupScores(BaseModel):
    """
    Aggregated scores for a meter group (arithmetic mean of member meters).
    """
    unified_score: float = Field(description="Primary display value (-100 to +100), average of member meters")
    harmony: float = Field(description="Supportive vs challenging quality (0-100)")
    intensity: float = Field(description="Activity level (0-100)")


class MeterGroupState(BaseModel):
    """
    Quality assessment for a meter group based on harmony and intensity.
    """
    label: str = Field(description="Human-readable state: Excellent, Supportive, Challenging, etc.")
    quality: str = Field(description="Enum value: excellent, supportive, harmonious, peaceful, mixed, quiet, challenging, intense")


class TrendMetric(BaseModel):
    """
    Trend data for a single metric comparing today vs yesterday.
    """
    previous: float = Field(description="Yesterday's value")
    delta: float = Field(description="Change amount (can be negative)")
    direction: str = Field(description="improving, worsening, stable, increasing, or decreasing")
    change_rate: str = Field(description="rapid, moderate, or slow")


class MeterGroupTrend(BaseModel):
    """
    Trend data for a meter group (aggregated from member meters).
    Optional - only present if yesterday data available.
    """
    unified_score: TrendMetric
    harmony: TrendMetric
    intensity: TrendMetric


class MeterGroupData(BaseModel):
    """
    Complete data for a single meter group.

    Combines:
    - Aggregated scores (from member meters)
    - State/quality label (from JSON labels)
    - LLM-generated interpretation (2-3 sentences)
    - Trend data (if available)
    - Member meter IDs (for drill-down)
    """
    group_name: str = Field(description="Group ID: mind, heart, body, instincts, growth")
    display_name: str = Field(description="Display name: Mind, Heart, Body, Instincts, Growth")
    scores: MeterGroupScores
    state: MeterGroupState
    interpretation: str = Field(description="LLM-generated 2-3 sentence interpretation (150-300 chars)")
    trend: Optional[MeterGroupTrend] = Field(None, description="Trend data if yesterday available")
    meter_ids: list[str] = Field(description="IDs of meters in this group")


class DailyHoroscope(BaseModel):
    """
    Daily horoscope - Prompt 1 fields shown immediately (<2s).

    Provides core transit analysis and immediate actionable guidance.
    Based on astrometers quantitative analysis (28 meters: 23 individual + 5 super-group aggregates).
    """
    date: str = Field(description="ISO date of horoscope")
    sun_sign: str = Field(description="Sun sign (e.g., 'taurus')")

    # Ordered for optimal user experience
    technical_analysis: str = Field(description="Astronomical explanation (3-5 sentences)")
    daily_theme_headline: str = Field(
        description="Shareable wisdom sentence (max 15 words, actionable)"
    )
    daily_overview: str = Field(
        description="Opening overview combining emotional tone, key transits explanation, and sun sign connection (3-4 sentences, 60-80 words)"
    )
    actionable_advice: ActionableAdvice = Field(
        description="Structured DO/DON'T/REFLECT guidance"
    )

    # Astrometers data (iOS-optimized with full explainability)
    astrometers: "AstrometersForIOS" = Field(
        description="Complete astrometers: 17 meters nested in 5 groups with LLM interpretations, astrological foundations, and top aspects"
    )

    # Transit Summary (enhanced natal-transit analysis)
    transit_summary: Optional[dict] = Field(
        None,
        description="Enhanced transit summary with priority transits, critical degrees, retrograde data, and theme synthesis from format_transit_summary_for_ui()"
    )

    # Moon Transit Detail (emotional climate & timing)
    moon_detail: Optional[Any] = Field(
        None,
        description="Comprehensive moon transit detail: aspects to natal, void-of-course, dispositor, next events (MoonTransitDetail object from moon.py)"
    )

    # Look Ahead (merged from detailed horoscope)
    look_ahead_preview: Optional[str] = Field(
        None,
        description="Upcoming significant transits (2-3 sentences)"
    )

    # Phase 1 Extensions (leveraging existing astrometer data)
    energy_rhythm: Optional[str] = Field(
        None,
        description="Energy pattern throughout day based on intensity curve and Moon movement (1-2 sentences)"
    )
    relationship_weather: Optional[str] = Field(
        None,
        description="Interpersonal dynamics (romantic, platonic, professional) from relationship meters (2-3 sentences)"
    )
    collective_energy: Optional[str] = Field(
        None,
        description="What everyone is feeling from outer planet context (1-2 sentences)"
    )

    # Engagement
    follow_up_questions: Optional[list[str]] = Field(
        None,
        description="5 thought-provoking questions to help user reflect on their horoscope"
    )

    # Metadata
    model_used: Optional[str] = Field(None, description="LLM model used")
    generation_time_ms: Optional[int] = Field(None, description="Generation time in milliseconds")
    usage: dict = Field(default_factory=dict, description="Raw usage metadata from LLM API")


# =============================================================================
# Compressed Horoscope Storage Models
# =============================================================================

class CompressedMeter(BaseModel):
    """Compressed meter data for storage (just name + scores)."""
    name: str = Field(description="Meter name")
    intensity: float = Field(ge=0, le=100, description="Intensity score 0-100")
    harmony: float = Field(ge=0, le=100, description="Harmony score 0-100")


class CompressedMeterGroup(BaseModel):
    """Compressed meter group data for storage."""
    name: str = Field(description="Group name: mind, heart, body, instincts, growth")
    intensity: float = Field(ge=0, le=100, description="Group intensity 0-100")
    harmony: float = Field(ge=0, le=100, description="Group harmony 0-100")
    meters: list[CompressedMeter] = Field(description="Member meters with scores only")


class CompressedTransit(BaseModel):
    """Compressed transit for Ask the Stars context."""
    interpretation: str = Field(description="Human-readable transit interpretation")


class CompressedTransitSummary(BaseModel):
    """Compressed transit summary for Ask the Stars context."""
    priority_transits: list[CompressedTransit] = Field(
        default_factory=list,
        description="Top priority transits with interpretations"
    )


class CompressedAstrometers(BaseModel):
    """Compressed astrometers summary for Ask the Stars context."""
    overall_state: str = Field(description="Overall state label (e.g., 'Quiet Reflection')")
    top_active_meters: list[str] = Field(description="Top 3-5 most active meters")
    top_flowing_meters: list[str] = Field(description="Top 3-5 meters with high harmony")
    top_challenging_meters: list[str] = Field(description="Top 3-5 meters needing attention")


class CompressedHoroscope(BaseModel):
    """
    Compressed horoscope for storage - only LLM-generated fields + meter scores.

    Reduces storage from ~128KB to ~5KB by removing all astrological foundations,
    aspects, trends, and verbose explainability data.

    Stored in: users/{user_id}/horoscopes/latest (FIFO, max 10)
    """
    date: str = Field(description="ISO date")
    sun_sign: str = Field(description="Sun sign")

    # LLM-generated fields (what user actually reads)
    technical_analysis: str
    daily_theme_headline: str
    daily_overview: str
    actionable_advice: ActionableAdvice
    look_ahead_preview: Optional[str] = None
    energy_rhythm: Optional[str] = None
    relationship_weather: Optional[str] = None
    collective_energy: Optional[str] = None
    follow_up_questions: Optional[list[str]] = None

    # Compressed meters (scores only, no foundations/aspects/trends)
    meter_groups: list[CompressedMeterGroup] = Field(
        description="5 groups with scores and member meters"
    )

    # Compressed astrometers summary (for Ask the Stars template)
    astrometers: CompressedAstrometers = Field(
        description="Summary of astrometers: overall state and top meters"
    )

    # Compressed transit summary (for Ask the Stars template)
    transit_summary: CompressedTransitSummary = Field(
        description="Top priority transits with interpretations"
    )

    # Metadata
    created_at: str = Field(description="ISO datetime of generation")


class UserHoroscopes(BaseModel):
    """
    User horoscopes collection - FIFO queue of last 10 horoscopes.

    Stored in: users/{user_id}/horoscopes/latest
    """
    user_id: str = Field(description="Firebase Auth user ID")
    horoscopes: dict[str, dict] = Field(
        description="Date-keyed horoscopes (max 10, FIFO)"
    )
    updated_at: str = Field(description="ISO datetime of last update")


# =============================================================================
# Helper Functions
# =============================================================================

def create_empty_memory(user_id: str) -> MemoryCollection:
    """
    Create an empty memory collection for a new user.

    Uses new 17-meter / 5-category hierarchy system (MeterGroupV2).

    Args:
        user_id: Firebase Auth user ID

    Returns:
        Initialized MemoryCollection
    """
    return MemoryCollection(
        user_id=user_id,
        categories={
            MeterGroupV2.MIND: CategoryEngagement(),
            MeterGroupV2.HEART: CategoryEngagement(),
            MeterGroupV2.BODY: CategoryEngagement(),
            MeterGroupV2.INSTINCTS: CategoryEngagement(),
            MeterGroupV2.GROWTH: CategoryEngagement(),
        },
        updated_at=datetime.now().isoformat()
    )


def compress_horoscope(horoscope: DailyHoroscope) -> CompressedHoroscope:
    """
    Compress a DailyHoroscope for storage.

    Reduces size from ~128KB to ~5KB by keeping only:
    - LLM-generated text fields (what user reads)
    - Meter scores (intensity + harmony only, no foundations/aspects/trends)
    - Astrometers summary (overall_state, top meters)
    - Transit summary (priority transits with interpretations)

    Args:
        horoscope: Full DailyHoroscope with complete astrometers

    Returns:
        CompressedHoroscope for storage
    """
    # Compress meter groups
    compressed_groups = []
    for group in horoscope.astrometers.groups:
        # Compress member meters
        compressed_meters = [
            CompressedMeter(
                name=meter.meter_name,
                intensity=meter.intensity,
                harmony=meter.harmony
            )
            for meter in group.meters
        ]

        compressed_groups.append(
            CompressedMeterGroup(
                name=group.group_name,
                intensity=group.intensity,
                harmony=group.harmony,
                meters=compressed_meters
            )
        )

    # Compress astrometers summary (for Ask the Stars template)
    compressed_astrometers = CompressedAstrometers(
        overall_state=horoscope.astrometers.overall_state,
        top_active_meters=horoscope.astrometers.top_active_meters,
        top_flowing_meters=horoscope.astrometers.top_flowing_meters,
        top_challenging_meters=horoscope.astrometers.top_challenging_meters
    )

    # Compress transit summary (for Ask the Stars template)
    compressed_transits = []
    if horoscope.transit_summary and horoscope.transit_summary.get("priority_transits"):
        for transit in horoscope.transit_summary["priority_transits"][:5]:
            # Build human-readable interpretation from transit data
            description = transit.get("description", "").lstrip("⚡ ")  # Remove intensity indicators
            meaning = transit.get("meaning", "")
            house_context = transit.get("house_context", "")

            # Compose interpretation
            parts = [description]
            if meaning:
                parts.append(f"({meaning})")
            if house_context:
                parts.append(f"- {house_context}")

            interpretation = " ".join(parts)
            compressed_transits.append(CompressedTransit(interpretation=interpretation))

    compressed_transit_summary = CompressedTransitSummary(
        priority_transits=compressed_transits
    )

    return CompressedHoroscope(
        date=horoscope.date,
        sun_sign=horoscope.sun_sign,
        technical_analysis=horoscope.technical_analysis,
        daily_theme_headline=horoscope.daily_theme_headline,
        daily_overview=horoscope.daily_overview,
        actionable_advice=horoscope.actionable_advice,
        look_ahead_preview=horoscope.look_ahead_preview,
        energy_rhythm=horoscope.energy_rhythm,
        relationship_weather=horoscope.relationship_weather,
        collective_energy=horoscope.collective_energy,
        follow_up_questions=horoscope.follow_up_questions,
        meter_groups=compressed_groups,
        astrometers=compressed_astrometers,
        transit_summary=compressed_transit_summary,
        created_at=datetime.now().isoformat()
    )


def calculate_entity_importance_score(
    entity: Entity,
    current_time: Optional[datetime] = None
) -> float:
    """
    Calculate importance score for entity filtering.

    Formula: importance = (recency * 0.6) + (frequency * 0.4)
    - Recency: 1.0 if seen today, decays over 30 days
    - Frequency: min(1.0, mention_count / 10)

    Args:
        entity: Entity to score
        current_time: Current time (defaults to now)

    Returns:
        Importance score (0.0 to 1.0)
    """
    if current_time is None:
        current_time = datetime.now()

    # Parse last_seen timestamp
    last_seen_dt = datetime.fromisoformat(entity.last_seen.replace('Z', '+00:00'))

    # Calculate recency (decays over 30 days)
    days_since_mention = (current_time - last_seen_dt).days
    recency = max(0.0, 1.0 - (days_since_mention / 30.0))

    # Calculate frequency (caps at 10 mentions)
    frequency = min(1.0, entity.mention_count / 10.0)

    # Weighted combination
    importance_score = (recency * 0.6) + (frequency * 0.4)

    return importance_score


# =============================================================================
# iOS-Optimized Astrometer Models (Clean, Explainable, Minimal)
# =============================================================================

class MeterAspect(BaseModel):
    """
    Single transit aspect contributing to this meter's score.

    Provides complete explainability: what aspect is active, how strong it is,
    when it will be exact, and how it contributes to the meter's score.
    """
    # Basic aspect info
    label: str = Field(description="Human-readable: 'Transit Saturn square Natal Sun'")
    natal_planet: str = Field(description="Natal planet name (e.g., 'sun', 'mars')")
    transit_planet: str = Field(description="Transit planet name")
    aspect_type: str = Field(description="Aspect type: conjunction, opposition, trine, square, sextile, quincunx")

    # Strength indicators (critical for understanding impact)
    orb: float = Field(description="Exact orb in degrees (e.g., 2.5°)")
    orb_percentage: float = Field(ge=0, le=100, description="% of max orb - tighter = stronger (e.g., 31.25% if 2.5° out of 8° max)")
    phase: str = Field(description="applying, exact, or separating")
    days_to_exact: Optional[float] = Field(None, description="Days until exact (negative = past exact)")

    # Scoring breakdown
    contribution: float = Field(description="DTI contribution (W_i × P_i)")
    quality_factor: float = Field(ge=-1, le=1, description="-1 (very challenging) to +1 (very harmonious)")

    # Context (explains WHY this aspect matters for THIS meter)
    natal_planet_house: int = Field(ge=1, le=12, description="House containing natal planet")
    natal_planet_sign: str = Field(description="Sign of natal planet (for dignity assessment)")
    houses_involved: list[int] = Field(description="Houses involved in this transit")
    natal_aspect_echo: Optional[str] = Field(None, description="If echoes natal aspect: 'Echoes natal Mars-Saturn square'")


class AstrologicalFoundation(BaseModel):
    """
    Explains what astrological factors drive this meter.

    This is the 'why' behind the meter - what planets and houses are monitored,
    and what each planet represents for this life area.
    """
    # What we're tracking
    natal_planets_tracked: list[str] = Field(description="Natal planets monitored (e.g., ['sun', 'mars'])")
    transit_planets_tracked: list[str] = Field(description="Transit planets that affect this (e.g., ['sun', 'mars', 'saturn', 'jupiter'])")
    key_houses: dict[str, str] = Field(description="House numbers and their meanings for this meter (e.g., {'1': 'Physical body...', '5': 'Creative vitality...'})")

    # Planetary meanings
    primary_planets: dict[str, str] = Field(description="Primary planetary influences with explanations (e.g., {'sun': 'Core life force...', 'mars': 'Physical drive...'})")
    secondary_planets: Optional[dict[str, str]] = Field(None, description="Secondary influences (e.g., {'saturn': 'Can temporarily deplete...'})")


class MeterForIOS(BaseModel):
    """
    Simplified meter data for iOS client - only essential fields with full explainability.

    Built from MeterReading but excludes internal fields like raw_scores.
    Includes all data needed for user to understand:
    - What this meter is (overview, detailed, foundation)
    - What's happening today (scores, state_label, interpretation)
    - Why it's happening (top_aspects with full context)
    - How it's changing (trend)
    """
    # Identity
    meter_name: str = Field(description="Internal meter ID (e.g., 'clarity')")
    display_name: str = Field(description="User-facing name (e.g., 'Clarity')")
    group: str = Field(description="Group ID: mind, heart, body, instincts, growth")

    # Scores (unified_score: -100 to +100, others: 0-100, normalized via calibration)
    unified_score: float = Field(ge=-100, le=100, description="Primary display value (-100 to +100, polar-style from intensity + harmony)")
    intensity: float = Field(ge=0, le=100, description="Activity level - how much is happening")
    harmony: float = Field(ge=0, le=100, description="Quality - supportive (high) vs challenging (low)")

    # Labels (two different purposes!)
    unified_quality: str = Field(description="Simple category: harmonious, challenging, mixed, quiet, peaceful")
    state_label: str = Field(description="Rich contextual state from JSON: 'Peak Performance', 'Pushing Through', 'Sluggish', etc.")

    # LLM-generated interpretation (1-2 sentences, 80-150 chars)
    interpretation: str = Field(description="Personalized daily interpretation referencing today's transits")

    # Trend (optional - only if yesterday data available)
    trend_delta: Optional[float] = Field(None, description="Change in unified_score from yesterday")
    trend_direction: Optional[str] = Field(None, description="improving, worsening, stable, increasing, decreasing")
    trend_change_rate: Optional[str] = Field(None, description="rapid, moderate, slow, stable")

    # Explainability - What is this meter? (static from JSON)
    overview: str = Field(description="What this meter represents (1 sentence, user-facing)")
    detailed: str = Field(description="How it's measured (2-3 sentences, explains calculation)")

    # Explainability - What drives this meter? (static from JSON)
    astrological_foundation: AstrologicalFoundation = Field(description="Planets, houses, and meanings")

    # Explainability - What's affecting it TODAY? (dynamic, daily)
    top_aspects: list[MeterAspect] = Field(description="Top 3-5 transit aspects driving today's score (sorted by contribution)")


class MeterGroupForIOS(BaseModel):
    """
    Simplified meter group for iOS - aggregated data with nested meters.

    Groups combine 3-4 related meters into life area categories.
    Scores are arithmetic means of member meters.
    """
    # Identity
    group_name: str = Field(description="Group ID: mind, heart, body, instincts, growth")
    display_name: str = Field(description="User-facing name: Mind, Heart, Body, Instincts, Growth")

    # Aggregated scores (arithmetic mean of member meters)
    unified_score: float = Field(ge=-100, le=100, description="Average unified score of member meters (-100 to +100)")
    intensity: float = Field(ge=0, le=100, description="Average intensity of member meters")
    harmony: float = Field(ge=0, le=100, description="Average harmony of member meters")

    # State
    state_label: str = Field(description="Aggregated state label from group JSON (contextual to group)")
    quality: str = Field(description="Generic enum: excellent, supportive, harmonious, peaceful, mixed, quiet, challenging, intense")

    # LLM interpretation (2-3 sentences, 150-300 chars)
    interpretation: str = Field(description="Group-level interpretation from existing LLM flow")

    # Member meters (simplified, nested for logical organization)
    meters: list[MeterForIOS] = Field(description="Individual meters in this group (3-4 meters)")

    # Trend (optional)
    trend_delta: Optional[float] = Field(None, description="Change in group unified_score from yesterday")
    trend_direction: Optional[str] = Field(None, description="improving, worsening, stable")
    trend_change_rate: Optional[str] = Field(None, description="rapid, moderate, slow, stable")

    # Group description (static from group JSON)
    overview: str = Field(description="What this group represents")
    detailed: str = Field(description="Which meters it combines + what it shows holistically")


class AstrometersForIOS(BaseModel):
    """
    Complete astrometers data for iOS - clean, explainable, and minimal.

    Replaces verbose AllMetersReading with iOS-optimized structure.
    All 17 meters nested within 5 groups for logical organization.
    """
    date: str = Field(description="ISO date of reading")

    # Overall stats (aggregated across all 17 meters)
    overall_unified_score: float = Field(ge=-100, le=100, description="Overall unified score across all meters (-100 to +100)")
    overall_intensity: "MeterReading" = Field(description="Overall intensity meter with state_label")
    overall_harmony: "MeterReading" = Field(description="Overall harmony meter with state_label")
    overall_quality: str = Field(description="Overall quality: harmonious, challenging, mixed, quiet, peaceful")
    overall_state: str = Field(description="Overall state label for the day (e.g., 'Quiet Reflection', 'Peak Energy', 'Under Pressure')")

    # 5 meter groups with their member meters nested (17 total meters)
    groups: list[MeterGroupForIOS] = Field(description="All 5 groups containing 17 total meters")

    # Top insights (for quick scanning on main screen)
    top_active_meters: list[str] = Field(description="Top 3-5 meter names by intensity (e.g., ['vitality', 'drive', 'communication'])")
    top_challenging_meters: list[str] = Field(description="Top 3-5 meter names by low harmony (need attention)")
    top_flowing_meters: list[str] = Field(description="Top 3-5 meter names by high unified_score (leverage these)")


# =============================================================================
# Rebuild forward references after all models are defined
# =============================================================================

# Import MeterReading now that we need it at runtime
from astrometers.meters import MeterReading

# Rebuild models that use forward references
AstrometersForIOS.model_rebuild()

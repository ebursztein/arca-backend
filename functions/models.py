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

class EntryType(str, Enum):
    """Journal entry type."""
    HOROSCOPE_READING = "horoscope_reading"
    TAROT_READING = "tarot_reading"  # V3+
    REFLECTION = "reflection"  # V3+
    QUESTION = "question"  # V3+


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


class CategoryViewed(BaseModel):
    """
    A category/group that was viewed in a reading.
    """
    category: MeterGroupV2 = Field(description="Meter group name")
    text: str = Field(description="Full text that was viewed")


class RecentReading(BaseModel):
    """
    A single reading in the recent history (FIFO queue, max 10).
    """
    date: str = Field(description="ISO date of reading")
    summary: str = Field(description="Summary text shown on main screen")
    categories_viewed: list[CategoryViewed] = Field(description="Categories expanded and read")
    astrometers_summary: Optional[dict] = Field(
        None,
        description="Key astrometers data: overall_intensity, overall_harmony, key_aspects (for trend analysis)"
    )


class MemoryCollection(BaseModel):
    """
    Memory collection stored in Firestore: memory/{userId}

    Server-side only - NOT accessible to client.
    Derivative cache used for personalization, rebuilt from journal.
    """
    user_id: str = Field(description="Firebase Auth user ID")

    # Category engagement tracking (using MeterGroupV2 hierarchy)
    categories: dict[MeterGroupV2, CategoryEngagement] = Field(
        description="Engagement counts per meter group"
    )

    # Recent readings for continuity (FIFO, max 10)
    recent_readings: list[RecentReading] = Field(
        default_factory=list,
        max_length=10,
        description="Last 10 readings with full text"
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

        # Recent readings for continuity
        lines.append("\nLast 10 Readings:")

        if self.recent_readings:
            for i, reading in enumerate(self.recent_readings[-10:], 1):
                lines.append(f"\n  Reading {i} ({reading.date}):")
                lines.append(f"    Summary: {reading.summary}")

                if reading.categories_viewed:
                    lines.append("    Categories viewed:")
                    for cat_view in reading.categories_viewed:
                        text_preview = cat_view.text[:100] + "..."
                        lines.append(
                            f"      - {cat_view.category.value}: {text_preview}"
                        )
        else:
            lines.append("  (First time user - no reading history)")

        return "\n".join(lines)


# =============================================================================
# Journal Entry Models
# =============================================================================

class JournalEntry(BaseModel):
    """
    Journal entry stored in Firestore: users/{userId}/journal/{entryId}

    Immutable log of user activity. Source of truth for memory collection.
    V1: horoscope readings. V3+: includes tarot, reflections, Q&A.
    """
    entry_id: str = Field(description="Auto-generated entry ID")
    date: str = Field(description="ISO date of reading")
    entry_type: EntryType = Field(description="Type of entry")

    # V1: Horoscope reading data
    summary_viewed: str = Field(description="Summary text shown to user")
    categories_viewed: list[CategoryViewed] = Field(description="Categories expanded and read")

    # V3+: Additional fields for tarot/reflections
    # tarot_cards: Optional[list] = None
    # user_question: Optional[str] = None
    # user_notes: Optional[str] = None

    time_spent_seconds: int = Field(ge=0, description="Time spent reading")
    created_at: str = Field(description="ISO datetime of creation")


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
    unified_score: float = Field(description="Primary display value (0-100), average of member meters")
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
    group_name: str = Field(description="Group ID: mind, emotions, body, spirit, growth")
    display_name: str = Field(description="Display name: Mind, Emotions, Body, Spirit, Growth")
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

    # Metadata
    model_used: Optional[str] = Field(None, description="LLM model used")
    generation_time_ms: Optional[int] = Field(None, description="Generation time in milliseconds")
    usage: dict = Field(default_factory=dict, description="Raw usage metadata from LLM API")


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
            MeterGroupV2.EMOTIONS: CategoryEngagement(),
            MeterGroupV2.BODY: CategoryEngagement(),
            MeterGroupV2.SPIRIT: CategoryEngagement(),
            MeterGroupV2.GROWTH: CategoryEngagement(),
        },
        recent_readings=[],
        updated_at=datetime.now().isoformat()
    )


def update_memory_from_journal(
    memory: MemoryCollection,
    journal_entry: JournalEntry
) -> MemoryCollection:
    """
    Update memory collection based on a journal entry.

    This simulates the Firestore trigger logic:
    - Increment category counts
    - Update last_mentioned timestamps
    - Add to recent_readings (FIFO, max 10)

    Args:
        memory: Current memory collection
        journal_entry: New journal entry to process

    Returns:
        Updated memory collection
    """
    # Update category counts
    for cat_view in journal_entry.categories_viewed:
        category = cat_view.category
        memory.categories[category].count += 1
        memory.categories[category].last_mentioned = journal_entry.date

    # Add to recent readings (FIFO, max 10)
    reading = RecentReading(
        date=journal_entry.date,
        summary=journal_entry.summary_viewed,
        categories_viewed=journal_entry.categories_viewed
    )
    memory.recent_readings.append(reading)

    # Keep only last 10 readings
    if len(memory.recent_readings) > 10:
        memory.recent_readings = memory.recent_readings[-10:]

    # Update timestamp
    memory.updated_at = datetime.now().isoformat()

    return memory


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
    meter_name: str = Field(description="Internal meter ID (e.g., 'mental_clarity')")
    display_name: str = Field(description="User-facing name (e.g., 'Mental Clarity')")
    group: str = Field(description="Group ID: mind, emotions, body, spirit, growth")

    # Scores (0-100, normalized via calibration)
    unified_score: float = Field(ge=0, le=100, description="Primary display value (balanced view of intensity + harmony)")
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
    group_name: str = Field(description="Group ID: mind, emotions, body, spirit, growth")
    display_name: str = Field(description="User-facing name: Mind, Emotions, Body, Spirit, Growth")

    # Aggregated scores (arithmetic mean of member meters)
    unified_score: float = Field(ge=0, le=100, description="Average unified score of member meters")
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
    overall_unified_score: float = Field(ge=0, le=100, description="Overall unified score across all meters")
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

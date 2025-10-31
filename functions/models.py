"""
Pydantic models for Arca Backend V1

All data structures used throughout the application for type safety and validation.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Any
from enum import Enum

# Import new hierarchy system
from astrometers.hierarchy import MeterGroup, SuperGroup


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
    category: MeterGroup = Field(description="Meter group name")
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

    # Category engagement tracking (using MeterGroup hierarchy)
    categories: dict[MeterGroup, CategoryEngagement] = Field(
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

class HoroscopeDetails(BaseModel):
    """
    Detailed horoscope predictions for 9 life groups (new hierarchy system).

    Based on 3-tier taxonomy: SuperGroup → MeterGroup → Meters
    This model uses Level 2 (MeterGroup) for organizing predictions.
    """
    overview: str = Field(description="Overall synthesis (~50-70 words)")
    mind: str = Field(description="Mental clarity, decisions, communication (~100-130 words)")
    emotions: str = Field(description="Feelings, relationships, resilience (~100-130 words)")
    body: str = Field(description="Physical energy, action, conflict (~100-130 words)")
    career: str = Field(description="Professional ambition and opportunities (~100-130 words)")
    evolution: str = Field(description="Growth, challenges, transformation (~100-130 words)")
    elements: str = Field(description="Elemental balance and temperament (~100-130 words)")
    spiritual: str = Field(description="Intuition, karmic lessons (~100-130 words)")
    collective: str = Field(description="Social consciousness and collective currents (~100-130 words)")


class ActionableAdvice(BaseModel):
    """
    Structured actionable guidance with do/don't/reflect format.
    """
    do: str = Field(description="Specific action aligned with transit energy")
    dont: str = Field(description="Specific thing to avoid (shadow/pitfall)")
    reflect_on: str = Field(description="Powerful journaling question for self-awareness")


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
    lunar_cycle_update: str = Field(
        description="Ritual and wellness guidance based on Moon phase (3-4 sentences)"
    )
    daily_theme_headline: str = Field(
        description="Shareable wisdom sentence (max 15 words, actionable)"
    )
    daily_overview: str = Field(
        description="Emotional/energetic tone for the day (2-3 sentences)"
    )
    summary: str = Field(description="Main screen summary (2-3 sentences)")
    actionable_advice: ActionableAdvice = Field(
        description="Structured DO/DON'T/REFLECT guidance"
    )

    # Astrometers data (quantitative foundation)
    astrometers: Any = Field(
        description="Complete astrometers reading with 28 meters (23 individual + 5 super-group), key aspects, and interpretations (AllMetersReading object)"
    )

    # Metadata
    model_used: Optional[str] = Field(None, description="LLM model used")
    generation_time_ms: Optional[int] = Field(None, description="Generation time in milliseconds")
    usage: dict = Field(default_factory=dict, description="Raw usage metadata from LLM API")


class DetailedHoroscope(BaseModel):
    """
    Detailed horoscope - Prompt 2 fields loaded in background (~5s).

    Provides collective context and detailed life category predictions.
    """
    general_transits_overview: list[str] = Field(
        description="Brief notes on collective transits (2-4 bullet points)"
    )
    look_ahead_preview: str = Field(
        description="Upcoming significant transits (2-3 sentences)"
    )
    details: HoroscopeDetails = Field(description="Detailed predictions for 8 categories")

    # Metadata
    model_used: Optional[str] = Field(None, description="LLM model used")
    generation_time_ms: Optional[int] = Field(None, description="Generation time in milliseconds")
    usage: dict = Field(default_factory=dict, description="Raw usage metadata from LLM API")


class CompleteHoroscope(BaseModel):
    """
    Complete horoscope combining daily + detailed responses.

    NOT stored in Firestore - generated on-demand per user.
    Convenience model for full horoscope data.
    """
    date: str = Field(description="ISO date of horoscope")
    sun_sign: str = Field(description="Sun sign (e.g., 'taurus')")

    # Core fields (shown on main screen)
    technical_analysis: str = Field(description="Astronomical explanation (3-5 sentences)")
    summary: str = Field(description="Main screen summary (2-3 sentences)")

    # Enhanced personalization fields
    daily_theme_headline: str = Field(
        description="Shareable wisdom sentence (max 15 words, profound and actionable)"
    )
    daily_overview: str = Field(
        description="Emotional/energetic tone for the day (2-3 sentences)"
    )
    actionable_advice: ActionableAdvice = Field(
        description="Structured DO/DON'T/REFLECT guidance"
    )
    lunar_cycle_update: str = Field(
        description="Ritual and wellness guidance based on Moon phase (3-4 sentences)"
    )
    general_transits_overview: list[str] = Field(
        description="Brief notes on collective transits (2-4 bullet points)"
    )
    look_ahead_preview: str = Field(
        description="Upcoming significant transits (2-3 sentences)"
    )

    # Astrometers data (quantitative foundation)
    astrometers: Any = Field(
        description="Complete astrometers reading with 23 meters, key aspects, and interpretations (AllMetersReading object)"
    )

    # Detailed predictions
    details: HoroscopeDetails = Field(description="Detailed predictions for 8 categories")

    # Metadata (optional)
    model_used: Optional[str] = Field(None, description="LLM model used (e.g., 'gemini-2.0-flash-exp')")
    generation_time_ms: Optional[int] = Field(None, description="Generation time in milliseconds")
    usage: dict = Field(default_factory=dict, description="Raw usage metadata from LLM API")


# =============================================================================
# Helper Functions
# =============================================================================

def create_empty_memory(user_id: str) -> MemoryCollection:
    """
    Create an empty memory collection for a new user.

    Uses new 9-group hierarchy system (MeterGroup).

    Args:
        user_id: Firebase Auth user ID

    Returns:
        Initialized MemoryCollection
    """
    return MemoryCollection(
        user_id=user_id,
        categories={
            MeterGroup.OVERVIEW: CategoryEngagement(),
            MeterGroup.MIND: CategoryEngagement(),
            MeterGroup.EMOTIONS: CategoryEngagement(),
            MeterGroup.BODY: CategoryEngagement(),
            MeterGroup.CAREER: CategoryEngagement(),
            MeterGroup.EVOLUTION: CategoryEngagement(),
            MeterGroup.ELEMENTS: CategoryEngagement(),
            MeterGroup.SPIRITUAL: CategoryEngagement(),
            MeterGroup.COLLECTIVE: CategoryEngagement(),
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

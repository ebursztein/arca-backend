"""
LLM integration for Arca Backend V1

Generates personalized daily horoscopes using:
- Gemini 2.5 Flash for fast, high-quality predictions
- Template-based prompt system with personalization
- PostHog integration for LLM observability
- Astrometers quantitative analysis
"""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import httpx
import uuid
from google import genai
from google.genai.types import GenerateContentResponse, GenerateContentResponseUsageMetadata

load_dotenv()

TEMPERATURE = 0.7

from astro import (
    ZodiacSign,
    SunSignProfile,
    describe_chart_emphasis,
    get_upcoming_transits,
    compute_birth_chart
)
from models import (
    DailyHoroscope,
    MemoryCollection,
    UserProfile,
    ActionableAdvice,
    MeterForIOS,
    MeterGroupForIOS,
    AstrometersForIOS,
    MeterAspect,
    AstrologicalFoundation,
    Entity,
    EntityCategory,
    RelationshipMention,
    RelationshipWeather,
)
from astrometers import get_meters, daily_meters_summary, get_meter_list
from compatibility import CompatibilityData
from astrometers.meter_groups import build_all_meter_groups, get_group_state_label
from astrometers.summary import meter_groups_summary
from astrometers.core import AspectContribution
from moon import get_moon_transit_detail, format_moon_summary_for_llm
from posthog_utils import capture_llm_generation
import json


# Initialize Jinja2 environment (point to templates root to allow includes across subdirs)
TEMPLATE_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


# =============================================================================
# Natal Chart Summary Generation
# =============================================================================

def generate_natal_chart_summary(
    chart_dict: dict,
    sun_sign_profile: SunSignProfile,
    user_name: str,
    api_key: str,
    user_id: str = "",
    posthog_api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash-lite"
) -> str:
    """
    Generate personalized natal chart interpretation.

    Args:
        chart_dict: NatalChartData as dict
        sun_sign_profile: User's sun sign profile
        user_name: User's first name for personalization
        api_key: Gemini API key
        user_id: User ID for PostHog tracking
        posthog_api_key: PostHog API key for observability
        model_name: Model to use

    Returns:
        3-4 sentence summary covering sun, moon, rising, and key aspects
    """
    import time
    start_time = time.time()

    # Get PostHog key
    if not posthog_api_key:
        posthog_api_key = os.environ.get("POSTHOG_API_KEY")

    # Load voice guidelines
    voice_path = Path(__file__).parent / "templates" / "voice.md"
    voice_content = voice_path.read_text() if voice_path.exists() else ""

    # Extract key chart elements
    sun_sign = sun_sign_profile.sign

    # Find moon sign
    moon_sign = None
    for planet in chart_dict.get("planets", []):
        planet_name = planet.get("name")
        if isinstance(planet_name, str):
            planet_name = planet_name.lower()
        elif hasattr(planet_name, "value"):
            planet_name = planet_name.value.lower()
        if planet_name == "moon":
            moon_sign = planet.get("sign")
            if hasattr(moon_sign, "value"):
                moon_sign = moon_sign.value
            break

    # Get ascendant sign
    asc_data = chart_dict.get("angles", {}).get("ascendant", {})
    asc_sign = asc_data.get("sign")
    if hasattr(asc_sign, "value"):
        asc_sign = asc_sign.value

    # Get top aspects (first 3 by orb)
    aspects = chart_dict.get("aspects", [])[:3]
    aspects_text = []
    for asp in aspects:
        p1 = asp.get("planet1", "")
        p2 = asp.get("planet2", "")
        asp_type = asp.get("aspect_type", "")
        if hasattr(p1, "value"):
            p1 = p1.value
        if hasattr(p2, "value"):
            p2 = p2.value
        if hasattr(asp_type, "value"):
            asp_type = asp_type.value
        aspects_text.append(f"{p1} {asp_type} {p2}")

    prompt = f"""{voice_content}

---

Generate a natal chart summary for {user_name}.

CHART DATA:
- Sun Sign: {sun_sign}
- Moon Sign: {moon_sign or 'unknown'}
- Rising Sign (Ascendant): {asc_sign or 'unknown'}
- Key Aspects: {', '.join(aspects_text) if aspects_text else 'none identified'}

SUN SIGN CONTEXT:
- Element: {sun_sign_profile.element.value}
- Modality: {sun_sign_profile.modality.value}
- Life Lesson: {sun_sign_profile.life_lesson}

INSTRUCTIONS:
Write exactly 4 sentences (approx. 50-60 words total) using this structure:

1. THE CORE: Open with the Sun sign to define their essential nature (e.g., "As a [Sun], you are...").
2. THE MASK: Connect the Rising sign to their outward style/approach (e.g., "Your [Rising] rising adds a layer of...").
3. THE HEART: Describe the Moon sign's emotional landscape (e.g., "With a [Moon] moon, you process feelings...").
4. THE SYNTHESIS: Write a final "bridge" sentence that resolves the tension or harmony between these three.
   - Look for Elemental conflict (e.g., Fire vs. Water) or Modality friction (Fixed vs. Mutable).
   - Example: "This creates a dynamic where your head wants to race ahead (Gemini), but your heart needs time to drift (Pisces)."

Use {user_name}'s name once naturally in sentence 1. Write like a wise friend, not an astrology textbook.
No jargon. No "energy" or "vibe". Be specific and grounded.

Return ONLY the summary text, no JSON wrapping."""

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=300
        )
    )

    latency_seconds = time.time() - start_time
    result_text = response.text.strip()

    # Debug: dump prompt and response to file (only when DEBUG_LLM is set)
    if os.environ.get("DEBUG_LLM"):
        import json
        debug_path = Path(__file__).parent / "debug_natal_chart_summary.json"
        debug_data = {
            "user_name": user_name,
            "prompt": prompt,
            "response": result_text,
            "sun_sign": str(sun_sign),
            "moon_sign": moon_sign,
            "asc_sign": asc_sign,
        }
        debug_path.write_text(json.dumps(debug_data, indent=2))
        print(f"[DEBUG] Natal chart summary dumped to {debug_path}")
        print(f"[DEBUG] user_name passed: '{user_name}'")

    # Track with PostHog
    if posthog_api_key and user_id:
        try:
            capture_llm_generation(
                posthog_api_key=posthog_api_key,
                distinct_id=user_id,
                model=model_name,
                provider="gemini",
                prompt=prompt,
                response=result_text,
                usage=response.usage_metadata if hasattr(response, 'usage_metadata') else None,
                latency=latency_seconds,
                generation_type="natal_chart_summary"
            )
        except Exception:
            pass  # Don't fail on PostHog errors

    return result_text


# =============================================================================
# Helper Functions for iOS Astrometers Conversion
# =============================================================================

METER_NAMES = [
    "clarity", "focus", "communication",
    "resilience", "connections", "vulnerability",
    "energy", "drive", "strength",
    "vision", "flow", "intuition", "creativity",
    "momentum", "ambition", "evolution", "circle"
]

METER_GROUP_MAPPING = {
    "mind": ["clarity", "focus", "communication"],
    "heart": ["resilience", "connections", "vulnerability"],
    "body": ["energy", "drive", "strength"],
    "instincts": ["vision", "flow", "intuition", "creativity"],
    "growth": ["momentum", "ambition", "evolution", "circle"]
}


def load_meter_descriptions() -> dict[str, dict]:
    """Load overview, detailed, and astrological_foundation from meter JSON files."""
    descriptions = {}
    base_path = Path(__file__).parent / "astrometers" / "labels"

    for meter_name in METER_NAMES:
        json_path = base_path / f"{meter_name}.json"
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                descriptions[meter_name] = {
                    "overview": data["description"]["overview"],
                    "detailed": data["description"]["detailed"],
                    "astrological_foundation": data["astrological_foundation"]
                }
        except Exception as e:
            print(f"Warning: Could not load {meter_name}.json: {e}")
            descriptions[meter_name] = {
                "overview": f"{meter_name.replace('_', ' ').title()}",
                "detailed": "Meter description unavailable",
                "astrological_foundation": {}
            }

    return descriptions


def load_group_descriptions() -> dict[str, dict]:
    """Load overview and detailed descriptions from group JSON files."""
    descriptions = {}
    base_path = Path(__file__).parent / "astrometers" / "labels" / "groups"

    for group_name in ["mind", "heart", "body", "instincts", "growth"]:
        json_path = base_path / f"{group_name}.json"
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                descriptions[group_name] = {
                    "overview": data["description"]["overview"],
                    "detailed": data["description"]["detailed"]
                }
        except Exception as e:
            print(f"Warning: Could not load {group_name}.json: {e}")
            descriptions[group_name] = {
                "overview": f"{group_name.title()}",
                "detailed": "Group description unavailable"
            }

    return descriptions


def convert_aspect_contribution_to_meter_aspect(
    aspect: AspectContribution
) -> MeterAspect:
    """
    Convert AspectContribution to MeterAspect with full explainability data.

    All data now comes directly from the AspectContribution object (no guessing!).

    Args:
        aspect: AspectContribution from astrometers core (with explainability fields)

    Returns:
        MeterAspect with all fields populated from real data
    """
    # Calculate orb percentage (orb / max_orb * 100)
    orb_percentage = (aspect.orb_deviation / aspect.max_orb * 100) if aspect.max_orb > 0 else 0.0

    # Calculate phase (applying vs separating)
    phase = "exact"
    days_to_exact = None

    if aspect.today_deviation is not None and aspect.tomorrow_deviation is not None:
        daily_change = abs(aspect.today_deviation - aspect.tomorrow_deviation)
        if daily_change > 0:
            if abs(aspect.tomorrow_deviation) < abs(aspect.today_deviation):
                phase = "applying"
                days_to_exact = abs(aspect.today_deviation) / daily_change
            else:
                phase = "separating"
                days_to_exact = -1 * (abs(aspect.today_deviation) / daily_change)
        # If daily_change == 0, keep phase as "exact" (stationary)

    # Exact aspect (orb < 0.5°)
    if aspect.orb_deviation < 0.5:
        phase = "exact"
        days_to_exact = 0.0

    return MeterAspect(
        label=aspect.label,
        natal_planet=aspect.natal_planet.value,
        transit_planet=aspect.transit_planet.value,
        aspect_type=aspect.aspect_type.value,
        orb=aspect.orb_deviation,
        orb_percentage=orb_percentage,
        phase=phase,
        days_to_exact=days_to_exact,
        contribution=aspect.dti_contribution,
        quality_factor=aspect.quality_factor,
        natal_planet_house=aspect.natal_planet_house,
        natal_planet_sign=aspect.natal_planet_sign.value,
        houses_involved=[aspect.natal_planet_house],  # Could expand if transit house available
        natal_aspect_echo=None  # Would need natal chart aspect analysis
    )


def build_astrometers_for_ios(
    all_meters_reading,
    meter_interpretations: dict[str, str],
    group_interpretations: dict[str, str],
) -> AstrometersForIOS:
    """
    Convert AllMetersReading to clean iOS-optimized structure.

    Args:
        all_meters_reading: Complete AllMetersReading object
        meter_interpretations: Dict of meter_name -> LLM interpretation
        group_interpretations: Dict of group_name -> LLM interpretation

    Returns:
        AstrometersForIOS with complete explainability data

    Note: State labels are computed by backend. iOS maps unified_score to bucket labels.
    """
    # Load descriptions once
    meter_descriptions = load_meter_descriptions()
    group_descriptions = load_group_descriptions()

    # Build groups
    groups = []
    all_meters_list = []

    for group_name in ["mind", "heart", "body", "instincts", "growth"]:
        meter_names = METER_GROUP_MAPPING[group_name]

        # Build MeterForIOS for each meter in group
        meters_for_ios = []
        for meter_name in meter_names:
            meter_reading = getattr(all_meters_reading, meter_name)
            meter_desc = meter_descriptions.get(meter_name, {})

            # Convert top aspects using real data from AspectContribution
            top_aspects = [
                convert_aspect_contribution_to_meter_aspect(asp)
                for asp in meter_reading.top_aspects[:5]
            ]

            # Build astrological foundation from JSON
            foundation_data = meter_desc.get("astrological_foundation", {})
            astrological_foundation = AstrologicalFoundation(
                natal_planets_tracked=foundation_data.get("natal_planets_tracked", []),
                transit_planets_tracked=foundation_data.get("transit_planets_tracked", []),
                key_houses={
                    str(k): v for k, v in foundation_data.get("key_houses", {}).items()
                },
                primary_planets=foundation_data.get("primary_planets", {}),
                secondary_planets=foundation_data.get("secondary_planets")
            )

            # Extract trend data
            trend_delta = None
            trend_direction = None
            trend_change_rate = None
            if meter_reading.trend:
                trend_delta = meter_reading.trend.unified_score.delta
                trend_direction = meter_reading.trend.unified_score.direction
                trend_change_rate = meter_reading.trend.unified_score.change_rate

            meter_for_ios = MeterForIOS(
                meter_name=meter_name,
                display_name=meter_reading.meter_name.replace('_', ' ').title(),
                group=group_name,
                unified_score=meter_reading.unified_score,
                intensity=meter_reading.intensity,
                harmony=meter_reading.harmony,
                unified_quality=meter_reading.unified_quality.value,
                state_label=meter_reading.state_label,
                interpretation=meter_interpretations.get(meter_name, ""),
                trend_delta=trend_delta,
                trend_direction=trend_direction,
                trend_change_rate=trend_change_rate,
                overview=meter_desc.get("overview", ""),
                detailed=meter_desc.get("detailed", ""),
                astrological_foundation=astrological_foundation,
                top_aspects=top_aspects
            )
            meters_for_ios.append(meter_for_ios)
            all_meters_list.append(meter_for_ios)

        # Calculate group aggregates
        avg_unified = sum(m.unified_score for m in meters_for_ios) / len(meters_for_ios)
        avg_intensity = sum(m.intensity for m in meters_for_ios) / len(meters_for_ios)
        avg_harmony = sum(m.harmony for m in meters_for_ios) / len(meters_for_ios)

        # Determine group quality from unified_score quadrants
        if avg_unified < -25:
            quality = "challenging"
        elif avg_unified < 10:
            quality = "turbulent"
        elif avg_unified < 50:
            quality = "peaceful"
        else:
            quality = "flowing"

        # State label computed by backend - iOS uses unified_score to map to bucket labels
        state_label = get_group_state_label(group_name, avg_intensity, avg_harmony)

        # Extract group trend (calculate from member meter trends)
        group_trend_delta = None
        group_trend_direction = None
        group_trend_change_rate = None
        if all(m.trend_delta is not None for m in meters_for_ios):
            group_trend_delta = sum(m.trend_delta for m in meters_for_ios) / len(meters_for_ios)
            # Determine direction based on delta
            if group_trend_delta > 5:
                group_trend_direction = "improving"
            elif group_trend_delta < -5:
                group_trend_direction = "worsening"
            else:
                group_trend_direction = "stable"

        group_desc = group_descriptions.get(group_name, {})

        group_for_ios = MeterGroupForIOS(
            group_name=group_name,
            display_name=group_name.title(),
            unified_score=avg_unified,
            intensity=avg_intensity,
            harmony=avg_harmony,
            state_label=state_label,
            quality=quality,
            interpretation=group_interpretations.get(group_name, ""),
            meters=meters_for_ios,
            trend_delta=group_trend_delta,
            trend_direction=group_trend_direction,
            trend_change_rate=group_trend_change_rate,
            overview=group_desc.get("overview", ""),
            detailed=group_desc.get("detailed", "")
        )
        groups.append(group_for_ios)

    # Calculate top meters
    sorted_by_intensity = sorted(all_meters_list, key=lambda m: m.intensity, reverse=True)
    sorted_by_harmony_low = sorted(all_meters_list, key=lambda m: m.harmony)
    sorted_by_unified_high = sorted(all_meters_list, key=lambda m: m.unified_score, reverse=True)

    top_active_meters = [m.meter_name for m in sorted_by_intensity[:5]]
    top_challenging_meters = [m.meter_name for m in sorted_by_harmony_low[:5] if m.harmony < 50]
    top_flowing_meters = [m.meter_name for m in sorted_by_unified_high[:5] if m.unified_score > 70]

    # Overall state computed by backend - iOS uses unified_score to map to bucket labels
    overall_intensity = all_meters_reading.overall_intensity.intensity
    overall_harmony = all_meters_reading.overall_harmony.harmony
    overall_state = get_group_state_label("overall", overall_intensity, overall_harmony)

    return AstrometersForIOS(
        date=all_meters_reading.date.isoformat(),
        overall_unified_score=all_meters_reading.overall_intensity.unified_score,
        overall_intensity=all_meters_reading.overall_intensity,
        overall_harmony=all_meters_reading.overall_harmony,
        overall_quality=all_meters_reading.overall_unified_quality.value,
        overall_state=overall_state,
        groups=groups,
        top_active_meters=top_active_meters,
        top_challenging_meters=top_challenging_meters,
        top_flowing_meters=top_flowing_meters
    )


def group_entities_by_category(entities: list[Entity]) -> dict:
    """
    Group user's entities by category for relationship weather.

    Args:
        entities: List of Entity objects from user's entity collection

    Returns:
        Dict with:
        - has_partner: bool
        - partner: Optional[Entity] - the partner entity if exists
        - family: list[Entity] - family members
        - friends: list[Entity] - friends
        - coworkers: list[Entity] - work relationships
        - has_relationships: bool - True if any relationship entities exist
    """
    result = {
        "has_partner": False,
        "partner": None,
        "family": [],
        "friends": [],
        "coworkers": [],
        "has_relationships": False
    }

    if not entities:
        return result

    for entity in entities:
        if not entity.category:
            continue

        if entity.category == EntityCategory.PARTNER:
            result["has_partner"] = True
            result["partner"] = entity
        elif entity.category == EntityCategory.FAMILY:
            result["family"].append(entity)
        elif entity.category == EntityCategory.FRIEND:
            result["friends"].append(entity)
        elif entity.category == EntityCategory.COWORKER:
            result["coworkers"].append(entity)

    # Check if any relationship entities exist
    result["has_relationships"] = (
        result["has_partner"] or
        len(result["family"]) > 0 or
        len(result["friends"]) > 0 or
        len(result["coworkers"]) > 0
    )

    return result


def update_memory_with_relationship_mention(
    memory: MemoryCollection,
    featured_relationship: Optional[Entity],
    date: str,
    relationship_weather: str
) -> MemoryCollection:
    """
    Update memory with relationship mention after horoscope generation.

    Appends to relationship_mentions (capped at 20, FIFO).
    This tracks what was said to avoid repetition in rotation.

    Args:
        memory: User's memory collection
        featured_relationship: Entity that was featured (or None)
        date: ISO date string
        relationship_weather: The relationship_weather text from horoscope

    Returns:
        Updated MemoryCollection
    """
    if not featured_relationship:
        return memory

    # Create new mention
    mention = RelationshipMention(
        entity_id=featured_relationship.entity_id,
        entity_name=featured_relationship.name,
        category=featured_relationship.category,
        date=date,
        context=relationship_weather[:500] if relationship_weather else ""  # Cap context length
    )

    # Append to list
    memory.relationship_mentions.append(mention)

    # FIFO: Keep only last 20
    if len(memory.relationship_mentions) > 20:
        memory.relationship_mentions = memory.relationship_mentions[-20:]

    return memory


def select_featured_relationship(
    entities: list[Entity],
    memory: MemoryCollection,
    date: str
) -> Optional[Entity]:
    """
    Select ONE entity to feature in today's horoscope using round-robin rotation.

    Rotates through all relationship entities (partner, family, friend, coworker),
    prioritizing those not recently featured. Uses relationship_mentions in memory
    to track what was last featured.

    Args:
        entities: List of Entity objects
        memory: User's memory collection with relationship_mentions
        date: Today's date (YYYY-MM-DD)

    Returns:
        Entity to feature, or None if no relationship entities exist
    """
    if not entities:
        return None

    # Filter to only relationship entities (have a category)
    relationship_entities = [
        e for e in entities
        if e.category and e.category != EntityCategory.OTHER
    ]

    if not relationship_entities:
        return None

    # Get recently featured entity IDs from memory
    recent_mentions = memory.relationship_mentions or []
    recently_featured_ids = {m.entity_id for m in recent_mentions[-10:]}

    # Prioritize entities NOT recently featured
    not_recently_featured = [
        e for e in relationship_entities
        if e.entity_id not in recently_featured_ids
    ]

    if not_recently_featured:
        # Pick from not recently featured, sorted by importance
        sorted_entities = sorted(
            not_recently_featured,
            key=lambda e: e.importance_score,
            reverse=True
        )
        return sorted_entities[0]

    # All have been featured recently - pick the one featured longest ago
    # by sorting relationship_mentions and picking the oldest
    if recent_mentions:
        # Create a map of entity_id -> last mention date
        mention_dates = {}
        for mention in recent_mentions:
            mention_dates[mention.entity_id] = mention.date

        # Sort by oldest mention first
        sorted_by_oldest = sorted(
            relationship_entities,
            key=lambda e: mention_dates.get(e.entity_id, "1900-01-01")
        )
        return sorted_by_oldest[0]

    # Fallback: just pick the highest importance
    return max(relationship_entities, key=lambda e: e.importance_score)


def select_featured_connection(
    connections: list[dict],
    memory: MemoryCollection,
    date: str
) -> Optional[dict]:
    """
    Select ONE connection to feature in today's relationship_weather.

    Uses round-robin rotation, prioritizing connections not recently featured.
    Uses connection_mentions in memory to track what was last featured.

    Args:
        connections: List of connection dicts from Firestore
        memory: User's memory collection with connection_mentions
        date: Today's date (YYYY-MM-DD)

    Returns:
        Connection dict to feature, or None if no connections exist
    """
    if not connections:
        return None

    # Get recently featured connection IDs from memory
    recent_mentions = memory.connection_mentions or []
    recently_featured_ids = {m.connection_id for m in recent_mentions[-10:]}

    # Prioritize connections NOT recently featured
    not_recently_featured = [
        c for c in connections
        if c.get("connection_id") not in recently_featured_ids
    ]

    if not_recently_featured:
        # Pick first not recently featured (could add priority by relationship_category/label)
        return not_recently_featured[0]

    # All have been featured recently - pick the one featured longest ago
    if recent_mentions:
        mention_dates = {m.connection_id: m.date for m in recent_mentions}
        sorted_by_oldest = sorted(
            connections,
            key=lambda c: mention_dates.get(c.get("connection_id"), "1900-01-01")
        )
        return sorted_by_oldest[0]

    # Fallback: just pick the first one
    return connections[0]


def update_memory_with_connection_mention(
    memory: MemoryCollection,
    featured_connection: Optional[dict],
    date: str,
    context: str
) -> MemoryCollection:
    """
    Update memory with connection mention after horoscope generation.

    Appends to connection_mentions (capped at 20, FIFO).
    This tracks what was said to avoid repetition in rotation.

    Args:
        memory: User's memory collection
        featured_connection: Connection dict that was featured (or None)
        date: ISO date string
        context: What was said about this connection (vibe text)

    Returns:
        Updated MemoryCollection
    """
    if not featured_connection:
        return memory

    # Import here to avoid circular import
    from models import ConnectionMention

    # Create new mention
    mention = ConnectionMention(
        connection_id=featured_connection.get("connection_id", ""),
        connection_name=featured_connection.get("name", ""),
        relationship_category=featured_connection.get("relationship_category", "friend"),
        relationship_label=featured_connection.get("relationship_label", "friend"),
        date=date,
        context=context[:500] if context else ""  # Cap context length
    )

    # Append to list
    memory.connection_mentions.append(mention)

    # FIFO: Keep only last 20
    if len(memory.connection_mentions) > 20:
        memory.connection_mentions = memory.connection_mentions[-20:]

    return memory


def generate_daily_horoscope(
    date: str,
    user_profile: UserProfile,
    sun_sign_profile: SunSignProfile,
    transit_summary: dict,
    memory: MemoryCollection,
    featured_connection: Optional[dict] = None,
    api_key: Optional[str] = None,
    posthog_api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash-lite",
) -> DailyHoroscope:
    """
    Generate daily horoscope (Prompt 1) - core transit analysis (async internal).

    Args:
        date: ISO date string (YYYY-MM-DD)
        user_profile: Complete user profile
        sun_sign_profile: Complete sun sign profile
        transit_summary: Enhanced transit summary dict from format_transit_summary_for_ui()
        memory: User's memory collection
        featured_connection: Optional connection dict for relationship_weather spotlight
        api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        posthog_api_key: PostHog API key for observability
        model_name: Model to use (default: gemini-2.5-flash-lite)

    Returns:
        DailyHoroscope with all fields populated
    """

    MAX_TOKENS = 4096
    THINKING_BUDGET = 0

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not provided")

    if not posthog_api_key:
        posthog_api_key = os.environ.get("POSTHOG_API_KEY")
    if not posthog_api_key:
        print("WARNING: POSTHOG_API_KEY not provided in generate_daily_horoscope")
        raise ValueError("POSTHOG_API_KEY not provided")

    # Initialize Gemini client (direct, no SDK wrapper)
    client = genai.Client(api_key=api_key)


    # Compute transit chart for astrometers
    transit_chart, _ = compute_birth_chart(
        birth_date=date,
        birth_time="12:00"  # Use noon for transits
    )

    # Calculate TODAY'S astrometers
    from datetime import datetime as dt, timedelta
    date_obj = dt.fromisoformat(date) if isinstance(date, str) else date
    astrometers = get_meters(
        natal_chart=user_profile.natal_chart,
        transit_chart=transit_chart,
        date=date_obj,
        user_id=user_profile.user_id  # Pass user_id for cosmic background noise
    )

    # Calculate YESTERDAY'S astrometers for trend data
    yesterday_date = date_obj - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime('%Y-%m-%d')
    yesterday_transit_chart, _ = compute_birth_chart(
        birth_date=yesterday_date_str,
        birth_time="12:00"
    )
    astrometers_yesterday = get_meters(
        natal_chart=user_profile.natal_chart,
        transit_chart=yesterday_transit_chart,
        date=yesterday_date
    )

    # Generate smart summary (replaces verbose dump in template)
    meters_summary = daily_meters_summary(astrometers, astrometers_yesterday)

    # Build meter groups with empty interpretations (LLM will fill these)
    meter_groups = build_all_meter_groups(
        astrometers,
        llm_interpretations=None,  # Will be filled from LLM response
        yesterday_all_meters_reading=astrometers_yesterday
    )
    groups_summary = meter_groups_summary(meter_groups)

    # Select featured meters for programmatic curation (1-2 groups, 1-2 meters each = 2-3 total)
    from astrometers.meters import select_featured_meters
    featured = select_featured_meters(
        all_meters=astrometers,
        user_id=user_profile.user_id,
        date=date,
        num_groups=2,
        num_meters_per_group=1
    )

    # Get comprehensive moon transit detail
    moon_detail = get_moon_transit_detail(
        natal_chart=user_profile.natal_chart,
        transit_chart=transit_chart,
        current_datetime=f"{date}T12:00:00"
    )
    moon_summary_for_llm = format_moon_summary_for_llm(moon_detail)

    # Prepare helper data
    chart_emphasis = describe_chart_emphasis(user_profile.natal_chart['distributions'])

    # Get upcoming transits for look_ahead_preview
    upcoming_transits_raw = get_upcoming_transits(user_profile.natal_chart, date, days_ahead=7)

    # Group transits by day and add day names
    from datetime import datetime as dt, timedelta
    from collections import defaultdict
    transits_by_day = defaultdict(list)
    date_obj = dt.fromisoformat(date)

    for transit in upcoming_transits_raw:
        transits_by_day[transit.days_away].append(transit)

    # Format for template with day names
    upcoming_transits_formatted = []
    for day_offset in sorted(transits_by_day.keys()):
        target_date = date_obj + timedelta(days=day_offset)
        day_name = target_date.strftime('%A')
        date_str = target_date.strftime('%Y-%m-%d')

        if day_offset == 0:
            header = f"TODAY ({day_name}):"
        else:
            header = f"Day +{day_offset} - {day_name} ({date_str}):"

        upcoming_transits_formatted.append({
            'header': header,
            'transits': transits_by_day[day_offset]
        })

    # Render static template with meter metadata for reference
    # fixme cache static
    cache_content = None

    static_template = jinja_env.get_template("horoscope/daily_static.j2")
    static_prompt = static_template.render()  # Static template has no variables now

    # Build all_groups with unified_score, trend direction, and word inspirations
    from astrometers.meters import select_state_words
    all_groups = []
    for group_name, group_data in meter_groups.items():
        words = select_state_words(
            group_name=group_name,
            intensity=group_data['scores']['intensity'],
            harmony=group_data['scores']['harmony'],
            user_id=user_profile.user_id,
            date=date,
            count=2
        )
        # Get trend direction as arrow symbol
        trend = None
        if group_data.get('trend') and group_data['trend'].get('unified_score'):
            trend_dir = group_data['trend']['unified_score'].get('direction')
            if trend_dir == 'increasing':
                trend = 'rising'
            elif trend_dir == 'decreasing':
                trend = 'falling'
            # stable = no trend shown

        all_groups.append({
            'name': group_name,
            'unified_score': group_data['scores']['unified_score'],
            'trend': trend,
            'words': words
        })

    # Flatten featured meters into a single list
    featured_meters = []
    for group_name, meters in featured['featured_meters'].items():
        for meter in meters:
            featured_meters.append(meter)

    # Render dynamic template with featured connection (replacing entities)
    dynamic_template = jinja_env.get_template("horoscope/daily_dynamic.j2")
    dynamic_prompt = dynamic_template.render(
        date=date,
        all_groups=all_groups,  # All 5 groups with scores + words
        featured_meters=featured_meters,  # 2-3 featured meters for emphasis
        upcoming_transits=upcoming_transits_formatted,
        moon_summary=moon_summary_for_llm,
        # Connection data for relationship weather section
        has_relationships=featured_connection is not None,
        featured_connection=featured_connection
    )

    # Calculate age and generation
    birth_year = int(user_profile.birth_date.split("-")[0])
    current_year = int(date.split("-")[0])
    age = current_year - birth_year

    if birth_year >= 2013:
        generation = "Gen Alpha"
    elif birth_year >= 1997:
        generation = "Gen Z"
    elif birth_year >= 1981:
        generation = "Millennial"
    elif birth_year >= 1965:
        generation = "Gen X"
    elif birth_year >= 1946:
        generation = "Baby Boomer"
    else:
        generation = "Silent Generation"

    # this is user specific can't be cached
    personalization_template = jinja_env.get_template("horoscope/personalization.j2")
    personalization_prompt = personalization_template.render(
        user=user_profile,
        sign=sun_sign_profile,
        memory=memory,
        chart_emphasis=chart_emphasis,
        age=age,
        generation=generation
    )

    # Compose final
    prompt = f"{static_prompt}\n\n{personalization_prompt}\n\n{dynamic_prompt}"

    # Debug output (only when running locally, not in Cloud Functions)
    if os.environ.get("DEBUG_PROMPT"):
        with open('debug_prompt.txt', 'w') as f:
            f.write(prompt)
        print(f"\n[yellow]Generated Daily Horoscope Prompt:[/yellow]")
        print(prompt)
        print("\n[yellow]End of Prompt[/yellow]\n")

    # Define response schema
    class DailyHoroscopeResponse(BaseModel):
        technical_analysis: str
        lunar_cycle_update: str
        daily_theme_headline: str
        daily_overview: str
        actionable_advice: ActionableAdvice

        # Meter group interpretations (2-3 sentences each, 150-300 chars)
        mind_interpretation: str
        heart_interpretation: str
        body_interpretation: str
        instincts_interpretation: str
        growth_interpretation: str

        # Look ahead (merged from detailed horoscope)
        look_ahead_preview: str

        # Phase 1 Extensions
        energy_rhythm: str
        relationship_weather: str
        collective_energy: str

        # Engagement
        follow_up_questions: list[str]

    # Generate
    try:
        start_time = datetime.now()

        config = types.GenerateContentConfig(
            temperature=TEMPERATURE,
            max_output_tokens=MAX_TOKENS,
            thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
            response_mime_type="application/json",
            response_schema=DailyHoroscopeResponse,
            cached_content=cache_content if cache_content else None
        )

        # Direct Gemini call (no SDK wrapper)
        response: GenerateContentResponse = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )

        generation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        usage = response.usage_metadata.model_dump() if response.usage_metadata else {}
        parsed: DailyHoroscopeResponse = response.parsed

        open('last_daily_horoscope_response.json', 'w').write(parsed.model_dump_json(indent=2))


        print(f"[generate_daily_horoscope]Model:{model_name} Time:{generation_time_ms}ms Usage:{usage}")

        # Manually capture to PostHog using HTTP API
        output = f"Headline: {parsed.daily_theme_headline}\nOverview: {parsed.daily_overview}"
        capture_llm_generation(
            posthog_api_key=posthog_api_key,
            distinct_id=user_profile.user_id,
            model=model_name,
            provider="gemini",
            prompt=prompt,
            response=output,
            usage=response.usage_metadata,
            latency=generation_time_ms / 1000.0,
            generation_type="daily_horoscope",
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            thinking_budget=THINKING_BUDGET
        )

        # Extract group interpretations (5 fields)
        group_interpretations = {
            "mind": parsed.mind_interpretation,
            "heart": parsed.heart_interpretation,
            "body": parsed.body_interpretation,
            "instincts": parsed.instincts_interpretation,
            "growth": parsed.growth_interpretation,
        }

        # Extract individual meter interpretations (17 fields)
        meter_interpretations = {
            "clarity": "",
            "focus": "",
            "communication": "",
            "resilience": "",
            "connections": "",
            "vulnerability": "",
            "energy": "",
            "drive": "",
            "strength": "",
            "vision": "",
            "flow": "",
            "intuition": "",
            "creativity": "",
            "momentum": "",
            "ambition": "",
            "evolution": "",
            "circle": "",
        }

        # Build iOS-optimized astrometers structure
        # State labels are computed from unified_score, not generated by LLM
        astrometers_for_ios = build_astrometers_for_ios(
            astrometers,
            meter_interpretations=meter_interpretations,
            group_interpretations=group_interpretations,
        )

        # Populate moon_detail.interpretation with LLM output
        moon_detail.interpretation = parsed.lunar_cycle_update

        horoscope = DailyHoroscope(
            date=date,
            sun_sign=user_profile.sun_sign,
            technical_analysis=parsed.technical_analysis,
            daily_theme_headline=parsed.daily_theme_headline,
            daily_overview=parsed.daily_overview,
            actionable_advice=parsed.actionable_advice,
            astrometers=astrometers_for_ios,  # iOS-optimized with full explainability
            transit_summary=transit_summary,
            moon_detail=moon_detail,
            look_ahead_preview=parsed.look_ahead_preview,
            energy_rhythm=parsed.energy_rhythm,
            # Wrap LLM string response in RelationshipWeather object
            # connection_vibes will be populated separately when connections exist
            relationship_weather=RelationshipWeather(
                overview=parsed.relationship_weather,
                connection_vibes=[]
            ) if parsed.relationship_weather else None,
            collective_energy=parsed.collective_energy,
            follow_up_questions=parsed.follow_up_questions,
            model_used=model_name,
            generation_time_ms=generation_time_ms,
            usage=usage
        )

        return horoscope

    except Exception as e:
        raise RuntimeError(f"Error generating daily horoscope: {e}")


# =============================================================================
# Compatibility Interpretation (LLM-generated personalized text)
# =============================================================================

class CategoryInsight(BaseModel):
    """LLM-generated insight for a single compatibility category."""
    category_id: str = Field(description="Category ID (e.g., emotional, communication)")
    insight: str = Field(description="1-2 sentence insight for this category")


class CompatibilityLLMResponse(BaseModel):
    """Structured LLM response for compatibility interpretation.

    This is the schema the LLM generates. We then merge this with
    the calculated data to produce the final CompatibilityResult.
    """
    headline: str = Field(description="5-8 word viral-worthy headline (e.g., 'Deep Waters, Shared Vision')")
    summary: str = Field(description="2-3 sentence elevator pitch of the relationship")
    strengths: str = Field(description="2-3 sentences about natural flows (harmonious aspects)")
    growth_areas: str = Field(description="1-2 sentences about challenges/opportunities")
    advice: str = Field(description="One concrete, actionable step they can take today")
    vibe_phrase: str = Field(description="Short energy label for the mode (e.g., 'Slow Burn', 'Ride or Die', 'Power Partners')")
    composite_purpose: str = Field(
        default="",
        description="1-2 sentences on why this relationship exists (from composite chart)"
    )
    destiny_note: str = Field(
        default="",
        description="1-2 sentences about karmic/fated connection (only if is_karmic is True)"
    )
    category_insights: list[CategoryInsight] = Field(
        default_factory=list,
        description="Per-category insights as list of objects with category_id and insight"
    )


def generate_compatibility_result(
    compatibility_data: "CompatibilityData",
    relationship_category: str,
    relationship_label: str,
    api_key: Optional[str] = None,
    user_id: str = "",
    posthog_api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash-lite"
) -> "CompatibilityResult":
    """
    Generate complete CompatibilityResult with LLM-enriched content.

    Takes the calculated CompatibilityData and enriches it with
    LLM-generated narrative content (headline, summary, insights, etc.)

    Args:
        compatibility_data: Calculated compatibility data from calculate_compatibility()
        relationship_category: Main category (love/friend/family/coworker/other)
        relationship_label: Specific label (crush/partner/best_friend/boss/etc)
        api_key: Gemini API key
        user_id: User ID for PostHog tracking
        posthog_api_key: PostHog API key for observability
        model_name: Model to use

    Returns:
        Complete CompatibilityResult ready for API response
    """
    import time
    from datetime import datetime
    from compatibility import (
        CompatibilityResult, ModeCompatibility, CompatibilityCategory,
        Composite, Karmic, RelationshipType,
    )

    start_time = time.time()

    # Get API key
    gemini_api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found")

    # Get PostHog key
    if not posthog_api_key:
        posthog_api_key = os.environ.get("POSTHOG_API_KEY")

    # Load voice guidelines
    voice_path = Path(__file__).parent / "templates" / "voice.md"
    voice_content = voice_path.read_text() if voice_path.exists() else ""

    # Extract data for prompt
    mode = compatibility_data.mode
    user_name = compatibility_data.user_name
    connection_name = compatibility_data.connection_name
    user_sun_sign = compatibility_data.user_sun_sign
    connection_sun_sign = compatibility_data.connection_sun_sign

    # Get relationship context
    try:
        from relationships import (
            RelationshipCategory as RelCat,
            RelationshipLabel as RelLabel,
            get_llm_guidance,
        )
        cat_enum = RelCat(relationship_category)
        label_enum = RelLabel(relationship_label)
        llm_guidance = get_llm_guidance(cat_enum, label_enum)
    except (ValueError, ImportError):
        llm_guidance = ""

    # Build category IDs list for rules
    category_ids = [cat.id for cat in mode.categories]

    # Format top aspects (limit to 8 for token efficiency)
    top_aspects = compatibility_data.aspects[:8]
    aspects_context = []
    for aspect in top_aspects:
        # Translate aspect type to plain language
        aspect_meanings = {
            "conjunction": "merges with",
            "opposition": "challenges",
            "trine": "flows with",
            "square": "clashes with",
            "sextile": "supports",
            "quincunx": "adjusts to",
        }
        aspect_verb = aspect_meanings.get(aspect.aspect_type, aspect.aspect_type)
        harmony = "harmonious" if aspect.is_harmonious else "tense"
        # Include orb - tighter orb (closer to 0) = stronger influence
        aspects_context.append(
            f"- {user_name}'s {aspect.user_planet.title()} {aspect_verb} {connection_name}'s {aspect.their_planet.title()} | orb: {aspect.orb:.1f} | {harmony}"
        )

    # Build composite context
    composite = compatibility_data.composite
    composite_context = f"Sun in {composite.sun_sign.title()}, Moon in {composite.moon_sign.title()}"
    if composite.rising_sign:
        composite_context += f", Rising in {composite.rising_sign.title()}"
    composite_context += f" (Dominant Element: {composite.dominant_element.title()})"

    # Build karmic context - ONLY if actually karmic
    karmic = compatibility_data.karmic
    karmic_section = ""
    if karmic.is_karmic:
        karmic_aspects_text = []
        for ka in compatibility_data.karmic_aspects_internal[:3]:
            owner = user_name if ka.planet_owner == "user" else connection_name
            node_owner = connection_name if ka.node_owner == "connection" else user_name
            karmic_aspects_text.append(
                f"- {owner}'s {ka.planet} {ka.aspect_type} {node_owner}'s {ka.node} (orb: {ka.orb:.1f}) - {ka.interpretation_hint}"
            )
        karmic_context = chr(10).join(karmic_aspects_text)
        karmic_section = f"""
KARMIC STATUS:
Is Karmic: True
Theme: {karmic.theme}
{karmic_context}
"""
    # When NOT karmic, don't include karmic section at all to avoid LLM mentioning it

    # Mode-specific vibe phrase examples
    vibe_examples = {
        "romantic": "Electric, Slow Burn, Twin Flames, Magnetic Pull, Deep Waters",
        "friendship": "Ride or Die, Adventure Buddies, Soul Sisters, Low Maintenance, Kindred Spirits",
        "coworker": "Power Partners, Dream Team, Creative Tension, Complementary Skills, Empire Builders",
    }
    vibe_hint = vibe_examples.get(mode.type, vibe_examples["friendship"])

    # Mode-specific tone guidance
    mode_tone = {
        "romantic": "Focus on intimacy, passion, attraction, long-term partnership potential. Use romantic language calibrated to the label (crush = lighter, spouse = deeper).",
        "friendship": "Focus on fun, loyalty, support, shared adventures. Use platonic language - NEVER romantic terms like 'passion' or 'intimacy'.",
        "coworker": "Focus on productivity, collaboration, professional respect, career synergy. NEVER use romantic language. Frame destiny as 'professional mentorship' or 'empire building'.",
    }

    # Mode-specific guidance for interpreting North Node / South Node aspects
    # These are traditionally "karmic" points but need reframing per mode
    nodal_interpretation_tips = {
        "romantic": "North Node/South Node aspects suggest growth direction together. If is_karmic=True, you may use 'fated' or 'destined' language. If is_karmic=False, frame as 'natural growth path' or 'where you push each other forward' - avoid past-life or destiny language.",
        "friendship": "North Node/South Node aspects indicate where this friendship helps each person grow. Frame as 'growth buddies' or 'you help each other level up' - never use romantic destiny language or past-life references.",
        "coworker": "North Node/South Node aspects should be interpreted strictly as 'long-term career alignment', 'professional legacy you build together', or 'career growth direction'. NEVER use spiritual, karmic, or destiny language.",
    }

    # Extract additional chart info
    user_moon_sign = compatibility_data.user_moon_sign
    connection_moon_sign = compatibility_data.connection_moon_sign
    user_rising_sign = compatibility_data.user_rising_sign
    connection_rising_sign = compatibility_data.connection_rising_sign

    # Build chart context strings
    user_chart_info = f"Sun: {user_sun_sign.title()}, Moon: {user_moon_sign.title()}"
    if user_rising_sign != "unknown":
        user_chart_info += f", Rising: {user_rising_sign.title()}"

    connection_chart_info = f"Sun: {connection_sun_sign.title()}, Moon: {connection_moon_sign.title()}"
    if connection_rising_sign != "unknown":
        connection_chart_info += f", Rising: {connection_rising_sign.title()}"

    # Category explanations for LLM context
    category_explanations = {
        # Romantic
        "emotional": "How deeply they connect emotionally - Moon-Moon, Moon-Venus interactions",
        "communication": "How well they understand each other - Mercury aspects",
        "attraction": "Physical/romantic chemistry - Venus-Mars dynamics",
        "values": "Shared beliefs and life philosophy - Venus-Jupiter alignment",
        "longTerm": "Stability and commitment potential - Saturn aspects to personal planets",
        "growth": "How they transform each other - Pluto and North Node contacts",
        # Friendship
        "fun": "Joy and adventure together - Jupiter-Jupiter, Sun-Sun energy",
        "loyalty": "Dependability and trust - Saturn-Moon/Sun bonds",
        "sharedInterests": "Common tastes and hobbies - Venus-Venus, Mercury-Venus",
        # Coworker
        "collaboration": "Working together effectively - Sun-Mars, Mars-Mars",
        "reliability": "Professional dependability - Saturn aspects",
        "ambition": "Shared drive and goals - Mars-Saturn, Jupiter-Saturn",
        "powerDynamics": "Authority and control - Pluto-Sun, Pluto-Mars",
    }

    # Build enhanced category context with explanations
    categories_with_explanations = []
    for cat in mode.categories:
        score_label = "strong" if cat.score > 60 else "moderate" if cat.score > 30 else "challenging" if cat.score > -30 else "difficult"
        explanation = category_explanations.get(cat.id, "")
        categories_with_explanations.append(
            f"- {cat.id} ({cat.name}): {cat.score} [{score_label}]\n  What it measures: {explanation}"
        )

    prompt = f"""{voice_content}

---

# TASK: COMPATIBILITY CHART GENERATION

You are generating content for a compatibility chart that {user_name} will see in the app. This chart helps them understand what the stars say about their connection with {connection_name}.

The chart displays:
- An overall vibe/headline
- Category-by-category breakdown with insights
- Strengths and growth areas
- Actionable advice

Your job: Transform the astrological data below into warm, insightful content that helps {user_name} understand this relationship.

---

## THE TWO PEOPLE

{user_name.upper()}'S CHART: {user_chart_info}
{connection_name.upper()}'S CHART: {connection_chart_info}

## RELATIONSHIP CONTEXT

Mode: {mode.type.upper()}
{mode_tone.get(mode.type, "")}

Relationship: {relationship_category}/{relationship_label}
{f"{chr(10)}Context: {llm_guidance}" if llm_guidance else ""}

---

## COMPATIBILITY DATA

SCORE GUIDE (for your reference, never mention scores to user):
- Above 60: Strong/harmonious - natural ease
- 30 to 60: Moderate - some compatibility
- -30 to 30: Challenging - requires effort
- Below -30: Difficult - significant friction

Overall Score: {mode.overall_score}/100

CATEGORY SCORES (what each area measures):
{chr(10).join(categories_with_explanations)}

KEY ASPECTS (planetary connections creating the chemistry):
Note: Orb = how exact the aspect is. Lower orb (closer to 0) = stronger influence.
{chr(10).join(aspects_context) if aspects_context else "Basic sun sign compatibility only"}

COMPOSITE CHART (the relationship's own identity):
{composite_context}
{karmic_section}
---

## INTERPRETATION TIPS FOR THIS MODE

North Node / South Node aspects:
{nodal_interpretation_tips.get(mode.type, nodal_interpretation_tips["friendship"])}

Handling difficult scores (below -30):
For "Difficult" categories, the path forward should be about realistic boundaries and mitigation (e.g., "work independently", "keep interactions structured", "accept this isn't a natural fit") - NOT forcing harmony where it doesn't exist. Toxic positivity like "just try harder!" is worse than honest acknowledgment.

---

## OUTPUT RULES:
0. {user_name} is the main user viewing this chart. {connection_name} is the person they added.
1. Write TO {user_name} (use "you"), refer to {connection_name} by name. Example: "Sarah, you share a powerful bond with Emma"
2. vibe_phrase: Pick 1-3 words from style "{vibe_hint}" or create similar
3. headline: 5-8 words combining their signs + composite vibe
4. category_insights: For EACH category_id ({', '.join(category_ids)}), write 1-2 sentences explaining WHY
5. composite_purpose: 1-2 sentences on what this relationship is "built for"
6. destiny_note: {"Write 1-2 sentences about the fated/karmic nature of this bond" if karmic.is_karmic else "EMPTY STRING - this relationship is NOT karmic, do NOT write anything"}
7. NEVER include numeric scores in text - describe quality only
8. Frame challenges constructively. For difficult scores, suggest boundaries and mitigation, not forced harmony.
9. {"Feel free to mention the karmic/fated connection naturally in the summary or strengths" if karmic.is_karmic else "Do NOT mention karmic, fated, destiny, or past-life themes - this relationship does not have those aspects"}"""

    # Initialize Gemini client
    client = genai.Client(api_key=gemini_api_key)

    # Generate with Pydantic schema
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=CompatibilityLLMResponse
        )
    )

    generation_time_ms = int((time.time() - start_time) * 1000)

    # Parse response
    try:
        if hasattr(response, 'parsed') and response.parsed:
            llm_result = response.parsed.model_dump()
        elif response.text:
            llm_result = json.loads(response.text)
        else:
            raise ValueError("No response text")
    except Exception as e:
        # Fallback
        llm_result = {
            "headline": f"{user_sun_sign.title()} meets {connection_sun_sign.title()}",
            "summary": "Your connection has unique potential.",
            "strengths": "",
            "growth_areas": "",
            "advice": "",
            "vibe_phrase": "",
            "composite_purpose": "",
            "destiny_note": "",
            "category_insights": [],
        }

    # Convert category_insights from list to dict
    insights_dict: dict[str, str] = {}
    for item in llm_result.get("category_insights", []):
        if isinstance(item, dict) and "category_id" in item and "insight" in item:
            insights_dict[item["category_id"]] = item["insight"]

    # Build enriched categories with insights
    enriched_categories = []
    for cat in mode.categories:
        enriched_categories.append(CompatibilityCategory(
            id=cat.id,
            name=cat.name,
            score=cat.score,
            insight=insights_dict.get(cat.id),
            aspect_ids=cat.aspect_ids,  # Preserve aspect_ids from calculation
        ))

    # Build enriched mode
    enriched_mode = ModeCompatibility(
        type=mode.type,
        overall_score=mode.overall_score,
        vibe_phrase=llm_result.get("vibe_phrase"),
        categories=enriched_categories,
    )

    # Build enriched composite
    enriched_composite = Composite(
        sun_sign=composite.sun_sign,
        moon_sign=composite.moon_sign,
        rising_sign=composite.rising_sign,
        dominant_element=composite.dominant_element,
        purpose=llm_result.get("composite_purpose"),
    )

    # Build enriched karmic (only include destiny_note if actually karmic)
    destiny_note = llm_result.get("destiny_note", "") if karmic.is_karmic else None
    enriched_karmic = Karmic(
        is_karmic=karmic.is_karmic,
        theme=karmic.theme,
        destiny_note=destiny_note,
    )

    # Track with PostHog
    latency_seconds = generation_time_ms / 1000.0
    if posthog_api_key and user_id:
        try:
            capture_llm_generation(
                posthog_api_key=posthog_api_key,
                distinct_id=user_id,
                model=model_name,
                provider="gemini",
                prompt=prompt,
                response=json.dumps(llm_result),
                usage=response.usage_metadata if hasattr(response, 'usage_metadata') else None,
                latency=latency_seconds,
                generation_type="compatibility"
            )
        except Exception:
            pass

    # Debug: dump prompt and response to file (only when DEBUG_LLM is set)
    if os.environ.get("DEBUG_LLM"):
        debug_dir = Path(__file__).parent.parent / "backend_output" / "prompts"
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_path = debug_dir / f"compatibility_{relationship_category}.json"
        debug_data = {
            "relationship_category": relationship_category,
            "relationship_label": relationship_label,
            "user_name": compatibility_data.user_name,
            "connection_name": compatibility_data.connection_name,
            "is_karmic": karmic.is_karmic,
            "prompt": prompt,
            "response": llm_result,
        }
        debug_path.write_text(json.dumps(debug_data, indent=2))
        print(f"[DEBUG] Compatibility prompt dumped to {debug_path}")

    # Build final result
    return CompatibilityResult(
        headline=llm_result.get("headline", ""),
        summary=llm_result.get("summary", ""),
        strengths=llm_result.get("strengths", ""),
        growth_areas=llm_result.get("growth_areas", ""),
        advice=llm_result.get("advice", ""),
        mode=enriched_mode,
        aspects=compatibility_data.aspects,
        composite=enriched_composite,
        karmic=enriched_karmic,
        calculated_at=datetime.now().isoformat(),
        generation_time_ms=generation_time_ms,
        model_used=model_name,
    )

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
from pydantic import BaseModel
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
    AstrologicalFoundation
)
from astrometers import get_meters, daily_meters_summary, get_meter_list
from astrometers.meter_groups import build_all_meter_groups, get_group_state_label
from astrometers.summary import meter_groups_summary
from astrometers.core import AspectContribution
from moon import get_moon_transit_detail, format_moon_summary_for_llm
from posthog_utils import capture_llm_generation
import json


# Initialize Jinja2 environment
TEMPLATE_DIR = Path(__file__).parent / "templates" / "horoscope"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


# =============================================================================
# Helper Functions for iOS Astrometers Conversion
# =============================================================================

METER_NAMES = [
    "mental_clarity", "focus", "communication",
    "love", "inner_stability", "sensitivity",
    "vitality", "drive", "wellness",
    "purpose", "connection", "intuition", "creativity",
    "opportunities", "career", "growth", "social_life"
]

METER_GROUP_MAPPING = {
    "mind": ["mental_clarity", "focus", "communication"],
    "emotions": ["love", "inner_stability", "sensitivity"],
    "body": ["vitality", "drive", "wellness"],
    "spirit": ["purpose", "connection", "intuition", "creativity"],
    "growth": ["opportunities", "career", "growth", "social_life"]
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

    for group_name in ["mind", "emotions", "body", "spirit", "growth"]:
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
        if abs(aspect.tomorrow_deviation) < abs(aspect.today_deviation):
            phase = "applying"
            # Rough estimate: if orb changes by 1° per day, days = orb
            daily_change = abs(aspect.today_deviation - aspect.tomorrow_deviation)
            if daily_change > 0:
                days_to_exact = abs(aspect.today_deviation) / daily_change
        else:
            phase = "separating"
            # Already past exact
            days_to_exact = -1 * (abs(aspect.today_deviation) / (abs(aspect.tomorrow_deviation - aspect.today_deviation)))

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
    group_state_labels: dict[str, str],
    overall_state_label: str
) -> AstrometersForIOS:
    """
    Convert AllMetersReading to clean iOS-optimized structure.

    Args:
        all_meters_reading: Complete AllMetersReading object
        meter_interpretations: Dict of meter_name -> LLM interpretation
        group_interpretations: Dict of group_name -> LLM interpretation
        group_state_labels: Dict of group_name -> LLM-generated state label
        overall_state_label: LLM-generated overall state label

    Returns:
        AstrometersForIOS with complete explainability data
    """
    # Load descriptions once
    meter_descriptions = load_meter_descriptions()
    group_descriptions = load_group_descriptions()

    # Build groups
    groups = []
    all_meters_list = []

    for group_name in ["mind", "emotions", "body", "spirit", "growth"]:
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

        # Determine group quality (same logic as meter quality)
        if avg_intensity < 25:
            quality = "quiet"
        elif avg_harmony >= 70:
            quality = "harmonious"
        elif avg_harmony < 40:
            quality = "challenging"
        else:
            quality = "mixed"

        # Use LLM-generated state label (contextual, personalized to today's energy)
        state_label = group_state_labels.get(group_name, "Active")

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

    # Use LLM-generated overall state label (passed as parameter)
    overall_state = overall_state_label

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


def generate_daily_horoscope(
    date: str,
    user_profile: UserProfile,
    sun_sign_profile: SunSignProfile,
    transit_summary: dict,
    memory: MemoryCollection,
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
        api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        model_name: Model to use (default: gemini-2.5-flash-lite)

    Returns:
        DailyHoroscope: Validated horoscope with 8 core fields
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
        date=date_obj
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

    static_template = jinja_env.get_template("daily_static.j2")

    # Load detailed meter descriptions from JSON files
    meter_descriptions = load_meter_descriptions()

    # Build enriched meter list with detailed descriptions
    meter_list_enriched = []
    for meter in get_meter_list(astrometers):
        desc = meter_descriptions.get(meter.meter_name, {})
        meter_list_enriched.append({
            'meter_name': meter.meter_name,
            'display_name': meter.meter_name.replace('_', ' ').title(),
            'detailed': desc.get('detailed', f"Measures {meter.meter_name.replace('_', ' ')}")
        })

    static_prompt = static_template.render(
        meter_list=meter_list_enriched  # Pass enriched meter data with detailed descriptions
    )

    # astrometers summary is now passed separately
    dynamic_template = jinja_env.get_template("daily_dynamic.j2")
    dynamic_prompt = dynamic_template.render(
        date=date,
        user_profile=user_profile,
        sun_sign_profile=sun_sign_profile,
        transit_summary=transit_summary,  # NEW: Enhanced transit summary dict
        meters_summary=meters_summary,  # Smart filtered summary
        groups_summary=groups_summary,  # NEW: Meter groups aggregated data
        upcoming_transits=upcoming_transits_formatted,  # NEW: For look_ahead_preview (grouped by day)
        astrometers=astrometers,  # Keep for overall stats in template
        moon_summary=moon_summary_for_llm  # NEW: Comprehensive moon transit detail
    )

    # this is user specific can't be cached
    personalization_template = jinja_env.get_template("personalization.j2")
    personalization_prompt = personalization_template.render(
        user=user_profile,
        sign=sun_sign_profile,
        memory=memory,
        chart_emphasis=chart_emphasis
    )

    # Compose final
    prompt = f"{static_prompt}\n\n{personalization_prompt}\n\n{dynamic_prompt}"

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
        emotions_interpretation: str
        body_interpretation: str
        spirit_interpretation: str
        growth_interpretation: str

        # Dynamic State Labels (2-3 words, evocative)
        overall_state_label: str
        mind_state_label: str
        emotions_state_label: str
        body_state_label: str
        spirit_state_label: str
        growth_state_label: str

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
            "emotions": parsed.emotions_interpretation,
            "body": parsed.body_interpretation,
            "spirit": parsed.spirit_interpretation,
            "growth": parsed.growth_interpretation,
        }

        # Extract LLM-generated state labels (6 total: overall + 5 groups)
        group_state_labels = {
            "mind": parsed.mind_state_label,
            "emotions": parsed.emotions_state_label,
            "body": parsed.body_state_label,
            "spirit": parsed.spirit_state_label,
            "growth": parsed.growth_state_label,
        }
        overall_state_label = parsed.overall_state_label

        # Extract individual meter interpretations (17 fields)
        meter_interpretations = {
            "mental_clarity": "",
            "focus": "",
            "communication": "",
            "love": "",
            "inner_stability": "",
            "sensitivity": "",
            "vitality": "",
            "drive": "",
            "wellness": "",
            "purpose": "",
            "connection": "",
            "intuition": "",
            "creativity": "",
            "opportunities": "",
            "career": "",
            "growth": "",
            "social_life": "",
        }

        # Build iOS-optimized astrometers structure
        astrometers_for_ios = build_astrometers_for_ios(
            astrometers,
            meter_interpretations=meter_interpretations,
            group_interpretations=group_interpretations,
            group_state_labels=group_state_labels,
            overall_state_label=overall_state_label
        )

        # Populate moon_detail.interpretation with LLM output
        moon_detail.interpretation = parsed.lunar_cycle_update

        return DailyHoroscope(
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
            relationship_weather=parsed.relationship_weather,
            collective_energy=parsed.collective_energy,
            follow_up_questions=parsed.follow_up_questions,
            model_used=model_name,
            generation_time_ms=generation_time_ms,
            usage=usage
        )

    except Exception as e:
        raise RuntimeError(f"Error generating daily horoscope: {e}")

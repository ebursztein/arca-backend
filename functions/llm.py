"""
Two-prompt LLM integration for Arca Backend V1

Implements split architecture:
- Prompt 1 (daily_horoscope): Fast core analysis (<2s)
- Prompt 2 (detailed_horoscope): Deep life domain predictions (~5s)

With context caching for cost optimization.
"""

import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv

from posthog.ai.gemini import Client as PHClient
from posthog import Posthog
POSTHOG_HOST = "https://us.i.posthog.com"
load_dotenv()

TEMPERATURE = 0.7

from astro import (
    ZodiacSign,
    SunSignProfile,
    EnhancedTransitSummary,
    describe_chart_emphasis,
    lunar_house_interpretation,
    format_primary_aspect_details,
    get_upcoming_transits
)
from models import (
    DailyHoroscope,
    DetailedHoroscope,
    HoroscopeDetails,
    MemoryCollection,
    UserProfile,
    ActionableAdvice
)


# Initialize Jinja2 environment
TEMPLATE_DIR = Path(__file__).parent / "templates" / "horoscope"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def generate_daily_horoscope(
    date: str,
    user_profile: UserProfile,
    sun_sign_profile: SunSignProfile,
    transit_data: EnhancedTransitSummary,
    memory: MemoryCollection,
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
) -> DailyHoroscope:
    """
    Generate daily horoscope (Prompt 1) - core transit analysis.

    Args:
        date: ISO date string (YYYY-MM-DD)
        user_profile: Complete user profile
        sun_sign_profile: Complete sun sign profile
        transit_data: Enhanced transit summary with natal-transit aspects
        memory: User's memory collection
        api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        model_name: Model to use (default: gemini-2.5-flash)

    Returns:
        DailyHoroscope: Validated horoscope with 8 core fields
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not found")

    # client = genai.Client(api_key=api_key)
    _POSTHOG_API_KEY = os.environ.get("POSTHOG_API_KEY")
    posthog = Posthog(_POSTHOG_API_KEY, host=POSTHOG_HOST)
    client = PHClient(api_key=api_key, posthog_client=posthog)

    # Prepare helper data
    chart_emphasis = describe_chart_emphasis(user_profile.natal_chart['distributions'])
    lunar_moon_interpretation = lunar_house_interpretation(transit_data.moon_house)
    primary_aspect_formatted = None
    if transit_data.primary_aspect:
        primary_aspect_formatted = format_primary_aspect_details(transit_data.primary_aspect)

    # Render templates valid for 24 hours
    static_template = jinja_env.get_template("daily_static.j2")
    static_prompt = static_template.render()

    dynamic_template = jinja_env.get_template("daily_dynamic.j2")
    dynamic_prompt = dynamic_template.render(
        date=date,
        transits=transit_data,
        lunar_moon_interpretation=lunar_moon_interpretation,
        primary_aspect_formatted=primary_aspect_formatted
    )

    daily_prompt = f"{static_prompt}\n\n{dynamic_prompt}"

    print("\n\n--- Daily Prompt ---\n")
    print(daily_prompt)
    print("\n--- End of Daily Prompt ---\n\n")

    # fixme cache dynamic + static
    cache_content = None

    # this is user specific can't be cached
    personalization_template = jinja_env.get_template("personalization.j2")
    personalization_prompt = personalization_template.render(
        user=user_profile,
        sign=sun_sign_profile,
        memory=memory,
        chart_emphasis=chart_emphasis
    )

    # Compose final prompt
    prompt = f"{daily_prompt}\n\n{personalization_prompt}"

    # console.print(f"\n[yellow]Generated Daily Horoscope Prompt:[/yellow]")
    # console.print(prompt)
    # console.print("\n[yellow]End of Prompt[/yellow]\n")

    # Define response schema
    class DailyHoroscopeResponse(BaseModel):
        technical_analysis: str
        key_active_transit: str
        area_of_life_activated: str
        lunar_cycle_update: str
        daily_theme_headline: str
        daily_overview: str
        summary: str
        actionable_advice: ActionableAdvice

    # Generate
    try:
        start_time = datetime.now()

        config = types.GenerateContentConfig(
            temperature=TEMPERATURE,
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            response_mime_type="application/json",
            response_schema=DailyHoroscopeResponse,
            cached_content=cache_content if cache_content else None
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
            # posthog specific metadata
            posthog_distinct_id=user_profile.user_id, # optional
            posthog_properties={"generation_type": "daily_horoscope"} # optional

        )

        generation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        usage = response.usage_metadata.model_dump() if response.usage_metadata else {}
        parsed: DailyHoroscopeResponse = response.parsed

        # Shutdown PostHog client to flush events as we're in a serverless environment
        posthog.shutdown()

        return DailyHoroscope(
            date=date,
            sun_sign=user_profile.sun_sign,
            technical_analysis=parsed.technical_analysis,
            key_active_transit=parsed.key_active_transit,
            area_of_life_activated=parsed.area_of_life_activated,
            lunar_cycle_update=parsed.lunar_cycle_update,
            daily_theme_headline=parsed.daily_theme_headline,
            daily_overview=parsed.daily_overview,
            summary=parsed.summary,
            actionable_advice=parsed.actionable_advice,
            model_used=model_name,
            generation_time_ms=generation_time_ms,
            usage=usage
        )

    except Exception as e:
        raise RuntimeError(f"Error generating daily horoscope: {e}")


def generate_detailed_horoscope(
    date: str,
    user_profile: UserProfile,
    sun_sign_profile: SunSignProfile,
    transit_data: EnhancedTransitSummary,
    memory: MemoryCollection,
    daily_horoscope: DailyHoroscope,
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
) -> DetailedHoroscope:
    """
    Generate detailed horoscope (Prompt 2) - life domain predictions.

    Args:
        date: ISO date string (YYYY-MM-DD)
        user_profile: Complete user profile
        sun_sign_profile: Complete sun sign profile
        transit_data: Enhanced transit summary
        memory: User's memory collection
        daily_horoscope: Result from Prompt 1 (foundation)
        api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        model_name: Model to use (default: gemini-2.5-flash)

    Returns:
        DetailedHoroscope: Validated horoscope with 8 life categories
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not found")

    # client = genai.Client(api_key=api_key)
    _POSTHOG_API_KEY = os.environ.get("POSTHOG_API_KEY")
    posthog = Posthog(_POSTHOG_API_KEY, host=POSTHOG_HOST)
    client = PHClient(api_key=api_key, posthog_client=posthog)

    # Get upcoming transits
    upcoming_transits = get_upcoming_transits(user_profile.natal_chart, date, days_ahead=5)

    # Prepare helper data
    chart_emphasis = describe_chart_emphasis(user_profile.natal_chart['distributions'])

    # Render templates
    static_template = jinja_env.get_template("detailed_static.j2")
    static_prompt = static_template.render()

    # FIXME caching here - use generic function
    cached_content = None

    # FIXME: part of the dynamic prompt that can be cached as it is related to all user
    # must be moved to static prompt
    dynamic_template = jinja_env.get_template("detailed_dynamic.j2")
    dynamic_prompt = dynamic_template.render(
        date=date,
        daily_horoscope=daily_horoscope,
        transits=transit_data,
        upcoming_transits=upcoming_transits
    )

    # fixme use _render_personalization_prompt as it is used cross function
    personalization_template = jinja_env.get_template("personalization.j2")
    personalization_prompt = personalization_template.render(
        user=user_profile,
        sign=sun_sign_profile,
        memory=memory,
        chart_emphasis=chart_emphasis
    )

    # Compose final prompt
    prompt = f"{static_prompt}\n\n{dynamic_prompt}\n\n{personalization_prompt}"

    # console.print(f"\n[yellow]Generated Detailed Horoscope Prompt:[/yellow]")
    # console.print(prompt)
    # console.print("\n[yellow]End of Prompt[/yellow]\n")
    # Define response schema
    class DetailedHoroscopeResponse(BaseModel):
        general_transits_overview: list[str]
        look_ahead_preview: str
        details: HoroscopeDetails

    # Generate
    try:
        start_time = datetime.now()

        config = types.GenerateContentConfig(
            temperature=TEMPERATURE,
            max_output_tokens=8192,
            response_mime_type="application/json",
            response_schema=DetailedHoroscopeResponse,
            cached_content=cached_content if cached_content else None,
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
            posthog_distinct_id=user_profile.user_id, # optional
            posthog_properties={"generation_type": "detailed_horoscope"} # optional
        )

        generation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        usage = response.usage_metadata.model_dump() if response.usage_metadata else {}
        parsed: DetailedHoroscopeResponse = response.parsed

        # Shutdown PostHog client to flush events as we're in a serverless environment
        posthog.shutdown()

        return DetailedHoroscope(
            general_transits_overview=parsed.general_transits_overview,
            look_ahead_preview=parsed.look_ahead_preview,
            details=parsed.details,
            model_used=model_name,
            generation_time_ms=generation_time_ms,
            usage=usage
        )

    except Exception as e:
        raise RuntimeError(f"Error generating detailed horoscope: {e}")


# Cache management functions
# FIXME use a single cache function
# def create_daily_static_cache(
#     date: str,
#     model_name: str = "gemini-2.5-flash",
#     api_key: Optional[str] = None,
#     ttl: str = "86400s"  # 24 hours
# ) -> Optional[str]:
#     """
#     Create cache for daily horoscope static instructions (Prompt 1).

#     Args:
#         date: ISO date string (YYYY-MM-DD) - used as cache key prefix
#         model_name: Model version (must include version suffix)
#         api_key: Gemini API key
#         ttl: Time to live (default: 24 hours)

#     Returns:
#         Cache name for use in generate_daily_horoscope
#     """
#     return None  # Disable caching for now
#     if not api_key:
#         api_key = os.environ.get("GEMINI_API_KEY")
#     if not api_key:
#         raise ValueError("GEMINI_API_KEY environment variable not found")

#     client = genai.Client(api_key=api_key)

#     # Check if cache already exists for this date
#     cache_display_name = f"arca-daily-static-{date}-{model_name}"
#     for existing_cache in client.caches.list():
#         if existing_cache.display_name == cache_display_name:
#             return existing_cache.name

#     # Render daily static template
#     daily_static = jinja_env.get_template("daily_static.j2").render()

#     # Check token count (min 1024 for caching, use 2000 token safety margin)
#     # Rough estimate: 1 token ~= 3-4 chars
#     if len(daily_static) < 6000:  # ~2000 tokens minimum for safety
#         return None  # Skip caching if too small

#     cache = client.caches.create(
#         model=f"models/{model_name}",
#         config=types.CreateCachedContentConfig(
#             display_name=cache_display_name,
#             system_instruction=daily_static,
#             ttl=ttl
#         )
#     )

#     return cache.name



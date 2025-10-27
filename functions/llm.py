"""
Two-prompt LLM integration for Arca Backend V1

Implements split architecture:
- Prompt 1 (daily_horoscope): Fast core analysis (<2s)
- Prompt 2 (detailed_horoscope): Deep life domain predictions (~5s)

With context caching for cost optimization.
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
    EnhancedTransitSummary,
    describe_chart_emphasis,
    lunar_house_interpretation,
    format_primary_aspect_details,
    get_upcoming_transits,
    compute_birth_chart
)
from models import (
    DailyHoroscope,
    DetailedHoroscope,
    HoroscopeDetails,
    MemoryCollection,
    UserProfile,
    ActionableAdvice
)
from astrometers import get_meters, group_meters_by_domain


# Initialize Jinja2 environment
TEMPLATE_DIR = Path(__file__).parent / "templates" / "horoscope"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def capture_llm_generation(
    posthog_api_key: str,
    distinct_id: str,
    model: str,
    provider: str,
    prompt: str,
    response: str,
    usage: GenerateContentResponseUsageMetadata | None,
    latency: float,
    generation_type: str,
    temperature: float = 0,
    max_tokens: int = 0,
    thinking_budget: int = 0,
):
    """
    Manually capture LLM generation event to PostHog using HTTP API.

    Args:
        posthog_api_key: PostHog project API key
        distinct_id: User's distinct ID
        model: Model name (e.g., "gemini-2.5-flash")
        provider: Provider name (e.g., "gemini")
        prompt: prompt messages
        output: model output
        usage: UsageMetadata object from Gemini response for token counts
        latency: Latency in seconds
        generation_type: Custom property for generation type
        temperature: Temperature parameter
        max_tokens: Max tokens parameter
        thinking_budget: Thinking budget parameter
    """
    POSTHOG_HOST = "https://us.i.posthog.com"

    # cleanup API key
    posthog_api_key = posthog_api_key.replace("\n", '')
    posthog_api_key = posthog_api_key.replace('"', '').replace("'", '').strip()

    # parse usage
    input_tokens = 0
    output_tokens = 0
    cached_tokens = 0
    if usage:
        # cached tokens
        if usage.cached_content_token_count:
            cached_tokens = usage.cached_content_token_count
        # input tokens
        if usage.prompt_token_count:
            input_tokens += usage.prompt_token_count

        # output tokens need to include candidates + thoughts
        if usage.thoughts_token_count:
            input_tokens += usage.thoughts_token_count
        if usage.candidates_token_count:
            output_tokens = usage.candidates_token_count

    # format messages
    input_messages=[{"role": "user",
                     "content": [{"type": "text", "text": prompt[:1000]}]  # Truncate for readability
                 }],

    output_messages=[{"role": "assistant",
                      "content": [{"type": "text", "text": response[:1000]}]  # Truncate for readability
                  }],



    try:
        # Build properties with distinct_id inside
        properties = {
            "distinct_id": distinct_id,
            "$ai_trace_id": str(uuid.uuid4()),
            "$ai_span_name": generation_type,
            "$ai_model": model,
            "$ai_provider": provider,
            "$ai_input": input_messages,
            "$ai_input_tokens": input_tokens,
            "$ai_output_choices": output_messages,
            "$ai_output_tokens": output_tokens,
            "$ai_cache_read_input_tokens": cached_tokens,
            "$ai_latency": latency,
            "$ai_http_status": 200,
            "$ai_is_error": False,

            # additional parameters
            "thinking_budget": thinking_budget,
            "generation_type": generation_type,
        }

        # Add optional parameters
        if temperature is not None:
            properties["$ai_temperature"] = temperature
        if max_tokens is not None:
            properties["$ai_max_tokens"] = max_tokens

        # PostHog event format
        # Use UTC time with Z suffix and no microseconds (or milliseconds only)
        utc_now = datetime.utcnow()
        timestamp = utc_now.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

        event_data = {
            "api_key": posthog_api_key,
            "event": "$ai_generation",
            "properties": properties,
            "timestamp": timestamp
        }
        print(f"[PostHog]LLM generation User: {distinct_id} | Type: {generation_type} | Tokens: {input_tokens}→{output_tokens}")

        # Send to PostHog event endpoint
        resp = httpx.post(
            f"{POSTHOG_HOST}/i/v0/e/",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=5.0
        )
        # from rich.console import Console
        # console = Console()
        # console.print(event_data)
        # console.print("[PostHog]LLM generation response:")
        # console.print(resp)

        # print(f"[PostHog] Response: {resp.status_code}: {resp.text}")

        if resp.status_code == 200:
            print("✓ PostHog event captured successfully")
        else:
            print(f"⚠ PostHog failed: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"⚠ PostHog error: {e}")
        import traceback
        traceback.print_exc()


def generate_daily_horoscope(
    date: str,
    user_profile: UserProfile,
    sun_sign_profile: SunSignProfile,
    transit_data: EnhancedTransitSummary,
    memory: MemoryCollection,
    api_key: Optional[str] = None,
    posthog_api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
) -> DailyHoroscope:
    """
    Generate daily horoscope (Prompt 1) - core transit analysis (async internal).

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

    # Calculate astrometers
    from datetime import datetime as dt
    date_obj = dt.fromisoformat(date) if isinstance(date, str) else date
    astrometers = get_meters(
        natal_chart=user_profile.natal_chart,
        transit_chart=transit_chart,
        date=date_obj
    )

    # Group meters by domain
    domain_meters = group_meters_by_domain(astrometers)

    # Prepare helper data
    chart_emphasis = describe_chart_emphasis(user_profile.natal_chart['distributions'])
    lunar_moon_interpretation = lunar_house_interpretation(transit_data.moon_house)

    # Get moon sign profile for emotional description
    from astro import get_sun_sign_profile
    moon_sign_profile = get_sun_sign_profile(transit_data.moon_sign)
    moon_sign_keywords = ", ".join(moon_sign_profile.keywords[:3]).lower() if moon_sign_profile else "emotional coloring"

    # Render templates valid for 24 hours
    static_template = jinja_env.get_template("daily_static.j2")
    static_prompt = static_template.render()

    dynamic_template = jinja_env.get_template("daily_dynamic.j2")
    dynamic_prompt = dynamic_template.render(
        date=date,
        transits=transit_data,
        lunar_moon_interpretation=lunar_moon_interpretation,
        moon_sign_emotional_description=moon_sign_keywords,
        astrometers=astrometers,
        domain_meters=domain_meters
    )

    daily_prompt = f"{static_prompt}\n\n{dynamic_prompt}"

    # print("\n\n--- Daily Prompt ---\n")
    # print(daily_prompt)
    # print("\n--- End of Daily Prompt ---\n\n")

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

        print(f"[generate_daily_horoscope]Model:{model_name} Time:{generation_time_ms}ms Usage:{usage}")

        # Manually capture to PostHog using HTTP API
        output = f"Headline: {parsed.daily_theme_headline}\nOverview: {parsed.daily_overview}\nSummary: {parsed.summary}"
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

        return DailyHoroscope(
            date=date,
            sun_sign=user_profile.sun_sign,
            technical_analysis=parsed.technical_analysis,
            lunar_cycle_update=parsed.lunar_cycle_update,
            daily_theme_headline=parsed.daily_theme_headline,
            daily_overview=parsed.daily_overview,
            summary=parsed.summary,
            actionable_advice=parsed.actionable_advice,
            astrometers=astrometers,
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
    posthog_api_key: Optional[str] = None,
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
    THINKING_BUDGET = 0
    MAX_TOKENS = 8192

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not provided")

    if not posthog_api_key:
        posthog_api_key = os.environ.get("POSTHOG_API_KEY")
    if not posthog_api_key:
        print("WARNING: POSTHOG_API_KEY not provided in generate_detailed_horoscope")
        raise ValueError("POSTHOG_API_KEY not provided")

    # Initialize Gemini client (direct, no SDK wrapper)
    client = genai.Client(api_key=api_key)

    # Get astrometers from daily horoscope and group by domain
    astrometers = daily_horoscope.astrometers
    domain_meters = group_meters_by_domain(astrometers)

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
        group_meters=domain_meters,
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
            max_output_tokens=MAX_TOKENS,
            response_mime_type="application/json",
            response_schema=DetailedHoroscopeResponse,
            thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
            cached_content=cached_content if cached_content else None,
        )

        # Direct Gemini call (no SDK wrapper)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )

        generation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        usage = response.usage_metadata.model_dump() if response.usage_metadata else {}
        parsed: DetailedHoroscopeResponse = response.parsed

        print(f"[generate_detailed_horoscope]Model:{model_name} Time:{generation_time_ms}ms Usage:{usage}")

        # Manually capture to PostHog using HTTP API
        response_output = parsed.look_ahead_preview
        capture_llm_generation(
            posthog_api_key=posthog_api_key,
            distinct_id=user_profile.user_id,
            model=model_name,
            provider="gemini",
            prompt=prompt,
            response=response_output,
            usage=response.usage_metadata,
            latency=generation_time_ms / 1000.0,
            generation_type="detailed_horoscope",
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            thinking_budget=THINKING_BUDGET
        )
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



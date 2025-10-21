"""
LLM integration for Arca Backend V1

Handles:
- Jinja2 prompt template rendering
- Gemini API client initialization
- Horoscope generation with structured output
- Token tracking and analytics
"""

import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch
from pydantic import BaseModel

from astro import (
    ZodiacSign,
    SunSignProfile,
    EnhancedTransitSummary,
    UpcomingTransit,
    describe_chart_emphasis,
    lunar_house_interpretation,
    format_primary_aspect_details,
    get_upcoming_transits
)
from models import (
    DailyHoroscope,
    DetailedHoroscope,
    CompleteHoroscope,
    HoroscopeDetails,
    MemoryCollection,
    UserProfile,
    ActionableAdvice
)


# Initialize Jinja2 environment
TEMPLATE_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


def generate_horoscope(
    date: str,
    user_profile: UserProfile,
    sun_sign_profile: SunSignProfile,
    transit_data: EnhancedTransitSummary,
    memory: MemoryCollection,
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash"
) -> CompleteHoroscope:
    """
    Generate personalized daily horoscope using Gemini API.

    This function:
    1. Renders the Jinja2 prompt template with user data
    2. Calls Gemini API with structured JSON output
    3. Validates and returns a DailyHoroscope Pydantic model

    Args:
        date: ISO date string (YYYY-MM-DD)
        user_profile: Complete user profile (name, birth info, natal chart)
        sun_sign_profile: Complete sun sign profile with element, modality, etc.
        transit_data: Enhanced transit summary with natal-transit aspects, lunar phase, etc.
        memory: User's memory collection for personalization
        api_key: Gemini API key (defaults to GEMINI_API_KEY env var)

    Returns:
        CompleteHoroscope: Validated horoscope with all 8 life categories

    Raises:
        ValueError: If API key is missing or response is invalid
        RuntimeError: If API call fails
    """

    # Get API key
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not found")

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    # Prepare helper data for template
    chart_emphasis = describe_chart_emphasis(user_profile.natal_chart['distributions'])
    lunar_moon_interpretation = lunar_house_interpretation(transit_data.moon_house)

    # Format primary aspect if present
    primary_aspect_formatted = None
    if transit_data.primary_aspect:
        primary_aspect_formatted = format_primary_aspect_details(transit_data.primary_aspect)

    # Get upcoming transits for look-ahead
    upcoming_transits = get_upcoming_transits(user_profile.natal_chart, date, days_ahead=5)

    # Load and render Jinja2 template
    template = jinja_env.get_template("horoscope_prompt.j2")

    # Pass full Pydantic models and helper data to template
    prompt = template.render(
        date=date,
        user=user_profile,
        sign=sun_sign_profile,
        transits=transit_data,
        memory=memory,
        chart_emphasis=chart_emphasis,
        lunar_moon_interpretation=lunar_moon_interpretation,
        primary_aspect_formatted=primary_aspect_formatted,
        upcoming_transits=upcoming_transits
    )

    # Define structured output schema using Pydantic models
    # Create a response schema that matches what the LLM should return
    class HoroscopeResponse(BaseModel):
        """Structured schema for LLM horoscope response."""
        daily_theme_headline: str
        daily_overview: str
        key_active_transit: str
        area_of_life_activated: str
        actionable_advice: ActionableAdvice
        lunar_cycle_update: str
        general_transits_overview: list[str]
        look_ahead_preview: str
        technical_analysis: str
        summary: str
        details: HoroscopeDetails

    # Generate horoscope with Gemini using structured output
    try:
        start_time = datetime.now()

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
                "response_schema": HoroscopeResponse,
            }
        )

        generation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # usage data
        if response.usage_metadata:
            usage = response.usage_metadata.model_dump()
        else:
            usage = {}

        # Access the parsed Pydantic object directly from response
        parsed_response: HoroscopeResponse = response.parsed

        # Return validated Pydantic model with enhanced fields
        horoscope = CompleteHoroscope(
            date=date,
            sun_sign=user_profile.sun_sign,
            technical_analysis=parsed_response.technical_analysis,
            summary=parsed_response.summary,
            daily_theme_headline=parsed_response.daily_theme_headline,
            daily_overview=parsed_response.daily_overview,
            key_active_transit=parsed_response.key_active_transit,
            area_of_life_activated=parsed_response.area_of_life_activated,
            actionable_advice=parsed_response.actionable_advice,
            lunar_cycle_update=parsed_response.lunar_cycle_update,
            general_transits_overview=parsed_response.general_transits_overview,
            look_ahead_preview=parsed_response.look_ahead_preview,
            details=parsed_response.details,
            model_used=model_name,
            generation_time_ms=generation_time_ms,
            usage=usage
        )

        return horoscope

    except Exception as e:
        raise RuntimeError(f"Error generating horoscope: {e}")

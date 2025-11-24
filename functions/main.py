# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn, options, firestore_fn, params
from firebase_admin import initialize_app, firestore
from datetime import datetime
from typing import Optional

from astro import (
    get_astro_chart,
    compute_birth_chart,
    get_sun_sign,
    get_sun_sign_profile,
    format_transit_summary_for_ui,
    synthesize_critical_degrees,
    synthesize_transit_themes,
    get_house_context,
    ChartType,
)
from models import (
    UserProfile,
    MemoryCollection,
    create_empty_memory,
)
from llm import generate_daily_horoscope

# Define secrets
GEMINI_API_KEY = params.SecretParam("GEMINI_API_KEY")
POSTHOG_API_KEY = params.SecretParam("POSTHOG_API_KEY")

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
options.set_global_options(max_instances=200)

# default LLM model
DEFAULT_MODEL = "gemini-2.5-flash-lite"

# Set default database name for Firestore client
# ! don't know how to change it -- the firestore.json don't sees to work
DATABASE_ID = "(default)"

# Initialize Firebase app (but only if not already initialized)
initialize_app()

@https_fn.on_call()
def natal_chart(req: https_fn.CallableRequest) -> dict:
    """
    Generate a natal (birth) chart.

    Callable from iOS app via Firebase SDK.

    Expected request data:
    {
        "utc_dt": "1980-04-20 06:30",  // UTC datetime string
        "lat": 25.0531,                 // Latitude
        "lon": 121.526                  // Longitude
    }

    Returns:
        Complete natal chart data as a dictionary
    """
    try:
        # Extract parameters from request
        data = req.data
        utc_dt = data.get("utc_dt")
        lat = data.get("lat")
        lon = data.get("lon")

        # Validate required parameters
        if not utc_dt or lat is None or lon is None:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: utc_dt, lat, lon"
            )

        # Generate natal chart
        chart = get_astro_chart(
            utc_dt=utc_dt,
            lat=float(lat),
            lon=float(lon),
            chart_type=ChartType.NATAL
        )

        # Return as dictionary
        return chart.model_dump()

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"Invalid parameter values: {str(e)}"
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error generating natal chart: {str(e)}"
        )


@https_fn.on_call()
def daily_transit(req: https_fn.CallableRequest) -> dict:
    """
    TIER 1: Generate daily transit chart (universal, no location).

    This should be cached and computed once per day at midnight UTC.
    Returns planetary positions and aspects without house placements.

    Callable from iOS app via Firebase SDK.

    Expected request data:
    {
        "utc_dt": "2025-10-16 00:00"  // Optional, defaults to today midnight UTC
    }

    Returns:
        Transit chart data with planets and aspects (houses will be at 0,0)
    """
    try:
        # Extract parameters from request
        data = req.data

        # Use provided datetime or default to today at midnight UTC
        utc_dt = data.get("utc_dt")
        if not utc_dt:
            # Get today's date at midnight UTC
            now = datetime.utcnow()
            utc_dt = f"{now.year:04d}-{now.month:02d}-{now.day:02d} 00:00"

        # Generate transit chart at reference location (0, 0)
        # Houses won't be meaningful, but planetary positions and aspects will be
        chart = get_astro_chart(
            utc_dt=utc_dt,
            lat=0.0,
            lon=0.0,
            chart_type=ChartType.TRANSIT
        )

        # Return as dictionary
        # Note: Caller should cache this for the day
        return chart.model_dump()

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"Invalid parameter values: {str(e)}"
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error generating daily transit: {str(e)}"
        )


@https_fn.on_call()
def user_transit(req: https_fn.CallableRequest) -> dict:
    """
    TIER 2: Generate user-specific transit chart overlay.

    Combines universal daily transits with user's natal chart location
    to provide personalized house placements.

    This can be cached per user per day.

    Callable from iOS app via Firebase SDK.

    Expected request data:
    {
        "utc_dt": "2025-10-16 18:30",  // Optional, defaults to now
        "birth_lat": 25.0531,           // User's birth latitude
        "birth_lon": 121.526            // User's birth longitude
    }

    Returns:
        Transit chart data with houses relative to user's natal chart location
    """
    try:
        # Extract parameters from request
        data = req.data
        birth_lat = data.get("birth_lat")
        birth_lon = data.get("birth_lon")

        # Validate required parameters
        if birth_lat is None or birth_lon is None:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: birth_lat, birth_lon"
            )

        # Use provided datetime or default to now
        utc_dt = data.get("utc_dt")
        if not utc_dt:
            # Generate current UTC datetime
            now = datetime.utcnow()
            utc_dt = f"{now.year:04d}-{now.month:02d}-{now.day:02d} {now.hour:02d}:{now.minute:02d}"

        # Generate transit chart using user's birth location
        # This gives transit planets in houses relative to their natal chart
        chart = get_astro_chart(
            utc_dt=utc_dt,
            lat=float(birth_lat),
            lon=float(birth_lon),
            chart_type=ChartType.TRANSIT
        )

        # Return as dictionary
        return chart.model_dump()

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"Invalid parameter values: {str(e)}"
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error generating user transit: {str(e)}"
        )

@https_fn.on_call()
def create_user_profile(req: https_fn.CallableRequest) -> dict:
    """
    Create user profile with birth chart computation.

    Supports V1 (minimal) and V2 (full birth data) modes:
    - V1: Only birth_date required → sun sign + approximate chart
    - V2: Full birth info → precise natal chart with houses

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "name": "User Name",
        "email": "user@example.com",
        "birth_date": "1990-06-15",  // YYYY-MM-DD (REQUIRED)

        // Optional V2 fields for precise chart:
        "birth_time": "14:30",  // HH:MM (optional)
        "birth_timezone": "America/New_York",  // IANA timezone (optional)
        "birth_lat": 40.7128,  // Latitude (optional)
        "birth_lon": -74.0060  // Longitude (optional)
    }

    Returns:
    {
        "success": true,
        "user_id": "firebase_auth_id",
        "sun_sign": "gemini",
        "exact_chart": false,  // true if all birth info provided
        "mode": "v1"  // "v1" or "v2"
    }
    """
    try:
        data = req.data

        # Required fields (V1 minimum)
        user_id = data.get("user_id")
        name = data.get("name")
        email = data.get("email")
        birth_date = data.get("birth_date")

        if not all([user_id, name, email, birth_date]):
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required fields: user_id, name, email, birth_date"
            )

        # Optional fields (V2 for precise chart)
        birth_time = data.get("birth_time")
        birth_timezone = data.get("birth_timezone")
        birth_lat = data.get("birth_lat")
        birth_lon = data.get("birth_lon")

        # Calculate sun sign (always works with just birth_date)
        sun_sign = get_sun_sign(birth_date)

        # Compute birth chart (handles both V1 and V2 modes)
        natal_chart, exact_chart = compute_birth_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_timezone=birth_timezone,
            birth_lat=birth_lat,
            birth_lon=birth_lon
        )

        # Determine mode
        has_full_info = all([birth_time, birth_timezone, birth_lat, birth_lon])
        mode = "v2" if has_full_info else "v1"

        # Create timestamps
        now = datetime.now().isoformat()

        # Create user profile (Pydantic validates)
        user_profile = UserProfile(
            user_id=user_id,
            name=name,
            email=email,
            is_premium=False,  # Default to non-premium
            premium_expiry=None,
            birth_date=birth_date,
            birth_time=birth_time,
            birth_timezone=birth_timezone,
            birth_lat=birth_lat,
            birth_lon=birth_lon,
            sun_sign=sun_sign.value,
            natal_chart=natal_chart,
            exact_chart=exact_chart,
            created_at=now,
            last_active=now
        )

        # Save to Firestore
        db = firestore.client(database_id=DATABASE_ID)
        db.collection("users").document(user_id).set(user_profile.model_dump())

        # Initialize empty memory collection
        memory = create_empty_memory(user_id)
        db.collection("memory").document(user_id).set(memory.model_dump())

        return {
            "success": True,
            "user_id": user_id,
            "sun_sign": sun_sign.value,
            "exact_chart": exact_chart,
            "mode": mode
        }

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"Invalid parameter values: {str(e)}"
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error creating user profile: {str(e)}"
        )


@https_fn.on_call()
def get_user_profile(req: https_fn.CallableRequest) -> dict:
    """
    Get user profile from Firestore.

    Expected request data:
    {
        "user_id": "firebase_auth_id"
    }

    Returns:
        Complete user profile dictionary or error if not found
    """
    try:
        data = req.data
        user_id = data.get("user_id")

        if not user_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameter: user_id"
            )

        db = firestore.client(database_id=DATABASE_ID)
        doc = db.collection("users").document(user_id).get()

        if not doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"User profile not found: {user_id}"
            )

        # Update last_active timestamp
        db.collection("users").document(user_id).update({
            "last_active": datetime.now().isoformat()
        })

        return doc.to_dict()

    except https_fn.HttpsError:
        raise
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error retrieving user profile: {str(e)}"
        )


@https_fn.on_call()
def get_memory(req: https_fn.CallableRequest) -> dict:
    """
    Get memory collection for a user (for LLM personalization).

    Expected request data:
    {
        "user_id": "firebase_auth_id"
    }

    Returns:
        Memory collection dictionary
    """
    try:
        data = req.data
        user_id = data.get("user_id")

        if not user_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameter: user_id"
            )

        db = firestore.client(database_id=DATABASE_ID)
        doc = db.collection("memory").document(user_id).get()

        if not doc.exists:
            # Return empty memory if doesn't exist yet
            memory = create_empty_memory(user_id)
            return memory.model_dump()

        return doc.to_dict()

    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error retrieving memory: {str(e)}"
        )


@https_fn.on_call()
def add_journal_entry(req: https_fn.CallableRequest) -> dict:
    """
    Create a journal entry when user reads their horoscope.

    Memory updates happen automatically via Firestore trigger.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "date": "2025-10-18",  // ISO date
        "entry_type": "horoscope_reading",
        "summary_viewed": "Today's summary text",
        "categories_viewed": [
            {
                "category": "mind",  // Valid values: "overview", "mind", "emotions", "body", "career", "evolution", "elements", "spiritual", "collective"
                "text": "Full text that was read..."
            }
        ],
        "time_spent_seconds": 180
    }

    Returns:
    {
        "success": true,
        "entry_id": "auto_generated_id"
    }
    """
    try:
        data = req.data
        user_id = data.get("user_id")

        if not user_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameter: user_id"
            )

        # Create journal entry data (Pydantic will validate)
        entry_data = {
            "entry_id": "temp",  # Will be replaced with Firestore ID
            "date": data.get("date"),
            "entry_type": data.get("entry_type"),
            "summary_viewed": data.get("summary_viewed"),
            "categories_viewed": data.get("categories_viewed", []),
            "time_spent_seconds": data.get("time_spent_seconds", 0),
            "created_at": datetime.now().isoformat()
        }

        # Validate with Pydantic
        journal_entry = JournalEntry(**entry_data)

        # Save to Firestore (auto-generate ID)
        db = firestore.client(database_id=DATABASE_ID)
        collection_ref = db.collection("users").document(user_id).collection("journal")
        doc_ref = collection_ref.document()
        entry_id = doc_ref.id

        # Update entry_id
        entry_dict = journal_entry.model_dump()
        entry_dict["entry_id"] = entry_id

        doc_ref.set(entry_dict)

        # Note: Firestore trigger will automatically update memory collection

        return {
            "success": True,
            "entry_id": entry_id
        }

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"Invalid journal entry data: {str(e)}"
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error creating journal entry: {str(e)}"
        )

@https_fn.on_call()
def get_sun_sign_from_date(req: https_fn.CallableRequest) -> dict:
    """
    Get sun sign from birth date.

    Simple utility for onboarding flow before full profile creation.

    Expected request data:
    {
        "birth_date": "1990-06-15"  // YYYY-MM-DD
    }

    Returns:
    {
        "sun_sign": "gemini",
        "element": "air",
        "modality": "mutable",
        "ruling_planet": "Mercury",
        "keywords": ["communication", "versatile", "curious", "social", "adaptable"],
        "summary": "Gemini, the third sign of the zodiac..."
    }
    """
    try:
        data = req.data
        birth_date = data.get("birth_date")

        if not birth_date:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameter: birth_date"
            )

        # Calculate sun sign
        sun_sign = get_sun_sign(birth_date)

        # Get sun sign profile
        sun_sign_profile = get_sun_sign_profile(sun_sign)

        if not sun_sign_profile:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INTERNAL,
                message=f"Sun sign profile not found: {sun_sign.value}"
            )

        # Return complete sun sign profile
        return {
            "sun_sign": sun_sign.value,
            "profile": sun_sign_profile.model_dump()
        }

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"Invalid birth date: {str(e)}"
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error calculating sun sign: {str(e)}"
        )

# The function run out of memory at 256MB, so increased to 512MB
@https_fn.on_call(memory=512, secrets=[GEMINI_API_KEY, POSTHOG_API_KEY])
def get_daily_horoscope(req: https_fn.CallableRequest) -> dict:
    """
    Generate daily horoscope - complete reading with meter groups.

    Includes:
    - Core fields: technical_analysis, daily_theme_headline, daily_overview,
                   summary, actionable_advice, lunar_cycle_update
    - Meter groups: 5 life areas (mind, emotions, body, spirit, growth) with
                    aggregated scores and LLM interpretations
    - Look ahead: Upcoming transits preview (next 7 days)
    - Astrometers: Complete 28-meter reading

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "date": "2025-10-18",  // Optional, defaults to today
    }

    Returns:
        DailyHoroscope model as dictionary
    """
    try:
        data = req.data
        user_id = data.get("user_id")

        if not user_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameter: user_id"
            )

        # Optional parameters
        date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        model_name = DEFAULT_MODEL

        # Get user profile from Firestore
        db = firestore.client(database_id=DATABASE_ID)
        user_doc = db.collection("users").document(user_id).get()

        if not user_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"User profile not found: {user_id}"
            )

        user_data = user_doc.to_dict()
        user_profile = UserProfile(**user_data)

        # Get sun sign profile
        sun_sign = get_sun_sign(user_profile.birth_date)
        sun_sign_profile = get_sun_sign_profile(sun_sign)

        if not sun_sign_profile:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INTERNAL,
                message=f"Sun sign profile not found: {sun_sign.value}"
            )

        # Memory collection: Using empty memory for all users
        memory = create_empty_memory(user_id)

        # Compute transit chart for today
        transit_chart, _ = compute_birth_chart(
            birth_date=date,
            birth_time="12:00"  # Use noon for transits
        )

        # Get natal chart from user profile
        natal_chart = user_profile.natal_chart

        # Generate enhanced transit data with natal-transit aspects
        transit_summary = format_transit_summary_for_ui(natal_chart, transit_chart, max_aspects=5)

        # Generate daily horoscope (Prompt 1)
        daily_horoscope = generate_daily_horoscope(
            date=date,
            user_profile=user_profile,
            sun_sign_profile=sun_sign_profile,
            transit_summary=transit_summary,
            memory=memory,
            api_key=GEMINI_API_KEY.value,
            posthog_api_key=POSTHOG_API_KEY.value,
            model_name=model_name
        )

        # Cache horoscope in UserHoroscopes collection (for Ask the Stars)
        horoscopes_ref = db.collection("users").document(user_id).collection("horoscopes").document("all")
        horoscopes_doc = horoscopes_ref.get()

        if horoscopes_doc.exists:
            # Update existing horoscopes
            horoscopes_ref.update({
                f"horoscopes.{date}": daily_horoscope.model_dump(),
                "updated_at": datetime.now().isoformat()
            })
        else:
            # Create new horoscopes document
            horoscopes_ref.set({
                "user_id": user_id,
                "horoscopes": {date: daily_horoscope.model_dump()},
                "updated_at": datetime.now().isoformat()
            })

        # Update last_active
        db.collection("users").document(user_id).update({
            "last_active": datetime.now().isoformat()
        })

        return daily_horoscope.model_dump()

    except https_fn.HttpsError:
        raise
    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"Invalid parameter values: {str(e)}"
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error generating daily horoscope: {str(e)}"
        )


# =============================================================================
# Sprint X: Astrometers - Quantitative Transit Analysis
# =============================================================================

@https_fn.on_call()
def get_astrometers(req: https_fn.CallableRequest) -> dict:
    """
    Calculate all 28 astrological meters for a user on a given date.

    Returns 23 individual meters + 5 super-group aggregate meters:

    INDIVIDUAL METERS (23):
    - Overall intensity and harmony of transits
    - Element energies (fire, earth, air, water)
    - Cognitive state (mental clarity, decision quality, communication)
    - Emotional state (intensity, relationship harmony, resilience)
    - Physical/action state (energy, conflict risk, motivation)
    - Life domains (career, opportunity, challenge, transformation)
    - Specialized areas (intuition, innovation, karmic lessons, collective)

    SUPER-GROUP AGGREGATES (5):
    - overview_super_group: Dashboard summary (2 meters)
    - inner_world_super_group: Thoughts + feelings (6 meters)
    - outer_world_super_group: Action + career (5 meters)
    - evolution_super_group: Transformation (3 meters)
    - deeper_dimensions_super_group: Elements + spiritual (7 meters)

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "date": "2025-10-26",  // Optional, defaults to today
    }

    Returns:
    {
        "date": "2025-10-26T00:00:00",
        "natal_chart_summary": {
            "sun_sign": "gemini",
            "ascendant_sign": "leo",
            "moon_sign": "pisces"
        },
        "aspect_count": 12,
        "overall_intensity": {...},  // MeterReading with intensity, harmony, interpretation, advice
        "overall_harmony": {...},
        "fire_energy": {...},
        ... // All 23 individual meters
        "overview_super_group": {...},  // Super-group aggregate meters
        "inner_world_super_group": {...},
        "outer_world_super_group": {...},
        "evolution_super_group": {...},
        "deeper_dimensions_super_group": {...}
    }
    """
    try:
        from astrometers import get_meters

        data = req.data
        user_id = data.get("user_id")

        if not user_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameter: user_id"
            )

        # Optional parameters
        date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))

        # Get user profile from Firestore
        db = firestore.client(database_id=DATABASE_ID)
        user_doc = db.collection("users").document(user_id).get()

        if not user_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"User profile not found: {user_id}"
            )

        user_data = user_doc.to_dict()
        user_profile = UserProfile(**user_data)

        # Get natal chart from user profile
        natal_chart = user_profile.natal_chart

        # Compute transit chart for the target date
        transit_chart, _ = compute_birth_chart(
            birth_date=date_str,
            birth_time="12:00"  # Use noon for transits
        )

        # Parse date string to datetime
        target_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Calculate all meters
        all_meters = get_meters(
            natal_chart=natal_chart,
            transit_chart=transit_chart,
            date=target_date
        )

        # Update last_active
        db.collection("users").document(user_id).update({
            "last_active": datetime.now().isoformat()
        })

        # Return as dictionary
        return all_meters.model_dump()

    except https_fn.HttpsError:
        raise
    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=f"Invalid parameter values: {str(e)}"
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error calculating astrometers: {str(e)}"
        )


# =============================================================================
# Ask the Stars - Conversational Q&A Feature
# =============================================================================

# Import Ask the Stars functions
from ask_the_stars import ask_the_stars
from triggers import extract_entities_on_message
from conversation_helpers import (
    get_conversation_history,
    get_user_entities,
    update_entity,
    delete_entity
)

# Functions are automatically registered when imported
# - ask_the_stars: HTTPS endpoint with SSE streaming
# - extract_entities_on_message: Firestore trigger (background)
# - get_conversation_history: Callable function
# - get_user_entities: Callable function
# - update_entity: Callable function
# - delete_entity: Callable function

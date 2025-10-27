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
    summarize_transits_with_natal,
    ChartType,
)
from models import (
    UserProfile,
    MemoryCollection,
    JournalEntry,
    create_empty_memory,
    update_memory_from_journal,
)
from llm import generate_daily_horoscope, generate_detailed_horoscope

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


# =============================================================================
# Sprint 3: User Profile & Memory Operations
# =============================================================================

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


# =============================================================================
# Sprint 3.5: Sun Sign Utilities
# =============================================================================

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


# =============================================================================
# Sprint 4: Horoscope Generation
# =============================================================================

@https_fn.on_call(secrets=[GEMINI_API_KEY, POSTHOG_API_KEY])
def get_daily_horoscope(req: https_fn.CallableRequest) -> dict:
    """
    Generate daily horoscope (Prompt 1) - fast, shown immediately.

    This is the two-prompt architecture's first prompt:
    - Includes: technical_analysis, key_active_transit, area_of_life_activated,
                daily_theme_headline, daily_overview, summary, actionable_advice,
                lunar_cycle_update
    - Returns in <2 seconds

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

        # Get memory collection
        memory_doc = db.collection("memory").document(user_id).get()
        if memory_doc.exists:
            memory_data = memory_doc.to_dict()
            memory = MemoryCollection(**memory_data)
        else:
            memory = create_empty_memory(user_id)

        # Compute transit chart for today
        transit_chart, _ = compute_birth_chart(
            birth_date=date,
            birth_time="12:00"  # Use noon for transits
        )

        # Get natal chart from user profile
        natal_chart = user_profile.natal_chart

        # Generate enhanced transit data with natal-transit aspects
        transit_data = summarize_transits_with_natal(natal_chart, transit_chart)

        # Generate daily horoscope (Prompt 1)
        daily_horoscope = generate_daily_horoscope(
            date=date,
            user_profile=user_profile,
            sun_sign_profile=sun_sign_profile,
            transit_data=transit_data,
            memory=memory,
            api_key=GEMINI_API_KEY.value,
            posthog_api_key=POSTHOG_API_KEY.value,
            model_name=model_name
        )

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


@https_fn.on_call(secrets=[GEMINI_API_KEY, POSTHOG_API_KEY])
def get_detailed_horoscope(req: https_fn.CallableRequest) -> dict:
    """
    Generate detailed horoscope (Prompt 2) - loaded in background.

    This is the two-prompt architecture's second prompt:
    - Includes: general_transits_overview, look_ahead_preview, details (8 categories)
    - Takes ~5 seconds
    - Uses daily_horoscope output as context

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "date": "2025-10-18",  // Optional, defaults to today
        "daily_horoscope": { ... },  // Output from get_daily_horoscope()
    }

    Returns:
        DetailedHoroscope model as dictionary
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        daily_horoscope_data = data.get("daily_horoscope")

        if not user_id or not daily_horoscope_data:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: user_id, daily_horoscope"
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

        # Get memory collection
        memory_doc = db.collection("memory").document(user_id).get()
        if memory_doc.exists:
            memory_data = memory_doc.to_dict()
            memory = MemoryCollection(**memory_data)
        else:
            memory = create_empty_memory(user_id)

        # Compute transit chart for today
        transit_chart, _ = compute_birth_chart(
            birth_date=date,
            birth_time="12:00"  # Use noon for transits
        )

        # Get natal chart from user profile
        natal_chart = user_profile.natal_chart

        # Generate enhanced transit data with natal-transit aspects
        transit_data = summarize_transits_with_natal(natal_chart, transit_chart)

        # Parse daily horoscope from request
        from models import DailyHoroscope
        daily_horoscope = DailyHoroscope(**daily_horoscope_data)

        # Generate detailed horoscope (Prompt 2)
        detailed_horoscope = generate_detailed_horoscope(
            date=date,
            user_profile=user_profile,
            sun_sign_profile=sun_sign_profile,
            transit_data=transit_data,
            memory=memory,
            daily_horoscope=daily_horoscope,
            api_key=GEMINI_API_KEY.value,
            posthog_api_key=POSTHOG_API_KEY.value,
            model_name=model_name
        )

        return detailed_horoscope.model_dump()

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
            message=f"Error generating detailed horoscope: {str(e)}"
        )


# =============================================================================
# Sprint X: Astrometers - Quantitative Transit Analysis
# =============================================================================

@https_fn.on_call()
def get_astrometers(req: https_fn.CallableRequest) -> dict:
    """
    Calculate all 23 astrological meters for a user on a given date.

    This provides quantitative analysis of:
    - Overall intensity and harmony of transits
    - Element energies (fire, earth, air, water)
    - Cognitive state (mental clarity, decision quality, communication)
    - Emotional state (intensity, relationship harmony, resilience)
    - Physical/action state (energy, conflict risk, motivation)
    - Life domains (career, opportunity, challenge, transformation)
    - Specialized areas (intuition, innovation, karmic lessons, collective)

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
        ... // All 23 meters
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
# Sprint 5: Firestore Triggers
# =============================================================================

@firestore_fn.on_document_created(document="users/{user_id}/journal/{entry_id}")  # type: ignore[arg-type]
def update_memory_on_journal_entry(
    event: firestore_fn.Event[firestore_fn.DocumentSnapshot]
) -> None:
    """
    Firestore trigger: Update memory collection when journal entry is created.

    This implements the Journal → Memory pattern:
    - Journal = immutable source of truth
    - Memory = derivative cache for personalization

    Process:
        1. Read the newly created journal entry
        2. Get current memory collection (or create if doesn't exist)
        3. Update category counts and last_mentioned
        4. Add to recent_readings (FIFO, max 10)
        5. Write updated memory back to Firestore
    """
    try:
        # Get user_id from path
        user_id = event.params["user_id"]

        # Get journal entry data
        journal_data = event.data.to_dict()

        if not journal_data:
            print(f"No data in journal entry for user {user_id}")
            return

        # Get Firestore client
        db = firestore.client(database_id=DATABASE_ID)

        # Get current memory or create new one
        memory_doc = db.collection("memory").document(user_id).get()

        if memory_doc.exists:
            memory_data = memory_doc.to_dict()
            memory = MemoryCollection(**memory_data)
        else:
            memory = create_empty_memory(user_id)

        # Create JournalEntry from data
        journal_entry = JournalEntry(**journal_data)

        # Update memory using helper function from models.py
        updated_memory = update_memory_from_journal(memory, journal_entry)

        # Write back to Firestore
        db.collection("memory").document(user_id).set(updated_memory.model_dump())

        print(f"Memory updated for user {user_id} after journal entry {journal_data.get('entry_id')}")

    except Exception as e:
        print(f"Error updating memory for user {user_id}: {str(e)}")
        # Don't raise - triggers should not fail the original operation

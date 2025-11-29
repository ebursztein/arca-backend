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

# Import shared secrets (centralized to avoid duplicate declarations)
from firebase_secrets import GEMINI_API_KEY, POSTHOG_API_KEY

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

@https_fn.on_call(secrets=[GEMINI_API_KEY, POSTHOG_API_KEY])
def create_user_profile(req: https_fn.CallableRequest) -> dict:
    """
    Create user profile with birth chart computation and LLM-generated summary.

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

        # Get sun sign profile for summary generation
        sun_sign_profile = get_sun_sign_profile(sun_sign)

        # Compute birth chart (handles both V1 and V2 modes)
        natal_chart, exact_chart = compute_birth_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_timezone=birth_timezone,
            birth_lat=birth_lat,
            birth_lon=birth_lon
        )

        # Generate natal chart summary (LLM call)
        from llm import generate_natal_chart_summary
        natal_chart_summary = generate_natal_chart_summary(
            chart_dict=natal_chart,
            sun_sign_profile=sun_sign_profile,
            user_name=name.split()[0],  # First name only
            api_key=GEMINI_API_KEY.value,
            user_id=user_id,
            posthog_api_key=POSTHOG_API_KEY.value
        )
        natal_chart["summary"] = natal_chart_summary

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


@https_fn.on_call(secrets=[GEMINI_API_KEY, POSTHOG_API_KEY])
def update_user_profile(req: https_fn.CallableRequest) -> dict:
    """
    Update user profile with optional natal chart regeneration.

    Two use cases:
    1. Photo update only
    2. Extended setup with birth time/location - triggers natal chart regeneration

    Args:
        user_id (str): Firebase auth user ID
        photo_path (str, optional): Firebase Storage path for profile photo
        birth_time (str, optional): Birth time HH:MM - triggers chart regeneration
        birth_timezone (str, optional): IANA timezone for birth time
        birth_lat (float, optional): Birth latitude
        birth_lon (float, optional): Birth longitude

    Returns:
        { "success": true, "profile": UserProfile with natal_chart and summary }
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
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"User profile not found: {user_id}"
            )

        user_data = user_doc.to_dict()
        updates = {}

        # Handle photo update
        photo_path = data.get("photo_path")
        if photo_path is not None:
            updates["photo_path"] = photo_path

        # Handle extended setup (birth time/location)
        birth_time = data.get("birth_time")
        birth_timezone = data.get("birth_timezone")
        birth_lat = data.get("birth_lat")
        birth_lon = data.get("birth_lon")

        # Check if any birth data is being updated
        has_birth_update = any([
            birth_time is not None,
            birth_timezone is not None,
            birth_lat is not None,
            birth_lon is not None
        ])

        if has_birth_update:
            # Update birth fields
            if birth_time is not None:
                updates["birth_time"] = birth_time
            if birth_timezone is not None:
                updates["birth_timezone"] = birth_timezone
            if birth_lat is not None:
                updates["birth_lat"] = birth_lat
            if birth_lon is not None:
                updates["birth_lon"] = birth_lon

            # Merge with existing user data to get complete birth info
            final_birth_time = birth_time or user_data.get("birth_time")
            final_birth_timezone = birth_timezone or user_data.get("birth_timezone")
            final_birth_lat = birth_lat if birth_lat is not None else user_data.get("birth_lat")
            final_birth_lon = birth_lon if birth_lon is not None else user_data.get("birth_lon")

            # Regenerate natal chart with updated birth data
            natal_chart, exact_chart = compute_birth_chart(
                birth_date=user_data["birth_date"],
                birth_time=final_birth_time,
                birth_timezone=final_birth_timezone,
                birth_lat=final_birth_lat,
                birth_lon=final_birth_lon
            )

            # Regenerate summary with new chart data
            from llm import generate_natal_chart_summary
            sun_sign = get_sun_sign(user_data["birth_date"])
            sun_sign_profile = get_sun_sign_profile(sun_sign)

            natal_chart_summary = generate_natal_chart_summary(
                chart_dict=natal_chart,
                sun_sign_profile=sun_sign_profile,
                user_name=user_data.get("name", "").split()[0],
                api_key=GEMINI_API_KEY.value,
                user_id=user_id,
                posthog_api_key=POSTHOG_API_KEY.value
            )
            natal_chart["summary"] = natal_chart_summary

            updates["natal_chart"] = natal_chart
            updates["exact_chart"] = exact_chart

        # Update last_active timestamp
        updates["last_active"] = datetime.now().isoformat()

        # Apply updates to Firestore
        if updates:
            user_ref.update(updates)

        # Get the updated profile
        updated_doc = user_ref.get()
        updated_profile = updated_doc.to_dict()

        return {
            "success": True,
            "profile": updated_profile
        }

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
            message=f"Error updating user profile: {str(e)}"
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
    - Meter groups: 5 life areas (mind, heart, body, instincts, growth) with
                    aggregated scores and LLM interpretations
    - Look ahead: Upcoming transits preview (next 7 days)
    - Astrometers: Complete 17-meter reading

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

        # Fetch user connections for relationship weather (replacing entities)
        from connections import get_connections_for_horoscope
        connections = get_connections_for_horoscope(db, user_id, limit=20)

        # Select ONE featured connection for today (rotation)
        from llm import select_featured_connection
        featured_connection = select_featured_connection(connections, memory, date)

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
        from llm import update_memory_with_connection_mention
        daily_horoscope = generate_daily_horoscope(
            date=date,
            user_profile=user_profile,
            sun_sign_profile=sun_sign_profile,
            transit_summary=transit_summary,
            memory=memory,
            featured_connection=featured_connection,
            api_key=GEMINI_API_KEY.value,
            posthog_api_key=POSTHOG_API_KEY.value,
            model_name=model_name
        )

        # Calculate connection vibe and add to relationship_weather
        if featured_connection and featured_connection.get("synastry_points"):
            from compatibility import find_transits_to_synastry, calculate_vibe_score
            from models import ConnectionVibe
            from astro import NatalChartData

            transit_chart_data = NatalChartData(**transit_chart)
            active_transits = find_transits_to_synastry(
                transit_chart=transit_chart_data,
                synastry_points=featured_connection["synastry_points"],
                orb=3.0
            )
            vibe_score = calculate_vibe_score(active_transits)

            # Generate template-based vibe text
            name = featured_connection.get("name", "")
            if vibe_score >= 75:
                vibe_text = f"Great energy between you and {name} today"
            elif vibe_score >= 50:
                vibe_text = f"Steady connection with {name}"
            elif vibe_score >= 25:
                vibe_text = f"Give {name} a little space today"
            else:
                vibe_text = f"Low-key day with {name}"

            connection_vibe = ConnectionVibe(
                connection_id=featured_connection.get("connection_id", ""),
                name=name,
                relationship_type=featured_connection.get("relationship_type", "friend"),
                vibe=vibe_text,
                vibe_score=vibe_score,
                key_transit=active_transits[0]["description"] if active_transits else None
            )

            # Add to relationship_weather
            if daily_horoscope.relationship_weather:
                daily_horoscope.relationship_weather.connection_vibes = [connection_vibe]

            # Store vibe on connection (FIFO last 10, like Co-Star updates)
            from connections import StoredVibe
            stored_vibe = StoredVibe(
                date=date,
                vibe=vibe_text,
                vibe_score=vibe_score,
                key_transit=active_transits[0]["description"] if active_transits else None
            )

            # Update connection with new vibe (FIFO)
            conn_ref = db.collection("users").document(user_id).collection("connections").document(featured_connection["connection_id"])
            conn_doc = conn_ref.get()
            if conn_doc.exists:
                conn_data = conn_doc.to_dict()
                vibes = conn_data.get("vibes", [])

                # Don't add duplicate for same date
                vibes = [v for v in vibes if v.get("date") != date]

                # Add new vibe at front, keep last 10
                vibes.insert(0, stored_vibe.model_dump())
                vibes = vibes[:10]

                conn_ref.update({"vibes": vibes, "updated_at": datetime.now().isoformat()})

        # Update memory with connection mention (for rotation tracking)
        if featured_connection:
            vibe_context = ""
            if daily_horoscope.relationship_weather and daily_horoscope.relationship_weather.connection_vibes:
                vibe_context = daily_horoscope.relationship_weather.connection_vibes[0].vibe
            memory = update_memory_with_connection_mention(
                memory=memory,
                featured_connection=featured_connection,
                date=date,
                context=vibe_context
            )
            # Save updated memory to Firestore
            memory_ref = db.collection("memory").document(user_id)
            memory_ref.set(memory.model_dump(), merge=True)

        # Cache compressed horoscope (for Ask the Stars)
        # Store in users/{user_id}/horoscopes/latest with FIFO limit of 10
        from models import compress_horoscope, UserHoroscopes, CompressedHoroscope

        compressed = compress_horoscope(daily_horoscope)
        horoscopes_ref = db.collection("users").document(user_id).collection("horoscopes").document("latest")
        horoscopes_doc = horoscopes_ref.get()

        if horoscopes_doc.exists:
            # Load existing and add new (FIFO enforcement)
            horoscopes_data = UserHoroscopes(**horoscopes_doc.to_dict())
            horoscopes_dict = horoscopes_data.horoscopes

            # Add new horoscope
            horoscopes_dict[date] = compressed.model_dump()

            # FIFO: Keep only last 10 (sort by date descending, take top 10)
            sorted_dates = sorted(horoscopes_dict.keys(), reverse=True)[:10]
            horoscopes_dict = {d: horoscopes_dict[d] for d in sorted_dates}

            horoscopes_ref.update({
                "horoscopes": horoscopes_dict,
                "updated_at": datetime.now().isoformat()
            })
        else:
            # Create new horoscopes document
            horoscopes_ref.set({
                "user_id": user_id,
                "horoscopes": {date: compressed.model_dump()},
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
    Calculate all 17 astrological meters for a user on a given date.

    Returns 17 individual meters organized into 5 groups:

    METER GROUPS (5):
    - Mind (3): clarity, focus, communication
    - Heart (3): connections, resilience, vulnerability
    - Body (3): energy, drive, strength
    - Instincts (4): vision, flow, intuition, creativity
    - Growth (4): momentum, ambition, evolution, circle

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
        "overall_intensity": {...},  // MeterReading with intensity, harmony, unified_score
        "overall_harmony": {...},
        "clarity": {...},
        ... // All 17 individual meters
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


# =============================================================================
# Connections & Compatibility - Charts API
# =============================================================================

from connections import (
    get_or_create_share_link,
    get_public_profile as get_public_profile_fn,
    import_connection as import_connection_fn,
    create_connection as create_connection_fn,
    update_connection as update_connection_fn,
    delete_connection as delete_connection_fn,
    list_connections as list_connections_fn,
    list_connection_requests as list_connection_requests_fn,
    update_share_mode as update_share_mode_fn,
    respond_to_request as respond_to_request_fn,
    register_device_token as register_device_token_fn,
)
from compatibility import (
    calculate_compatibility,
    get_compatibility_from_birth_data,
)


@https_fn.on_call()
def get_share_link(req: https_fn.CallableRequest) -> dict:
    """
    Get user's shareable profile link for "Add me on Arca".

    Creates share link if doesn't exist.

    Expected request data:
    {
        "user_id": "firebase_auth_id"
    }

    Returns:
    {
        "share_url": "https://arca-app.com/u/abc123xyz",
        "share_mode": "public",
        "qr_code_data": "https://arca-app.com/u/abc123xyz"
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

        db = firestore.client(database_id=DATABASE_ID)
        user_doc = db.collection("users").document(user_id).get()

        if not user_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"User not found: {user_id}"
            )

        result = get_or_create_share_link(db, user_id, user_doc.to_dict())
        return result.model_dump()

    except https_fn.HttpsError:
        raise
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error getting share link: {str(e)}"
        )


@https_fn.on_call()
def get_public_profile(req: https_fn.CallableRequest) -> dict:
    """
    Fetch public profile data from a share link.

    Expected request data:
    {
        "share_secret": "abc123xyz"
    }

    Returns (public mode):
    {
        "profile": { "name": "John", "birth_date": "...", "sun_sign": "gemini" },
        "share_mode": "public",
        "can_add": true
    }

    Returns (request mode):
    {
        "profile": { "name": "John", "sun_sign": "gemini" },
        "share_mode": "request",
        "can_add": false,
        "message": "John requires approval..."
    }
    """
    try:
        data = req.data
        share_secret = data.get("share_secret")

        if not share_secret:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameter: share_secret"
            )

        db = firestore.client(database_id=DATABASE_ID)
        result = get_public_profile_fn(db, share_secret)
        return result.model_dump()

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message=str(e)
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error getting public profile: {str(e)}"
        )


@https_fn.on_call()
def import_connection(req: https_fn.CallableRequest) -> dict:
    """
    Add a connection from a share link.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "share_secret": "abc123xyz",
        "relationship_type": "friend"
    }

    Returns:
    {
        "success": true,
        "connection_id": "conn_xyz789",
        "connection": { "name": "John", "sun_sign": "gemini" },
        "notification_sent": true
    }
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        share_secret = data.get("share_secret")
        relationship_type = data.get("relationship_type", "friend")

        if not user_id or not share_secret:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: user_id, share_secret"
            )

        db = firestore.client(database_id=DATABASE_ID)
        result = import_connection_fn(db, user_id, share_secret, relationship_type)
        return result.model_dump()

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message=str(e)
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error importing connection: {str(e)}"
        )


@https_fn.on_call()
def create_connection(req: https_fn.CallableRequest) -> dict:
    """
    Manually create a connection (not via share link).

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "connection": {
            "name": "Sarah",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",  // Optional
            "birth_lat": 40.7128,   // Optional
            "birth_lon": -74.0060,  // Optional
            "birth_timezone": "America/New_York",  // Optional
            "relationship_type": "romantic"
        }
    }

    Returns:
        Created connection data
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        conn_data = data.get("connection", {})

        if not user_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameter: user_id"
            )

        name = conn_data.get("name")
        birth_date = conn_data.get("birth_date")
        relationship_type = conn_data.get("relationship_type", "friend")

        if not name or not birth_date:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required connection fields: name, birth_date"
            )

        db = firestore.client(database_id=DATABASE_ID)
        connection = create_connection_fn(
            db=db,
            user_id=user_id,
            name=name,
            birth_date=birth_date,
            relationship_type=relationship_type,
            birth_time=conn_data.get("birth_time"),
            birth_lat=conn_data.get("birth_lat"),
            birth_lon=conn_data.get("birth_lon"),
            birth_timezone=conn_data.get("birth_timezone")
        )
        return connection.model_dump()

    except https_fn.HttpsError:
        raise
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error creating connection: {str(e)}"
        )


@https_fn.on_call()
def update_connection(req: https_fn.CallableRequest) -> dict:
    """
    Update a connection's details.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "connection_id": "conn_abc123",
        "updates": {
            "name": "New Name",
            "relationship_type": "romantic"
        }
    }

    Returns:
        Updated connection data
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        connection_id = data.get("connection_id")
        updates = data.get("updates", {})

        if not user_id or not connection_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: user_id, connection_id"
            )

        db = firestore.client(database_id=DATABASE_ID)
        connection = update_connection_fn(db, user_id, connection_id, updates)
        return connection.model_dump()

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message=str(e)
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error updating connection: {str(e)}"
        )


@https_fn.on_call()
def delete_connection(req: https_fn.CallableRequest) -> dict:
    """
    Delete a connection.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "connection_id": "conn_abc123"
    }

    Returns:
        { "success": true }
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        connection_id = data.get("connection_id")

        if not user_id or not connection_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: user_id, connection_id"
            )

        db = firestore.client(database_id=DATABASE_ID)
        delete_connection_fn(db, user_id, connection_id)
        return {"success": True}

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message=str(e)
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error deleting connection: {str(e)}"
        )


@https_fn.on_call()
def list_connections(req: https_fn.CallableRequest) -> dict:
    """
    List all user's connections.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "limit": 50  // Optional, default 50
    }

    Returns:
    {
        "connections": [...],
        "total_count": 5
    }
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        limit = data.get("limit", 50)

        if not user_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameter: user_id"
            )

        db = firestore.client(database_id=DATABASE_ID)
        result = list_connections_fn(db, user_id, limit)
        return result.model_dump()

    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error listing connections: {str(e)}"
        )


@https_fn.on_call()
def list_connection_requests(req: https_fn.CallableRequest) -> dict:
    """
    List pending connection requests for a user.

    Expected request data:
    {
        "user_id": "firebase_auth_id"
    }

    Returns:
    {
        "requests": [...]
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

        db = firestore.client(database_id=DATABASE_ID)
        requests = list_connection_requests_fn(db, user_id)
        return {"requests": requests}

    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error listing connection requests: {str(e)}"
        )


@https_fn.on_call()
def update_share_mode(req: https_fn.CallableRequest) -> dict:
    """
    Toggle between public and request-only share modes.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "share_mode": "request"  // or "public"
    }

    Returns:
        { "share_mode": "request" }
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        share_mode = data.get("share_mode")

        if not user_id or share_mode not in ["public", "request"]:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing/invalid parameters: user_id, share_mode (public|request)"
            )

        db = firestore.client(database_id=DATABASE_ID)
        result = update_share_mode_fn(db, user_id, share_mode)
        return result

    except https_fn.HttpsError:
        raise
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error updating share mode: {str(e)}"
        )


@https_fn.on_call()
def respond_to_request(req: https_fn.CallableRequest) -> dict:
    """
    Approve or reject a connection request.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "request_id": "req_abc123",
        "action": "approve"  // or "reject"
    }

    Returns:
        { "success": true, "action": "approved", "connection_id": "..." }
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        request_id = data.get("request_id")
        action = data.get("action")

        if not user_id or not request_id or action not in ["approve", "reject"]:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing/invalid parameters: user_id, request_id, action (approve|reject)"
            )

        db = firestore.client(database_id=DATABASE_ID)
        result = respond_to_request_fn(db, user_id, request_id, action)
        return result

    except ValueError as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message=str(e)
        )
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error responding to request: {str(e)}"
        )


@https_fn.on_call()
def register_device_token(req: https_fn.CallableRequest) -> dict:
    """
    Register device token for push notifications.

    Called by iOS on login/app launch.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "device_token": "fcm_device_token"
    }

    Returns:
        { "success": true }
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        device_token = data.get("device_token")

        if not user_id or not device_token:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: user_id, device_token"
            )

        db = firestore.client(database_id=DATABASE_ID)
        success = register_device_token_fn(db, user_id, device_token)
        return {"success": success}

    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error registering device token: {str(e)}"
        )


@https_fn.on_call()
def get_natal_chart_for_connection(req: https_fn.CallableRequest) -> dict:
    """
    Get natal chart for a connection.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "connection_id": "conn_abc123"
    }

    Returns:
        Natal chart data for the connection
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        connection_id = data.get("connection_id")

        if not user_id or not connection_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: user_id, connection_id"
            )

        db = firestore.client(database_id=DATABASE_ID)

        # Get connection
        conn_doc = db.collection("users").document(user_id).collection(
            "connections"
        ).document(connection_id).get()

        if not conn_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"Connection not found: {connection_id}"
            )

        conn_data = conn_doc.to_dict()

        # Compute natal chart from connection's birth data
        chart_dict, has_exact = compute_birth_chart(
            birth_date=conn_data.get("birth_date"),
            birth_time=conn_data.get("birth_time"),
            birth_timezone=conn_data.get("birth_timezone"),
            birth_lat=conn_data.get("birth_lat"),
            birth_lon=conn_data.get("birth_lon")
        )

        return {
            "chart": chart_dict,
            "has_exact_chart": has_exact,
            "connection_name": conn_data.get("name"),
            "sun_sign": conn_data.get("sun_sign")
        }

    except https_fn.HttpsError:
        raise
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error getting connection chart: {str(e)}"
        )


@https_fn.on_call(memory=512, secrets=[GEMINI_API_KEY, POSTHOG_API_KEY])
def get_compatibility(req: https_fn.CallableRequest) -> dict:
    """
    Get compatibility analysis between user and a connection.

    Returns all three modes (romantic, friendship, coworker) in single response.
    Always includes LLM-generated personalized interpretation.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "connection_id": "conn_abc123"
    }

    Returns:
    {
        "romantic": { "overall_score": 78, "categories": [...] },
        "friendship": { "overall_score": 85, "categories": [...] },
        "coworker": { "overall_score": 72, "categories": [...] },
        "aspects": [...],
        "composite_summary": { "composite_sun": "Libra", ... },
        "calculated_at": "2025-11-25T14:30:00Z",
        "interpretation": { "headline": "...", "summary": "...", ... }
    }
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        connection_id = data.get("connection_id")

        if not user_id or not connection_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: user_id, connection_id"
            )

        db = firestore.client(database_id=DATABASE_ID)

        # Get user profile
        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"User not found: {user_id}"
            )
        user_data = user_doc.to_dict()

        # Get connection
        conn_doc = db.collection("users").document(user_id).collection(
            "connections"
        ).document(connection_id).get()

        if not conn_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"Connection not found: {connection_id}"
            )
        conn_data = conn_doc.to_dict()

        # Calculate compatibility
        from astro import NatalChartData

        user_chart = NatalChartData(**user_data.get("natal_chart", {}))

        # Build connection chart from birth data
        conn_chart_dict, _ = compute_birth_chart(
            birth_date=conn_data.get("birth_date"),
            birth_time=conn_data.get("birth_time"),
            birth_timezone=conn_data.get("birth_timezone"),
            birth_lat=conn_data.get("birth_lat"),
            birth_lon=conn_data.get("birth_lon")
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        result = calculate_compatibility(user_chart, conn_chart)
        response = result.model_dump()

        # Generate LLM interpretation (always)
        from llm import generate_compatibility_interpretation
        from astro import get_sun_sign

        # Get user's sun sign and name
        user_sun_sign = user_data.get("sun_sign", "")
        user_name = user_data.get("name", "").split()[0] if user_data.get("name") else "You"

        # Get connection's sun sign (calculate from birth date if not stored)
        conn_sun_sign = conn_data.get("sun_sign")
        if not conn_sun_sign and conn_data.get("birth_date"):
            conn_sun_sign = get_sun_sign(conn_data["birth_date"]).value
        conn_name = conn_data.get("name", "Your connection")

        interpretation = generate_compatibility_interpretation(
            user_name=user_name,
            user_sun_sign=user_sun_sign,
            connection_name=conn_name,
            connection_sun_sign=conn_sun_sign or "Unknown",
            relationship_type=conn_data.get("relationship_type", "friend"),
            compatibility_result=result,
            api_key=GEMINI_API_KEY.value,
            user_id=user_id,
            posthog_api_key=POSTHOG_API_KEY.value
        )

        # Merge category summaries into response
        category_summaries = interpretation.get("category_summaries", {})
        for mode_key in ["romantic", "friendship", "coworker"]:
            if mode_key in response:
                for cat in response[mode_key].get("categories", []):
                    cat_id = cat.get("id")
                    if cat_id and cat_id in category_summaries:
                        cat["summary"] = category_summaries[cat_id]

        # Merge aspect interpretations into response
        aspect_interps = {
            ai.get("aspect_id"): ai.get("interpretation")
            for ai in interpretation.get("aspect_interpretations", [])
            if ai.get("aspect_id")
        }
        for aspect in response.get("aspects", []):
            asp_id = aspect.get("id")
            if asp_id and asp_id in aspect_interps:
                aspect["interpretation"] = aspect_interps[asp_id]

        # Add overall interpretation for headline/summary/etc
        response["interpretation"] = {
            "headline": interpretation.get("headline", ""),
            "summary": interpretation.get("summary", ""),
            "strengths": interpretation.get("strengths", ""),
            "growth_areas": interpretation.get("growth_areas", ""),
            "advice": interpretation.get("advice", ""),
            "generation_time_ms": interpretation.get("generation_time_ms", 0),
            "model_used": interpretation.get("model_used", ""),
        }

        return response

    except https_fn.HttpsError:
        raise
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error calculating compatibility: {str(e)}"
        )


@https_fn.on_call(memory=512)
def get_synastry_chart(req: https_fn.CallableRequest) -> dict:
    """
    Get both natal charts and synastry aspects in a single call.

    Reduces round trips for iOS chart visualization - returns user's chart,
    connection's chart, and all synastry aspects between them.

    Expected request data:
    {
        "user_id": "firebase_auth_id",
        "connection_id": "conn_abc123"
    }

    Returns:
    {
        "user_chart": { NatalChartData },
        "connection_chart": { NatalChartData },
        "synastry_aspects": [ SynastryAspect ]
    }
    """
    try:
        data = req.data
        user_id = data.get("user_id")
        connection_id = data.get("connection_id")

        if not user_id or not connection_id:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message="Missing required parameters: user_id, connection_id"
            )

        db = firestore.client(database_id=DATABASE_ID)

        # Get user profile with natal chart
        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"User not found: {user_id}"
            )
        user_data = user_doc.to_dict()

        if not user_data.get("natal_chart"):
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.FAILED_PRECONDITION,
                message="User natal chart not found"
            )

        # Get connection
        conn_doc = db.collection("users").document(user_id).collection(
            "connections"
        ).document(connection_id).get()

        if not conn_doc.exists:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.NOT_FOUND,
                message=f"Connection not found: {connection_id}"
            )
        conn_data = conn_doc.to_dict()

        # Build charts
        from astro import NatalChartData
        from compatibility import calculate_synastry_aspects

        user_chart = NatalChartData(**user_data.get("natal_chart", {}))

        conn_chart_dict, _ = compute_birth_chart(
            birth_date=conn_data.get("birth_date"),
            birth_time=conn_data.get("birth_time"),
            birth_timezone=conn_data.get("birth_timezone"),
            birth_lat=conn_data.get("birth_lat"),
            birth_lon=conn_data.get("birth_lon")
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        # Calculate synastry aspects
        synastry_aspects = calculate_synastry_aspects(user_chart, conn_chart)

        return {
            "user_chart": user_chart.model_dump(),
            "connection_chart": conn_chart.model_dump(),
            "synastry_aspects": [a.model_dump() for a in synastry_aspects]
        }

    except https_fn.HttpsError:
        raise
    except Exception as e:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INTERNAL,
            message=f"Error getting synastry chart: {str(e)}"
        )

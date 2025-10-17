# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn, options
from firebase_admin import initialize_app
from datetime import datetime

from astro import get_astro_chart

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
options.set_global_options(max_instances=10)

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
            chart_type="natal"
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
            chart_type="transit"
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
            chart_type="transit"
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

"""
iOS Contract Validation Schemas.

Defines required field sets per endpoint based on docs/PUBLIC_API_GENERATED.md.
These schemas ensure backend responses match what iOS expects.

If a test fails due to missing fields, it indicates a breaking change
that would crash the iOS app.
"""

# ---------------------------------------------------------------------------
# User Profile Schemas
# ---------------------------------------------------------------------------

USER_PROFILE_REQUIRED_FIELDS = {
    "user_id",
    "name",
    "email",
    "birth_date",
    "sun_sign",
    "natal_chart",
    "exact_chart",
    "created_at",
    "last_active",
}

USER_PROFILE_OPTIONAL_FIELDS = {
    "is_premium",
    "premium_expiry",
    "is_trial_active",
    "trial_end_date",
    "birth_time",
    "birth_timezone",
    "birth_lat",
    "birth_lon",
    "photo_path",
}

USER_PROFILE_ALL_FIELDS = USER_PROFILE_REQUIRED_FIELDS | USER_PROFILE_OPTIONAL_FIELDS

SUN_SIGN_RESPONSE_FIELDS = {"sun_sign", "profile"}

CREATE_USER_PROFILE_RESPONSE_FIELDS = {
    "success",
    "user_id",
    "sun_sign",
    "exact_chart",
    "mode",
}

UPDATE_USER_PROFILE_RESPONSE_FIELDS = {"success", "profile"}


# ---------------------------------------------------------------------------
# Daily Horoscope Schemas
# ---------------------------------------------------------------------------

DAILY_HOROSCOPE_REQUIRED_FIELDS = {
    "date",
    "sun_sign",
    "technical_analysis",
    "daily_theme_headline",
    "daily_overview",
    "actionable_advice",
    "astrometers",
}

DAILY_HOROSCOPE_OPTIONAL_FIELDS = {
    "transit_summary",
    "moon_detail",
    "look_ahead_preview",
    "energy_rhythm",
    "relationship_weather",
    "collective_energy",
    "follow_up_questions",
    "model_used",
    "generation_time_ms",
    "usage",
}

DAILY_HOROSCOPE_ALL_FIELDS = DAILY_HOROSCOPE_REQUIRED_FIELDS | DAILY_HOROSCOPE_OPTIONAL_FIELDS

ACTIONABLE_ADVICE_REQUIRED_FIELDS = {"do", "dont", "reflect_on"}

RELATIONSHIP_WEATHER_REQUIRED_FIELDS = {"overview"}
RELATIONSHIP_WEATHER_OPTIONAL_FIELDS = {"connection_vibes"}

CONNECTION_VIBE_REQUIRED_FIELDS = {
    "connection_id",
    "name",
    "relationship_type",
    "vibe",
    "vibe_score",
    "key_transit",
}


# ---------------------------------------------------------------------------
# Astrometers Schemas
# ---------------------------------------------------------------------------

ASTROMETERS_FOR_IOS_REQUIRED_FIELDS = {
    "date",
    "overall_unified_score",
    "overall_intensity",
    "overall_harmony",
    "overall_quality",
    "overall_state",
    "groups",
    "top_active_meters",
    "top_challenging_meters",
    "top_flowing_meters",
}

METER_GROUP_FOR_IOS_REQUIRED_FIELDS = {
    "group_name",
    "display_name",
    "unified_score",
    "intensity",
    "harmony",
    "state_label",
    "quality",
    "interpretation",
    "meters",
    "overview",
    "detailed",
}

METER_GROUP_FOR_IOS_OPTIONAL_FIELDS = {
    "trend_delta",
    "trend_direction",
    "trend_change_rate",
}

METER_FOR_IOS_REQUIRED_FIELDS = {
    "meter_name",
    "display_name",
    "group",
    "unified_score",
    "intensity",
    "harmony",
    "unified_quality",
    "state_label",
    "interpretation",
    "overview",
    "detailed",
    "astrological_foundation",
    "top_aspects",
}

METER_FOR_IOS_OPTIONAL_FIELDS = {
    "trend_delta",
    "trend_direction",
    "trend_change_rate",
}

METER_READING_REQUIRED_FIELDS = {
    "meter_name",
    "date",
    "group",
    "unified_score",
    "intensity",
    "harmony",
    "unified_quality",
    "state_label",
    "interpretation",
    "advice",
    "top_aspects",
    "raw_scores",
}


# ---------------------------------------------------------------------------
# Chart Schemas
# ---------------------------------------------------------------------------

NATAL_CHART_DATA_REQUIRED_FIELDS = {
    "chart_type",
    "datetime_utc",
    "location_lat",
    "location_lon",
    "angles",
    "planets",
    "houses",
    "aspects",
    "distributions",
}

NATAL_CHART_DATA_OPTIONAL_FIELDS = {"summary"}

CHART_ANGLES_REQUIRED_FIELDS = {
    "ascendant",
    "imum_coeli",
    "descendant",
    "midheaven",
}

ANGLE_POSITION_REQUIRED_FIELDS = {
    "sign",
    "degree_in_sign",
    "absolute_degree",
    "position_dms",
}

PLANET_POSITION_REQUIRED_FIELDS = {
    "name",
    "symbol",
    "position_dms",
    "sign",
    "degree_in_sign",
    "absolute_degree",
    "house",
    "speed",
    "retrograde",
    "element",
    "modality",
}

HOUSE_CUSP_REQUIRED_FIELDS = {
    "number",
    "sign",
    "degree_in_sign",
    "absolute_degree",
    "ruler",
    "ruler_sign",
    "ruler_house",
    "classic_ruler",
    "classic_ruler_sign",
    "classic_ruler_house",
}

ASPECT_DATA_REQUIRED_FIELDS = {
    "body1",
    "body2",
    "aspect_type",
    "aspect_symbol",
    "exact_degree",
    "orb",
    "applying",
}


# ---------------------------------------------------------------------------
# Connection Schemas
# ---------------------------------------------------------------------------

CONNECTION_REQUIRED_FIELDS = {
    "connection_id",
    "name",
    "birth_date",
    "relationship_type",
    "created_at",
    "updated_at",
}

CONNECTION_OPTIONAL_FIELDS = {
    "birth_time",
    "birth_lat",
    "birth_lon",
    "birth_timezone",
    "source_user_id",
    "sun_sign",
    "photo_path",
    "synastry_points",
    "arca_notes",
    "vibes",
    "natal_chart",
    "exact_chart",
}

CONNECTION_ALL_FIELDS = CONNECTION_REQUIRED_FIELDS | CONNECTION_OPTIONAL_FIELDS

CONNECTION_LIST_RESPONSE_FIELDS = {"connections", "total_count"}

SHARE_LINK_RESPONSE_FIELDS = {"share_url", "share_mode", "qr_code_data"}

PUBLIC_PROFILE_RESPONSE_FIELDS = {"profile", "share_mode", "can_add"}

IMPORT_CONNECTION_RESPONSE_FIELDS = {"success"}

CONNECTION_REQUEST_FIELDS = {
    "request_id",
    "from_user_id",
    "from_name",
    "status",
    "created_at",
}


# ---------------------------------------------------------------------------
# Compatibility Schemas
# ---------------------------------------------------------------------------

COMPATIBILITY_RESULT_REQUIRED_FIELDS = {
    "romantic",
    "friendship",
    "coworker",
    "aspects",
    "calculated_at",
}

COMPATIBILITY_RESULT_OPTIONAL_FIELDS = {
    "composite_summary",
    "interpretation",
}

MODE_COMPATIBILITY_REQUIRED_FIELDS = {"overall_score", "categories"}

MODE_COMPATIBILITY_OPTIONAL_FIELDS = {"relationship_verb", "missing_data_prompts"}

COMPATIBILITY_CATEGORY_REQUIRED_FIELDS = {"id", "name", "score"}

COMPATIBILITY_CATEGORY_OPTIONAL_FIELDS = {"summary", "aspect_ids"}

SYNASTRY_ASPECT_REQUIRED_FIELDS = {
    "id",
    "user_planet",
    "their_planet",
    "aspect_type",
    "orb",
    "is_harmonious",
}

SYNASTRY_ASPECT_OPTIONAL_FIELDS = {"interpretation"}

SYNASTRY_CHART_RESPONSE_FIELDS = {
    "user_chart",
    "connection_chart",
    "synastry_aspects",
}

COMPOSITE_SUMMARY_FIELDS = {
    "composite_sun",
    "composite_moon",
    "summary",
    "strengths",
    "challenges",
}


# ---------------------------------------------------------------------------
# Entity Schemas
# ---------------------------------------------------------------------------

ENTITY_REQUIRED_FIELDS = {
    "entity_id",
    "name",
    "entity_type",
    "first_seen",
    "last_seen",
    "created_at",
    "updated_at",
}

ENTITY_OPTIONAL_FIELDS = {
    "status",
    "aliases",
    "category",
    "relationship_label",
    "notes",
    "attributes",
    "related_entities",
    "mention_count",
    "context_snippets",
    "importance_score",
    "connection_id",
}

ENTITY_ALL_FIELDS = ENTITY_REQUIRED_FIELDS | ENTITY_OPTIONAL_FIELDS


# ---------------------------------------------------------------------------
# Conversation Schemas
# ---------------------------------------------------------------------------

CONVERSATION_REQUIRED_FIELDS = {
    "conversation_id",
    "user_id",
    "horoscope_date",
    "messages",
    "created_at",
    "updated_at",
}

MESSAGE_REQUIRED_FIELDS = {
    "message_id",
    "role",
    "content",
    "timestamp",
}


# ---------------------------------------------------------------------------
# Memory Schemas
# ---------------------------------------------------------------------------

MEMORY_COLLECTION_REQUIRED_FIELDS = {
    "user_id",
    "categories",
    "updated_at",
}

MEMORY_COLLECTION_OPTIONAL_FIELDS = {
    "entity_summary",
    "last_conversation_date",
    "total_conversations",
    "question_categories",
    "relationship_mentions",
    "connection_mentions",
}


# ---------------------------------------------------------------------------
# Validation Functions
# ---------------------------------------------------------------------------

def assert_ios_contract(
    response: dict,
    required_fields: set,
    optional_fields: set = None,
    endpoint: str = "endpoint",
) -> None:
    """
    Validate response has all required iOS fields.

    Args:
        response: Response dict to validate
        required_fields: Set of required field names
        optional_fields: Set of optional field names (for strict mode)
        endpoint: Endpoint name for error messages

    Raises:
        AssertionError: If required fields missing
    """
    actual_fields = set(response.keys())
    missing = required_fields - actual_fields
    assert not missing, f"Missing iOS fields for {endpoint}: {missing}"

    # In strict mode, also check for unexpected fields
    if optional_fields is not None:
        all_allowed = required_fields | optional_fields
        unexpected = actual_fields - all_allowed
        if unexpected:
            # Warning only - don't fail for extra fields
            import warnings
            warnings.warn(f"Extra fields in {endpoint} (iOS may ignore): {unexpected}")


def assert_daily_horoscope_contract(response: dict) -> None:
    """Validate DailyHoroscope response matches iOS contract."""
    assert_ios_contract(
        response,
        DAILY_HOROSCOPE_REQUIRED_FIELDS,
        DAILY_HOROSCOPE_OPTIONAL_FIELDS,
        "get_daily_horoscope",
    )

    # Validate nested actionable_advice
    if "actionable_advice" in response:
        assert_ios_contract(
            response["actionable_advice"],
            ACTIONABLE_ADVICE_REQUIRED_FIELDS,
            endpoint="actionable_advice",
        )


def assert_astrometers_contract(response: dict) -> None:
    """Validate AstrometersForIOS response matches iOS contract."""
    assert_ios_contract(
        response,
        ASTROMETERS_FOR_IOS_REQUIRED_FIELDS,
        endpoint="get_astrometers",
    )

    # Validate groups
    if "groups" in response:
        for i, group in enumerate(response["groups"]):
            assert_ios_contract(
                group,
                METER_GROUP_FOR_IOS_REQUIRED_FIELDS,
                METER_GROUP_FOR_IOS_OPTIONAL_FIELDS,
                f"meter_group[{i}]",
            )

            # Validate meters in group
            if "meters" in group:
                for j, meter in enumerate(group["meters"]):
                    assert_ios_contract(
                        meter,
                        METER_FOR_IOS_REQUIRED_FIELDS,
                        METER_FOR_IOS_OPTIONAL_FIELDS,
                        f"meter[{i}][{j}]",
                    )


def assert_user_profile_contract(response: dict) -> None:
    """Validate UserProfile response matches iOS contract."""
    assert_ios_contract(
        response,
        USER_PROFILE_REQUIRED_FIELDS,
        USER_PROFILE_OPTIONAL_FIELDS,
        "get_user_profile",
    )


def assert_connection_contract(response: dict) -> None:
    """Validate Connection response matches iOS contract."""
    assert_ios_contract(
        response,
        CONNECTION_REQUIRED_FIELDS,
        CONNECTION_OPTIONAL_FIELDS,
        "connection",
    )


def assert_compatibility_contract(response: dict) -> None:
    """Validate CompatibilityResult response matches iOS contract."""
    assert_ios_contract(
        response,
        COMPATIBILITY_RESULT_REQUIRED_FIELDS,
        COMPATIBILITY_RESULT_OPTIONAL_FIELDS,
        "get_compatibility",
    )

    # Validate mode compatibility structs
    for mode in ["romantic", "friendship", "coworker"]:
        if mode in response:
            assert_ios_contract(
                response[mode],
                MODE_COMPATIBILITY_REQUIRED_FIELDS,
                MODE_COMPATIBILITY_OPTIONAL_FIELDS,
                f"compatibility.{mode}",
            )


def assert_synastry_chart_contract(response: dict) -> None:
    """Validate get_synastry_chart response matches iOS contract."""
    assert_ios_contract(
        response,
        SYNASTRY_CHART_RESPONSE_FIELDS,
        endpoint="get_synastry_chart",
    )


def assert_natal_chart_contract(response: dict) -> None:
    """Validate NatalChartData response matches iOS contract."""
    assert_ios_contract(
        response,
        NATAL_CHART_DATA_REQUIRED_FIELDS,
        NATAL_CHART_DATA_OPTIONAL_FIELDS,
        "natal_chart",
    )

    # Validate angles
    if "angles" in response:
        assert_ios_contract(
            response["angles"],
            CHART_ANGLES_REQUIRED_FIELDS,
            endpoint="chart.angles",
        )

    # Validate planets
    if "planets" in response:
        assert len(response["planets"]) == 11, "Expected 11 planets"
        for i, planet in enumerate(response["planets"]):
            assert_ios_contract(
                planet,
                PLANET_POSITION_REQUIRED_FIELDS,
                endpoint=f"planet[{i}]",
            )

    # Validate houses
    if "houses" in response:
        assert len(response["houses"]) == 12, "Expected 12 houses"
        for i, house in enumerate(response["houses"]):
            assert_ios_contract(
                house,
                HOUSE_CUSP_REQUIRED_FIELDS,
                endpoint=f"house[{i}]",
            )

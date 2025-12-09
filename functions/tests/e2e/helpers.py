"""
Helper utilities for E2E tests.

Provides:
- Mock Firebase CallableRequest creation
- Response validation utilities
- iOS contract validation
- SSE stream parsing
- Performance assertions
"""
import json
import re
from typing import Any, Type
from unittest.mock import MagicMock


def create_callable_request(data: dict, auth_uid: str = None) -> MagicMock:
    """
    Create mock Firebase CallableRequest for function testing.

    Args:
        data: Request data dict
        auth_uid: Optional authenticated user ID

    Returns:
        MagicMock: Mock request object
    """
    req = MagicMock()
    req.data = data
    if auth_uid:
        req.auth = MagicMock()
        req.auth.uid = auth_uid
    else:
        req.auth = None
    return req


def assert_response_matches_model(response: dict, model_class: Type) -> Any:
    """
    Validate response against Pydantic model.

    Args:
        response: Response dict to validate
        model_class: Pydantic model class

    Returns:
        The validated model instance

    Raises:
        ValidationError: If response doesn't match model
    """
    instance = model_class(**response)
    return instance


def assert_json_serializable(data: Any) -> str:
    """
    Assert data can be serialized to JSON (for iOS compatibility).

    Args:
        data: Data to serialize

    Returns:
        JSON string

    Raises:
        TypeError: If data is not JSON serializable
    """
    json_str = json.dumps(data)
    # Verify round-trip
    parsed = json.loads(json_str)
    assert parsed is not None
    return json_str


def assert_response_size_under(response: dict, max_kb: int = 100) -> float:
    """
    Assert response JSON size is under limit (for mobile performance).

    Args:
        response: Response dict
        max_kb: Maximum size in kilobytes

    Returns:
        Actual size in KB

    Raises:
        AssertionError: If response exceeds size limit
    """
    json_str = json.dumps(response)
    size_kb = len(json_str) / 1024
    assert size_kb < max_kb, f"Response too large: {size_kb:.1f}KB > {max_kb}KB"
    return size_kb


def parse_sse_stream(response_text: str) -> list[dict]:
    """
    Parse Server-Sent Events stream into list of events.

    Args:
        response_text: Raw SSE response text

    Returns:
        List of parsed event dicts
    """
    events = []
    for line in response_text.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                event_data = json.loads(line[6:])  # Remove "data: " prefix
                events.append(event_data)
            except json.JSONDecodeError:
                pass
    return events


def assert_sse_stream_complete(events: list[dict]) -> dict:
    """
    Assert SSE stream has complete structure with 'done' event.

    Args:
        events: List of parsed SSE events

    Returns:
        The 'done' event dict

    Raises:
        AssertionError: If stream is incomplete
    """
    assert len(events) > 0, "No events in stream"

    # Find done event
    done_event = None
    for event in events:
        if event.get("type") == "done":
            done_event = event
            break

    assert done_event is not None, "No 'done' event found in stream"
    assert "conversation_id" in done_event, "Missing conversation_id in done event"
    assert "message_id" in done_event, "Missing message_id in done event"

    return done_event


def assert_no_emoji_in_text(text: str, field_name: str = "text") -> None:
    """
    Assert text contains no emoji (brand voice requirement).

    Args:
        text: Text to check
        field_name: Field name for error message

    Raises:
        AssertionError: If emoji found in text
    """
    # Comprehensive emoji pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended
        "\U00002600-\U000026FF"  # misc symbols
        "]+",
        flags=re.UNICODE,
    )

    match = emoji_pattern.search(text)
    assert not match, f"Found emoji in {field_name}: '{match.group()}' in '{text[:100]}...'"


def assert_fields_present(response: dict, required_fields: set, endpoint: str = "response") -> None:
    """
    Assert all required fields are present in response.

    Args:
        response: Response dict
        required_fields: Set of required field names
        endpoint: Endpoint name for error message

    Raises:
        AssertionError: If any required fields missing
    """
    actual_fields = set(response.keys())
    missing = required_fields - actual_fields
    assert not missing, f"Missing fields for {endpoint}: {missing}"


def assert_no_unexpected_fields(
    response: dict,
    allowed_fields: set,
    endpoint: str = "response",
) -> None:
    """
    Assert no unexpected fields in response.

    Args:
        response: Response dict
        allowed_fields: Set of allowed field names
        endpoint: Endpoint name for error message

    Raises:
        AssertionError: If unexpected fields found
    """
    actual_fields = set(response.keys())
    unexpected = actual_fields - allowed_fields
    assert not unexpected, f"Unexpected fields in {endpoint}: {unexpected}"


def assert_score_in_range(
    score: float,
    min_val: float,
    max_val: float,
    field_name: str = "score",
) -> None:
    """
    Assert a score is within expected range.

    Args:
        score: Score value to check
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Field name for error message

    Raises:
        AssertionError: If score out of range
    """
    assert min_val <= score <= max_val, (
        f"{field_name} out of range: {score} (expected {min_val} to {max_val})"
    )


def assert_valid_sun_sign(sign: str) -> None:
    """
    Assert a valid zodiac sign.

    Args:
        sign: Sign name to validate

    Raises:
        AssertionError: If invalid sign
    """
    valid_signs = {
        "aries", "taurus", "gemini", "cancer",
        "leo", "virgo", "libra", "scorpio",
        "sagittarius", "capricorn", "aquarius", "pisces",
    }
    assert sign.lower() in valid_signs, f"Invalid sun sign: {sign}"


def assert_valid_relationship_category(category: str) -> None:
    """
    Assert a valid relationship category.

    Args:
        category: Relationship category to validate

    Raises:
        AssertionError: If invalid category
    """
    valid_categories = {"love", "friend", "family", "coworker", "other"}
    assert category.lower() in valid_categories, f"Invalid relationship category: {category}"


def assert_valid_relationship_label(label: str) -> None:
    """
    Assert a valid relationship label.

    Args:
        label: Relationship label to validate

    Raises:
        AssertionError: If invalid label
    """
    valid_labels = {
        # Love
        "crush", "dating", "situationship", "partner", "boyfriend", "girlfriend", "spouse", "ex",
        # Friend
        "friend", "close_friend", "new_friend",
        # Family
        "mother", "father", "sister", "brother", "daughter", "son", "grandparent", "extended",
        # Coworker
        "manager", "colleague", "mentor", "mentee", "client", "business_partner",
        # Other
        "acquaintance", "neighbor", "ex_friend", "complicated",
    }
    assert label.lower() in valid_labels, f"Invalid relationship label: {label}"


def assert_valid_iso_date(date_str: str) -> None:
    """
    Assert a valid ISO date string (YYYY-MM-DD).

    Args:
        date_str: Date string to validate

    Raises:
        AssertionError: If invalid format
    """
    import re
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    assert re.match(pattern, date_str), f"Invalid ISO date format: {date_str}"


def assert_valid_iso_datetime(dt_str: str) -> None:
    """
    Assert a valid ISO datetime string.

    Args:
        dt_str: Datetime string to validate

    Raises:
        AssertionError: If invalid format
    """
    from datetime import datetime

    try:
        # Try parsing common ISO formats
        for fmt in ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
            try:
                datetime.strptime(dt_str.replace("+00:00", "+0000"), fmt)
                return
            except ValueError:
                continue
        # Try fromisoformat as fallback
        datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError) as e:
        raise AssertionError(f"Invalid ISO datetime format: {dt_str}") from e


def assert_chart_has_planets(chart: dict, count: int = 12) -> None:
    """
    Assert chart has expected number of planets.

    Args:
        chart: NatalChartData dict
        count: Expected planet count (default 12: Sun-Pluto + North Node + South Node)

    Raises:
        AssertionError: If planet count mismatch
    """
    planets = chart.get("planets", [])
    assert len(planets) == count, f"Expected {count} planets, got {len(planets)}"


def assert_chart_has_houses(chart: dict, count: int = 12) -> None:
    """
    Assert chart has expected number of houses.

    Args:
        chart: NatalChartData dict
        count: Expected house count (default 12)

    Raises:
        AssertionError: If house count mismatch
    """
    houses = chart.get("houses", [])
    assert len(houses) == count, f"Expected {count} houses, got {len(houses)}"


def assert_chart_has_angles(chart: dict) -> None:
    """
    Assert chart has all four angles.

    Args:
        chart: NatalChartData dict

    Raises:
        AssertionError: If angles missing
    """
    angles = chart.get("angles", {})
    required = {"ascendant", "descendant", "midheaven", "imum_coeli"}
    actual = set(angles.keys())
    missing = required - actual
    assert not missing, f"Missing chart angles: {missing}"


def wait_for_condition(
    condition_fn,
    timeout_seconds: int = 10,
    poll_interval: float = 0.5,
) -> bool:
    """
    Wait for a condition to become true.

    Args:
        condition_fn: Function that returns True when condition met
        timeout_seconds: Maximum wait time
        poll_interval: Time between checks

    Returns:
        True if condition met, False if timeout
    """
    import time

    start = time.time()
    while time.time() - start < timeout_seconds:
        if condition_fn():
            return True
        time.sleep(poll_interval)
    return False

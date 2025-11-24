"""
PostHog integration utilities for LLM observability.

Provides manual HTTP-based event capture for Gemini LLM generations.
"""

import uuid
import httpx
from datetime import datetime
from google.genai.types import GenerateContentResponseUsageMetadata


POSTHOG_HOST = "https://us.i.posthog.com"


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
        model: Model name (e.g., "gemini-2.5-flash-lite")
        provider: Provider name (e.g., "gemini")
        prompt: Prompt messages
        response: Model output
        usage: UsageMetadata object from Gemini response for token counts
        latency: Latency in seconds
        generation_type: Custom property for generation type
        temperature: Temperature parameter
        max_tokens: Max tokens parameter
        thinking_budget: Thinking budget parameter
    """
    # Cleanup API key
    posthog_api_key = posthog_api_key.replace("\n", '').replace('"', '').replace("'", '').strip()

    # Parse usage
    input_tokens = 0
    output_tokens = 0
    cached_tokens = 0
    if usage:
        # Cached tokens
        if usage.cached_content_token_count:
            cached_tokens = usage.cached_content_token_count
        # Input tokens
        if usage.prompt_token_count:
            input_tokens += usage.prompt_token_count

        # Output tokens need to include candidates + thoughts
        if usage.thoughts_token_count:
            input_tokens += usage.thoughts_token_count
        if usage.candidates_token_count:
            output_tokens = usage.candidates_token_count

    # Format messages
    input_messages = [{
        "role": "user",
        "content": [{"type": "text", "text": prompt[:1000]}]  # Truncate for readability
    }]

    output_messages = [{
        "role": "assistant",
        "content": [{"type": "text", "text": response[:1000]}]  # Truncate for readability
    }]

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

            # Additional parameters
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

        print(f"[PostHog] LLM generation - User: {distinct_id} | Type: {generation_type} | Tokens: {input_tokens}→{output_tokens} | Latency: {latency:.2f}s")

        # Send to PostHog event endpoint
        resp = httpx.post(
            f"{POSTHOG_HOST}/i/v0/e/",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=5.0
        )

        if resp.status_code == 200:
            print("✓ PostHog event captured successfully")
        else:
            print(f"⚠ PostHog failed: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"⚠ PostHog error: {e}")
        import traceback
        traceback.print_exc()

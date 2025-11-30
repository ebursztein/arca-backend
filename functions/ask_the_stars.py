"""
Ask the Stars - Conversational Q&A endpoint with SSE streaming.

Main HTTPS function for real-time streaming responses.
"""

import json
import uuid
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from firebase_functions import https_fn, params, options
from firebase_admin import firestore, auth
from google import genai
from google.genai import types
from jinja2 import Environment, FileSystemLoader

from models import (
    Conversation,
    Message,
    MessageRole,
    UserEntities,
    UserHoroscopes,
    UserProfile,
    MemoryCollection,
    CompressedHoroscope
)
from entity_extraction import get_top_entities_by_importance
from posthog_utils import capture_llm_generation

# Import shared secrets (centralized to avoid duplicate declarations)
from firebase_secrets import GEMINI_API_KEY

# Template path relative to this file - include both conversation and parent for voice.md
TEMPLATES_BASE = Path(__file__).parent / 'templates'
TEMPLATE_DIR = TEMPLATES_BASE / 'conversation'
template_env = Environment(loader=FileSystemLoader([str(TEMPLATE_DIR), str(TEMPLATES_BASE)]))


def stream_ask_the_stars_response(
    question: str,
    horoscope_date: str,
    user_profile: UserProfile,
    horoscope: CompressedHoroscope,
    entities: list,
    memory: MemoryCollection,
    conversation_messages: list[Message],
    mentioned_connections: Optional[list] = None,
    posthog_api_key: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0.7,
    max_tokens: int = 500
):
    """Stream LLM response for Ask the Stars question (synchronous generator)."""
    import time
    start_time = time.time()

    # Get API key (same pattern as llm.py)
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not provided")

    # Create client (same pattern as llm.py)
    gemini_client = genai.Client(api_key=api_key)

    # Calculate age from birth date
    birth_year = int(user_profile.birth_date.split("-")[0])
    age = datetime.now().year - birth_year

    template = template_env.get_template('ask_the_stars.j2')
    prompt = template.render(
        user_name=user_profile.name,
        sun_sign=user_profile.sun_sign,
        birth_date=user_profile.birth_date,
        age=age,
        horoscope_date=horoscope_date,
        horoscope=horoscope,
        entities=entities,
        memory=memory,
        mentioned_connections=mentioned_connections or [],
        messages=conversation_messages,
        question=question
    )

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens
    )

    full_response = ""
    last_usage = None

    # Use synchronous streaming API
    for chunk in gemini_client.models.generate_content_stream(
        model=model,
        contents=prompt,
        config=config
    ):
        if chunk.text:
            full_response += chunk.text
            yield f"data: {json.dumps({'type': 'chunk', 'text': chunk.text})}\n\n"

        # Capture usage from last chunk
        if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
            last_usage = chunk.usage_metadata

    # Capture to PostHog after streaming completes
    if posthog_api_key:
        latency_seconds = time.time() - start_time
        capture_llm_generation(
            posthog_api_key=posthog_api_key,
            distinct_id=user_profile.user_id,
            model=model,
            provider="gemini",
            prompt=prompt,
            response=full_response[:1000],  # Truncate for readability
            usage=last_usage,
            latency=latency_seconds,
            generation_type="ask_the_stars_streaming",
            temperature=temperature,
            max_tokens=max_tokens
        )

    # Return full response for caller to use
    return full_response


@https_fn.on_request(
    memory=512,  # Bumped from default 256MB to avoid OOM
    cors=options.CorsOptions(
        cors_origins="*",
        cors_methods=["POST", "OPTIONS"]
    ),
    secrets=[GEMINI_API_KEY]
)
def ask_the_stars(req: https_fn.Request) -> https_fn.Response:
    """
    HTTPS endpoint: Ask the Stars with SSE streaming.

    Conversational Q&A about today's horoscope. Streams responses in real-time
    via Server-Sent Events (SSE). Uses the user's latest stored horoscope.

    Authentication:
        Authorization: Bearer <firebase_id_token>
        Dev mode: Bearer dev_arca_2025 (requires user_id in body)

    Expected request data:
    {
        "question": "string",       // The user's question (required)
        "conversation_id": "string", // Optional - continue existing conversation
        "user_id": "string"         // Optional - required only with dev token
    }

    SSE Response Events:
        Content-Type: text/event-stream

        Chunk events (streamed as LLM generates):
            data: {"type": "chunk", "text": "partial response text..."}

        Done event (sent when complete):
            data: {"type": "done", "conversation_id": "conv_abc123", "message_id": "msg_xyz789"}

    Returns:
        AskTheStarsSSEResponse - SSE stream with events:
        - type="chunk": Partial text (string) as LLM generates
        - type="done": Final event with conversation_id (string) and message_id (string)
    """
    if req.method == "OPTIONS":
        return https_fn.Response(status=204)

    # Parse request
    try:
        body = req.get_json()
        question = body.get('question')
        conversation_id = body.get('conversation_id')

        if not question:
            return https_fn.Response(
                json.dumps({"error": "Missing question"}),
                status=400,
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": f"Invalid request: {str(e)}"}),
            status=400,
            headers={"Content-Type": "application/json"}
        )

    # Authenticate user (iOS sends Firebase ID token or dev token)
    # DEV MODE: Use static token "dev_arca_2025" with user_id from body
    DEV_TOKEN = "dev_arca_2025"

    try:
        auth_header = req.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return https_fn.Response(
                json.dumps({"error": "Missing Authorization header"}),
                status=401,
                headers={"Content-Type": "application/json"}
            )

        token = auth_header.split('Bearer ')[1]

        # Dev mode bypass - use user_id from request body
        if token == DEV_TOKEN:
            user_id = body.get('user_id')
            if not user_id:
                return https_fn.Response(
                    json.dumps({"error": "Dev mode requires user_id in body"}),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
        else:
            # Production: verify Firebase ID token
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']
    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": f"Authentication failed: {str(e)}"}),
            status=401,
            headers={"Content-Type": "application/json"}
        )

    # Fetch data (4-5 reads total)
    db = firestore.client(database_id="(default)")

    try:
        # 1. User profile
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return https_fn.Response(
                json.dumps({"error": "User not found"}),
                status=404,
                headers={"Content-Type": "application/json"}
            )
        user_data = user_doc.to_dict()
        user_profile = UserProfile(**user_data)

        # 2. Horoscope (compressed) - use most recent from latest document
        horoscope_doc = db.collection('users').document(user_id).collection('horoscopes').document('latest').get()
        if not horoscope_doc.exists:
            return https_fn.Response(
                json.dumps({"error": "No horoscopes found"}),
                status=404,
                headers={"Content-Type": "application/json"}
            )
        horoscopes_data = UserHoroscopes(**horoscope_doc.to_dict())
        if not horoscopes_data.horoscopes:
            return https_fn.Response(
                json.dumps({"error": "No horoscopes found"}),
                status=404,
                headers={"Content-Type": "application/json"}
            )
        # Use the most recent horoscope (sorted by date descending)
        from models import CompressedHoroscope
        latest_date = sorted(horoscopes_data.horoscopes.keys(), reverse=True)[0]
        horoscope = CompressedHoroscope(**horoscopes_data.horoscopes[latest_date])

        # 3. Entities
        entities_doc = db.collection('users').document(user_id).collection('entities').document('all').get()
        if entities_doc.exists:
            user_entities = UserEntities(**entities_doc.to_dict())
            top_entities = get_top_entities_by_importance(user_entities.entities, limit=15)
        else:
            top_entities = []

        # 3b. Connections - check if question mentions any connection names
        connections_ref = db.collection('users').document(user_id).collection('connections')
        connections_docs = connections_ref.limit(20).get()
        all_connections = []
        mentioned_connections = []

        # Normalize question for matching (lowercase, split into words)
        import re
        question_lower = question.lower()
        question_words = set(re.findall(r'\b\w+\b', question_lower))

        for doc in connections_docs:
            conn_data = doc.to_dict()
            conn_data['connection_id'] = doc.id
            all_connections.append(conn_data)

            # Check if connection name (or any part of it) appears in question
            # This handles "John" matching "John Smith" and vice versa
            conn_name = conn_data.get('name', '').lower()
            if not conn_name:
                continue

            conn_name_words = set(re.findall(r'\b\w+\b', conn_name))

            # Match if ANY word from connection name appears in question
            # This catches "John" in "What about John?" or "Johnny" won't match "John"
            if conn_name_words & question_words:  # Set intersection
                mentioned_connections.append(conn_data)

        # 3c. Calculate synastry aspects for mentioned connections (use cached if available)
        if mentioned_connections and user_data.get('natal_chart'):
            from astro import NatalChartData, compute_birth_chart
            from compatibility import calculate_compatibility

            user_chart = NatalChartData(**user_data['natal_chart'])

            for conn in mentioned_connections:
                # Skip if already has cached synastry_aspects
                if conn.get('synastry_aspects'):
                    continue

                # Calculate on-the-fly if not cached
                if conn.get('birth_date'):
                    try:
                        conn_chart_dict, _ = compute_birth_chart(
                            birth_date=conn['birth_date'],
                            birth_time=conn.get('birth_time'),
                            birth_timezone=conn.get('birth_timezone'),
                            birth_lat=conn.get('birth_lat'),
                            birth_lon=conn.get('birth_lon')
                        )
                        conn_chart = NatalChartData(**conn_chart_dict)
                        compatibility = calculate_compatibility(user_chart, conn_chart)

                        # Get top 5 tightest aspects
                        sorted_aspects = sorted(compatibility.aspects, key=lambda a: a.orb)[:5]
                        conn['synastry_aspects'] = [
                            {
                                "user_planet": asp.user_planet,
                                "their_planet": asp.their_planet,
                                "aspect_type": asp.aspect_type,
                                "is_harmonious": asp.is_harmonious
                            }
                            for asp in sorted_aspects
                        ]
                    except Exception as e:
                        print(f"Failed to calc synastry for {conn.get('name')}: {e}")

        # 4. Memory
        memory_doc = db.collection('memory').document(user_id).get()
        if memory_doc.exists:
            memory = MemoryCollection(**memory_doc.to_dict())
        else:
            from models import create_empty_memory
            memory = create_empty_memory(user_id)

        # 5. Conversation (optional)
        conversation_messages = []
        if conversation_id:
            conv_doc = db.collection('conversations').document(conversation_id).get()
            if conv_doc.exists:
                conversation = Conversation(**conv_doc.to_dict())
                conversation_messages = conversation.messages

    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": f"Failed to fetch data: {str(e)}"}),
            status=500,
            headers={"Content-Type": "application/json"}
        )

    # Stream response
    def generate():
        full_response = ""
        for chunk in stream_ask_the_stars_response(
            question=question,
            horoscope_date=latest_date,
            user_profile=user_profile,
            horoscope=horoscope,
            entities=top_entities,
            memory=memory,
            conversation_messages=conversation_messages,
            mentioned_connections=mentioned_connections,
            api_key=GEMINI_API_KEY.value
        ):
            chunk_data = json.loads(chunk.split('data: ')[1])
            full_response += chunk_data.get('text', '')
            yield chunk

        # Save messages after streaming
        user_message = Message(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            role=MessageRole.USER,
            content=question,
            timestamp=datetime.now().isoformat()
        )

        assistant_message = Message(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            role=MessageRole.ASSISTANT,
            content=full_response,
            timestamp=datetime.now().isoformat()
        )

        # Create or update conversation
        if not conversation_id:
            new_conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
            conversation = Conversation(
                conversation_id=new_conversation_id,
                user_id=user_id,
                horoscope_date=latest_date,
                messages=[user_message, assistant_message],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            db.collection('conversations').document(new_conversation_id).set(conversation.model_dump())
            final_conversation_id = new_conversation_id
        else:
            conversation_messages.extend([user_message, assistant_message])
            db.collection('conversations').document(conversation_id).update({
                'messages': [m.model_dump() for m in conversation_messages],
                'updated_at': datetime.now().isoformat()
            })
            final_conversation_id = conversation_id

        # Done event
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': final_conversation_id, 'message_id': assistant_message.message_id})}\n\n"

    return https_fn.Response(
        generate(),
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

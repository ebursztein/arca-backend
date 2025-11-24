"""
Ask the Stars - Conversational Q&A endpoint with SSE streaming.

Main HTTPS function for real-time streaming responses.
"""

import json
import uuid
import os
from datetime import datetime
from typing import AsyncGenerator, Optional
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
    DailyHoroscope
)
from entity_extraction import get_top_entities_by_importance
from posthog_utils import capture_llm_generation

GEMINI_API_KEY = params.SecretParam("GEMINI_API_KEY")

# Template path relative to this file
TEMPLATE_DIR = Path(__file__).parent / 'templates' / 'conversation'
template_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


async def stream_ask_the_stars_response(
    question: str,
    horoscope_date: str,
    user_profile: UserProfile,
    horoscope: DailyHoroscope,
    entities: list,
    memory: MemoryCollection,
    conversation_messages: list[Message],
    gemini_client: genai.Client,
    posthog_api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0.7,
    max_tokens: int = 500
) -> AsyncGenerator[str, None]:
    """Stream LLM response for Ask the Stars question."""
    import time
    start_time = time.time()

    template = template_env.get_template('ask_the_stars.j2')
    prompt = template.render(
        user_name=user_profile.name,
        sun_sign=user_profile.sun_sign,
        horoscope_date=horoscope_date,
        horoscope=horoscope,
        entities=entities,
        messages=conversation_messages,
        question=question
    )

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens
    )

    full_response = ""
    last_usage = None

    async for chunk in await gemini_client.aio.models.generate_content_stream(
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


@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins="*",
        cors_methods=["POST", "OPTIONS"]
    ),
    secrets=[GEMINI_API_KEY]
)
async def ask_the_stars(req: https_fn.Request) -> https_fn.Response:
    """
    HTTPS endpoint: Ask the Stars with SSE streaming.

    iOS sends:
    - Authorization: Bearer <firebase_id_token>
    - Body: {"question": "...", "horoscope_date": "2025-01-20", "conversation_id": "..."}

    Returns: Server-Sent Events stream
    """
    if req.method == "OPTIONS":
        return https_fn.Response(status=204)

    # Parse request
    try:
        body = req.get_json()
        question = body.get('question')
        horoscope_date = body.get('horoscope_date')
        conversation_id = body.get('conversation_id')

        if not question or not horoscope_date:
            return https_fn.Response(
                json.dumps({"error": "Missing question or horoscope_date"}),
                status=400,
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": f"Invalid request: {str(e)}"}),
            status=400,
            headers={"Content-Type": "application/json"}
        )

    # Authenticate user (iOS sends Firebase ID token)
    try:
        auth_header = req.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return https_fn.Response(
                json.dumps({"error": "Missing Authorization header"}),
                status=401,
                headers={"Content-Type": "application/json"}
            )

        id_token = auth_header.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": f"Authentication failed: {str(e)}"}),
            status=401,
            headers={"Content-Type": "application/json"}
        )

    # Fetch data (4-5 reads total)
    db = firestore.client()

    try:
        # 1. User profile
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return https_fn.Response(
                json.dumps({"error": "User not found"}),
                status=404,
                headers={"Content-Type": "application/json"}
            )
        user_profile = UserProfile(**user_doc.to_dict())

        # 2. Horoscope
        horoscope_doc = db.collection('users').document(user_id).collection('horoscopes').document('all').get()
        if not horoscope_doc.exists:
            return https_fn.Response(
                json.dumps({"error": "No horoscopes found"}),
                status=404,
                headers={"Content-Type": "application/json"}
            )
        horoscopes_data = UserHoroscopes(**horoscope_doc.to_dict())
        if horoscope_date not in horoscopes_data.horoscopes:
            return https_fn.Response(
                json.dumps({"error": f"Horoscope for {horoscope_date} not found"}),
                status=404,
                headers={"Content-Type": "application/json"}
            )
        horoscope = DailyHoroscope(**horoscopes_data.horoscopes[horoscope_date])

        # 3. Entities
        entities_doc = db.collection('users').document(user_id).collection('entities').document('all').get()
        if entities_doc.exists:
            user_entities = UserEntities(**entities_doc.to_dict())
            top_entities = get_top_entities_by_importance(user_entities.entities, limit=15)
        else:
            top_entities = []

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

    # Initialize Gemini
    gemini_client = genai.Client(api_key=GEMINI_API_KEY.value)

    # Stream response
    async def generate():
        full_response = ""
        async for chunk in stream_ask_the_stars_response(
            question=question,
            horoscope_date=horoscope_date,
            user_profile=user_profile,
            horoscope=horoscope,
            entities=top_entities,
            memory=memory,
            conversation_messages=conversation_messages,
            gemini_client=gemini_client
        ):
            chunk_data = json.loads(chunk.split('data: ')[1])
            full_response += chunk_data['text']
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
                horoscope_date=horoscope_date,
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

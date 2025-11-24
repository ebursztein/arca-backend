"""
Firestore triggers for Ask the Stars feature.

Background processing for entity extraction and updates.
"""

import asyncio
from datetime import datetime
from firebase_functions import firestore_fn, params
from firebase_admin import firestore
from google import genai

from models import (
    Conversation,
    UserEntities,
    MessageRole
)
from entity_extraction import (
    extract_entities_from_message,
    merge_entities_with_existing,
    execute_merge_actions
)

# Define secrets
GEMINI_API_KEY = params.SecretParam("GEMINI_API_KEY")


@firestore_fn.on_document_written(
    document="conversations/{conversationId}",
    secrets=[GEMINI_API_KEY]
)
def extract_entities_on_message(
    event: firestore_fn.Event[firestore_fn.Change[firestore_fn.DocumentSnapshot] | None]
) -> None:
    """
    Background trigger: Extract and merge entities when conversation is updated.

    Fires when a conversation document is created or updated.
    Extracts entities from the latest user message only (skips assistant messages).

    This runs asynchronously after the user receives their response - no user latency.
    """
    if not event.data or not event.data.after:
        return

    conv_data = event.data.after.to_dict()
    if not conv_data:
        return

    conversation = Conversation(**conv_data)

    if not conversation.messages:
        return

    latest_message = conversation.messages[-1]

    # Skip if assistant message (only process user messages)
    if latest_message.role != MessageRole.USER:
        return

    # Run async entity extraction
    asyncio.run(_extract_and_merge_entities(
        user_id=conversation.user_id,
        user_message=latest_message.content,
        horoscope_date=conversation.horoscope_date,
        gemini_api_key=GEMINI_API_KEY.value
    ))


async def _extract_and_merge_entities(
    user_id: str,
    user_message: str,
    horoscope_date: str,
    gemini_api_key: str
) -> None:
    """Extract entities from message and merge with existing."""
    client = genai.Client(api_key=gemini_api_key)
    db = firestore.client()

    # Fetch existing entities (1 read)
    entities_ref = db.collection('users').document(user_id).collection('entities').document('all')
    entities_doc = entities_ref.get()

    if entities_doc.exists:
        user_entities = UserEntities(**entities_doc.to_dict())
        existing_entities = user_entities.entities
    else:
        existing_entities = []

    # LLM CALL 1: Extract entities
    extracted = await extract_entities_from_message(
        user_message=user_message,
        current_date=horoscope_date,
        gemini_client=client,
        model="gemini-2.0-flash-exp"
    )

    if not extracted.entities:
        return

    # LLM CALL 2: Merge with existing
    merged = await merge_entities_with_existing(
        extracted_entities=extracted,
        existing_entities=existing_entities,
        current_date=horoscope_date,
        gemini_client=client,
        model="gemini-2.0-flash-exp"
    )

    if not merged.actions:
        return

    # Execute merge actions
    updated_entities = execute_merge_actions(
        actions=merged,
        existing_entities=existing_entities,
        current_time=datetime.now()
    )

    # Update entities document (1 write)
    entities_ref.set({
        'user_id': user_id,
        'entities': [e.model_dump() for e in updated_entities],
        'updated_at': datetime.now().isoformat()
    })

    # Update memory collection (1 write)
    memory_ref = db.collection('memory').document(user_id)
    memory_doc = memory_ref.get()

    if memory_doc.exists:
        entity_summary = {}
        for entity in updated_entities:
            entity_summary[entity.entity_type] = entity_summary.get(entity.entity_type, 0) + 1

        memory_ref.update({
            'entity_summary': entity_summary,
            'last_conversation_date': horoscope_date,
            'total_conversations': firestore.Increment(1),
            'updated_at': datetime.now().isoformat()
        })

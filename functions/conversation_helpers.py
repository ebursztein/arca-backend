"""
Helper callable functions for Ask the Stars feature.

- get_conversation_history
- get_user_entities
- update_entity
- delete_entity
"""

from firebase_functions import https_fn
from firebase_admin import firestore

from models import (
    Conversation,
    UserEntities,
    Entity,
    EntityStatus
)


@https_fn.on_call()
def get_conversation_history(req: https_fn.CallableRequest) -> dict:
    """
    Get full conversation with all messages.

    Args:
        conversation_id (str): Conversation ID to fetch

    Returns:
        { "conversation": Conversation }
    """
    # Authenticate
    if not req.auth:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="Authentication required"
        )

    user_id = req.auth.uid
    conversation_id = req.data.get('conversation_id')

    if not conversation_id:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="Missing conversation_id"
        )

    # Fetch conversation
    db = firestore.client()
    conv_doc = db.collection('conversations').document(conversation_id).get()

    if not conv_doc.exists:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message="Conversation not found"
        )

    conversation = Conversation(**conv_doc.to_dict())

    # Verify ownership
    if conversation.user_id != user_id:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.PERMISSION_DENIED,
            message="Not authorized to access this conversation"
        )

    return {"conversation": conversation.model_dump()}


@https_fn.on_call()
def get_user_entities(req: https_fn.CallableRequest) -> dict:
    """
    Get user's entities with optional filtering.

    Args:
        status (str, optional): Filter by status: "active", "archived", "resolved"
        limit (int, optional): Max entities to return (default 50)

    Returns:
        { "entities": Entity[], "total_count": int }
    """
    if not req.auth:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="Authentication required"
        )

    user_id = req.auth.uid
    status_filter = req.data.get('status')
    limit = req.data.get('limit', 50)

    # Fetch entities
    db = firestore.client()
    entities_doc = db.collection('users').document(user_id).collection('entities').document('all').get()

    if not entities_doc.exists:
        return {"entities": [], "total_count": 0}

    user_entities = UserEntities(**entities_doc.to_dict())
    entities = user_entities.entities

    # Filter by status if provided
    if status_filter:
        try:
            status_enum = EntityStatus(status_filter)
            entities = [e for e in entities if e.status == status_enum]
        except ValueError:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message=f"Invalid status: {status_filter}"
            )

    # Sort by importance score (descending)
    entities.sort(key=lambda e: e.importance_score, reverse=True)

    # Limit results
    entities = entities[:limit]

    return {
        "entities": [e.model_dump() for e in entities],
        "total_count": len(user_entities.entities)
    }


@https_fn.on_call()
def update_entity(req: https_fn.CallableRequest) -> dict:
    """
    Update an entity (status, aliases, context).

    Args:
        entity_id (str): Entity ID to update
        status (str, optional): New status: "active", "archived", "resolved"
        add_aliases (str[], optional): Aliases to add
        add_context (str, optional): Context snippet to add

    Returns:
        { "success": true, "entity": Entity }
    """
    if not req.auth:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="Authentication required"
        )

    user_id = req.auth.uid
    entity_id = req.data.get('entity_id')

    if not entity_id:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="Missing entity_id"
        )

    # Fetch entities
    db = firestore.client()
    entities_ref = db.collection('users').document(user_id).collection('entities').document('all')
    entities_doc = entities_ref.get()

    if not entities_doc.exists:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message="No entities found"
        )

    user_entities = UserEntities(**entities_doc.to_dict())

    # Find entity
    target_entity = None
    for entity in user_entities.entities:
        if entity.entity_id == entity_id:
            target_entity = entity
            break

    if not target_entity:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message="Entity not found"
        )

    # Apply updates
    if 'status' in req.data:
        try:
            target_entity.status = EntityStatus(req.data['status'])
        except ValueError:
            raise https_fn.HttpsError(
                code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                message=f"Invalid status: {req.data['status']}"
            )

    if 'add_aliases' in req.data:
        for alias in req.data['add_aliases']:
            if alias not in target_entity.aliases:
                target_entity.aliases.append(alias)

    if 'add_context' in req.data:
        target_entity.context_snippets.append(req.data['add_context'])
        if len(target_entity.context_snippets) > 10:
            target_entity.context_snippets = target_entity.context_snippets[-10:]

    from datetime import datetime
    target_entity.updated_at = datetime.now().isoformat()

    # Save updates
    entities_ref.set({
        'user_id': user_id,
        'entities': [e.model_dump() for e in user_entities.entities],
        'updated_at': datetime.now().isoformat()
    })

    return {
        "success": True,
        "entity": target_entity.model_dump()
    }


@https_fn.on_call()
def delete_entity(req: https_fn.CallableRequest) -> dict:
    """
    Delete an entity permanently.

    Args:
        entity_id (str): Entity ID to delete

    Returns:
        { "success": true }
    """
    if not req.auth:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="Authentication required"
        )

    user_id = req.auth.uid
    entity_id = req.data.get('entity_id')

    if not entity_id:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="Missing entity_id"
        )

    # Fetch entities
    db = firestore.client()
    entities_ref = db.collection('users').document(user_id).collection('entities').document('all')
    entities_doc = entities_ref.get()

    if not entities_doc.exists:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message="No entities found"
        )

    user_entities = UserEntities(**entities_doc.to_dict())

    # Remove entity
    updated_entities = [e for e in user_entities.entities if e.entity_id != entity_id]

    if len(updated_entities) == len(user_entities.entities):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message="Entity not found"
        )

    # Save updates
    from datetime import datetime
    entities_ref.set({
        'user_id': user_id,
        'entities': [e.model_dump() for e in updated_entities],
        'updated_at': datetime.now().isoformat()
    })

    return {"success": True}

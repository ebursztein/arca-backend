"""
Entity extraction and merging for Ask the Stars feature.

This module handles:
1. Extracting entities from user messages (LLM call 1)
2. Merging entities with existing tracked entities (LLM call 2)
3. Executing merge actions to update entity store
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from google import genai
from google.genai import types

load_dotenv()

from models import (
    Entity,
    ExtractedEntities,
    MergedEntities,
    EntityStatus,
    AttributeKV,
    calculate_entity_importance_score
)
from posthog_utils import capture_llm_generation

# Initialize Jinja2 environment
import os
template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'conversation')
template_env = Environment(loader=FileSystemLoader(template_dir))


def merge_attributes(existing: list[AttributeKV], updates: list[AttributeKV]) -> list[AttributeKV]:
    """
    Merge attribute updates into existing attributes.
    Updates existing keys or adds new ones.
    """
    # Convert to dict for easy merging
    attrs_dict = {attr.key: attr.value for attr in existing}

    # Apply updates
    for update in updates:
        attrs_dict[update.key] = update.value

    # Convert back to list
    return [AttributeKV(key=k, value=v) for k, v in attrs_dict.items()]



def extract_entities_from_message(
    user_message: str,
    current_date: str,
    user_id: str,
    posthog_api_key: Optional[str] = None,
    api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0.0
) -> tuple[ExtractedEntities, dict]:
    """
    Extract entities from user message using LLM structured output.

    Args:
        user_message: User's message text
        current_date: Current ISO date for temporal attribute extraction
        user_id: User ID for PostHog tracking
        posthog_api_key: PostHog API key for observability
        api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        model: Model to use for extraction
        temperature: LLM temperature (default 0 for consistency)

    Returns:
        Tuple of (ExtractedEntities, performance_dict)
    """
    import time
    start_time = time.time()

    # Get API key (same pattern as llm.py)
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not provided")

    # Create client (same pattern as llm.py)
    client = genai.Client(api_key=api_key)

    # Load and render template
    template = template_env.get_template('extract_entities.j2')
    prompt = template.render(
        user_message=user_message,
        current_date=current_date
    )

    # Configure LLM for structured output
    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        response_schema=ExtractedEntities
    )

    # Call LLM (synchronous - async has DNS issues with httpx)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config
    )

    # Calculate performance
    elapsed_ms = int((time.time() - start_time) * 1000)
    latency_seconds = elapsed_ms / 1000.0
    performance = {
        "model": model,
        "time_ms": elapsed_ms,
        "usage": dict(response.usage_metadata) if hasattr(response, 'usage_metadata') else {}
    }

    # Parse structured output
    parsed = response.parsed

    # Capture to PostHog
    if posthog_api_key:
        response_summary = f"Extracted {len(parsed.entities)} entities: " + ", ".join([e.name for e in parsed.entities[:5]])
        capture_llm_generation(
            posthog_api_key=posthog_api_key,
            distinct_id=user_id,
            model=model,
            provider="gemini",
            prompt=prompt,
            response=response_summary,
            usage=response.usage_metadata if hasattr(response, 'usage_metadata') else None,
            latency=latency_seconds,
            generation_type="entity_extraction",
            temperature=temperature,
            max_tokens=0
        )

    return parsed, performance


def merge_entities_with_existing(
    extracted_entities: ExtractedEntities,
    existing_entities: list[Entity],
    current_date: str,
    gemini_client: genai.Client,
    user_id: str,
    posthog_api_key: Optional[str] = None,
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0.0
) -> tuple[MergedEntities, dict]:
    """
    Merge newly extracted entities with existing entities using LLM.

    Determines which entities are:
    - NEW (create)
    - DUPLICATES (merge)
    - UPDATES (add context/attributes)
    - LINKS (create relationships)

    Args:
        extracted_entities: Entities extracted from user message
        existing_entities: Current tracked entities
        current_date: Current ISO date
        gemini_client: Gemini API client
        user_id: User ID for PostHog tracking
        posthog_api_key: PostHog API key for observability
        model: Model to use for merging
        temperature: LLM temperature (default 0 for consistency)

    Returns:
        Tuple of (MergedEntities, performance_dict)
    """
    import time
    start_time = time.time()

    # Prepare existing entities as JSON for prompt
    existing_entities_json = json.dumps(
        [e.model_dump() for e in existing_entities],
        indent=2
    )

    # Prepare extracted entities as JSON
    extracted_entities_json = json.dumps(
        extracted_entities.model_dump()['entities'],
        indent=2
    )

    # Load and render template
    template = template_env.get_template('merge_entities.j2')
    prompt = template.render(
        existing_entities_json=existing_entities_json,
        extracted_entities_json=extracted_entities_json,
        current_date=current_date
    )

    # Configure LLM for structured output
    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        response_schema=MergedEntities
    )

    # Call LLM (synchronous - async has DNS issues with httpx)
    response = gemini_client.models.generate_content(
        model=model,
        contents=prompt,
        config=config
    )

    # Calculate performance
    elapsed_ms = int((time.time() - start_time) * 1000)
    latency_seconds = elapsed_ms / 1000.0
    performance = {
        "model": model,
        "time_ms": elapsed_ms,
        "usage": dict(response.usage_metadata) if hasattr(response, 'usage_metadata') else {}
    }

    # Parse structured output
    parsed = response.parsed

    # Capture to PostHog
    if posthog_api_key:
        response_summary = f"Generated {len(parsed.actions)} merge actions: " + ", ".join([f"{a.action}:{a.entity_name}" for a in parsed.actions[:5]])
        capture_llm_generation(
            posthog_api_key=posthog_api_key,
            distinct_id=user_id,
            model=model,
            provider="gemini",
            prompt=prompt,
            response=response_summary,
            usage=response.usage_metadata if hasattr(response, 'usage_metadata') else None,
            latency=latency_seconds,
            generation_type="entity_merging",
            temperature=temperature,
            max_tokens=0
        )

    return parsed, performance


def execute_merge_actions(
    actions: MergedEntities,
    existing_entities: list[Entity],
    current_time: Optional[datetime] = None
) -> list[Entity]:
    """
    Execute merge actions to update entity list.

    IMPORTANT: This function does NOT mutate the input entities.
    It creates deep copies before any modifications.

    Args:
        actions: MergedEntities with list of actions
        existing_entities: Current tracked entities
        current_time: Current datetime (defaults to now)

    Returns:
        Updated list of entities (new copies, inputs unchanged)
    """
    if current_time is None:
        current_time = datetime.now()

    now_iso = current_time.isoformat()

    # Create deep copies to avoid mutating inputs
    # Use model_copy(deep=True) for Pydantic v2
    entities_dict = {e.entity_id: e.model_copy(deep=True) for e in existing_entities}

    # Also create lookup by name (lowercase) for finding entities
    entities_by_name = {e.name.lower(): entities_dict[e.entity_id] for e in existing_entities}

    for action in actions.actions:
        if action.action == "create":
            # Create new entity
            new_entity = Entity(
                entity_id=f"ent_{uuid.uuid4().hex[:8]}",
                name=action.entity_name,
                entity_type=action.entity_type,
                status=EntityStatus.ACTIVE,
                aliases=[],
                attributes=action.attribute_updates,
                related_entities=[],
                first_seen=now_iso,
                last_seen=now_iso,
                mention_count=1,
                context_snippets=[action.context_update] if action.context_update else [],
                importance_score=0.5,  # Default for new entities
                created_at=now_iso,
                updated_at=now_iso
            )

            # Add relationship link if specified
            if action.link_to_entity_id:
                new_entity.related_entities.append(action.link_to_entity_id)

            entities_dict[new_entity.entity_id] = new_entity

        elif action.action == "merge":
            # Merge with existing entity
            if action.merge_with_id in entities_dict:
                existing = entities_dict[action.merge_with_id]

                # Add new alias if provided
                if action.new_alias and action.new_alias.lower() not in [a.lower() for a in existing.aliases]:
                    existing.aliases.append(action.new_alias)

                # Update attributes (merge, don't overwrite)
                existing.attributes = merge_attributes(existing.attributes, action.attribute_updates)

                # Add context snippet
                if action.context_update:
                    existing.context_snippets.append(action.context_update)
                    # Keep only last 10 snippets (FIFO)
                    if len(existing.context_snippets) > 10:
                        existing.context_snippets = existing.context_snippets[-10:]

                # Update tracking
                existing.last_seen = now_iso
                existing.mention_count += 1
                existing.updated_at = now_iso

                # Recalculate importance score
                existing.importance_score = calculate_entity_importance_score(
                    existing,
                    current_time
                )

                # Add relationship link if specified
                if action.link_to_entity_id and action.link_to_entity_id not in existing.related_entities:
                    existing.related_entities.append(action.link_to_entity_id)

        elif action.action == "update":
            # Update existing entity (by name or ID)
            target_entity = None

            # Try to find by merge_with_id first
            if action.merge_with_id and action.merge_with_id in entities_dict:
                target_entity = entities_dict[action.merge_with_id]
            # Otherwise find by name
            elif action.entity_name.lower() in entities_by_name:
                target_entity = entities_by_name[action.entity_name.lower()]

            if target_entity:
                # Update attributes
                target_entity.attributes = merge_attributes(target_entity.attributes, action.attribute_updates)

                # Add context snippet
                if action.context_update:
                    target_entity.context_snippets.append(action.context_update)
                    if len(target_entity.context_snippets) > 10:
                        target_entity.context_snippets = target_entity.context_snippets[-10:]

                # Update tracking
                target_entity.last_seen = now_iso
                target_entity.mention_count += 1
                target_entity.updated_at = now_iso

                # Recalculate importance score
                target_entity.importance_score = calculate_entity_importance_score(
                    target_entity,
                    current_time
                )

                # Add relationship link if specified
                if action.link_to_entity_id and action.link_to_entity_id not in target_entity.related_entities:
                    target_entity.related_entities.append(action.link_to_entity_id)

        elif action.action == "link":
            # Create relationship link between entities
            # Find source entity
            source_entity = None
            if action.merge_with_id and action.merge_with_id in entities_dict:
                source_entity = entities_dict[action.merge_with_id]
            elif action.entity_name.lower() in entities_by_name:
                source_entity = entities_by_name[action.entity_name.lower()]

            if source_entity and action.link_to_entity_id:
                if action.link_to_entity_id not in source_entity.related_entities:
                    source_entity.related_entities.append(action.link_to_entity_id)
                    source_entity.updated_at = now_iso

    return list(entities_dict.values())


def get_top_entities_by_importance(
    entities: list[Entity],
    limit: int = 15,
    current_time: Optional[datetime] = None
) -> list[Entity]:
    """
    Get top N entities sorted by importance score.

    Args:
        entities: List of all entities
        limit: Maximum number of entities to return
        current_time: Current datetime for score calculation

    Returns:
        Top N entities by importance score
    """
    # Recalculate importance scores
    for entity in entities:
        entity.importance_score = calculate_entity_importance_score(
            entity,
            current_time
        )

    # Filter active entities only
    active_entities = [e for e in entities if e.status == EntityStatus.ACTIVE]

    # Sort by importance score (descending)
    sorted_entities = sorted(
        active_entities,
        key=lambda e: e.importance_score,
        reverse=True
    )

    return sorted_entities[:limit]


def route_people_to_connections(
    entities: list[Entity],
    connections: list[dict],
    context_date: str
) -> tuple[list[Entity], list[dict]]:
    """
    Route person entities to Connection.arca_notes instead of entity bank.

    For each entity with entity_type="relationship" (a person), check if
    there's a matching Connection by name. If matched, add the context
    to Connection.arca_notes and exclude from entity list.

    Args:
        entities: List of entities after merge actions
        connections: List of user's Connection dicts from Firestore
        context_date: ISO date string for the note

    Returns:
        Tuple of (filtered_entities, connection_updates)
        - filtered_entities: Entities with matched people removed
        - connection_updates: List of {connection_id, note} to update
    """
    if not connections:
        return entities, []

    # Build lookup by name (lowercase) and aliases
    connection_by_name = {}
    for conn in connections:
        conn_name = conn.get("name", "").lower()
        if conn_name:
            connection_by_name[conn_name] = conn
        # Also check aliases if present
        for alias in conn.get("aliases", []):
            if alias:
                connection_by_name[alias.lower()] = conn

    filtered_entities = []
    connection_updates = []

    for entity in entities:
        # Only route relationship entities (people)
        if entity.entity_type != "relationship":
            filtered_entities.append(entity)
            continue

        # Try to match by name or aliases
        matched_connection = None
        names_to_check = [entity.name.lower()] + [a.lower() for a in entity.aliases]

        for name in names_to_check:
            if name in connection_by_name:
                matched_connection = connection_by_name[name]
                break

        if matched_connection:
            # Route to Connection.arca_notes
            latest_context = entity.context_snippets[-1] if entity.context_snippets else ""
            connection_id = matched_connection.get("connection_id")
            # Only create update if we have both context and a valid connection_id
            if latest_context and connection_id:
                connection_updates.append({
                    "connection_id": connection_id,
                    "note": {
                        "date": context_date,
                        "note": latest_context,
                        "context": "ask_the_stars"
                    }
                })
            # Don't add to filtered entities - person is tracked via Connection
        else:
            # No matching connection - keep in entity bank
            filtered_entities.append(entity)

    return filtered_entities, connection_updates

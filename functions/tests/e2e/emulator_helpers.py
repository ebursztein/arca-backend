"""
Firebase Emulator Helpers for E2E tests.

Provides utilities for:
- Checking if emulator is running
- Getting emulator Firestore client
- Seeding test data
- Cleaning up test data
"""
import os
import socket
from typing import Optional


def is_emulator_running(host: str = "localhost", port: int = 8080) -> bool:
    """
    Check if Firestore emulator is running.

    Args:
        host: Emulator host (default localhost)
        port: Emulator port (default 8080)

    Returns:
        True if emulator is running and accepting connections
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_emulator_client():
    """
    Get Firestore client connected to local emulator.

    Sets FIRESTORE_EMULATOR_HOST environment variable and
    initializes Firebase app if needed.

    Returns:
        Firestore client connected to emulator
    """
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"

    # Initialize Firebase app if not already done
    import firebase_admin
    from firebase_admin import firestore

    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app()

    return firestore.client(database_id="(default)")


def clear_collection(db, collection_path: str) -> int:
    """
    Clear all documents in a collection.

    Args:
        db: Firestore client
        collection_path: Path to collection

    Returns:
        Number of documents deleted
    """
    docs = db.collection(collection_path).stream()
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    return count


def clear_subcollection(db, parent_path: str, subcollection: str) -> int:
    """
    Clear all documents in a subcollection.

    Args:
        db: Firestore client
        parent_path: Path to parent document (e.g., "users/user123")
        subcollection: Name of subcollection (e.g., "connections")

    Returns:
        Number of documents deleted
    """
    docs = db.document(parent_path).collection(subcollection).stream()
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    return count


def clear_test_data(db, test_user_id: str) -> dict:
    """
    Clear all data for a test user.

    Args:
        db: Firestore client
        test_user_id: User ID to clear

    Returns:
        Dict with counts of deleted documents per collection
    """
    counts = {}

    # Delete user document
    db.collection("users").document(test_user_id).delete()
    counts["users"] = 1

    # Delete user subcollections
    user_path = f"users/{test_user_id}"
    for subcoll in ["connections", "entities", "horoscopes"]:
        count = clear_subcollection(db, user_path, subcoll)
        counts[subcoll] = count

    # Delete memory
    db.collection("memory").document(test_user_id).delete()
    counts["memory"] = 1

    # Delete conversations for this user
    convs = db.collection("conversations").where("user_id", "==", test_user_id).stream()
    conv_count = 0
    for conv in convs:
        conv.reference.delete()
        conv_count += 1
    counts["conversations"] = conv_count

    return counts


def seed_user_profile(db, user_data: dict) -> None:
    """
    Insert user profile into emulator.

    Args:
        db: Firestore client
        user_data: User profile data dict
    """
    user_id = user_data["user_id"]
    db.collection("users").document(user_id).set(user_data)


def seed_memory(db, user_id: str, memory_data: dict) -> None:
    """
    Insert memory collection into emulator.

    Args:
        db: Firestore client
        user_id: User ID
        memory_data: Memory collection data dict
    """
    db.collection("memory").document(user_id).set(memory_data)


def seed_connection(db, user_id: str, connection_data: dict) -> None:
    """
    Insert connection into emulator.

    Args:
        db: Firestore client
        user_id: User ID
        connection_data: Connection data dict
    """
    conn_id = connection_data["connection_id"]
    db.collection("users").document(user_id).collection("connections").document(conn_id).set(connection_data)


def seed_connections(db, user_id: str, connections: list[dict]) -> None:
    """
    Insert multiple connections into emulator.

    Args:
        db: Firestore client
        user_id: User ID
        connections: List of connection data dicts
    """
    for conn in connections:
        seed_connection(db, user_id, conn)


def seed_conversation(db, conversation_data: dict) -> None:
    """
    Insert conversation into emulator.

    Args:
        db: Firestore client
        conversation_data: Conversation data dict
    """
    conv_id = conversation_data["conversation_id"]
    db.collection("conversations").document(conv_id).set(conversation_data)


def seed_horoscope(db, user_id: str, horoscope_data: dict) -> None:
    """
    Insert horoscope into emulator.

    Args:
        db: Firestore client
        user_id: User ID
        horoscope_data: Compressed horoscope data dict
    """
    # Horoscopes are stored in users/{userId}/horoscopes/latest
    # with date-keyed entries inside
    db.collection("users").document(user_id).collection("horoscopes").document("latest").set({
        "user_id": user_id,
        "horoscopes": {
            horoscope_data["date"]: horoscope_data,
        },
        "updated_at": horoscope_data.get("created_at"),
    })


def seed_entity(db, user_id: str, entity_data: dict) -> None:
    """
    Insert entity into emulator.

    Args:
        db: Firestore client
        user_id: User ID
        entity_data: Entity data dict
    """
    # Entities are stored in users/{userId}/entities/all
    entities_ref = db.collection("users").document(user_id).collection("entities").document("all")

    # Get existing or create new
    doc = entities_ref.get()
    if doc.exists:
        existing = doc.to_dict()
        entities = existing.get("entities", [])
        entities.append(entity_data)
        entities_ref.update({"entities": entities, "updated_at": entity_data["updated_at"]})
    else:
        from datetime import datetime, timezone
        entities_ref.set({
            "user_id": user_id,
            "entities": [entity_data],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })


def seed_share_link(db, user_id: str, share_secret: str, share_mode: str = "public") -> None:
    """
    Insert share link into emulator.

    Args:
        db: Firestore client
        user_id: User ID
        share_secret: Share secret token
        share_mode: "public" or "request"
    """
    from datetime import datetime, timezone

    # Share links are stored in share_links collection keyed by secret
    db.collection("share_links").document(share_secret).set({
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # Also update user's share settings
    db.collection("users").document(user_id).update({
        "share_secret": share_secret,
        "share_mode": share_mode,
    })


# ---------------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------------

def get_user_from_emulator(db, user_id: str) -> Optional[dict]:
    """
    Retrieve user from emulator.

    Args:
        db: Firestore client
        user_id: User ID

    Returns:
        User profile dict or None if not found
    """
    doc = db.collection("users").document(user_id).get()
    return doc.to_dict() if doc.exists else None


def get_memory_from_emulator(db, user_id: str) -> Optional[dict]:
    """
    Retrieve memory from emulator.

    Args:
        db: Firestore client
        user_id: User ID

    Returns:
        Memory collection dict or None if not found
    """
    doc = db.collection("memory").document(user_id).get()
    return doc.to_dict() if doc.exists else None


def get_connection_from_emulator(db, user_id: str, connection_id: str) -> Optional[dict]:
    """
    Retrieve connection from emulator.

    Args:
        db: Firestore client
        user_id: User ID
        connection_id: Connection ID

    Returns:
        Connection dict or None if not found
    """
    doc = db.collection("users").document(user_id).collection("connections").document(connection_id).get()
    return doc.to_dict() if doc.exists else None


def get_all_connections_from_emulator(db, user_id: str) -> list[dict]:
    """
    Retrieve all connections for a user.

    Args:
        db: Firestore client
        user_id: User ID

    Returns:
        List of connection dicts
    """
    docs = db.collection("users").document(user_id).collection("connections").stream()
    return [doc.to_dict() for doc in docs]


def get_conversation_from_emulator(db, conversation_id: str) -> Optional[dict]:
    """
    Retrieve conversation from emulator.

    Args:
        db: Firestore client
        conversation_id: Conversation ID

    Returns:
        Conversation dict or None if not found
    """
    doc = db.collection("conversations").document(conversation_id).get()
    return doc.to_dict() if doc.exists else None


def get_entities_from_emulator(db, user_id: str) -> list[dict]:
    """
    Retrieve all entities for a user.

    Args:
        db: Firestore client
        user_id: User ID

    Returns:
        List of entity dicts
    """
    doc = db.collection("users").document(user_id).collection("entities").document("all").get()
    if doc.exists:
        data = doc.to_dict()
        return data.get("entities", [])
    return []


def count_documents(db, collection_path: str) -> int:
    """
    Count documents in a collection.

    Args:
        db: Firestore client
        collection_path: Path to collection

    Returns:
        Number of documents
    """
    docs = db.collection(collection_path).stream()
    return sum(1 for _ in docs)

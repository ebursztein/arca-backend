"""
Connections Module - "Add Me on Arca"

Manages user connections for compatibility features:
- Share links for profile sharing
- Connection CRUD operations
- Privacy modes (public vs request-only)
- Push notifications via Firebase Cloud Messaging

Firestore Collections:
- users/{userId}/connections/{connectionId} - User's connections
- share_links/{share_secret} - Reverse lookup for share URLs
- users/{userId}/connection_requests/{requestId} - Pending requests
"""

import secrets
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from firebase_admin import firestore, messaging

from astro import get_sun_sign, ZodiacSign, compute_birth_chart, NatalChartData
from models import VALID_SUN_SIGNS
from relationships import RelationshipCategory, RelationshipLabel

from compatibility import calculate_synastry_points, calculate_compatibility


# Constants
MAX_NAME_LENGTH = 500


# =============================================================================
# Pydantic Models
# =============================================================================

class StoredVibe(BaseModel):
    """
    A daily vibe stored on a connection (FIFO last 10).

    Similar to Co-Star's relationship updates - shows history of vibes.
    """
    date: str = Field(description="ISO date YYYY-MM-DD")
    vibe: str = Field(max_length=500, description="Vibe text, e.g., 'Great energy today'")
    vibe_score: int = Field(ge=0, le=100, description="0-100 score")
    key_transit: Optional[str] = Field(None, max_length=500, description="Transit that triggered this vibe")


class Connection(BaseModel):
    """
    A connection (person) stored in user's connections subcollection.

    Stored at: users/{userId}/connections/{connectionId}
    """
    connection_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$", description="Unique connection ID")
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH, description="Connection's name")
    birth_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="Birth date YYYY-MM-DD")
    birth_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="Birth time HH:MM")
    birth_lat: Optional[float] = Field(None, ge=-90, le=90)
    birth_lon: Optional[float] = Field(None, ge=-180, le=180)
    birth_timezone: Optional[str] = Field(None, max_length=64, description="IANA timezone")
    relationship_category: RelationshipCategory = Field(
        description="Main category (love/friend/family/coworker/other)"
    )
    relationship_label: RelationshipLabel = Field(
        description="Specific label (crush/partner/best_friend/boss/etc)"
    )
    source_user_id: Optional[str] = Field(
        None,
        max_length=128,
        description="User ID if imported via share link"
    )
    sun_sign: Optional[str] = Field(None, description="Calculated sun sign")
    photo_path: Optional[str] = Field(
        None,
        max_length=500,
        description="Firebase Storage path for connection photo"
    )
    created_at: str = Field(description="ISO timestamp")
    updated_at: str = Field(description="ISO timestamp")

    # Synastry data (cached for daily horoscope)
    synastry_points: Optional[list[dict]] = Field(
        None,
        description="Cached synastry midpoints for daily transit checking"
    )

    # Notes from Ask the Stars conversations
    arca_notes: list[dict] = Field(
        default_factory=list,
        max_length=100,
        description="Notes extracted from conversations: [{date, note, context}]"
    )

    # Daily vibes history (FIFO last 10, like Co-Star updates)
    vibes: list[StoredVibe] = Field(
        default_factory=list,
        max_length=10,
        description="Last 10 daily vibes for this connection"
    )

    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, v: str) -> str:
        """Validate birth date is a valid date and not in the future."""
        try:
            date = datetime.strptime(v, "%Y-%m-%d")
            if date > datetime.now():
                raise ValueError("Birth date cannot be in the future")
            # Also check for reasonable date range (not before 1900)
            if date.year < 1900:
                raise ValueError("Birth date year must be 1900 or later")
        except ValueError as e:
            if "Birth date" in str(e):
                raise
            raise ValueError(f"Invalid date: {v}. Must be valid YYYY-MM-DD format")
        return v

    @field_validator('sun_sign')
    @classmethod
    def validate_sun_sign(cls, v: Optional[str]) -> Optional[str]:
        """Validate sun sign if provided."""
        if v is not None and v.lower() not in VALID_SUN_SIGNS:
            raise ValueError(f"Invalid sun sign: {v}. Must be one of {VALID_SUN_SIGNS}")
        return v.lower() if v else None

    @model_validator(mode='after')
    def validate_lat_lon_together(self):
        """Ensure lat and lon are both set or both None."""
        if (self.birth_lat is None) != (self.birth_lon is None):
            raise ValueError("birth_lat and birth_lon must both be set or both be None")
        return self


class ShareLink(BaseModel):
    """
    Share link reverse lookup.

    Stored at: share_links/{share_secret}
    """
    user_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$", description="Owner's user ID")
    created_at: str = Field(description="ISO timestamp")


class ConnectionRequest(BaseModel):
    """
    Pending connection request (for request-only mode).

    Stored at: users/{userId}/connection_requests/{requestId}
    """
    request_id: str = Field(min_length=1, max_length=64, description="Unique request ID")
    from_user_id: str = Field(min_length=1, max_length=128, description="Requester's user ID")
    from_name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH, description="Requester's name")
    status: Literal["pending", "approved", "rejected"] = Field(default="pending")
    created_at: str = Field(description="ISO timestamp")


# =============================================================================
# Response Models
# =============================================================================

class ShareLinkResponse(BaseModel):
    """Response for get_share_link."""
    share_url: str
    share_mode: Literal["public", "request"]
    qr_code_data: str


class PublicProfileResponse(BaseModel):
    """Response for get_public_profile."""
    profile: dict = Field(description="Public profile data")
    share_mode: Literal["public", "request"]
    can_add: bool
    message: Optional[str] = None


class ImportConnectionResponse(BaseModel):
    """Response for import_connection."""
    success: bool
    connection_id: Optional[str] = None
    connection: Optional[dict] = None
    notification_sent: bool = False
    message: Optional[str] = None


class ConnectionListResponse(BaseModel):
    """Response for list_connections."""
    connections: list[dict]
    total_count: int


# =============================================================================
# Push Notification Functions
# =============================================================================

def send_push_notification(
    db: firestore.Client,
    user_id: str,
    title: str,
    body: str,
    data: Optional[dict] = None
) -> bool:
    """
    Send push notification to a user via Firebase Cloud Messaging.

    Args:
        db: Firestore client
        user_id: Target user's ID
        title: Notification title
        body: Notification body
        data: Optional data payload

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Get user's device token
        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            return False

        user_data = user_doc.to_dict()
        device_token = user_data.get("device_token")

        if not device_token:
            # User hasn't registered for push notifications
            return False

        # Build message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            token=device_token
        )

        # Send
        messaging.send(message)
        return True

    except messaging.UnregisteredError:
        # Token is invalid/expired - clear it
        db.collection("users").document(user_id).update({
            "device_token": firestore.DELETE_FIELD
        })
        return False
    except Exception as e:
        print(f"Push notification failed for {user_id}: {e}")
        return False


def register_device_token(
    db: firestore.Client,
    user_id: str,
    device_token: str
) -> bool:
    """
    Register or update user's device token for push notifications.

    Called by iOS on login/app launch.

    Args:
        db: Firestore client
        user_id: User's ID
        device_token: FCM device token from iOS

    Returns:
        True if registered successfully
    """
    try:
        db.collection("users").document(user_id).update({
            "device_token": device_token,
            "device_token_updated_at": datetime.now().isoformat()
        })
        return True
    except Exception as e:
        print(f"Failed to register device token for {user_id}: {e}")
        return False


# =============================================================================
# Helper Functions
# =============================================================================

def generate_share_secret() -> str:
    """Generate a URL-safe share secret (12 chars)."""
    return secrets.token_urlsafe(9)  # 12 chars


def get_share_url(share_secret: str) -> str:
    """Build the share URL from secret."""
    return f"https://arca-app.com/u/{share_secret}"


# =============================================================================
# Connection Management Functions
# =============================================================================

def get_or_create_share_link(
    db: firestore.Client,
    user_id: str,
    user_profile: dict
) -> ShareLinkResponse:
    """
    Get user's share link, creating one if it doesn't exist.

    Args:
        db: Firestore client
        user_id: User's Firebase ID
        user_profile: User's profile dict

    Returns:
        ShareLinkResponse with URL and mode
    """
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    user_data = user_doc.to_dict() if user_doc.exists else {}

    share_secret = user_data.get("share_secret")
    share_mode = user_data.get("share_mode", "public")

    # Create share secret if doesn't exist
    if not share_secret:
        share_secret = generate_share_secret()
        now = datetime.now().isoformat()

        # Update user with share secret
        user_ref.update({
            "share_secret": share_secret,
            "share_mode": share_mode
        })

        # Create reverse lookup
        db.collection("share_links").document(share_secret).set({
            "user_id": user_id,
            "created_at": now
        })

    share_url = get_share_url(share_secret)

    return ShareLinkResponse(
        share_url=share_url,
        share_mode=share_mode,
        qr_code_data=share_url
    )


def get_public_profile(
    db: firestore.Client,
    share_secret: str
) -> PublicProfileResponse:
    """
    Fetch public profile data from share link.

    Args:
        db: Firestore client
        share_secret: The share secret from URL

    Returns:
        PublicProfileResponse with profile data based on share mode
    """
    # Look up user from share secret
    share_doc = db.collection("share_links").document(share_secret).get()

    if not share_doc.exists:
        raise ValueError("Invalid share link")

    user_id = share_doc.to_dict().get("user_id")
    user_doc = db.collection("users").document(user_id).get()

    if not user_doc.exists:
        raise ValueError("User not found")

    user_data = user_doc.to_dict()
    share_mode = user_data.get("share_mode", "public")

    # Calculate sun sign if not stored
    sun_sign = user_data.get("sun_sign")
    if not sun_sign and user_data.get("birth_date"):
        sun_sign = get_sun_sign(user_data["birth_date"]).value

    if share_mode == "public":
        # Return full birth data
        profile = {
            "name": user_data.get("name"),
            "birth_date": user_data.get("birth_date"),
            "birth_time": user_data.get("birth_time"),
            "birth_lat": user_data.get("birth_lat"),
            "birth_lon": user_data.get("birth_lon"),
            "birth_timezone": user_data.get("birth_timezone"),
            "sun_sign": sun_sign
        }
        return PublicProfileResponse(
            profile=profile,
            share_mode="public",
            can_add=True
        )
    else:
        # Request mode - only return name and sun sign
        profile = {
            "name": user_data.get("name"),
            "sun_sign": sun_sign
        }
        return PublicProfileResponse(
            profile=profile,
            share_mode="request",
            can_add=False,
            message=f"{user_data.get('name')} requires approval to share compatibility data"
        )


def import_connection(
    db: firestore.Client,
    user_id: str,
    share_secret: str,
    relationship_category: str,
    relationship_label: str
) -> ImportConnectionResponse:
    """
    Add a connection from a share link.

    Args:
        db: Firestore client
        user_id: Current user's ID
        share_secret: Share secret from URL
        relationship_category: Main category (love/friend/family/coworker/other)
        relationship_label: Specific label (crush/partner/best_friend/boss/etc)

    Returns:
        ImportConnectionResponse with connection data
    """
    # Look up source user
    share_doc = db.collection("share_links").document(share_secret).get()

    if not share_doc.exists:
        raise ValueError("Invalid share link")

    source_user_id = share_doc.to_dict().get("user_id")

    # Can't add yourself
    if source_user_id == user_id:
        raise ValueError("Cannot add yourself as a connection")

    # Check for duplicate connection
    existing_connections = db.collection("users").document(user_id).collection(
        "connections"
    ).where("source_user_id", "==", source_user_id).limit(1).get()

    if len(list(existing_connections)) > 0:
        raise ValueError("You've already added this person as a connection")

    source_user_doc = db.collection("users").document(source_user_id).get()

    if not source_user_doc.exists:
        raise ValueError("User not found")

    source_data = source_user_doc.to_dict()
    share_mode = source_data.get("share_mode", "public")

    # Get current user's name for notifications
    current_user_doc = db.collection("users").document(user_id).get()
    current_user_name = current_user_doc.to_dict().get("name", "Someone") if current_user_doc.exists else "Someone"

    now = datetime.now().isoformat()

    if share_mode == "request":
        # Create connection request instead of direct add
        request_id = secrets.token_urlsafe(16)

        request = ConnectionRequest(
            request_id=request_id,
            from_user_id=user_id,
            from_name=current_user_name,
            status="pending",
            created_at=now
        )

        db.collection("users").document(source_user_id).collection(
            "connection_requests"
        ).document(request_id).set(request.model_dump())

        # Send push notification
        notification_sent = send_push_notification(
            db=db,
            user_id=source_user_id,
            title="Connection Request",
            body=f"{current_user_name} wants to connect with you",
            data={"type": "connection_request", "request_id": request_id}
        )

        return ImportConnectionResponse(
            success=True,
            message=f"Request sent to {source_data.get('name')}. They'll need to approve before you can see compatibility.",
            notification_sent=notification_sent
        )

    # Public mode - create connection directly
    connection_id = secrets.token_urlsafe(16)

    # Calculate sun sign
    sun_sign = None
    if source_data.get("birth_date"):
        sun_sign = get_sun_sign(source_data["birth_date"]).value

    # Convert string params to enums
    cat_enum = RelationshipCategory(relationship_category)
    label_enum = RelationshipLabel(relationship_label)

    connection = Connection(
        connection_id=connection_id,
        name=source_data.get("name", "Unknown"),
        birth_date=source_data.get("birth_date", ""),
        birth_time=source_data.get("birth_time"),
        birth_lat=source_data.get("birth_lat"),
        birth_lon=source_data.get("birth_lon"),
        birth_timezone=source_data.get("birth_timezone"),
        relationship_category=cat_enum,
        relationship_label=label_enum,
        source_user_id=source_user_id,
        sun_sign=sun_sign,
        created_at=now,
        updated_at=now
    )

    # Save to user's connections
    db.collection("users").document(user_id).collection(
        "connections"
    ).document(connection_id).set(connection.model_dump())

    # Calculate and cache synastry points (async in background)
    current_user_data = current_user_doc.to_dict() if current_user_doc.exists else {}
    if current_user_data.get("birth_date") and connection.birth_date:
        calculate_and_cache_synastry(
            db=db,
            user_id=user_id,
            connection_id=connection_id,
            user_birth_date=current_user_data.get("birth_date"),
            user_birth_time=current_user_data.get("birth_time"),
            user_birth_lat=current_user_data.get("birth_lat"),
            user_birth_lon=current_user_data.get("birth_lon"),
            user_birth_timezone=current_user_data.get("birth_timezone"),
            conn_birth_date=connection.birth_date,
            conn_birth_time=connection.birth_time,
            conn_birth_lat=connection.birth_lat,
            conn_birth_lon=connection.birth_lon,
            conn_birth_timezone=connection.birth_timezone
        )

    # Send push notification to source user
    notification_sent = send_push_notification(
        db=db,
        user_id=source_user_id,
        title=f"{current_user_name} added you!",
        body="Add them back to see compatibility",
        data={"type": "connection_added", "from_user_id": user_id}
    )

    return ImportConnectionResponse(
        success=True,
        connection_id=connection_id,
        connection={
            "name": connection.name,
            "sun_sign": connection.sun_sign
        },
        notification_sent=notification_sent
    )


def create_connection(
    db: firestore.Client,
    user_id: str,
    name: str,
    birth_date: str,
    relationship_category: str,
    relationship_label: str,
    birth_time: Optional[str] = None,
    birth_lat: Optional[float] = None,
    birth_lon: Optional[float] = None,
    birth_timezone: Optional[str] = None,
    photo_path: Optional[str] = None
) -> Connection:
    """
    Manually create a connection (not via share link).

    Args:
        db: Firestore client
        user_id: User's ID
        name: Connection's name
        birth_date: Birth date YYYY-MM-DD
        relationship_category: Main category (love/friend/family/coworker/other)
        relationship_label: Specific label (crush/partner/best_friend/boss/etc)
        birth_time: Optional birth time
        birth_lat: Optional latitude
        birth_lon: Optional longitude
        birth_timezone: Optional timezone
        photo_path: Optional Firebase Storage path for photo

    Returns:
        Created Connection
    """
    connection_id = secrets.token_urlsafe(16)
    now = datetime.now().isoformat()

    # Calculate sun sign
    sun_sign = None
    if birth_date:
        sun_sign = get_sun_sign(birth_date).value

    # Convert string params to enums
    cat_enum = RelationshipCategory(relationship_category)
    label_enum = RelationshipLabel(relationship_label)

    connection = Connection(
        connection_id=connection_id,
        name=name,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_lat=birth_lat,
        birth_lon=birth_lon,
        birth_timezone=birth_timezone,
        relationship_category=cat_enum,
        relationship_label=label_enum,
        source_user_id=None,
        sun_sign=sun_sign,
        photo_path=photo_path,
        created_at=now,
        updated_at=now
    )

    db.collection("users").document(user_id).collection(
        "connections"
    ).document(connection_id).set(connection.model_dump())

    # Calculate and cache synastry points
    user_doc = db.collection("users").document(user_id).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        if user_data.get("birth_date") and birth_date:
            calculate_and_cache_synastry(
                db=db,
                user_id=user_id,
                connection_id=connection_id,
                user_birth_date=user_data.get("birth_date"),
                user_birth_time=user_data.get("birth_time"),
                user_birth_lat=user_data.get("birth_lat"),
                user_birth_lon=user_data.get("birth_lon"),
                user_birth_timezone=user_data.get("birth_timezone"),
                conn_birth_date=birth_date,
                conn_birth_time=birth_time,
                conn_birth_lat=birth_lat,
                conn_birth_lon=birth_lon,
                conn_birth_timezone=birth_timezone
            )

    return connection


def update_connection(
    db: firestore.Client,
    user_id: str,
    connection_id: str,
    updates: dict
) -> Connection:
    """
    Update a connection's details.

    Args:
        db: Firestore client
        user_id: User's ID
        connection_id: Connection to update
        updates: Fields to update

    Returns:
        Updated Connection
    """
    conn_ref = db.collection("users").document(user_id).collection(
        "connections"
    ).document(connection_id)

    conn_doc = conn_ref.get()
    if not conn_doc.exists:
        raise ValueError("Connection not found")

    # Filter allowed fields
    allowed_fields = {
        "name", "birth_date", "birth_time", "birth_lat",
        "birth_lon", "birth_timezone", "relationship_category", "relationship_label", "photo_path"
    }
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    # Recalculate sun sign if birth_date changed
    if "birth_date" in filtered_updates:
        filtered_updates["sun_sign"] = get_sun_sign(filtered_updates["birth_date"]).value

    filtered_updates["updated_at"] = datetime.now().isoformat()

    conn_ref.update(filtered_updates)

    # Return updated connection
    updated_doc = conn_ref.get()
    return Connection(**updated_doc.to_dict())


def delete_connection(
    db: firestore.Client,
    user_id: str,
    connection_id: str
) -> bool:
    """
    Delete a connection.

    Args:
        db: Firestore client
        user_id: User's ID
        connection_id: Connection to delete

    Returns:
        True if deleted
    """
    conn_ref = db.collection("users").document(user_id).collection(
        "connections"
    ).document(connection_id)

    conn_doc = conn_ref.get()
    if not conn_doc.exists:
        raise ValueError("Connection not found")

    conn_ref.delete()
    return True


def list_connections(
    db: firestore.Client,
    user_id: str,
    limit: int = 50
) -> ConnectionListResponse:
    """
    List all user's connections.

    Args:
        db: Firestore client
        user_id: User's ID
        limit: Max connections to return

    Returns:
        ConnectionListResponse with connections list
    """
    connections_ref = db.collection("users").document(user_id).collection("connections")
    docs = connections_ref.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).get()

    connections = [doc.to_dict() for doc in docs]

    return ConnectionListResponse(
        connections=connections,
        total_count=len(connections)
    )


def list_connection_requests(
    db: firestore.Client,
    user_id: str
) -> list[dict]:
    """
    List pending connection requests for a user.

    Args:
        db: Firestore client
        user_id: User's ID

    Returns:
        List of pending request dicts
    """
    requests_ref = db.collection("users").document(user_id).collection("connection_requests")
    docs = requests_ref.where("status", "==", "pending").order_by(
        "created_at", direction=firestore.Query.DESCENDING
    ).get()

    return [doc.to_dict() for doc in docs]


def update_share_mode(
    db: firestore.Client,
    user_id: str,
    share_mode: Literal["public", "request"]
) -> dict:
    """
    Toggle between public and request-only share modes.

    Args:
        db: Firestore client
        user_id: User's ID
        share_mode: New share mode

    Returns:
        Updated settings
    """
    user_ref = db.collection("users").document(user_id)
    user_ref.update({"share_mode": share_mode})

    return {"share_mode": share_mode}


def respond_to_request(
    db: firestore.Client,
    user_id: str,
    request_id: str,
    action: Literal["approve", "reject"]
) -> dict:
    """
    Approve or reject a connection request.

    Args:
        db: Firestore client
        user_id: User receiving the request
        request_id: Request to respond to
        action: approve or reject

    Returns:
        Result of the action
    """
    request_ref = db.collection("users").document(user_id).collection(
        "connection_requests"
    ).document(request_id)

    request_doc = request_ref.get()
    if not request_doc.exists:
        raise ValueError("Request not found")

    request_data = request_doc.to_dict()

    if request_data.get("status") != "pending":
        raise ValueError("Request already processed")

    now = datetime.now().isoformat()
    from_user_id = request_data.get("from_user_id")

    if action == "reject":
        request_ref.update({
            "status": "rejected",
            "updated_at": now
        })

        # Notify requester
        send_push_notification(
            db=db,
            user_id=from_user_id,
            title="Connection Request",
            body="Your connection request was declined",
            data={"type": "connection_rejected", "request_id": request_id}
        )

        return {"success": True, "action": "rejected"}

    # Approve - create connection for the requester
    # Get current user's data to create connection
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict()

    connection_id = secrets.token_urlsafe(16)

    sun_sign = None
    if user_data.get("birth_date"):
        sun_sign = get_sun_sign(user_data["birth_date"]).value

    connection = Connection(
        connection_id=connection_id,
        name=user_data.get("name", "Unknown"),
        birth_date=user_data.get("birth_date", ""),
        birth_time=user_data.get("birth_time"),
        birth_lat=user_data.get("birth_lat"),
        birth_lon=user_data.get("birth_lon"),
        birth_timezone=user_data.get("birth_timezone"),
        relationship_category=RelationshipCategory.FRIEND,  # Default, they can change later
        relationship_label=RelationshipLabel.FRIEND,
        source_user_id=user_id,
        sun_sign=sun_sign,
        created_at=now,
        updated_at=now
    )

    # Add to requester's connections
    db.collection("users").document(from_user_id).collection(
        "connections"
    ).document(connection_id).set(connection.model_dump())

    # Update request status
    request_ref.update({
        "status": "approved",
        "updated_at": now
    })

    # Notify requester
    send_push_notification(
        db=db,
        user_id=from_user_id,
        title=f"{user_data.get('name')} accepted!",
        body="You can now see your compatibility",
        data={"type": "connection_approved", "connection_id": connection_id}
    )

    return {
        "success": True,
        "action": "approved",
        "connection_id": connection_id
    }


def get_connections_for_horoscope(
    db: firestore.Client,
    user_id: str,
    limit: int = 10
) -> list[dict]:
    """
    Get top connections for daily horoscope relationship weather.

    Returns most recent connections by created_at.

    Args:
        db: Firestore client
        user_id: User's ID
        limit: Max connections (default 10)

    Returns:
        List of connection dicts with birth data
    """
    connections_ref = db.collection("users").document(user_id).collection("connections")
    docs = connections_ref.order_by(
        "created_at",
        direction=firestore.Query.DESCENDING
    ).limit(limit).get()

    return [doc.to_dict() for doc in docs]


def calculate_and_cache_synastry(
    db: firestore.Client,
    user_id: str,
    connection_id: str,
    user_birth_date: str,
    user_birth_time: Optional[str],
    user_birth_lat: Optional[float],
    user_birth_lon: Optional[float],
    user_birth_timezone: Optional[str],
    conn_birth_date: str,
    conn_birth_time: Optional[str],
    conn_birth_lat: Optional[float],
    conn_birth_lon: Optional[float],
    conn_birth_timezone: Optional[str]
) -> Optional[dict]:
    """
    Calculate synastry points AND aspects between user and connection, cache on connection.

    Args:
        db: Firestore client
        user_id: User's ID
        connection_id: Connection ID to update
        user_birth_*: User's birth data
        conn_birth_*: Connection's birth data

    Returns:
        Dict with synastry_points and synastry_aspects, or None if calculation fails
    """
    try:
        # Build user chart
        user_chart_dict, _ = compute_birth_chart(
            birth_date=user_birth_date,
            birth_time=user_birth_time,
            birth_timezone=user_birth_timezone,
            birth_lat=user_birth_lat,
            birth_lon=user_birth_lon
        )
        user_chart = NatalChartData(**user_chart_dict)

        # Build connection chart
        conn_chart_dict, _ = compute_birth_chart(
            birth_date=conn_birth_date,
            birth_time=conn_birth_time,
            birth_timezone=conn_birth_timezone,
            birth_lat=conn_birth_lat,
            birth_lon=conn_birth_lon
        )
        conn_chart = NatalChartData(**conn_chart_dict)

        # Calculate synastry points (midpoints for transit tracking)
        synastry_points = calculate_synastry_points(user_chart, conn_chart)

        # Calculate full compatibility to get aspects
        compatibility = calculate_compatibility(user_chart, conn_chart)

        # Get top 6 tightest aspects for display
        sorted_aspects = sorted(compatibility.aspects, key=lambda a: a.orb)[:6]
        synastry_aspects = [
            {
                "user_planet": asp.user_planet,
                "their_planet": asp.their_planet,
                "aspect_type": asp.aspect_type,
                "is_harmonious": asp.is_harmonious,
                "orb": round(asp.orb, 1)
            }
            for asp in sorted_aspects
        ]

        # Cache on connection record
        conn_ref = db.collection("users").document(user_id).collection(
            "connections"
        ).document(connection_id)
        conn_ref.update({
            "synastry_points": synastry_points,
            "synastry_aspects": synastry_aspects
        })

        return {
            "synastry_points": synastry_points,
            "synastry_aspects": synastry_aspects
        }

    except Exception as e:
        print(f"Failed to calculate synastry for connection {connection_id}: {e}")
        return None

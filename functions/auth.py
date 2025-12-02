"""
Authentication helpers for Firebase callable functions.
"""

from firebase_functions import https_fn

# =============================================================================
# Dev Accounts - Bypass authentication for testing
# =============================================================================
# These user IDs can be passed directly in request data to bypass Firebase Auth.
# Used for testing in Xcode Canvas/previews where Firebase Auth is unavailable.
DEV_ACCOUNT_UIDS = {
    "test_user_a",
    "test_user_b",
    "test_user_c",
    "test_user_d",
    "test_user_e",
    # Additional accounts for isolated test scenarios
    "test_crud_user",
    "test_sharing_source",
    "test_sharing_importer",
}


def get_authenticated_user_id(req: https_fn.CallableRequest, allow_override: bool = True) -> str:
    """
    Get user ID from request, allowing test accounts to bypass authentication.

    Test accounts listed in DEV_ACCOUNT_UIDS can pass user_id in request data
    to bypass Firebase Auth entirely. This enables testing in environments
    where Firebase Auth is unavailable (e.g., Xcode Canvas/previews).

    Args:
        req: The callable request object
        allow_override: If True, allow test account bypass

    Returns:
        The user ID (from auth token or test account override)

    Raises:
        HttpsError: If not authenticated and not a valid test account
    """
    # Check for test account bypass first
    if allow_override and req.data:
        user_id_param = req.data.get("user_id")
        if user_id_param and user_id_param in DEV_ACCOUNT_UIDS:
            return user_id_param

    # Otherwise require Firebase Auth
    if not req.auth:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="Authentication required"
        )

    if not req.auth.uid:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="Invalid authentication token: missing uid"
        )

    return req.auth.uid

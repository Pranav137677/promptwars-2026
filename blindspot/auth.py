"""Firebase Authentication integration with optional grace fallback.

When FIREBASE_ENABLED is False, authentication is bypassed cleanly.
When True, requests bearing an Authorization Bearer header are verified using firebase-admin.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any

from flask import g, jsonify, request

from blindspot.config import config

logger = logging.getLogger(__name__)

_firebase_app_initialized = False


def init_firebase_admin() -> None:
    """Initialize firebase-admin app once if FIREBASE_ENABLED is True."""
    global _firebase_app_initialized
    if not config.firebase_enabled:
        return

    if not _firebase_app_initialized:
        try:
            import firebase_admin
            from firebase_admin import credentials

            # Default credentials pick up GOOGLE_APPLICATION_CREDENTIALS or Cloud Run metadata
            try:
                firebase_admin.get_app()
                _firebase_app_initialized = True
            except ValueError:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(
                    cred, {"projectId": config.firebase_project_id}
                )
                _firebase_app_initialized = True
                logger.info(
                    "Firebase Admin successfully initialized for project: %s",
                    config.firebase_project_id,
                )
        except Exception as e:
            logger.warning(
                "Could not initialize Firebase Admin SDK (%s). Running in unauthenticated mode.",
                e,
            )


def verify_firebase_token(token: str) -> dict[str, Any] | None:
    """Verify Firebase ID token using firebase_admin.auth.

    Args:
        token: Raw JWT ID token string.

    Returns:
        Decoded token payload dict if valid, None otherwise.
    """
    if not config.firebase_enabled:
        return None
    try:
        from firebase_admin import auth

        decoded = auth.verify_id_token(token)
        return decoded
    except Exception as e:
        logger.warning("Token verification failed: %s", e)
        return None


def optional_auth(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to identify user if token is present, but allow anonymous access."""

    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        g.user_id = None
        g.user_email = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ", 1)[1].strip()
            if config.firebase_enabled:
                decoded = verify_firebase_token(token)
                if decoded:
                    g.user_id = decoded.get("uid")
                    g.user_email = decoded.get("email")
                else:
                    return (
                        jsonify(
                            {
                                "error": "Invalid or expired authentication token. Please sign in again."
                            }
                        ),
                        401,
                    )
        return f(*args, **kwargs)

    return decorated_function


def require_auth(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator requiring a valid Firebase authenticated user.

    If FIREBASE_ENABLED is False, returns 403 Feature Disabled.
    """

    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not config.firebase_enabled:
            return (
                jsonify(
                    {
                        "error": "Firebase feature is disabled on this server. Enable FIREBASE_ENABLED=true."
                    }
                ),
                403,
            )

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return (
                jsonify(
                    {"error": "Authentication required. Missing Bearer token in Authorization header."}
                ),
                401,
            )

        token = auth_header.split("Bearer ", 1)[1].strip()
        decoded = verify_firebase_token(token)
        if not decoded or "uid" not in decoded:
            return (
                jsonify(
                    {"error": "Invalid or expired authentication token."}
                ),
                401,
            )

        g.user_id = decoded["uid"]
        g.user_email = decoded.get("email")
        return f(*args, **kwargs)

    return decorated_function

"""Firestore storage repository for user reflections history."""

import datetime
import logging
import uuid
from typing import Any

from blindspot.config import config

logger = logging.getLogger(__name__)

_firestore_client = None


def get_firestore_client() -> Any:
    """Lazily obtain firestore client if enabled."""
    global _firestore_client
    if not config.firebase_enabled:
        return None
    if _firestore_client is None:
        try:
            from firebase_admin import firestore

            _firestore_client = firestore.client()
        except Exception as e:
            logger.warning("Could not initialize Firestore client: %s", e)
            return None
    return _firestore_client


def save_reflection(user_id: str, data: dict[str, Any]) -> str | None:
    """Save user reflection to Firestore under users/{userId}/reflections/{reflectionId}.

    Args:
        user_id: Authenticated Firebase user UID.
        data: Reflection data payload.

    Returns:
        Reflection ID if saved successfully, None otherwise.
    """
    if not config.firebase_enabled or not user_id:
        return None

    db = get_firestore_client()
    if db is None:
        return None

    try:
        reflection_id = str(uuid.uuid4())
        doc_data = {
            "id": reflection_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "decision": data.get("decision", ""),
            "summary": data.get("summary", ""),
            "round1": data.get("round1"),
            "round2": data.get("round2"),
        }
        db.collection("users").document(user_id).collection("reflections").document(
            reflection_id
        ).set(doc_data)
        logger.info(
            "Saved reflection %s for user %s", reflection_id, user_id
        )
        return reflection_id
    except Exception as e:
        logger.error("Failed to save reflection to Firestore: %s", e)
        return None


def list_reflections(user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """List recent reflections for the authenticated user.

    Args:
        user_id: Authenticated Firebase user UID.
        limit: Max number of reflections to retrieve.

    Returns:
        List of reflection summary dictionaries.
    """
    if not config.firebase_enabled or not user_id:
        return []

    db = get_firestore_client()
    if db is None:
        return []

    try:
        docs = (
            db.collection("users")
            .document(user_id)
            .collection("reflections")
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        reflections = []
        for doc in docs:
            item = doc.to_dict()
            reflections.append(item)
        return reflections
    except Exception as e:
        logger.error("Failed to list reflections from Firestore: %s", e)
        return []


def delete_reflection(user_id: str, reflection_id: str) -> bool:
    """Delete a reflection belonging to the authenticated user.

    Args:
        user_id: Authenticated Firebase user UID.
        reflection_id: ID of reflection to delete.

    Returns:
        True if deleted, False otherwise.
    """
    if not config.firebase_enabled or not user_id:
        return False

    db = get_firestore_client()
    if db is None:
        return False

    try:
        doc_ref = (
            db.collection("users")
            .document(user_id)
            .collection("reflections")
            .document(reflection_id)
        )
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return False
        doc_ref.delete()
        logger.info(
            "Deleted reflection %s for user %s", reflection_id, user_id
        )
        return True
    except Exception as e:
        logger.error("Failed to delete reflection from Firestore: %s", e)
        return False

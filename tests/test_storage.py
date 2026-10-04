"""Tests for blindspot.storage verifying Firestore operations and fallback behaviors."""

from unittest.mock import MagicMock, patch

from blindspot.config import config
from blindspot.storage import (
    delete_reflection,
    list_reflections,
    save_reflection,
)


def test_storage_when_firebase_disabled():
    """Verify storage functions fail safely when FIREBASE_ENABLED is False."""
    with patch.object(config, "firebase_enabled", False):
        assert save_reflection("user-1", {"decision": "test"}) is None
        assert list_reflections("user-1") == []
        assert delete_reflection("user-1", "doc-1") is False


def test_save_reflection_success():
    """Verify reflection document is constructed and saved with Firestore client."""
    mock_db = MagicMock()
    mock_user_doc = MagicMock()
    mock_reflections_col = MagicMock()
    mock_doc = MagicMock()

    mock_db.collection.return_value.document.return_value = mock_user_doc
    mock_user_doc.collection.return_value = mock_reflections_col
    mock_reflections_col.document.return_value = mock_doc

    with patch.object(config, "firebase_enabled", True):
        with patch("blindspot.storage.get_firestore_client", return_value=mock_db):
            doc_id = save_reflection("user-123", {
                "decision": "Test Decision",
                "summary": "Test Summary",
                "round1": {"summary": "Round 1"}
            })

            assert doc_id is not None
            assert mock_doc.set.called


def test_list_reflections_success():
    """Verify listing reflections parses documents properly."""
    mock_db = MagicMock()
    mock_query = MagicMock()

    mock_doc1 = MagicMock()
    mock_doc1.to_dict.return_value = {"id": "1", "decision": "Decision 1"}
    mock_doc2 = MagicMock()
    mock_doc2.to_dict.return_value = {"id": "2", "decision": "Decision 2"}

    mock_query.stream.return_value = [mock_doc1, mock_doc2]
    mock_db.collection.return_value.document.return_value.collection.return_value.order_by.return_value.limit.return_value = mock_query

    with patch.object(config, "firebase_enabled", True):
        with patch("blindspot.storage.get_firestore_client", return_value=mock_db):
            results = list_reflections("user-123", limit=10)
            assert len(results) == 2
            assert results[0]["id"] == "1"


def test_delete_reflection_flow():
    """Verify deleting existing vs non-existent reflection."""
    mock_db = MagicMock()
    mock_doc_ref = MagicMock()
    mock_snapshot = MagicMock()

    # Case 1: Exists
    mock_snapshot.exists = True
    mock_doc_ref.get.return_value = mock_snapshot
    mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_doc_ref

    with patch.object(config, "firebase_enabled", True):
        with patch("blindspot.storage.get_firestore_client", return_value=mock_db):
            assert delete_reflection("user-123", "doc-abc") is True
            assert mock_doc_ref.delete.called

    # Case 2: Does not exist
    mock_snapshot.exists = False
    with patch.object(config, "firebase_enabled", True):
        with patch("blindspot.storage.get_firestore_client", return_value=mock_db):
            assert delete_reflection("user-123", "doc-xyz") is False

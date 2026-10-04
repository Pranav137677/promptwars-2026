"""Additional tests boosting code coverage across storage, auth, and config modules."""

from unittest.mock import MagicMock, patch

from blindspot.auth import (
    init_firebase_admin,
    verify_firebase_token,
)
from blindspot.config import _str_to_bool, config
from blindspot.storage import (
    delete_reflection,
    get_firestore_client,
    list_reflections,
    save_reflection,
)


def test_str_to_bool_variations():
    """Verify _str_to_bool parses all standard truthy and falsy strings."""
    assert _str_to_bool(None, default=True) is True
    assert _str_to_bool(None, default=False) is False
    assert _str_to_bool("true") is True
    assert _str_to_bool("1") is True
    assert _str_to_bool("yes") is True
    assert _str_to_bool("on") is True
    assert _str_to_bool("false") is False
    assert _str_to_bool("0") is False
    assert _str_to_bool("no") is False
    assert _str_to_bool("random") is False


def test_init_firebase_admin_flow():
    """Verify init_firebase_admin initializes the app when enabled."""
    with patch.object(config, "firebase_enabled", True):
        with patch("firebase_admin.get_app", side_effect=ValueError("No app")):
            with patch("firebase_admin.initialize_app") as mock_init:
                init_firebase_admin()
                assert mock_init.called


def test_verify_firebase_token_live_branch():
    """Verify verify_firebase_token interacts with firebase_admin.auth."""
    with patch.object(config, "firebase_enabled", True):
        with patch("firebase_admin.auth.verify_id_token", return_value={"uid": "u123"}):
            decoded = verify_firebase_token("valid-jwt-token")
            assert decoded == {"uid": "u123"}

        with patch("firebase_admin.auth.verify_id_token", side_effect=Exception("Expired")):
            assert verify_firebase_token("expired-jwt") is None


def test_get_firestore_client_live_branch():
    """Verify get_firestore_client initializes client when enabled."""
    import blindspot.storage as storage_mod
    storage_mod._firestore_client = None

    with patch.object(config, "firebase_enabled", True):
        with patch("firebase_admin.firestore.client", return_value=MagicMock()) as mock_client:
            client = get_firestore_client()
            assert client is not None
            assert mock_client.called

    storage_mod._firestore_client = None


def test_storage_exceptions_handled_gracefully():
    """Verify Firestore exceptions return fallback values without crashing."""
    mock_db = MagicMock()
    mock_db.collection.side_effect = Exception("Firestore connection timeout")

    with patch.object(config, "firebase_enabled", True):
        with patch("blindspot.storage.get_firestore_client", return_value=mock_db):
            assert save_reflection("u1", {"decision": "test"}) is None
            assert list_reflections("u1") == []
            assert delete_reflection("u1", "doc1") is False

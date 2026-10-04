"""Tests for blindspot.auth covering optional and required auth decorators and verification."""

from unittest.mock import patch

import pytest
from flask import Flask, g, jsonify

from blindspot.auth import optional_auth, require_auth
from blindspot.config import config


@pytest.fixture
def auth_test_app():
    """Flask test app for auth decorator inspection."""
    test_app = Flask(__name__)

    @test_app.route("/open")
    @optional_auth
    def open_route():
        return jsonify({"user_id": g.user_id, "user_email": g.user_email}), 200

    @test_app.route("/protected")
    @require_auth
    def protected_route():
        return jsonify({"user_id": g.user_id, "user_email": g.user_email}), 200

    return test_app


def test_optional_auth_when_firebase_disabled(auth_test_app):
    """When FIREBASE_ENABLED is False, optional_auth sets user_id=None and succeeds."""
    client = auth_test_app.test_client()
    with patch.object(config, "firebase_enabled", False):
        res = client.get("/open")
        assert res.status_code == 200
        assert res.get_json() == {"user_id": None, "user_email": None}


def test_optional_auth_with_valid_token(auth_test_app):
    """When FIREBASE_ENABLED is True and valid token is passed, user context is populated."""
    client = auth_test_app.test_client()
    mock_decoded = {"uid": "user-12345", "email": "student@example.com"}

    with patch.object(config, "firebase_enabled", True):
        with patch("blindspot.auth.verify_firebase_token", return_value=mock_decoded):
            res = client.get(
                "/open",
                headers={"Authorization": "Bearer valid-firebase-token"}
            )
            assert res.status_code == 200
            data = res.get_json()
            assert data["user_id"] == "user-12345"
            assert data["user_email"] == "student@example.com"


def test_optional_auth_with_invalid_token(auth_test_app):
    """When FIREBASE_ENABLED is True and token is invalid, returns 401."""
    client = auth_test_app.test_client()
    with patch.object(config, "firebase_enabled", True):
        with patch("blindspot.auth.verify_firebase_token", return_value=None):
            res = client.get(
                "/open",
                headers={"Authorization": "Bearer invalid-token"}
            )
            assert res.status_code == 401
            assert "Invalid or expired" in res.get_json()["error"]


def test_require_auth_disabled(auth_test_app):
    """When FIREBASE_ENABLED is False, protected routes return 403."""
    client = auth_test_app.test_client()
    with patch.object(config, "firebase_enabled", False):
        res = client.get("/protected")
        assert res.status_code == 403
        assert "disabled" in res.get_json()["error"]


def test_require_auth_missing_header(auth_test_app):
    """When FIREBASE_ENABLED is True but header is absent, returns 401."""
    client = auth_test_app.test_client()
    with patch.object(config, "firebase_enabled", True):
        res = client.get("/protected")
        assert res.status_code == 401
        assert "Missing Bearer token" in res.get_json()["error"]


def test_require_auth_valid(auth_test_app):
    """When valid token is passed to protected route, it succeeds."""
    client = auth_test_app.test_client()
    mock_decoded = {"uid": "user-999", "email": "tester@example.com"}
    with patch.object(config, "firebase_enabled", True):
        with patch("blindspot.auth.verify_firebase_token", return_value=mock_decoded):
            res = client.get(
                "/protected",
                headers={"Authorization": "Bearer good-token"}
            )
            assert res.status_code == 200
            assert res.get_json()["user_id"] == "user-999"

"""Flask application factory and API routing for Blind Spot."""

import logging
import sys
from typing import Any

from flask import Flask, g, jsonify, render_template, request
from flask_compress import Compress
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from blindspot.auth import init_firebase_admin, optional_auth, require_auth
from blindspot.config import AppConfig
from blindspot.config import config as default_config
from blindspot.gemini_client import GeminiServiceError, gemini_client
from blindspot.storage import (
    delete_reflection,
    list_reflections,
    save_reflection,
)
from blindspot.validators import (
    ValidationError,
    validate_round1_input,
    validate_round2_input,
)

logger = logging.getLogger("blindspot")


def setup_logging(cfg: AppConfig) -> None:
    """Configure structured Cloud Logging on GCP or standard logging locally."""
    if cfg.is_cloud_run:
        try:
            import google.cloud.logging

            client = google.cloud.logging.Client(project=cfg.gcp_project)
            client.setup_logging()
            logger.info("Google Cloud Logging successfully attached.")
            return
        except Exception as e:
            logger.warning("Could not attach Google Cloud Logging: %s", e)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure an instance of the Blind Spot Flask application."""
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # Load configuration
    cfg = default_config
    if test_config:
        app.config.update(test_config)

    app.config["MAX_CONTENT_LENGTH"] = cfg.max_content_length
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600

    setup_logging(cfg)
    init_firebase_admin()

    # Enable HTTP compression
    Compress(app)

    # Rate limiting on IP address
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day"],
        storage_uri="memory://",
    )

    # ---------------------------------------------------------
    # Security Headers and Cache Control
    # ---------------------------------------------------------
    @app.after_request
    def set_security_headers(response):
        # Strict Content-Security-Policy supporting Firebase Auth CDN and Google Fonts
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://www.gstatic.com https://apis.google.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://*.firebaseio.com; "
            "frame-src 'self' https://*.firebaseapp.com; "
            "img-src 'self' data: https:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response

    # ---------------------------------------------------------
    # Error Handlers
    # ---------------------------------------------------------
    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(GeminiServiceError)
    def handle_gemini_error(err: GeminiServiceError):
        logger.error("Gemini Service Error: %s", err.message)
        return (
            jsonify(
                {
                    "error": "The reasoning mirror encountered an issue analyzing your input. Please try again."
                }
            ),
            err.status_code,
        )

    @app.errorhandler(413)
    def handle_payload_too_large(_):
        return (
            jsonify(
                {
                    "error": "Request payload exceeds maximum allowed size limit of 16 KB."
                }
            ),
            413,
        )

    @app.errorhandler(429)
    def handle_ratelimit(_):
        return (
            jsonify(
                {
                    "error": "Too many requests. Please wait a minute before submitting further analysis."
                }
            ),
            429,
        )

    @app.errorhandler(404)
    def handle_not_found(_):
        return jsonify({"error": "Requested resource was not found."}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(err: Exception):
        logger.exception("Unhandled server exception: %s", err)
        return (
            jsonify(
                {
                    "error": "An unexpected server error occurred. Please try again later."
                }
            ),
            500,
        )

    # ---------------------------------------------------------
    # UI and Health Routes
    # ---------------------------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/health")
    def health_check():
        return jsonify(
            {
                "status": "healthy",
                "service": "blindspot",
                "model": cfg.gemini_model,
                "firebase_enabled": cfg.firebase_enabled,
            }
        )

    @app.route("/config")
    def client_config():
        """Safe public configuration endpoint for client Firebase SDK initialization."""
        return jsonify(cfg.client_firebase_config())

    # ---------------------------------------------------------
    # API Routes
    # ---------------------------------------------------------
    @app.route("/api/analyze", methods=["POST"])
    @limiter.limit(cfg.ratelimit_default)
    @optional_auth
    def api_analyze():
        """Round 1: Uncover unstated assumptions, overlooked factors, and probing questions."""
        payload = request.get_json(silent=True)
        validated = validate_round1_input(payload)

        result = gemini_client.analyze_round1(
            decision=validated["decision"],
            details=validated["details"],
            reasons=validated["reasons"],
            unsure=validated["unsure"],
        )

        reflection_id = None
        if g.user_id:
            reflection_id = save_reflection(
                g.user_id,
                {
                    "decision": validated["decision"],
                    "summary": result.get("summary", ""),
                    "round1": result,
                },
            )

        return (
            jsonify(
                {
                    "analysis": result,
                    "reflection_id": reflection_id,
                }
            ),
            200,
        )

    @app.route("/api/reflect", methods=["POST"])
    @limiter.limit(cfg.ratelimit_default)
    @optional_auth
    def api_reflect():
        """Round 2: Reflect on user's answers to probing questions without rendering a verdict."""
        payload = request.get_json(silent=True)
        validated = validate_round2_input(payload)

        result = gemini_client.reflect_round2(
            decision=validated["decision"],
            summary=validated["summary"],
            answers=validated["answers"],
        )

        return (
            jsonify(
                {
                    "reflection": result,
                }
            ),
            200,
        )

    @app.route("/api/history", methods=["GET"])
    @require_auth
    def api_get_history():
        """Retrieve recent saved reflections for the authenticated user."""
        items = list_reflections(g.user_id)
        return jsonify({"reflections": items}), 200

    @app.route("/api/history/<reflection_id>", methods=["DELETE"])
    @require_auth
    def api_delete_history(reflection_id: str):
        """Delete a saved reflection for the authenticated user."""
        deleted = delete_reflection(g.user_id, reflection_id)
        if not deleted:
            return jsonify({"error": "Reflection not found or could not be deleted."}), 404
        return jsonify({"success": True}), 200

    return app

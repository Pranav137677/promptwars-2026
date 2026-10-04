"""Configuration management for the Blind Spot application."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load local .env if present (ignored in production)
load_dotenv()


def _str_to_bool(val: str | None, default: bool = False) -> bool:
    """Convert common truthy/falsy environment string values to boolean."""
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "t", "on"}


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""

    # Google Gemini Settings
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Server Settings
    port: int = int(os.getenv("PORT", "8080"))
    environment: str = os.getenv("ENVIRONMENT", "production")
    ratelimit_default: str = os.getenv("RATELIMIT_DEFAULT", "10 per minute")
    max_content_length: int = 16 * 1024  # 16 KB request limit

    # Firebase Settings (Optional)
    firebase_enabled: bool = _str_to_bool(os.getenv("FIREBASE_ENABLED", "false"))
    firebase_project_id: str = os.getenv(
        "FIREBASE_PROJECT_ID", "promptwars-pranav-2026"
    )
    firebase_api_key: str = os.getenv("FIREBASE_API_KEY", "")
    firebase_auth_domain: str = os.getenv(
        "FIREBASE_AUTH_DOMAIN", f"{os.getenv('FIREBASE_PROJECT_ID', 'promptwars-pranav-2026')}.firebaseapp.com"
    )

    # Cloud Logging Settings
    gcp_project: str = os.getenv(
        "GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", "promptwars-pranav-2026")
    )
    is_cloud_run: bool = bool(os.getenv("K_SERVICE"))

    def validate_for_analysis(self) -> None:
        """Fail fast if critical API keys are missing when performing analysis."""
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is missing. "
                "Set GEMINI_API_KEY in your environment or Secret Manager before starting."
            )

    def client_firebase_config(self) -> dict[str, str | bool]:
        """Return safe public client configuration for Firebase Auth CDN integration."""
        return {
            "enabled": self.firebase_enabled,
            "projectId": self.firebase_project_id,
            "apiKey": self.firebase_api_key,
            "authDomain": self.firebase_auth_domain,
        }


# Singleton config instance
config = AppConfig()

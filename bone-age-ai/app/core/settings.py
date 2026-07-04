"""Application settings loaded from environment variables / .env file.

All configuration is centralised here so that no other module needs to read
``os.environ`` directly. This keeps configuration explicit and testable.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are read from environment variables and an optional ``.env`` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # --- Compute ---
    # "auto" resolves to cuda -> mps -> cpu depending on availability.
    device: str = "auto"

    # --- Models ---
    model_version: str = "current"
    crop_model_id: str = "ianpan/bone-age-crop"
    bone_age_model_id: str = "ianpan/bone-age"

    # --- Crop behaviour ---
    crop_padding: float = Field(default=0.05, ge=0.0, le=1.0)
    crop_confidence_threshold: float = Field(default=0.30, ge=0.0, le=1.0)

    # --- Upload limits ---
    max_upload_bytes: int = 25_000_000

    # --- Offline enforcement (mirrored into os.environ at startup) ---
    hf_hub_offline: str = "1"
    transformers_offline: str = "1"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, process-wide :class:`Settings` instance."""
    return Settings()

"""Filesystem paths and resolved runtime constants.

This module derives concrete paths (model directories, upload/log folders) from
:mod:`app.core.settings` and exposes a couple of helpers used across the app.
It also enforces HuggingFace *offline* mode as early as possible.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.core.settings import get_settings

# Project root = bone-age-ai/  (this file lives at app/core/config.py)
BASE_DIR: Path = Path(__file__).resolve().parents[2]

MODELS_DIR: Path = BASE_DIR / "models"
UPLOADS_DIR: Path = BASE_DIR / "uploads"
LOGS_DIR: Path = BASE_DIR / "logs"

CROP_MODEL_ROOT: Path = MODELS_DIR / "crop"
BONE_AGE_MODEL_ROOT: Path = MODELS_DIR / "bone-age"

# Reference image used for histogram matching (shipped inside the bone-age repo).
REF_IMAGE_NAME = "ref_img.png"


def _enforce_offline_mode() -> None:
    """Force Transformers / HuggingFace Hub to never touch the network.

    The architecture spec is explicit: the service must run completely offline
    and never call HuggingFace at runtime.
    """
    settings = get_settings()
    os.environ.setdefault("HF_HUB_OFFLINE", settings.hf_hub_offline)
    os.environ.setdefault("TRANSFORMERS_OFFLINE", settings.transformers_offline)
    # Avoid tokenizer fork warnings and keep things deterministic offline.
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def ensure_runtime_dirs() -> None:
    """Create the writable runtime directories if they do not yet exist."""
    for path in (UPLOADS_DIR, LOGS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def crop_model_dir(version: str | None = None) -> Path:
    """Return the on-disk directory for the crop model of ``version``."""
    version = version or get_settings().model_version
    return CROP_MODEL_ROOT / version


def bone_age_model_dir(version: str | None = None) -> Path:
    """Return the on-disk directory for the bone-age model of ``version``."""
    version = version or get_settings().model_version
    return BONE_AGE_MODEL_ROOT / version


# Enforce offline mode on import so it is set before Transformers is imported.
_enforce_offline_mode()

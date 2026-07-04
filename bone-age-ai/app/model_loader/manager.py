"""Singleton model manager.

Loads both models exactly once at startup, keeps them resident in memory, and
exposes them to the pipeline. This is the *only* piece of global state in the
service, as recommended by the architecture spec.
"""

from __future__ import annotations

import threading

import torch

from app.core.config import bone_age_model_dir, crop_model_dir
from app.core.logger import logger
from app.core.settings import get_settings
from app.model_loader.bone_age_model import BoneAgeModel
from app.model_loader.crop_model import CropModel


def resolve_device(preference: str) -> str:
    """Resolve a device preference into a concrete torch device string."""
    preference = (preference or "auto").lower()
    if preference == "auto":
        if torch.cuda.is_available():
            return "cuda"
        # Note: MPS is only used when explicitly requested to avoid subtle
        # numerical/op-support differences in custom model code.
        return "cpu"
    if preference == "cuda" and not torch.cuda.is_available():
        logger.warning("CUDA requested but not available; falling back to CPU.")
        return "cpu"
    if preference == "mps" and not torch.backends.mps.is_available():
        logger.warning("MPS requested but not available; falling back to CPU.")
        return "cpu"
    return preference


class ModelManager:
    """Owns the loaded crop and bone-age models for the process lifetime."""

    _instance: "ModelManager | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._settings = get_settings()
        self.device: str = resolve_device(self._settings.device)
        self.version: str = self._settings.model_version
        self.crop: CropModel | None = None
        self.bone_age: BoneAgeModel | None = None
        self._loaded = False

    @classmethod
    def instance(cls) -> "ModelManager":
        """Return the process-wide singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @property
    def loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        """Load and warm both models. Idempotent."""
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return

            logger.info(f"Initialising models on device='{self.device}'")
            self.crop = CropModel.load(
                path=crop_model_dir(self.version),
                device=self.device,
                model_id=self._settings.crop_model_id,
            )
            self.bone_age = BoneAgeModel.load(
                path=bone_age_model_dir(self.version),
                device=self.device,
                model_id=self._settings.bone_age_model_id,
            )

            logger.info("Warming models...")
            self.crop.warmup()
            self.bone_age.warmup()

            self._loaded = True
            logger.info("All models loaded and warm. Service is ready.")

    def unload(self) -> None:
        """Release model references (used on shutdown)."""
        self.crop = None
        self.bone_age = None
        self._loaded = False
        if self.device == "cuda":
            torch.cuda.empty_cache()

    def require_crop(self) -> CropModel:
        if not self._loaded or self.crop is None:
            raise RuntimeError("Crop model not loaded.")
        return self.crop

    def require_bone_age(self) -> BoneAgeModel:
        if not self._loaded or self.bone_age is None:
            raise RuntimeError("Bone-age model not loaded.")
        return self.bone_age

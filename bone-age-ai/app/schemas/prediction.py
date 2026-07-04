"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Sex(str, Enum):
    """Patient biological sex. Required by the bone-age model."""

    male = "male"
    female = "female"

    @property
    def is_female(self) -> int:
        """Model expects 1 for female, 0 for male."""
        return 1 if self is Sex.female else 0


class PredictionResponse(BaseModel):
    """Structured prediction result returned by ``POST /predict``."""

    bone_age_months: float = Field(..., description="Predicted bone age in months.")
    bone_age_years: float = Field(..., description="Predicted bone age in years.")
    crop_confidence: float = Field(
        ..., description="Heuristic confidence (0-1) that a hand was cropped."
    )
    bbox: list[int] = Field(
        ..., description="Crop bounding box in original pixels: [x, y, w, h]."
    )
    sex: Sex = Field(..., description="Patient sex used for the prediction.")
    model: str = Field(..., description="Bone-age model identifier.")
    crop_model: str = Field(..., description="Crop model identifier.")
    model_version: str = Field(..., description="Served model version.")
    processing_time_ms: int = Field(..., description="Total server-side latency.")
    request_id: str = Field(..., description="Correlation id for this request.")


class ModelInfo(BaseModel):
    """Metadata for a single loaded model."""

    id: str
    version: str
    loaded: bool
    path: str


class ModelsResponse(BaseModel):
    """Response body for ``GET /models``."""

    crop: ModelInfo
    bone_age: ModelInfo
    device: str


class HealthResponse(BaseModel):
    """Response body for ``GET /health``."""

    status: str = Field(..., description="'ready' once both models are warm.")
    models_loaded: bool
    device: str
    version: str

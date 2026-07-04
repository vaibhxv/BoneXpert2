"""Inference stage: run the bone-age model on a preprocessed image."""

from __future__ import annotations

import numpy as np

from app.model_loader.bone_age_model import BoneAgeModel
from app.schemas.prediction import Sex


class InferenceService:
    """Wraps the bone-age model forward pass."""

    def __init__(self, model: BoneAgeModel):
        self._model = model

    def predict_months(self, preprocessed: np.ndarray, sex: Sex) -> float:
        """Return the predicted bone age in months for the given sex."""
        return self._model.predict_months(preprocessed, is_female=sex.is_female)

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

    def predict_distribution(
        self, preprocessed: np.ndarray, sex: Sex
    ) -> tuple[float, np.ndarray]:
        """Return ``(bone_age_months, class_probabilities)`` for the given sex."""
        return self._model.predict_distribution(preprocessed, is_female=sex.is_female)

    @staticmethod
    def age_concentration(probs: np.ndarray, months: float, window: int) -> float:
        """Fraction of probability mass within +/- ``window`` months of ``months``.

        High for a confident (in-distribution) hand radiograph; low for diffuse
        out-of-distribution predictions.
        """
        idx = np.arange(probs.shape[0])
        lo, hi = months - window, months + window
        mask = (idx >= lo) & (idx <= hi)
        return float(probs[mask].sum())

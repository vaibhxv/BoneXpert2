"""Loader/wrapper for the bone-age model (``ianpan/bone-age``).

The published model is a 3-fold ``convnextv2_tiny`` ensemble with a
classification head; ``forward(x, female)`` returns the predicted bone age in
**months**. Histogram matching against the repo's ``ref_img.png`` is applied by
the preprocessing stage, so we expose that reference image here.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import torch

from app.core.config import REF_IMAGE_NAME
from app.core.logger import logger


class BoneAgeModel:
    """Thin wrapper around the bone-age model with a numpy-friendly API."""

    def __init__(
        self,
        model: torch.nn.Module,
        device: str,
        model_id: str,
        path: Path,
        ref_image: np.ndarray | None,
    ):
        self._model = model
        self._device = device
        self.model_id = model_id
        self.path = path
        self._ref_image = ref_image

    @classmethod
    def load(cls, path: Path, device: str, model_id: str) -> "BoneAgeModel":
        """Load the bone-age model and its histogram-matching reference image."""
        from transformers import AutoModel

        if not path.exists():
            raise FileNotFoundError(
                f"Bone-age model directory not found: {path}. "
                "Run `python scripts/download_models.py` first."
            )

        logger.info(f"Loading bone-age model from {path}")
        model = AutoModel.from_pretrained(str(path), trust_remote_code=True)
        model = model.eval().to(device)

        ref_image = cls._load_ref_image(path)
        return cls(
            model=model,
            device=device,
            model_id=model_id,
            path=path,
            ref_image=ref_image,
        )

    @staticmethod
    def _load_ref_image(path: Path) -> np.ndarray | None:
        ref_path = path / REF_IMAGE_NAME
        if not ref_path.exists():
            logger.warning(
                f"Reference image {ref_path} not found; histogram matching will "
                "be skipped (this slightly reduces accuracy)."
            )
            return None
        ref = cv2.imread(str(ref_path), cv2.IMREAD_GRAYSCALE)
        if ref is None:
            logger.warning(f"Failed to read reference image {ref_path}.")
        return ref

    @property
    def ref_image(self) -> np.ndarray | None:
        """Grayscale reference image for histogram matching (or ``None``)."""
        return self._ref_image

    def preprocess(self, image_gray: np.ndarray) -> np.ndarray:
        """Delegate to the model's own preprocessing (resize + normalise)."""
        return self._model.preprocess(image_gray)

    @torch.inference_mode()
    def predict_months(self, preprocessed: np.ndarray, is_female: int) -> float:
        """Run inference on an already-preprocessed image, returning months.

        ``preprocessed`` is the ``HxW`` array returned by :meth:`preprocess`.
        """
        x = torch.from_numpy(preprocessed).unsqueeze(0).unsqueeze(0).float()
        female = torch.tensor([int(is_female)])
        out = self._model(x.to(self._device), female.to(self._device))
        return float(torch.as_tensor(out).squeeze().detach().cpu().item())

    @torch.inference_mode()
    def predict_distribution(
        self, preprocessed: np.ndarray, is_female: int
    ) -> tuple[float, np.ndarray]:
        """Return ``(bone_age_months, class_probabilities)``.

        The class probabilities are the softmax over the ensemble's averaged
        logits (class ``i`` == ``i`` months). The expected value of this
        distribution is the predicted bone age. The full distribution lets the
        pipeline gauge how *concentrated* the prediction is, which is used as an
        out-of-distribution guardrail.
        """
        x = torch.from_numpy(preprocessed).unsqueeze(0).unsqueeze(0).float()
        female = torch.tensor([int(is_female)])
        logits = self._model(
            x.to(self._device), female.to(self._device), return_logits=True
        )
        probs = logits.softmax(1)[0].detach().cpu().numpy().astype(np.float64)
        indices = np.arange(probs.shape[0], dtype=np.float64)
        months = float((probs * indices).sum())
        return months, probs

    def warmup(self) -> None:
        """Run a dummy forward pass so the first real request is fast."""
        dummy = np.zeros((256, 256), dtype=np.uint8)
        pre = self.preprocess(dummy)
        self.predict_months(pre, is_female=0)
        logger.info("Bone-age model warmed up.")

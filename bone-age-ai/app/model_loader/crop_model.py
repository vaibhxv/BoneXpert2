"""Loader/wrapper for the hand-crop model (``ianpan/bone-age-crop``).

The published model is a ``mobilenetv3_small_100`` regressor that predicts
normalised ``xywh`` coordinates and rescales them to the original image when an
``img_shape`` tensor is supplied. We wrap it so the rest of the pipeline never
touches Transformers/torch details directly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from app.core.logger import logger


class CropModel:
    """Thin wrapper around the crop model with a numpy-friendly API."""

    def __init__(self, model: torch.nn.Module, device: str, model_id: str, path: Path):
        self._model = model
        self._device = device
        self.model_id = model_id
        self.path = path

    @classmethod
    def load(cls, path: Path, device: str, model_id: str) -> "CropModel":
        """Load the crop model from a local directory (offline)."""
        from transformers import AutoModel

        if not path.exists():
            raise FileNotFoundError(
                f"Crop model directory not found: {path}. "
                "Run `python scripts/download_models.py` first."
            )

        logger.info(f"Loading crop model from {path}")
        model = AutoModel.from_pretrained(str(path), trust_remote_code=True)
        model = model.eval().to(device)
        return cls(model=model, device=device, model_id=model_id, path=path)

    @torch.inference_mode()
    def predict_coords(self, image_gray: np.ndarray) -> np.ndarray:
        """Return the predicted crop box as ``[x, y, w, h]`` in original pixels.

        ``image_gray`` must be a 2-D grayscale ``uint8`` numpy array.
        """
        img_shape = torch.tensor([image_gray.shape[:2]])
        # The model ships its own preprocessing to guarantee an exact match.
        x = self._model.preprocess(image_gray)
        x = torch.from_numpy(x).unsqueeze(0).unsqueeze(0).float()
        coords = self._model(x.to(self._device), img_shape.to(self._device))
        return coords[0].detach().cpu().numpy()

    def warmup(self) -> None:
        """Run a dummy forward pass so the first real request is fast."""
        dummy = np.zeros((512, 512), dtype=np.uint8)
        self.predict_coords(dummy)
        logger.info("Crop model warmed up.")

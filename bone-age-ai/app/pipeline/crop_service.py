"""Crop stage: detect the hand and produce a padded, square crop.

The published crop model is a *regressor* (it outputs ``xywh`` directly) and
therefore has no native object-detection confidence score. We derive a
pragmatic, well-documented heuristic confidence from the geometric validity of
the predicted box (is it inside the image? is its area sensible?). This lets us
reject obviously bad crops (e.g. blank images / non-hand inputs) as required by
the spec's error handling section.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.core.logger import logger
from app.model_loader.crop_model import CropModel


@dataclass
class CropResult:
    """Output of the crop stage."""

    cropped: np.ndarray  # grayscale crop used downstream
    bbox: list[int]  # [x, y, w, h] in original image pixels
    confidence: float  # heuristic confidence in [0, 1]


class CropService:
    """Runs the crop model and shapes its output for downstream stages."""

    def __init__(self, model: CropModel, padding: float = 0.05):
        self._model = model
        self._padding = padding

    def crop(self, image_gray: np.ndarray) -> CropResult:
        """Detect the hand and return a padded, square, in-bounds crop."""
        h_img, w_img = image_gray.shape[:2]
        raw = self._model.predict_coords(image_gray)
        x, y, w, h = (float(v) for v in raw)

        confidence = self._estimate_confidence(x, y, w, h, w_img, h_img)

        x0, y0, x1, y1 = self._to_padded_square_box(x, y, w, h, w_img, h_img)
        cropped = image_gray[y0:y1, x0:x1]

        # Degenerate crop -> fall back to the full image so downstream never
        # receives an empty array, and force a low confidence.
        if cropped.size == 0:
            logger.warning("Crop produced an empty region; using full image.")
            cropped = image_gray
            x0, y0, x1, y1 = 0, 0, w_img, h_img
            confidence = 0.0

        bbox = [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]
        logger.info(f"Crop bbox={bbox} confidence={confidence:.3f}")
        return CropResult(cropped=cropped, bbox=bbox, confidence=confidence)

    def _to_padded_square_box(
        self, x: float, y: float, w: float, h: float, w_img: int, h_img: int
    ) -> tuple[int, int, int, int]:
        """Add padding, expand to a centered square, and clamp to the image."""
        cx, cy = x + w / 2.0, y + h / 2.0
        side = max(w, h) * (1.0 + 2.0 * self._padding)

        x0 = int(round(cx - side / 2.0))
        y0 = int(round(cy - side / 2.0))
        x1 = int(round(cx + side / 2.0))
        y1 = int(round(cy + side / 2.0))

        x0 = max(0, min(x0, w_img))
        y0 = max(0, min(y0, h_img))
        x1 = max(0, min(x1, w_img))
        y1 = max(0, min(y1, h_img))
        return x0, y0, x1, y1

    @staticmethod
    def _estimate_confidence(
        x: float, y: float, w: float, h: float, w_img: int, h_img: int
    ) -> float:
        """Heuristic confidence based on geometric plausibility of the box.

        Returns ~1.0 for a well-formed box occupying a sensible fraction of the
        frame, and drops towards 0 for degenerate / out-of-bounds boxes.
        """
        if w <= 1 or h <= 1 or w_img <= 0 or h_img <= 0:
            return 0.0

        img_area = float(w_img * h_img)
        box_area = float(max(w, 0.0) * max(h, 0.0))
        area_ratio = box_area / img_area if img_area > 0 else 0.0

        # A hand radiograph crop typically covers a large fraction of the frame.
        # Penalise very small (<5%) or implausibly large (>100%) boxes.
        if area_ratio <= 0.0:
            area_score = 0.0
        elif area_ratio < 0.05:
            area_score = area_ratio / 0.05
        elif area_ratio <= 1.0:
            area_score = 1.0
        else:
            area_score = max(0.0, 2.0 - area_ratio)

        # How well the box sits inside the image bounds.
        inside_w = max(0.0, min(x + w, w_img) - max(x, 0.0))
        inside_h = max(0.0, min(y + h, h_img) - max(y, 0.0))
        containment = (inside_w * inside_h) / box_area if box_area > 0 else 0.0

        return float(max(0.0, min(1.0, 0.5 * area_score + 0.5 * containment)))

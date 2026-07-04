"""Preprocessing stage.

This stage must match the author's published pipeline exactly:

1. Histogram matching against the repo's ``ref_img.png`` (skimage
   ``match_histograms``), then
2. the model's own ``preprocess`` (resize + pixel normalisation).

Keeping step 2 delegated to the model guarantees byte-for-byte identical
preprocessing to the original implementation.
"""

from __future__ import annotations

import numpy as np
from skimage.exposure import match_histograms

from app.core.logger import logger
from app.model_loader.bone_age_model import BoneAgeModel


class PreprocessService:
    """Applies histogram matching + model preprocessing to a cropped image."""

    def __init__(self, model: BoneAgeModel, enable_histogram_matching: bool = True):
        self._model = model
        self._enable_hist = enable_histogram_matching

    def run(self, cropped_gray: np.ndarray) -> np.ndarray:
        """Return the preprocessed array ready for the bone-age model."""
        image = cropped_gray

        ref = self._model.ref_image
        if self._enable_hist and ref is not None:
            # match_histograms works on 2-D grayscale arrays across skimage
            # versions; it returns a float array which the model's preprocess
            # accepts (identical to the author's usage).
            image = match_histograms(image, ref)
        else:
            logger.debug("Histogram matching skipped (no reference image).")

        return self._model.preprocess(image)

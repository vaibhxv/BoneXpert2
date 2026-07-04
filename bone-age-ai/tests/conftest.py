"""Shared test fixtures.

Tests use lightweight fakes for the two models so the full suite runs without
downloading any weights. This isolates the pipeline/business logic (crop
geometry, confidence heuristic, preprocessing wiring, postprocessing) from the
heavy ML dependencies, exactly as the spec's "benchmark each stage separately"
guidance suggests.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest


class FakeCropModel:
    """Returns a fixed bbox regardless of input."""

    model_id = "fake/crop"

    def __init__(self, coords=(100.0, 50.0, 400.0, 500.0)):
        self._coords = np.array(coords, dtype=np.float32)

    def predict_coords(self, image_gray: np.ndarray) -> np.ndarray:
        return self._coords.copy()


class FakeBoneAgeModel:
    """Echoes a fixed age and a trivial preprocess (identity resize)."""

    model_id = "fake/bone-age"

    def __init__(self, months=120.0, ref_image=None):
        self._months = months
        self._ref_image = ref_image

    @property
    def ref_image(self):
        return self._ref_image

    def preprocess(self, image_gray: np.ndarray) -> np.ndarray:
        return image_gray.astype(np.float32) / 255.0

    def predict_months(self, preprocessed: np.ndarray, is_female: int) -> float:
        # Return a value that depends on sex so tests can assert wiring.
        return self._months + (1.5 if is_female else 0.0)


@pytest.fixture
def fake_crop_model() -> FakeCropModel:
    return FakeCropModel()


@pytest.fixture
def fake_bone_age_model() -> FakeBoneAgeModel:
    ref = np.linspace(0, 255, 256 * 256, dtype=np.uint8).reshape(256, 256)
    return FakeBoneAgeModel(ref_image=ref)


@pytest.fixture
def sample_gray_image() -> np.ndarray:
    """A 600x800 grayscale image with a bright central rectangle."""
    img = np.zeros((600, 800), dtype=np.uint8)
    img[80:520, 150:520] = 200
    return img


@pytest.fixture
def sample_png_bytes(sample_gray_image: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", sample_gray_image)
    assert ok
    return buf.tobytes()

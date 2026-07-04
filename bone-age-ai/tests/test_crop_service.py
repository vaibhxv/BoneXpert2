"""Tests for the crop stage (geometry + confidence heuristic)."""

from __future__ import annotations

import numpy as np

from app.pipeline.crop_service import CropService
from tests.conftest import FakeCropModel


def test_crop_produces_square_padded_inbounds_box(sample_gray_image):
    service = CropService(model=FakeCropModel((100, 50, 400, 500)), padding=0.05)
    result = service.crop(sample_gray_image)

    x, y, w, h = result.bbox
    # Square (within rounding) and inside the image.
    assert abs(w - h) <= 2
    assert x >= 0 and y >= 0
    assert x + w <= sample_gray_image.shape[1]
    assert y + h <= sample_gray_image.shape[0]
    assert result.cropped.size > 0


def test_crop_confidence_high_for_reasonable_box(sample_gray_image):
    service = CropService(model=FakeCropModel((100, 50, 400, 500)), padding=0.05)
    result = service.crop(sample_gray_image)
    assert result.confidence > 0.5


def test_crop_confidence_low_for_degenerate_box(sample_gray_image):
    # A 1x1 box is degenerate -> confidence must be ~0.
    service = CropService(model=FakeCropModel((0, 0, 1, 1)), padding=0.05)
    result = service.crop(sample_gray_image)
    assert result.confidence < 0.3


def test_crop_handles_out_of_bounds_box(sample_gray_image):
    h, w = sample_gray_image.shape
    service = CropService(model=FakeCropModel((w - 5, h - 5, 400, 500)), padding=0.05)
    result = service.crop(sample_gray_image)
    bx, by, bw, bh = result.bbox
    assert bx + bw <= w
    assert by + bh <= h

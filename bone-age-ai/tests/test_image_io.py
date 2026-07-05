"""Tests for image decoding / validation."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from app.pipeline.errors import InvalidImageError
from app.pipeline.image_io import decode, decode_image


def test_decode_valid_png(sample_png_bytes: bytes):
    img = decode_image(sample_png_bytes, "hand.png")
    assert img.ndim == 2
    assert img.shape == (600, 800)
    assert img.dtype == np.uint8


def test_decode_empty_upload_raises():
    with pytest.raises(InvalidImageError):
        decode_image(b"", "empty.png")


def test_decode_corrupted_bytes_raises():
    with pytest.raises(InvalidImageError):
        decode_image(b"not-a-real-image", "broken.png")


def test_grayscale_image_has_zero_colorfulness(sample_png_bytes: bytes):
    result = decode(sample_png_bytes, "hand.png")
    assert result.colorfulness < 0.05


def test_color_image_has_high_colorfulness():
    rng = np.random.default_rng(0)
    color = rng.integers(0, 255, (200, 200, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".png", color)
    assert ok
    result = decode(buf.tobytes(), "photo.png")
    assert result.colorfulness > 0.5

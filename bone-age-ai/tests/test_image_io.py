"""Tests for image decoding / validation."""

from __future__ import annotations

import numpy as np
import pytest

from app.pipeline.errors import InvalidImageError
from app.pipeline.image_io import decode_image


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

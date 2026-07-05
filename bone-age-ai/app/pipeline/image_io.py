"""Decode uploaded bytes into a grayscale numpy image.

Supports standard raster formats (PNG/JPEG/BMP/TIFF via OpenCV) and DICOM
(``.dcm``) when ``pydicom`` is available. The models expect a 2-D grayscale
``uint8`` array, matching ``cv2.imread(path, 0)`` in the author's examples.

In addition to the grayscale image, decoding also reports a *colorfulness*
metric (fraction of noticeably-saturated pixels). Real radiographs are
(near) grayscale, so a high value is a strong signal that the upload is an
ordinary colour photo rather than an X-ray.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.pipeline.errors import InvalidImageError

_DICOM_MAGIC = b"DICM"  # located at byte offset 128 in a DICOM file


@dataclass
class DecodedImage:
    """Result of decoding an upload."""

    gray: np.ndarray  # 2-D grayscale uint8
    colorfulness: float  # 0.0 (pure grayscale) .. 1.0 (fully saturated colour)


def _looks_like_dicom(data: bytes, filename: str | None) -> bool:
    if filename and filename.lower().endswith((".dcm", ".dicom")):
        return True
    return len(data) > 132 and data[128:132] == _DICOM_MAGIC


def _decode_dicom(data: bytes) -> np.ndarray:
    try:
        import io

        import pydicom
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise InvalidImageError(
            "DICOM upload received but pydicom is not installed."
        ) from exc

    try:
        ds = pydicom.dcmread(io.BytesIO(data))
        arr = ds.pixel_array.astype(np.float32)
    except Exception as exc:  # noqa: BLE001
        raise InvalidImageError(f"Corrupted or unreadable DICOM file: {exc}") from exc

    # Normalise to 8-bit grayscale.
    arr -= arr.min()
    peak = arr.max()
    if peak > 0:
        arr = arr / peak * 255.0
    return arr.astype(np.uint8)


def _colorfulness(color_bgr: np.ndarray) -> float:
    """Fraction of pixels that are noticeably saturated (chromatic).

    ~0 for a true grayscale image (R==G==B), high for colour photographs.
    """
    hsv = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1].astype(np.float32) / 255.0
    return float(np.mean(sat > 0.15))


def decode(data: bytes, filename: str | None = None) -> DecodedImage:
    """Decode ``data`` into grayscale plus a colorfulness metric.

    Raises :class:`InvalidImageError` for empty, corrupted, or unsupported
    uploads.
    """
    if not data:
        raise InvalidImageError("Empty upload: no image bytes received.")

    if _looks_like_dicom(data, filename):
        # DICOM is intrinsically grayscale.
        return DecodedImage(gray=_decode_dicom(data), colorfulness=0.0)

    buffer = np.frombuffer(data, dtype=np.uint8)
    color = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if color is None:
        raise InvalidImageError(
            "Could not decode image. Supported formats: PNG, JPEG, BMP, TIFF, DICOM."
        )
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    return DecodedImage(gray=gray, colorfulness=_colorfulness(color))


def decode_image(data: bytes, filename: str | None = None) -> np.ndarray:
    """Backwards-compatible helper returning only the grayscale image."""
    return decode(data, filename).gray

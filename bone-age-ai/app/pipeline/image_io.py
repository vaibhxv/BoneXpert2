"""Decode uploaded bytes into a grayscale numpy image.

Supports standard raster formats (PNG/JPEG/BMP/TIFF via OpenCV) and DICOM
(``.dcm``) when ``pydicom`` is available. The models expect a 2-D grayscale
``uint8`` array, matching ``cv2.imread(path, 0)`` in the author's examples.
"""

from __future__ import annotations

import cv2
import numpy as np

from app.pipeline.errors import InvalidImageError

_DICOM_MAGIC = b"DICM"  # located at byte offset 128 in a DICOM file


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


def decode_image(data: bytes, filename: str | None = None) -> np.ndarray:
    """Decode ``data`` into a 2-D grayscale ``uint8`` numpy array.

    Raises :class:`InvalidImageError` for empty, corrupted, or unsupported
    uploads.
    """
    if not data:
        raise InvalidImageError("Empty upload: no image bytes received.")

    if _looks_like_dicom(data, filename):
        return _decode_dicom(data)

    buffer = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise InvalidImageError(
            "Could not decode image. Supported formats: PNG, JPEG, BMP, TIFF, DICOM."
        )
    return image

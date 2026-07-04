"""Domain-specific pipeline exceptions.

These are translated into descriptive HTTP errors by the API layer.
"""

from __future__ import annotations


class PipelineError(Exception):
    """Base class for all recoverable pipeline errors (mapped to HTTP 4xx)."""

    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidImageError(PipelineError):
    """Raised when the upload cannot be decoded into a valid image."""

    status_code = 422


class LowCropConfidenceError(PipelineError):
    """Raised when no hand is confidently detected in the radiograph."""

    status_code = 422

"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.model_loader.manager import ModelManager
from app.schemas.prediction import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report service readiness. 'ready' only once both models are warm."""
    manager = ModelManager.instance()
    return HealthResponse(
        status="ready" if manager.loaded else "loading",
        models_loaded=manager.loaded,
        device=manager.device,
        version=__version__,
    )

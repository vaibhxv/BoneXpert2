"""FastAPI application entry point.

Startup sequence (per the architecture spec):

    FastAPI starts -> load crop model -> load bone-age model ->
    warm both models -> health ready

Models are loaded exactly once via the singleton :class:`ModelManager` and kept
resident until shutdown.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__

# Import config first so HF offline mode is enforced before Transformers loads.
from app.core.config import ensure_runtime_dirs
from app.core.logger import configure_logging, logger
from app.core.settings import get_settings
from app.api import health, models, predict
from app.model_loader.manager import ModelManager
from app.pipeline.pipeline import BoneAgePipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    ensure_runtime_dirs()
    logger.info(f"Starting BoneXpert AI service v{__version__}")

    manager = ModelManager.instance()
    manager.load()  # load + warm both models
    app.state.pipeline = BoneAgePipeline(manager)

    logger.info("Startup complete; service is ready.")
    try:
        yield
    finally:
        logger.info("Shutting down; releasing models.")
        app.state.pipeline = None
        manager.unload()


def create_app() -> FastAPI:
    settings = get_settings()  # noqa: F841 - ensures settings resolve cleanly

    app = FastAPI(
        title="BoneXpert 2.0 - Offline Bone Age AI",
        version=__version__,
        description="Offline hand-radiograph bone-age inference service.",
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(models.router)
    app.include_router(predict.router)
    return app


app = create_app()


def main() -> None:
    """Run the service with uvicorn (used by ``python -m app.main``)."""
    import uvicorn

    settings = get_settings()
    configure_logging()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

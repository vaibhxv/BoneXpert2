"""Centralised Loguru configuration.

Logs are emitted to stderr (human friendly) and to a rotating file under
``logs/``. A per-request ``request_id`` is bound via ``logger.bind(...)`` in the
prediction endpoint so every stage can be correlated.
"""

from __future__ import annotations

import sys

from loguru import logger

from app.core.config import LOGS_DIR, ensure_runtime_dirs
from app.core.settings import get_settings

_CONFIGURED = False

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[request_id]}</cyan> | "
    "<level>{message}</level>"
)

_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{extra[request_id]} | {name}:{function}:{line} | {message}"
)


def configure_logging() -> None:
    """Configure Loguru sinks exactly once for the process."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    ensure_runtime_dirs()
    settings = get_settings()

    logger.remove()
    # Default a request_id so records outside a request context still format.
    logger.configure(extra={"request_id": "-"})

    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        format=_CONSOLE_FORMAT,
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )
    logger.add(
        LOGS_DIR / "service_{time:YYYY-MM-DD}.log",
        level=settings.log_level.upper(),
        format=_FILE_FORMAT,
        rotation="20 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    _CONFIGURED = True


__all__ = ["logger", "configure_logging"]

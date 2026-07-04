"""Tests for the health endpoint (no models required).

We mount only the health router on a bare app so the model-loading lifespan
does not run.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import health


def test_health_endpoint_returns_status():
    app = FastAPI()
    app.include_router(health.router)
    client = TestClient(app)

    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in {"ready", "loading"}
    assert "device" in body
    assert "models_loaded" in body

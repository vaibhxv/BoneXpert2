"""Prediction endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.core.logger import logger
from app.core.settings import get_settings
from app.pipeline.errors import PipelineError
from app.pipeline.pipeline import BoneAgePipeline
from app.schemas.prediction import PredictionResponse, Sex

router = APIRouter(tags=["predict"])


def _get_pipeline(request: Request) -> BoneAgePipeline:
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(
            status_code=503, detail="Service is still loading models. Try again shortly."
        )
    return pipeline


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: Request,
    image: UploadFile = File(..., description="Hand radiograph (PNG/JPEG/DICOM)."),
    sex: Sex = Form(..., description="Patient sex: 'male' or 'female'."),
) -> PredictionResponse:
    """Predict bone age from a hand radiograph."""
    settings = get_settings()
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request_logger = logger.bind(request_id=request_id)

    data = await image.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Upload exceeds maximum size of {settings.max_upload_bytes} bytes.",
        )

    request_logger.info(
        f"predict request: filename='{image.filename}' "
        f"content_type='{image.content_type}' size={len(data)} sex='{sex.value}'"
    )

    pipeline = _get_pipeline(request)

    try:
        with logger.contextualize(request_id=request_id):
            result = pipeline.run(
                image_bytes=data,
                filename=image.filename,
                sex=sex,
                request_id=request_id,
            )
    except PipelineError as exc:
        request_logger.warning(f"pipeline rejected request: {exc.message}")
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception as exc:  # noqa: BLE001
        request_logger.exception("unexpected inference error")
        raise HTTPException(
            status_code=500, detail="Internal inference error."
        ) from exc

    return result

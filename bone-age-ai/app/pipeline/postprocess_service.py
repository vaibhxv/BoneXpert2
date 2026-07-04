"""Post-processing stage: assemble the final structured response."""

from __future__ import annotations

from app.pipeline.crop_service import CropResult
from app.schemas.prediction import PredictionResponse, Sex


class PostprocessService:
    """Converts raw model output into the public :class:`PredictionResponse`."""

    def build(
        self,
        *,
        bone_age_months: float,
        crop: CropResult,
        sex: Sex,
        model_id: str,
        crop_model_id: str,
        model_version: str,
        processing_time_ms: int,
        request_id: str,
    ) -> PredictionResponse:
        return PredictionResponse(
            bone_age_months=round(bone_age_months, 2),
            bone_age_years=round(bone_age_months / 12.0, 2),
            crop_confidence=round(crop.confidence, 4),
            bbox=crop.bbox,
            sex=sex,
            model=model_id,
            crop_model=crop_model_id,
            model_version=model_version,
            processing_time_ms=processing_time_ms,
            request_id=request_id,
        )

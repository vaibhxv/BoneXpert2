"""End-to-end bone-age prediction pipeline orchestrator.

Wires the individual stages together, times each one for benchmarking, and
enforces the crop-confidence threshold. Every stage is a separate injectable
class so it can be tested and benchmarked in isolation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.core.logger import logger
from app.core.settings import get_settings
from app.model_loader.manager import ModelManager
from app.pipeline.crop_service import CropService
from app.pipeline.errors import LowCropConfidenceError
from app.pipeline.image_io import decode_image
from app.pipeline.inference_service import InferenceService
from app.pipeline.postprocess_service import PostprocessService
from app.pipeline.preprocess_service import PreprocessService
from app.schemas.prediction import PredictionResponse, Sex


@dataclass
class StageTimings:
    decode_ms: int = 0
    crop_ms: int = 0
    preprocess_ms: int = 0
    inference_ms: int = 0
    total_ms: int = 0


class BoneAgePipeline:
    """Coordinates decode -> crop -> preprocess -> inference -> postprocess."""

    def __init__(self, manager: ModelManager):
        self._manager = manager
        self._settings = get_settings()
        self._crop = CropService(
            model=manager.require_crop(), padding=self._settings.crop_padding
        )
        self._preprocess = PreprocessService(model=manager.require_bone_age())
        self._inference = InferenceService(model=manager.require_bone_age())
        self._postprocess = PostprocessService()

    def run(
        self,
        *,
        image_bytes: bytes,
        filename: str | None,
        sex: Sex,
        request_id: str,
    ) -> PredictionResponse:
        """Execute the full pipeline and return a structured prediction."""
        timings = StageTimings()
        t_start = time.perf_counter()

        # 1. Decode + validate.
        t0 = time.perf_counter()
        image = decode_image(image_bytes, filename)
        timings.decode_ms = _ms_since(t0)

        # 2. Crop.
        t0 = time.perf_counter()
        crop = self._crop.crop(image)
        timings.crop_ms = _ms_since(t0)

        threshold = self._settings.crop_confidence_threshold
        if crop.confidence < threshold:
            raise LowCropConfidenceError(
                f"No hand detected with sufficient confidence "
                f"({crop.confidence:.2f} < {threshold:.2f}). "
                "Please upload a clear hand radiograph."
            )

        # 3. Preprocess (histogram match + model preprocessing).
        t0 = time.perf_counter()
        preprocessed = self._preprocess.run(crop.cropped)
        timings.preprocess_ms = _ms_since(t0)

        # 4. Inference.
        t0 = time.perf_counter()
        months = self._inference.predict_months(preprocessed, sex)
        timings.inference_ms = _ms_since(t0)

        timings.total_ms = _ms_since(t_start)

        logger.info(
            "Pipeline complete: decode={}ms crop={}ms preprocess={}ms "
            "inference={}ms total={}ms bone_age_months={:.2f}".format(
                timings.decode_ms,
                timings.crop_ms,
                timings.preprocess_ms,
                timings.inference_ms,
                timings.total_ms,
                months,
            )
        )

        # 5. Post-process.
        return self._postprocess.build(
            bone_age_months=months,
            crop=crop,
            sex=sex,
            model_id=self._manager.require_bone_age().model_id,
            crop_model_id=self._manager.require_crop().model_id,
            model_version=self._manager.version,
            processing_time_ms=timings.total_ms,
            request_id=request_id,
        )


def _ms_since(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)

"""Tests for inference wiring and postprocessing."""

from __future__ import annotations

import numpy as np

from app.pipeline.crop_service import CropResult
from app.pipeline.inference_service import InferenceService
from app.pipeline.postprocess_service import PostprocessService
from app.schemas.prediction import Sex


def test_inference_passes_sex_flag(fake_bone_age_model):
    service = InferenceService(model=fake_bone_age_model)
    pre = np.zeros((8, 8), dtype=np.float32)
    male = service.predict_months(pre, Sex.male)
    female = service.predict_months(pre, Sex.female)
    assert female != male  # fake model adds 1.5 months for female


def test_postprocess_converts_months_to_years():
    crop = CropResult(cropped=np.zeros((4, 4), np.uint8), bbox=[0, 0, 4, 4], confidence=0.9)
    resp = PostprocessService().build(
        bone_age_months=138.0,
        crop=crop,
        sex=Sex.female,
        model_id="m",
        crop_model_id="c",
        model_version="current",
        processing_time_ms=42,
        request_id="abc",
    )
    assert resp.bone_age_months == 138.0
    assert resp.bone_age_years == 11.5
    assert resp.crop_confidence == 0.9
    assert resp.model_version == "current"
    assert resp.request_id == "abc"


def test_sex_is_female_flag():
    assert Sex.female.is_female == 1
    assert Sex.male.is_female == 0

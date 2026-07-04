"""Tests for the preprocessing stage."""

from __future__ import annotations

import numpy as np

from app.pipeline.preprocess_service import PreprocessService
from tests.conftest import FakeBoneAgeModel


def test_preprocess_returns_model_preprocessed_array(fake_bone_age_model, sample_gray_image):
    service = PreprocessService(model=fake_bone_age_model)
    out = service.run(sample_gray_image)
    assert out.dtype == np.float32
    assert out.max() <= 1.0


def test_preprocess_skips_histogram_matching_without_ref(sample_gray_image):
    model = FakeBoneAgeModel(ref_image=None)
    service = PreprocessService(model=model)
    out = service.run(sample_gray_image)
    # Identity preprocess (divide by 255) since no histogram matching applied.
    np.testing.assert_allclose(out, sample_gray_image.astype(np.float32) / 255.0)


def test_preprocess_applies_histogram_matching_with_ref(fake_bone_age_model, sample_gray_image):
    service = PreprocessService(model=fake_bone_age_model)
    out = service.run(sample_gray_image)
    # With histogram matching the flat 200-valued region is remapped, so the
    # output should differ from the naive identity preprocessing.
    identity = sample_gray_image.astype(np.float32) / 255.0
    assert not np.allclose(out, identity)

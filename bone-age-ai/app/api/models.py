"""Models metadata endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import bone_age_model_dir, crop_model_dir
from app.model_loader.manager import ModelManager
from app.schemas.prediction import ModelInfo, ModelsResponse

router = APIRouter(tags=["models"])


@router.get("/models", response_model=ModelsResponse)
def models() -> ModelsResponse:
    """Return the loaded model identifiers, versions, and device."""
    manager = ModelManager.instance()
    version = manager.version

    return ModelsResponse(
        crop=ModelInfo(
            id=manager.crop.model_id if manager.crop else manager._settings.crop_model_id,
            version=version,
            loaded=manager.crop is not None,
            path=str(crop_model_dir(version)),
        ),
        bone_age=ModelInfo(
            id=(
                manager.bone_age.model_id
                if manager.bone_age
                else manager._settings.bone_age_model_id
            ),
            version=version,
            loaded=manager.bone_age is not None,
            path=str(bone_age_model_dir(version)),
        ),
        device=manager.device,
    )

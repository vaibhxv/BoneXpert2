#!/usr/bin/env python3
"""Download the crop and bone-age models from HuggingFace for OFFLINE use.

This is the *only* script permitted to touch the network. It downloads a full
snapshot of each model repository (weights + custom modeling code + the
``ref_img.png`` reference used for histogram matching) into a versioned folder
and then points ``current`` at that version.

Layout produced::

    models/
      crop/
        v1/            <- downloaded snapshot
        current -> v1  <- symlink used at runtime
      bone-age/
        v1/
        current -> v1

Usage::

    python scripts/download_models.py                # download into "v1"
    python scripts/download_models.py --version v2   # download into "v2"
    python scripts/download_models.py --no-activate  # download but keep current

After running this once, start the service with HF_HUB_OFFLINE=1 (the default)
and it will never contact HuggingFace again.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Make sure we can import the app package regardless of CWD.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# This script *must* be allowed online, so explicitly disable offline mode
# before importing anything that reads those env vars.
os.environ["HF_HUB_OFFLINE"] = "0"
os.environ["TRANSFORMERS_OFFLINE"] = "0"

from app.core.config import (  # noqa: E402
    BONE_AGE_MODEL_ROOT,
    CROP_MODEL_ROOT,
)
from app.core.settings import get_settings  # noqa: E402


def _download_one(repo_id: str, root: Path, version: str, activate: bool) -> Path:
    """Snapshot ``repo_id`` into ``root/version`` and optionally activate it."""
    from huggingface_hub import snapshot_download

    target = root / version
    target.mkdir(parents=True, exist_ok=True)

    print(f"[download] {repo_id} -> {target}")
    # snapshot_download copies real files into local_dir (self-contained and
    # portable for offline deployment).
    snapshot_download(repo_id=repo_id, local_dir=str(target))

    if activate:
        _activate(root, version)
    return target


def _activate(root: Path, version: str) -> None:
    """Point ``root/current`` at ``root/version`` via a relative symlink."""
    current = root / "current"
    if current.is_symlink() or current.exists():
        if current.is_symlink() or current.is_file():
            current.unlink()
        else:
            # A real directory named "current" already holds weights; leave it.
            print(f"[activate] {current} is a real directory; not replacing it.")
            return
    current.symlink_to(version, target_is_directory=True)
    print(f"[activate] {current} -> {version}")


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        default="v1",
        help="Version folder to download into (default: v1).",
    )
    parser.add_argument(
        "--no-activate",
        action="store_true",
        help="Do not repoint 'current' to the downloaded version.",
    )
    parser.add_argument(
        "--crop-model-id", default=settings.crop_model_id, help="Crop model repo id."
    )
    parser.add_argument(
        "--bone-age-model-id",
        default=settings.bone_age_model_id,
        help="Bone-age model repo id.",
    )
    args = parser.parse_args()

    activate = not args.no_activate

    try:
        _download_one(args.crop_model_id, CROP_MODEL_ROOT, args.version, activate)
        _download_one(
            args.bone_age_model_id, BONE_AGE_MODEL_ROOT, args.version, activate
        )
    except Exception as exc:  # noqa: BLE001 - surface a clean CLI error.
        print(f"[error] download failed: {exc}", file=sys.stderr)
        return 1

    print("\n[done] Models are ready for offline inference.")
    print("       Start the service with:  python -m app.main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

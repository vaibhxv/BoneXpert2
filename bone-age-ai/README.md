# BoneXpert 2.0 — Offline Bone-Age AI Service

A production-ready, **fully offline** FastAPI service that predicts skeletal
(bone) age from a pediatric hand radiograph. It uses two published models:

| Role      | Model                     | Backbone              |
|-----------|---------------------------|-----------------------|
| Crop      | `ianpan/bone-age-crop`    | `mobilenetv3_small_100` |
| Bone age  | `ianpan/bone-age`         | `convnextv2_tiny` (3-fold ensemble) |

NestJS handles auth, uploads, storage, and reporting. This service does the AI
inference only.

---

## 1. Setup

```bash
cd bone-age-ai

# create + activate a virtualenv (Python 3.12)
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# copy config (optional; sane defaults are built in)
cp .env.example .env
```

## 2. Download the models (one-time, requires internet)

This is the **only** step that touches the network. It fetches the weights, the
custom modeling code, and `ref_img.png` (needed for histogram matching) into
`models/…/v1/` and points `current` at it.

```bash
python scripts/download_models.py
```

Result:

```
models/
  crop/      current -> v1/
  bone-age/  current -> v1/
```

After this, the service runs completely offline (`HF_HUB_OFFLINE=1` is enforced
in code).

## 3. Run the service

```bash
python -m app.main
# or, with autoreload during development:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On startup it loads and warms both models, then reports `ready` on `/health`.

## 4. Endpoints

### `GET /health`
```json
{ "status": "ready", "models_loaded": true, "device": "cpu", "version": "1.0.0" }
```

### `GET /models`
Returns loaded model ids, versions, on-disk paths, and the compute device.

### `POST /predict` (multipart)
Fields: `image` (file), `sex` (`male` | `female`).

```bash
curl -X POST http://localhost:8000/predict \
  -F "image=@hand.png" \
  -F "sex=female"
```

Response:
```json
{
  "bone_age_months": 138.4,
  "bone_age_years": 11.53,
  "crop_confidence": 0.99,
  "bbox": [120, 45, 812, 921],
  "sex": "female",
  "model": "ianpan/bone-age",
  "crop_model": "ianpan/bone-age-crop",
  "model_version": "current",
  "processing_time_ms": 612,
  "request_id": "a1b2c3d4e5f6"
}
```

## 5. Architecture

```
app/
  api/          FastAPI routers (health, models, predict)
  core/         settings, config/paths, logging
  model_loader/ crop_model, bone_age_model, singleton manager
  pipeline/     crop -> preprocess -> inference -> postprocess (+ orchestrator)
  schemas/      pydantic request/response models
  main.py       app factory + startup lifespan
scripts/
  download_models.py   one-time offline model fetch
models/         downloaded weights (git-ignored)
uploads/ logs/  runtime artifacts
tests/          per-stage unit tests
```

Each pipeline stage is a standalone class and can be tested/benchmarked
independently. The **only** global state is the singleton `ModelManager`, which
loads both models once at startup and never reloads per request.

### Preprocessing fidelity
Preprocessing intentionally reuses each model's own `.preprocess()` method plus
`skimage.exposure.match_histograms` against the shipped `ref_img.png`, matching
the author's published pipeline exactly (best reported MAE = 4.16 months).

### Crop confidence
The crop model is a *regressor* with no native detection score. `crop_confidence`
is a documented geometric heuristic (box area ratio + in-bounds containment)
used only to reject blank/non-hand uploads via
`CROP_CONFIDENCE_THRESHOLD`.

### Input-validity guardrails
Because the crop model always emits a box and the bone-age model is a
classifier that will map *any* texture onto an age, two guardrails reject
non-radiograph uploads (returning HTTP 422 with a clear message):

1. **Colorfulness** — real radiographs are (near) grayscale. Uploads whose
   fraction of saturated pixels exceeds `MAX_COLORFULNESS` (default 0.20) are
   rejected as colour photos before any inference runs.
2. **Age-distribution concentration** — for a genuine hand the classifier's
   softmax mass concentrates within a few months of the prediction. If less
   than `MIN_AGE_CONCENTRATION` (default 0.70) of the mass falls within
   `±AGE_CONCENTRATION_WINDOW` months (default 18), the image is treated as
   out-of-distribution and rejected.

Empirically a valid hand scored ~0.98 concentration while noise/gradients/blobs
scored ≤0.59, giving clean separation.

## 6. Model versioning

```bash
# download new weights into a new version without activating
python scripts/download_models.py --version v2 --no-activate
# then point current at it and restart
ln -sfn v2 models/bone-age/current
ln -sfn v2 models/crop/current
```

To deploy your own fine-tuned weights, replace the contents of
`models/bone-age/current/` and restart. **No API changes required.**

## 7. Tests

```bash
pytest          # runs without downloading any models (uses fakes)
```

## 8. Configuration

All settings live in `.env` (see `.env.example`). Key options: `DEVICE`
(`auto`/`cpu`/`cuda`/`mps`), `CROP_CONFIDENCE_THRESHOLD`, `CROP_PADDING`,
`MAX_UPLOAD_BYTES`, `MODEL_VERSION`.

> ⚠️ Research/demonstration use only. Not approved for clinical use.

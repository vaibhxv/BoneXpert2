# BoneXpert 2.0 -- Offline AI Inference Service Architecture Specification

> Version: 1.0
>
> Purpose: This document is the engineering specification for an offline
> bone-age inference service using two Hugging Face models:
>
> -   Crop model: `ianpan/bone-age-crop`
> -   Bone age model: `ianpan/bone-age`
>
> NestJS is **not** responsible for AI inference. It orchestrates
> uploads, authentication, storage, reporting, and API access.

------------------------------------------------------------------------

# 1. Objectives

Build a production-ready Python inference service that:

-   Runs completely offline
-   Loads both models once during startup
-   Accepts hand radiographs
-   Crops the hand automatically
-   Applies identical preprocessing expected by the published model
-   Predicts bone age
-   Returns structured JSON
-   Can later be replaced with your own fine-tuned weights without
    changing the API

------------------------------------------------------------------------

# 2. High-Level Architecture

``` text
                 Client
                    │
                    ▼
               NestJS API
                    │
          Save uploaded image
                    │
                    ▼
          HTTP POST /predict
                    │
                    ▼
        Python FastAPI AI Service
                    │
      ┌─────────────┴─────────────┐
      ▼                           ▼
 Crop Model                 Bone Age Model
 (ianpan/bone-age-crop)     (ianpan/bone-age)
      │                           ▲
      └────► Preprocessing ───────┘
                    │
              JSON Response
                    │
                    ▼
               NestJS stores result
```

------------------------------------------------------------------------

# 3. Repository Structure

``` text
bone-age-ai/
│
├── app/
│   ├── api/
│   │   ├── health.py
│   │   ├── predict.py
│   │   └── models.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── settings.py
│   │
│   ├── pipeline/
│   │   ├── crop_service.py
│   │   ├── preprocess_service.py
│   │   ├── inference_service.py
│   │   ├── postprocess_service.py
│   │   └── pipeline.py
│   │
│   ├── model_loader/
│   │   ├── crop_model.py
│   │   ├── bone_age_model.py
│   │   └── manager.py
│   │
│   ├── schemas/
│   └── main.py
│
├── models/
│   ├── crop/
│   │   └── current/
│   └── bone-age/
│       └── current/
│
├── uploads/
├── logs/
└── tests/
```

------------------------------------------------------------------------

# 4. Tech Stack

## Runtime

-   Python 3.12
-   FastAPI
-   Uvicorn

## AI

-   PyTorch
-   Transformers
-   HuggingFace Hub (download only)
-   Pillow
-   OpenCV
-   NumPy

## Utilities

-   Pydantic
-   python-multipart
-   Loguru
-   pytest

No Docker.

------------------------------------------------------------------------

# 5. Offline Model Download

Run once:

``` bash
git lfs install

git clone https://huggingface.co/ianpan/bone-age
git clone https://huggingface.co/ianpan/bone-age-crop
```

Copy into:

``` text
models/
  crop/current/
  bone-age/current/
```

The application must always load from local disk.

Never call Hugging Face at runtime.

------------------------------------------------------------------------

# 6. Startup Sequence

``` text
FastAPI Starts
      │
Load Crop Model
      │
Load Bone Age Model
      │
Warm Both Models
      │
Health Ready
```

Both models remain in memory until shutdown.

------------------------------------------------------------------------

# 7. Prediction Pipeline

``` text
Receive Upload
      │
Validate Image
      │
Crop Model
      │
Crop Hand
      │
Histogram Matching
      │
Resize
      │
Normalize
      │
Bone Age Model
      │
Convert Output
      │
Return JSON
```

------------------------------------------------------------------------

# 8. Crop Service

Responsibilities

-   Load crop model
-   Detect hand
-   Extract bounding box
-   Add configurable padding
-   Produce square crop
-   Reject if confidence is too low

Return:

``` json
{
  "crop_confidence":0.99,
  "bbox":[120,45,812,921]
}
```

------------------------------------------------------------------------

# 9. Preprocessing Service

This stage **must exactly match the author's preprocessing**.

Tasks:

-   RGB conversion (if required)
-   Histogram matching
-   Resize
-   Pixel normalization
-   Tensor conversion

Changing preprocessing will reduce accuracy.

------------------------------------------------------------------------

# 10. Bone Age Service

Input:

-   Preprocessed tensor
-   Patient sex (if required)

Output:

``` json
{
  "bone_age_months":138.4,
  "bone_age_years":11.53
}
```

------------------------------------------------------------------------

# 11. Post Processing

Return:

``` json
{
  "bone_age_months":138.4,
  "bone_age_years":11.53,
  "crop_confidence":0.99,
  "model":"ianpan/bone-age",
  "crop_model":"ianpan/bone-age-crop",
  "model_version":"v1",
  "processing_time_ms":612
}
```

------------------------------------------------------------------------

# 12. FastAPI Endpoints

## GET /health

Returns service status.

## GET /models

Returns loaded model names and versions.

## POST /predict

Multipart:

-   image
-   sex

Returns prediction.

------------------------------------------------------------------------

# 13. Error Handling

Reject:

-   Empty uploads
-   Unsupported formats
-   Missing hand
-   Crop confidence below threshold
-   Corrupted images

Return descriptive HTTP errors.

------------------------------------------------------------------------

# 14. Logging

Record:

-   Request ID
-   Filename
-   Crop duration
-   Inference duration
-   Total latency
-   Errors

------------------------------------------------------------------------

# 15. Model Versioning

``` text
models/
  crop/
    current/
    v1/
    v2/
  bone-age/
    current/
    v1/
    v2/
```

To deploy a new model:

1.  Copy new weights into a version folder.
2.  Point `current` to the new version.
3.  Restart FastAPI.

NestJS remains unchanged.

------------------------------------------------------------------------

# 16. NestJS Integration

NestJS responsibilities:

-   Authentication
-   Upload handling
-   File storage
-   Patient records
-   Report generation
-   Audit logs

Prediction flow:

``` text
Upload
   │
NestJS
   │
Save File
   │
POST /predict
   │
FastAPI
   │
Prediction JSON
   │
NestJS
   │
Persist & Respond
```

------------------------------------------------------------------------

# 17. Development Order

1.  Project scaffold
2.  Health endpoint
3.  Local model loading
4.  Crop service
5.  Preprocessing
6.  Bone-age inference
7.  Prediction endpoint
8.  Logging
9.  Unit tests
10. NestJS integration

------------------------------------------------------------------------

# 18. Future Upgrades

The public models are your baseline only.

Later replace only the weights:

``` text
models/bone-age/current/
```

with your fine-tuned model trained on your own dataset.

No API changes are required.

------------------------------------------------------------------------

# Cursor Implementation Notes

-   Keep every stage in a separate class.
-   Avoid global state except the singleton model manager.
-   Load both models once at startup.
-   Never reload weights per request.
-   Keep preprocessing identical to the original implementation.
-   Write unit tests for crop, preprocessing, and inference
    independently.
-   Ensure every stage can be benchmarked separately.

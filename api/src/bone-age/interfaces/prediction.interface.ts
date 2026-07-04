/**
 * Shape of the JSON returned by the Python inference service `POST /predict`.
 * Kept in sync with `app/schemas/prediction.py` in the bone-age-ai service.
 */
export interface BoneAgePrediction {
  bone_age_months: number;
  bone_age_years: number;
  crop_confidence: number;
  bbox: [number, number, number, number];
  sex: 'male' | 'female';
  model: string;
  crop_model: string;
  model_version: string;
  processing_time_ms: number;
  request_id: string;
}

/** Shape of the Python service `GET /health` response. */
export interface BoneAgeHealth {
  status: 'ready' | 'loading';
  models_loaded: boolean;
  device: string;
  version: string;
}

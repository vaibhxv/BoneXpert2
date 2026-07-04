/**
 * Client for the NestJS bone-age gateway.
 *
 * Requests are same-origin: in dev, Vite proxies `/bone-age/*` to the NestJS
 * server; in production NestJS serves this UI and the API together. An explicit
 * base can be provided via `VITE_API_URL` when the API lives elsewhere.
 */

// Same-origin by default: the NestJS gateway serves this UI and exposes the API
// under `/api`. Override with VITE_API_URL when the API lives elsewhere.
const API_BASE = (import.meta.env.VITE_API_URL ?? '/api').replace(/\/+$/, '');

export type Sex = 'male' | 'female';

export interface BoneAgePrediction {
  bone_age_months: number;
  bone_age_years: number;
  crop_confidence: number;
  bbox: [number, number, number, number];
  sex: Sex;
  model: string;
  crop_model: string;
  model_version: string;
  processing_time_ms: number;
  request_id: string;
}

export interface BoneAgeHealth {
  status: 'ready' | 'loading';
  models_loaded: boolean;
  device: string;
  version: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function extractDetail(data: unknown, fallback: string): string {
  if (data && typeof data === 'object' && 'message' in data) {
    const msg = (data as { message: unknown }).message;
    if (Array.isArray(msg)) return msg.join(', ');
    if (typeof msg === 'string') return msg;
  }
  if (data && typeof data === 'object' && 'detail' in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
  }
  return fallback;
}

export async function getHealth(signal?: AbortSignal): Promise<BoneAgeHealth> {
  const res = await fetch(`${API_BASE}/bone-age/health`, { signal });
  if (!res.ok) throw new ApiError('Gateway unavailable', res.status);
  return (await res.json()) as BoneAgeHealth;
}

export async function predict(
  file: File,
  sex: Sex,
  signal?: AbortSignal,
): Promise<BoneAgePrediction> {
  const form = new FormData();
  form.append('image', file);
  form.append('sex', sex);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/bone-age/predict`, {
      method: 'POST',
      body: form,
      signal,
    });
  } catch (err) {
    if ((err as Error).name === 'AbortError') throw err;
    throw new ApiError('Cannot reach the analysis gateway.', 0);
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(
      extractDetail(data, 'Analysis failed. Please try another image.'),
      res.status,
    );
  }
  return data as BoneAgePrediction;
}

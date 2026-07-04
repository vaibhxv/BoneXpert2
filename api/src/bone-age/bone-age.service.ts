import {
  HttpException,
  Injectable,
  InternalServerErrorException,
  Logger,
  ServiceUnavailableException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { HttpService } from '@nestjs/axios';
import { AxiosError } from 'axios';
import FormData from 'form-data';
import { firstValueFrom } from 'rxjs';

import { Sex } from './dto/predict-bone-age.dto';
import {
  BoneAgeHealth,
  BoneAgePrediction,
} from './interfaces/prediction.interface';

/**
 * Thin client around the Python FastAPI inference service.
 *
 * NestJS never runs AI code: it forwards the uploaded radiograph to the Python
 * service and returns the structured prediction. All HTTP concerns (base URL,
 * timeout, error translation) live here.
 */
@Injectable()
export class BoneAgeService {
  private readonly logger = new Logger(BoneAgeService.name);
  private readonly baseUrl: string;
  private readonly timeoutMs: number;

  constructor(
    private readonly http: HttpService,
    private readonly config: ConfigService,
  ) {
    this.baseUrl = this.config
      .get<string>('PYTHON_SERVICE_URL', 'http://localhost:8000')
      .replace(/\/+$/, '');
    this.timeoutMs = this.config.get<number>('PYTHON_SERVICE_TIMEOUT_MS', 30000);
  }

  /** Forward an in-memory image buffer to the Python `/predict` endpoint. */
  async predict(
    file: { buffer: Buffer; originalname: string; mimetype: string },
    sex: Sex,
    requestId: string,
  ): Promise<BoneAgePrediction> {
    const form = new FormData();
    form.append('image', file.buffer, {
      filename: file.originalname || 'upload',
      contentType: file.mimetype || 'application/octet-stream',
    });
    form.append('sex', sex);

    try {
      const { data } = await firstValueFrom(
        this.http.post<BoneAgePrediction>(`${this.baseUrl}/predict`, form, {
          headers: { ...form.getHeaders(), 'x-request-id': requestId },
          timeout: this.timeoutMs,
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
        }),
      );
      return data;
    } catch (error) {
      throw this.translateError(error, requestId);
    }
  }

  /** Proxy the Python service health check. */
  async health(): Promise<BoneAgeHealth> {
    try {
      const { data } = await firstValueFrom(
        this.http.get<BoneAgeHealth>(`${this.baseUrl}/health`, {
          timeout: this.timeoutMs,
        }),
      );
      return data;
    } catch (error) {
      throw this.translateError(error, 'health');
    }
  }

  /**
   * Map axios errors to appropriate Nest HTTP exceptions without leaking
   * internal details, while preserving client-facing validation messages
   * (HTTP 4xx) produced by the Python service.
   */
  private translateError(error: unknown, requestId: string): HttpException {
    const axiosErr = error as AxiosError<{ detail?: string }>;

    if (axiosErr.response) {
      const status = axiosErr.response.status;
      const detail = axiosErr.response.data?.detail ?? 'Inference service error.';
      this.logger.warn(
        `[${requestId}] inference service responded ${status}: ${detail}`,
      );
      // Surface client errors (bad image, low confidence, etc.) verbatim.
      if (status >= 400 && status < 500) {
        return new HttpException(detail, status);
      }
      return new InternalServerErrorException('Inference service failed.');
    }

    if (axiosErr.code === 'ECONNREFUSED' || axiosErr.code === 'ECONNABORTED') {
      this.logger.error(
        `[${requestId}] inference service unreachable: ${axiosErr.code}`,
      );
      return new ServiceUnavailableException(
        'Bone-age inference service is unavailable.',
      );
    }

    this.logger.error(`[${requestId}] unexpected inference error`, axiosErr.stack);
    return new InternalServerErrorException('Unexpected inference error.');
  }
}

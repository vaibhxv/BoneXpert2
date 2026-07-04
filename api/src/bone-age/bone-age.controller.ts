import { randomUUID } from 'node:crypto';

import {
  BadRequestException,
  Controller,
  Get,
  MaxFileSizeValidator,
  ParseFilePipe,
  Post,
  UploadedFile,
  UsePipes,
  ValidationPipe,
  Body,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { UseInterceptors } from '@nestjs/common';

import { BoneAgeService } from './bone-age.service';
import { PredictBoneAgeDto } from './dto/predict-bone-age.dto';

const MAX_UPLOAD_BYTES = 25 * 1024 * 1024; // 25 MB, mirrors the Python service.
const ALLOWED_MIME = /^(image\/(png|jpe?g|bmp|tiff)|application\/(dicom|octet-stream))$/i;

@Controller('bone-age')
export class BoneAgeController {
  constructor(private readonly boneAgeService: BoneAgeService) {}

  @Get('health')
  health() {
    return this.boneAgeService.health();
  }

  @Post('predict')
  @UseInterceptors(
    FileInterceptor('image', {
      limits: { fileSize: MAX_UPLOAD_BYTES, files: 1 },
    }),
  )
  @UsePipes(new ValidationPipe({ whitelist: true, transform: true }))
  async predict(
    @UploadedFile(
      new ParseFilePipe({
        validators: [new MaxFileSizeValidator({ maxSize: MAX_UPLOAD_BYTES })],
        fileIsRequired: true,
      }),
    )
    image: Express.Multer.File,
    @Body() dto: PredictBoneAgeDto,
  ) {
    if (!image?.buffer?.length) {
      throw new BadRequestException('An image file is required.');
    }
    if (image.mimetype && !ALLOWED_MIME.test(image.mimetype)) {
      throw new BadRequestException(`Unsupported file type: ${image.mimetype}`);
    }

    const requestId = randomUUID().replace(/-/g, '').slice(0, 12);
    return this.boneAgeService.predict(image, dto.sex, requestId);
  }
}

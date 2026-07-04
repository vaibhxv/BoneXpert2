import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { ConfigModule, ConfigService } from '@nestjs/config';

import { BoneAgeController } from './bone-age.controller';
import { BoneAgeService } from './bone-age.service';

@Module({
  imports: [
    ConfigModule,
    HttpModule.registerAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        timeout: config.get<number>('PYTHON_SERVICE_TIMEOUT_MS', 30000),
        maxRedirects: 0,
      }),
    }),
  ],
  controllers: [BoneAgeController],
  providers: [BoneAgeService],
  exports: [BoneAgeService],
})
export class BoneAgeModule {}

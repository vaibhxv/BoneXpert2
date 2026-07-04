import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // All API routes are served under /api; the root path serves the web UI.
  app.setGlobalPrefix('api');

  // CORS is only needed when the UI is hosted on a different origin than the
  // API. In the default single-origin deployment it is a no-op. Configure with
  // a comma-separated CORS_ORIGIN list.
  const corsOrigin = process.env.CORS_ORIGIN;
  if (corsOrigin) {
    app.enableCors({ origin: corsOrigin.split(',').map((s) => s.trim()) });
  }

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: true,
    }),
  );

  await app.listen(process.env.PORT ?? 3000);
}
bootstrap();

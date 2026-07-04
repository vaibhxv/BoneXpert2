import { join } from 'node:path';

import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ServeStaticModule } from '@nestjs/serve-static';

import { AppController } from './app.controller';
import { AppService } from './app.service';
import { BoneAgeModule } from './bone-age/bone-age.module';

// Path to the built web UI. Defaults to the sibling `web/dist` folder; override
// with WEB_DIST_PATH when deploying from a different layout.
const WEB_DIST =
  process.env.WEB_DIST_PATH ?? join(__dirname, '..', '..', 'web', 'dist');

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    // Serve the compiled single-page UI. API routes live under the global
    // `/api` prefix (set in main.ts) so they never collide with static assets.
    ServeStaticModule.forRoot({
      rootPath: WEB_DIST,
      exclude: ['/api/{*path}'],
    }),
    BoneAgeModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}

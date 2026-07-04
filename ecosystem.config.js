// PM2 process definitions for production (VPS) deployment.
//
// Two long-running processes:
//   1. bonexpert-engine — Python FastAPI inference service (:8000)
//   2. bonexpert-api     — NestJS gateway that ALSO serves the built web UI (:3000)
//
// The web UI is static and served by the NestJS process, so there is no third
// process to manage. Run with:  npx pm2 start ecosystem.config.js
const path = require('node:path');
const ROOT = __dirname;

module.exports = {
  apps: [
    {
      name: 'bonexpert-engine',
      cwd: path.join(ROOT, 'bone-age-ai'),
      script: '.venv/bin/python',
      args: '-m app.main',
      interpreter: 'none',
      autorestart: true,
      max_restarts: 10,
      env: {
        HOST: '127.0.0.1',
        PORT: '8000',
      },
    },
    {
      name: 'bonexpert-api',
      cwd: path.join(ROOT, 'api'),
      script: 'dist/main.js',
      autorestart: true,
      max_restarts: 10,
      env: {
        PORT: '3000',
        PYTHON_SERVICE_URL: 'http://127.0.0.1:8000',
        WEB_DIST_PATH: path.join(ROOT, 'web', 'dist'),
      },
    },
  ],
};

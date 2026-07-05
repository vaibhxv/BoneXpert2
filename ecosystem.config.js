// PM2 process definitions for production (VPS) deployment.
//
// Three long-running processes:
//   1. bonexpert-engine — Python FastAPI inference service (:8000)
//   2. bonexpert-api     — NestJS gateway that ALSO serves the built web UI (:3000)
//   3. bonexpert-ngrok   — ngrok HTTPS tunnel to the gateway (:3000)
//
// The web UI is static and served by the NestJS process, so ngrok only needs to
// forward to the gateway. Run with:  npx pm2 start ecosystem.config.js
const path = require('node:path');
const ROOT = __dirname;
const ngrokArgs = process.env.NGROK_URL
  ? `http --url=${process.env.NGROK_URL} 3000 --log=stdout`
  : 'http 3000 --log=stdout';

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
    {
      name: 'bonexpert-ngrok',
      cwd: ROOT,
      script: 'ngrok',
      args: ngrokArgs,
      interpreter: 'none',
      autorestart: true,
      max_restarts: 10,
    },
  ],
};

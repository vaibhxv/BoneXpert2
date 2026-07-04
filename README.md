# BoneXpert 2.0 — Offline Skeletal Bone-Age Platform

Estimate pediatric skeletal (bone) age from a hand radiograph — **fully offline**,
on your own hardware. Three cooperating apps in one repo:

| App | Path | Role | Port |
|-----|------|------|------|
| **Engine** | `bone-age-ai/` | Python / FastAPI AI inference (crop → histogram match → estimate) | `8000` |
| **API** | `api/` | NestJS gateway: uploads, validation, serves the UI | `3000` |
| **Web** | `web/` | React/Vite radiograph-viewer UI (bone/x-ray themed) | `5173` (dev) |

```
Browser ──▶ NestJS API (/api) ──▶ Python engine ──▶ crop + bone-age models
   ▲             │
   └── UI served by NestJS at /
```

In production a **single NestJS process serves both the UI and the API**, so a
VPS only runs two processes: the Python engine and the NestJS gateway.

---

## Quick start (single commands)

**Prerequisites:** Python 3.12, Node 18+ (Node 20+ recommended), `make`.

```bash
# 1. Install everything + download AI models (run once; needs internet)
make setup

# 2a. Develop with hot reload (engine + API + UI)
make dev            # UI at http://localhost:5173

# 2b. …or build + run production stack under pm2
make deploy         # UI + API at http://localhost:3000
```

That's it. `make setup` creates the Python venv, installs all Python + Node
deps, and downloads the models. After that the app is fully offline.

> Prefer raw scripts? `bash scripts/setup.sh` then `bash scripts/dev.sh`.

Run `make` (or `make help`) to see every target:

```
setup     Install ALL deps + download models (one command, run once)
models    (Re)download the AI models
dev       Run engine + API + web with hot reload
build     Build the web UI and the NestJS API for production
start     Build then start engine + API under pm2
deploy    Build + start + persist pm2 process list (for VPS)
stop      Stop pm2-managed processes
logs      Tail pm2 logs
test      Run Python engine unit tests
clean     Remove build artifacts and node_modules
```

---

## Deploy on a VPS

```bash
# On a fresh Ubuntu box:
sudo apt update && sudo apt install -y python3.12-venv nodejs npm make

git clone <your-repo> bonexpert && cd bonexpert

make setup          # deps + models (one time)
make deploy         # builds UI+API, starts pm2 (engine + gateway)

npx pm2 startup     # (optional) start pm2 on boot; follow printed instructions
```

Then put nginx in front for TLS using the provided sample:

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/bonexpert
# edit server_name, symlink into sites-enabled, then:
sudo certbot --nginx -d bonexpert.example.com
```

The Python engine binds to `127.0.0.1` in production (see `ecosystem.config.js`)
so it is never exposed publicly — only the NestJS gateway is reverse-proxied.

---

## Configuration

Each app reads its own `.env` (copy from the `.env.example` next to it).

**Engine** (`bone-age-ai/.env`): `DEVICE` (`auto`/`cpu`/`cuda`/`mps`),
`CROP_CONFIDENCE_THRESHOLD`, `MAX_UPLOAD_BYTES`, `MODEL_VERSION`.

**API** (`api/.env`):
- `PORT` — gateway port (default `3000`).
- `PYTHON_SERVICE_URL` — engine URL (default `http://localhost:8000`).
- `PYTHON_SERVICE_TIMEOUT_MS` — inference timeout (default `30000`).
- `WEB_DIST_PATH` — path to built UI (default `../web/dist`).
- `CORS_ORIGIN` — only needed if the UI is hosted on a different origin.

**Web** (`web/`): `VITE_API_URL` — override only if the API is not same-origin.

---

## Project layout

```
xray-mvp/
├── bone-age-ai/     Python FastAPI inference engine (see its own README)
├── api/             NestJS gateway (serves UI + /api)
├── web/             React/Vite UI (see its own README)
├── scripts/         setup.sh, dev.sh
├── deploy/          nginx.conf.example
├── ecosystem.config.js   pm2 process definitions
└── Makefile         single-command entry points
```

Detailed docs live in [`bone-age-ai/README.md`](bone-age-ai/README.md) and
[`web/README.md`](web/README.md).

---

## Troubleshooting

- **UI shows "Engine offline"** — the Python engine isn't up. `make logs` or run
  `cd bone-age-ai && ./.venv/bin/python -m app.main` to see errors.
- **First model load is slow** — the engine loads a 3-fold ensemble and warms it
  at startup; `/api/bone-age/health` reports `ready` once warm.
- **`make deploy` can't find pm2** — it uses `npx pm2`; ensure network access on
  first run, or `npm i -g pm2`.

> ⚠️ Research & demonstration only. Not a medical device; not approved for
> clinical use.

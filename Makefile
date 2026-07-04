## BoneXpert 2.0 — root task runner.
## Run `make` or `make help` to list targets.

SHELL := /bin/bash
PM2   := npx pm2

.DEFAULT_GOAL := help

.PHONY: help setup models dev build start stop restart logs deploy test clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install ALL deps + download models (one command, run once)
	bash scripts/setup.sh

models: ## (Re)download the AI models into bone-age-ai/models
	cd bone-age-ai && ./.venv/bin/python scripts/download_models.py

dev: ## Run engine + API + web with hot reload (Ctrl-C to stop)
	bash scripts/dev.sh

build: ## Build the web UI and the NestJS API for production
	cd web && npm run build
	cd api && npm run build

start: build ## Build then start engine + API under pm2 (serves UI too)
	$(PM2) start ecosystem.config.js

deploy: build ## Build + start + persist pm2 process list (for VPS)
	$(PM2) start ecosystem.config.js
	$(PM2) save
	@echo "Deployed. UI + API at http://<server>:3000  (front with nginx for TLS)."

stop: ## Stop pm2-managed processes
	$(PM2) stop ecosystem.config.js || true

restart: ## Restart pm2-managed processes
	$(PM2) restart ecosystem.config.js

logs: ## Tail pm2 logs
	$(PM2) logs

test: ## Run Python engine unit tests
	cd bone-age-ai && ./.venv/bin/python -m pytest

clean: ## Remove build artifacts and node_modules (keeps venv + models)
	rm -rf web/dist api/dist web/node_modules api/node_modules

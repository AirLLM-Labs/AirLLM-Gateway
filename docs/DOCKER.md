# Docker usage

This project now runs as a Docker-first stack. Use `docker compose up -d` from
the repository root to start the full app.

## Services

- `postgres` — Postgres 16 for metadata, API keys, request logs, and model registry.
- `backend` — FastAPI gateway that exposes `/v1/*`, `/health`, and `/admin/*`.
- `frontend` — Next.js dashboard that proxies admin traffic to `backend`.
- `coder-model` — llama.cpp server for code-focused models.
- `vision-model` — llama.cpp server for vision-capable models.
- `deepseek-model` — llama.cpp server for DeepSeek-Coder-V2-Lite.

## Startup

1. Copy `.env.example` to `.env`.
2. Edit `MODEL_DIR` and the model filenames.
3. Run:

```bash
docker compose up -d
```

## Environment configuration

All runtime configuration is defined in `.env`:

- `BACKEND_PORT` — backend host port.
- `FRONTEND_PORT` — dashboard host port.
- `POSTGRES_PORT` — Postgres host port.
- `CODER_PORT`, `VISION_PORT`, `DEEPSEEK_PORT` — model container ports.
- `MODEL_DIR` — host path containing model files.
- `CODER_MODEL_FILE`, `VISION_MODEL_FILE`, `VISION_MMPROJ_FILE`, `DEEPSEEK_MODEL_FILE`.
- `MODEL_DISCOVERY_ENABLED` / `MODEL_DISCOVERY_INTERVAL` — backend model discovery.
- `ADMIN_API_KEY` — shared admin token used by backend and dashboard.

## Override support

`docker-compose.override.yml` is merged automatically by Docker Compose.
Use it to add local mounts or alter ports without changing `docker-compose.yml`.

## Healthchecks

Every service includes a healthcheck:

- `postgres` — `pg_isready`
- `backend` — `GET /health`
- `frontend` — `GET /`
- `coder-model`, `vision-model`, `deepseek-model` — `GET /health`

## Model discovery

The backend now automatically probes configured model servers and registers
healthy upstreams in the model registry. This happens at startup and periodically
while the app is running.

## Troubleshooting

- If the dashboard cannot reach the backend, verify `BACKEND_PORT` and that the
  `backend` service is healthy.
- If model containers fail to start, ensure `MODEL_DIR` is correct and contains
  the configured `.gguf` files.
- If you only want the app stack without model containers, remove
  `COMPOSE_PROFILES=models` from `.env`.

## Migration steps

1. Copy `.env.example` to `.env`.
2. Update `MODEL_DIR` and the model filenames for your local machine.
3. Confirm the port values you want to expose in `.env`.
4. Run `docker compose up -d` from the repository root.
5. Verify service health with `docker compose ps` and `docker compose logs -f`.
6. If you need machine-specific changes, put them into `docker-compose.override.yml`.

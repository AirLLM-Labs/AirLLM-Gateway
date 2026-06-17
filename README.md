# AirLLM Gateway

> Self-hosted gateway that exposes your local **llama.cpp** servers through a
> single, authenticated, **OpenAI-compatible API** — with a dark, modern
> dashboard for models, keys, traffic and health.

**Phase 1** ships the core gateway: OpenAI-compatible `/v1` endpoints
(streaming + non-streaming), a model registry, hashed API keys, request logging,
health checks, and a Next.js dashboard. Existing OpenAI SDK clients work
unchanged — just point them at the gateway.

```python
from openai import OpenAI

client = OpenAI(api_key="sk-airllm_xxxxxxxx", base_url="http://localhost:4000/v1")
resp = client.chat.completions.create(
    model="coder",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(resp.choices[0].message.content)
```

---

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Quick start (Docker)](#quick-start-docker)
- [Using your existing llama.cpp servers](#using-your-existing-llamacpp-servers)
- [Local development (without Docker)](#local-development-without-docker)
- [Connecting OpenAI SDK clients](#connecting-openai-sdk-clients)
- [Project structure](#project-structure)
- [Configuration](#configuration)
- [Testing](#testing)

---

## Features

- **OpenAI-compatible API** — `GET /v1/models`, `POST /v1/chat/completions`
  (streaming SSE **and** non-streaming).
- **llama.cpp connector** — forwards to one or more upstream servers and proxies
  their OpenAI-style responses verbatim.
- **Model registry** — CRUD over models (`name`, `provider`, `endpoint_url`,
  `enabled`, `capabilities`).
- **API keys** — `sk-airllm_…` format, **stored hashed only**, shown once at
  creation; protect every `/v1` endpoint. Enable/disable and last-used tracking.
- **Dashboard** — active models, key count, requests, **token usage**, version &
  uptime, health; model & key management; latest requests. Dark theme inspired by
  OpenAI Platform / Vercel.
- **Client Setup wizard** — copy-paste configs for VS Code, Continue.dev, the
  OpenAI SDK (Python/Node) and curl. No Swagger required.
- **Usage analytics** — requests/day, tokens/day and per-model charts.
- **Request logging** — endpoint, model, latency, status, **token counts**.
- **Health checks** — `GET /health` reports database + every registered upstream;
  surfaced per-model in the dashboard, auto-refreshing.
- **One-click start** — `scripts/Start-AirLLM.bat` (Windows) / `start-airllm.sh`
  (Linux/macOS) bring up Postgres, the gateway and the dashboard, then open your
  browser. Idempotent: re-running reuses healthy services instead of spawning
  duplicates; `--restart` forces fresh instances.

## Tech stack

**Backend:** Python 3.11 · FastAPI · Uvicorn · SQLAlchemy (async) · Alembic ·
PostgreSQL · Pydantic · httpx
**Frontend:** Next.js (App Router) · TypeScript · Tailwind CSS · shadcn/ui ·
React Query · Zustand
**Container:** Docker · docker-compose

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full picture and
[`docs/API.md`](docs/API.md) for the API reference. In short:

```
OpenAI SDK ─► Gateway (FastAPI, :4000) ─► llama.cpp servers (:8080, :8081, …)
                  │  registry · keys · logs in PostgreSQL
Dashboard (Next.js, :3000) ─► /api/proxy/* ─► Gateway   (admin token kept server-side)
```

---

## Quick start (Docker)

**Prerequisites:** Docker + Docker Compose, and your llama.cpp `server`
instances running on the host (see next section).

```bash
# 1. Configure
cp .env.example .env
#   → edit .env and set a strong ADMIN_API_KEY

# 2. Build & run (Postgres + backend + dashboard).
#    Migrations run automatically on backend startup.
docker compose up --build
```

| Service     | URL                            |
| ----------- | ------------------------------ |
| Dashboard   | http://localhost:3000          |
| Gateway API | http://localhost:4000          |
| API docs    | http://localhost:4000/docs     |
| Health      | http://localhost:4000/health   |

Then, in the dashboard:

1. **Models → Add model** — register each llama.cpp server (see below).
2. **API Keys → Create key** — copy the `sk-airllm_…` key (shown once).
3. Point your OpenAI client at `http://localhost:4000/v1` using that key.

## Using your existing llama.cpp servers

Phase 1 connects to llama.cpp `server` instances you already run. Typical setup:

```bash
# Coder model on :8080
./llama-server -m qwen2.5-coder-7b-instruct-q4_k_m.gguf --host 0.0.0.0 --port 8080

# Vision model on :8081
./llama-server -m llava-v1.6-mistral-7b.Q4_K_M.gguf --mmproj mmproj-model-f16.gguf \
  --host 0.0.0.0 --port 8081
```

Register them in **Models → Add model** (or via the admin API):

| Field         | Coder example                       | Vision example                      |
| ------------- | ----------------------------------- | ----------------------------------- |
| Model id      | `coder`                             | `vision`                            |
| Endpoint URL  | `http://127.0.0.1:8080`             | `http://127.0.0.1:8081`             |
| Capabilities  | `chat`                              | `vision`                            |

> **Running the gateway in Docker?** Containers can't see the host as
> `127.0.0.1`. Use `http://host.docker.internal:8080` / `:8081` for the endpoint
> URLs instead. (Compose already maps `host.docker.internal` on Linux.)

Prefer to run llama.cpp in Docker too? See
[`docker/llamacpp.example.yml`](docker/llamacpp.example.yml).

---

## One-click start (local, without Docker Compose)

After a one-time setup (Python venv + `npm install`, see below), launch the whole
stack — Postgres (Docker), gateway and dashboard — with a single script that also
opens your browser:

```bat
REM Windows
scripts\Start-AirLLM.bat
```

```bash
# Linux / macOS
./scripts/start-airllm.sh
```

Both scripts share one `ADMIN_API_KEY` across the backend and dashboard so they
agree out of the box (override by exporting `ADMIN_API_KEY` first).

### Idempotent & non-destructive

The launcher is **safe to run repeatedly** — it never creates duplicate backend
or dashboard processes, so you'll no longer hit
`[Errno 10048] only one usage of each socket address is normally permitted`:

- **Backend** — before starting, it probes `127.0.0.1:4000/health`. If a healthy
  AirLLM backend already answers there it is reused and you'll see
  `[AirLLM] Backend already running on port 4000.` If `:4000` is held by some
  other (non-AirLLM) process, the launcher **skips** starting rather than
  crashing, and warns you.
- **Dashboard** — if `:3000` is already serving, it prints
  `[AirLLM] Dashboard already running on port 3000.` and does not launch a second
  instance.
- **Nothing is killed automatically.** Healthy services are reused.
- The browser only opens when a service was actually (re)started.

Each run finishes with a status banner:

```
====================================
 AirLLM Startup Status
====================================
Backend   : Running (port 4000)
Dashboard : Running (port 3000)
Database  : Connected
====================================
```

### Restarting

To force fresh instances, pass `--restart`. This stops **only AirLLM-owned**
backend/dashboard processes (Postgres is left running) and then starts them
again:

```bat
REM Windows
scripts\Start-AirLLM.bat --restart
```

```bash
# Linux / macOS
./scripts/start-airllm.sh --restart
```

### Stopping

Stop with `scripts\Stop-AirLLM.bat` / `./scripts/stop-airllm.sh`. These only
touch AirLLM-owned processes — on Windows the backend/dashboard are matched by
their window titles (`AirLLM Backend` / `AirLLM Dashboard`), never by port, so an
unrelated service that happens to use `:4000`/`:3000` is left alone. Add
`--services-only` to stop the backend and dashboard but keep the Postgres
container running.

## Local development (without Docker)

Run Postgres however you like (a container is easiest):

```bash
docker run --name airllm-pg -e POSTGRES_USER=airllm -e POSTGRES_PASSWORD=airllm \
  -e POSTGRES_DB=airllm -p 5432:5432 -d postgres:16-alpine
```

### Backend

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows (Git Bash)
#                                  source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env                # adjust DATABASE_URL / ADMIN_API_KEY

alembic upgrade head                # create tables
uvicorn app.main:app --reload --port 4000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local          # BACKEND_INTERNAL_URL + ADMIN_API_KEY
npm run dev                         # http://localhost:3000
```

> Keep `ADMIN_API_KEY` identical in `backend/.env` and `frontend/.env.local`.

---

## Connecting OpenAI SDK clients

**Python**

```python
from openai import OpenAI
client = OpenAI(api_key="sk-airllm_xxxxxxxx", base_url="http://localhost:4000/v1")

# Streaming
for chunk in client.chat.completions.create(
    model="coder",
    messages=[{"role": "user", "content": "Stream a limerick."}],
    stream=True,
):
    print(chunk.choices[0].delta.content or "", end="")
```

**Node.js**

```ts
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: "sk-airllm_xxxxxxxx",
  baseURL: "http://localhost:4000/v1",
});

const res = await client.chat.completions.create({
  model: "coder",
  messages: [{ role: "user", content: "Hello!" }],
});
console.log(res.choices[0].message.content);
```

**curl**

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-airllm_xxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"coder","messages":[{"role":"user","content":"hi"}]}'
```

---

## Project structure

```
AirLLM-Gateway/
├── backend/                     # FastAPI gateway
│   ├── app/
│   │   ├── api/                 # routing: v1/, admin/, health, deps
│   │   ├── core/                # config, logging, security
│   │   ├── db/                  # async engine + session, declarative base
│   │   ├── models/              # SQLAlchemy: Model, ApiKey, RequestLog
│   │   ├── schemas/             # Pydantic (OpenAI shapes + admin DTOs)
│   │   ├── services/            # llama.cpp connector, registries, health, logs
│   │   ├── middleware/          # request logging
│   │   └── main.py              # app factory + ASGI entrypoint
│   ├── migrations/              # Alembic env + versions/0001_initial.py
│   ├── tests/                   # pytest (async, in-memory SQLite)
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # Next.js dashboard
│   ├── app/                     # App Router: /, /models, /api-keys, /usage,
│   │   │                        #             /setup, api/proxy
│   ├── components/              # ui/ (shadcn) + feature components (setup/, usage/)
│   ├── hooks/                   # React Query hooks
│   ├── lib/                     # api client, types, utils
│   ├── store/                   # Zustand UI state
│   └── Dockerfile
├── scripts/                     # One-click start/stop launchers (bat + sh)
├── docker/                      # compose notes + optional llama.cpp override
├── docs/                        # ARCHITECTURE.md, API.md, V2_UPGRADE_PLAN.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## Configuration

Root `.env` (compose) — see [`.env.example`](.env.example):

| Variable            | Default               | Purpose                              |
| ------------------- | --------------------- | ------------------------------------ |
| `POSTGRES_USER/PASSWORD/DB` | `airllm`      | Database credentials.                |
| `ADMIN_API_KEY`     | `changeme-admin-key`  | Protects `/admin` + dashboard proxy. |
| `CORS_ORIGINS`      | `http://localhost:3000` | Allowed dashboard origin(s).       |
| `DEBUG` / `LOG_LEVEL` | `false` / `INFO`    | Logging verbosity.                   |

Backend-only ([`backend/.env.example`](backend/.env.example)) also exposes
`DATABASE_URL`, `UPSTREAM_TIMEOUT`, `HEALTH_TIMEOUT`.
Frontend-only ([`frontend/.env.example`](frontend/.env.example)) exposes
`BACKEND_INTERNAL_URL` and `ADMIN_API_KEY`.

> **Security:** always set a long, random `ADMIN_API_KEY` outside local dev.

## Testing

```bash
cd backend
pip install -r requirements.txt
pytest                 # async suite runs against in-memory SQLite (no Postgres needed)
```

Covers API-key hashing, admin model CRUD, key creation/auth/revocation, health,
and the chat proxy (streaming + non-streaming, with a mocked upstream).

# Architecture (Phase 1)

AirLLM Gateway is a self-hosted reverse proxy that exposes one or more local
[llama.cpp](https://github.com/ggml-org/llama.cpp) `server` instances behind a
single, authenticated, OpenAI-compatible API — plus a dashboard to manage it.

```
                       ┌──────────────────────────────┐
   OpenAI SDK ───────► │  AirLLM Gateway (FastAPI)    │
   (Python / Node)     │                              │
   Authorization:      │  /v1/models                  │      ┌────────────────┐
   Bearer sk-airllm_…  │  /v1/chat/completions ───────┼────► │ llama.cpp :8080│  (coder)
                       │                              │      └────────────────┘
                       │  /admin/*  (X-Admin-Token)   │      ┌────────────────┐
                       │  /health                     │────► │ llama.cpp :8081│  (vision)
                       └───────────┬──────────────────┘      └────────────────┘
                                   │
   Dashboard (Next.js) ────────────┘   request logs · model registry · API keys
   /api/proxy/*  ──► backend             stored in PostgreSQL
   (injects X-Admin-Token server-side)
```

## Request flow: `POST /v1/chat/completions`

1. **Auth** — `require_api_key` extracts the bearer token, hashes it (SHA-256)
   and looks up an enabled `ApiKey`. Unknown/disabled → `401`.
2. **Routing** — the request `model` is resolved against the **model registry**
   (`resolve_enabled`). Unknown/disabled model → `404` (OpenAI error shape).
3. **Forwarding** — `LlamaCppConnector` forwards the (extra-field-preserving)
   payload to that model's `endpoint_url`.
   - *Non-streaming*: upstream JSON is returned as-is.
   - *Streaming*: upstream SSE bytes are proxied through unchanged (llama.cpp
     already emits OpenAI-style `data: …` / `data: [DONE]` frames). The stream
     is "primed" (first chunk awaited) so connection failures surface as a clean
     JSON error rather than a half-open stream.
4. **Logging** — `RequestLoggingMiddleware` records endpoint, model, latency,
   status and **token usage** to `request_logs` (on its own DB session, never
   blocking the request).
   - *Non-streaming*: usage is read from the upstream response body and stashed
     on `request.state` for the middleware to persist.
   - *Streaming*: the middleware finishes before the body streams, so the
     streaming path opts into `stream_options.include_usage`, sniffs the trailing
     usage frame, and writes its own log row when the stream drains (setting
     `request.state.skip_request_log` so the middleware doesn't double-log). This
     also yields accurate end-to-end stream latency.

## Layout (backend)

| Layer        | Responsibility                                              |
| ------------ | ----------------------------------------------------------- |
| `api/`       | HTTP routing + dependencies (`v1`, `admin`, `health`).      |
| `schemas/`   | Pydantic request/response models (incl. OpenAI shapes).     |
| `services/`  | Business logic: connector, registries, logging, health.     |
| `models/`    | SQLAlchemy ORM tables.                                       |
| `db/`        | Async engine + session.                                     |
| `core/`      | Config, logging, security (key gen/hash).                   |
| `middleware/`| Cross-cutting request logging.                              |

## Docker service architecture

The project now runs as a Docker-first stack.

```
      +------------+      +---------------+      +---------------+
      |   frontend |<---->|    backend    |<---->|   postgres    |
      +------------+      +---------------+      +---------------+
                                 ^   ^   ^
                                 |   |   |
            +--------------------+   |   +--------------------+
            |                        |                        |
    +----------------+    +----------------+    +----------------+
    |   coder-model  |    |  vision-model  |    | deepseek-model |
    +----------------+    +----------------+    +----------------+
```

- `frontend` — Next.js dashboard, server-side proxies requests to `backend`.
- `backend` — FastAPI gateway, auto-discovers healthy llama.cpp model servers.
- `postgres` — persistent metadata storage for API keys, request logs, model registry.
- `coder-model` / `vision-model` / `deepseek-model` — GPU llama.cpp servers with
  model paths driven by `MODEL_DIR` and filenames from `.env`.

The root `docker-compose.yml` defines all ports and model paths in `.env`
(`BACKEND_PORT`, `FRONTEND_PORT`, `CODER_PORT`, `VISION_PORT`, `DEEPSEEK_PORT`,
`MODEL_DIR`), and uses `docker-compose.override.yml` for local machine-specific
customizations.

## Key decisions

- **Async end-to-end.** The gateway is I/O-bound (it mostly waits on upstreams),
  so the app uses async SQLAlchemy (asyncpg) + `httpx.AsyncClient`. A single
  pooled HTTP client is shared across requests. Alembic runs synchronously
  (psycopg2) since migrations don't benefit from async.
- **llama.cpp is already OpenAI-compatible**, so the connector is a thin proxy
  rather than a translation layer — fewer places to drift from the spec.
- **Keys are stored hashed only.** Plaintext is shown once at creation. A short
  non-sensitive `preview` is stored for display.
- **Admin auth is a single shared token** (`ADMIN_API_KEY`). Phase 1 has no user
  accounts by design. The dashboard keeps this token server-side via a BFF proxy
  (`/api/proxy/*`), so the browser never sees it and there is no CORS surface.

## Data model

- **models** — `id, name (unique), provider, endpoint_url, enabled,
  capabilities (JSON), created_at`
- **api_keys** — `id, name, hashed_key (unique), preview, enabled, created_at,
  last_used_at`
- **request_logs** — `id, endpoint, model_used, latency_ms, status_code,
  prompt_tokens, completion_tokens, total_tokens, created_at`

Migrations: `0001_initial` → `0002_request_log_tokens` → `0003_api_key_last_used`
(all additive / nullable, so rollouts and rollbacks are safe).

## Explicitly out of scope (later phases)

Anthropic compatibility · capability-based vision routing · fallback chains ·
user accounts · billing · multi-machine clustering · single-origin serving on
`:4000` (see [`V2_UPGRADE_PLAN.md`](V2_UPGRADE_PLAN.md) Phase 8).

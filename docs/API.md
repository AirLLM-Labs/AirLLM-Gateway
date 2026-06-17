# API Reference (Phase 1)

Base URL (default): `http://localhost:4000`

Interactive docs (Swagger UI) are served at `/docs`.

---

## Authentication

| Endpoint group | Auth                                                     |
| -------------- | -------------------------------------------------------- |
| `/v1/*`        | `Authorization: Bearer sk-airllm_…` (a gateway API key)  |
| `/admin/*`     | `X-Admin-Token: <ADMIN_API_KEY>` (or `Authorization: Bearer <ADMIN_API_KEY>`) |
| `/health`, `/` | none                                                     |

---

## OpenAI-compatible endpoints

### `GET /v1/models`

Returns enabled registry models in OpenAI list form.

```json
{
  "object": "list",
  "data": [
    { "id": "coder", "object": "model", "created": 1718409600, "owned_by": "llamacpp" }
  ]
}
```

### `POST /v1/chat/completions`

Standard OpenAI chat-completions request. `stream: true` returns
`text/event-stream` SSE; otherwise a JSON body. Unknown sampling parameters are
forwarded to llama.cpp untouched.

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-airllm_xxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "coder",
    "messages": [{"role": "user", "content": "Write a haiku about caches."}]
  }'
```

Errors use the OpenAI shape:

```json
{ "error": { "message": "The model 'foo' does not exist or is not enabled.", "type": "model_not_found", "code": 404 } }
```

---

## Admin — Models

| Method   | Path                  | Body                                              |
| -------- | --------------------- | ------------------------------------------------- |
| `GET`    | `/admin/models`       | —                                                 |
| `POST`   | `/admin/models`       | `{ name, endpoint_url, provider?, enabled?, capabilities? }` |
| `PUT`    | `/admin/models/{id}`  | partial of the above                              |
| `DELETE` | `/admin/models/{id}`  | —                                                 |

```bash
curl -X POST http://localhost:4000/admin/models \
  -H "X-Admin-Token: changeme-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"name":"coder","endpoint_url":"http://127.0.0.1:8080","capabilities":["chat"]}'
```

## Admin — API Keys

| Method   | Path                    | Notes                                                  |
| -------- | ----------------------- | ------------------------------------------------------ |
| `GET`    | `/admin/api-keys`       | Never returns plaintext. Includes `last_used_at`.       |
| `POST`   | `/admin/api-keys`       | `{ name }` → returns `key` **once**.                    |
| `PATCH`  | `/admin/api-keys/{id}`  | `{ enabled?, name? }` — enable/disable or rename a key.  |
| `DELETE` | `/admin/api-keys/{id}`  | Revokes the key.                                        |

A disabled key (`enabled: false`) is rejected at `/v1` with `401`. Each
successful authentication stamps `last_used_at`.

## Admin — Observability

| Method | Path                    | Notes                                                   |
| ------ | ----------------------- | ------------------------------------------------------- |
| `GET`  | `/admin/logs?limit=50`  | Recent request logs (newest first), incl. token counts. |
| `GET`  | `/admin/stats`          | Dashboard counters incl. `version`, `uptime_seconds`, `total_tokens`, `tokens_last_24h`. |
| `GET`  | `/admin/usage?days=7`   | Time-series + per-model rollups for the Usage page.     |

```jsonc
// GET /admin/usage?days=7
{
  "days": 7,
  "requests_this_week": 254,
  "tokens_this_week": 1245302,
  "daily": [ { "day": "2026-06-16", "requests": 30, "tokens": 145000 } ],
  "per_model": [ { "model": "coder", "requests": 200, "tokens": 980000, "avg_latency_ms": 9.1 } ]
}
```

Request logs now carry `prompt_tokens` / `completion_tokens` / `total_tokens`
(nullable — captured from the upstream `usage` block; streaming opts into
`stream_options.include_usage`).

---

## `GET /health`

```json
{
  "status": "ok",
  "database": "ok",
  "upstreams": [
    { "id": 1, "name": "coder", "endpoint_url": "http://127.0.0.1:8080",
      "status": "ok", "latency_ms": 3.1, "detail": null }
  ]
}
```

`status` is `ok` (all good), `degraded` (DB up, an upstream down or none
registered) or `down` (DB unreachable → HTTP 503).

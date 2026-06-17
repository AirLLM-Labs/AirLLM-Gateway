# Docker assets

The production images live next to their code:

| Image      | Dockerfile          | Port |
| ---------- | ------------------- | ---- |
| Backend    | `../backend/Dockerfile`  | 4000 |
| Dashboard  | `../frontend/Dockerfile` | 3000 |
| Postgres   | `postgres:16-alpine` (pulled) | 5432 |

They are orchestrated by the root [`../docker-compose.yml`](../docker-compose.yml).

## Reaching your llama.cpp servers

Phase 1 assumes you already run your llama.cpp `server` binaries on the host
(e.g. `127.0.0.1:8080` and `127.0.0.1:8081`). From inside the containers, refer
to the host as **`host.docker.internal`** instead of `127.0.0.1`:

```
http://host.docker.internal:8080
http://host.docker.internal:8081
```

The compose file already maps `host.docker.internal` on Linux via
`extra_hosts: host-gateway`.

## Optional: run llama.cpp in Docker too

If you'd rather run llama.cpp in containers, see
[`llamacpp.example.yml`](./llamacpp.example.yml) for a starting point and merge
it in with:

```bash
docker compose -f docker-compose.yml -f docker/llamacpp.example.yml up
```

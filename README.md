# Lighthouse Media Manager (LHMM)

## About
LighthouseMM is a modern media manager that utilizes Plex-like libraries to help keep your media organized. 

## Layout (in-container)
```
/lhmm/app/backend  (FastAPI)
/lhmm/app/frontend (React build or dev server bind mount)
/lhmm/media        (bind mount from host)
/lhmm/config       (bind mount; SQLite at `/lhmm/config/db/lhmm.sqlite3`; caches under `/lhmm/config/cache`)
/lhmm/logs         (bind mount; rotating logs)
```

## Quickstart
- `cp .env.example .env` and update `MEDIA_HOST_PATH` to your media folder
- Install Vite React TS in ./web (see below)
- `docker compose -f docker-compose.dev.yml up --build`

### Dev Links
- **API**: http://localhost:8080/api/v1/healthz
- **Web**: http://localhost:5173
- **DB Pragma**: http://localhost:8080/api/v1/db/pragma
- **DB Ping**: http://localhost:8080/api/v1/db/ping

## Database & migrations
- SQLite DB: `/lhmm/config/db/lhmm.sqlite3` (WAL enabled; foreign keys enforced per-connection)
- Apply latest migrations (inside container):

```bash
docker compose -f docker-compose.dev.yml exec -T server bash -lc 'alembic upgrade head'
```

- Create a new migration and upgrade:

```bash
docker compose -f docker-compose.dev.yml exec -T server bash -lc 'alembic revision -m "schema change" --autogenerate && alembic upgrade head'
```

- Check runtime PRAGMAs via the app:

```bash
curl -s http://localhost:8080/api/v1/db/pragma
```

## Create the React app
```
#From repo root:
docker run --rm -it -v "$PWD/web":/app -w /app node:20 sh -lc "npm create vite@latest . -- --template react-ts && npm i"
#or locally:
npm create vite@latest web -- --template react-ts && cd web && npm i
```

## Notes
- App lives under `/lhmm` inside the container.
- SQLite DB path: `/lhmm/config/db/lhmm.sqlite3`
- Cache path: `/lhmm/config/cache`
- Logs: `/lhmm/logs`
- Media root: `/lhmm/media`

## Dev over Cloudflare Tunnel (no ports, real HTTPS)
Use a Cloudflare Tunnel sidecar to expose the dev UI/API on your real domains without opening ports.

**Setup**
1. In Cloudflare → Zero Trust → Access → Tunnels → Create Tunnel. Copy the token.
2. Add to `.env`:
   ```
   DEV_DOMAIN=lhmm.dev
   API_DEV_DOMAIN=api.lhmm.dev
   CLOUDFLARE_TUNNEL_TOKEN=...token...
   LHMM__CORS__ALLOWED_ORIGINS='["https://lhmm.dev"]'
   ```
3. In the Tunnel Public Hostnames, add:
   - `lhmm.dev` → HTTP → `web:5173`
   - `api.lhmm.dev` → HTTP → `server:8080`
4. Start:
   ```
   docker compose -f docker-compose.dev.yml up -d
   ```
5. Test:
   - https://lhmm.dev
   - https://api.lhmm.dev/api/v1/healthz
   - https://api.lhmm.dev/api/v1/tmdb/search?q=dune

Notes:
- Vite HMR uses WSS via `DEV_DOMAIN` (no port URLs).
- Backend CORS is controlled via config/env (`LHMM__CORS__ALLOWED_ORIGINS`).


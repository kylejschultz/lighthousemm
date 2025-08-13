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


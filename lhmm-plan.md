# Lighthouse Media Manager (LHMM) — End‑to‑End Build Plan (Docker‑first)

**Stack**: FastAPI (Python 3.11), SQLite (WAL), SQLAlchemy 2.0 + Alembic, APScheduler (AsyncIO), httpx, Pydantic v2, TMDB API, Vite + React + TypeScript, TanStack Query, React Router, Tailwind (or CSS Modules), Zod, Docker (single container), GitHub Actions → GHCR.

**Conventions**: Monorepo (backend `server/`, frontend `web/`, shared `packages/` optional). API base path **`/api/v1`**. **Container layout**: `/lhmm/app/backend` (API, DB access, jobs), `/lhmm/app/frontend` (built static UI). **Bind mounts**: `/lhmm/media/<drive-name>`, `/lhmm/config` (includes SQLite DB under `/lhmm/config/db/` and caches), `/lhmm/logs`. Local JSON‑structured logs with local timestamps + rotating files (default 10MB, keep 5). Optional basic‑auth (single admin user) via config flag. Unified Search hits **local + TMDB only** (indexers are used only during download flows).

```
/lhmm/
  app/
    frontend/   # React build output (prod) or bind mount (dev)
    backend/    # FastAPI app code
  media/        # bind-mounted media roots
  config/       # bind-mounted app config, DB at config/db/lhmm.sqlite3, caches
  logs/         # bind-mounted rotating logs
```

**Implementation order**: UI shell → standards/contracts → **Git workflow & release policy (early)** → logging & config → DB/domain → API → **Libraries** → **Unified Search** → Indexers → SAB → Scanner/Ingest → Post‑processing/Renamer → Quality/Upgrade → Jobs/Observability → Setup Wizard → Tests → Docker production image → CI/CD → Requests → Auth hardening → Future.

---

## 0) Docker‑first repo bootstrap & logging baseline
**Goal**: Start in Docker so bind mounts and build flow are proven on day one. Logging wired immediately.

**Deliverables**
- `docker-compose.dev.yml` with two services: `server` (FastAPI, hot‑reload) and `web` (Vite dev server), both mounting the repo and mapping volumes for `/lhmm/media`, `/lhmm/config`, `/lhmm/logs`.
- `server/` FastAPI skeleton calling a logging setup that writes JSON logs to `/lhmm/logs/lhmm.log` (rotate at 10MB × 5) and pretty logs to console; timestamps in local time.
- `web/` Vite React TS skeleton with sidebar shell + dark theme tokens.
- `docs/ADR-0001-architecture.md` capturing Docker‑first dev decision.

**Notes/Tech**
- SQLite in WAL mode; DB file under `/lhmm/config/db/lhmm.sqlite3`.
- Compose profiles: `dev` (hot reload) and later `prod` (single container).

**Warp prompt**
Create monorepo `lhmm/` with `server/` (FastAPI) and `web/` (Vite React TS). Add docker‑compose for dev with two services, bind‑mount repo, map `/lhmm/media`, `/lhmm/config`, `/lhmm/logs`. Implement logging config that rotates at 10MB (5 backups) with local timestamps. Confirm both services start cleanly in Docker and can talk over `http://server:8080`.

---

## 1) Standards & API contracts
**Goal**: Lock IDs, timestamps, error envelope, pagination/sorting, versioned routes.

**Deliverables**
- `docs/STANDARDS.md` (IDs = ULIDs; `created_at/updated_at` ISO 8601 with local offset; errors `{error:{code,message,details}}`).
- Shared Pydantic models `ErrorResponse`, `Page[T]`.
- Health/status endpoints at `/api/v1/healthz` and `/api/v1/status`.

**Warp prompt**
Add `/api/v1/healthz` and `/api/v1/status` endpoints, define `ErrorResponse` and generic `Page[T]` schemas, and enable CORS for `http://localhost:5173`.

## 1.5) Git workflow & release policy (early)
**Goal**: Establish branching, PR, and release/tagging rules now so we can commit with confidence from day one. Full automation remains in step 17.

**Deliverables**
- `docs/CI-CD.md` with: protected `main`, feature branches `feat/*`, `fix/*`, `chore/*`; PRs required with status checks; Conventional Commits; SemVer releases via annotated tags `vMAJOR.MINOR.PATCH`; `edge` images from `main` (later in step 17).
- `.github/PULL_REQUEST_TEMPLATE.md` and `.github/ISSUE_TEMPLATE/bug_report.md`, `feature_request.md`.
- Branch protection notes (who can push, required reviews) captured in docs.

**Warp prompt**
Document the Git workflow and release policy in `docs/CI-CD.md` (protected `main`, feature branches, Conventional Commits, SemVer tags). Add PR/issue templates. Do **not** add build workflows yet; those come in step 17.

---

## 2) Config system (YAML + schema)
**Goal**: Central config with validation and env overrides.

**Deliverables**
- `config/default.yml` with sections: `logging`, `db`, `paths`, `scheduler`, `tmdb`, `sabnzbd`, `indexers`, `auth`.
- Pydantic settings loader that merges YAML + env and validates.
- `docs/CONFIG.md` and a `config-check` CLI.

**Warp prompt**
Implement `Settings` that loads YAML + env overrides. Keys: logging {file,max_bytes,backups,level,timezone}, db {url sqlite path, wal:true}, paths {media_root:/lhmm/media}, scheduler {enabled:true}, tmdb {api_key}, sabnzbd {url,api_key}, indexers:[], auth {basic:{enabled:false,username,password}}.

---

## 2.5) TMDB client & metadata wiring (early)
**Goal**: TMDB API integration and caching.

**Deliverables**
- TMDB client service using API key from config.
- Local cache file at `/lhmm/config/cache/tmdb.json` with expiry.
- Metadata fetching for movies and TV shows.

**Warp prompt**
Build TMDB client reading API key from settings, caching responses in `/lhmm/config/cache/tmdb.json`. Provide methods to fetch movie and TV metadata.

---

## 3) Domain & database schema
**Goal**: Normalized model for disks, libraries, items, files, images, and jobs.

**Deliverables**
- SQLAlchemy models + Alembic migration.
- Entities: `Disk`, `Library`, `MediaItem`, `MediaFile`, `Job`, `Indexer` with sensible indexes.

**Warp prompt**
Create the models above, enforce foreign keys, add indexes, and generate an initial Alembic migration. Enable SQLite WAL on connect and place the DB under `/lhmm/config/db/`.

---

## 4) API v1 scaffold
**Goal**: CRUD/list for disks and libraries; middleware (request IDs, structured request logs).

**Deliverables**
- Routers: `/api/v1/disks`, `/api/v1/libraries` with pagination/sorting.
- Optional basic‑auth for admin endpoints via config flag.

**Warp prompt**
Implement CRUD for `/disks` and `/libraries`. Validate that library paths live under the selected Disk mount. Add request‑id middleware and structured access logging.

---

## 5) UI shell (homepage, sidebar, settings)
**Goal**: Core React UI with persistent layout and settings forms wired to the API.

**Deliverables**
- Sidebar links: Home, Libraries, Search, Downloads, Settings.
- Settings forms: TMDB key, SAB settings, logging level/file size, auth basic toggle.
- Scaffold pages (routes only at this step): **Libraries (list)**, **Library detail** (grid), **Movie detail**, **Series detail** (seasons & episodes scaffold), **Downloads**, **Indexers**. These will wire up real data in later steps.

**Warp prompt**
Scaffold routes and pages, add TanStack Query client, implement Settings page bound to `/api/v1/settings` GET/PUT with Zod validation and toast errors.

---

## 6) Library management (multi‑disk)
**Goal**: CRUD libraries with friendly disk names and per‑library settings.

**Deliverables**
- Library editor UI with disk selector; server validation of path and uniqueness.
- Per‑library SAB category mapping and profile.
- Libraries **list** page showing all libraries with counts (placeholder until scanner lands).
- **Library detail** page showing current items grid (initially empty/placeholder, populated after scanning).

**Warp prompt**
Build library forms (name,type,disk,root_subdir,sab_category,profile). Enforce a path constraint: must be within the chosen Disk mount.

---

## 7) Unified Search (local + TMDB)
**Goal**: Search across LHMM catalog and TMDB; no indexers here.

**Deliverables**
- `/api/v1/search?q=` returning `{local:[...], tmdb:{movies:[...], tv:[...]}}` plus minimal type metadata to disambiguate items.
- Search UI with grouped results; **Movie detail** and **Series detail** pages show both local state (in‑library files, quality) and TMDB metadata (cast, overview). From detail pages: actions to **Add to Library** (future) and **Request** (future).
- Deep links from search → detail pages → (later) download flow.

**Warp prompt**
Implement TMDB client (reads api key from settings) and local search against `MediaItem`. Merge results, add detail links, exclude indexer queries.

---

## 8) Indexer manager (Newznab family)
**Goal**: Configure multiple indexers and probe capabilities/categories.

**Deliverables**
- `/api/v1/indexers` CRUD and a `probe` action that stores caps/category IDs.
- Indexers UI with status and last‑probe.

**Warp prompt**
Create indexer model + probe endpoint that discovers and persists categories (movie,tv,anime). Show status and errors in UI.

---

## 9) SABnzbd integration
**Goal**: Add to queue, poll queue/history, map categories per library.

**Deliverables**
- `/api/v1/downloads/add` to send NZB url/name to SAB with category.
- Poller job to sync queue + history into the DB; Downloads UI.

**Warp prompt**
Implement SAB client (url,api_key). Endpoints: add via URL, get queue, get history. Poll every 30s when enabled. Use the library’s SAB category.

---

## 10) Scanner & ingest pipeline
**Goal**: Walk files, parse names, match to TMDB, upsert items/files, cache images.

**Deliverables**
- Idempotent per‑library scanner. Filename parser for movies and SxxEyy/daily/anime patterns.
- Image cache under `/lhmm/config/cache/images/`. Rescan action + job page.

**Warp prompt**
Build scanner service: traverse library root, infer candidates, verify with TMDB, upsert MediaItem/MediaFile, cache poster/backdrop. Expose `/api/v1/libraries/{id}/scan`.

---

## 11) Post‑processing & renaming
**Goal**: On completed downloads, move/rename into library using TRaSH Plex TMDB templates; also support `simple` and `none`.

**Deliverables**
- Renamer templating for movie/tv, safe moves, conflict handling + rollback.
- Per‑library template override.

**Warp prompt**
Implement a renamer that applies default TRaSH Plex TMDB templates for Movies/TV (plus `simple` and `none`). Trigger on SAB completion and validate resulting paths remain inside the library root.

---

## 12) Quality profiles & upgrade engine (phase 1)
**Goal**: Minimal tiers now; plan TRaSH presets later.

**Deliverables**
- Quality profile schema (score + allowed codecs/resolution/source) and evaluation service.
- Endpoint to compare an indexer result vs current files and declare upgrade/no‑upgrade.

**Warp prompt**
Add quality evaluation, store normalized quality on MediaFile, and implement an endpoint that decides whether a candidate is a worthy upgrade.

---

## 13) Jobs, logs & observability
**Goal**: Async scheduler with persistent job store and a simple log viewer.

**Deliverables**
- APScheduler AsyncIOScheduler with jobs persisted in DB; `/api/v1/jobs` list/detail.
- `/api/v1/logs/tail` returning the last N lines from the configured log file.

**Warp prompt**
Wire scheduler at startup with decorators for jobs, persist executions, and expose `/jobs` APIs. Implement `/logs/tail` with size guard and follow‑mode support.

---

## 14) First‑time setup wizard
**Goal**: Guide: TMDB → at least one Disk + Library → (optional) SAB + Indexers → verify.

**Deliverables**
- `/setup` route gated until config exists; writes `config.yml` and triggers settings reload.

**Warp prompt**
Build a wizard to collect TMDB key, a Disk and Library, and optional SAB/indexers. Validate and persist, then signal the server to reload settings.

---

## 15) Testing & fixtures
**Goal**: Baseline tests to prevent regressions.

**Deliverables**
- Pytest for config, parser, renamer; API smoke tests; TMDB client mock.
- Web tests (Vitest) for Settings and Search.

**Warp prompt**
Add pytest with coverage, fixtures for sample filenames and TMDB responses, and Vitest for two key components.

---

## 16) Docker production image (single container)
**Goal**: Multi‑stage build that produces one image with server + static web.

**Deliverables**
- Dockerfile that builds the web app, bundles static assets into server, and runs FastAPI under Uvicorn. Healthchecks; volumes for `/lhmm/media`, `/lhmm/config`, `/lhmm/logs`.

**Warp prompt**
Author a multi‑stage Dockerfile: build frontend, copy `dist` into server, and start FastAPI. Define healthcheck and document required volumes.

---

## 17) CI/CD (GitHub Actions → GHCR; PR‑first)
**Goal**: Lint/test/build on PR; tag releases publish images; `:edge` on main via PR only.

**Deliverables**
- `.github/workflows/ci.yml` (lint + tests) and `release.yml` (build/push GHCR on tag).
- `docs/CI-CD.md` for branching and release process.

**Warp prompt**
Create CI to run lint/tests on PR. On `v*` tags, build and push `ghcr.io/<org>/lhmm:<tag>` and `:latest`. Protect `main` so merges require passing checks.

---

## 18) Request management (Overseerr‑style, phase 1)
**Goal**: Users request titles; admin approves → indexer search → SAB add.

**Deliverables**
- Local‑only `User` and `Request` models, session handling, request UI + admin queue.

**Warp prompt**
Add `User` and `Request` models. Public search uses TMDB only. Authenticated users can submit requests; admin can approve/deny. On approve, search configured indexers and add best match to SAB.

---

## 19) Auth hardening & settings (phase 2)
**Goal**: Optional basic‑auth site‑wide; roles for admin vs user; basic rate limits.

**Deliverables**
- Config‑gated basic auth for admin routes; session cookies for user area; rate‑limit on sensitive endpoints.

**Warp prompt**
Implement basic auth middleware for admin routes if enabled, role checks for request actions, and naive rate‑limiting for `downloads/add`.

---

## 20) Future: Presets, music, extensibility
**Goal**: Plan without blocking v1.

**Deliverables**
- Import TRaSH quality presets as JSON; profile editor UI.
- Music domain (MusicBrainz) behind feature flag.
- Plugin/provider interfaces.

**Warp prompt**
Add a presets loader for TRaSH quality profiles and an editor. Define provider interfaces to enable plugins.

---

# Documentation checklist
- `docs/ADR-0001-architecture.md` — architecture & tradeoffs (Docker‑first dev).
- `docs/STANDARDS.md` — IDs, timestamps, error envelope, pagination, versioning.
- `docs/CONFIG.md` — all config keys with examples.
- `docs/DEVELOPMENT.md` — dev flow with Docker; hot reload.
- `docs/DEPLOYMENT.md` — single‑container run; volumes for `/lhmm/media`, `/lhmm/config`, `/lhmm/logs`.
- `docs/NAMING.md` — default rename templates (Plex TMDB) and `simple`/`none` variants.
- `docs/CI-CD.md` — branching strategy, tags, release process.

# Acceptance criteria for v1
- Runs fully via Docker from day one; bind mounts for `/lhmm/media`, `/lhmm/config`, `/lhmm/logs` verified in dev.
- UI shell + Settings; Disks + Libraries CRUD; Unified Search operational; SAB add/poll works; Scanner + Renamer correctly place files using defaults; Logs rotate with local timestamps; Jobs visible; Setup wizard on first run; OpenAPI at `/api/v1/docs`.
- Libraries **list** and **detail** pages exist and render data.
- **Movie detail** and **Series detail** pages exist with combined local + TMDB information (where available).
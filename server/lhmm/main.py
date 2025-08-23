from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from lhmm.settings import settings
from lhmm.logging_config import setup_logging
from lhmm.api.v1 import tmdb as tmdb_routes
import os, time
import logging, time as _time
try:
    import ulid as _ulid
except Exception:  # optional
    _ulid = None

# make sure log dir exists
os.makedirs(os.path.dirname(settings.logging.file), exist_ok=True)

# init logging from settings
setup_logging(
    log_file=settings.logging.file,
    max_bytes=settings.logging.max_bytes,
    backups=settings.logging.backups,
    level=settings.logging.level,
    timezone=settings.logging.timezone,
)

app = FastAPI(
    title="Lighthouse API",
    docs_url="/api/v1/docs",
    redoc_url=None,
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api/v1")

@api.get("/healthz")
def healthz():
    return {"ok": True, "time": int(time.time())}

# DB health check
from lhmm.db.session import SessionLocal
from lhmm.db.session import engine
from sqlalchemy import text

@api.get("/db/ping")
def db_ping():
    # Open and close a session to ensure DB is reachable
    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
    return {"db": "ok"}


# Report current SQLite PRAGMAs via the app's SQLAlchemy engine
@api.get("/db/pragma")
def db_pragma():
    # Report current SQLite PRAGMAs via the app's SQLAlchemy engine
    with engine.connect() as conn:
        jm = conn.exec_driver_sql("PRAGMA journal_mode;").scalar()
        fk = conn.exec_driver_sql("PRAGMA foreign_keys;").scalar()
    return {"journal_mode": jm, "foreign_keys": fk}

from lhmm.api.v1 import disks as disks_routes
from lhmm.api.v1 import libraries as libraries_routes

api.include_router(tmdb_routes.router)
api.include_router(disks_routes.router)
api.include_router(libraries_routes.router)

@app.middleware("http")
async def request_id_logger(request: Request, call_next):
    rid = (_ulid.new().str if _ulid else str(int(_time.time() * 1000)))
    start = _time.perf_counter()
    response = await call_next(request)
    dur_ms = int((_time.perf_counter() - start) * 1000)
    response.headers["X-Request-ID"] = rid
    logging.getLogger("uvicorn.access").info({
        "event": "request",
        "rid": rid,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "dur_ms": dur_ms,
    })
    return response

app.include_router(api)


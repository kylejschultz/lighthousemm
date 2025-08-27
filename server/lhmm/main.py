from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from lhmm.settings import settings
from lhmm.logging_json import setup_json_logging
from lhmm.api.v1 import tmdb as tmdb_routes
import os, time
from lhmm.api.v1 import system as system_routes
import logging
import json

# make sure log dir exists
os.makedirs(os.path.dirname(settings.logging.file), exist_ok=True)

app = FastAPI(
    title="Lighthouse API",
    docs_url="/api/v1/docs",
    redoc_url=None,
    openapi_url="/api/v1/openapi.json",
)

# Initialize JSON logging immediately after app creation
setup_json_logging(
    level=settings.logging.level,
    logfile=settings.logging.file,
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
api.include_router(system_routes.router)
api.include_router(disks_routes.router)
api.include_router(libraries_routes.router)

@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dur_ms = int((time.perf_counter() - start) * 1000)
    logging.getLogger("lhmm.request").info({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "dur_ms": dur_ms,
    })
    return response

app.include_router(api)

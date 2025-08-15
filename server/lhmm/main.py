from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from lhmm.settings import settings
from lhmm.logging_config import setup_logging
from lhmm.api.v1 import tmdb as tmdb_routes
import os, time

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
    allow_origins=["http://localhost:5173"],
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

api.include_router(tmdb_routes.router)
app.include_router(api)


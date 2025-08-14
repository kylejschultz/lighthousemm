import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Configure logging BEFORE app instantiation
try:
    from .logging_config import setup_logging
except ImportError:  # pragma: no cover
    from lhmm.logging_config import setup_logging  # type: ignore

LOG_DIR = os.environ.get("LHMM_LOG_DIR", "/lhmm/logs")
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "lhmm.log")
LOG_FILE = os.environ.get("LHMM_LOG_FILE", DEFAULT_LOG_FILE)
LOG_LEVEL = os.environ.get("LHMM_LOG_LEVEL", "INFO")
LOG_TZ = os.environ.get("LHMM_LOG_TZ", "local")
LOG_MAX_BYTES = int(os.environ.get("LHMM_LOG_MAX_BYTES", "10000000"))
LOG_BACKUPS = int(os.environ.get("LHMM_LOG_BACKUPS", "5"))
setup_logging(
    log_file=LOG_FILE,
    max_bytes=LOG_MAX_BYTES,
    backups=LOG_BACKUPS,
    level=LOG_LEVEL,
    timezone=LOG_TZ,
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
    return {"ok": True}

app.include_router(api)


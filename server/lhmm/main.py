from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from lhmm.settings import settings
from lhmm.logging_config import setup_logging
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

app.include_router(api)


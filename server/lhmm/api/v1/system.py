from fastapi import APIRouter
from lhmm.settings import settings

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/config")
def get_config():
    # Return only safe, non-secret parts the UI needs.
    tmdb_key = settings.tmdb.api_key or ""
    tmdb_mask = (tmdb_key[:4] + "…" + tmdb_key[-2:]) if len(tmdb_key) >= 8 else ""
    return {
        "cors": {"allowed_origins": settings.cors.allowed_origins},
        "paths": {"media_root": settings.paths.media_root},
        "db": {"url": settings.db.url},
        "tmdb": {"api_key_mask": tmdb_mask, "configured": bool(settings.tmdb.api_key)},
        "sabnzbd": {"url": settings.sabnzbd.url, "configured": bool(settings.sabnzbd.api_key)},
    }


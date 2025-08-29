from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, conint, confloat, field_validator
from ...db.session import SessionLocal
from ...services.config_service import load_config, save_partial
from ...services.sab import SabClient
import logging, json

router = APIRouter(prefix="/system", tags=["system"])

from pydantic import BaseModel, conint, confloat, field_validator

class ConfigPatch(BaseModel):
    # existing
    tmdb_api_key: str | None = None
    log_level: str | None = None
    log_max_bytes: conint(ge=1) | None = None
    log_max_mb: confloat(gt=0) | None = None
    log_backups: conint(ge=0) | None = None
    cors_allowed_origins: list[str] | str | None = None
    # NEW: SAB
    sab_url: str | None = None
    sab_api_key: str | None = None
    sab_category_movies: str | None = None
    sab_category_tv: str | None = None

    @field_validator("log_level")
    @classmethod
    def _lv(cls, v):
        if v is None: return v
        v2 = v.upper()
        if v2 not in {"DEBUG","INFO","WARNING","ERROR","CRITICAL"}:
            raise ValueError("invalid log_level")
        return v2

@router.get("/config")
def get_config():
    db = SessionLocal()
    try:
        return load_config(db)
    finally:
        db.close()

@router.put("/config")
def update_config(patch: ConfigPatch):
    db = SessionLocal()
    try:
        old = load_config(db)
        payload = {k: v for k, v in patch.model_dump(exclude_unset=True).items() if v is not None}
        new_cfg = save_partial(db, payload)

        logger = logging.getLogger("lhmm.config")
        def _mask(k, v):
            return "***" if (k in {"tmdb_api_key","sab_api_key"} and v) else v
        changes = []
        for k in (
            "tmdb_api_key","log_level","log_max_bytes","log_backups","cors_allowed_origins",
            "sab_url","sab_api_key","sab_category_movies","sab_category_tv",
        ):
            ov, nv = old.get(k), new_cfg.get(k)
            if ov != nv:
                if k == "cors_allowed_origins":
                    changes.append({"key": k, "old_count": len(ov or []), "new_count": len(nv or [])})
                else:
                    changes.append({"key": k, "old": _mask(k, ov), "new": _mask(k, nv)})
        if changes:
            logger.info({"event":"config.update","changes": changes})

        # apply log level immediately
        if patch.log_level:
            lvl = getattr(logging, (patch.log_level or "INFO").upper(), logging.INFO)
            for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access", "lhmm"):
                logging.getLogger(name).setLevel(lvl)
        return {"ok": True, "config": new_cfg, "note": "CORS origins changes require backend restart"}
    finally:
        db.commit(); db.close()

@router.post("/sab/test")
async def sab_test():
    db = SessionLocal()
    try:
        cfg = load_config(db)
    finally:
        db.close()
    url = (cfg.get("sab_url") or "").strip()
    key = (cfg.get("sab_api_key") or "").strip()
    if not url or not key:
        raise HTTPException(status_code=400, detail="SABnzbd URL or API key missing")
    try:
        ver = await SabClient(url, key).version()
        logging.getLogger("lhmm.sab").info({"event":"sab.test.ok","url":url})
        return {"ok": True, "version": ver}
    except Exception as e:
        logging.getLogger("lhmm.sab").warning({"event":"sab.test.fail","url":url,"err":str(e)})
        raise HTTPException(status_code=502, detail=f"SAB test failed: {e}")

# Optional: read-only queue and history
@router.get("/sab/queue")
async def sab_queue():
    db = SessionLocal()
    try:
        cfg = load_config(db)
    finally:
        db.close()
    url = (cfg.get("sab_url") or "").strip()
    key = (cfg.get("sab_api_key") or "").strip()
    if not url or not key:
        raise HTTPException(status_code=400, detail="SABnzbd URL or API key missing")
    return await SabClient(url, key).queue()

@router.get("/sab/history")
async def sab_history(limit: int = 50):
    db = SessionLocal()
    try:
        cfg = load_config(db)
    finally:
        db.close()
    url = (cfg.get("sab_url") or "").strip()
    key = (cfg.get("sab_api_key") or "").strip()
    if not url or not key:
        raise HTTPException(status_code=400, detail="SABnzbd URL or API key missing")
    return await SabClient(url, key).history(0, limit)


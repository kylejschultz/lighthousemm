from fastapi import APIRouter
from pydantic import BaseModel, conint, confloat, field_validator
from ...db.session import SessionLocal
from ...services.config_service import load_config, save_partial
import logging, json

router = APIRouter(prefix="/system", tags=["system"])

class ConfigPatch(BaseModel):
    tmdb_api_key: str | None = None
    log_level: str | None = None
    log_max_bytes: conint(ge=1) | None = None
    log_max_mb: confloat(gt=0) | None = None
    log_backups: conint(ge=0) | None = None
    cors_allowed_origins: list[str] | str | None = None

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
            return "***" if k == "tmdb_api_key" and v else v
        changes = []
        for k in ("tmdb_api_key","log_level","log_max_bytes","log_backups","cors_allowed_origins"):
            ov, nv = old.get(k), new_cfg.get(k)
            if ov != nv:
                if k == "cors_allowed_origins":
                    ovd = len(ov or [])
                    nvd = len(nv or [])
                    changes.append({"key": k, "old_count": ovd, "new_count": nvd})
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


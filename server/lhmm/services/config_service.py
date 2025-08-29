from __future__ import annotations
from sqlalchemy.orm import Session
from lhmm.db.models import AppConfig
import os

DEFAULTS = {
  "tmdb_api_key": None,
  "log_level": "INFO",
  "log_max_bytes": 10_000_000,  # ~10 MB
  "log_backups": 5,
  # UI origins only (dev + your domain)
  "cors_allowed_origins": [
    "https://lhmm.dev",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173"
  ],
  # SABnzbd
  "sab_url": None,
  "sab_api_key": None,
  "sab_category_movies": "movies",
  "sab_category_tv": "tv",
}

def _ensure_row(db: Session) -> AppConfig:
  row = db.query(AppConfig).filter_by(id=1).one_or_none()
  if not row:
    row = AppConfig(id=1, data=DEFAULTS.copy())
    db.add(row); db.flush()
  return row

def _normalize_origins(val):
  if not val: return []
  if isinstance(val, str):
    val = [s.strip() for s in val.split(",")]
  out = []
  seen = set()
  for x in val:
    if not x: continue
    k = x.strip().rstrip("/")
    if k not in seen:
      seen.add(k); out.append(k)
  return out

def _mask_secret(v): 
  return "***" if v else None

def load_config(db: Session) -> dict:
  row = _ensure_row(db)
  cfg = {**DEFAULTS, **(row.data or {})}
  # env overrides (optional)
  if os.getenv("TMDB_API_KEY"): cfg["tmdb_api_key"] = os.getenv("TMDB_API_KEY")
  if os.getenv("LHMM_LOG_LEVEL"): cfg["log_level"] = os.getenv("LHMM_LOG_LEVEL")
  cfg["cors_allowed_origins"] = _normalize_origins(cfg.get("cors_allowed_origins"))
  return cfg

def save_partial(db: Session, patch: dict) -> dict:
  row = _ensure_row(db)
  merged = {**DEFAULTS, **(row.data or {})}
  # accept log_max_mb (preferred), or legacy log_max_bytes
  if "log_max_mb" in patch and patch["log_max_mb"] is not None:
    merged["log_max_bytes"] = int(float(patch["log_max_mb"]) * 1_000_000)
  if "log_max_bytes" in patch and patch["log_max_bytes"] is not None:
    merged["log_max_bytes"] = int(patch["log_max_bytes"])
  # other fields
  for k in ("tmdb_api_key","log_level","log_backups"):
    if k in patch and patch[k] is not None:
      merged[k] = patch[k]
  # SAB settings
  for k in ("sab_url","sab_api_key","sab_category_movies","sab_category_tv"):
      if k in patch and patch[k] is not None:
          merged[k] = patch[k]
  if "cors_allowed_origins" in patch and patch["cors_allowed_origins"] is not None:
    merged["cors_allowed_origins"] = _normalize_origins(patch["cors_allowed_origins"])
  row.data = merged
  db.add(row); db.flush()
  return merged


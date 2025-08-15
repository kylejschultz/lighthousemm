from __future__ import annotations
import json, os, pathlib
from typing import List, Optional, Dict, Any
import yaml
from pydantic import BaseModel, Field, ValidationError

CONFIG_DIR = pathlib.Path(os.environ.get("LHMM_CONFIG_DIR", "/lhmm/config"))
DEFAULT_YAML = CONFIG_DIR / "default.yml"

class LoggingCfg(BaseModel):
    file: str = "/lhmm/logs/lhmm.log"
    max_bytes: int = 10_000_000
    backups: int = 5
    level: str = "INFO"
    timezone: str = "local"

class DBCfg(BaseModel):
    url: str = "sqlite:////lhmm/config/db/lhmm.sqlite3"

class PathsCfg(BaseModel):
    media_root: str = "/lhmm/media"

class SchedulerCfg(BaseModel):
    enabled: bool = True

class TMDBCfg(BaseModel):
    api_key: str = ""

class SABCfg(BaseModel):
    url: str = ""
    api_key: str = ""
    category_default: str = ""

class IndexerCfg(BaseModel):
    name: str
    url: str
    api_key: str = ""
    capabilities: Dict[str, Any] = Field(default_factory=dict)

class BasicAuthCfg(BaseModel):
    enabled: bool = False
    username: str = ""
    password: str = ""

class AuthCfg(BaseModel):
    basic: BasicAuthCfg = BasicAuthCfg()

class Settings(BaseModel):
    logging: LoggingCfg = LoggingCfg()
    db: DBCfg = DBCfg()
    paths: PathsCfg = PathsCfg()
    scheduler: SchedulerCfg = SchedulerCfg()
    tmdb: TMDBCfg = TMDBCfg()
    sabnzbd: SABCfg = SABCfg()
    indexers: List[IndexerCfg] = Field(default_factory=list)
    auth: AuthCfg = AuthCfg()

def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def _parse_env_overrides() -> Dict[str, Any]:
    """
    Nested overrides via LHMM__SECTION__KEY=VALUE
    Examples:
      LHMM__LOGGING__LEVEL=DEBUG
      LHMM__DB__URL=sqlite:////lhmm/config/db/lhmm.sqlite3
      LHMM__INDEXERS=[{"name":"NZB","url":"https://..."}]
    """
    prefix = "LHMM__"
    data: Dict[str, Any] = {}
    for k, v in os.environ.items():
        if not k.startswith(prefix):
            continue
        parts = k[len(prefix):].split("__")
        if not parts:
            continue
        # Try JSON; fall back to bool/int/str
        try:
            val = json.loads(v)
        except Exception:
            lo = v.lower()
            if lo in ("true", "false"):
                val = (lo == "true")
            else:
                try:
                    val = int(v)
                except ValueError:
                    val = v
        cursor = data
        for p in parts[:-1]:
            p = p.lower()
            cursor = cursor.setdefault(p, {})
        cursor[parts[-1].lower()] = val
    return data

def load_settings() -> Settings:
    baseline = Settings().model_dump()
    file_cfg: Dict[str, Any] = {}
    if DEFAULT_YAML.exists():
        with DEFAULT_YAML.open("r", encoding="utf-8") as f:
            file_cfg = yaml.safe_load(f) or {}
    merged = _deep_merge(baseline, file_cfg)
    env_cfg = _parse_env_overrides()
    merged = _deep_merge(merged, env_cfg)
    try:
        return Settings.model_validate(merged)
    except ValidationError as ve:
        raise SystemExit(f"Invalid configuration: {ve}")

# Singleton
settings = load_settings()


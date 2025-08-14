import logging
import logging.config
from logging.handlers import RotatingFileHandler
import os
import json
import time
import sys
import platform
import typing as t
from datetime import datetime, timezone as dt_timezone

try:
    # Python 3.9+
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

try:
    # python-json-logger is in requirements
    from pythonjsonlogger.jsonlogger import JsonFormatter
except Exception as e:  # pragma: no cover
    raise RuntimeError("python-json-logger is required but not installed") from e


def _resolve_tz(timezone: str):
    tz = None
    if timezone.upper() == "UTC":
        tz = dt_timezone.utc
    elif timezone.lower() == "local":
        # Best effort local tz with offset
        tz = datetime.now().astimezone().tzinfo
    else:
        if ZoneInfo is None:
            # tzdata may not be present; fall back to local
            tz = datetime.now().astimezone().tzinfo
        else:
            try:
                tz = ZoneInfo(timezone)
            except Exception:
                tz = datetime.now().astimezone().tzinfo
    return tz


class TzAwareJsonFormatter(JsonFormatter):
    def __init__(self, *args, timezone: str = "local", **kwargs):
        super().__init__(*args, **kwargs)
        self._tz = _resolve_tz(timezone)

    def formatTime(self, record, datefmt=None):  # noqa: N802 (match logging API)
        ts = datetime.fromtimestamp(record.created, tz=self._tz)
        # ISO8601 with offset, second precision
        return ts.isoformat(timespec="seconds")

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # Ensure level and logger name included and consistent
        if 'level' not in log_record:
            log_record['level'] = record.levelname
        if 'logger' not in log_record:
            log_record['logger'] = record.name
        # Rename default "asctime" to "ts" if present
        if 'asctime' in log_record:
            log_record['ts'] = log_record.pop('asctime')
        # Ensure message is a string (json-serializable)
        if 'message' in log_record and isinstance(log_record['message'], bytes):
            log_record['message'] = log_record['message'].decode('utf-8', errors='replace')


class TzAwareConsoleFormatter(logging.Formatter):
    def __init__(self, timezone: str = "local"):
        super().__init__()
        self._tz = _resolve_tz(timezone)

    def formatTime(self, record, datefmt=None):  # noqa: N802
        ts = datetime.fromtimestamp(record.created, tz=self._tz)
        if datefmt:
            return ts.strftime(datefmt)
        return ts.strftime("%H:%M:%S")

    def format(self, record):
        base = f"[{self.formatTime(record)}] {record.levelname:>5} {record.name}: "
        msg = record.getMessage()
        # Render extras (dict-like) if present
        extras = {}
        for k, v in record.__dict__.items():
            if k in (
                'name','msg','args','levelname','levelno','pathname','filename','module',
                'exc_info','exc_text','stack_info','lineno','funcName','created','msecs',
                'relativeCreated','thread','threadName','processName','process','asctime'
            ):
                continue
            extras[k] = v
        extra_str = ""
        if extras:
            try:
                # Compact JSON for extras
                extra_str = " " + json.dumps(extras, ensure_ascii=False, separators=(",", ":"))
            except Exception:
                extra_str = f" extras={extras!r}"
        return base + str(msg) + extra_str


def setup_logging(
    log_file: str = "/lhmm/logs/lhmm.log",
    max_bytes: int = 10_000_000,
    backups: int = 5,
    level: str = "INFO",
    timezone: str = "local",
) -> None:
    """
    Configure application logging with rotating JSON file and pretty console.

    Must be called before creating the FastAPI app instance.
    """
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Build dictConfig
    dict_config: t.Dict[str, t.Any] = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': f"{__name__}.TzAwareJsonFormatter",
                'fmt': '%(asctime)s %(name)s %(levelname)s %(message)s',
                'timezone': timezone,
            },
            'console': {
                '()': f"{__name__}.TzAwareConsoleFormatter",
                'timezone': timezone,
            },
        },
        'handlers': {
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': level,
                'formatter': 'json',
                'filename': log_file,
                'maxBytes': max_bytes,
                'backupCount': backups,
                'encoding': 'utf-8',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'console',
                'stream': 'ext://sys.stdout',
            },
        },
        'root': {
            'level': level,
            'handlers': ['console', 'file'],
        },
    }

    logging.config.dictConfig(dict_config)

    # Emit startup banner once here
    logger = logging.getLogger("lhmm")
    try:
        pid = os.getpid()
    except Exception:
        pid = None
    logger.info("startup", extra={"event": "startup", "version": "dev", "pid": pid})

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Any, Dict
from http import HTTPStatus

class HumanFormatter(logging.Formatter):
    """Human-readable log lines; colored for console, plain for file.
    Aligned columns (Option #4):
    11:34:15 PM  INFO   lhmm.req   GET    /api/v1/tmdb/search                     200 OK   186ms
    """
    COLORS = {
        "DEBUG": "\x1b[90m",
        "INFO": "\x1b[36m",
        "WARNING": "\x1b[33m",
        "ERROR": "\x1b[31m",
        "CRITICAL": "\x1b[35m",
        "GREEN": "\x1b[32m",
    }
    RESET = "\x1b[0m"

    def __init__(self, color: bool):
        super().__init__()
        self.color = color

    @classmethod
    def _status_color(cls, status: int) -> str:
        if status >= 500:
            return cls.COLORS["ERROR"]
        if status >= 400:
            return cls.COLORS["WARNING"]
        return cls.COLORS["GREEN"]

    def _colorize(self, level: str, text: str) -> str:
        if not self.color:
            return text
        c = self.COLORS.get(level.upper(), "")
        return f"{c}{text}{self.RESET}" if c else text

    @staticmethod
    def _short_level(level: str) -> str:
        return {"WARNING": "WARN", "CRITICAL": "CRIT"}.get(level, level)

    @staticmethod
    def _truncate(s: str, width: int) -> str:
        if len(s) <= width:
            return s
        if width <= 1:
            return s[:width]
        return s[: width - 1] + "…"

    def format(self, record: logging.LogRecord) -> str:
        # 12-hour time with AM/PM
        ts = datetime.now().strftime("%I:%M:%S %p")
        # Columns
        level = self._short_level(record.levelname)
        level_col = f"{level:<5}"  # INFO , WARN , ERROR
        if self.color:
            level_col = self._colorize(record.levelname, level_col)

        short_logger = {
            "uvicorn.access": "uvi.acc",
            "uvicorn.error": "uvi.err",
            "httpx": "httpx",
            "lhmm.request": "lhmm.req",
        }.get(record.name, record.name)
        logger_col = f"{short_logger:<10}"

        msg = record.msg
        # Structured request dict from our middleware
        if isinstance(msg, dict) and msg.get("event") == "request":
            from http import HTTPStatus
            method = msg.get("method", "?")
            path = msg.get("path", "?")
            status = int(msg.get("status", 0))
            dur = msg.get("dur_ms", 0)
            # Pad columns
            method_col = f"{method:<6}"
            path_col = f"{self._truncate(path, 44):<44}"
            try:
                phrase = HTTPStatus(status).phrase
            except Exception:
                phrase = ""
            status_txt = f"{status} {phrase}".strip()
            if self.color and status:
                status_txt = f"{self._status_color(status)}{status_txt}{self.RESET}"
            status_col = f"{status_txt:<8}"
            dur_col = f"{dur}ms"
            return f"{ts}  {level_col}  {logger_col} {method_col} {path_col} {status_col}  {dur_col}"

        # Generic dict -> key=value compact after the aligned prefix
        if isinstance(msg, dict):
            kv = " ".join(f"{k}={v}" for k, v in msg.items())
            return f"{ts}  {level_col}  {logger_col} {kv}"

        # Plain string messages
        text = record.getMessage()
        text_col = self._truncate(text, 80)
        return f"{ts}  {level_col}  {logger_col} {text_col}"


def setup_json_logging(level: str = "INFO", logfile: str = "/lhmm/logs/app.log",
                        max_bytes: int | None = None, backup_count: int | None = None) -> None:
    """Configure logging with human-readable lines for both console and file; suppress duplicate uvicorn access."""
    lvl = getattr(logging, level.upper(), logging.INFO)
    max_bytes = max_bytes or int(os.getenv("LHMM_LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    backup_count = backup_count or int(os.getenv("LHMM_LOG_BACKUPS", "5"))

    # Console gets color only when attached to a TTY
    color_console = getattr(sys.stdout, "isatty", lambda: False)()

    console = logging.StreamHandler()
    console.setLevel(lvl)
    console.setFormatter(HumanFormatter(color_console))

    fileh = RotatingFileHandler(logfile, maxBytes=max_bytes, backupCount=backup_count)
    fileh.setLevel(lvl)
    fileh.setFormatter(HumanFormatter(False))

    root = logging.getLogger()
    root.handlers = [console, fileh]
    root.setLevel(lvl)

    # Apply same handlers to uvicorn loggers and prevent propagation
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers = [console, fileh]
        lg.setLevel(lvl)
        lg.propagate = False

    # Permanently suppress uvicorn access INFO lines to avoid duplicates
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)

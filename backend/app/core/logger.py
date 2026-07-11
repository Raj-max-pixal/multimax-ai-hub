"""
Structured Logging Module.

Provides JSON-formatted logging with context support.
Logs include correlation IDs, request IDs, and structured metadata
for easy integration with log aggregation tools.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.config import Settings


class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Add extra context from the record
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "id", "levelname", "levelno",
                "lineno", "module", "msecs", "message", "msg",
                "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
            ):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


def setup_logging(settings: Settings) -> None:
    """Configure the root logger based on settings.

    Args:
        settings: Application settings containing log configuration.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.APP_LOG_LEVEL.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if settings.LOG_FILE:
        try:
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                settings.LOG_FILE,
                maxBytes=settings.LOG_MAX_BYTES,
                backupCount=settings.LOG_BACKUP_COUNT,
            )
            if settings.LOG_FORMAT == "json":
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                )
            root_logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            root_logger.warning(f"Could not create log file {settings.LOG_FILE}: {e}")

    # Set third-party log levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured",
        extra={
            "log_level": settings.APP_LOG_LEVEL,
            "log_format": settings.LOG_FORMAT,
            "log_file": settings.LOG_FILE,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
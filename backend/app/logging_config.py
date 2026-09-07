"""
Structured logging setup.

Emits one JSON object per log line so logs are machine-parseable and ready for
later SIEM/monitoring integration. Per project rules we NEVER log raw audio,
secrets, or unnecessary personal information — only operational metadata such
as call_id, module, processing_time, status, and error_type.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Merge any structured 'extra' fields attached to the record.
        # Standard LogRecord attributes are skipped so only custom keys remain.
        standard = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)
        standard.update({"message", "asctime"})
        for key, value in record.__dict__.items():
            if key not in standard and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["error_type"] = record.exc_info[0].__name__
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger with a JSON handler (idempotent)."""
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Avoid duplicate handlers if called more than once (e.g. reload).
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

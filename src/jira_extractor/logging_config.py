"""Configure stdlib logging with optional JSON output."""
from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO", fmt: str = "text") -> None:
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if fmt == "json":
        try:
            from pythonjsonlogger import jsonlogger  # type: ignore[import-untyped]

            formatter = jsonlogger.JsonFormatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s"
            )
        except ImportError:
            formatter = _text_formatter()
    else:
        formatter = _text_formatter()

    handler.setFormatter(formatter)
    root.handlers.clear()
    root.addHandler(handler)


def _text_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

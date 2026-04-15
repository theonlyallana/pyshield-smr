"""Logger factory with a consistent format."""

from __future__ import annotations

import logging
from typing import Optional


def get_logger(
    name: str = "pyshield_smr",
    *,
    level: int | str = "INFO",
    fmt: Optional[str] = None,
) -> logging.Logger:
    """Return a configured logger. Idempotent."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt or "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "%Y-%m-%dT%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(level if isinstance(level, int) else logging.getLevelName(level))
    return logger

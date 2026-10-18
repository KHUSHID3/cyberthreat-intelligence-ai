"""
Simple logging configuration for the project.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from config import settings


def setup_logging(
    level: Optional[str] = None,
    name: str = "cyberthreat_intelligence_ai",
) -> logging.Logger:
    """
    Configure root logger for the application.

    Parameters
    ----------
    level : str, optional
        Logging level (DEBUG, INFO, WARNING, ...). Defaults to settings.LOG_LEVEL.
    name : str
        Logger name.

    Returns
    -------
    logging.Logger
    """
    level = (level or settings.LOG_LEVEL).upper()
    numeric_level = getattr(logging, level, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers when called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Prevent propagation to root logger to avoid double messages
    logger.propagate = False
    return logger


def get_logger(name: str = "cyberthreat_intelligence_ai") -> logging.Logger:
    """
    Return a logger. Calls setup_logging if the logger has no handlers yet.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logging(name=name)
    return logger 
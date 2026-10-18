"""
Small generic helper functions used across the project.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def ensure_dir(path: Path | str) -> Path:
    """Create directory (and parents) if it does not exist. Return Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 string with Z suffix."""
    return datetime.utcnow().isoformat() + "Z"


def safe_get(d: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely traverse nested dictionaries.

    Example
    -------
    safe_get(data, "entities", "cve", default=[])
    """
    current = d
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is default:
            return default
    return current


def truncate_text(text: str, max_length: int = 200, suffix: str = "…") -> str:
    """
    Truncate a string to max_length characters, appending suffix if truncated.
    """
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)].rstrip() + suffix


def is_empty(value: Any) -> bool:
    """Return True if value is None, empty string, empty list/dict, or NaN-like."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict, tuple, set)) and len(value) == 0:
        return True
    try:
        import pandas as pd
        if pd.isna(value):
            return True
    except Exception:
        pass
    return False
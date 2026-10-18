"""
Text cleaning and DataFrame preparation utilities.
"""

from __future__ import annotations

import re
from typing import Any, List, Optional

import pandas as pd


def clean_text(text: Any) -> str:
    """
    Basic defensive text normalization.

    - Lowercases
    - Removes URLs and emails
    - Keeps alphanumeric characters, spaces, hyphens and dots
    - Collapses repeated whitespace
    """
    if not isinstance(text, str):
        return ""

    text = text.lower().strip()
    text = re.sub(r"http\S+|www\.\S+", " ", text)       # URLs
    text = re.sub(r"\S+@\S+", " ", text)                # emails
    text = re.sub(r"[^a-z0-9\s\-\.]", " ", text)        # keep safe chars
    text = re.sub(r"\s+", " ", text)                    # collapse spaces
    return text.strip()


def _safe_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return []


def _safe_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    return {}


def prepare_dataframe(
    df: pd.DataFrame,
    min_text_length: int = 20,
    drop_empty_urgency: bool = True,
) -> pd.DataFrame:
    """
    Apply standard cleaning and feature preparation steps.

    Creates:
    - title_clean
    - summary_clean
    - text               (title_clean + summary_clean)
    - urgency_level      (lower-cased, stripped)
    - parsed date columns (if present)

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe from the loader.
    min_text_length : int
        Rows whose combined text is shorter than this are dropped.
    drop_empty_urgency : bool
        If True, rows with missing urgency_level are removed.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe (new object).
    """
    df = df.copy()

    # Ensure core text columns exist
    if "title" not in df.columns:
        df["title"] = ""
    if "summary" not in df.columns:
        df["summary"] = ""

    df["title"] = df["title"].fillna("").astype(str)
    df["summary"] = df["summary"].fillna("").astype(str)

    # Cleaned versions
    df["title_clean"] = df["title"].map(clean_text)
    df["summary_clean"] = df["summary"].map(clean_text)
    df["text"] = (df["title_clean"] + " " + df["summary_clean"]).str.strip()

    # Urgency
    if "urgency_level" in df.columns:
        df["urgency_level"] = (
            df["urgency_level"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.strip()
        )
        if drop_empty_urgency:
            df = df[df["urgency_level"] != ""].copy()

    # Dates
    for col in ("first_reported", "last_reported"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Normalize list / dict columns
    if "keywords" in df.columns:
        df["keywords"] = df["keywords"].map(_safe_list)
    if "sources" in df.columns:
        df["sources"] = df["sources"].map(_safe_list)
    if "entities" in df.columns:
        df["entities"] = df["entities"].map(_safe_dict)

    # Drop rows with extremely short text
    if min_text_length > 0:
        df = df[df["text"].str.len() >= min_text_length].copy()

    # Ensure cluster_id is string
    if "cluster_id" in df.columns:
        df["cluster_id"] = df["cluster_id"].astype(str)

    df = df.reset_index(drop=True)
    return df
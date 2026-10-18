"""
Safe numeric / metadata feature helpers.
Only uses fields that do not leak the target.
"""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

# Columns considered safe metadata features
METADATA_COLUMNS: List[str] = [
    "threat_score",
    "severity_score",
    "article_count",
    "source_count",
    "credibility_score",
]


def extract_metadata_features(
    df: pd.DataFrame,
    columns: List[str] | None = None,
    fill_value: float = 0.0,
) -> np.ndarray:
    """
    Extract numeric metadata features as a dense numpy array.

    Parameters
    ----------
    df : pd.DataFrame
    columns : list of str, optional
        Subset of METADATA_COLUMNS to use. Defaults to all available.
    fill_value : float
        Value used to fill NaNs.

    Returns
    -------
    np.ndarray of shape (n_samples, n_features)
    """
    cols = columns or METADATA_COLUMNS
    available = [c for c in cols if c in df.columns]

    if not available:
        return np.zeros((len(df), 0), dtype=np.float32)

    mat = df[available].apply(pd.to_numeric, errors="coerce")
    mat = mat.fillna(fill_value).astype(np.float32)
    return mat.values
"""
Expected schema, constants, and lightweight validation helpers
for the ThreatCluster dataset.
"""

from __future__ import annotations

from typing import List, Set

import pandas as pd

# Constants derived from the actual dataset card / viewer

EXPECTED_COLUMNS: List[str] = [
    "cluster_id",
    "title",
    "summary",
    "article_count",
    "threat_score",
    "severity_score",
    "credibility_score",
    "urgency_level",
    "keywords",
    "first_reported",
    "last_reported",
    "entities",
    "sources",
    "url",
    "source_count",
]

# Observed urgency levels (may evolve; treat as reference)
URGENCY_LEVELS: List[str] = [
    "low",
    "medium",
    "high",
    "critical",
    "unknown",
]

# Numeric columns that should be treated as scores
SCORE_COLUMNS: List[str] = [
    "threat_score",
    "severity_score",
    "credibility_score",
]


def validate_dataframe(
    df: pd.DataFrame,
    required: List[str] | None = None,
    raise_on_missing: bool = False,
) -> dict:
    """
    Lightweight schema validation.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to inspect.
    required : list of str, optional
        Columns that must be present. Defaults to a core subset.
    raise_on_missing : bool
        If True, raise ValueError when required columns are missing.

    Returns
    -------
    dict
        Validation report containing:
        - missing_columns
        - extra_columns
        - null_counts (for expected columns)
        - n_rows
        - is_valid
    """
    if required is None:
        required = [
            "cluster_id",
            "title",
            "summary",
            "urgency_level",
        ]

    present: Set[str] = set(df.columns)
    required_set: Set[str] = set(required)
    expected_set: Set[str] = set(EXPECTED_COLUMNS)

    missing = sorted(required_set - present)
    extra = sorted(present - expected_set)

    null_counts = {}
    for col in EXPECTED_COLUMNS:
        if col in df.columns:
            null_counts[col] = int(df[col].isna().sum())

    report = {
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "missing_columns": missing,
        "extra_columns": extra,
        "null_counts": null_counts,
        "is_valid": len(missing) == 0,
    }

    if raise_on_missing and missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            f"Available columns: {sorted(present)}"
        )

    return report
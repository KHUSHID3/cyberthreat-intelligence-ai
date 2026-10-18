"""
Dataset loading utilities.

IMPORTANT:
- The dataset is ALWAYS fetched via the Hugging Face `datasets` library.
- No static CSV / JSON download is performed.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from datasets import Dataset, load_dataset

from config import settings


def load_threatcluster_dataset(
    split: Optional[str] = None,
    streaming: bool = False,
) -> Dataset:
    """
    Load the ThreatCluster dataset from Hugging Face.

    Parameters
    ----------
    split : str, optional
        Dataset split to load. Defaults to settings.HF_DATASET_SPLIT.
    streaming : bool
        If True, return a streaming dataset (useful for very large data).

    Returns
    -------
    datasets.Dataset
    """
    split = split or settings.HF_DATASET_SPLIT

    ds = load_dataset(
        settings.HF_DATASET_NAME,
        split=split,
        streaming=streaming,
    )
    return ds


def dataset_to_dataframe(
    ds: Optional[Dataset] = None,
    split: Optional[str] = None,
    max_records: Optional[int] = None,
) -> pd.DataFrame:
    """
    Load the dataset (if needed) and convert it to a pandas DataFrame.

    Parameters
    ----------
    ds : Dataset, optional
        Pre-loaded dataset. If None, it will be loaded automatically.
    split : str, optional
        Split to load when ds is None.
    max_records : int, optional
        If provided, only the first `max_records` rows are returned.

    Returns
    -------
    pd.DataFrame
    """
    if ds is None:
        ds = load_threatcluster_dataset(split=split)

    df = ds.to_pandas()

    if max_records is not None and max_records > 0:
        df = df.head(max_records).copy()

    return df
"""
Text feature extraction helpers (TF-IDF / CountVectorizer).
No deep learning.
"""

from __future__ import annotations

from typing import List, Optional, Union

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from scipy.sparse import spmatrix


def build_tfidf_vectorizer(
    max_features: int = 15000,
    ngram_range: tuple = (1, 2),
    min_df: int = 3,
    max_df: float = 0.95,
    sublinear_tf: bool = True,
    stop_words: Optional[str] = "english",
) -> TfidfVectorizer:
    """Return a configured TfidfVectorizer."""
    return TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=sublinear_tf,
        stop_words=stop_words,
    )


def build_count_vectorizer(
    max_features: int = 15000,
    ngram_range: tuple = (1, 2),
    min_df: int = 3,
    max_df: float = 0.95,
    stop_words: Optional[str] = "english",
) -> CountVectorizer:
    """Return a configured CountVectorizer (Bag-of-Words)."""
    return CountVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        max_df=max_df,
        stop_words=stop_words,
    )


def transform_texts(
    vectorizer: Union[TfidfVectorizer, CountVectorizer],
    texts: List[str],
    fit: bool = False,
) -> spmatrix:
    """
    Fit (optional) and transform a list of texts.

    Parameters
    ----------
    vectorizer : TfidfVectorizer or CountVectorizer
    texts : list of str
    fit : bool
        If True, call fit_transform; otherwise transform only.
    """
    if fit:
        return vectorizer.fit_transform(texts)
    return vectorizer.transform(texts)
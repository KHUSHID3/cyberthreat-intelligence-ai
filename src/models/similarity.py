"""
Text similarity / retrieval using TF-IDF + cosine similarity.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import spmatrix

from src.features.text import build_tfidf_vectorizer
from src.data.cleaner import clean_text


class SimilarityIndex:
    """
    In-memory TF-IDF + cosine similarity index for incident retrieval.
    """

    def __init__(
        self,
        max_features: int = 10000,
        ngram_range: tuple = (1, 2),
    ):
        self.vectorizer = build_tfidf_vectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
        )
        self.matrix: Optional[spmatrix] = None
        self.documents: Optional[pd.DataFrame] = None
        self._fitted = False

    def fit(self, df: pd.DataFrame, text_column: str = "text") -> "SimilarityIndex":
        """
        Build the index from a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain the text_column and ideally cluster_id, title, etc.
        text_column : str
            Name of the column containing cleaned text.
        """
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in DataFrame")

        texts = df[text_column].fillna("").astype(str).tolist()
        self.matrix = self.vectorizer.fit_transform(texts)
        self.documents = df.reset_index(drop=True).copy()
        self._fitted = True
        return self

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        return_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Retrieve the most similar documents.

        Parameters
        ----------
        query_text : str
            Raw or cleaned query string.
        top_k : int
            Number of results to return.
        return_columns : list of str, optional
            Columns to include in the result. Defaults to a useful subset.

        Returns
        -------
        pd.DataFrame
            Top-k most similar rows with an extra 'similarity' column.
        """
        if not self._fitted or self.matrix is None or self.documents is None:
            raise RuntimeError("SimilarityIndex must be fitted before querying")

        cleaned = clean_text(query_text)
        q_vec = self.vectorizer.transform([cleaned])
        sims = cosine_similarity(q_vec, self.matrix).flatten()

        top_idx = np.argsort(sims)[::-1][:top_k]

        if return_columns is None:
            return_columns = [
                c for c in [
                    "cluster_id", "title", "urgency_level",
                    "threat_score", "severity_score", "url",
                ]
                if c in self.documents.columns
            ]

        result = self.documents.iloc[top_idx][return_columns].copy()
        result["similarity"] = sims[top_idx]
        result = result.reset_index(drop=True)
        return result

    def query_by_index(self, doc_index: int, top_k: int = 5) -> pd.DataFrame:
        """
        Find documents similar to an existing document in the index
        (useful for "similar to this incident" feature).
        """
        if not self._fitted or self.matrix is None:
            raise RuntimeError("SimilarityIndex must be fitted before querying")

        if doc_index < 0 or doc_index >= self.matrix.shape[0]:
            raise IndexError(f"doc_index {doc_index} out of range")

        q_vec = self.matrix[doc_index]
        sims = cosine_similarity(q_vec, self.matrix).flatten()
        # Exclude the document itself
        sims[doc_index] = -1.0

        top_idx = np.argsort(sims)[::-1][:top_k]
        return_columns = [
            c for c in [
                "cluster_id", "title", "urgency_level",
                "threat_score", "severity_score",
            ]
            if c in self.documents.columns
        ]
        result = self.documents.iloc[top_idx][return_columns].copy()
        result["similarity"] = sims[top_idx]
        return result.reset_index(drop=True)
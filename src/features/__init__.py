"""
Feature engineering utilities (classic ML / NLP only).
"""

from .text import (
    build_tfidf_vectorizer,
    build_count_vectorizer,
    transform_texts,
)
from .metadata import extract_metadata_features, METADATA_COLUMNS

__all__ = [
    "build_tfidf_vectorizer",
    "build_count_vectorizer",
    "transform_texts",
    "extract_metadata_features",
    "METADATA_COLUMNS",
]
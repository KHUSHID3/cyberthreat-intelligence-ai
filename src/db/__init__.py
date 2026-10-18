"""
MongoDB access layer (local Community Server only).
"""

from .connection import get_client, get_database, get_collection, check_connection
from .repositories import (
    IncidentRepository,
    PredictionRepository,
    ModelMetadataRepository,
    AnalysisResultsRepository,
)
from .indexes import ensure_indexes

__all__ = [
    "get_client",
    "get_database",
    "get_collection",
    "check_connection",
    "IncidentRepository",
    "PredictionRepository",
    "ModelMetadataRepository",
    "AnalysisResultsRepository",
    "ensure_indexes",
]
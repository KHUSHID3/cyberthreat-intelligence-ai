"""
MongoDB service facade for the Streamlit application.

Provides a single entry point for common database operations
used by the tabs, with graceful handling when MongoDB is down.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path when this file is run directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.connection import check_connection, get_database
from src.db.repositories import (
    IncidentRepository,
    PredictionRepository,
    ModelMetadataRepository,
    AnalysisResultsRepository,
)
from src.db.indexes import ensure_indexes
from config import settings


class MongoService:
    """
    High-level MongoDB operations for the UI layer.
    """

    def __init__(self):
        self._incident_repo: Optional[IncidentRepository] = None
        self._prediction_repo: Optional[PredictionRepository] = None
        self._meta_repo: Optional[ModelMetadataRepository] = None
        self._analysis_repo: Optional[AnalysisResultsRepository] = None

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------
    @property
    def is_available(self) -> bool:
        """Return True if MongoDB is reachable."""
        return check_connection()

    def ping(self) -> bool:
        return self.is_available

    # ------------------------------------------------------------------
    # Lazy repository accessors
    # ------------------------------------------------------------------
    @property
    def incidents(self) -> IncidentRepository:
        if self._incident_repo is None:
            self._incident_repo = IncidentRepository()
        return self._incident_repo

    @property
    def predictions(self) -> PredictionRepository:
        if self._prediction_repo is None:
            self._prediction_repo = PredictionRepository()
        return self._prediction_repo

    @property
    def model_metadata(self) -> ModelMetadataRepository:
        if self._meta_repo is None:
            self._meta_repo = ModelMetadataRepository()
        return self._meta_repo

    @property
    def analysis_results(self) -> AnalysisResultsRepository:
        if self._analysis_repo is None:
            self._analysis_repo = AnalysisResultsRepository()
        return self._analysis_repo

    # ------------------------------------------------------------------
    # Convenience methods used by multiple tabs
    # ------------------------------------------------------------------
    def get_incident_count(self) -> int:
        if not self.is_available:
            return 0
        return self.incidents.count()

    def get_prediction_count(self) -> int:
        if not self.is_available:
            return 0
        return self.predictions.count()

    def get_urgency_distribution(self) -> List[Dict[str, Any]]:
        if not self.is_available:
            return []
        return self.incidents.urgency_distribution()

    def get_recent_incidents(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.is_available:
            return []
        return self.incidents.find_many(
            sort=[("first_reported", -1)],
            limit=limit,
            projection={
                "cluster_id": 1,
                "title": 1,
                "urgency_level": 1,
                "threat_score": 1,
                "severity_score": 1,
                "first_reported": 1,
                "url": 1,
                "_id": 0,
            },
        )

    def search_incidents(
        self,
        text_query: Optional[str] = None,
        urgency: Optional[str] = None,
        min_threat_score: Optional[float] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        if not self.is_available:
            return []
        return self.incidents.search(
            text_query=text_query,
            urgency=urgency,
            min_threat_score=min_threat_score,
            skip=skip,
            limit=limit,
        )

    def get_latest_model_metadata(self) -> Optional[Dict[str, Any]]:
        if not self.is_available:
            return None
        return self.model_metadata.get_latest()

    def save_prediction(
        self,
        input_text: str,
        predicted_label: str,
        probabilities: Optional[Dict[str, float]] = None,
        model_version: str = "unknown",
        extra: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Persist a prediction. Returns inserted ID or None on failure.
        """
        if not self.is_available:
            return None
        try:
            return self.predictions.insert_prediction(
                input_text=input_text,
                predicted_label=predicted_label,
                probabilities=probabilities,
                model_version=model_version,
                extra=extra,
            )
        except Exception:
            return None

    def ensure_indexes(self) -> Optional[dict]:
        """Create recommended indexes (idempotent)."""
        if not self.is_available:
            return None
        try:
            return ensure_indexes()
        except Exception:
            return None

    def get_db_stats(self) -> Dict[str, Any]:
        """Return a small status summary for the dashboard."""
        if not self.is_available:
            return {
                "connected": False,
                "db_name": settings.MONGO_DB_NAME,
                "incident_count": 0,
                "prediction_count": 0,
            }

        return {
            "connected": True,
            "db_name": settings.MONGO_DB_NAME,
            "incident_count": self.get_incident_count(),
            "prediction_count": self.get_prediction_count(),
            "collections": get_database().list_collection_names(),
        }
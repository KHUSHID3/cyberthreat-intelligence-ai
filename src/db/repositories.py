"""
Repository classes for the four main collections.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, DESCENDING, UpdateOne
from pymongo.collection import Collection
from pymongo.results import BulkWriteResult, UpdateResult

from config import settings
from .connection import get_collection


class BaseRepository:
    """Common helpers for all repositories."""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._col: Optional[Collection] = None

    @property
    def col(self) -> Collection:
        if self._col is None:
            self._col = get_collection(self.collection_name)
        return self._col

    def count(self, query: Optional[Dict] = None) -> int:
        return self.col.count_documents(query or {})

    def find_one(self, query: Dict, projection: Optional[Dict] = None) -> Optional[Dict]:
        return self.col.find_one(query, projection)

    def find_many(
        self,
        query: Optional[Dict] = None,
        projection: Optional[Dict] = None,
        sort: Optional[List] = None,
        skip: int = 0,
        limit: int = 0,
    ) -> List[Dict]:
        cursor = self.col.find(query or {}, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)


class IncidentRepository(BaseRepository):
    """incidents collection."""

    def __init__(self):
        super().__init__(settings.COLLECTION_INCIDENTS)

    def upsert_one(self, document: Dict[str, Any]) -> UpdateResult:
        cluster_id = document.get("cluster_id")
        if not cluster_id:
            raise ValueError("document must contain cluster_id")
        return self.col.update_one(
            {"cluster_id": cluster_id},
            {"$set": document},
            upsert=True,
        )

    def bulk_upsert(self, documents: List[Dict[str, Any]]) -> BulkWriteResult:
        operations = []
        for doc in documents:
            cid = doc.get("cluster_id")
            if not cid:
                continue
            operations.append(
                UpdateOne(
                    {"cluster_id": cid},
                    {"$set": doc},
                    upsert=True,
                )
            )
        if not operations:
            raise ValueError("No valid documents to upsert")
        return self.col.bulk_write(operations, ordered=False)

    def get_by_cluster_id(self, cluster_id: str) -> Optional[Dict]:
        return self.find_one({"cluster_id": cluster_id})

    def search(
        self,
        text_query: Optional[str] = None,
        urgency: Optional[str] = None,
        min_threat_score: Optional[float] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict]:
        query: Dict[str, Any] = {}

        if urgency:
            query["urgency_level"] = urgency.lower().strip()

        if min_threat_score is not None:
            query["threat_score"] = {"$gte": min_threat_score}

        if text_query:
            # Prefer text index when available; fall back to regex
            query["$text"] = {"$search": text_query}

        sort = [("threat_score", DESCENDING), ("first_reported", DESCENDING)]
        return self.find_many(query=query, sort=sort, skip=skip, limit=limit)

    def urgency_distribution(self) -> List[Dict]:
        pipeline = [
            {"$group": {"_id": "$urgency_level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        return list(self.col.aggregate(pipeline))


class PredictionRepository(BaseRepository):
    """predictions collection."""

    def __init__(self):
        super().__init__(settings.COLLECTION_PREDICTIONS)

    def insert_prediction(
        self,
        input_text: str,
        predicted_label: str,
        probabilities: Optional[Dict[str, float]] = None,
        model_version: str = "unknown",
        extra: Optional[Dict] = None,
    ) -> str:
        doc = {
            "input_text": input_text,
            "predicted_label": predicted_label,
            "probabilities": probabilities or {},
            "model_version": model_version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if extra:
            doc.update(extra)

        result = self.col.insert_one(doc)
        return str(result.inserted_id)

    def recent(self, limit: int = 50, model_version: Optional[str] = None) -> List[Dict]:
        query = {}
        if model_version:
            query["model_version"] = model_version
        return self.find_many(
            query=query,
            sort=[("timestamp", DESCENDING)],
            limit=limit,
        )


class ModelMetadataRepository(BaseRepository):
    """model_metadata collection."""

    def __init__(self):
        super().__init__(settings.COLLECTION_MODEL_METADATA)

    def upsert_metadata(self, version: str, metadata: Dict[str, Any]) -> UpdateResult:
        metadata = dict(metadata)
        metadata["version"] = version
        metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
        return self.col.update_one(
            {"version": version},
            {"$set": metadata},
            upsert=True,
        )

    def get_latest(self) -> Optional[Dict]:
        return self.col.find_one(sort=[("created_at", DESCENDING)])

    def get_by_version(self, version: str) -> Optional[Dict]:
        return self.find_one({"version": version})


class AnalysisResultsRepository(BaseRepository):
    """analysis_results collection (optional aggregates)."""

    def __init__(self):
        super().__init__(settings.COLLECTION_ANALYSIS_RESULTS)

    def save_result(
        self,
        analysis_type: str,
        payload: Dict[str, Any],
        version: Optional[str] = None,
    ) -> str:
        doc = {
            "analysis_type": analysis_type,
            "payload": payload,
            "version": version,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        result = self.col.insert_one(doc)
        return str(result.inserted_id)

    def get_latest_by_type(self, analysis_type: str) -> Optional[Dict]:
        return self.col.find_one(
            {"analysis_type": analysis_type},
            sort=[("created_at", DESCENDING)],
        )
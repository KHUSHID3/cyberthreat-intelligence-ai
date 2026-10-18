"""
Index creation helpers (idempotent).
"""

from __future__ import annotations

from pymongo import ASCENDING, DESCENDING, TEXT

from config import settings
from .connection import get_database


def ensure_indexes() -> dict:
    """
    Create all recommended indexes.
    Safe to call multiple times.

    Returns
    -------
    dict
        Summary of indexes created / existing per collection.
    """
    db = get_database()
    summary = {}

    # incidents
    incidents = db[settings.COLLECTION_INCIDENTS]
    incidents.create_index([("cluster_id", ASCENDING)], unique=True, name="idx_cluster_id_unique")
    incidents.create_index([("urgency_level", ASCENDING)], name="idx_urgency_level")
    incidents.create_index([("first_reported", DESCENDING)], name="idx_first_reported_desc")
    incidents.create_index([("last_reported", DESCENDING)], name="idx_last_reported_desc")
    incidents.create_index([("threat_score", DESCENDING)], name="idx_threat_score_desc")
    incidents.create_index([("severity_score", DESCENDING)], name="idx_severity_score_desc")
    incidents.create_index(
        [("urgency_level", ASCENDING), ("first_reported", DESCENDING)],
        name="idx_urgency_first_reported",
    )
    try:
        incidents.create_index(
            [("title", TEXT), ("summary", TEXT), ("text", TEXT)],
            name="idx_text_search",
            default_language="english",
        )
    except Exception:
        pass  # text index may already exist with different options

    summary["incidents"] = [idx["name"] for idx in incidents.list_indexes()]

    # predictions
    predictions = db[settings.COLLECTION_PREDICTIONS]
    predictions.create_index([("timestamp", DESCENDING)], name="idx_timestamp_desc")
    predictions.create_index([("model_version", ASCENDING)], name="idx_model_version")
    predictions.create_index(
        [("model_version", ASCENDING), ("timestamp", DESCENDING)],
        name="idx_model_version_timestamp",
    )
    summary["predictions"] = [idx["name"] for idx in predictions.list_indexes()]

    # model_metadata
    model_meta = db[settings.COLLECTION_MODEL_METADATA]
    model_meta.create_index([("version", ASCENDING)], unique=True, name="idx_version_unique")
    model_meta.create_index([("created_at", DESCENDING)], name="idx_created_at_desc")
    summary["model_metadata"] = [idx["name"] for idx in model_meta.list_indexes()]

    # analysis_results

    analysis = db[settings.COLLECTION_ANALYSIS_RESULTS]
    analysis.create_index([("analysis_type", ASCENDING)], name="idx_analysis_type")
    analysis.create_index([("created_at", DESCENDING)], name="idx_created_at_desc")
    summary["analysis_results"] = [idx["name"] for idx in analysis.list_indexes()]

    return summary
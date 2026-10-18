"""
Create recommended indexes for the cyberthreat_intelligence_ai MongoDB collections.

Safe to run multiple times (idempotent).
Handles existing indexes that may have been created with default names.
Local MongoDB Community Server only.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings


def get_mongo_client():
    try:
        from pymongo import MongoClient
        client = MongoClient(**settings.get_mongo_client_kwargs())
        client.admin.command("ping")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"[ERROR] Cannot connect to MongoDB at {settings.MONGO_URI}")
        print(f"        {e}")
        sys.exit(1)


def _index_exists(collection, keys) -> bool:
    """Return True if an index with the same key pattern already exists."""
    desired = list(keys)
    for idx in collection.list_indexes():
        existing = list(idx["key"].items())
        if existing == desired:
            return True
    return False


def _safe_create_index(collection, keys, **kwargs):
    """
    Create an index only if an equivalent one does not already exist.
    Swallows IndexOptionsConflict / equivalent-index errors.
    """
    name = kwargs.get("name", str(keys))
    if _index_exists(collection, keys):
        print(f"  ✓ {name} (already exists)")
        return

    try:
        collection.create_index(keys, **kwargs)
        print(f"  ✓ {name}")
    except OperationFailure as e:
        # 85 = IndexOptionsConflict, 86 = IndexKeySpecsConflict
        if e.code in (85, 86):
            print(f"  ✓ {name} (equivalent index already present)")
        else:
            print(f"  ⚠ {name} failed: {e}")
    except Exception as e:
        print(f"  ⚠ {name} failed: {e}")


def create_indexes() -> None:
    print("=" * 70)
    print("Creating indexes for cyberthreat_intelligence_ai")
    print("=" * 70)
    print(f"MongoDB URI : {settings.MONGO_URI}")
    print(f"Database    : {settings.MONGO_DB_NAME}")
    print()

    client = get_mongo_client()
    db = client[settings.MONGO_DB_NAME]

    # incidents
    incidents = db[settings.COLLECTION_INCIDENTS]
    print(f"→ {settings.COLLECTION_INCIDENTS}")

    _safe_create_index(
        incidents,
        [("cluster_id", ASCENDING)],
        unique=True,
        name="idx_cluster_id_unique",
    )
    _safe_create_index(
        incidents,
        [("urgency_level", ASCENDING)],
        name="idx_urgency_level",
    )
    _safe_create_index(
        incidents,
        [("first_reported", DESCENDING)],
        name="idx_first_reported_desc",
    )
    _safe_create_index(
        incidents,
        [("last_reported", DESCENDING)],
        name="idx_last_reported_desc",
    )
    _safe_create_index(
        incidents,
        [("threat_score", DESCENDING)],
        name="idx_threat_score_desc",
    )
    _safe_create_index(
        incidents,
        [("severity_score", DESCENDING)],
        name="idx_severity_score_desc",
    )
    _safe_create_index(
        incidents,
        [("urgency_level", ASCENDING), ("first_reported", DESCENDING)],
        name="idx_urgency_first_reported",
    )

    # Text index (special handling)
    try:
        if not _index_exists(incidents, [("title", "text"), ("summary", "text"), ("text", "text")]):
            # Also check for any existing text index
            has_text = any(idx.get("textIndexVersion") for idx in incidents.list_indexes())
            if not has_text:
                incidents.create_index(
                    [("title", TEXT), ("summary", TEXT), ("text", TEXT)],
                    name="idx_text_search",
                    default_language="english",
                )
                print("  ✓ idx_text_search")
            else:
                print("  ✓ idx_text_search (text index already present)")
        else:
            print("  ✓ idx_text_search (already exists)")
    except Exception as e:
        print(f"  ⚠ text index skipped: {e}")

    # predictions
    predictions = db[settings.COLLECTION_PREDICTIONS]
    print(f"\n→ {settings.COLLECTION_PREDICTIONS}")

    _safe_create_index(
        predictions,
        [("timestamp", DESCENDING)],
        name="idx_timestamp_desc",
    )
    _safe_create_index(
        predictions,
        [("model_version", ASCENDING)],
        name="idx_model_version",
    )
    _safe_create_index(
        predictions,
        [("model_version", ASCENDING), ("timestamp", DESCENDING)],
        name="idx_model_version_timestamp",
    )

    # model_metadata
    model_meta = db[settings.COLLECTION_MODEL_METADATA]
    print(f"\n→ {settings.COLLECTION_MODEL_METADATA}")

    _safe_create_index(
        model_meta,
        [("version", ASCENDING)],
        unique=True,
        name="idx_version_unique",
    )
    _safe_create_index(
        model_meta,
        [("created_at", DESCENDING)],
        name="idx_created_at_desc",
    )

    # analysis_results
    analysis = db[settings.COLLECTION_ANALYSIS_RESULTS]
    print(f"\n→ {settings.COLLECTION_ANALYSIS_RESULTS}")

    _safe_create_index(
        analysis,
        [("analysis_type", ASCENDING)],
        name="idx_analysis_type",
    )
    _safe_create_index(
        analysis,
        [("created_at", DESCENDING)],
        name="idx_created_at_desc",
    )

    print("\n" + "=" * 70)
    print("INDEX CREATION COMPLETE")
    print("=" * 70)

    print("\nCurrent indexes on incidents:")
    for idx in incidents.list_indexes():
        print(f"  - {idx['name']}: {dict(idx['key'])}")

    client.close()


if __name__ == "__main__":
    create_indexes()
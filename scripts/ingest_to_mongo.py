"""
Repeatable batch ingestion of ThreatCluster incident data into local MongoDB.

- Dataset is ALWAYS fetched via Hugging Face `datasets` library (never static file)
- Local MongoDB Community Server only (no Atlas)
- Safe upserts on cluster_id
- Batch processing with progress bar
- Idempotent: can be run multiple times safely
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from datasets import load_dataset
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError, ConnectionFailure, ServerSelectionTimeoutError
from tqdm import tqdm

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings


def utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 string with Z suffix (timezone-aware)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clean_text(text: Any) -> str:
    """Basic text normalization (mirrors notebook logic)."""
    if not isinstance(text, str):
        return ""
    import re
    text = text.lower().strip()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s\-\.]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def row_to_document(row: pd.Series) -> Dict[str, Any]:
    """Convert a DataFrame row into a clean MongoDB document."""
    title = row.get("title", "") or ""
    summary = row.get("summary", "") or ""

    title_clean = clean_text(title)
    summary_clean = clean_text(summary)
    text = f"{title_clean} {summary_clean}".strip()

    def safe_float(val):
        try:
            return float(val) if pd.notna(val) else None
        except (TypeError, ValueError):
            return None

    def safe_int(val):
        try:
            return int(val) if pd.notna(val) else None
        except (TypeError, ValueError):
            return None

    def safe_list(val):
        if isinstance(val, list):
            return val
        return []

    def safe_dict(val):
        if isinstance(val, dict):
            return val
        return {}

    def safe_iso(val):
        if pd.isna(val):
            return None
        try:
            return pd.to_datetime(val).isoformat()
        except Exception:
            return None

    doc = {
        "cluster_id": str(row.get("cluster_id", "")),
        "title": title,
        "summary": summary,
        "title_clean": title_clean,
        "summary_clean": summary_clean,
        "text": text,
        "urgency_level": str(row.get("urgency_level", "")).lower().strip() or None,
        "threat_score": safe_float(row.get("threat_score")),
        "severity_score": safe_float(row.get("severity_score")),
        "credibility_score": safe_float(row.get("credibility_score")),
        "article_count": safe_int(row.get("article_count")),
        "source_count": safe_int(row.get("source_count")),
        "keywords": safe_list(row.get("keywords")),
        "entities": safe_dict(row.get("entities")),
        "sources": safe_list(row.get("sources")),
        "url": row.get("url"),
        "first_reported": safe_iso(row.get("first_reported")),
        "last_reported": safe_iso(row.get("last_reported")),
        "ingested_at": utc_now_iso(),
    }
    return doc


def get_mongo_client() -> MongoClient:
    """Create a MongoDB client using project settings."""
    try:
        client = MongoClient(**settings.get_mongo_client_kwargs())
        # Force a quick ping
        client.admin.command("ping")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"[ERROR] Cannot connect to MongoDB at {settings.MONGO_URI}")
        print(f"        {e}")
        print("        Make sure MongoDB Community Server is running locally.")
        sys.exit(1)


def ingest(
    batch_size: int = 500,
    max_records: int | None = None,
    drop_existing: bool = False,
) -> None:
    """Main ingestion routine."""
    print("=" * 70)
    print("ThreatCluster → Local MongoDB Ingestion")
    print("=" * 70)
    print(f"Dataset     : {settings.HF_DATASET_NAME}")
    print(f"MongoDB URI : {settings.MONGO_URI}")
    print(f"Database    : {settings.MONGO_DB_NAME}")
    print(f"Collection  : {settings.COLLECTION_INCIDENTS}")
    print(f"Batch size  : {batch_size}")
    if max_records:
        print(f"Max records : {max_records}")
    print()

    # 1. Load dataset from Hugging Face
    print("Loading dataset from Hugging Face (this may take a moment)...")
    ds = load_dataset(settings.HF_DATASET_NAME, split=settings.HF_DATASET_SPLIT)
    df = ds.to_pandas()

    if max_records is not None and max_records > 0:
        df = df.head(max_records)

    print(f"Loaded {len(df):,} records")

    # Basic cleaning filter
    df["title"] = df["title"].fillna("")
    df["summary"] = df["summary"].fillna("")
    df = df[df["cluster_id"].notna()].copy()
    print(f"Records with valid cluster_id: {len(df):,}")

    # 2. Connect to MongoDB
    client = get_mongo_client()
    db = client[settings.MONGO_DB_NAME]
    collection = db[settings.COLLECTION_INCIDENTS]

    if drop_existing:
        print("Dropping existing collection...")
        collection.drop()
        print("Collection dropped.")

    # Ensure unique index on cluster_id
    collection.create_index("cluster_id", unique=True)
    print("Unique index on cluster_id ensured.")

    # 3. Batch upsert
    total = len(df)
    upserted = 0
    modified = 0
    errors = 0

    print(f"\nStarting batch upsert of {total:,} documents...")

    for start in tqdm(range(0, total, batch_size), desc="Ingesting", unit="batch"):
        end = min(start + batch_size, total)
        batch_df = df.iloc[start:end]

        operations: List[UpdateOne] = []
        for _, row in batch_df.iterrows():
            doc = row_to_document(row)
            if not doc["cluster_id"]:
                continue
            operations.append(
                UpdateOne(
                    {"cluster_id": doc["cluster_id"]},
                    {"$set": doc},
                    upsert=True,
                )
            )

        if not operations:
            continue

        try:
            result = collection.bulk_write(operations, ordered=False)
            upserted += result.upserted_count
            modified += result.modified_count
        except BulkWriteError as bwe:
            # Partial success is still useful
            upserted += bwe.details.get("nUpserted", 0)
            modified += bwe.details.get("nModified", 0)
            errors += len(bwe.details.get("writeErrors", []))
            print(
                f"\n[WARN] BulkWriteError in batch {start}-{end}: "
                f"{len(bwe.details.get('writeErrors', []))} errors"
            )

    # ------------------------------------------------------------------
    # 4. Summary
    # ------------------------------------------------------------------
    final_count = collection.count_documents({})
    print("\n" + "=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)
    print(f"Upserted (new) : {upserted:,}")
    print(f"Modified       : {modified:,}")
    print(f"Write errors   : {errors:,}")
    print(f"Total in DB    : {final_count:,}")
    print("=" * 70)

    client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Ingest ThreatCluster dataset into local MongoDB (idempotent upserts)."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of documents per bulk write (default: 500)",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Limit number of records to ingest (useful for testing)",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop the incidents collection before ingesting (destructive)",
    )
    args = parser.parse_args()

    ingest(
        batch_size=args.batch_size,
        max_records=args.max_records,
        drop_existing=args.drop,
    )


if __name__ == "__main__":
    main()
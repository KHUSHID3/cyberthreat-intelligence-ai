"""
MongoDB connection helpers.

Strictly local MongoDB Community Server (no Atlas).
"""

from __future__ import annotations

from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from config import settings

# Module-level client (lazy)
_client: Optional[MongoClient] = None


def get_client(force_new: bool = False) -> MongoClient:
    """
    Return a shared MongoClient instance.

    Parameters
    ----------
    force_new : bool
        If True, create a new client even if one already exists.
    """
    global _client

    if _client is None or force_new:
        _client = MongoClient(**settings.get_mongo_client_kwargs())

    return _client


def get_database(db_name: Optional[str] = None) -> Database:
    """Return the configured database."""
    client = get_client()
    return client[db_name or settings.MONGO_DB_NAME]


def get_collection(name: str, db_name: Optional[str] = None) -> Collection:
    """Return a collection by name."""
    db = get_database(db_name)
    return db[name]


def check_connection(timeout_ms: int = 3000) -> bool:
    """
    Ping MongoDB and return True if reachable.

    Returns
    -------
    bool
    """
    try:
        client = get_client()
        client.admin.command("ping")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False
    except Exception:
        return False


def close_connection() -> None:
    """Close the shared client (mainly for clean shutdown)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
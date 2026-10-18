"""
Application settings for cyberthreat_intelligence_ai.

- Loads configuration from environment variables (.env)
- Local MongoDB Community Server only (no Atlas)
- Central place for collection names, artifact paths, and constants
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root (one level above config/)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class Settings:
    """Central configuration object."""

    # Project paths

    PROJECT_ROOT: Path = _PROJECT_ROOT
    ARTIFACTS_DIR: Path = PROJECT_ROOT / os.getenv("ARTIFACTS_DIR", "artifacts")
    MODELS_DIR: Path = PROJECT_ROOT / os.getenv("MODELS_DIR", "artifacts/models")
    VECTORIZERS_DIR: Path = PROJECT_ROOT / os.getenv(
        "VECTORIZERS_DIR", "artifacts/vectorizers"
    )
    METADATA_DIR: Path = PROJECT_ROOT / os.getenv("METADATA_DIR", "artifacts/metadata")

    # MongoDB (local Community Server only)

    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "cyberthreat_intelligence_ai")

    MONGO_USERNAME: Optional[str] = os.getenv("MONGO_USERNAME") or None
    MONGO_PASSWORD: Optional[str] = os.getenv("MONGO_PASSWORD") or None
    MONGO_AUTH_SOURCE: str = os.getenv("MONGO_AUTH_SOURCE", "admin")

    # Collection names
    COLLECTION_INCIDENTS: str = "incidents"
    COLLECTION_PREDICTIONS: str = "predictions"
    COLLECTION_MODEL_METADATA: str = "model_metadata"
    COLLECTION_ANALYSIS_RESULTS: str = "analysis_results"

    # Application

    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Dataset (always fetched via Hugging Face datasets library)

    HF_DATASET_NAME: str = "threatcluster/threat-incident-clusters"
    HF_DATASET_SPLIT: str = "train"  # adjust if multiple splits appear later

    # Model / Artifact defaults

    DEFAULT_MODEL_VERSION: str = "v1"
    RANDOM_STATE: int = 42
    TEST_SIZE: float = 0.2
    VALIDATION_SIZE: float = 0.1

    # Helpers

    @classmethod
    def ensure_directories(cls) -> None:
        """Create artifact directories if they do not exist."""
        for path in (
            cls.ARTIFACTS_DIR,
            cls.MODELS_DIR,
            cls.VECTORIZERS_DIR,
            cls.METADATA_DIR,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_mongo_client_kwargs(cls) -> dict:
        """
        Return kwargs suitable for pymongo.MongoClient.
        Only includes auth parameters when username/password are provided.
        """
        kwargs = {
            "host": cls.MONGO_URI,
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 5000,
        }
        if cls.MONGO_USERNAME and cls.MONGO_PASSWORD:
            kwargs.update(
                {
                    "username": cls.MONGO_USERNAME,
                    "password": cls.MONGO_PASSWORD,
                    "authSource": cls.MONGO_AUTH_SOURCE,
                }
            )
        return kwargs


# Singleton instance used across the project
settings = Settings()

# Ensure directories exist at import time (safe for both notebook & Streamlit)
settings.ensure_directories()
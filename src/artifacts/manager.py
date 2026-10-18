"""
Save and load versioned model artifacts (joblib + JSON metadata).

Artifacts are stored under the directories defined in config.settings:
- models/
- vectorizers/
- metadata/
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import joblib

from config import settings


class ArtifactManager:
    """
    Handles versioned persistence of sklearn models, vectorizers and metadata.
    """

    def __init__(
        self,
        models_dir: Optional[Path] = None,
        vectorizers_dir: Optional[Path] = None,
        metadata_dir: Optional[Path] = None,
    ):
        self.models_dir = Path(models_dir or settings.MODELS_DIR)
        self.vectorizers_dir = Path(vectorizers_dir or settings.VECTORIZERS_DIR)
        self.metadata_dir = Path(metadata_dir or settings.METADATA_DIR)

        # Ensure directories exist
        for d in (self.models_dir, self.vectorizers_dir, self.metadata_dir):
            d.mkdir(parents=True, exist_ok=True)

    # Version helpers
    @staticmethod
    def make_version(prefix: str = "v1") -> str:
        """Return a timestamped version string, e.g. v1_20261015_143022."""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{ts}"

    # Save
    def save_model(self, model: Any, version: str, name: str = "urgency_model") -> Path:
        """Serialize a fitted model with joblib."""
        path = self.models_dir / f"{name}_{version}.joblib"
        joblib.dump(model, path)
        return path

    def save_vectorizer(self, vectorizer: Any, version: str, name: str = "tfidf_vectorizer") -> Path:
        """Serialize a fitted vectorizer with joblib."""
        path = self.vectorizers_dir / f"{name}_{version}.joblib"
        joblib.dump(vectorizer, path)
        return path

    def save_metadata(self, metadata: Dict[str, Any], version: str, name: str = "model_meta") -> Path:
        """Save metadata as pretty-printed JSON."""
        metadata = dict(metadata)
        metadata.setdefault("version", version)
        metadata.setdefault("saved_at", datetime.utcnow().isoformat() + "Z")

        path = self.metadata_dir / f"{name}_{version}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, default=str)
        return path

    def save_all(
        self,
        model: Any,
        vectorizer: Any,
        metadata: Dict[str, Any],
        version: Optional[str] = None,
        model_name: str = "urgency_model",
        vectorizer_name: str = "tfidf_vectorizer",
    ) -> Dict[str, Path]:
        """
        Save model + vectorizer + metadata under the same version.

        Returns
        -------
        dict with keys: version, model, vectorizer, metadata
        """
        version = version or self.make_version()

        model_path = self.save_model(model, version, name=model_name)
        vec_path = self.save_vectorizer(vectorizer, version, name=vectorizer_name)
        meta_path = self.save_metadata(metadata, version)

        return {
            "version": version,
            "model": model_path,
            "vectorizer": vec_path,
            "metadata": meta_path,
        }

    # Load
    def load_model(self, path: Union[str, Path]) -> Any:
        """Load a joblib model from an explicit path."""
        return joblib.load(path)

    def load_vectorizer(self, path: Union[str, Path]) -> Any:
        """Load a joblib vectorizer from an explicit path."""
        return joblib.load(path)

    def load_metadata(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Load metadata JSON."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def find_latest(
        self,
        model_name: str = "urgency_model",
        vectorizer_name: str = "tfidf_vectorizer",
        meta_name: str = "model_meta",
    ) -> Optional[Dict[str, Path]]:
        """
        Locate the most recent matching set of artifacts by filename timestamp.

        Returns
        -------
        dict with keys version, model, vectorizer, metadata  or  None
        """
        model_files = sorted(self.models_dir.glob(f"{model_name}_*.joblib"), reverse=True)
        if not model_files:
            return None

        latest_model = model_files[0]
        # Extract version part: urgency_model_v1_20261015_143022.joblib → v1_20261015_143022
        version = latest_model.stem.replace(f"{model_name}_", "", 1)

        vec_path = self.vectorizers_dir / f"{vectorizer_name}_{version}.joblib"
        meta_path = self.metadata_dir / f"{meta_name}_{version}.json"

        if not vec_path.exists() or not meta_path.exists():
            # Incomplete set – still return what we have
            return {
                "version": version,
                "model": latest_model,
                "vectorizer": vec_path if vec_path.exists() else None,
                "metadata": meta_path if meta_path.exists() else None,
            }

        return {
            "version": version,
            "model": latest_model,
            "vectorizer": vec_path,
            "metadata": meta_path,
        }

    def load_latest(
        self,
        model_name: str = "urgency_model",
        vectorizer_name: str = "tfidf_vectorizer",
    ) -> Optional[Tuple[Any, Any, Dict[str, Any]]]:
        """
        Convenience method: load the latest model, vectorizer and metadata.

        Returns
        -------
        (model, vectorizer, metadata) or None if nothing found
        """
        info = self.find_latest(model_name=model_name, vectorizer_name=vectorizer_name)
        if info is None or info.get("model") is None:
            return None

        model = self.load_model(info["model"])
        vectorizer = self.load_vectorizer(info["vectorizer"]) if info.get("vectorizer") else None
        metadata = self.load_metadata(info["metadata"]) if info.get("metadata") else {}

        return model, vectorizer, metadata
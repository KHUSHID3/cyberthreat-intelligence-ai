"""
Model inference service for the Streamlit application.

Loads versioned artifacts (model + vectorizer) if present and
exposes a simple predict() API. Degrades gracefully when artifacts
are missing.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Ensure project root is on sys.path when this file is run directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.artifacts.manager import ArtifactManager
from src.data.cleaner import clean_text
from config import settings


class InferenceService:
    """
    Handles loading of the latest model artifacts and running inference.
    """

    def __init__(self):
        self._manager = ArtifactManager()
        self._model = None
        self._vectorizer = None
        self._metadata: Dict[str, Any] = {}
        self._loaded = False
        self._load_error: Optional[str] = None

    # Loading
    def load(self, force: bool = False) -> bool:
        """
        Attempt to load the latest model + vectorizer + metadata.

        Returns
        -------
        bool
            True if artifacts were loaded successfully.
        """
        if self._loaded and not force:
            return True

        result = self._manager.load_latest()
        if result is None:
            self._model = None
            self._vectorizer = None
            self._metadata = {}
            self._loaded = False
            self._load_error = "No model artifacts found"
            return False

        model, vectorizer, metadata = result
        if model is None or vectorizer is None:
            self._load_error = "Incomplete artifact set (model or vectorizer missing)"
            self._loaded = False
            return False

        self._model = model
        self._vectorizer = vectorizer
        self._metadata = metadata or {}
        self._loaded = True
        self._load_error = None
        return True

    @property
    def is_ready(self) -> bool:
        """True when a model is loaded and ready for inference."""
        if not self._loaded:
            self.load()
        return self._loaded and self._model is not None and self._vectorizer is not None

    @property
    def metadata(self) -> Dict[str, Any]:
        if not self._loaded:
            self.load()
        return self._metadata

    @property
    def version(self) -> str:
        return self.metadata.get("version", "unknown")

    @property
    def classes(self) -> List[str]:
        return list(self.metadata.get("classes") or [])

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    # Inference
    def predict(
        self,
        title: str = "",
        summary: str = "",
        text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run urgency prediction on the provided text.

        Parameters
        ----------
        title : str
        summary : str
        text : str, optional
            If provided, used directly instead of title+summary.

        Returns
        -------
        dict with keys:
            - success: bool
            - label: str | None
            - probabilities: dict[str, float]
            - version: str
            - error: str | None
        """
        if not self.is_ready:
            return {
                "success": False,
                "label": None,
                "probabilities": {},
                "version": self.version,
                "error": self._load_error or "Model not available",
            }

        if text is None:
            text = clean_text(title) + " " + clean_text(summary)
        text = text.strip()

        if len(text) < 10:
            return {
                "success": False,
                "label": None,
                "probabilities": {},
                "version": self.version,
                "error": "Input text too short after cleaning",
            }

        try:
            X = self._vectorizer.transform([text])
            pred_idx = int(self._model.predict(X)[0])

            classes = self.classes
            label = classes[pred_idx] if classes and pred_idx < len(classes) else str(pred_idx)

            probabilities: Dict[str, float] = {}
            if hasattr(self._model, "predict_proba"):
                proba = self._model.predict_proba(X)[0]
                if classes and len(classes) == len(proba):
                    probabilities = {
                        cls: float(p) for cls, p in zip(classes, proba)
                    }
                else:
                    probabilities = {
                        str(i): float(p) for i, p in enumerate(proba)
                    }
            elif hasattr(self._model, "decision_function"):
                # Best-effort conversion for LinearSVC-style models
                decision = self._model.decision_function(X)[0]
                decision = np.atleast_1d(decision)
                exp_d = np.exp(decision - np.max(decision))
                proba = exp_d / exp_d.sum()
                if classes and len(classes) == len(proba):
                    probabilities = {
                        cls: float(p) for cls, p in zip(classes, proba)
                    }

            return {
                "success": True,
                "label": label,
                "probabilities": probabilities,
                "version": self.version,
                "error": None,
                "input_text": text[:2000],
            }

        except Exception as e:
            return {
                "success": False,
                "label": None,
                "probabilities": {},
                "version": self.version,
                "error": str(e),
            }

    def get_status(self) -> Dict[str, Any]:
        """Return a status summary suitable for the UI."""
        ready = self.is_ready
        return {
            "ready": ready,
            "version": self.version if ready else None,
            "model_type": self.metadata.get("model_type") if ready else None,
            "classes": self.classes if ready else [],
            "error": self._load_error,
            "artifacts_dir": str(settings.MODELS_DIR),
        }
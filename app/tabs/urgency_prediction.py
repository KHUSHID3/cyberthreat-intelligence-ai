"""
Tab 4 — Urgency Prediction
Accept incident title/summary and display selected model output + probabilities.
"""

from __future__ import annotations

import streamlit as st
import numpy as np
from pathlib import Path

from src.db.connection import check_connection
from src.db.repositories import PredictionRepository, ModelMetadataRepository
from src.artifacts.manager import ArtifactManager
from src.data.cleaner import clean_text
from config import settings


def _load_artifacts():
    """Try to load the latest model + vectorizer. Return (model, vectorizer, meta) or None."""
    manager = ArtifactManager()
    result = manager.load_latest()
    return result  # (model, vectorizer, metadata) or None


def render_urgency_prediction() -> None:
    st.header("Urgency Prediction")
    st.caption(
        "Estimate urgency level from incident title and summary. "
        "Predictions reflect patterns in the training data, not verified real-world severity."
    )

    # Load model
    artifacts = _load_artifacts()

    if artifacts is None:
        st.warning(
            "No trained model artifacts found.\n\n"
            "Run the research notebook to train a model and export artifacts, "
            "then refresh this page."
        )
        st.info(f"Expected location: `{settings.MODELS_DIR}`")
        return

    model, vectorizer, metadata = artifacts
    version = metadata.get("version", "unknown")
    classes = metadata.get("classes", [])
    model_type = metadata.get("model_type", "unknown")

    st.success(f"Loaded model **{version}** ({model_type})")

    # Input form
    with st.form("prediction_form"):
        title = st.text_input("Incident title", placeholder="e.g. Critical Ransomware Attack on Healthcare Provider")
        summary = st.text_area(
            "Incident summary",
            height=150,
            placeholder="Paste or type a short description of the incident...",
        )
        submitted = st.form_submit_button("Predict Urgency", type="primary")

    if not submitted:
        st.markdown("---")
        st.subheader("Model Information")
        st.json({
            "version": version,
            "model_type": model_type,
            "classes": classes,
            "metrics": metadata.get("metrics"),
        })
        return

    if not title.strip() and not summary.strip():
        st.error("Please provide at least a title or a summary.")
        return

    # Inference
    text = clean_text(title) + " " + clean_text(summary)
    text = text.strip()

    if len(text) < 10:
        st.error("Combined text is too short after cleaning. Please provide more content.")
        return

    try:
        X = vectorizer.transform([text])
        pred_idx = model.predict(X)[0]

        # Probabilities (if available)
        proba = None
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
        elif hasattr(model, "decision_function"):
            # Fallback for LinearSVC-like models
            decision = model.decision_function(X)[0]
            if decision.ndim == 0:
                decision = np.array([decision])
            # Softmax-ish normalization for display only
            exp_d = np.exp(decision - np.max(decision))
            proba = exp_d / exp_d.sum()

        label = classes[pred_idx] if classes and pred_idx < len(classes) else str(pred_idx)

        st.subheader("Prediction Result")
        st.markdown(f"### Predicted Urgency: `{label}`")

        if proba is not None and classes:
            proba_dict = {cls: float(p) for cls, p in zip(classes, proba)}
            st.write("Class probabilities:")
            proba_df = (
                pd.DataFrame.from_dict(proba_dict, orient="index", columns=["probability"])
                .sort_values("probability", ascending=False)
            )
            st.bar_chart(proba_df)
            st.dataframe(proba_df.style.format("{:.3f}"), use_container_width=True)
        else:
            proba_dict = {}
            st.info("Probability estimates are not available for this model type.")

        # Persist prediction (optional, only if MongoDB is up)
        if check_connection():
            try:
                pred_repo = PredictionRepository()
                pred_repo.insert_prediction(
                    input_text=text[:2000],
                    predicted_label=label,
                    probabilities=proba_dict,
                    model_version=version,
                    extra={"title": title, "summary": summary[:1000]},
                )
                st.caption("Prediction saved to history.")
            except Exception as e:
                st.caption(f"Could not save prediction: {e}")

    except Exception as e:
        st.error(f"Inference failed: {e}")
        st.exception(e)


# pandas is required for the probability table
import pandas as pd
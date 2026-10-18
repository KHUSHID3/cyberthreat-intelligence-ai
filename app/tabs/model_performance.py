"""
Tab 9 — Model Performance
Display saved metrics, per-class results, confusion matrix, model version.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from src.db.connection import check_connection
from src.db.repositories import ModelMetadataRepository
from src.artifacts.manager import ArtifactManager
from config import settings


def render_model_performance() -> None:
    st.header("Model Performance")
    st.caption("Evaluation metrics and metadata of the currently selected model artifacts.")

    # Try MongoDB metadata first, then fall back to local JSON
    meta = None
    source = None

    if check_connection():
        repo = ModelMetadataRepository()
        meta = repo.get_latest()
        if meta:
            source = "MongoDB"

    if meta is None:
        manager = ArtifactManager()
        latest = manager.find_latest()
        if latest and latest.get("metadata"):
            try:
                meta = manager.load_metadata(latest["metadata"])
                source = "local artifact file"
            except Exception:
                meta = None

    if meta is None:
        st.warning(
            "No model metadata found.\n\n"
            "Train and export a model from the research notebook, "
            "or ensure model_metadata collection / artifacts/metadata is populated."
        )
        st.info(f"Artifact directory: `{settings.METADATA_DIR}`")
        return

    st.success(f"Loaded metadata from **{source}**")

    # Overview
    c1, c2, c3 = st.columns(3)
    c1.metric("Version", meta.get("version", "n/a"))
    c2.metric("Model type", meta.get("model_type", "n/a"))
    c3.metric("Target", meta.get("target", "n/a"))

    st.markdown(f"**Created at:** {meta.get('created_at', meta.get('saved_at', 'n/a'))}")
    st.markdown(f"**Dataset:** {meta.get('dataset', 'n/a')}")

    # Aggregate metrics
    metrics = meta.get("metrics") or {}
    if metrics:
        st.subheader("Aggregate Metrics")
        cols = st.columns(4)
        cols[0].metric("Accuracy", f"{metrics.get('accuracy', 0):.4f}")
        cols[1].metric("Balanced Acc", f"{metrics.get('balanced_accuracy', metrics.get('balanced_acc', 0)):.4f}")
        cols[2].metric("Macro F1", f"{metrics.get('macro_f1', 0):.4f}")
        cols[3].metric("Weighted F1", f"{metrics.get('weighted_f1', 0):.4f}")

    # Per-class report
    report = metrics.get("classification_report") or meta.get("classification_report")
    if report and isinstance(report, dict):
        st.subheader("Per-class Metrics")
        rows = []
        for label, vals in report.items():
            if isinstance(vals, dict) and "precision" in vals:
                rows.append({
                    "class": label,
                    "precision": vals.get("precision"),
                    "recall": vals.get("recall"),
                    "f1-score": vals.get("f1-score"),
                    "support": vals.get("support"),
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Confusion matrix
    cm = metrics.get("confusion_matrix") or meta.get("confusion_matrix")
    classes = meta.get("classes") or []
    if cm and isinstance(cm, list):
        st.subheader("Confusion Matrix")
        cm_arr = np.array(cm)
        fig = px.imshow(
            cm_arr,
            text_auto=True,
            labels=dict(x="Predicted", y="True", color="Count"),
            x=classes if classes else None,
            y=classes if classes else None,
            color_continuous_scale="Blues",
            title="Confusion Matrix",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Raw metadata
    with st.expander("Raw metadata JSON"):
        st.json(meta)
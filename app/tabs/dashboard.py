"""
Tab 1 — Dashboard
Incident totals, urgency distribution, recent activity, source coverage,
database status, and key summaries.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from src.db.connection import check_connection
from src.db.repositories import IncidentRepository, PredictionRepository, ModelMetadataRepository
from config import settings


def render_dashboard() -> None:
    st.header("Dashboard")
    st.caption("High-level overview of stored incident intelligence and system status.")

    # Database health
    db_ok = check_connection()
    col1, col2, col3 = st.columns(3)

    with col1:
        if db_ok:
            st.success("MongoDB: Connected")
        else:
            st.error("MongoDB: Unavailable")
            st.info("Start local MongoDB Community Server and run the ingestion script.")
            return

    incident_repo = IncidentRepository()
    prediction_repo = PredictionRepository()
    meta_repo = ModelMetadataRepository()

    total_incidents = incident_repo.count()
    total_predictions = prediction_repo.count()
    latest_meta = meta_repo.get_latest()

    with col2:
        st.metric("Incidents in DB", f"{total_incidents:,}")
    with col3:
        st.metric("Stored Predictions", f"{total_predictions:,}")

    if total_incidents == 0:
        st.warning("No incidents found. Run `python scripts/ingest_to_mongo.py` first.")
        return

    # Urgency distribution
    st.subheader("Urgency Level Distribution")
    dist = incident_repo.urgency_distribution()
    if dist:
        dist_df = pd.DataFrame(dist).rename(columns={"_id": "urgency_level", "count": "count"})
        dist_df = dist_df.dropna(subset=["urgency_level"])
        fig = px.bar(
            dist_df,
            x="urgency_level",
            y="count",
            color="urgency_level",
            title="Incidents by Urgency Level",
            labels={"urgency_level": "Urgency", "count": "Count"},
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No urgency data available.")

    # Recent incidents
    st.subheader("Recent Incidents")
    recent = incident_repo.find_many(
        sort=[("first_reported", -1)],
        limit=10,
        projection={
            "cluster_id": 1,
            "title": 1,
            "urgency_level": 1,
            "threat_score": 1,
            "first_reported": 1,
            "_id": 0,
        },
    )
    if recent:
        recent_df = pd.DataFrame(recent)
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
    else:
        st.info("No recent incidents to display.")

    # Model status
    st.subheader("Model Status")
    if latest_meta:
        st.json({
            "version": latest_meta.get("version"),
            "model_type": latest_meta.get("model_type"),
            "target": latest_meta.get("target"),
            "created_at": latest_meta.get("created_at"),
            "metrics": latest_meta.get("metrics"),
        })
    else:
        st.info(
            "No model metadata found in MongoDB. "
            "Train a model in the research notebook and save artifacts."
        )
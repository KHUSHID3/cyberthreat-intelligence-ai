"""
Tab 3 — Incident Explorer
Paginated incident records with filters for dates, labels, sources, scores, entities.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime

from src.db.connection import check_connection
from src.db.repositories import IncidentRepository
from src.utils.helpers import truncate_text


def render_explorer() -> None:
    st.header("Incident Explorer")
    st.caption("Browse and filter stored incident records with pagination.")

    if not check_connection():
        st.error("MongoDB is unavailable.")
        return

    repo = IncidentRepository()
    total = repo.count()
    if total == 0:
        st.warning("No incidents available. Run the ingestion script first.")
        return

    # Filters
    with st.expander("Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            urgency = st.multiselect(
                "Urgency level",
                options=["low", "medium", "high", "critical", "unknown"],
            )
        with c2:
            min_threat = st.number_input("Min threat score", 0.0, 100.0, 0.0, 1.0)
        with c3:
            min_severity = st.number_input("Min severity score", 0.0, 100.0, 0.0, 1.0)

        page_size = st.selectbox("Page size", [10, 20, 50, 100], index=1)

    # Build query
    query = {}
    if urgency:
        query["urgency_level"] = {"$in": urgency}
    if min_threat > 0:
        query["threat_score"] = {"$gte": min_threat}
    if min_severity > 0:
        query.setdefault("severity_score", {})
        query["severity_score"]["$gte"] = min_severity

    filtered_total = repo.count(query)
    st.write(f"Showing **{filtered_total:,}** matching incidents (of {total:,} total)")

    if filtered_total == 0:
        st.info("No incidents match the current filters.")
        return

    # Pagination
    max_page = max(1, (filtered_total + page_size - 1) // page_size)
    page = st.number_input("Page", min_value=1, max_value=max_page, value=1, step=1)
    skip = (page - 1) * page_size

    results = repo.find_many(
        query=query,
        sort=[("first_reported", -1)],
        skip=skip,
        limit=page_size,
        projection={
            "cluster_id": 1,
            "title": 1,
            "summary": 1,
            "urgency_level": 1,
            "threat_score": 1,
            "severity_score": 1,
            "article_count": 1,
            "source_count": 1,
            "first_reported": 1,
            "last_reported": 1,
            "keywords": 1,
            "url": 1,
            "_id": 0,
        },
    )

    st.caption(f"Page {page} of {max_page}")

    for doc in results:
        title = truncate_text(doc.get("title", "Untitled"), 100)
        with st.container():
            st.markdown(f"### {title}")
            meta_cols = st.columns(5)
            meta_cols[0].write(f"**ID:** `{doc.get('cluster_id', 'n/a')}`")
            meta_cols[1].write(f"**Urgency:** {doc.get('urgency_level', 'n/a')}")
            meta_cols[2].write(f"**Threat:** {doc.get('threat_score', 'n/a')}")
            meta_cols[3].write(f"**Severity:** {doc.get('severity_score', 'n/a')}")
            meta_cols[4].write(f"**Articles:** {doc.get('article_count', 'n/a')}")

            st.write(truncate_text(doc.get("summary", ""), 400))

            if doc.get("keywords"):
                st.caption("Keywords: " + ", ".join(doc["keywords"][:8]))

            if doc.get("url"):
                st.markdown(f"[View source]({doc['url']})")

            st.divider()
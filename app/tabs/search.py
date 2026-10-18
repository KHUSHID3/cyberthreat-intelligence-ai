"""
Tab 2 — Incident Intelligence Search
Search by keyword, entity, identifier, or incident description.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src.db.connection import check_connection
from src.db.repositories import IncidentRepository
from src.utils.helpers import truncate_text


def render_search() -> None:
    st.header("Incident Intelligence Search")
    st.caption("Search stored incidents by keyword, cluster ID, urgency, or free-text description.")

    if not check_connection():
        st.error("MongoDB is unavailable. Please start the local MongoDB server.")
        return

    repo = IncidentRepository()
    total = repo.count()
    if total == 0:
        st.warning("No incidents in the database. Run the ingestion script first.")
        return

    st.write(f"Searching across **{total:,}** stored incidents.")

    # Search controls
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Search query",
            placeholder="e.g. ransomware, CVE-2026, mikrotik, cluster_id...",
        )
    with col2:
        urgency_filter = st.selectbox(
            "Urgency filter",
            options=["(any)", "low", "medium", "high", "critical", "unknown"],
            index=0,
        )

    min_score = st.slider("Minimum threat score", 0.0, 100.0, 0.0, 1.0)
    top_k = st.slider("Max results", 5, 100, 20, 5)

    if st.button("Search", type="primary") or query:
        urgency = None if urgency_filter == "(any)" else urgency_filter

        # Prefer MongoDB text index when a query is provided
        results = repo.search(
            text_query=query.strip() if query else None,
            urgency=urgency,
            min_threat_score=min_score if min_score > 0 else None,
            limit=top_k,
        )

        # Fallback: simple regex / field search if text index returns nothing
        if not results and query:
            regex = {"$regex": query.strip(), "$options": "i"}
            fallback_query = {
                "$or": [
                    {"title": regex},
                    {"summary": regex},
                    {"text": regex},
                    {"cluster_id": query.strip()},
                    {"keywords": query.strip().lower()},
                ]
            }
            if urgency:
                fallback_query["urgency_level"] = urgency
            if min_score > 0:
                fallback_query["threat_score"] = {"$gte": min_score}

            results = repo.find_many(
                query=fallback_query,
                sort=[("threat_score", -1)],
                limit=top_k,
                projection={
                    "cluster_id": 1,
                    "title": 1,
                    "summary": 1,
                    "urgency_level": 1,
                    "threat_score": 1,
                    "severity_score": 1,
                    "first_reported": 1,
                    "url": 1,
                    "_id": 0,
                },
            )

        if not results:
            st.info("No matching incidents found.")
            return

        st.success(f"Found {len(results)} result(s)")

        for doc in results:
            with st.expander(
                f"{doc.get('cluster_id', 'N/A')} — {truncate_text(doc.get('title', ''), 90)}"
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("Urgency", doc.get("urgency_level", "n/a"))
                c2.metric("Threat Score", f"{doc.get('threat_score', 'n/a')}")
                c3.metric("Severity", f"{doc.get('severity_score', 'n/a')}")

                st.markdown("**Summary**")
                st.write(doc.get("summary") or "No summary available.")

                if doc.get("url"):
                    st.markdown(f"[Open on ThreatCluster]({doc['url']})")

                st.caption(f"First reported: {doc.get('first_reported', 'n/a')}")
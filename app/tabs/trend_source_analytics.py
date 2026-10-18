"""
Tab 7 — Trend & Source Analytics
Temporal patterns, source coverage, score distributions.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from src.db.connection import check_connection
from src.db.repositories import IncidentRepository


def render_trend_source_analytics() -> None:
    st.header("Trend & Source Analytics")
    st.caption("Temporal trends, source coverage, and score distributions from stored incidents.")

    if not check_connection():
        st.error("MongoDB is unavailable.")
        return

    repo = IncidentRepository()
    total = repo.count()
    if total == 0:
        st.warning("No incidents available.")
        return

    max_docs = st.slider("Documents to analyse", 500, 15000, 5000, 500)
    docs = repo.find_many(
        limit=max_docs,
        projection={
            "first_reported": 1,
            "last_reported": 1,
            "urgency_level": 1,
            "threat_score": 1,
            "severity_score": 1,
            "credibility_score": 1,
            "source_count": 1,
            "article_count": 1,
            "sources": 1,
            "_id": 0,
        },
    )

    df = pd.DataFrame(docs)
    if df.empty:
        st.info("No data returned.")
        return

    # Parse dates
    for col in ("first_reported", "last_reported"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    st.write(f"Analysing **{len(df):,}** incidents")

    # Temporal trend
    st.subheader("Incidents over Time")
    if "first_reported" in df.columns and df["first_reported"].notna().any():
        ts = (
            df.dropna(subset=["first_reported"])
            .set_index("first_reported")
            .resample("W")
            .size()
            .reset_index(name="count")
        )
        fig = px.line(ts, x="first_reported", y="count", title="Weekly Incident Volume")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No usable first_reported dates.")

    # Score distributions
    st.subheader("Score Distributions")
    score_cols = [c for c in ["threat_score", "severity_score", "credibility_score"] if c in df.columns]
    if score_cols:
        cols = st.columns(len(score_cols))
        for col, name in zip(cols, score_cols):
            with col:
                fig = px.histogram(df, x=name, nbins=30, title=name.replace("_", " ").title())
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No score columns available.")

    # Source coverage
    st.subheader("Source Coverage")
    if "sources" in df.columns:
        source_counter = Counter()
        for srcs in df["sources"].dropna():
            if isinstance(srcs, list):
                source_counter.update([str(s).strip() for s in srcs if s])

        if source_counter:
            top_sources = source_counter.most_common(20)
            src_df = pd.DataFrame(top_sources, columns=["source", "count"])
            fig = px.bar(src_df, x="count", y="source", orientation="h", title="Top Sources")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source lists found.")
    else:
        st.info("sources field not present.")

    # Urgency vs Threat Score
    st.subheader("Urgency vs Threat Score")
    if "urgency_level" in df.columns and "threat_score" in df.columns:
        fig = px.box(
            df.dropna(subset=["urgency_level", "threat_score"]),
            x="urgency_level",
            y="threat_score",
            title="Threat Score by Urgency Level",
        )
        st.plotly_chart(fig, use_container_width=True)


# Counter is used above
from collections import Counter
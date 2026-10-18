"""
Tab 5 — Similar Incident Finder
Retrieve textually related records with similarity scores.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src.db.connection import check_connection
from src.db.repositories import IncidentRepository
from src.models.similarity import SimilarityIndex
from src.data.cleaner import clean_text
from src.utils.helpers import truncate_text


@st.cache_resource(show_spinner="Building similarity index...")
def _build_similarity_index(max_docs: int = 5000) -> SimilarityIndex | None:
    """Build (and cache) a TF-IDF similarity index from MongoDB incidents."""
    if not check_connection():
        return None

    repo = IncidentRepository()
    total = repo.count()
    if total == 0:
        return None

    # Pull a reasonable subset for in-memory index
    docs = repo.find_many(
        sort=[("first_reported", -1)],
        limit=min(max_docs, total),
        projection={
            "cluster_id": 1,
            "title": 1,
            "summary": 1,
            "text": 1,
            "urgency_level": 1,
            "threat_score": 1,
            "severity_score": 1,
            "url": 1,
            "_id": 0,
        },
    )
    if not docs:
        return None

    df = pd.DataFrame(docs)
    if "text" not in df.columns or df["text"].str.len().sum() == 0:
        # Fallback: rebuild text on the fly
        df["text"] = (
            df.get("title", "").fillna("").map(clean_text)
            + " "
            + df.get("summary", "").fillna("").map(clean_text)
        ).str.strip()

    index = SimilarityIndex(max_features=8000)
    index.fit(df, text_column="text")
    return index


def render_similar_incidents() -> None:
    st.header("Similar Incident Finder")
    st.caption(
        "Find incidents whose descriptions are textually similar to a query or to a selected incident. "
        "Similarity does not prove shared actor, campaign, or root cause."
    )

    if not check_connection():
        st.error("MongoDB is unavailable.")
        return

    index = _build_similarity_index()
    if index is None:
        st.warning("No incidents available to build a similarity index. Run ingestion first.")
        return

    st.success(f"Similarity index ready ({len(index.documents):,} documents)")

    mode = st.radio(
        "Search mode",
        options=["Free-text query", "Similar to existing incident"],
        horizontal=True,
    )

    top_k = st.slider("Number of results", 3, 20, 8)

    if mode == "Free-text query":
        query = st.text_area(
            "Describe the incident or paste a title/summary",
            height=120,
            placeholder="e.g. ransomware attack targeting healthcare providers with data exfiltration",
        )
        if st.button("Find Similar", type="primary") and query.strip():
            results = index.query(query, top_k=top_k)
            _display_results(results)
    else:
        # Let user pick from recent incidents
        repo = IncidentRepository()
        recent = repo.find_many(
            sort=[("first_reported", -1)],
            limit=50,
            projection={"cluster_id": 1, "title": 1, "_id": 0},
        )
        if not recent:
            st.info("No incidents available.")
            return

        options = {
            f"{d['cluster_id']} — {truncate_text(d.get('title', ''), 70)}": d["cluster_id"]
            for d in recent
        }
        selected_label = st.selectbox("Select an incident", list(options.keys()))
        selected_id = options[selected_label]

        if st.button("Find Similar", type="primary"):
            # Locate the document index inside the similarity index
            matches = index.documents.index[
                index.documents["cluster_id"] == selected_id
            ].tolist()
            if not matches:
                st.warning("Selected incident is not present in the current index.")
                return
            results = index.query_by_index(matches[0], top_k=top_k)
            _display_results(results)


def _display_results(results: pd.DataFrame) -> None:
    if results is None or results.empty:
        st.info("No similar incidents found.")
        return

    st.subheader(f"Top {len(results)} similar incidents")
    for _, row in results.iterrows():
        with st.expander(
            f"{row.get('cluster_id', 'n/a')} — {truncate_text(str(row.get('title', '')), 90)} "
            f"(sim={row.get('similarity', 0):.3f})"
        ):
            c1, c2, c3 = st.columns(3)
            c1.metric("Similarity", f"{row.get('similarity', 0):.3f}")
            c2.metric("Urgency", row.get("urgency_level", "n/a"))
            c3.metric("Threat Score", row.get("threat_score", "n/a"))
            if row.get("url"):
                st.markdown(f"[Open source]({row['url']})")
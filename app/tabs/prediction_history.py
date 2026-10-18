"""
Tab 8 — Prediction History
Search / paginate stored predictions.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src.db.connection import check_connection
from src.db.repositories import PredictionRepository
from src.utils.helpers import truncate_text


def render_prediction_history() -> None:
    st.header("Prediction History")
    st.caption("Previously submitted urgency predictions stored in MongoDB.")

    if not check_connection():
        st.error("MongoDB is unavailable.")
        return

    repo = PredictionRepository()
    total = repo.count()
    if total == 0:
        st.info(
            "No predictions stored yet. "
            "Make predictions in the Urgency Prediction tab to populate history."
        )
        return

    st.write(f"Total stored predictions: **{total:,}**")

    # Filters
    c1, c2 = st.columns(2)
    with c1:
        model_version = st.text_input("Filter by model version (optional)")
    with c2:
        page_size = st.selectbox("Page size", [10, 20, 50], index=1)

    query = {}
    if model_version.strip():
        query["model_version"] = model_version.strip()

    filtered_total = repo.count(query)
    max_page = max(1, (filtered_total + page_size - 1) // page_size)
    page = st.number_input("Page", 1, max_page, 1)
    skip = (page - 1) * page_size

    results = repo.find_many(
        query=query,
        sort=[("timestamp", -1)],
        skip=skip,
        limit=page_size,
    )

    st.caption(f"Page {page} of {max_page} ({filtered_total} matching)")

    if not results:
        st.info("No predictions match the current filter.")
        return

    for doc in results:
        with st.expander(
            f"{doc.get('timestamp', 'n/a')} — {doc.get('predicted_label', 'n/a')} "
            f"(model: {doc.get('model_version', 'n/a')})"
        ):
            st.markdown("**Input text**")
            st.write(truncate_text(doc.get("input_text", ""), 500))

            st.markdown("**Predicted label**")
            st.code(doc.get("predicted_label", "n/a"))

            probs = doc.get("probabilities") or {}
            if probs:
                st.markdown("**Probabilities**")
                prob_df = (
                    pd.DataFrame.from_dict(probs, orient="index", columns=["probability"])
                    .sort_values("probability", ascending=False)
                )
                st.dataframe(prob_df.style.format("{:.3f}"), use_container_width=True)
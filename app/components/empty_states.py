"""
Consistent empty-state and error messages used across tabs.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from config import settings


def show_db_unavailable(extra_message: Optional[str] = None) -> None:
    """MongoDB is not reachable."""
    st.error("MongoDB is unavailable.")
    st.info(
        "Please ensure MongoDB Community Server is running locally "
        f"({settings.MONGO_URI}) and that the connection settings in `.env` are correct."
    )
    if extra_message:
        st.caption(extra_message)


def show_no_data(
    entity: str = "incidents",
    action_hint: str = "Run `python scripts/ingest_to_mongo.py` to load data.",
) -> None:
    """Collection is empty."""
    st.warning(f"No {entity} found in the database.")
    st.info(action_hint)


def show_no_model(
    extra_message: Optional[str] = None,
) -> None:
    """No trained model artifacts available."""
    st.warning("No trained model artifacts found.")
    st.info(
        "Run the research notebook to train a model and export artifacts, "
        "then refresh this page.\n\n"
        f"Expected location: `{settings.MODELS_DIR}`"
    )
    if extra_message:
        st.caption(extra_message)


def show_no_results(context: str = "your query") -> None:
    """Search / filter returned nothing."""
    st.info(f"No results matched {context}.")


def show_error(message: str, exception: Optional[Exception] = None) -> None:
    """Generic error display."""
    st.error(message)
    if exception is not None:
        with st.expander("Technical details"):
            st.exception(exception)
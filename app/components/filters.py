"""
Reusable filter widgets for Streamlit tabs.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import streamlit as st


def urgency_filter(
    label: str = "Urgency level",
    include_any: bool = True,
    key: Optional[str] = None,
) -> Optional[List[str]]:
    """
    Multi-select urgency filter.

    Returns
    -------
    list of selected urgency strings, or None if "(any)" / nothing selected.
    """
    options = ["low", "medium", "high", "critical", "unknown"]
    if include_any:
        display_options = ["(any)"] + options
        default = ["(any)"]
    else:
        display_options = options
        default = []

    selected = st.multiselect(
        label,
        options=display_options,
        default=default,
        key=key,
    )

    if not selected or "(any)" in selected:
        return None
    return selected


def score_range_filter(
    label: str = "Threat score range",
    min_value: float = 0.0,
    max_value: float = 100.0,
    default: Tuple[float, float] = (0.0, 100.0),
    key: Optional[str] = None,
) -> Tuple[float, float]:
    """
    Double-ended slider for score filtering.
    Returns (min_score, max_score).
    """
    return st.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        value=default,
        step=1.0,
        key=key,
    )


def page_size_selector(
    label: str = "Page size",
    options: Optional[List[int]] = None,
    default_index: int = 1,
    key: Optional[str] = None,
) -> int:
    """
    Standard page-size selector.
    """
    options = options or [10, 20, 50, 100]
    return st.selectbox(label, options=options, index=default_index, key=key)


def simple_text_search(
    label: str = "Search",
    placeholder: str = "Enter keywords...",
    key: Optional[str] = None,
) -> str:
    """
    Single-line text search input.
    """
    return st.text_input(label, placeholder=placeholder, key=key).strip()
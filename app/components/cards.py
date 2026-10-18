"""
Small reusable visual cards for the Streamlit UI.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from src.utils.helpers import truncate_text


def metric_card(
    label: str,
    value: Any,
    delta: Optional[str] = None,
    help_text: Optional[str] = None,
) -> None:
    """
    Display a single metric in a clean card-like layout.
    Wrapper around st.metric with consistent defaults.
    """
    st.metric(label=label, value=value, delta=delta, help=help_text)


def info_card(
    title: str,
    body: str,
    icon: str = "ℹ️",
    expanded: bool = False,
) -> None:
    """
    Simple informational expander / card.
    """
    with st.expander(f"{icon} {title}", expanded=expanded):
        st.markdown(body)


def incident_card(
    doc: Dict[str, Any],
    show_summary: bool = True,
    summary_max_len: int = 350,
) -> None:
    """
    Render a compact incident summary card.

    Expected keys (all optional):
    - cluster_id, title, summary, urgency_level,
      threat_score, severity_score, url, first_reported
    """
    title = truncate_text(doc.get("title") or "Untitled incident", 110)
    cluster_id = doc.get("cluster_id", "n/a")

    with st.container():
        st.markdown(f"#### {title}")

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**ID:** `{cluster_id}`")
        c2.markdown(f"**Urgency:** {doc.get('urgency_level', 'n/a')}")
        c3.markdown(f"**Threat:** {doc.get('threat_score', 'n/a')}")
        c4.markdown(f"**Severity:** {doc.get('severity_score', 'n/a')}")

        if show_summary and doc.get("summary"):
            st.write(truncate_text(doc["summary"], summary_max_len))

        meta_parts = []
        if doc.get("first_reported"):
            meta_parts.append(f"First reported: {doc['first_reported']}")
        if doc.get("url"):
            meta_parts.append(f"[Source]({doc['url']})")

        if meta_parts:
            st.caption(" · ".join(meta_parts))

        st.divider()
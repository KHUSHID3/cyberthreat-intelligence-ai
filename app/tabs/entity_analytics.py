"""
Tab 6 — Threat Entity Analytics
Explore frequent entities and co-occurrence patterns.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

import streamlit as st
import pandas as pd
import plotly.express as px

from src.db.connection import check_connection
from src.db.repositories import IncidentRepository
from src.utils.helpers import safe_get


def render_entity_analytics() -> None:
    st.header("Threat Entity Analytics")
    st.caption("Frequent entities extracted from incident records and simple co-occurrence patterns.")

    if not check_connection():
        st.error("MongoDB is unavailable.")
        return

    repo = IncidentRepository()
    total = repo.count()
    if total == 0:
        st.warning("No incidents available.")
        return

    # Pull a working set
    max_docs = st.slider("Documents to analyse", 500, 10000, 3000, 500)
    docs = repo.find_many(
        limit=max_docs,
        projection={"entities": 1, "keywords": 1, "urgency_level": 1, "_id": 0},
    )

    if not docs:
        st.info("No documents returned.")
        return

    st.write(f"Analysing **{len(docs):,}** incidents")

    # ------------------------------------------------------------------
    # Entity frequency by type
    # ------------------------------------------------------------------
    entity_counters = {
        "cve": Counter(),
        "malware": Counter(),
        "company": Counter(),
        "country": Counter(),
        "attack_type": Counter(),
        "mitre_attack": Counter(),
        "platform": Counter(),
    }

    keyword_counter = Counter()

    for doc in docs:
        entities = doc.get("entities") or {}
        if isinstance(entities, dict):
            for etype in entity_counters:
                values = entities.get(etype) or []
                if isinstance(values, list):
                    entity_counters[etype].update([str(v).strip() for v in values if v])

        kws = doc.get("keywords") or []
        if isinstance(kws, list):
            keyword_counter.update([str(k).lower().strip() for k in kws if k])

    # Display top entities
    st.subheader("Top Entities by Type")
    tabs = st.tabs(list(entity_counters.keys()) + ["keywords"])

    for tab, etype in zip(tabs, list(entity_counters.keys()) + ["keywords"]):
        with tab:
            counter = entity_counters.get(etype, keyword_counter)
            if not counter:
                st.info(f"No {etype} entities found in the sample.")
                continue
            top = counter.most_common(25)
            df = pd.DataFrame(top, columns=["entity", "count"])
            fig = px.bar(df, x="count", y="entity", orientation="h", title=f"Top {etype}")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

    # Simple co-occurrence (CVEs appearing together)
    st.subheader("CVE Co-occurrence (pairs)")
    cve_pairs = Counter()
    for doc in docs:
        cves = safe_get(doc, "entities", "cve", default=[])
        if isinstance(cves, list) and len(cves) >= 2:
            clean = sorted({str(c).strip() for c in cves if c})
            for a, b in combinations(clean, 2):
                cve_pairs[(a, b)] += 1

    if cve_pairs:
        pair_df = pd.DataFrame(
            [(a, b, cnt) for (a, b), cnt in cve_pairs.most_common(20)],
            columns=["cve_1", "cve_2", "count"],
        )
        st.dataframe(pair_df, use_container_width=True, hide_index=True)
    else:
        st.info("Not enough multi-CVE incidents to compute co-occurrence.")
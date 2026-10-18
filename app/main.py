"""
Streamlit entry point — Cyber Threat Intelligence & Incident Analytics.

Run with:
    streamlit run app/main.py

The app never executes the research notebook and never trains models on startup.
It only reads from local MongoDB and from previously exported artifacts.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so "src" and "config" imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from config import settings

# Tab renderers
from app.tabs.dashboard import render_dashboard
from app.tabs.search import render_search
from app.tabs.explorer import render_explorer
from app.tabs.urgency_prediction import render_urgency_prediction
from app.tabs.similar_incidents import render_similar_incidents
from app.tabs.entity_analytics import render_entity_analytics
from app.tabs.trend_source_analytics import render_trend_source_analytics
from app.tabs.prediction_history import render_prediction_history
from app.tabs.model_performance import render_model_performance
from app.tabs.about import render_about


def _configure_page() -> None:
    st.set_page_config(
        page_title="Cyber Threat Intelligence AI",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _render_sidebar() -> None:
    with st.sidebar:
        st.title(" Threat Analytics")
        st.caption("Defensive Cyber Threat Intelligence")
        st.markdown("---")
        st.markdown(
            """
**Project**  
`cyberthreat_intelligence_ai`

**Stack**  
Python · scikit-learn · PyMongo · Streamlit

**Database**  
Local MongoDB Community Server
"""
        )
        st.markdown("---")
        st.caption(f"Env: `{settings.APP_ENV}`")
        st.caption(f"DB: `{settings.MONGO_DB_NAME}`")
        st.markdown(
            """
<div style="font-size:0.8rem;color:#888;">
Predictions are estimates of dataset label patterns,
not verified real-world severity assessments.
</div>
""",
            unsafe_allow_html=True,
        )


def main() -> None:
    _configure_page()
    _render_sidebar()

    st.title("Cyber Threat Intelligence & Incident Analytics")
    st.caption(
        "Explore threat-incident clusters, search related reports, "
        "and review model-generated urgency estimates."
    )

    # ------------------------------------------------------------------
    # Ten primary tabs (required by project specification)
    # ------------------------------------------------------------------
    (
        tab_dashboard,
        tab_search,
        tab_explorer,
        tab_urgency,
        tab_similar,
        tab_entities,
        tab_trends,
        tab_history,
        tab_performance,
        tab_about,
    ) = st.tabs([
        "Dashboard",
        "Incident Search",
        "Incident Explorer",
        "Urgency Prediction",
        "Similar Incidents",
        "Entity Analytics",
        "Trend & Source Analytics",
        "Prediction History",
        "Model Performance",
        "About & Methodology",
    ])

    with tab_dashboard:
        render_dashboard()

    with tab_search:
        render_search()

    with tab_explorer:
        render_explorer()

    with tab_urgency:
        render_urgency_prediction()

    with tab_similar:
        render_similar_incidents()

    with tab_entities:
        render_entity_analytics()

    with tab_trends:
        render_trend_source_analytics()

    with tab_history:
        render_prediction_history()

    with tab_performance:
        render_model_performance()

    with tab_about:
        render_about()


if __name__ == "__main__":
    main()
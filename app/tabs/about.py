"""
Tab 10 — About, Dataset & Methodology
Project scope, dataset attribution, data dictionary, methodology,
limitations, and responsible-use guidance.
"""

from __future__ import annotations

import streamlit as st

from config import settings


def render_about() -> None:
    st.header("About, Dataset & Methodology")
    st.caption("Project scope, data provenance, methodology, and responsible-use guidance.")

    st.markdown("""
### Project Overview

**cyberthreat_intelligence_ai** is a defensive, educational cyber-threat-intelligence analytics project.

It organises incident intelligence from the ThreatCluster dataset, learns patterns from labelled
incident records using classic machine-learning / NLP techniques, and provides interactive
exploration tools. Predictions are estimates of dataset label patterns — **not** verified
real-world severity assessments.
""")

    st.markdown("""
### Dataset

| Item | Value |
|------|-------|
| Name | ThreatCluster — Threat Incident Clusters |
| Source | [Hugging Face – threatcluster/threat-incident-clusters](https://huggingface.co/datasets/threatcluster/threat-incident-clusters) |
| Access method | Always fetched via the `datasets` library (never stored as a static project file) |
| License | CC-BY-4.0 (confirm current license on the dataset card before redistribution) |

**Key fields used**
- `cluster_id`, `title`, `summary`
- `urgency_level` (prediction target)
- `threat_score`, `severity_score`, `credibility_score`
- `keywords`, `entities`, `sources`
- `first_reported`, `last_reported`
""")

    st.markdown("""
### Methodology (Summary)

1. **Data loading** — Hugging Face `datasets` → pandas  
2. **Cleaning** — text normalisation, missing-value handling, rare-class filtering  
3. **Feature engineering** — TF-IDF / Bag-of-Words representations  
4. **Modelling** — at least seven classic ML/NLP approaches evaluated:
   - Logistic Regression + TF-IDF
   - Linear SVC + TF-IDF
   - Multinomial Naive Bayes + TF-IDF
   - Random Forest + TF-IDF
   - HistGradientBoosting + TF-IDF
   - K-Nearest Neighbours (cosine) + TF-IDF
   - Logistic Regression + CountVectorizer (BoW)
5. **Evaluation** — precision, recall, F1, balanced accuracy, confusion matrix  
6. **Persistence** — local MongoDB (Community Server) via PyMongo  
7. **Interface** — independent Streamlit application (10 tabs)
""")

    st.markdown("""
### Technology Stack

- Python, pandas, NumPy, scikit-learn  
- Hugging Face `datasets`  
- MongoDB Community Server + PyMongo  
- Streamlit + Plotly  
- Jupyter Notebook (research only)
""")

    st.markdown("""
### Responsible Use & Limitations

- This is **defensive, educational** analytics — not an autonomous response system.
- A model’s predicted urgency is an estimate of the dataset’s label pattern, **not** a verified real-world severity assessment.
- Treat generated summaries, extracted entities, and source metadata as data requiring validation.
- Text similarity does **not** prove that two incidents share an actor, campaign, or root cause.
- Do **not** use this project to generate exploits, collect credentials, or take actions against third-party systems.
- Always confirm the current dataset license and attribution requirements before any redistribution.
""")

    st.markdown("""
### Project Links

- GitHub repository: [https://github.com/ArshiBansal/cyberthreat_intelligence_ai](https://github.com/ArshiBansal/cyberthreat_intelligence_ai)
- Dataset: [https://huggingface.co/datasets/threatcluster/threat-incident-clusters](https://huggingface.co/datasets/threatcluster/threat-incident-clusters)
""")

    st.markdown(f"""
### Runtime Configuration

| Setting | Value |
|---------|-------|
| MongoDB URI | `{settings.MONGO_URI}` |
| Database | `{settings.MONGO_DB_NAME}` |
| Artifacts directory | `{settings.ARTIFACTS_DIR}` |
""")

    st.info(
        "For full experimental details, metrics, and selection rationale, "
        "see the research notebook and the generated evaluation report."
    )
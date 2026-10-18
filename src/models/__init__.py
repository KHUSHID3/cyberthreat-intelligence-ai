"""
Classic ML / NLP model training, similarity, and evaluation utilities.
No deep learning.
"""

from .trainers import (
    build_logreg_tfidf_pipeline,
    build_linearsvc_tfidf_pipeline,
    build_multinomialnb_tfidf_pipeline,
    build_random_forest_tfidf,
    build_histgradientboosting_tfidf,
    build_knn_tfidf,
    build_logreg_bow_pipeline,
    train_and_evaluate_pipeline,
)
from .similarity import SimilarityIndex
from .evaluation import (
    compute_classification_metrics,
    print_classification_report,
    plot_confusion_matrix,
    compare_models,
)

__all__ = [
    # trainers
    "build_logreg_tfidf_pipeline",
    "build_linearsvc_tfidf_pipeline",
    "build_multinomialnb_tfidf_pipeline",
    "build_random_forest_tfidf",
    "build_histgradientboosting_tfidf",
    "build_knn_tfidf",
    "build_logreg_bow_pipeline",
    "train_and_evaluate_pipeline",
    # similarity
    "SimilarityIndex",
    # evaluation
    "compute_classification_metrics",
    "print_classification_report",
    "plot_confusion_matrix",
    "compare_models",
]
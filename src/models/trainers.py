"""
Model builders and training helpers (classic ML only).

Provides the seven algorithmic approaches required by the project:
1. Logistic Regression + TF-IDF
2. Linear SVC + TF-IDF
3. Multinomial Naive Bayes + TF-IDF
4. Random Forest + TF-IDF
5. HistGradientBoosting + TF-IDF
6. K-Nearest Neighbors (cosine) + TF-IDF
7. Logistic Regression + CountVectorizer (BoW)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.base import BaseEstimator

from src.features.text import build_tfidf_vectorizer, build_count_vectorizer
from src.models.evaluation import compute_classification_metrics


def build_logreg_tfidf_pipeline(
    max_features: int = 15000,
    ngram_range: tuple = (1, 2),
    C: float = 1.0,
    random_state: int = 42,
) -> Pipeline:
    """1. Logistic Regression + TF-IDF"""
    return Pipeline([
        ("tfidf", build_tfidf_vectorizer(max_features=max_features, ngram_range=ngram_range)),
        ("clf", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            C=C,
            random_state=random_state,
            n_jobs=-1,
        )),
    ])


def build_linearsvc_tfidf_pipeline(
    max_features: int = 15000,
    ngram_range: tuple = (1, 2),
    C: float = 1.0,
    random_state: int = 42,
) -> Pipeline:
    """2. Linear SVC + TF-IDF"""
    return Pipeline([
        ("tfidf", build_tfidf_vectorizer(max_features=max_features, ngram_range=ngram_range)),
        ("clf", LinearSVC(
            class_weight="balanced",
            C=C,
            random_state=random_state,
            dual="auto",
        )),
    ])


def build_multinomialnb_tfidf_pipeline(
    max_features: int = 15000,
    ngram_range: tuple = (1, 2),
    alpha: float = 0.5,
) -> Pipeline:
    """3. Multinomial Naive Bayes + TF-IDF"""
    return Pipeline([
        ("tfidf", build_tfidf_vectorizer(max_features=max_features, ngram_range=ngram_range)),
        ("clf", MultinomialNB(alpha=alpha)),
    ])


def build_random_forest_tfidf(
    max_features: int = 5000,
    ngram_range: tuple = (1, 2),
    n_estimators: int = 200,
    max_depth: int = 20,
    random_state: int = 42,
) -> Tuple[Any, RandomForestClassifier]:
    """
    4. Random Forest + TF-IDF
    Returns (vectorizer, classifier) because RF works better with explicit matrix.
    """
    vectorizer = build_tfidf_vectorizer(max_features=max_features, ngram_range=ngram_range)
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )
    return vectorizer, clf


def build_histgradientboosting_tfidf(
    max_features: int = 3000,
    ngram_range: tuple = (1, 2),
    max_iter: int = 150,
    learning_rate: float = 0.08,
    max_depth: int = 8,
    random_state: int = 42,
) -> Tuple[Any, HistGradientBoostingClassifier]:
    """
    5. HistGradientBoosting + TF-IDF
    Returns (vectorizer, classifier). Requires dense input.
    """
    vectorizer = build_tfidf_vectorizer(max_features=max_features, ngram_range=ngram_range)
    clf = HistGradientBoostingClassifier(
        max_iter=max_iter,
        learning_rate=learning_rate,
        max_depth=max_depth,
        random_state=random_state,
    )
    return vectorizer, clf


def build_knn_tfidf(
    max_features: int = 4000,
    ngram_range: tuple = (1, 2),
    n_neighbors: int = 7,
) -> Tuple[Any, KNeighborsClassifier]:
    """
    6. K-Nearest Neighbors (cosine) + TF-IDF
    Returns (vectorizer, classifier).
    """
    vectorizer = build_tfidf_vectorizer(max_features=max_features, ngram_range=ngram_range)
    clf = KNeighborsClassifier(
        n_neighbors=n_neighbors,
        weights="distance",
        metric="cosine",
        n_jobs=-1,
    )
    return vectorizer, clf


def build_logreg_bow_pipeline(
    max_features: int = 12000,
    ngram_range: tuple = (1, 2),
    C: float = 1.0,
    random_state: int = 42,
) -> Pipeline:
    """7. Logistic Regression + CountVectorizer (Bag-of-Words)"""
    return Pipeline([
        ("count", build_count_vectorizer(max_features=max_features, ngram_range=ngram_range)),
        ("clf", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            C=C,
            random_state=random_state,
            n_jobs=-1,
        )),
    ])


def train_and_evaluate_pipeline(
    pipeline: Pipeline,
    X_train,
    y_train,
    X_test,
    y_test,
    target_names: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Fit a sklearn Pipeline and return metrics + predictions.
    """
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    metrics = compute_classification_metrics(y_test, y_pred, target_names=target_names)
    metrics["y_pred"] = y_pred
    metrics["model"] = pipeline
    return metrics
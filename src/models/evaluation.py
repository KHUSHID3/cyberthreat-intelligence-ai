"""
Classification metrics, reporting, and comparison utilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix,
)


def compute_classification_metrics(
    y_true,
    y_pred,
    target_names: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Compute a standard set of classification metrics.
    """
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "macro_precision": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
    }

    # Per-class report as dict
    report = classification_report(
        y_true,
        y_pred,
        target_names=target_names,
        output_dict=True,
        zero_division=0,
    )
    metrics["classification_report"] = report
    metrics["confusion_matrix"] = confusion_matrix(y_true, y_pred).tolist()

    return metrics


def print_classification_report(
    y_true,
    y_pred,
    target_names: Optional[Sequence[str]] = None,
    title: str = "Classification Report",
) -> None:
    """Pretty-print classification metrics."""
    print("=" * 60)
    print(title)
    print("=" * 60)
    print(classification_report(
        y_true, y_pred,
        target_names=target_names,
        digits=3,
        zero_division=0,
    ))
    print(f"Balanced Accuracy: {balanced_accuracy_score(y_true, y_pred):.4f}")
    print(f"Macro F1         : {f1_score(y_true, y_pred, average='macro', zero_division=0):.4f}")


def plot_confusion_matrix(
    y_true,
    y_pred,
    target_names: Optional[Sequence[str]] = None,
    title: str = "Confusion Matrix",
    figsize: tuple = (8, 6),
    cmap: str = "Blues",
) -> None:
    """Plot a confusion matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=figsize)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap=cmap,
        xticklabels=target_names,
        yticklabels=target_names,
    )
    plt.title(title)
    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.tight_layout()
    plt.show()


def compare_models(
    results: List[Dict[str, Any]],
    sort_by: str = "balanced_accuracy",
) -> pd.DataFrame:
    """
    Build a comparison table from a list of metric dictionaries.

    Each dict in `results` is expected to contain at least:
    - "model_name"
    - the metric keys produced by compute_classification_metrics
    """
    rows = []
    for r in results:
        rows.append({
            "model": r.get("model_name", "unknown"),
            "accuracy": r.get("accuracy"),
            "balanced_acc": r.get("balanced_accuracy"),
            "macro_f1": r.get("macro_f1"),
            "weighted_f1": r.get("weighted_f1"),
            "macro_precision": r.get("macro_precision"),
            "macro_recall": r.get("macro_recall"),
        })

    df = pd.DataFrame(rows)
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=False).reset_index(drop=True)
    return df
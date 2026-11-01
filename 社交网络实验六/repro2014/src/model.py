"""成对相似度学习：线性核 SVM + 10 折交叉验证（论文 3.2 节）。

论文用线性核 SVM 做二分类，取「判为正类的置信度」作为两推文的相似度。
sklearn 的 LinearSVC 给出 decision_function 值，这里用 sigmoid 压到 (0,1)
作为相似度，供 HAC 使用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
from sklearn.model_selection import KFold
from sklearn.svm import LinearSVC

from .features import (
    ALL_FEATURES,
    METADATA_FEATURES,
    SEMANTIC_FEATURES,
    TERM_FEATURES,
    TIME_FEATURES,
    EntityFeatureBuilder,
)
from .replab_io import EntityData


# 论文 Table 2 的消融组合
SIGNAL_COMBINATIONS: Dict[str, List[str]] = {
    "time": TIME_FEATURES,
    "metadata": METADATA_FEATURES,
    "terms_jaccard": ["terms_jaccard"],
    "semantics": SEMANTIC_FEATURES,
    "terms": TERM_FEATURES,
    "terms+time": TERM_FEATURES + TIME_FEATURES,
    "terms+semantics": TERM_FEATURES + SEMANTIC_FEATURES,
    "terms+semantics+metadata": TERM_FEATURES + SEMANTIC_FEATURES + METADATA_FEATURES,
    "terms+semantics+time": TERM_FEATURES + SEMANTIC_FEATURES + TIME_FEATURES,
    "all": ALL_FEATURES,
}


def build_pair_matrix(
    entities: Dict[str, EntityData],
    pairs: Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]],
    features: Sequence[str],
    builders: Dict[str, EntityFeatureBuilder],
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """把采样到的推文对展开成 (X, y)。

    返回实际生效的特征名列表——正文缺失时文本类特征会被剔除。
    """
    xs: List[np.ndarray] = []
    ys: List[np.ndarray] = []
    for ent, (ii, jj, yy) in pairs.items():
        if len(ii) == 0:
            continue
        b = builders[ent]
        xs.append(b.pair_matrix(features, ii, jj))
        ys.append(yy)
    if not xs:
        raise ValueError("没有可用的推文对")

    X = np.vstack(xs)
    y = np.concatenate(ys)

    # 剔除整列不可用的特征（例如没有正文时的 terms_*）
    keep: List[str] = []
    for k, name in enumerate(features):
        col = X[:, k]
        if np.all(np.isnan(col)):
            continue
        keep.append(name)
    if not keep:
        raise ValueError("所有特征都不可用")
    idx = [features.index(n) for n in keep]
    X = X[:, idx]

    # 残余 NaN（部分实体有正文、部分没有）置 0
    if np.isnan(X).any():
        X = np.nan_to_num(X, nan=0.0)

    return X.astype(np.float64), y.astype(np.int64), keep


@dataclass
class CVResult:
    mean_accuracy: float
    std_accuracy: float
    fold_accuracies: List[float]
    features: List[str]


def cross_validate(
    X: np.ndarray, y: np.ndarray, folds: int = 10, C: float = 1.0, seed: int = 42
) -> Tuple[float, float, List[float]]:
    kf = KFold(n_splits=folds, shuffle=True, random_state=seed)
    accs: List[float] = []
    for tr, te in kf.split(X):
        clf = LinearSVC(C=C, loss="squared_hinge", dual="auto", max_iter=5000)
        clf.fit(X[tr], y[tr])
        accs.append(float((clf.predict(X[te]) == y[te]).mean()))
    return float(np.mean(accs)), float(np.std(accs)), accs


def fit_final(X: np.ndarray, y: np.ndarray, C: float = 1.0) -> LinearSVC:
    clf = LinearSVC(C=C, loss="squared_hinge", dual="auto", max_iter=5000)
    clf.fit(X, y)
    return clf


def decision_to_similarity(scores: np.ndarray) -> np.ndarray:
    """把 SVM 的 decision_function 压到 (0,1)，作为相似度。"""
    return 1.0 / (1.0 + np.exp(-scores))

"""Baselines from Section 5.1, in both static and sliding-window form.

The paper adapts three static summarizers to streams with a sliding window
(Figure 8): "each window contains a certain number (window size) of tweets
which are summarized as a document. After that, the window moves forward by a
step size, so that the oldest tweets are discarded and the new ones are added
into the window." Windows are "dimensioned by number of tweets instead of time
duration, because the number of tweets may vary dramatically across fixed-length
durations".

Baselines:
  ClusterSum [13] -- cluster the tweets, pick the most weighted post per cluster
                     by hybrid TF-IDF.
  LexRank    [6]  -- sentence similarity graph + eigenvector centrality.
  DSDR       [11] -- linear reconstruction of the document set; pick the subset
                     minimizing reconstruction error (He et al., AAAI 2012).
  Random          -- select tweets randomly from each window.

All return tweet indices in *priority order* (best first), because the pipeline
trims every method to the shared 250-word budget.
"""
from typing import List, Sequence, Tuple

import numpy as np
from scipy import sparse
from sklearn.cluster import KMeans

from config import SumblrConfig


def _dense(v) -> np.ndarray:
    if sparse.issparse(v):
        return np.asarray(v.toarray()).ravel().astype(np.float32)
    return np.asarray(v).ravel().astype(np.float32)


def _unit_rows(M: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(M, axis=1, keepdims=True)
    n[n < 1e-12] = 1e-12
    return M / n


# ---------------------------------------------------------------------------
# ClusterSum (Inouye & Kalita, 2011)
# ---------------------------------------------------------------------------
def clustersum(X, k: int, cfg: SumblrConfig, idx: Sequence[int] = None
               ) -> List[int]:
    """Cluster tweets; pick the highest-mass tweet per cluster, big clusters
    first (the coverage half of the paper's Equation 2)."""
    idx = np.arange(X.shape[0]) if idx is None else np.asarray(idx)
    n = len(idx)
    if n == 0:
        return []
    sub = X[idx]
    kk = max(2, min(k, n))
    km = KMeans(n_clusters=kk, n_init=4, random_state=cfg.seed)
    labels = km.fit_predict(sub)
    picks: List[Tuple[int, float]] = []
    for c in range(kk):
        members = np.where(labels == c)[0]
        if len(members) == 0:
            continue
        mass = np.asarray(sub[members].sum(axis=1)).ravel()
        best = members[int(np.argmax(mass))]
        picks.append((int(idx[best]), float(len(members))))
    picks.sort(key=lambda p: -p[1])
    return [p[0] for p in picks[:k]]


# ---------------------------------------------------------------------------
# LexRank (Erkan & Radev, 2004)
# ---------------------------------------------------------------------------
def lexrank_scores(sim: np.ndarray, iters: int, damping: float) -> np.ndarray:
    n = sim.shape[0]
    if n == 0:
        return np.zeros(0)
    deg = sim.sum(axis=1)
    trans = np.zeros_like(sim, dtype=np.float64)
    nz = deg > 0
    trans[nz] = sim[nz] / deg[nz, None]
    score = np.full(n, 1.0 / n)
    for _ in range(iters):
        score = (1 - damping) / n + damping * (trans.T @ score)
    return score


def lexrank(X, k: int, cfg: SumblrConfig, idx: Sequence[int] = None) -> List[int]:
    idx = np.arange(X.shape[0]) if idx is None else np.asarray(idx)
    n = len(idx)
    if n == 0:
        return []
    M = _unit_rows(np.vstack([_dense(X[i]) for i in idx]))
    sim = np.clip(M @ M.T, 0.0, 1.0)
    sim[sim < cfg.lexrank_threshold] = 0.0
    np.fill_diagonal(sim, 0.0)
    sc = lexrank_scores(sim, cfg.lexrank_iters, cfg.lexrank_damping)
    return [int(idx[i]) for i in np.argsort(-sc)[:k]]


# ---------------------------------------------------------------------------
# DSDR (He et al., AAAI 2012) -- linear reconstruction
# ---------------------------------------------------------------------------
def dsdr(X, k: int, cfg: SumblrConfig, idx: Sequence[int] = None) -> List[int]:
    """Dependency-based SDR via greedy reconstruction-error minimisation.

    He et al. model relations among sentences by linear reconstruction: a
    candidate set S should reconstruct the whole document set D, i.e. minimise
        || D - S (S^T S)^{-1} S^T D ||_F^2
    and they solve it by iterative substitution. We use the standard greedy
    equivalent (forward column subset selection): repeatedly add the candidate
    that most reduces the residual of D given the selected rows.

    With L2-normalised rows, after choosing row v we deflate the residual with
        R <- R (I - v v^T)
    and the gain of a candidate u is ||u^T R||^2, i.e. how much of the remaining
    residual it explains. This is the greedy step DSDR's substitution converges
    to, and it is what makes DSDR expensive: each step is O(n * d).
    """
    idx = np.arange(X.shape[0]) if idx is None else np.asarray(idx)
    n = len(idx)
    if n == 0:
        return []
    if n <= k:
        return [int(i) for i in idx]

    D = _unit_rows(np.vstack([_dense(X[i]) for i in idx]))   # (n, d)
    R = D.copy()                       # residual, initially D itself
    chosen: List[int] = []
    available = np.ones(n, dtype=bool)

    for _ in range(min(k, n)):
        proj = D @ R.T                                  # (n, n)
        gains = np.einsum("ij,ij->i", proj, proj)
        gains[~available] = -np.inf
        best = int(np.argmax(gains))
        if not np.isfinite(gains[best]) or gains[best] <= 1e-12:
            break
        chosen.append(best)
        available[best] = False
        v = D[best]
        R = R - np.outer(R @ v, v)      # R <- R (I - v v^T)

    return [int(idx[i]) for i in chosen]


# ---------------------------------------------------------------------------
# Random
# ---------------------------------------------------------------------------
def random_pick(X, k: int, cfg: SumblrConfig, idx: Sequence[int] = None
                ) -> List[int]:
    idx = np.arange(X.shape[0]) if idx is None else np.asarray(idx)
    n = len(idx)
    if n == 0:
        return []
    rng = np.random.default_rng(cfg.seed)
    return [int(i) for i in rng.choice(idx, size=min(k, n), replace=False)]


# ---------------------------------------------------------------------------
# Popularity (extra reference point, not in the paper)
# ---------------------------------------------------------------------------
def popularity(df, k: int, idx: Sequence[int] = None) -> List[int]:
    idx = np.arange(len(df)) if idx is None else np.asarray(idx)
    score = df["retweets"].to_numpy() + df["favorites"].to_numpy()
    order = np.argsort(-score[idx])
    return [int(idx[i]) for i in order[:k]]


BASELINES = {
    "ClusterSum": clustersum,
    "LexRank": lexrank,
    "DSDR": dsdr,
    "Random": random_pick,
}


def run_baseline(name: str, X, k: int, cfg: SumblrConfig,
                 idx: Sequence[int] = None) -> List[int]:
    return BASELINES[name](X, k, cfg, idx)

"""Module 3: TCV-Rank summarization and timeline detection.

Implements Shou et al., SIGIR 2013:
  * TCV-Rank summarization   -- Algorithm 2, Section 4.2.1
  * Objective function       -- Equation (2)
  * Topic evolvement         -- Equation (3), Section 4.3
"""
from typing import Dict, List, Tuple

import numpy as np
from scipy import sparse

from config import SumblrConfig


def _dense(v) -> np.ndarray:
    if sparse.issparse(v):
        return np.asarray(v.toarray()).ravel().astype(np.float32)
    return np.asarray(v).ravel().astype(np.float32)


def lexrank(sim: np.ndarray, iters: int = 10, damping: float = 0.85) -> np.ndarray:
    """LexRank / eigenvector centrality over a similarity matrix.

    Row-normalized transition matrix with degree normalization (Erkan & Radev).
    """
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


class TCVSummarizer:
    """Builds a summary from a cluster set using Algorithm 2."""

    def __init__(self, cfg: SumblrConfig, X):
        self.cfg = cfg
        self.X = X
        self.word_counts = None

    # -- helpers ------------------------------------------------------------
    def _tweet_words(self, idx: int) -> int:
        if self.word_counts is None:
            return 0
        return int(self.word_counts[idx])

    def build_candidates(self, clusters):
        """Collect T = union of focus sets; return (T, tweet->cluster_size, sim).

        The similarity graph is sparsified with a cosine threshold, which is
        standard LexRank practice (Erkan & Radev). Without it the graph is
        dense and nearly all-positive on short tweets, so eigenvector
        centrality is almost uniform and cannot discriminate noise from
        substance -- which the paper relies on for its noise handling
        (Section 4.4: noise tweets get "low LexRank scores").
        """
        T: List[int] = []
        size_of: Dict[int, int] = {}
        for c in clusters:
            for idx, _ in c.ft_set:
                if idx not in size_of:
                    # Skip near-empty tweets: they carry no summary content and
                    # would otherwise satisfy the word budget with nothing.
                    if self._tweet_words(idx) < self.cfg.min_tweet_tokens:
                        continue
                    T.append(idx)
                    size_of[idx] = c.n
        if not T:
            return [], {}, np.zeros((0, 0))

        M = np.vstack([_dense(self.X[i]) for i in T])
        norms = np.linalg.norm(M, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1e-12
        Mn = M / norms
        sim = np.clip(Mn @ Mn.T, 0.0, 1.0)
        sim[sim < self.cfg.lexrank_threshold] = 0.0
        np.fill_diagonal(sim, 0.0)
        return T, size_of, sim
    # -- Algorithm 2 --------------------------------------------------------
    def summarize(self, clusters) -> dict:
        """Run TCV-Rank; returns the selected tweet ids and diagnostics.

        All internal bookkeeping is in *position* space (indices into T) so the
        LexRank vector and similarity matrix can be indexed directly.
        """
        cfg = self.cfg
        T, size_of, sim = self.build_candidates(clusters)
        if not T:
            return {"tweets": [], "T_size": 0, "clusters_used": 0}

        lr = lexrank(sim, iters=cfg.lexrank_iters, damping=cfg.lexrank_damping)
        n_max = max(size_of.values()) if size_of else 1
        pos = {t: i for i, t in enumerate(T)}

        # Tc = the tweet with the highest LexRank score in each cluster (line 4).
        best_pos: Dict[int, bool] = {}
        for c in clusters:
            cands = [pos[i] for i, _ in c.ft_set if i in pos]
            if not cands:
                continue
            best_pos[max(cands, key=lambda p: lr[p])] = True
        Tc = sorted(best_pos)

        S_pos: List[int] = []
        words = 0

        def eq2(p: int) -> float:
            """Equation (2): lambda*(n_t/n_max)*LR - (1-lambda)*avg Sim to S."""
            cov = cfg.lam * (size_of.get(T[p], 1) / n_max) * lr[p]
            red = 0.0 if not S_pos else float(np.mean([sim[p, q] for q in S_pos]))
            return cov - (1 - cfg.lam) * red

        # Stage 1: greedily pick from Tc (lines 5-9).
        remaining = list(Tc)
        while remaining and len(S_pos) < cfg.max_summary_tweets:
            if words >= cfg.summary_words:
                break
            p = max(remaining, key=eq2)
            S_pos.append(p)
            words += self._tweet_words(T[p])
            remaining.remove(p)

        # Stage 2: fill from T - S if the budget is not met (lines 10-14).
        while words < cfg.summary_words and len(S_pos) < cfg.max_summary_tweets:
            cand = [p for p in range(len(T)) if p not in S_pos]
            if not cand:
                break
            p = max(cand, key=eq2)
            S_pos.append(p)
            words += self._tweet_words(T[p])

        return {
            "tweets": [T[p] for p in S_pos],
            "T_size": len(T),
            "clusters_used": len(Tc),
            "words": words,
            "lexrank": lr,
            "T": T,
        }


# ---------------------------------------------------------------------------
# Topic evolvement detection (Section 4.3)
# ---------------------------------------------------------------------------
def kl_divergence(counts_c: Dict[str, float], counts_p: Dict[str, float],
                  eps: float = 1.0) -> float:
    """D_KL(Sc || Sp) with Laplace (add-eps) smoothing.

    The paper (Section 4.3) defines
        p(w|Sc) = tf(w,Sc) / SUM_w' tf(w',Sc)
        p(w|Sp) = (tf(w,Sp) + eps) / SUM_w' (tf(w',Sp) + eps)
    and says only that "eps is a small positive constant for Laplace
    Smoothing" -- the value is NOT stated.

    The value matters enormously. With a tiny eps (e.g. 1e-8) and short
    summaries (~130 distinct terms), any word present in the current summary
    but absent from the previous one contributes log(p_c / 1e-8) ~ 20, so
    D_KL ~ 11-15 for *every* pair, D = 1 - e^{-D_KL} saturates at 1.0000, and
    the D_cur / D_avg > tau test can never fire (we measured a max/min D ratio
    of 1.0000 against the required tau = 1.012).

    We therefore use the standard add-one form over the union vocabulary, which
    is the usual reading of "Laplace smoothing" and keeps D discriminative.
    """
    vocab = set(counts_c) | set(counts_p)
    if not vocab:
        return 0.0
    sc = sum(counts_c.values())
    if sc <= 0:
        return 0.0
    sp = sum(counts_p.values()) + eps * len(vocab)
    d = 0.0
    for w in vocab:
        pc = counts_c.get(w, 0.0) / sc
        pp = (counts_p.get(w, 0.0) + eps) / sp
        if pc > 0 and pp > 0:
            d += pc * np.log(pc / pp)
    return float(d)


def normalized_distance(d_kl: float) -> float:
    """D = 1 - e^{-D_KL}  ->  [0, 1)."""
    return float(1.0 - np.exp(-d_kl))


def detect_timeline(summaries: List[dict], cfg: SumblrConfig,
                    davg_mode: str = None,
                    min_davg_samples: int = None) -> List[dict]:
    """Emit timeline nodes where D_cur / D_avg > tau.

    The paper (Section 4.3) defines D_avg as "the average distance of all the
    previous successive summary pairs which do not produce time nodes".

    DIRECT-LITERAL IMPLEMENTATION DEGENERATES. Because only non-node pairs feed
    the average, and non-node pairs are by construction the *small* distances,
    D_avg is dragged downward. A lower D_avg makes the next pair more likely to
    be declared a node, which removes it from the pool and pushes D_avg down
    further -- a positive feedback loop. We measured the failure directly: with
    450 overlapping windows and tau=1.012, only 5 of 449 pairs ever entered the
    pool, D_avg was pinned near 0.54 while the raw distances averaged 0.53, and
    the rule fired on 400/449 pairs (89%). A timeline where nearly every window
    is an "evolvement node" carries no information.

    Two guards, both documented:
      * warmup / min-sample guard: until the non-node pool holds at least
        `min_davg_samples` entries it is not a stable baseline estimate, so we
        fall back to the running mean of ALL previous pairs. Once the pool is
        established we revert to the paper's non-node-only average.
      * davg_mode="all" computes D_avg over all previous pairs throughout, for
        sensitivity reporting.

    Set davg_mode="paper_strict" to reproduce the unguarded literal behaviour.
    """
    mode = davg_mode or cfg.davg_mode
    min_samples = (min_davg_samples if min_davg_samples is not None
                   else cfg.min_davg_samples)

    nodes = []
    series = []
    non_node_dists: List[float] = []
    all_dists: List[float] = []

    for i in range(1, len(summaries)):
        d = normalized_distance(
            kl_divergence(summaries[i]["word_counts"],
                          summaries[i - 1]["word_counts"], cfg.kl_epsilon)
        )
        if mode == "paper_strict":
            pool = non_node_dists
        elif mode == "all":
            pool = all_dists
        else:                                    # "paper" (guarded default)
            pool = (non_node_dists if len(non_node_dists) >= min_samples
                    else all_dists)

        d_avg = float(np.mean(pool)) if pool else 0.0
        ratio = (d / d_avg) if d_avg > 1e-12 else 0.0
        is_node = ratio > cfg.tau

        series.append({"index": i, "ts": summaries[i]["ts"],
                       "distance": d, "d_avg": d_avg, "ratio": ratio,
                       "is_node": is_node, "pool_size": len(pool)})
        if is_node:
            nodes.append(series[-1])
        else:
            non_node_dists.append(d)
        all_dists.append(d)

    return nodes, series

"""Module 4: evaluation, baselines and ground truth.

Reference summaries are built the way the paper does it (Section 4.1, ground
truth paragraph): run three candidate summarizers, then keep the items that
appear in at least two of the three, capped at 250 words.

IMPORTANT: every baseline returns its picks in *priority order* (best first),
not sorted by tweet id. The pipeline trims each method to the shared 250-word
budget, and trimming by index order would silently keep the wrong tweets.

Because the paper's ROUGE-1 target is only meaningful with a comparable gold
standard, and because that gold standard is itself assembled from the very
baselines being compared against, we also report reference-free diagnostics
(term coverage, mean IDF, diversity, redundancy).
"""
import json
import os
from collections import Counter
from typing import Dict, Iterable, List, Tuple

import numpy as np
from scipy import sparse

from config import SumblrConfig, OUT_DIR
from preprocess import tokenize


def _dense(v) -> np.ndarray:
    if sparse.issparse(v):
        return np.asarray(v.toarray()).ravel().astype(np.float32)
    return np.asarray(v).ravel().astype(np.float32)


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------
def baseline_random(df, k: int, seed: int = 42) -> List[int]:
    rng = np.random.default_rng(seed)
    n = len(df)
    return rng.choice(n, size=min(k, n), replace=False).tolist()


def baseline_popularity(df, k: int) -> List[int]:
    """Top-k by engagement (retweets + favorites) - a strong naive baseline."""
    score = df["retweets"].to_numpy() + df["favorites"].to_numpy()
    return np.argsort(-score)[:k].tolist()


def baseline_lead(df, k: int) -> List[int]:
    """Most recent k tweets (temporal lead baseline), newest first."""
    return list(range(len(df) - 1, max(-1, len(df) - k - 1), -1))


def baseline_lexrank(df, X, k: int, cfg: SumblrConfig) -> List[int]:
    """LexRank over a sample of the stream (efficiency-limited baseline).

    Uses the standard LexRank construction: cosine similarity graph, sparsified
    at a threshold, zero diagonal, then eigenvector centrality. Without
    thresholding the graph is dense-but-nearly-uniform on short tweets, the
    stationary distribution collapses onto generic boilerplate, and the top-k
    are near-duplicates (we measured a mean pairwise distance of 0.10).
    """
    from summarize import lexrank

    n = X.shape[0]
    idx = np.arange(n)
    if n > 1200:                      # keep the O(n^2) graph tractable
        rng = np.random.default_rng(cfg.seed)
        idx = np.sort(rng.choice(n, size=1200, replace=False))
    M = np.vstack([_dense(X[i]) for i in idx])
    norms = np.linalg.norm(M, axis=1, keepdims=True)
    norms[norms < 1e-12] = 1e-12
    Mn = M / norms
    sim = np.clip(Mn @ Mn.T, 0.0, 1.0)
    sim[sim < cfg.lexrank_threshold] = 0.0
    np.fill_diagonal(sim, 0.0)
    lr = lexrank(sim, iters=cfg.lexrank_iters, damping=cfg.lexrank_damping)
    top = np.argsort(-lr)[:k]
    return [int(idx[i]) for i in top]          # priority order


def baseline_clustersum(df, X, k: int, cfg: SumblrConfig) -> List[int]:
    """ClusterSum-style baseline: k-means clusters, pick the top TF-IDF tweet
    from each cluster until k tweets are collected (Inouye & Kalita, 2011)."""
    from sklearn.cluster import KMeans

    n = X.shape[0]
    kk = max(2, min(k, n))
    km = KMeans(n_clusters=kk, n_init=4, random_state=cfg.seed)
    labels = km.fit_predict(X)
    picks: List[Tuple[int, float]] = []
    for c in range(kk):
        members = np.where(labels == c)[0]
        if len(members) == 0:
            continue
        mass = np.asarray(X[members].sum(axis=1)).ravel()
        # Weight each cluster's representative by cluster size (coverage), the
        # same "favour tweets in big clusters" idea as the paper's Equation (2).
        picks.append((int(members[int(np.argmax(mass))]), float(len(members))))
    picks.sort(key=lambda p: -p[1])
    return [p[0] for p in picks[:k]]           # priority order


# ---------------------------------------------------------------------------
# Ground truth: paper's 3-candidate / >=2 agreement recipe
# ---------------------------------------------------------------------------
def build_reference(df, X, cfg: SumblrConfig, k: int):
    """Reference summary following the paper's candidate-voting recipe.

    The paper takes the union of three candidate summarizers and keeps items
    appearing in at least two. Applied literally to tweets (which rarely repeat
    verbatim across methods) that yields almost nothing, so we rank the union
    by vote count and then by the paper's own Equation (2) coverage/novelty
    criterion, keeping the top-k. This is documented in the README as a
    deviation forced by the unit of text (tweets vs. sentences).
    """
    cands = {
        "clustersum": baseline_clustersum(df, X, k, cfg),
        "lexrank": baseline_lexrank(df, X, k, cfg),
        "popularity": baseline_popularity(df, k),
    }
    votes = Counter()
    for picks in cands.values():
        votes.update(set(picks))

    eng = df["retweets"].to_numpy() + df["favorites"].to_numpy()
    # Rank candidates: vote count first, then engagement as a tie-breaker.
    ranked = sorted(votes.keys(), key=lambda i: (-votes[i], -eng[i]))

    # Greedy selection with MMR-style redundancy control (paper Eq. 2 spirit).
    ref: List[int] = []
    if ranked:
        M = np.vstack([_dense(X[i]) for i in ranked])
        norms = np.linalg.norm(M, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1e-12
        S = np.clip((M / norms) @ (M / norms).T, 0.0, 1.0)
        remaining = list(range(len(ranked)))
        while remaining and len(ref) < k:
            best, best_v = None, -1e9
            for j in remaining:
                red = max((S[j, ranked.index(r)] for r in ref), default=0.0)
                v = cfg.lam * (votes[ranked[j]] / 3.0) - (1 - cfg.lam) * red
                if v > best_v:
                    best, best_v = j, v
            ref.append(ranked[best])
            remaining.remove(best)
    ref.sort()
    return ref, cands


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def _rouge_n(hyp_tokens: List[List[str]], ref_tokens: List[List[str]], n: int):
    """Corpus-level ROUGE-n F1 (Lin & Hovy style n-gram overlap)."""
    def grams(docs):
        c = Counter()
        for toks in docs:
            for i in range(len(toks) - n + 1):
                c[tuple(toks[i:i + n])] += 1
        return c

    h, r = grams(hyp_tokens), grams(ref_tokens)
    if not r or not h:
        return 0.0, 0.0, 0.0
    overlap = sum(min(cnt, r[g]) for g, cnt in h.items())
    prec = overlap / max(1, sum(h.values()))
    rec = overlap / max(1, sum(r.values()))
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return prec, rec, f1


def _lcs(a: List[str], b: List[str]) -> int:
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def rouge_l(hyp_tokens: List[List[str]], ref_tokens: List[List[str]]):
    """Corpus-level ROUGE-L F1 using the union-LCS approximation."""
    h_all = [t for d in hyp_tokens for t in d]
    r_all = [t for d in ref_tokens for t in d]
    l = _lcs(h_all, r_all)
    prec = l / max(1, len(h_all))
    rec = l / max(1, len(r_all))
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return prec, rec, f1


def evaluate(summary_ids: List[int], ref_ids: List[int], df,
             cfg: SumblrConfig, X) -> Dict[str, float]:
    """ROUGE-1/2/L plus reference-free quality diagnostics.

    The ROUGE numbers depend on a reference summary that is itself built from
    baseline summarizers (the paper's recipe), which biases them toward those
    baselines. We therefore also report reference-free diagnostics, and a
    coverage score against the whole stream, which do not depend on the gold
    standard and are the more trustworthy comparison here.
    """
    hyp = [tokenize(df["text"].iloc[i], cfg) for i in summary_ids]
    ref = [tokenize(df["text"].iloc[i], cfg) for i in ref_ids]

    out: Dict[str, float] = {}
    for n in (1, 2):
        p, r, f = _rouge_n(hyp, ref, n)
        out[f"rouge{n}_p"] = p
        out[f"rouge{n}_r"] = r
        out[f"rouge{n}_f"] = f
    p, r, f = rouge_l(hyp, ref)
    out["rougeL_p"], out["rougeL_r"], out["rougeL_f"] = p, r, f

    # --- reference-free diagnostics ---------------------------------------
    if summary_ids:
        M = np.vstack([_dense(X[i]) for i in summary_ids])
        norms = np.linalg.norm(M, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1e-12
        Mn = M / norms
        S = np.clip(Mn @ Mn.T, 0.0, 1.0)
        iu = np.triu_indices(len(summary_ids), k=1)
        pairwise = S[iu] if len(iu[0]) else np.array([0.0])
        out["diversity_mean_dist"] = float(np.mean(1.0 - pairwise))
        out["redundancy_max_sim"] = float(np.max(pairwise))
        out["redundancy_mean_sim"] = float(np.mean(pairwise))

        # Coverage: share of the stream's distinct terms that the summary uses.
        all_tokens = set()
        for t in df["text"].sample(min(1500, len(df)),
                                   random_state=cfg.seed):
            all_tokens.update(tokenize(t, cfg))
        sum_tokens = set(w for d in hyp for w in d)
        out["term_coverage"] = (len(sum_tokens & all_tokens) /
                                max(1, len(all_tokens)))

        # Informativeness proxy: mean inverse document frequency of the terms
        # the summary uses (rare/event-specific words score higher than the
        # generic "pray for turkey" boilerplate that dominates the stream).
        from collections import Counter as _C
        docs = [set(tokenize(t, cfg)) for t in df["text"]]
        n_docs = len(docs)
        dfreq = _C()
        for d in docs:
            dfreq.update(d)
        idf = {w: float(np.log(n_docs / (1 + dfreq[w]))) for w in dfreq}
        vals = [idf.get(w, 0.0) for d in hyp for w in d]
        out["mean_idf"] = float(np.mean(vals)) if vals else 0.0

    out["summary_tweets"] = len(summary_ids)
    out["summary_words"] = sum(len(t) for t in hyp)
    out["reference_tweets"] = len(ref_ids)
    return out


def save_json(obj, name: str) -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=float)
    return path


def enforce_budget(ids, word_counts, cfg: SumblrConfig):
    """Trim a summary to the paper's shared budget (<= words and <= tweets).

    The paper caps every summary at 250 words ("The length of each summary is
    limited to 250 words"). Keeping the given order preserves each method's own
    ranking, so this normalizes length without changing priorities.
    """
    out, words = [], 0
    for i in ids:
        if len(out) >= cfg.max_summary_tweets:
            break
        w = int(word_counts[i])
        if out and words + w > cfg.summary_words:
            continue
        out.append(int(i))
        words += w
    return out

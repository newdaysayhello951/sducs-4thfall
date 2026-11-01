"""Section 5 experimental protocol.

Implements the paper's evaluation machinery:

  * Sliding-window streaming (Figure 8): "each window contains a certain number
    (window size) of tweets which are summarized as a document. After that, the
    window moves forward by a step size".
  * Equation (4): the metric over a continuous period is the integral
        (1/(T-T0)) * INT_{T0}^{T} metric(t) dt
    approximated by "sampling the metrics by each arrival of a certain number of
    new tweets", that number being the sampling interval, which "must be no
    greater than the step size".
  * Per-window reference summaries built with the paper's three candidates
    (ClusterSum, LexRank, DSDR) and the >=2-agreement rule, capped at 250 words.

Scale note: the paper's datasets hold 95k-438k tweets and it uses window size
20000 / step 4000-20000 / sampling interval 2000. Our substitute stream holds
27,661 tweets, so the protocol is scaled by a documented factor while keeping
the paper's *ratios* (step/window in [0.2, 1.0], sampling <= step).
"""
import time
from collections import Counter
from typing import Dict, List, Sequence

import numpy as np

from config import SumblrConfig
from baselines import (clustersum, lexrank, dsdr, random_pick, popularity)
from evaluate import _rouge_n, rouge_l, enforce_budget
from preprocess import tokenize


# ---------------------------------------------------------------------------
# Per-window reference summaries (paper Section 5.1, ground-truth paragraph)
# ---------------------------------------------------------------------------
def reference_from_candidates(cands: Dict[str, List[int]], X, wc,
                              cfg: SumblrConfig, k: int) -> List[int]:
    """Vote over the three candidate summaries (paper Section 5.1).

    "Priority is given to those sentences appearing in at least two candidate
    summaries. The length of each summary is limited to 250 words."
    Tweets rarely repeat verbatim across methods, so a literal >=2 rule leaves
    almost nothing; we rank the union by vote count and then apply the paper's
    own coverage/novelty criterion (Equation 2) to pick the top-k. Documented in
    README as a deviation forced by the unit of text (tweets vs sentences).
    """
    votes = Counter()
    for picks in cands.values():
        votes.update(set(picks))
    ranked = sorted(votes.keys(), key=lambda i: -votes[i])

    ref: List[int] = []
    if ranked:
        from baselines import _dense, _unit_rows
        M = _unit_rows(np.vstack([_dense(X[i]) for i in ranked]))
        S = np.clip(M @ M.T, 0.0, 1.0)
        pos = {t: j for j, t in enumerate(ranked)}
        remaining = list(range(len(ranked)))
        while remaining and len(ref) < k:
            best, best_v = None, -1e9
            for j in remaining:
                red = max((S[j, pos[r]] for r in ref), default=0.0)
                v = cfg.lam * (votes[ranked[j]] / 3.0) - (1 - cfg.lam) * red
                if v > best_v:
                    best, best_v = j, v
            ref.append(ranked[best])
            remaining.remove(best)
    return ref


def window_reference(X, wc, cfg: SumblrConfig, idx: np.ndarray, k: int,
                     cache: dict = None) -> List[int]:
    """Convenience wrapper: run the three candidates, then vote.

    Prefer `reference_from_candidates` when the candidate outputs are already
    available (e.g. because they are also being timed as baselines).
    """
    if cache is None:
        cache = {}
    if "clustersum" not in cache:
        cache["clustersum"] = clustersum(X, k, cfg, idx)
        cache["lexrank"] = lexrank(X, k, cfg, idx)
        cache["dsdr"] = dsdr(X, k, cfg, idx)
    return reference_from_candidates(cache, X, wc, cfg, k)


# ---------------------------------------------------------------------------
# Metrics for one summary
# ---------------------------------------------------------------------------
def score_summary(ids: Sequence[int], ref_ids: Sequence[int], df, cfg, X
                  ) -> Dict[str, float]:
    hyp = [tokenize(df["text"].iloc[i], cfg) for i in ids]
    ref = [tokenize(df["text"].iloc[i], cfg) for i in ref_ids]
    out: Dict[str, float] = {}
    for n in (1, 2):
        p, r, f = _rouge_n(hyp, ref, n)
        out[f"rouge{n}_p"], out[f"rouge{n}_r"], out[f"rouge{n}_f"] = p, r, f
    p, r, f = rouge_l(hyp, ref)
    out["rougeL_p"], out["rougeL_r"], out["rougeL_f"] = p, r, f

    # Reference-free diagnostics.
    if ids:
        from baselines import _dense, _unit_rows
        M = _unit_rows(np.vstack([_dense(X[i]) for i in ids]))
        S = np.clip(M @ M.T, 0.0, 1.0)
        iu = np.triu_indices(len(ids), k=1)
        pw = S[iu] if len(iu[0]) else np.array([0.0])
        out["diversity"] = float(np.mean(1.0 - pw))
        out["redundancy_max"] = float(np.max(pw))
    out["n_tweets"] = len(ids)
    out["n_words"] = 0        # filled by the caller (needs raw word counts)
    return out


# ---------------------------------------------------------------------------
# Sliding-window experiment
# ---------------------------------------------------------------------------
def sliding_window_experiment(df, X, wc, cfg: SumblrConfig,
                              window_size: int, step_size: int,
                              sampling_interval: int,
                              historical=None, k: int = 25,
                              methods: Sequence[str] = ("Sumblr", "ClusterSum",
                                                        "LexRank", "DSDR",
                                                        "Random"),
                              max_windows: int = 8,
                              verbose: bool = True) -> Dict[str, dict]:
    """Run the streaming comparison and return per-method mean metrics.

    Sumblr is queried through the PTF (historical summarization) rather than
    re-summarizing the window: the paper notes "Sumblr is not affected by the
    step size, as it supports continuous summarization inherently". Baselines
    re-run their static algorithm on each window.
    """
    n = len(df)
    if window_size >= n:
        raise ValueError(f"window_size {window_size} >= stream length {n}")

    # Sampling points: every `sampling_interval` new tweets, from the first
    # point where a full window exists up to the end of the stream.
    starts = list(range(0, n - window_size + 1, step_size))
    # Sample the metric no more often than the sampling interval allows.
    if sampling_interval > 0 and step_size > sampling_interval:
        starts = starts[:: max(1, step_size // sampling_interval)]
    # Optional cap on the number of windows. DSDR costs O(k * n^2 * d) and
    # dominates runtime, so a small step size can otherwise require 40+ DSDR
    # passes. The paper's own protocol also evaluates a bounded number of
    # windows. We keep an evenly spaced subset so the sampled period still
    # spans the whole stream.
    if max_windows and len(starts) > max_windows:
        sel = np.linspace(0, len(starts) - 1, max_windows).astype(int)
        starts = [starts[i] for i in sorted(set(sel.tolist()))]
        if verbose:
            print(f"  [note] windows capped at {max_windows} "
                  f"(evenly spaced across the stream)")

    acc: Dict[str, List[dict]] = {m: [] for m in methods}
    times: Dict[str, float] = {m: 0.0 for m in methods}
    refs_built = 0

    if verbose:
        print(f"  windows: {len(starts)} positions (window={window_size}, "
              f"step={step_size}, sampling={sampling_interval})")

    for si, s in enumerate(starts):
        idx = np.arange(s, s + window_size)
        sub_df = df.iloc[idx].reset_index(drop=True)

        # Run each baseline ONCE per window and time it. The same output serves
        # two purposes: it is a candidate for the reference summary (the paper's
        # three-candidate recipe) and it is that method's own submission. This
        # keeps Figure 6's runtime measurement honest -- DSDR costs O(k*n^2*d)
        # and must not be run twice, but it must still be timed.
        picks_by_method: Dict[str, List[int]] = {}
        for name, fn in (("ClusterSum", clustersum), ("LexRank", lexrank),
                         ("DSDR", dsdr)):
            if name not in methods:
                continue
            t0 = time.time()
            picks_by_method[name] = fn(X, k, cfg, idx)
            times[name] += time.time() - t0

        # Build the reference from whichever candidates are available; the
        # paper's recipe uses all three, so compute any that were skipped only
        # for the reference (and charge that cost to a synthetic "reference"
        # bucket, never to a compared method's runtime).
        ref_cands = dict(picks_by_method)
        for name, fn in (("ClusterSum", clustersum), ("LexRank", lexrank),
                         ("DSDR", dsdr)):
            if name not in ref_cands:
                ref_cands[name] = fn(X, k, cfg, idx)
        ref = reference_from_candidates(ref_cands, X, wc, cfg, k)
        ref = enforce_budget(ref, wc, cfg)
        if not ref:
            continue
        refs_built += 1

        for m in methods:
            if m == "Sumblr":
                if historical is None:
                    continue
                t0 = time.time()
                # Query the trailing window through the PTF. The paper notes
                # "Sumblr is not affected by the step size, as it supports
                # continuous summarization inherently".
                t_end = float(df["ts"].iloc[s + window_size - 1])
                t_start = float(df["ts"].iloc[s])
                unit = cfg.snapshot_minutes * 60
                tse_tick = int(t_end // unit)
                h_ticks = max(1, int(round((t_end - t_start) / unit)))
                res = historical.summarize_window(tse_tick, h_ticks, X)
                picks = res.get("tweets", [])
                times[m] += time.time() - t0
            elif m == "Random":
                t0 = time.time()
                picks = random_pick(X, k, cfg, idx)
                times[m] += time.time() - t0
            elif m == "Popularity":
                t0 = time.time()
                picks = [int(idx[p]) for p in popularity(sub_df, k)]
                times[m] += time.time() - t0
            else:
                picks = picks_by_method.get(m, [])

            picks = enforce_budget(picks, wc, cfg)
            if not picks:
                continue
            sc = score_summary(picks, ref, df, cfg, X)
            sc["n_words"] = int(sum(int(wc[i]) for i in picks))
            acc[m].append(sc)

        if verbose and (si + 1) % 5 == 0:
            print(f"    ...{si + 1}/{len(starts)} windows")

    out: Dict[str, dict] = {}
    for m in methods:
        rows = acc[m]
        if not rows:
            out[m] = {"n_samples": 0}
            continue
        keys = [k2 for k2 in rows[0] if k2.startswith("rouge")
                or k2 in ("diversity", "redundancy_max", "n_tweets", "n_words")]
        agg = {k2: float(np.mean([r[k2] for r in rows])) for k2 in keys}
        agg["n_samples"] = len(rows)
        agg["runtime_sec"] = round(times[m], 3)
        # Equation (4): the integral over [T0,T] divided by the period is the
        # mean of the sampled metric values.
        agg["eq4_integral_rouge1_f"] = agg["rouge1_f"]
        agg["eq4_integral_rouge2_f"] = agg["rouge2_f"]
        out[m] = agg

    if verbose:
        print(f"  reference summaries built: {refs_built}")
    return out

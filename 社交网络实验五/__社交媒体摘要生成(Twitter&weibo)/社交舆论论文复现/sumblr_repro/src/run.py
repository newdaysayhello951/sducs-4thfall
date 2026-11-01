"""Sumblr reproduction -- main pipeline.

Runs the full Shou et al. (SIGIR 2013) pipeline on the Turkey earthquake
tweet stream:

    load -> TF-IDF -> online clustering (TCV) -> TCV-Rank summary
         -> baselines -> ROUGE + reference-free diagnostics -> outputs

Usage:
    python src/run.py                 # default day (2023-02-10), all tweets
    python src/run.py --day 2023-02-11
    python src/run.py --max-tweets 3000
    python src/run.py --all-days
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SumblrConfig, OUT_DIR
from preprocess import load_tweets, build_vectors, tokenize, count_words
from sumblr import SumblrClusterer
from summarize import TCVSummarizer, detect_timeline
from evaluate import (baseline_random, baseline_popularity, baseline_lead,
                      baseline_lexrank, baseline_clustersum, build_reference,
                      evaluate, save_json, enforce_budget)


def parse_args():
    p = argparse.ArgumentParser(description="Sumblr reproduction pipeline")
    p.add_argument("--day", default="2023-02-10",
                   help="experiment day (YYYY-MM-DD); ignored with --all-days")
    p.add_argument("--all-days", action="store_true",
                   help="use the whole stream instead of a single day")
    p.add_argument("--max-tweets", type=int, default=None,
                   help="cap the number of tweets")
    p.add_argument("--beta", type=float, default=0.07)
    p.add_argument("--n-max", type=int, default=150)
    p.add_argument("--m", type=int, default=40)
    p.add_argument("--lam", type=float, default=0.4)
    p.add_argument("--summary-words", type=int, default=250)
    p.add_argument("--k", type=int, default=25,
                   help="summary tweet cap (paper's k/L not stated)")
    p.add_argument("--no-freshness", action="store_true",
                   help="disable outdated-cluster deletion")
    p.add_argument("--sim-mode", default="paper",
                   choices=["paper", "absolute"],
                   help="MBS rule: paper's beta*avg_sim, or absolute beta")
    p.add_argument("--tag", default="", help="suffix for output filenames")
    p.add_argument("--timeline-step", type=int, default=None,
                   help="minutes between timeline windows (default: window "
                        "length, i.e. non-overlapping)")
    p.add_argument("--timeline-window", type=int, default=None,
                   help="timeline window length in minutes (default 120)")
    p.add_argument("--tau", type=float, default=None,
                   help="evolvement threshold (paper 1.012; our stream's "
                        "optimum is ~1.06, see REPORT.md)")
    return p.parse_args()


def build_timeline_summaries(df, X, X_norm, wc, cfg: SumblrConfig,
                             clusterer, window_min: int = 360,
                             step_min: int = None):
    """Build successive summaries for topic-evolvement detection (Sec. 4.3).

    The paper's timeline compares successive *summaries*, and its online
    summaries come from "the current clusters maintained in memory". Comparing
    the whole cumulative state makes consecutive summaries nearly identical
    (D_KL -> 0), while comparing disjoint bins makes them share almost no
    vocabulary (D_KL ~ 10, so D = 1 - e^-KL saturates at 1.0 and no ratio can
    exceed tau). Neither extreme is informative.

    We therefore summarize a window of the stream -- the content that is
    "current" at each point -- so successive summaries overlap partially, which
    is the regime the D_cur / D_avg test is designed for.

    `step_min` controls how far the window advances. Leaving it at the snapshot
    interval (default) creates heavy overlap: a 360-minute window with a
    60-minute step overlaps 6x, so adjacent summaries are nearly identical and D
    collapses to a narrow band (measured mean 0.530, std 0.083, CV 0.156). With
    that little spread, any tau > 1 flags 50-90% of windows as nodes, which is
    meaningless. Pass step_min == window_min for the paper's non-overlapping
    successive periods.
    """
    t0 = df["dt"].iloc[0]
    step = pd.Timedelta(minutes=step_min if step_min else cfg.snapshot_minutes)
    win = pd.Timedelta(minutes=window_min)
    bins = []

    t = df["dt"].iloc[0] + win
    end = df["dt"].iloc[-1]
    while t <= end:
        m = (df["dt"] > t - win) & (df["dt"] <= t)
        sub = df[m]
        if len(sub) < 30:
            t += step
            continue
        # Summarize the tweets inside this window with a fresh Sumblr run,
        # so the "current clusters" reflect the window's content.
        idxs = sub.index.to_numpy()
        sub_ts = (sub["dt"] - sub["dt"].iloc[0]).dt.total_seconds().to_numpy()
        Xs, Xs_norm = X[idxs], X_norm[idxs]
        c = SumblrConfig(**{**cfg.__dict__, "verbose": False,
                            "init_size": min(cfg.init_size, len(sub))})
        cl = SumblrClusterer(c, dim=X.shape[1])
        cl.initialize(Xs, Xs_norm, sub_ts)
        cl.process(Xs, Xs_norm, sub_ts, start=c.init_size)

        s = TCVSummarizer(c, Xs)
        s.word_counts = wc[idxs]
        r = s.summarize(cl.clusters)

        cnt = {}
        for li in r["tweets"]:
            for w in tokenize(sub["text"].iloc[li], c):
                cnt[w] = cnt.get(w, 0) + 1
        if not cnt:
            t += step
            continue
        bins.append({"ts": (t - t0).total_seconds(), "hour": str(t),
                     "n": len(sub), "word_counts": cnt})
        t += step

    info = {"n_bins": len(bins),
            "granularity": f"{window_min}-min window, "
                           f"{int(step.total_seconds() // 60)}-min step",
            "overlap_factor": round(window_min /
                                    max(1, int(step.total_seconds() // 60)), 2),
            "method": "KL between successive window summaries"}
    return info, bins


def main() -> int:
    args = parse_args()

    cfg = SumblrConfig(
        day=None if args.all_days else args.day,
        max_tweets=args.max_tweets,
        beta=args.beta,
        n_max=args.n_max,
        m=args.m,
        lam=args.lam,
        summary_words=args.summary_words,
        max_summary_tweets=args.k,
    )
    if args.no_freshness:
        cfg.freshness_days = 1e9
    if args.timeline_window:
        cfg.timeline_window_min = args.timeline_window
    if args.tau is not None:
        cfg.tau = args.tau

    t0 = time.time()
    print("=" * 72)
    print("Sumblr reproduction -- Shou et al., SIGIR 2013")
    print(f"day={cfg.day}  max_tweets={cfg.max_tweets}  beta={cfg.beta} "
          f"n_max={cfg.n_max}  m={cfg.m}  lambda={cfg.lam}")
    print("=" * 72)

    # ---- 1. Data + vectors ------------------------------------------------
    df = load_tweets(cfg)
    if len(df) < 50:
        print("[run] ERROR: too few tweets after filtering; pick another day")
        return 1
    X, X_norm, vec = build_vectors(df, cfg)
    ts = df["ts"].to_numpy()

    # Auto-scale the timeline window now that the stream span is known, so the
    # number of successive summaries stays in the low tens. With too few bins
    # the D_cur / D_avg test has no history; with too many, D's narrow spread
    # (CV ~0.05 on this corpus) makes almost every window a "node".
    if not args.timeline_window:
        span_min = max(1.0, (df["dt"].iloc[-1] - df["dt"].iloc[0])
                       .total_seconds() / 60.0)
        cfg.timeline_window_min = int(max(
            60, round(span_min / max(1, cfg.timeline_target_bins))))
    # Timeline window advance: default to a full window (non-overlapping), the
    # regime the paper's D_cur / D_avg test assumes. Kept separate from
    # snapshot_minutes, which controls PTF resolution.
    tl_step = (args.timeline_step if args.timeline_step
               else cfg.timeline_window_min)

    # ---- 2. Online clustering --------------------------------------------
    cl = SumblrClusterer(cfg, dim=X.shape[1])
    cl.sim_mode = args.sim_mode
    cl.initialize(X, X_norm, ts)
    cl.process(X, X_norm, ts, start=cfg.init_size)
    cstats = cl.stats()
    print("[run] clustering stats:")
    for k, v in cstats.items():
        print(f"        {k:22} {v}")

    # ---- 3. TCV-Rank summarization ---------------------------------------
    # Word counts for the length budget: raw whitespace words, matching the
    # paper's "summary length is limited to 250 words".
    wc = np.array([max(1, count_words(t)) for t in df["text"]])
    summ = TCVSummarizer(cfg, X)
    summ.word_counts = wc
    res = summ.summarize(cl.clusters)
    sys_ids = res["tweets"]
    print(f"[run] summary: {len(sys_ids)} tweets, {res.get('words', 0)} words "
          f"(candidates T={res.get('T_size', 0)}, clusters={res.get('clusters_used', 0)})")

    # ---- 4. Ground truth + baselines -------------------------------------
    k = cfg.max_summary_tweets
    ref_ids, cands = build_reference(df, X, cfg, k)
    print(f"[run] reference summary (paper's >=2-of-3 recipe): {len(ref_ids)} tweets")

    methods = {
        "Sumblr": sys_ids,
        "Random": baseline_random(df, k, cfg.seed),
        "Popularity": baseline_popularity(df, k),
        "Lead": baseline_lead(df, k),
        "ClusterSum": baseline_clustersum(df, X, k, cfg),
        "LexRank": baseline_lexrank(df, X, k, cfg),
    }

    # Enforce the paper's shared length budget on every method: a fixed word
    # limit and a fixed tweet cap. Without this, methods that happen to pick
    # long tweets are credited with more content than the paper allows.
    methods = {name: enforce_budget(ids, wc, cfg) for name, ids in methods.items()}
    ref_ids = enforce_budget(ref_ids, wc, cfg)
    print(f"[run] length-normalized: <= {cfg.summary_words} words, "
          f"<= {cfg.max_summary_tweets} tweets per method")
    print(f"[run] reference after normalization: {len(ref_ids)} tweets, "
          f"{int(wc[ref_ids].sum())} words")

    # ---- 5. Evaluation ----------------------------------------------------
    table = {}
    for name, ids in methods.items():
        table[name] = evaluate(ids, ref_ids, df, cfg, X)

    print()
    print("=" * 88)
    print("ROUGE vs. reference summary (paper's recipe) + reference-free diagnostics")
    print("=" * 88)
    hdr = (f"{'method':<12}{'R-1 F':>8}{'R-2 F':>8}{'R-L F':>8}"
           f"{'cover':>8}{'idf':>7}{'div':>7}{'red_max':>9}{'#tw':>5}{'#tok':>6}")
    print(hdr)
    print("-" * len(hdr))
    for name, mt in table.items():
        print(f"{name:<12}{mt['rouge1_f']:>8.4f}{mt['rouge2_f']:>8.4f}"
              f"{mt['rougeL_f']:>8.4f}"
              f"{mt.get('term_coverage', 0):>8.4f}"
              f"{mt.get('mean_idf', 0):>7.2f}"
              f"{mt.get('diversity_mean_dist', 0):>7.3f}"
              f"{mt.get('redundancy_max_sim', 0):>9.3f}"
              f"{mt['summary_tweets']:>5d}{mt['summary_words']:>6d}")
    print("  (#tok = tokens after cleaning/stemming; the shared 250-word budget"
          " is enforced on raw words)")

    # ---- 6. Timeline (topic evolvement) ----------------------------------
    # The paper compares successive *summaries* (Section 4.3: "the distance
    # between current summary and its previous neighboring summary"), not whole
    # time bins. Comparing raw bins makes the vocabulary large and disjoint, so
    # D_KL ~ 10 and D = 1 - e^-KL saturates at 1 for every pair, which destroys
    # the D_cur / D_avg test. We therefore summarize each bin with the same
    # Sumblr machinery and compare those summaries.
    #
    # The window advances by a full window (non-overlapping), matching the
    # paper's "successive summaries as the stream advances". A heavy overlap
    # (e.g. 360-min window with a 60-min step = 6x) makes adjacent summaries
    # nearly identical, collapsing D into a narrow band and flagging ~half of
    # all windows as evolvement nodes.
    tl, summ_by_hour = build_timeline_summaries(
        df, X, X_norm, wc, cfg, cl,
        window_min=cfg.timeline_window_min,
        step_min=tl_step)
    nodes, tl_series = detect_timeline(summ_by_hour, cfg)
    # Attach the human-readable window label so the saved JSON is self-describing
    # (the raw node records only carry a seconds offset).
    for nd in nodes:
        nd["hour"] = summ_by_hour[nd["index"]]["hour"]
    tl["n_nodes"] = len(nodes)
    tl["nodes"] = nodes
    tl["series"] = tl_series
    print()
    print(f"[run] timeline: {len(summ_by_hour)} bins -> {len(nodes)} evolvement "
          f"nodes (tau={cfg.tau})")
    for nd in nodes[:10]:
        print(f"        {summ_by_hour[nd['index']]['hour']}  "
              f"D={nd['distance']:.4f}  D/D_avg={nd['ratio']:.2f}")
    if not nodes and tl_series:
        ds = [s["distance"] for s in tl_series]
        rs = [s["ratio"] for s in tl_series]
        print(f"        [diag] D range [{min(ds):.4f}, {max(ds):.4f}]  "
              f"ratio range [{min(rs):.2f}, {max(rs):.2f}]  "
              f"max ratio vs tau={cfg.tau}")

    # ---- 7. Persist -------------------------------------------------------
    tag = f"_{args.tag}" if args.tag else ""
    suffix = "alldays" if cfg.day is None else cfg.day

    out = {
        "config": {k2: (list(v) if isinstance(v, set) else v)
                   for k2, v in cfg.__dict__.items()},
        "n_tweets": int(len(df)),
        "time_span": [str(df["dt"].min()), str(df["dt"].max())],
        "clustering": cstats,
        "summary_stats": {k2: v for k2, v in res.items()
                          if k2 not in ("lexrank", "T")},
        "metrics": table,
        "timeline": tl,
        "reference_recipe": "tweets selected by >=2 of {ClusterSum, LexRank, Popularity}",
        "runtime_sec": round(time.time() - t0, 2),
    }
    p1 = save_json(out, f"results_{suffix}{tag}.json")

    # Human-readable summary + reference
    import pandas as pd
    def dump(ids, path, label):
        rows = []
        for rank, i in enumerate(ids, 1):
            rows.append({
                "rank": rank,
                "id": df["id"].iloc[i],
                "dt": str(df["dt"].iloc[i]),
                "retweets": int(df["retweets"].iloc[i]),
                "favorites": int(df["favorites"].iloc[i]),
                "text": df["text"].iloc[i],
            })
        pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
        return path

    os.makedirs(OUT_DIR, exist_ok=True)
    p2 = dump(sys_ids, os.path.join(OUT_DIR, f"system_summary_{suffix}{tag}.csv"),
              "Sumblr")
    p3 = dump(ref_ids, os.path.join(OUT_DIR, f"reference_summary_{suffix}{tag}.csv"),
              "reference")

    print()
    print(f"[run] wrote {p1}")
    print(f"[run] wrote {p2}")
    print(f"[run] wrote {p3}")
    print(f"[run] total runtime {out['runtime_sec']}s")

    # ---- 8. Show the actual summary --------------------------------------
    print()
    print("=" * 72)
    print("Sumblr summary (top 12 tweets)")
    print("=" * 72)
    for rank, i in enumerate(sys_ids[:12], 1):
        txt = df["text"].iloc[i].replace("\n", " ")
        print(f"{rank:>3}. [{str(df['dt'].iloc[i])[:16]}] {txt[:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

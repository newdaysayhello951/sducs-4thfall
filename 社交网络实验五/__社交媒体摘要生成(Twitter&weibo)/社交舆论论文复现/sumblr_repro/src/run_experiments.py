"""Run the paper's Section 5 experiments.

  --step-sweep    Section 5.2 / Figures 5 & 6: quality and runtime vs step size
  --scalability   Section 5.2 / Figure 7: runtime vs data (window) size
  --params        Section 5.3 / Figure 9: effect of beta, Nmax, mc, m, lambda
  --flexibility   Section 5.4 / Figure 10: PTF accuracy vs l for drill-down /
                  roll-up summaries over durations of varying length
  --timeline      Section 5.5 / Figure 11: timeline precision/recall/F vs tau
  --all           all of the above

Scale note: the paper uses window size 20000 and step 4000-20000 on 95k-438k
tweet streams. Our substitute stream has ~27.7k tweets, so the protocol is
scaled down while preserving the paper's ratios (step/window in [0.2, 1.0] and
sampling interval <= step). The scaling factor is recorded in the output.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SumblrConfig, OUT_DIR
from preprocess import load_tweets, build_vectors, count_words, tokenize
from sumblr import SumblrClusterer
from summarize import TCVSummarizer, detect_timeline, kl_divergence, \
    normalized_distance
from historical import HistoricalSummarizer
from experiments import sliding_window_experiment
from evaluate import save_json


def build_stream(args):
    cfg = SumblrConfig(day=None, verbose=False,
                       max_tweets=args.max_tweets,
                       beta=args.beta, n_max=args.n_max, m=args.m,
                       lam=args.lam, ptf_l=args.ptf_l, alpha=args.alpha,
                       snapshot_minutes=args.snapshot_minutes)
    df = load_tweets(cfg)
    X, X_norm, _ = build_vectors(df, cfg)
    wc = np.array([max(1, count_words(t)) for t in df["text"]])
    return cfg, df, X, X_norm, wc


def build_clusterer(cfg, X, X_norm, ts):
    cl = SumblrClusterer(cfg, dim=X.shape[1])
    cl.initialize(X, X_norm, ts)
    cl.process(X, X_norm, ts, start=cfg.init_size)
    return cl


def make_summarizer_factory(cfg, wc):
    def factory(Xm):
        s = TCVSummarizer(cfg, Xm)
        s.word_counts = wc
        return s
    return factory


# ---------------------------------------------------------------------------
def exp_step_sweep(args):
    """Section 5.2, Figures 5 (quality) and 6 (efficiency) vs step size."""
    cfg, df, X, X_norm, wc = build_stream(args)
    ts = df["ts"].to_numpy()
    n = len(df)
    print(f"[step-sweep] stream = {n} tweets")

    cl = build_clusterer(cfg, X, X_norm, ts)
    hist = HistoricalSummarizer(cfg, cl.ptf, X.shape[1],
                                make_summarizer_factory(cfg, wc))
    print(f"[step-sweep] PTF: {json.dumps(cl.ptf.stats())}")

    window = args.window
    steps = [int(window * r) for r in args.step_ratios]
    steps = [s for s in steps if 0 < s <= window]
    results = {"window_size": window, "steps": steps, "by_step": {}}

    for step in steps:
        sampling = max(1, min(step, window // 10))
        print(f"\n[step-sweep] step={step} (ratio {step/window:.2f}), "
              f"sampling={sampling}")
        t0 = time.time()
        res = sliding_window_experiment(
            df, X, wc, cfg, window_size=window, step_size=step,
            sampling_interval=sampling, historical=hist,
            k=args.k, max_windows=args.max_windows, verbose=True)
        results["by_step"][str(step)] = res
        results["by_step"][str(step)]["_elapsed"] = round(time.time() - t0, 2)
        for m, mt in res.items():
            if isinstance(mt, dict) and mt.get("n_samples"):
                print(f"    {m:11} R-1 F={mt['rouge1_f']:.4f} "
                      f"R-2 F={mt['rouge2_f']:.4f} "
                      f"runtime={mt['runtime_sec']:.2f}s "
                      f"(n={mt['n_samples']})")

    save_json(results, f"exp_step_sweep_w{window}.json")
    return results


def exp_scalability(args):
    """Section 5.2, Figure 7: runtime vs data (window) size, log scale."""
    cfg, df, X, X_norm, wc = build_stream(args)
    ts = df["ts"].to_numpy()
    print("[scalability] single-window runtime vs window size")
    out = {}
    for w in args.scale_sizes:
        if w > len(df):
            continue
        idx = np.arange(0, w)
        row = {}
        from baselines import clustersum, lexrank, dsdr
        for name, fn in (("ClusterSum", clustersum), ("LexRank", lexrank),
                         ("DSDR", dsdr)):
            t0 = time.time()
            fn(X, args.k, cfg, idx)
            row[name] = round(time.time() - t0, 3)
        # Sumblr on the same data: cluster it, then summarize.
        t0 = time.time()
        c2 = SumblrConfig(**{**cfg.__dict__, "verbose": False,
                             "init_size": min(cfg.init_size, w)})
        cl = SumblrClusterer(c2, dim=X.shape[1])
        cl.initialize(X[:w], X_norm[:w], ts[:w])
        cl.process(X[:w], X_norm[:w], ts[:w], start=c2.init_size)
        s = TCVSummarizer(c2, X[:w])
        s.word_counts = wc[:w]
        s.summarize(cl.clusters)
        row["Sumblr"] = round(time.time() - t0, 3)
        out[str(w)] = row
        print(f"  window={w:>6}: " +
              "  ".join(f"{k}={v:7.3f}s" for k, v in row.items()))
    save_json({"by_size": out}, "exp_scalability.json")
    return out


def exp_params(args):
    """Section 5.3, Figure 9: beta, Nmax, mc, m, lambda."""
    cfg0, df, X, X_norm, wc = build_stream(args)
    ts = df["ts"].to_numpy()
    # The sweep needs 47 full clustering runs. The paper sweeps on full streams
    # (95k-438k); we cap the stream to keep the sweep tractable and record it.
    cap = min(args.param_stream, len(df))
    df, X, X_norm, wc, ts = (df.iloc[:cap].reset_index(drop=True),
                             X[:cap], X_norm[:cap], wc[:cap], ts[:cap])
    print(f"[params] parameter sweeps on {cap} tweets "
          f"(paper sweeps on full 95k-438k streams)")

    # Precompute the IDF table once instead of per configuration.
    from collections import Counter
    docs = [set(tokenize(t, cfg0)) for t in df["text"]]
    dfreq = Counter()
    for d in docs:
        dfreq.update(d)
    idf = {w: float(np.log(len(docs) / (1 + dfreq[w]))) for w in dfreq}
    tokens_cache = [tokenize(t, cfg0) for t in df["text"]]
    out = {}

    def evaluate_params(**over):
        c = SumblrConfig(**{**cfg0.__dict__, **over, "verbose": False})
        cl = SumblrClusterer(c, dim=X.shape[1])
        t0 = time.time()
        cl.initialize(X, X_norm, ts)
        cl.process(X, X_norm, ts, start=c.init_size)
        runtime = time.time() - t0
        s = TCVSummarizer(c, X)
        s.word_counts = wc
        res = s.summarize(cl.clusters)
        picks = res["tweets"]
        vals = [idf.get(w, 0.0) for i in picks for w in tokens_cache[i]]
        st = cl.stats()
        return {
            "n_selected": len(picks),
            "mean_idf": float(np.mean(vals)) if vals else 0.0,
            "runtime_sec": round(runtime, 2),
            "clusters_alive": st["clusters_alive"],
            "clusters_merged": st["clusters_merged"],
            "clusters_deleted": st["clusters_deleted"],
            "largest_cluster_share": st["largest_cluster_share"],
        }

    sweeps = {
        "beta": ([0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11], "beta"),
        "n_max": ([30, 50, 70, 90, 110, 130, 150, 170, 190, 210], "n_max"),
        "mc": ([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9], "mc"),
        "m": ([10, 20, 30, 40, 50, 60, 70, 80], "m"),
        "lam": ([round(x, 1) for x in np.arange(0.0, 1.01, 0.1)], "lam"),
    }
    for name, (values, key) in sweeps.items():
        out[name] = {}
        print(f"\n  --- {name} ---")
        for v in values:
            r = evaluate_params(**{key: v})
            out[name][str(v)] = r
            print(f"    {name}={v:<5} sel={r['n_selected']:>3} "
                  f"idf={r['mean_idf']:.3f} runtime={r['runtime_sec']:>6.2f}s "
                  f"alive={r['clusters_alive']:>4} merged={r['clusters_merged']:>4}")
    save_json(out, "exp_params.json")
    return out


def exp_flexibility(args):
    """Section 5.4, Figure 10: PTF accuracy for drill-down/roll-up summaries.

    The paper fixes alpha=2, uses a one-month subset, one-hour snapshot
    interval, and durations len = 1..10 days, reporting
        score(ts) = sum_len F-score([ts-len, ts]) / 10            (Equation 5)
    sampled by 48-hour intervals. We follow the same shape on our 20-day
    stream with day-scale durations.
    """
    cfg, df, X, X_norm, wc = build_stream(args)
    ts = df["ts"].to_numpy()
    print("[flexibility] drill-down / roll-up accuracy vs l")
    out = {}
    unit = cfg.snapshot_minutes * 60
    last_tick = int(ts.max() // unit)

    # The reference summary for a given (ts, len) depends only on the time
    # range, NOT on l, so build each one once and reuse it across all l values.
    # Without this cache the reference (which includes the O(k*n^2*d) DSDR
    # baseline) is rebuilt 3x for l in {3,5,8}, which dominates the runtime.
    ref_cache: dict = {}

    def reference_for(tse: int, h_ticks: int, c: SumblrConfig):
        key = (tse, h_ticks)
        if key in ref_cache:
            return ref_cache[key]
        lo = (tse - h_ticks) * unit
        hi = tse * unit
        ref_idx = np.where((ts >= lo) & (ts <= hi))[0]
        if len(ref_idx) < 10:
            ref_cache[key] = None
            return None
        # Cap the pool the reference is built from (DSDR is O(n^2)).
        if len(ref_idx) > args.ref_cap:
            sel = np.linspace(0, len(ref_idx) - 1, args.ref_cap).astype(int)
            ref_idx = ref_idx[sel]
        from experiments import window_reference, enforce_budget
        ref = window_reference(X, wc, c, ref_idx, args.k)
        ref = enforce_budget(ref, wc, c)
        ref_cache[key] = ref if ref else None
        return ref_cache[key]

    for l in args.l_values:
        c = SumblrConfig(**{**cfg.__dict__, "ptf_l": l, "verbose": False})
        cl = build_clusterer(c, X, X_norm, ts)
        hist = HistoricalSummarizer(c, cl.ptf, X.shape[1],
                                    make_summarizer_factory(c, wc))
        ptf_stats = cl.ptf.stats()
        rows = []
        # Sample ts by 48-hour intervals, per the paper.
        for hours_back in range(48, int(ts.max() // 3600) + 1, 48):
            tse = last_tick - int(round(hours_back / (c.snapshot_minutes / 60)))
            if tse <= 0:
                continue
            fs = []
            for len_days in range(1, 11):          # len = 1..10 days
                h_ticks = int(round(len_days * 24 * 60 / c.snapshot_minutes))
                r = hist.summarize_window(tse, h_ticks, X)
                if not r.get("tweets"):
                    continue
                # Reference: a reference SUMMARY for the same duration, built
                # with the paper's recipe. Using the raw tweets in the range as
                # the reference would make ROUGE meaningless: the summary holds
                # ~250 words while the range holds thousands, so recall
                # collapses to ~0 (we measured 0.011 before this fix).
                ref = reference_for(tse, h_ticks, c)
                if not ref:
                    continue
                from experiments import score_summary
                sc = score_summary(r["tweets"], ref, df, c, X)
                fs.append(sc["rouge1_f"])
            if fs:
                rows.append({"ts_hours_back": hours_back,
                             "score_eq5": float(np.mean(fs)),
                             "n_len": len(fs)})
        out[str(l)] = {
            "ptf": ptf_stats,
            "n_samples": len(rows),
            "mean_score_eq5": float(np.mean([r["score_eq5"] for r in rows]))
            if rows else 0.0,
            "rows": rows,
        }
        print(f"  l={l}: snapshots={ptf_stats['n_live']:>4} "
              f"orders={ptf_stats['orders_used']} "
              f"mean score(Eq.5)={out[str(l)]['mean_score_eq5']:.4f} "
              f"(n={len(rows)})")
    save_json(out, "exp_flexibility.json")
    return out


def exp_timeline(args):
    """Section 5.5, Figure 11: timeline precision/recall/F vs tau.

    The paper builds reference timelines manually for two sports topics. Our
    substitute stream is a disaster event, so we derive the reference timeline
    from documented event dates (earthquake milestones) and evaluate whether
    detected nodes land on them within a tolerance window. The reference is
    therefore approximate; this is recorded in the output and README.
    """
    cfg, df, X, X_norm, wc = build_stream(args)
    ts = df["ts"].to_numpy()
    print("[timeline] precision/recall/F vs tau")
    cl = build_clusterer(cfg, X, X_norm, ts)
    unit = cfg.snapshot_minutes * 60

    # Build successive summaries for evolvement detection.
    #
    # IMPORTANT: the paper compares successive summaries produced as the stream
    # advances (Section 4.3), i.e. over *consecutive, non-overlapping* periods.
    # Using a heavily overlapping sliding window (e.g. 360-min window with a
    # 60-min step = 6x overlap) makes adjacent summaries nearly identical, so D
    # collapses into a narrow band (we measured mean 0.530, std 0.083, i.e. a
    # coefficient of variation of only 0.156). With such a narrow spread any
    # tau > 1 flags ~50-90% of windows as "evolvement nodes", which is
    # meaningless. We therefore use a non-overlapping step equal to the window
    # (the paper's one-hour snapshot interval over day-scale periods).
    from run import build_timeline_summaries
    step_min = args.tl_step if args.tl_step else args.tl_window
    info, bins = build_timeline_summaries(df, X, X_norm, wc, cfg, cl,
                                          window_min=args.tl_window,
                                          step_min=step_min)
    print(f"  {len(bins)} summary bins ({info['granularity']})")

    # Reference timeline: documented milestones of the 2023 Turkey-Syria
    # earthquake, expressed as hours since stream start. This is a SUBSTITUTE
    # for the paper's manually built reference timelines (it read news from
    # Yahoo!/ESPN for two sports topics). It is approximate: it lists the
    # widely reported milestones, not an exhaustive event list, so precision is
    # the meaningful number here and recall should be read with care.
    t0 = df["dt"].iloc[0]
    milestones = [
        ("2023-02-07 10:00", "initial M7.8 quake, mass casualties reported"),
        ("2023-02-08 00:00", "international rescue teams arrive"),
        ("2023-02-09 00:00", "death toll passes 15k"),
        ("2023-02-10 00:00", "death toll passes 20k, aid surge"),
        ("2023-02-11 00:00", "WHO warns of secondary disaster"),
        ("2023-02-13 00:00", "death toll passes 35k, shelter crisis"),
        ("2023-02-15 00:00", "focus shifts to survivors and housing"),
        ("2023-02-18 00:00", "aid distribution and rebuilding debate"),
        ("2023-02-20 12:00", "M6.4 aftershock in Hatay/Antakya"),
        ("2023-02-24 00:00", "death toll passes 50k, reconstruction begins"),
    ]
    ref_hours = []
    for s, _label in milestones:
        try:
            import pandas as pd
            d = pd.to_datetime(s).tz_localize(None)
            h = (d - t0).total_seconds() / 3600.0
            if 0 <= h <= (ts.max() / 3600.0):
                ref_hours.append(h)
        except Exception:
            pass
    print(f"  reference milestones within stream: {len(ref_hours)}")

    out = {}
    tol_hours = args.tl_tolerance
    for tau in args.tau_values:
        c = SumblrConfig(**{**cfg.__dict__, "tau": tau, "verbose": False})
        if args.davg_mode:
            c.davg_mode = args.davg_mode
        nodes, series = detect_timeline(bins, c)
        det_hours = [b["ts"] / 3600.0 for b in
                     (bins[n["index"]] for n in nodes)]

        matched_ref, matched_det = set(), set()
        for di, dh in enumerate(det_hours):
            for ri, rh in enumerate(ref_hours):
                if abs(dh - rh) <= tol_hours and ri not in matched_ref:
                    matched_ref.add(ri)
                    matched_det.add(di)
                    break
        tp = len(matched_det)
        prec = tp / len(det_hours) if det_hours else 0.0
        rec = tp / len(ref_hours) if ref_hours else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        out[str(tau)] = {"n_nodes": len(nodes), "precision": round(prec, 4),
                         "recall": round(rec, 4), "f1": round(f1, 4),
                         "tp": tp, "n_ref": len(ref_hours)}
        print(f"  tau={tau:<6} nodes={len(nodes):>3} P={prec:.3f} "
              f"R={rec:.3f} F1={f1:.3f}")

    save_json({"bins": len(bins), "reference": milestones,
               "tolerance_hours": tol_hours, "by_tau": out},
              "exp_timeline.json")
    return out


def main():
    # Line-buffer stdout so progress is visible when redirected to a log file.
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    p = argparse.ArgumentParser()
    p.add_argument("--max-tweets", type=int, default=None)
    p.add_argument("--beta", type=float, default=0.07)
    p.add_argument("--n-max", type=int, default=150)
    p.add_argument("--m", type=int, default=40)
    p.add_argument("--lam", type=float, default=0.4)
    p.add_argument("--ptf-l", type=int, default=3)
    p.add_argument("--alpha", type=int, default=2)
    p.add_argument("--snapshot-minutes", type=int, default=60)
    p.add_argument("--k", type=int, default=25)
    # step sweep
    p.add_argument("--window", type=int, default=3000,
                   help="window size in tweets (paper: 20000 on 95k-438k)")
    p.add_argument("--step-ratios", type=float, nargs="+",
                   default=[0.2, 0.4, 0.6, 0.8, 1.0],
                   help="step/window ratios (paper: 4000..20000 / 20000)")
    # scalability
    p.add_argument("--scale-sizes", type=int, nargs="+",
                   default=[500, 1000, 2000, 4000, 8000])
    # flexibility
    p.add_argument("--l-values", type=int, nargs="+", default=[3, 5, 8])
    # timeline
    p.add_argument("--tau-values", type=float, nargs="+",
                   default=[1.000, 1.012, 1.025, 1.040, 1.060, 1.080,
                            1.100, 1.150],
                   help="tau sweep. The paper's optimum (1.012) was calibrated "
                        "on its own 95k-438k-tweet streams; on our substitute "
                        "stream D has a much narrower spread (CV 0.06 vs the "
                        "paper's regime), so the informative range extends "
                        "well above 1.012.")
    p.add_argument("--tl-window", type=int, default=360)
    p.add_argument("--tl-step", type=int, default=None,
                   help="minutes the timeline window advances; default = "
                        "tl-window (non-overlapping, per the paper). A smaller "
                        "value creates overlap and collapses D into a narrow "
                        "band, inflating node counts.")
    p.add_argument("--davg-mode", default=None,
                   choices=[None, "paper", "paper_strict", "all"],
                   help="D_avg estimator for the tau test; see detect_timeline")
    p.add_argument("--tl-tolerance", type=float, default=12.0,
                   help="hours; a node matches a milestone within this window")
    p.add_argument("--param-stream", type=int, default=8000,
                   help="tweets used for the parameter sweeps (47 clustering "
                        "runs; the paper sweeps on full streams)")
    p.add_argument("--ref-cap", type=int, default=600,
                   help="max tweets used to build a reference summary; DSDR is "
                        "O(k*n^2*d) so this bounds the reference cost")
    p.add_argument("--max-windows", type=int, default=8,
                   help="cap on windows per step size (DSDR is O(k*n^2*d))")
    p.add_argument("--which", nargs="+", default=["all"],
                   choices=["all", "step", "scalability", "params",
                            "flexibility", "timeline"])
    args = p.parse_args()

    which = args.which
    do_all = "all" in which
    t_start = time.time()
    if do_all or "step" in which:
        print("=" * 72); print("EXPERIMENT: step-size sweep (Fig. 5 & 6)")
        print("=" * 72)
        exp_step_sweep(args)
    if do_all or "scalability" in which:
        print("=" * 72); print("EXPERIMENT: scalability (Fig. 7)")
        print("=" * 72)
        exp_scalability(args)
    if do_all or "params" in which:
        print("=" * 72); print("EXPERIMENT: parameter sweeps (Fig. 9)")
        print("=" * 72)
        exp_params(args)
    if do_all or "flexibility" in which:
        print("=" * 72); print("EXPERIMENT: flexibility / PTF (Fig. 10)")
        print("=" * 72)
        exp_flexibility(args)
    if do_all or "timeline" in which:
        print("=" * 72); print("EXPERIMENT: timeline P/R/F vs tau (Fig. 11)")
        print("=" * 72)
        exp_timeline(args)
    print(f"\n[done] total {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()

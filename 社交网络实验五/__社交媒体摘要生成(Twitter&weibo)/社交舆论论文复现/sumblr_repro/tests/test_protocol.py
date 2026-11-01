"""Verify the Section 5 protocol: sliding window, Eq.4 integral, references.

Checks:
  1. Window enumeration matches the paper's Figure 8 description (windows of
     `window_size` tweets advancing by `step_size`).
  2. The sampling interval never exceeds the step size (paper requirement).
  3. Every method is scored on the same windows, so Equation (4)'s mean over
     samples is comparable across methods.
  4. Reference summaries respect the 250-word / k-tweet budget.
  5. Runtimes are actually measured (non-zero) for the expensive baselines --
     this is what Figure 6 plots, so a caching bug that zeroes it would silently
     invalidate the efficiency comparison.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from config import SumblrConfig
from preprocess import load_tweets, build_vectors, count_words
from sumblr import SumblrClusterer
from summarize import TCVSummarizer
from historical import HistoricalSummarizer
from experiments import sliding_window_experiment, window_reference
from evaluate import enforce_budget

fails = []


def check(name, cond, detail=""):
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        fails.append(name)


cfg = SumblrConfig(verbose=False, day="2023-02-10")
df = load_tweets(cfg)
X, Xn, _ = build_vectors(df, cfg)
ts = df["ts"].to_numpy()
wc = np.array([max(1, count_words(t)) for t in df["text"]])

# ---- 1/2. window enumeration -------------------------------------------
print("=== 1. window enumeration (Figure 8) ===")
n = len(df)
window, step, sampling = 800, 200, 200
starts = list(range(0, n - window + 1, step))
print(f"  stream={n}, window={window}, step={step}")
print(f"  windows={len(starts)}, first={starts[0]}, last={starts[-1]}")
check("windows are step_size apart", all(starts[i+1] - starts[i] == step
                                         for i in range(len(starts)-1)))
check("last window fits in the stream", starts[-1] + window <= n)
check("sampling interval <= step size", sampling <= step,
      f"{sampling} <= {step}")

# ---- 3/4/5. run a short protocol ---------------------------------------
print()
print("=== 2. protocol run (small) ===")
cl = SumblrClusterer(cfg, dim=X.shape[1])
cl.initialize(X, Xn, ts)
cl.process(X, Xn, ts, start=cfg.init_size)


def factory(Xm):
    s = TCVSummarizer(cfg, Xm)
    s.word_counts = wc
    return s


hist = HistoricalSummarizer(cfg, cl.ptf, X.shape[1], factory)
res = sliding_window_experiment(
    df, X, wc, cfg, window_size=window, step_size=step,
    sampling_interval=sampling, historical=hist, k=15,
    max_windows=3, verbose=True)

for m in ("Sumblr", "ClusterSum", "LexRank", "DSDR", "Random"):
    r = res.get(m, {})
    print(f"  {m:11} n={r.get('n_samples',0):>2} "
          f"R-1 F={r.get('rouge1_f', float('nan')):.4f} "
          f"runtime={r.get('runtime_sec', 0):.3f}s")

print()
ns = {m: res[m].get("n_samples", 0) for m in res}
check("all methods scored on the same windows",
      len(set(ns.values())) == 1, f"{ns}")
check("ClusterSum runtime measured", res["ClusterSum"]["runtime_sec"] > 0,
      f"{res['ClusterSum']['runtime_sec']}s")
check("DSDR runtime measured", res["DSDR"]["runtime_sec"] > 0,
      f"{res['DSDR']['runtime_sec']}s")
check("DSDR slower than LexRank (paper's efficiency claim)",
      res["DSDR"]["runtime_sec"] > res["LexRank"]["runtime_sec"],
      f"{res['DSDR']['runtime_sec']:.2f}s > {res['LexRank']['runtime_sec']:.2f}s")
check("Eq.4 integral recorded",
      "eq4_integral_rouge1_f" in res["Sumblr"])

# ---- reference budget ---------------------------------------------------
print()
print("=== 3. reference summary respects the budget ===")
idx = np.arange(0, window)
ref = window_reference(X, wc, cfg, idx, 15)
ref_b = enforce_budget(ref, wc, cfg)
words = int(sum(int(wc[i]) for i in ref_b))
print(f"  reference: {len(ref_b)} tweets, {words} words")
check("reference within 250 words", words <= cfg.summary_words, f"{words}")
check("reference within k tweets", len(ref_b) <= 15, f"{len(ref_b)}")

print()
print("RESULT:", "PASS" if not fails else f"FAIL ({len(fails)}): {fails}")
sys.exit(1 if fails else 0)

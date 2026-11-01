"""Sweep tau for topic-evolvement detection after the smoothing fix."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SumblrConfig
from preprocess import load_tweets, build_vectors, count_words
from sumblr import SumblrClusterer
from summarize import detect_timeline
from run import build_timeline_summaries

cfg = SumblrConfig(verbose=False)
df = load_tweets(cfg)
X, X_norm, _ = build_vectors(df, cfg)
ts = df["ts"].to_numpy()
wc = np.array([max(1, count_words(t)) for t in df["text"]])

cl = SumblrClusterer(cfg, dim=X.shape[1])
cl.initialize(X, X_norm, ts)
cl.process(X, X_norm, ts, start=cfg.init_size)

info, bins = build_timeline_summaries(df, X, X_norm, wc, cfg, cl,
                                      window_min=cfg.timeline_window_min)
print(f"bins={len(bins)}  {info['granularity']}")
print()

for tau in (1.000, 1.005, 1.010, 1.012, 1.02, 1.05, 1.1, 1.2):
    c = SumblrConfig(verbose=False, tau=tau)
    nodes, series = detect_timeline(bins, c)
    ds = [s["distance"] for s in series]
    rs = [s["ratio"] for s in series]
    print(f"tau={tau:>5}: nodes={len(nodes):>3}  "
          f"D in [{min(ds):.4f},{max(ds):.4f}]  "
          f"ratio in [{min(rs):.2f},{max(rs):.2f}]")
    for nd in nodes[:4]:
        print(f"          node @ bin {nd['index']} "
              f"({bins[nd['index']]['hour']})  D={nd['distance']:.4f} "
              f"ratio={nd['ratio']:.2f}")

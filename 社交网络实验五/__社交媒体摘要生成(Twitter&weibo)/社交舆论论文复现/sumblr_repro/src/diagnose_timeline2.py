"""Diagnose why topic-evolvement distances saturate at D = 1.

D = 1 - e^{-D_KL} is a squash: D ~ 1 whenever D_KL > ~5. The paper's tau=1.012
test only works when consecutive summaries are similar enough that D_avg is
well below 1. This script measures the raw D_KL and the vocabulary overlap
between successive window summaries.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SumblrConfig
from preprocess import load_tweets, build_vectors, tokenize, count_words
from sumblr import SumblrClusterer
from summarize import kl_divergence, normalized_distance
from run import build_timeline_summaries

cfg = SumblrConfig(verbose=False)
df = load_tweets(cfg)
X, X_norm, _ = build_vectors(df, cfg)
ts = df["ts"].to_numpy()
wc = np.array([max(1, count_words(t)) for t in df["text"]])

cl = SumblrClusterer(cfg, dim=X.shape[1])
cl.initialize(X, X_norm, ts)
cl.process(X, X_norm, ts, start=cfg.init_size)

for window in (180, 360, 720):
    info, bins = build_timeline_summaries(df, X, X_norm, wc, cfg, cl,
                                          window_min=window)
    print(f"=== window={window}min  bins={len(bins)} ===")
    kls, jac, sizes = [], [], []
    for i in range(1, len(bins)):
        a = set(bins[i]["word_counts"])
        b = set(bins[i - 1]["word_counts"])
        jac.append(len(a & b) / max(1, len(a | b)))
        kls.append(kl_divergence(bins[i]["word_counts"],
                                 bins[i - 1]["word_counts"], cfg.kl_epsilon))
        sizes.append((len(a), len(b)))
    if not kls:
        print("  (no comparable bins)")
        continue
    kls = np.array(kls)
    print(f"  vocab sizes: {sizes[:5]} ...")
    print(f"  Jaccard overlap: mean={np.mean(jac):.3f} "
          f"min={np.min(jac):.3f} max={np.max(jac):.3f}")
    print(f"  D_KL: mean={kls.mean():.2f} min={kls.min():.2f} "
          f"max={kls.max():.2f}")
    ds = 1 - np.exp(-kls)
    print(f"  D=1-e^-KL: mean={ds.mean():.4f} min={ds.min():.4f} "
          f"max={ds.max():.4f}")
    print(f"  max/min D = {ds.max()/max(ds.min(),1e-9):.4f} "
          f"(need > tau={cfg.tau})")
    print()

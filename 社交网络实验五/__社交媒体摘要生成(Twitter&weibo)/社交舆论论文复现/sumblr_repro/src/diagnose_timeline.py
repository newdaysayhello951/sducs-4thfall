"""Diagnose topic-evolvement detection (Section 4.3)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SumblrConfig
from preprocess import load_tweets, tokenize
from summarize import kl_divergence, normalized_distance

cfg = SumblrConfig(verbose=False)
df = load_tweets(cfg)

bins = []
for h, grp in df.groupby(df["dt"].dt.floor("h")):
    if len(grp) < 20:
        continue
    cnt = {}
    for t in grp["text"]:
        for w in tokenize(t, cfg):
            cnt[w] = cnt.get(w, 0) + 1
    bins.append({"hour": str(h), "n": len(grp), "word_counts": cnt})

print(f"{len(bins)} hourly bins")
print()
print(f"{'hour':<18}{'n':>6}{'D_KL':>10}{'D=1-e^-KL':>12}{'ratio':>9}")
print("-" * 56)
dists = []
for i in range(1, len(bins)):
    d_kl = kl_divergence(bins[i]["word_counts"], bins[i - 1]["word_counts"],
                         cfg.kl_epsilon)
    d = normalized_distance(d_kl)
    dists.append(d)
    print(f"{bins[i]['hour']:<18}{bins[i]['n']:>6}{d_kl:>10.4f}{d:>12.4f}")

d = np.array(dists)
print()
print(f"distances: min={d.min():.4f} max={d.max():.4f} mean={d.mean():.4f} "
      f"std={d.std():.4f}")
print(f"max/mean = {d.max()/d.mean():.4f}   (paper's tau = {cfg.tau})")

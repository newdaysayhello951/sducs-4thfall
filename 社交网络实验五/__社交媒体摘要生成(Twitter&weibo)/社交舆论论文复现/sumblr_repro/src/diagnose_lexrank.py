"""Diagnose the LexRank baseline's degeneracy."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SumblrConfig
from preprocess import load_tweets, build_vectors
from summarize import lexrank

cfg = SumblrConfig(verbose=False)
df = load_tweets(cfg)
X, X_norm, _ = build_vectors(df, cfg)
n = X.shape[0]
print(f"stream: {n} tweets")

rng = np.random.default_rng(cfg.seed)
idx = np.sort(rng.choice(n, size=min(1200, n), replace=False))
M = np.asarray(X_norm[idx].todense())
sim = np.clip(M @ M.T, 0.0, 1.0)
np.fill_diagonal(sim, 0.0)

print(f"pairwise cosine: mean={sim.mean():.4f} max={sim.max():.4f} "
      f"p99={np.percentile(sim, 99):.4f}")
for thr in (0.0, 0.05, 0.1, 0.15, 0.2):
    s = sim.copy()
    s[s < thr] = 0.0
    deg = s.sum(axis=1)
    isolated = int((deg <= 0).sum())
    lr = lexrank(s, iters=cfg.lexrank_iters, damping=cfg.lexrank_damping)
    top = np.argsort(-lr)[:25]
    # diversity of the resulting picks
    T = M[top]
    Ts = np.clip(T @ T.T, 0, 1)
    iu = np.triu_indices(len(top), k=1)
    print(f"thr={thr:>4}: isolated={isolated:>5}  lr range="
          f"[{lr.min():.2e},{lr.max():.2e}]  top25 mean_dist="
          f"{(1 - Ts[iu]).mean():.3f}")

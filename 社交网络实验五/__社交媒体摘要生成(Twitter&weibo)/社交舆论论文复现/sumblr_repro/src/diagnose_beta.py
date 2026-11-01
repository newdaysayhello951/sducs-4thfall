"""Diagnostic: does the paper's MBS rule degenerate on this corpus?

For L2-normalized tweets with w_i = 1, the paper's
    Sim(co, t_i) = (wsum_v . sum_v) / (n * ||wsum_v||)
collapses to ||centroid||, because sum_v == wsum_v. So
    MBS = beta * ||centroid||,
which shrinks as a cluster grows and diffuses -- a positive feedback loop.
This script measures cluster-size distribution across beta values.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SumblrConfig
from preprocess import load_tweets, build_vectors
from sumblr import SumblrClusterer

cfg = SumblrConfig(verbose=False)
df = load_tweets(cfg)
X, X_norm, _ = build_vectors(df, cfg)
ts = df["ts"].to_numpy()
print(f"corpus: {X.shape[0]} tweets x {X.shape[1]} terms")
print()

# Confirm the two sums now differ (raw vs normalized).
from sumblr import TCV
t = TCV(dim=X.shape[1], m=40)
for i in range(min(50, X.shape[0])):
    t.add(i, X[i].toarray().ravel(), X_norm[i].toarray().ravel(), float(i),
          1.0, 0.5)
print(f"after fix: avg_similarity()={t.avg_similarity():.6f}  "
      f"||centroid||={np.linalg.norm(t.centroid):.6f}  (should now DIFFER)")
print()

print(f"{'beta':>7}{'alive':>8}{'created':>9}{'merged':>8}{'deleted':>9}"
      f"{'largest':>9}{'top1_share':>12}{'median':>8}{'singletons':>12}")
print("-" * 81)

# The paper swept beta over 0.04-0.11 and recommends 0.07 (Section 5.3).
# Values much above ~0.15 make MBS exceed the typical nearest-centroid cosine
# on this short-text corpus, so almost every tweet spawns a cluster and the
# Nmax merge loop churns; we scan the paper's range and note the breakdown.
for beta in (0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.15, 0.25):
    c = SumblrConfig(verbose=False, beta=beta)
    cl = SumblrClusterer(c, dim=X.shape[1])
    cl.initialize(X, X_norm, ts)
    cl.process(X, X_norm, ts, start=c.init_size)
    s = cl.stats()
    print(f"{beta:>7.2f}{s['clusters_alive']:>8}{s['clusters_created']:>9}"
          f"{s['clusters_merged']:>8}{s['clusters_deleted']:>9}"
          f"{s['largest_cluster']:>9}{s['largest_cluster_share']:>12.3f}"
          f"{s['median_cluster']:>8.1f}{s['singleton_clusters']:>12}")

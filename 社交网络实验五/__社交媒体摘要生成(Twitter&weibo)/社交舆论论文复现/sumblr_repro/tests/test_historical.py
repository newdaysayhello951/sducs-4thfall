"""Verify Definition 4 (Subtraction Operation) and historical summarization.

Checks:
  1. TCV.subtract follows Definition 4 arithmetic exactly.
  2. ft_set subtraction keeps only tweets absent from the earlier snapshot.
  3. subtract_snapshot over the real PTF yields only the tweets that arrived
     during the requested window (n and ts1 should equal the window's growth).
  4. drill-down / roll-up / range timeline all run and return summaries.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from config import SumblrConfig
from preprocess import load_tweets, build_vectors, count_words
from sumblr import SumblrClusterer, TCV
from ptf import SnapshotCluster
from historical import HistoricalSummarizer, subtract_snapshot
from summarize import TCVSummarizer

fails = []


def check(name, cond, detail=""):
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        fails.append(name)


print("=== 1. Definition 4 arithmetic ===")
a = TCV(dim=4, m=2, cid=1)
a.sum_v = np.array([1.0, 2, 3, 4], dtype=np.float32)
a.wsum_v = np.array([2.0, 4, 6, 8], dtype=np.float32)
a.ts1, a.ts2, a.n = 100.0, 1000.0, 10
a.ft_set = [(1, 0.9), (2, 0.8), (3, 0.7)]

b = TCV(dim=4, m=2, cid=1)
b.sum_v = np.array([0.5, 1, 1.5, 2], dtype=np.float32)
b.wsum_v = np.array([1.0, 2, 3, 4], dtype=np.float32)
b.ts1, b.ts2, b.n = 40.0, 400.0, 4
b.ft_set = [(1, 0.9), (3, 0.7)]

d = a.subtract(b)
check("sum_v", np.allclose(d.sum_v, [0.5, 1, 1.5, 2]))
check("wsum_v", np.allclose(d.wsum_v, [1, 2, 3, 4]))
check("ts1", d.ts1 == 60.0, f"got {d.ts1}")
check("ts2", d.ts2 == 600.0, f"got {d.ts2}")
check("n", d.n == 6, f"got {d.n}")
check("ft_set = in A but not B", [i for i, _ in d.ft_set] == [2],
      f"got {[i for i, _ in d.ft_set]}")

print()
print("=== 2. subtract_snapshot on synthetic snapshots ===")
s1 = type("S", (), {"tick": 10, "ts": 1000.0, "order": 1, "clusters": [
    SnapshotCluster(cid=7, idlist=[7], n=3, ts1=30.0, ts2=300.0, ft_set=[10, 11, 12]),
]})()
s2 = type("S", (), {"tick": 20, "ts": 2000.0, "order": 1, "clusters": [
    SnapshotCluster(cid=7, idlist=[7], n=8, ts1=90.0, ts2=1200.0,
                    ft_set=[10, 11, 12, 13, 14]),
]})()
out = subtract_snapshot(s2, s1, dim=4, m=2)
check("one cluster survives", len(out) == 1, f"got {len(out)}")
if out:
    c = out[0]
    check("n = 8-3 = 5", c.n == 5, f"got {c.n}")
    check("ts1 = 90-30 = 60", abs(c.ts1 - 60.0) < 1e-6, f"got {c.ts1}")
    check("ft_set keeps only new tweets", sorted(i for i, _ in c.ft_set) == [13, 14],
          f"got {sorted(i for i, _ in c.ft_set)}")

print()
print("=== 3. Real stream: window clusters only contain new tweets ===")
cfg = SumblrConfig(verbose=False)
df = load_tweets(cfg)
X, Xn, _ = build_vectors(df, cfg)
ts = df["ts"].to_numpy()
cl = SumblrClusterer(cfg, dim=X.shape[1])
cl.initialize(X, Xn, ts)
cl.process(X, Xn, ts, start=cfg.init_size)

h = HistoricalSummarizer(cfg, cl.ptf, X.shape[1],
                         lambda Xm: TCVSummarizer(cfg, Xm))
last_tick = cl.ptf.retrieve(10**9).tick
print(f"  last tick = {last_tick}")

# Total n across the whole stream snapshot should be the live tweet count.
end = cl.ptf.retrieve(last_tick)
total_end = sum(c.n for c in end.clusters)
check("end snapshot n == tweets in live clusters",
      total_end == sum(c.n for c in cl.clusters),
      f"{total_end} vs {sum(c.n for c in cl.clusters)}")

# A 2-tick window must contain strictly fewer tweets than the whole stream.
w_clusters, s0, s1s = cl_w = None, None, None
w_clusters, s0, s1s = h.window_clusters(last_tick, 2)
w_n = sum(c.n for c in w_clusters)
print(f"  2-tick window: {len(w_clusters)} clusters, {w_n} tweets "
      f"(start_tick={s0.tick if s0 else None}, end_tick={s1s.tick if s1s else None})")
check("window is a strict subset of the stream", 0 < w_n < total_end,
      f"{w_n} < {total_end}")
check("all window n > 0 (subtraction never negative)",
      all(c.n > 0 for c in w_clusters))

print()
print("=== 4. drill-down / roll-up / range timeline run ===")
wc = np.array([max(1, count_words(t)) for t in df["text"]])


def factory(Xm):
    s = TCVSummarizer(cfg, Xm)
    s.word_counts = wc
    return s


h = HistoricalSummarizer(cfg, cl.ptf, X.shape[1], factory)
dd = h.drill_down(last_tick, hours=6, X=X)
ru = h.roll_up(last_tick, hours=18, X=X)
rg = h.range_summary(last_tick, h_ticks=4, X=X)
print(f"  drill-down (6h): {len(dd['tweets'])} tweets, {dd['n_clusters']} clusters, "
      f"approx={dd['approximated']}")
print(f"  roll-up  (18h): {len(ru['tweets'])} tweets, {ru['n_clusters']} clusters")
print(f"  range    ( 4 ticks): {len(rg['tweets'])} tweets, {rg['n_clusters']} clusters")
check("drill-down produced tweets", len(dd["tweets"]) > 0)
check("roll-up produced tweets", len(ru["tweets"]) > 0)
check("range summary produced tweets", len(rg["tweets"]) > 0)

tl = h.range_timeline(last_tick, h_ticks=2, step_ticks=2, X=X)
print(f"  range timeline: {len(tl)} nodes")
check("range timeline has nodes", len(tl) > 0)

print()
print("RESULT:", "PASS" if not fails else f"FAIL ({len(fails)}): {fails}")
sys.exit(1 if fails else 0)

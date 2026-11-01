"""Module 2: Sumblr online tweet-stream clustering.

Implements Shou et al., SIGIR 2013:
  * Tweet Cluster Vector (TCV)      -- Definition 1, Section 3.2
  * Incremental clustering          -- Algorithm 1, Section 4.1.2
  * Outdated-cluster deletion       -- Section 4.1.3
  * Cluster merging                 -- Section 4.1.4, Definition 3
  * Pyramidal Time Frame snapshots  -- Definition 2, Section 3.3

IMPORTANT implementation detail
-------------------------------
The paper's TCV keeps two *different* sums of the same tweet vectors:
    sum_v  = SUM_i tv_i / ||tv_i||      (normalized vectors)
    wsum_v = SUM_i w_i * tv_i           (raw vectors)
Because the Minimum Bounding Similarity is
    MBS = beta * (wsum_v . sum_v) / (n * ||wsum_v||)
these must not be conflated: if a single L2-normalized matrix is fed to both,
then sum_v == wsum_v (with w_i = 1) and the MBS degenerates to beta*||centroid||,
which collapses every stream into one giant cluster. We therefore accept two
matrices, X_raw and X_norm, and keep the two sums separate.
"""
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np
from scipy import sparse
from scipy.special import erfinv
from sklearn.cluster import KMeans

from config import SumblrConfig
from ptf import PyramidalTimeFrame, SnapshotCluster


def _dense(v) -> np.ndarray:
    """Densify a single tweet row (sparse or dense) to 1-D float32."""
    if sparse.issparse(v):
        return np.asarray(v.toarray()).ravel().astype(np.float32)
    return np.asarray(v).ravel().astype(np.float32)


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    d = float(np.linalg.norm(a)) * float(np.linalg.norm(b))
    return float(np.dot(a, b) / d) if d > 1e-12 else 0.0


# ---------------------------------------------------------------------------
# Tweet Cluster Vector (Definition 1)
# ---------------------------------------------------------------------------
@dataclass
class TCV:
    """Compressed in-memory statistics of one cluster.

    sum_v   : sum of normalized textual vectors      (paper: sum_v)
    wsum_v  : sum of weighted raw textual vectors    (paper: wsum_v)
    ts1     : sum of timestamps                      (paper: ts1)
    ts2     : sum of squared timestamps              (paper: ts2)
    n       : number of tweets                       (paper: n)
    ft_set  : focus tweet set, closest m to centroid (paper: ft_set)
    """
    dim: int
    m: int
    sum_v: np.ndarray = None
    wsum_v: np.ndarray = None
    ts1: float = 0.0
    ts2: float = 0.0
    n: int = 0
    ft_set: List[Tuple[int, float]] = field(default_factory=list)
    # Section 4.1.4: "each composite cluster is given an IDList which consists
    # of IDs of the clusters merged in it." A single cluster's IDList is {cid}.
    cid: int = -1
    idlist: List[int] = field(default_factory=list)

    def __post_init__(self):
        if self.sum_v is None:
            self.sum_v = np.zeros(self.dim, dtype=np.float32)
        if self.wsum_v is None:
            self.wsum_v = np.zeros(self.dim, dtype=np.float32)
        if not self.idlist and self.cid >= 0:
            self.idlist = [self.cid]

    # -- derived quantities -------------------------------------------------
    @property
    def centroid(self) -> np.ndarray:
        """cv = wsum_v / n   (Equation 1)."""
        if self.n == 0:
            return np.zeros(self.dim, dtype=np.float32)
        return (self.wsum_v / self.n).astype(np.float32)

    def avg_similarity(self) -> float:
        """Sim(co, t_i), the average cosine similarity between centroid and
        members, computed from TCV contents (paper Section 4.1.2):
            Sim(co, t_i) = (wsum_v . sum_v) / (n * ||wsum_v||)
        """
        denom = self.n * float(np.linalg.norm(self.wsum_v))
        if denom <= 1e-12:
            return 0.0
        return float(np.dot(self.wsum_v, self.sum_v) / denom)

    @property
    def mean_time(self) -> float:
        return self.ts1 / self.n if self.n else 0.0

    @property
    def std_time(self) -> float:
        if self.n == 0:
            return 0.0
        var = self.ts2 / self.n - (self.ts1 / self.n) ** 2
        return float(np.sqrt(max(var, 0.0)))

    # -- updates ------------------------------------------------------------
    def add(self, idx: int, raw: np.ndarray, norm: np.ndarray, ts: float,
            w: float, sim: float) -> None:
        """Incrementally absorb a tweet."""
        self.sum_v += norm
        self.wsum_v += w * raw
        self.ts1 += ts
        self.ts2 += ts * ts
        self.n += 1
        self._update_focus(idx, sim)

    def _update_focus(self, idx: int, sim: float) -> None:
        """Keep the m closest tweets to the centroid.

        Paper heuristic: compare the new tweet against the existing ft_set and
        keep the closest m, giving fresh tweets a chance to enter.
        """
        self.ft_set.append((idx, sim))
        if len(self.ft_set) > self.m:
            self.ft_set.sort(key=lambda p: -p[1])
            self.ft_set = self.ft_set[: self.m]

    def merge(self, other: "TCV") -> None:
        """Aggregation Operation (Definition 3).

        Also unions the two IDLists, per Section 4.1.4: composite clusters keep
        the IDs of every cluster merged into them, which is what makes the
        Subtraction Operation (Definition 4) possible for historical summaries.
        """
        self.sum_v = self.sum_v + other.sum_v
        self.wsum_v = self.wsum_v + other.wsum_v
        self.ts1 += other.ts1
        self.ts2 += other.ts2
        self.n += other.n
        union = dict(other.ft_set)
        union.update(dict(self.ft_set))
        self.ft_set = list(union.items())
        for cid in other.idlist:
            if cid not in self.idlist:
                self.idlist.append(cid)

    def subtract(self, other: "TCV") -> "TCV":
        """Subtraction Operation (Definition 4).

        Given cluster C1 in S(ts1) and its corresponding cluster C2 in S(ts2),
        TCV(C1 - C2) is:
            sum_v  = sum_v1  - sum_v2
            wsum_v = wsum_v1 - wsum_v2
            ts1    = ts1_1   - ts1_2
            ts2    = ts2_1   - ts2_2
            n      = n1      - n2
            ft_set = tweets in ft_set1 but not in ft_set2

        This eliminates the influence of clusters created before ts2, so the
        result describes only the tweets added during the requested duration.
        """
        out = TCV(dim=self.dim, m=self.m, cid=self.cid,
                  idlist=list(self.idlist))
        out.sum_v = self.sum_v - other.sum_v
        out.wsum_v = self.wsum_v - other.wsum_v
        out.ts1 = self.ts1 - other.ts1
        out.ts2 = self.ts2 - other.ts2
        out.n = self.n - other.n
        other_ids = {i for i, _ in other.ft_set}
        out.ft_set = [(i, s) for i, s in self.ft_set if i not in other_ids]
        return out


# ---------------------------------------------------------------------------
# Canopy-style initialization (paper Section 4.1.1)
# ---------------------------------------------------------------------------
def canopy_init(X, t2: float = 0.15, seed: int = 42, cap: int = 15) -> List[int]:
    """Cheap Canopy pre-clustering to pick k and the initial centroids.

    The paper says k and the initial centroids are "decided via the Canopy
    method" but gives no thresholds; t2/cap are our documented choice.
    """
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    order = rng.permutation(n)
    centers: List[int] = []
    assigned = np.zeros(n, dtype=bool)
    for i in order:
        if assigned[i]:
            continue
        centers.append(int(i))
        row = X[i]
        sims = np.asarray((X @ row.T).todense()).ravel()
        assigned |= sims >= t2
        if len(centers) >= cap:
            break
    return centers


# ---------------------------------------------------------------------------
# Clustering driver
# ---------------------------------------------------------------------------
class SumblrClusterer:
    """Maintains the live cluster set S and the Pyramidal Time Frame."""

    def __init__(self, cfg: SumblrConfig, dim: int):
        self.cfg = cfg
        self.dim = dim
        self.clusters: List[TCV] = []
        self.centroids = np.zeros((0, dim), dtype=np.float32)
        self.unit_centroids = np.zeros((0, dim), dtype=np.float32)
        # Pyramidal Time Frame (Definition 2). Snapshots are filed by order and
        # evicted per-order, unlike a flat FIFO.
        self.ptf = PyramidalTimeFrame(cfg)
        self._tick = 0            # timestamp unit = snapshot_minutes
        self._last_tick_stored = -1
        self.n_created = 0
        self.n_merged = 0
        self.n_deleted = 0
        self._next_snapshot_ts = -1.0
        self.sim_mode = "paper"
        # tweet index -> index of the cluster it was assigned to. Needed to
        # reconstruct "the current clusters" for a given time window, since the
        # paper's summaries are retrieved from the live cluster set (Sec. 4.2).
        self.assignment: dict = {}
        self._cid_counter = 0

    def _next_cid(self) -> int:
        self._cid_counter += 1
        return self._cid_counter

    # -- centroid matrix bookkeeping ---------------------------------------
    def _refresh_centroids(self) -> None:
        if not self.clusters:
            self.centroids = np.zeros((0, self.dim), dtype=np.float32)
            self.unit_centroids = np.zeros((0, self.dim), dtype=np.float32)
            return
        self.centroids = np.vstack([c.centroid for c in self.clusters])
        nrm = np.linalg.norm(self.centroids, axis=1, keepdims=True)
        nrm[nrm < 1e-12] = 1e-12
        self.unit_centroids = (self.centroids / nrm).astype(np.float32)

    def _update_one_centroid(self, i: int) -> None:
        self.centroids[i] = self.clusters[i].centroid
        n = float(np.linalg.norm(self.centroids[i]))
        self.unit_centroids[i] = (self.centroids[i] / n if n > 1e-12
                                  else self.centroids[i])

    # -- initialization -----------------------------------------------------
    def initialize(self, X_raw, X_norm, ts: np.ndarray) -> None:
        cfg = self.cfg
        k0 = min(cfg.init_size, X_raw.shape[0])
        sub_raw, sub_norm = X_raw[:k0], X_norm[:k0]
        cap = max(2, min(cfg.canopy_cap, k0))
        centers = canopy_init(sub_norm, seed=cfg.seed, cap=cap)
        k = max(2, min(len(centers), cfg.init_k, k0))

        init_centers = _dense(sub_raw[centers[0]])[None, :]
        for ci in centers[1:k]:
            init_centers = np.vstack([init_centers, _dense(sub_raw[ci])[None, :]])
        km = KMeans(n_clusters=k, init=init_centers, n_init=1,
                    random_state=cfg.seed)
        labels = km.fit_predict(sub_norm)

        for c in range(k):
            members = np.where(labels == c)[0]
            if len(members) == 0:
                continue
            tcv = TCV(dim=self.dim, m=cfg.m, cid=self._next_cid())
            cv = km.cluster_centers_[c].astype(np.float32)
            ncv = float(np.linalg.norm(cv))
            ucv = cv / ncv if ncv > 1e-12 else cv
            for i in members:
                tcv.add(int(i), _dense(sub_raw[i]), _dense(sub_norm[i]),
                        float(ts[i]), 1.0, _cos(_dense(sub_norm[i]), ucv))
            self.clusters.append(tcv)

        self.n_created = len(self.clusters)
        self._refresh_centroids()
        if cfg.verbose:
            print(f"[sumblr] initialized {len(self.clusters)} clusters from "
                  f"first {k0} tweets (Canopy -> k={k}, KMeans)")

    # -- main loop ----------------------------------------------------------
    def process(self, X_raw, X_norm, ts: np.ndarray, start: int = 0) -> None:
        cfg = self.cfg
        n = X_raw.shape[0]
        for i in range(start, n):
            self._assign(int(i), X_raw[i], X_norm[i], float(ts[i]))
            if cfg.check_interval and (i + 1) % cfg.check_interval == 0:
                self.delete_outdated(float(ts[i]))
            self._maybe_snapshot(float(ts[i]))
        # Store the final state so that queries about "now" (online summaries,
        # and the end point of any historical window) can always be answered.
        # Without this the PTF's newest snapshot lags the stream by up to one
        # snapshot interval, and tweets in that tail are unreachable.
        if n > start:
            self.snapshot_now(float(ts[n - 1]))

    def _assign(self, idx: int, raw, norm, t: float) -> None:
        cfg = self.cfg
        if not self.clusters:
            c = TCV(dim=self.dim, m=cfg.m, cid=self._next_cid())
            c.add(idx, _dense(raw), _dense(norm), t, 1.0, 1.0)
            self.clusters.append(c)
            self._refresh_centroids()
            self.n_created += 1
            return

        rv = _dense(raw)
        nv = _dense(norm)
        # Step 1: choose the cluster whose centroid is closest to t.
        # Cosine similarity, i.e. dot product against unit-normalized centroids
        # (the tweet side is already L2-normalized).
        sims = np.asarray(self.unit_centroids @ nv).ravel()
        p = int(np.argmax(sims))
        max_sim = float(sims[p])
        cp = self.clusters[p]

        # Step 2: Heuristic 1 -- MaxSim(co,t) < MBS -> create a new cluster.
        # MBS = beta * Sim(co, t_i), the paper's average intra-cluster cosine.
        if self.sim_mode == "paper":
            mbs = cfg.beta * cp.avg_similarity()
        else:                       # documented absolute-threshold fallback
            mbs = cfg.beta
        if max_sim < mbs:
            c = TCV(dim=self.dim, m=cfg.m, cid=self._next_cid())
            c.add(idx, rv, nv, t, 1.0, 1.0)
            self.clusters.append(c)
            self.centroids = np.vstack([self.centroids, c.centroid[None, :]])
            n = float(np.linalg.norm(c.centroid))
            u = (c.centroid / n if n > 1e-12 else c.centroid).astype(np.float32)
            self.unit_centroids = np.vstack([self.unit_centroids, u[None, :]])
            self.n_created += 1
            if len(self.clusters) > cfg.n_max:
                self.merge_clusters()
        else:
            cp.add(idx, rv, nv, t, 1.0, max_sim)
            self.assignment[idx] = p
            self._update_one_centroid(p)

    # -- outdated cluster deletion (Section 4.1.3) --------------------------
    def delete_outdated(self, now_ts: float) -> None:
        cfg = self.cfg
        p_prime = 1.0 - cfg.p_percent / 200.0        # (100 - p/2)%
        z = float(np.sqrt(2.0) * erfinv(2.0 * p_prime - 1.0))
        keep = []
        for c in self.clusters:
            if c.n < 2:
                keep.append(c)
                continue
            x = c.mean_time + c.std_time * z         # start of last p% tweets
            if (now_ts - x) / 86400.0 > cfg.freshness_days:
                self.n_deleted += 1
            else:
                keep.append(c)
        if len(keep) != len(self.clusters):
            self.clusters = keep
            self._refresh_centroids()

    # -- merging (Section 4.1.4) -------------------------------------------
    def merge_clusters(self) -> None:
        """Greedy pairwise merging until only mc fraction of clusters remain.

        The paper sorts cluster pairs by centroid similarity and merges the
        most similar pair repeatedly, letting composite clusters keep growing
        (its worked example chains {c1,c2} -> {c1,c2,c4}).

        Implementation: keep a similarity matrix in sync as clusters merge,
        instead of recomputing all pairs each round (which is O(N^3 d)) and
        instead of freezing the matrix (which chains unrelated clusters,
        because a merged centroid would be judged by its parts' similarities).
        After merging b into a we recompute only row/column a.
        """
        cfg = self.cfg
        target = max(1, int(len(self.clusters) * cfg.mc))

        self._refresh_centroids()
        C = self.unit_centroids
        sim = np.clip(C @ C.T, -1.0, 1.0)
        np.fill_diagonal(sim, -np.inf)

        alive = list(range(len(self.clusters)))
        while len(alive) > target:
            # Most similar currently-alive pair.
            sub = sim[np.ix_(alive, alive)]
            k = int(np.argmax(sub))
            ia, ib = np.unravel_index(k, sub.shape)
            a, b = alive[ia], alive[ib]
            if not np.isfinite(sub[ia, ib]):
                break

            self.clusters[a].merge(self.clusters[b])
            self.n_merged += 1
            # Update only centroid a (and its unit vector) in place.
            self.centroids[a] = self.clusters[a].centroid
            na = float(np.linalg.norm(self.centroids[a]))
            self.unit_centroids[a] = (self.centroids[a] / na if na > 1e-12
                                      else self.centroids[a])
            ca = self.unit_centroids[a]
            for j in alive:
                if j == a or j == b:
                    continue
                s = float(np.clip(np.dot(ca, self.unit_centroids[j]), -1, 1))
                sim[a, j] = sim[j, a] = s
            sim[a, b] = sim[b, a] = -np.inf
            sim[a, a] = -np.inf
            alive.remove(b)

        self.clusters = [self.clusters[i] for i in alive]
        self._refresh_centroids()

    # -- Pyramidal Time Frame (Section 3.3) --------------------------------
    def _maybe_snapshot(self, t: float) -> None:
        """Store a snapshot when the current timestamp crosses a tick boundary.

        The paper's timestamp unit is the snapshot interval ("The interval
        between two successive snapshots (timestamp unit) is one hour",
        Section 5.4), and a snapshot of order i is taken when the tick is
        divisible by alpha^i (Definition 2).
        """
        cfg = self.cfg
        unit = cfg.snapshot_minutes * 60
        tick = int(t // unit)
        if tick <= self._last_tick_stored:
            return
        self._last_tick_stored = tick
        self._tick = tick
        self.ptf.maybe_store(tick, t, self._snapshot_clusters())

    def _snapshot_clusters(self) -> List[SnapshotCluster]:
        return [
            SnapshotCluster(cid=c.cid, idlist=list(c.idlist), n=c.n,
                            ts1=c.ts1, ts2=c.ts2,
                            ft_set=[i for i, _ in c.ft_set])
            for c in self.clusters
        ]

    def snapshot_now(self, t: float) -> None:
        """Force a snapshot (used to seed the PTF at stream start)."""
        unit = self.cfg.snapshot_minutes * 60
        tick = int(t // unit)
        self.ptf.maybe_store(tick, t, self._snapshot_clusters())
        self._last_tick_stored = tick
        self._tick = tick

    # -- reporting ----------------------------------------------------------
    def stats(self) -> dict:
        sizes = sorted((c.n for c in self.clusters), reverse=True)
        total = int(sum(sizes)) or 1
        return {
            "clusters_alive": len(self.clusters),
            "clusters_created": self.n_created,
            "clusters_merged": self.n_merged,
            "clusters_deleted": self.n_deleted,
            "snapshots_live": self.ptf.stats()["n_live"],
            "snapshots_stored": self.ptf.n_stored,
            "snapshots_dropped": self.ptf.n_dropped,
            "ptf_orders": self.ptf.stats()["orders_used"],
            "tweets_clustered": int(sum(sizes)),
            "largest_cluster": int(sizes[0]) if sizes else 0,
            "largest_cluster_share": round(sizes[0] / total, 3) if sizes else 0.0,
            "median_cluster": float(np.median(sizes)) if sizes else 0.0,
            "singleton_clusters": int(sum(1 for s in sizes if s == 1)),
        }

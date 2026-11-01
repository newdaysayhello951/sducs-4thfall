"""Historical summarization -- Section 4.2.

The paper's second contribution is summarization over an arbitrary
user-defined time duration, supported by the Pyramidal Time Frame.

Procedure (Section 4.2):
  1. Given duration length H ending at tse, "we can retrieve two snapshots
     whose timestamps are either equal to or right before tse and tse - H".
     Denote their timestamps ts1 and ts2 and cluster sets S(ts1), S(ts2).
     "Now the original duration [tse-H, tse] is approximated by [ts2, ts1]."
  2. For each cluster C in S(ts1), take its ID (single) or the IDs in its
     IDList (composite). For each such ID, find the corresponding cluster in
     S(ts2) and subtract its TCV from C's TCV (Definition 4).
  3. "The final set of clusters after this process is the input for historical
     summarization" -- i.e. feed it to TCV-Rank (Algorithm 2).

This yields the paper's three use cases (Section 1):
  * range timeline  -- a summary over [tse-H, tse]
  * drill-down      -- a short, recent duration
  * roll-up         -- a long duration
"""
from typing import Dict, List, Optional, Tuple

import numpy as np

from config import SumblrConfig
from ptf import PyramidalTimeFrame, Snapshot, SnapshotCluster
from sumblr import TCV, _dense


def subtract_snapshot(snap_end: Snapshot, snap_start: Snapshot,
                      dim: int, m: int) -> List[TCV]:
    """Apply Definition 4 across two snapshots.

    For each cluster C in S(ts1) we build a TCV holding only the tweets that
    arrived during (ts2, ts1]:

        TCV(C - C2) with C2 = the corresponding cluster in S(ts2)

    Correspondence is established through the IDList: "For each of these IDs,
    we find the corresponding cluster in S(ts2)". A cluster in S(ts1) may be a
    composite of several clusters that were separate (or absent) at ts2, so we
    subtract each matching ID's TCV in turn.
    """
    # Index the earlier snapshot's clusters by their own cluster ID.
    start_by_id: Dict[int, SnapshotCluster] = {c.cid: c for c in snap_start.clusters}

    out: List[TCV] = []
    for c in snap_end.clusters:
        tcv = TCV(dim=dim, m=m, cid=c.cid, idlist=list(c.idlist))
        tcv.n = c.n
        tcv.ts1 = c.ts1
        tcv.ts2 = c.ts2
        tcv.ft_set = [(i, 0.0) for i in c.ft_set]

        # Subtract every constituent that already existed at ts2.
        for cid in c.idlist:
            old = start_by_id.get(cid)
            if old is None:
                continue          # cluster did not exist yet -> nothing to remove
            tcv.n -= old.n
            tcv.ts1 -= old.ts1
            tcv.ts2 -= old.ts2
            old_ft = set(old.ft_set)
            tcv.ft_set = [(i, s) for i, s in tcv.ft_set if i not in old_ft]

        # Only keep clusters that actually gained tweets in this window.
        if tcv.n > 0 and tcv.ft_set:
            out.append(tcv)
    return out


class HistoricalSummarizer:
    """Range / drill-down / roll-up summaries over the PTF.

    Note on snapshot contents: the paper stores whole TCVs in the PTF, but also
    says "we only store the identifiers and sums of values of the words
    occurring in the cluster" (sparse) and that snapshots live on disk. Our
    snapshots keep (cid, idlist, n, ts1, ts2, ft_set) -- exactly the fields
    TCV-Rank needs (ft_set for candidates, n for the n_ti/n_max coverage term).
    Storing full dense sum_v/wsum_v per snapshot would cost ~10 MB x 77
    snapshots for no benefit, since Equation (2) never reads them.
    """

    def __init__(self, cfg: SumblrConfig, ptf: PyramidalTimeFrame, dim: int,
                 summarizer_factory):
        """summarizer_factory: callable(X) -> TCVSummarizer-like object.

        It must expose `.word_counts` and `.summarize(clusters)`.
        """
        self.cfg = cfg
        self.ptf = ptf
        self.dim = dim
        self.summarizer_factory = summarizer_factory

    # -- window -> cluster set ---------------------------------------------
    def window_clusters(self, tse_tick: int, h_ticks: int
                        ) -> Tuple[List[TCV], Optional[Snapshot], Optional[Snapshot]]:
        start, end = self.ptf.retrieve_range(tse_tick, h_ticks)
        if end is None:
            return [], start, end
        if start is None or start.tick == end.tick:
            # Nothing earlier available: the whole duration is the end snapshot.
            clusters = []
            for c in end.clusters:
                tcv = TCV(dim=self.dim, m=self.cfg.m, cid=c.cid,
                          idlist=list(c.idlist))
                tcv.n, tcv.ts1, tcv.ts2 = c.n, c.ts1, c.ts2
                tcv.ft_set = [(i, 0.0) for i in c.ft_set]
                if tcv.ft_set:
                    clusters.append(tcv)
            return clusters, start, end
        return subtract_snapshot(end, start, self.dim, self.cfg.m), start, end

    # -- summarization ------------------------------------------------------
    def summarize_window(self, tse_tick: int, h_ticks: int, X) -> dict:
        clusters, start, end = self.window_clusters(tse_tick, h_ticks)
        if not clusters:
            return {"tweets": [], "n_clusters": 0, "start_tick": None,
                    "end_tick": None, "approximated": False}

        s = self.summarizer_factory(X)
        res = s.summarize(clusters)
        res["n_clusters"] = len(clusters)
        res["start_tick"] = start.tick if start else None
        res["end_tick"] = end.tick if end else None
        # The paper notes the requested duration is only approximated by the
        # two retrieved snapshots.
        res["approximated"] = bool(
            start is None or end is None or
            (end.tick - start.tick) != h_ticks
        )
        return res

    def range_summary(self, tse_tick: int, h_ticks: int, X) -> dict:
        """Range timeline node: one summary over [tse-H, tse]."""
        return self.summarize_window(tse_tick, h_ticks, X)

    def drill_down(self, tse_tick: int, hours: int, X) -> dict:
        """Drill-down: a detailed summary for a small recent duration."""
        h_ticks = max(1, int(round(hours * 60 / self.cfg.snapshot_minutes)))
        return self.summarize_window(tse_tick, h_ticks, X)

    def roll_up(self, tse_tick: int, hours: int, X) -> dict:
        """Roll-up: a concise summary over a long duration."""
        h_ticks = max(1, int(round(hours * 60 / self.cfg.snapshot_minutes)))
        return self.summarize_window(tse_tick, h_ticks, X)

    def range_timeline(self, tse_tick: int, h_ticks: int, step_ticks: int,
                       X) -> List[dict]:
        """A sequence of range summaries stepping back through the stream."""
        out = []
        t = tse_tick
        while t - h_ticks >= 0:
            r = self.summarize_window(t, h_ticks, X)
            r["end_tick_abs"] = t
            out.append(r)
            t -= step_ticks
        out.reverse()
        return out

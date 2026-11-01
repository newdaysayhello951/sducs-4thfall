"""Pyramidal Time Frame (PTF) -- Definition 2, Section 3.3.

The PTF stores cluster snapshots at *differing levels of granularity depending
on recency*. The paper's rules (Section 3.3):

  * Snapshots are classified into orders 0 .. log(T), where T is the time
    elapsed since the beginning of the stream.
  * A snapshot of the i-th order is taken at a moment when the timestamp from
    the beginning of the stream is exactly divisible by alpha^i.
  * At any moment, only the last alpha^l + 1 (l >= 1) snapshots of each order
    are stored.
  * "Redundancy is removed by storing each snapshot only in its highest
    possible order."

So a snapshot at tick t belongs to exactly one order:
    order(t) = max{ i : t % alpha^i == 0 }   (0 when t % alpha != 0)

Worked example from the paper (alpha=3, l=2 -> 3^2+1 = 10 per order, T=86):
    order 4: {81}
    order 3: {54, 27}
    order 2: {72, 63, 45, 36, 18, 9}
    order 1: {84, 78, 75, 69, 66, 60, 57, 51, 48, 42}
    order 0: {86, 85, 83, 82, 80, 79, 77, 76, 74, 73}
`tests/test_ptf.py` verifies this table exactly.

The timestamp unit is one hour, per Section 5.4: "The interval between two
successive snapshots (timestamp unit) is one hour."
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from config import SumblrConfig


def order_of(tick: int, alpha: int) -> int:
    """Highest order i such that tick is divisible by alpha^i."""
    if tick <= 0:
        return 0
    i, p = 0, alpha
    while tick % p == 0:
        i += 1
        p *= alpha
    return i


@dataclass
class SnapshotCluster:
    """One cluster's state inside a snapshot.

    cid    : the cluster's own identifier
    idlist : IDs of every cluster merged into it (a composite cluster). For a
             single cluster this is just {cid}.
    """
    cid: int
    idlist: List[int]
    n: int
    ts1: float
    ts2: float
    ft_set: List[int] = field(default_factory=list)

    def copy(self) -> "SnapshotCluster":
        return SnapshotCluster(self.cid, list(self.idlist), self.n,
                               self.ts1, self.ts2, list(self.ft_set))


@dataclass
class Snapshot:
    tick: int          # timestamp in units of the snapshot interval
    ts: float          # raw stream timestamp (seconds)
    order: int
    clusters: List[SnapshotCluster]


class PyramidalTimeFrame:
    """Order-layered snapshot store with pyramidal eviction."""

    def __init__(self, cfg: SumblrConfig):
        self.cfg = cfg
        self.alpha = cfg.alpha
        self.l = cfg.ptf_l
        self.capacity = self.alpha ** self.l + 1     # alpha^l + 1 per order
        # order -> list of snapshots (chronological)
        self.orders: Dict[int, List[Snapshot]] = {}
        self.n_stored = 0
        self.n_dropped = 0

    # -- storage ------------------------------------------------------------
    def maybe_store(self, tick: int, ts: float,
                    clusters: List[SnapshotCluster]) -> Optional[Snapshot]:
        """Store a snapshot if this tick is a snapshot moment for its order.

        A tick qualifies when it is divisible by alpha^i for some i >= 1; the
        snapshot is filed under its highest such order (redundancy removal).
        Order 0 is reserved for ticks not divisible by alpha, which the paper's
        example populates (order 0 holds 86, 85, 83, ... -- i.e. every tick
        that is not a multiple of alpha). We therefore also store order-0
        snapshots, which keeps every tick represented exactly once.
        """
        o = order_of(tick, self.alpha)
        snap = Snapshot(tick=tick, ts=ts, order=o,
                        clusters=[c.copy() for c in clusters])
        bucket = self.orders.setdefault(o, [])
        # Definition 2 gives one snapshot per moment ("each snapshot of the
        # i-th order is taken at a moment in time when the timestamp ... is
        # exactly divisible by alpha^i"). Re-storing the same tick therefore
        # replaces the earlier state rather than duplicating it -- which is what
        # happens when the stream's final state is flushed at the same tick as
        # the last periodic snapshot.
        for idx in range(len(bucket) - 1, -1, -1):
            if bucket[idx].tick == tick:
                bucket[idx] = snap
                return snap
        bucket.append(snap)
        self.n_stored += 1
        # Keep only the last alpha^l + 1 snapshots of this order.
        while len(bucket) > self.capacity:
            bucket.pop(0)
            self.n_dropped += 1
        return snap

    # -- retrieval ----------------------------------------------------------
    def retrieve(self, target_tick: int) -> Optional[Snapshot]:
        """Snapshot whose timestamp is equal to, or right before, target_tick.

        This implements the paper's "we can retrieve two snapshots whose
        timestamps are either equal to or right before tse and tse - H".
        """
        best: Optional[Snapshot] = None
        for bucket in self.orders.values():
            for s in bucket:
                if s.tick <= target_tick:
                    if best is None or s.tick > best.tick:
                        best = s
        return best

    def retrieve_range(self, tse_tick: int, h_ticks: int):
        """Return (snap_start, snap_end) approximating [tse-H, tse].

        The paper: "the original duration [tse-H, tse] is approximated by
        [ts2, ts1]" where ts1/ts2 come from the two retrieved snapshots.
        """
        end = self.retrieve(tse_tick)
        start = self.retrieve(max(0, tse_tick - h_ticks))
        return start, end

    # -- reporting ----------------------------------------------------------
    def stats(self) -> dict:
        return {
            "n_stored": self.n_stored,
            "n_dropped": self.n_dropped,
            "n_live": sum(len(b) for b in self.orders.values()),
            "capacity_per_order": self.capacity,
            "orders_used": len(self.orders),
            "per_order": {o: len(b) for o, b in sorted(self.orders.items())},
        }

    def max_bound(self, T: int) -> int:
        """The paper's bound: (alpha^l + 1) * log(T)."""
        return self.capacity * max(1, int(np.log(max(T, 2))))

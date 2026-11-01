"""Verify the PTF against the paper's Table 1 (alpha=3, l=2, T=86).

Paper Table 1:
    order 4: 81
    order 3: 54 27
    order 2: 72 63 45 36 18 9
    order 1: 84 78 75 69 66 60 57 51 48 42
    order 0: 86 85 83 82 80 79 77 76 74 73

Note the paper stores order 0 only for the most recent alpha^l+1 ticks, so
earlier non-multiples of alpha (e.g. 1..41) have been evicted by T=86.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from config import SumblrConfig
from ptf import PyramidalTimeFrame, order_of

cfg = SumblrConfig(verbose=False, alpha=3, ptf_l=2)

print("=== order_of(t, alpha=3) spot checks ===")
for t in (9, 18, 27, 54, 81, 72, 63, 45, 36, 84, 78, 86, 85):
    print(f"  t={t:>3} -> order {order_of(t, 3)}")
print()

ptf = PyramidalTimeFrame(cfg)
print(f"capacity per order = alpha^l + 1 = {ptf.capacity}")
print()

# Feed ticks 1..86, storing at every tick.
for t in range(1, 87):
    ptf.maybe_store(t, float(t), clusters=[])

print("=== retrieved PTF contents at T=86 ===")
expected = {
    4: [81],
    3: [54, 27],
    2: [72, 63, 45, 36, 18, 9],
    1: [84, 78, 75, 69, 66, 60, 57, 51, 48, 42],
    0: [86, 85, 83, 82, 80, 79, 77, 76, 74, 73],
}
ok_all = True
for o in sorted(ptf.orders, reverse=True):
    got = sorted((s.tick for s in ptf.orders[o]), reverse=True)
    exp = expected.get(o, [])
    match = got == exp
    ok_all &= match
    print(f"  order {o}: {got}")
    if o in expected:
        print(f"          expected {exp}  -> {'MATCH' if match else 'MISMATCH'}")
    else:
        print("          (order not listed in the paper's table)")
print()

# Check no tick is stored twice (redundancy removal).
allticks = [s.tick for b in ptf.orders.values() for s in b]
print(f"duplicate ticks stored: {len(allticks) - len(set(allticks))} (must be 0)")
print(f"total live snapshots: {len(allticks)}")
print(f"paper's bound (alpha^l+1)*log2(T) = {ptf.max_bound(86)}")
print()
print("RESULT:", "PASS" if ok_all else "FAIL")

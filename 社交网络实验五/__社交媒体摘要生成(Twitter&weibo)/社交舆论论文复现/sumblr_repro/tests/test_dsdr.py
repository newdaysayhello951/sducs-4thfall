"""Verify the DSDR baseline behaves as a reconstruction-error minimiser.

DSDR (He et al., AAAI 2012) selects a subset that best reconstructs the whole
document set. Properties we can test without re-running the original code:

  1. Greedy reconstruction error is monotonically non-increasing as we add rows.
  2. The selected set reconstructs D better than a random subset of equal size.
  3. Selection is deterministic for a fixed seed/data.
  4. It returns exactly min(k, n) picks and no duplicates.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from config import SumblrConfig
from preprocess import load_tweets, build_vectors
from baselines import dsdr, _unit_rows, _dense

fails = []


def check(name, cond, detail=""):
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def recon_error(D: np.ndarray, rows: np.ndarray) -> float:
    """||D - S (S^T S)^+ S^T D||_F^2 with S = D[rows] (orthonormalised)."""
    S = D[rows]
    # Orthonormal basis for span(S) via QR.
    Q, _ = np.linalg.qr(S.T)          # (d, r)
    Q = Q[:, :np.linalg.matrix_rank(S)]
    P = Q @ Q.T
    R = D - D @ P
    return float(np.sum(R * R))


cfg = SumblrConfig(verbose=False, day="2023-02-10")
df = load_tweets(cfg)
X, Xn, _ = build_vectors(df, cfg)
idx = np.arange(0, 400)
D = _unit_rows(np.vstack([_dense(X[i]) for i in idx]))

print("=== 1. reconstruction error decreases as rows are added ===")
picks = dsdr(X, 20, cfg, idx)
errs = [recon_error(D, np.array(picks[:j])) for j in range(1, len(picks) + 1)]
monotone = all(errs[i] <= errs[i - 1] + 1e-9 for i in range(1, len(errs)))
check("monotone non-increasing", monotone)
print(f"       err(1)={errs[0]:.4f}  err(5)={errs[4]:.4f}  err(20)={errs[-1]:.4f}")

print()
print("=== 2. DSDR beats a random subset of the same size ===")
full = recon_error(D, np.arange(D.shape[0]))
rng = np.random.default_rng(0)
rand_errs = []
for _ in range(10):
    r = rng.choice(D.shape[0], size=len(picks), replace=False)
    rand_errs.append(recon_error(D, r))
mean_rand = float(np.mean(rand_errs))
dsdr_err = recon_error(D, np.array(picks))
check("DSDR error < mean random error", dsdr_err < mean_rand,
      f"{dsdr_err:.4f} < {mean_rand:.4f}")
print(f"       full-set error={full:.4f}  DSDR={dsdr_err:.4f}  "
      f"random={mean_rand:.4f}")

print()
print("=== 3/4. determinism, count, uniqueness ===")
a = dsdr(X, 20, cfg, idx)
b = dsdr(X, 20, cfg, idx)
check("deterministic", a == b)
check("returns k picks", len(a) == 20, f"got {len(a)}")
check("no duplicates", len(set(a)) == len(a))
check("picks are valid global indices", all(i in set(idx.tolist()) for i in a))

print()
print("RESULT:", "PASS" if not fails else f"FAIL ({len(fails)}): {fails}")
sys.exit(1 if fails else 0)

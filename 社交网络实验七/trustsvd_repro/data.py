from dataclasses import dataclass
from pathlib import Path
import hashlib
import numpy as np
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[1]
PAPER_COUNTS = {
    'filmtrust': (1508, 2071, 35497, 1853),
    'epinions': (40163, 139738, 664824, 487183),
    'ciao': (7375, 99746, 280391, 111781),
    'flixster': (53213, 18197, 409803, 655054),
}


@dataclass
class Dataset:
    name: str
    u: np.ndarray
    i: np.ndarray
    r: np.ndarray
    tu: np.ndarray
    tv: np.ndarray
    t: np.ndarray
    n_users: int
    n_items: int
    minimum: float
    maximum: float
    metadata: dict


def load_dataset(name, root=ROOT, allow_mismatch=False):
    folder = root / 'datasets' / {'epinions': 'epinions_665k'}.get(name, name)
    rf = folder / ('ratings_data.txt' if name == 'epinions' else 'ratings.txt')
    tf = folder / ('trust_data.txt' if name == 'epinions' else 'trust.txt')
    if not rf.exists() or not tf.exists():
        raise FileNotFoundError(f'{name}: missing {rf} or {tf}; no substitute data are generated.')
    ratings = np.loadtxt(rf, ndmin=2)
    trust = np.loadtxt(tf, ndmin=2)
    if ratings.shape[1] != 3 or trust.shape[1] not in (2, 3):
        raise ValueError('Expected ratings: user item value; trust: source target [value]')
    if not np.isfinite(ratings).all() or not np.isfinite(trust).all():
        raise ValueError('Non-finite input')
    users = np.unique(np.concatenate([ratings[:, 0], trust[:, 0], trust[:, 1]]))
    items = np.unique(ratings[:, 1])
    u = np.searchsorted(users, ratings[:, 0]).astype(np.int64)
    i = np.searchsorted(items, ratings[:, 1]).astype(np.int64)
    tu = np.searchsorted(users, trust[:, 0]).astype(np.int64)
    tv = np.searchsorted(users, trust[:, 1]).astype(np.int64)
    pairs = u.astype(np.int64) * len(items) + i
    duplicates = len(pairs) - len(np.unique(pairs))
    t = trust[:, 2] if trust.shape[1] == 3 else np.ones(len(trust))
    if not np.all(t > 0):
        raise ValueError('This reproduction expects observed positive trust edges only.')
    counts = (len(np.unique(u)), len(items), len(ratings), len(trust))
    meta = dict(counts=list(counts), expected=list(PAPER_COUNTS[name]), duplicate_pairs=duplicates,
                matches_paper=counts == PAPER_COUNTS[name],
                user_union=len(users),
                ratings_sha256=hashlib.sha256(rf.read_bytes()).hexdigest(),
                trust_sha256=hashlib.sha256(tf.read_bytes()).hexdigest())
    if not meta['matches_paper'] and not allow_mismatch:
        raise ValueError(f'{name}: counts {counts} differ from paper {PAPER_COUNTS[name]}')
    minimum, maximum = {'filmtrust': (.5, 4.), 'flixster': (.5, 5.)}.get(name, (1., 5.))
    if np.any((ratings[:,2]<minimum)|(ratings[:,2]>maximum)):
        raise ValueError(f'{name}: ratings outside [{minimum}, {maximum}]')
    if np.any(t>1):
        raise ValueError(f'{name}: trust values above 1')
    return Dataset(name, u, i, ratings[:, 2], tu, tv, t, len(users), len(items), minimum, maximum, meta)


def folds_for(data, seed=20261026, n_folds=5):
    """Rating-level folds, deterministic; all models share exactly the same folds."""
    p = ROOT / 'results' / 'splits' / f'{data.name}_seed{seed}_k{n_folds}.npz'
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        with np.load(p) as z:
            if str(z['ratings_sha256']) != data.metadata['ratings_sha256']:
                raise ValueError('Stored folds belong to a different ratings file')
            return z['fold']
    # FilmTrust contains 3 extra observations for repeated pairs, two with
    # conflicting values. Keep raw observations but put each pair in ONE fold.
    # This retains the paper's 35,497 rows without same-pair train/test leakage.
    _, group = np.unique(data.u.astype(np.int64)*data.n_items + data.i, return_inverse=True)
    order = np.random.default_rng(seed).permutation(group.max()+1)
    group_fold = np.empty(len(order), dtype=np.int8)
    group_fold[order] = np.arange(len(order)) % n_folds
    fold = group_fold[group]
    np.savez_compressed(p, fold=fold, ratings_sha256=data.metadata['ratings_sha256'])
    return fold


def adjacency(u, i, shape):
    mat = csr_matrix((np.ones(len(u)), (u, i)), shape=shape)
    mat.sum_duplicates()
    mat.data[:] = 1.
    mat.sort_indices()
    return mat


def invsqrt(n):
    """An empty neighborhood contributes zero, never infinity."""
    out = np.zeros(len(n), dtype=np.float64)
    np.divide(1., np.sqrt(n), out=out, where=np.asarray(n) > 0)
    return out

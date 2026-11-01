"""Verify saved experimental outputs without retraining or trusting CSV tables."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import scipy
import numba
from .data import ROOT, load_dataset, folds_for
from .experiment import metrics, hyperparameters
from .objectives import Objective


def audit(run='gradient_descent'):
    base = ROOT/'results'/run
    manifest = json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    checks, errors, observed = [], [], set()
    for name in manifest['available']:
        data = load_dataset(name, allow_mismatch=name in manifest['arguments'].get('allow_mismatch', []))
        folds = folds_for(data, manifest['arguments']['seed'])
        pairs = data.u.astype(np.int64)*data.n_items+data.i
        for f in range(5):
            if np.intersect1d(pairs[folds==f], pairs[folds!=f]).size:
                errors.append(f'{name}: pair leakage in fold {f}')
        for path in sorted((base/name).glob('*.json')):
            r = json.loads(path.read_text(encoding='utf-8'))
            if r.get('status') != 'completed':
                continue
            try:
                assert r['hyperparameters']==hyperparameters(name,r['model'])
                assert r['data']['ratings_sha256']==data.metadata['ratings_sha256']
                assert r['data']['trust_sha256']==data.metadata['trust_sha256']
                if r['optimizer']=='gd':
                    for stage in r['training']:
                        losses=np.array([v['objective'] for v in stage['trace']])
                        assert np.isfinite(losses).all()
                        assert np.all(np.diff(losses)<=1e-11)
                with np.load(path.with_suffix('.npz')) as z:
                    expected = np.flatnonzero(folds==r['fold'])
                    np.testing.assert_array_equal(z['indices'], expected)
                    np.testing.assert_array_equal(z['truth'], data.r[expected])
                    assert np.isfinite(z['prediction']).all()
                    assert np.all((z['prediction']>=data.minimum)&(z['prediction']<=data.maximum))
                    np.testing.assert_array_equal(z['user'],data.u[expected])
                    m = metrics(z['truth'], z['prediction'])
                    for k in ('mae','rmse'):
                        np.testing.assert_allclose(m[k], r['all'][k], atol=1e-12)
                    train = np.flatnonzero(folds!=r['fold'])
                    for name_count, source in [('train',data.u[train]),('total',data.u)]:
                        counts = np.bincount(source, minlength=data.n_users)
                        cold = metrics(z['truth'], z['prediction'], counts[data.u[expected]]<5)
                        old = r[f'cold_{name_count}_lt5']
                        assert cold['n']==old['n']
                        for k in ('mae','rmse'):
                            if cold[k] is not None:
                                np.testing.assert_allclose(cold[k], old[k], atol=1e-12)
                    split = np.load(path.with_suffix('.split.npz'))
                    np.testing.assert_array_equal(np.sort(np.r_[split['validation'],split['inner_train']]),train)
                    assert not np.intersect1d(pairs[split['validation']], pairs[split['inner_train']]).size
                    assert not np.intersect1d(expected, split['validation']).size
                    assert not np.intersect1d(expected, split['inner_train']).size
                    if r['model']=='TrustSVD':
                        model = np.load(path.with_suffix('.model.npz'))
                        obj = Objective(data, train, 'TrustSVD', r['dim'], **r['hyperparameters'])
                        assert float(model['mean'])==obj.mean
                        x = obj.pack({n:model[n] for n,_ in obj.fields})
                        pred = np.clip(obj.predict(x,data.u[expected],data.i[expected]),data.minimum,data.maximum)
                        np.testing.assert_allclose(pred,z['prediction'],atol=1e-12)
                checks.append(str(path.relative_to(ROOT)))
                observed.add((name,r['model'],r['dim'],r['fold']))
            except Exception as e:
                errors.append(f'{path}: {type(e).__name__}: {e}')
    cfg=manifest['arguments']
    expected={(ds,m,d,f) for ds in manifest['available'] for m in cfg['models'] for d in cfg['dims'] for f in cfg['folds']}
    result = dict(checked_fits=len(checks), errors=errors, missing_tasks=sorted(expected-observed),
                  unexpected_tasks=sorted(observed-expected),complete_for_available=observed==expected,
                  complete_for_entire_paper=len(checks)==400 and not manifest['missing'] and all(m['matches_paper'] for m in manifest['available'].values()),
                  versions=dict(numpy=np.__version__, scipy=scipy.__version__, numba=numba.__version__),
                  source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (ROOT/'trustsvd_repro').glob('*.py')})
    (base/'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if errors:
        raise SystemExit(1)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',default='gradient_descent')
    audit(parser.parse_args().run)

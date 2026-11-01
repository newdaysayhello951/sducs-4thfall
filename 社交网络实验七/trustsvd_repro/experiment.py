"""Leakage-controlled CV runner; no published implementation is imported."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
import os
from pathlib import Path
import platform
import time
import traceback
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from .data import ROOT, load_dataset, folds_for
from .objectives import Objective, MODELS
from .optimizers import gradient_descent

PARAMETERS = {
    'filmtrust': dict(svd=.1, reg=1.2, trust=.9, sorec=.1, soreg=.1, alpha=1.),
    'epinions': dict(svd=.35, reg=.9, trust=.5, sorec=1., soreg=.1, alpha=.4),
    'flixster': dict(svd=.03, reg=.8, trust=.5, sorec=.001, soreg=1., alpha=1.),
    'ciao': dict(svd=.1, reg=.5, trust=1., sorec=.01, soreg=.1, alpha=1.),
}


def hyperparameters(dataset, model):
    cfg = PARAMETERS[dataset]
    return dict(reg=cfg['reg'] if model == 'TrustSVD' else cfg['svd'] if model == 'SVD++' else .001,
                social=cfg['trust'] if model == 'TrustSVD' else cfg['sorec'] if model == 'SoRec'
                else cfg['soreg'] if model == 'SoReg' else 1., alpha=cfg['alpha'])


def metrics(truth, pred, mask=None):
    if mask is not None:
        truth, pred = truth[mask], pred[mask]
    if len(truth) == 0:
        return dict(n=0, mae=None, rmse=None)
    err = pred - truth
    return dict(n=len(truth), mae=float(np.mean(np.abs(err))), rmse=float(np.sqrt(np.mean(err**2))))


class StopValidation(Exception):
    pass


def optimize(obj, seed, iterations, validation=None, patience=5, optimizer='lbfgs'):
    """Both solvers use the exact full objective and analytic gradient.

    Selection inspects ONLY an inner validation subset, every 5 iterations.
    Returned iteration count is refit on all four outer training folds.
    """
    x0 = obj.initial(seed)
    history, best, wait, counter = [], [np.inf, 0], [0], [0]
    started = time.perf_counter()

    def callback(x):
        counter[0] += 1
        if counter[0] % 5 and counter[0] != iterations:
            return
        value, grad = obj.value_grad(x)
        entry = dict(iteration=counter[0], objective=value, gradient_norm=float(np.linalg.norm(grad)))
        if validation is not None:
            vu, vi, vr = validation
            pred = np.clip(obj.predict(x, vu, vi), obj.data.minimum, obj.data.maximum)
            score = metrics(vr, pred)['rmse']
            entry['validation_rmse'] = score
            if score < best[0] - 1e-5:
                best[:] = [score, counter[0]]
                wait[0] = 0
            else:
                wait[0] += 1
        history.append(entry)
        if validation is not None and wait[0] >= patience:
            raise StopValidation()

    last_x = [x0]
    def cb(x):
        last_x[0] = x.copy()
        callback(x)
    try:
        if optimizer == 'gd':
            fitted = gradient_descent(obj.value_grad, x0, iterations, callback=cb)
        else:
            fitted = minimize(obj.value_grad, x0, jac=True, method='L-BFGS-B', callback=cb,
                              options=dict(maxiter=iterations, maxcor=7, ftol=1e-10,
                                           gtol=1e-7, maxls=30))
        x, message = fitted.x, str(fitted.message)
        nit = int(fitted.nit)
    except StopValidation:
        x, message, nit = last_x[0], 'inner validation patience reached', counter[0]
    loss, grad = obj.value_grad(x)
    if not np.isfinite(loss) or not np.isfinite(x).all():
        raise FloatingPointError('Non-finite fitted parameters')
    return x, dict(iterations=nit, selected_iterations=best[1] or max(1, nit),
                   best_validation_rmse=None if validation is None else float(best[0]),
                   objective=loss, gradient_norm=float(np.linalg.norm(grad)),
                   message=message, seconds=time.perf_counter()-started, trace=history)


def average_predict(data, train, test, model):
    u, i, r = data.u[train], data.i[train], data.r[train]
    idx = u if model == 'UserAvg' else i
    count = np.bincount(idx, minlength=data.n_users if model == 'UserAvg' else data.n_items)
    sums = np.bincount(idx, weights=r, minlength=len(count))
    averages = np.divide(sums, count, out=np.full(len(count), r.mean()), where=count > 0)
    return averages[(data.u if model == 'UserAvg' else data.i)[test]]


def run_one(task):
    dataset, model, dim, fold, args = task
    started = time.perf_counter()
    out = ROOT / 'results' / args['run'] / dataset / f'{model.replace("+", "p")}_d{dim}_fold{fold}'
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.with_suffix('.json').exists() and not args['force']:
        previous = json.loads(out.with_suffix('.json').read_text(encoding='utf-8'))
        if previous.get('status') == 'completed' and out.with_suffix('.npz').exists():
            return dict(cached=True, **previous)
    data = load_dataset(dataset, allow_mismatch=dataset in args.get('allow_mismatch', []))
    folds = folds_for(data, args['seed'])
    test, train = np.flatnonzero(folds == fold), np.flatnonzero(folds != fold)
    # Internal validation never touches outer test labels. Save its indices too.
    seed = args['seed'] + fold*1000 + dim
    keys = data.u[train].astype(np.int64)*data.n_items + data.i[train]
    unique, group = np.unique(keys, return_inverse=True)
    order = np.random.default_rng(seed).permutation(len(unique))
    ng = max(1, int(len(unique)*args['validation'])) if args['validation'] else 0
    valid_mask = np.isin(group, order[:ng])
    valid, inner = train[valid_mask], train[~valid_mask]
    nv = len(valid)
    np.savez_compressed(out.with_suffix('.split.npz'), validation=valid, inner_train=inner)
    cfg = hyperparameters(dataset, model)
    info = dict(dataset=dataset, model=model, dim=dim, fold=fold, seed=seed,
                hyperparameters=cfg, n_train=len(train), n_test=len(test),
                status='completed', data=data.metadata, optimizer=args.get('optimizer','lbfgs'),
                validation_fraction=args['validation'], maxiter=args['maxiter'])
    raw, training = None, []
    final_models = []
    if model in ('UserAvg', 'ItemAvg'):
        raw = average_predict(data, train, test, model)
    else:
        roles = ['truster', 'trustee'] if model == 'TrustMF' else ['truster']
        for role in roles:
            selected = args['maxiter']
            if nv:
                obj_inner = Objective(data, inner, model, dim, **cfg, role=role)
                _, selection = optimize(obj_inner, seed, args['maxiter'],
                                        (data.u[valid], data.i[valid], data.r[valid]), args['patience'],args.get('optimizer','lbfgs'))
                selected = selection['selected_iterations']
                selection['stage'], selection['role'] = 'selection', role
                training.append(selection)
                del obj_inner
            obj = Objective(data, train, model, dim, **cfg, role=role)
            x, fit = optimize(obj, seed, selected, optimizer=args.get('optimizer','lbfgs'))
            fit['stage'], fit['role'] = 'refit', role
            training.append(fit)
            final_models.append((obj, x))
        if model == 'TrustMF':
            za = final_models[0][0].unpack(final_models[0][1])
            zb = final_models[1][0].unpack(final_models[1][1])
            # Yang et al. 2013 Eq. (7), including cross terms; NOT mean of scores.
            hp = .5*(za['p'][data.u[test]] + zb['p'][data.u[test]])
            hq = .5*(za['q'][data.i[test]] + zb['q'][data.i[test]])
            raw = data.maximum*expit(np.einsum('ij,ij->i', hp, hq))
        else:
            obj, x = final_models[0]
            raw = obj.predict(x, data.u[test], data.i[test])
        if model == 'TrustSVD':
            obj, x = final_models[0]
            np.savez_compressed(out.with_suffix('.model.npz'), **obj.unpack(x), mean=obj.mean,
                                train_indices=train, test_indices=test)
    pred = np.clip(raw, data.minimum, data.maximum)
    training_counts = np.bincount(data.u[train], minlength=data.n_users)
    total_counts = np.bincount(data.u, minlength=data.n_users)
    degree = np.bincount(data.tu, minlength=data.n_users)
    # Paper says "users who rate less than five items" without clarifying
    # full-data vs training counts. Primary definition uses observable train counts;
    # the full-data interpretation is ALSO reported, never silently substituted.
    info['all'] = metrics(data.r[test], pred)
    info['cold_train_lt5'] = metrics(data.r[test], pred, training_counts[data.u[test]] < 5)
    info['cold_total_lt5'] = metrics(data.r[test], pred, total_counts[data.u[test]] < 5)
    info['all_unclipped'] = metrics(data.r[test], raw)
    info['training'] = training
    info['seconds'] = time.perf_counter()-started
    np.savez_compressed(out.with_suffix('.npz'), indices=test, prediction=pred, raw_prediction=raw,
                        truth=data.r[test], user=data.u[test], trust_degree=degree[data.u[test]],
                        train_rating_count=training_counts[data.u[test]],
                        total_rating_count=total_counts[data.u[test]])
    temp = out.with_suffix('.json.tmp')
    temp.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(out.with_suffix('.json'))
    return info


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--datasets', nargs='+', default=['filmtrust', 'epinions', 'ciao', 'flixster'])
    p.add_argument('--models', nargs='+', choices=MODELS, default=MODELS)
    p.add_argument('--dims', nargs='+', type=int, default=[5, 10])
    p.add_argument('--folds', nargs='+', type=int, default=list(range(5)))
    p.add_argument('--maxiter', type=int, default=200)
    p.add_argument('--validation', type=float, default=.1)
    p.add_argument('--patience', type=int, default=5)
    p.add_argument('--seed', type=int, default=20261026)
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--optimizer', choices=['lbfgs','gd'], default='gd')
    p.add_argument('--run', default='gradient_descent')
    p.add_argument('--force', action='store_true')
    p.add_argument('--allow-mismatch', nargs='+', default=[], choices=['ciao'],
                   help='Explicitly accept the documented alternate Ciao input; retain mismatch metadata.')
    a = p.parse_args()
    if not 0 <= a.validation < .5 or a.maxiter < 1 or any(f not in range(5) for f in a.folds):
        p.error('Invalid validation, maxiter, or fold values')
    dest = ROOT / 'results' / a.run
    dest.mkdir(parents=True, exist_ok=True)
    prior_manifest = dest/'manifest.json'
    if prior_manifest.exists():
        old = json.loads(prior_manifest.read_text(encoding='utf-8'))['arguments']
        keys = ('maxiter','validation','patience','seed','optimizer','allow_mismatch')
        mismatch = [k for k in keys if old.get(k,'lbfgs' if k=='optimizer' else [] if k=='allow_mismatch' else None)!=vars(a)[k]]
        if mismatch:
            p.error(f'Training settings changed ({mismatch}). Use a new --run directory; do not mix results.')
    manifest = dict(arguments=vars(a), python=platform.python_version(), platform=platform.platform(),
                    numpy=np.__version__, available={}, missing={}, independence='No released model code read/imported/copied.')
    tasks = []
    for name in a.datasets:
        try:
            data = load_dataset(name, allow_mismatch=name in a.allow_mismatch)
            folds_for(data, a.seed)
            manifest['available'][name] = data.metadata
        except (FileNotFoundError, ValueError) as e:
            manifest['missing'][name] = str(e)
            print('UNAVAILABLE:', e, flush=True)
            continue
        for model in a.models:
            for dim in a.dims:
                # Averages do not depend on d, but repeat for a rectangular table.
                for fold in a.folds:
                    tasks.append((name, model, dim, fold, vars(a)))
    (dest/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    done, errors = 0, []
    # Threads avoid Windows named-pipe permissions and share compiled kernels.
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        futures = {pool.submit(run_one, task): task[:4] for task in tasks}
        for future in as_completed(futures):
            done += 1
            task = futures[future]
            try:
                r = future.result()
                print(f'{done}/{len(tasks)} {task}: RMSE={r["all"]["rmse"]:.6f} MAE={r["all"]["mae"]:.6f}'
                      f' {r["seconds"]:.1f}s' + (' CACHED' if r.get('cached') else ''), flush=True)
            except Exception:
                error = dict(task=task, traceback=traceback.format_exc())
                errors.append(error)
                print('FAILED', task, error['traceback'], flush=True)
            (dest/'progress.json').write_text(json.dumps(dict(completed=done, total=len(tasks), errors=errors), indent=2), encoding='utf-8')
    print(f'FINISHED {done} tasks, {len(errors)} failed; unavailable={list(manifest["missing"])}', flush=True)
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

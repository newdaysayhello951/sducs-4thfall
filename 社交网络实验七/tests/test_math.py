import numpy as np
import pytest
from trustsvd_repro.data import Dataset, invsqrt
from trustsvd_repro.objectives import Objective
from trustsvd_repro.experiment import metrics, average_predict


def tiny():
    return Dataset('tiny', np.array([0, 0, 1, 1, 2, 2]), np.array([0, 1, 0, 2, 1, 2]),
                   np.array([4., 3., 2., 5., 1., 4.]), np.array([0, 1, 2, 3]),
                   np.array([1, 2, 0, 0]), np.ones(4), 4, 4, 1., 5., {})


@pytest.mark.parametrize('model', ['PMF', 'RSTE', 'SoRec', 'SoReg', 'SocialMF', 'TrustMF', 'SVD++', 'TrustSVD'])
def test_gradient_central_difference(model):
    obj = Objective(tiny(), np.arange(5), model, 2, reg=.4, social=.7, alpha=.4)
    x = obj.initial(4) + np.random.default_rng(5).normal(0, .1, obj.size)
    loss, analytic = obj.value_grad(x)
    numeric = np.zeros_like(x)
    for k in range(len(x)):
        plus, minus = x.copy(), x.copy()
        plus[k] += 1e-6
        minus[k] -= 1e-6
        numeric[k] = (obj.value_grad(plus)[0] - obj.value_grad(minus)[0]) / 2e-6
    np.testing.assert_allclose(analytic, numeric, rtol=3e-5, atol=2e-8)


def test_trustmf_trustee_gradient():
    obj = Objective(tiny(), np.arange(5), 'TrustMF', 2, .1, 1., role='trustee')
    x = obj.initial(9)
    _, g = obj.value_grad(x)
    direction = np.random.default_rng(7).normal(size=x.size)
    h = 1e-5
    approx = (obj.value_grad(x+h*direction)[0] - obj.value_grad(x-h*direction)[0])/(2*h)
    np.testing.assert_allclose(g@direction, approx, atol=1e-8)


def test_held_out_rating_is_not_in_implicit_history_or_mean():
    obj = Objective(tiny(), np.arange(5), 'TrustSVD', 2, 1.2, .9)
    assert obj.A[2, 2] == 0
    assert obj.mean == np.mean(tiny().r[:5])
    # Perturbing a test label cannot affect training objective or gradients.
    data = tiny()
    data.r[5] = 999.
    other = Objective(data, np.arange(5), 'TrustSVD', 2, 1.2, .9)
    x = obj.initial(0)
    a, b = obj.value_grad(x), other.value_grad(x)
    assert a[0] == b[0]
    np.testing.assert_array_equal(a[1], b[1])


def test_exact_printed_trustsvd_objective():
    data = tiny()
    obj = Objective(data, np.arange(5), 'TrustSVD', 2, 1.2, .9)
    x = obj.initial(1)
    z = obj.unpack(x)
    pred = obj.predict(x, data.u[:5], data.i[:5])
    value = .5*np.sum((pred-data.r[:5])**2)
    tp = np.sum(z['p'][data.tu]*z['w'][data.tv], axis=1)
    value += .5*.9*np.sum((tp-data.t)**2)
    weights = dict(p=1.2*invsqrt(obj.rc)+.9*invsqrt(obj.tc),
                   q=1.2*invsqrt(obj.ic), y=1.2*invsqrt(obj.ic),
                   w=1.2*invsqrt(obj.tin), bu=1.2*invsqrt(obj.rc), bi=1.2*invsqrt(obj.ic))
    for key, a in z.items():
        value += .5*np.sum(weights[key]*(np.sum(a*a, axis=1) if a.ndim == 2 else a*a))
    np.testing.assert_allclose(obj.value_grad(x)[0], value/5, atol=1e-12)


def test_explicit_trust_trains_a_user_without_ratings():
    obj = Objective(tiny(), np.arange(5), 'TrustSVD', 2, 1.2, .9)
    x = obj.initial(1)
    g = obj.unpack(obj.value_grad(x)[1])
    assert np.linalg.norm(g['p'][3]) > 0


def test_metrics_and_empty_views():
    m = metrics(np.array([1., 3.]), np.array([2., 1.]))
    assert m['mae'] == 1.5
    assert m['rmse'] == np.sqrt(2.5)
    assert metrics(np.array([]), np.array([]))['rmse'] is None


def test_average_cold_user_fallback():
    data = tiny()
    data.u[5] = 3
    p = average_predict(data, np.arange(5), np.array([5]), 'UserAvg')
    assert p[0] == data.r[:5].mean()


def test_independent_gradient_descent_decreases_actual_objective():
    from trustsvd_repro.optimizers import gradient_descent
    obj = Objective(tiny(), np.arange(5), 'TrustSVD', 2, 1.2, .9)
    x = obj.initial(2)
    initial = obj.value_grad(x)[0]
    result = gradient_descent(obj.value_grad, x, 30)
    assert result.fun < initial
    np.testing.assert_allclose(result.jac,obj.value_grad(result.x)[1])


def test_duplicate_pairs_stay_in_one_fold(monkeypatch):
    import trustsvd_repro.data as module
    # Some Windows sandbox tokens cannot reopen pytest's mode-0700 tmp dirs.
    # This directory contains only this test's deterministic toy split file.
    test_root=module.ROOT/'tmp'/'test_grouped_folds'
    test_root.mkdir(parents=True,exist_ok=True)
    monkeypatch.setattr(module,'ROOT',test_root)
    data=tiny()
    data.u=np.append(data.u,0)
    data.i=np.append(data.i,0)
    data.r=np.append(data.r,1.)
    data.metadata={'ratings_sha256':'toy'}
    f=module.folds_for(data,seed=42)
    assert f[0]==f[-1]
    assert len(f)==len(data.r)
    np.testing.assert_array_equal(f,module.folds_for(data,seed=42))


def test_forward_matches_direct_neighbor_sums():
    data=tiny()
    obj=Objective(data,np.arange(5),'TrustSVD',2,1.2,.9)
    x=obj.initial(2)
    z=obj.unpack(x)
    expected=[]
    for u,i in zip(data.u,data.i):
        history=np.flatnonzero(obj.A[u].toarray().ravel())
        neighbors=np.flatnonzero(obj.T[u].toarray().ravel())
        h=z['p'][u].copy()
        if len(history):h+=z['y'][history].sum(axis=0)/np.sqrt(len(history))
        if len(neighbors):h+=z['w'][neighbors].sum(axis=0)/np.sqrt(len(neighbors))
        expected.append(obj.mean+z['bu'][u]+z['bi'][i]+z['q'][i]@h)
    np.testing.assert_allclose(obj.predict(x,data.u,data.i),expected,atol=1e-12)


def test_soreg_pcc_averages_duplicate_values_instead_of_summing():
    data=tiny()
    data.u=np.append(data.u,0)
    data.i=np.append(data.i,0)
    data.r=np.append(data.r,1.)
    obj=Objective(data,np.arange(7),'SoReg',2,.001,.1)
    # User 0 now has matrix ratings [2.5,3], mean 2.75.
    # User 1's common item rating lies below its mean: PCC=+1.
    assert obj.sim[0]==1.
    # User 2's common rating lies below its mean, user 0's above: PCC=-1.
    assert obj.sim[2]==0.

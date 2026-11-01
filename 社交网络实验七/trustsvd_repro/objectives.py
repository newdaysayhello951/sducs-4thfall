"""Analytic gradients derived from the papers, not from released model code.

TrustSVD implements printed Eq. (1). The last w_v penalty is summed over v
(the typeset equation omits that summation). Each penalty is applied once
globally, NOT silently repeated per rating. Full-batch sparse aggregation is
algebraically equivalent to the nested implicit-neighbor sums.
"""
import numpy as np
from numba import njit
from scipy.special import expit
from scipy.sparse import csr_matrix, diags
from .data import adjacency, invsqrt


@njit(cache=True, nogil=True)
def rating_loss_grad(u, i, target, h, q, bu, bi, mean, logistic):
    gh = np.zeros_like(h)
    gq = np.zeros_like(q)
    gu = np.zeros_like(bu)
    gi = np.zeros_like(bi)
    loss = 0.
    for k in range(len(u)):
        a, b = u[k], i[k]
        raw = 0.
        for d in range(q.shape[1]):
            raw += h[a, d] * q[b, d]
        if logistic:
            pred = 1. / (1. + np.exp(-min(40., max(-40., raw))))
            err = pred - target[k]
            der = err * pred * (1. - pred)
        else:
            err = raw + mean + bu[a] + bi[b] - target[k]
            der = err
            gu[a] += err
            gi[b] += err
        loss += .5 * err * err
        for d in range(q.shape[1]):
            gh[a, d] += der * q[b, d]
            gq[b, d] += der * h[a, d]
    return loss, gh, gq, gu, gi


@njit(cache=True, nogil=True)
def edge_loss_grad(tu, tv, target, p, w, strength, logistic):
    gp, gw = np.zeros_like(p), np.zeros_like(w)
    loss = 0.
    for k in range(len(tu)):
        a, b = tu[k], tv[k]
        raw = 0.
        for d in range(p.shape[1]):
            raw += p[a, d] * w[b, d]
        pred = 1. / (1. + np.exp(-min(40., max(-40., raw)))) if logistic else raw
        err = pred - target[k]
        der = strength * err * pred * (1. - pred) if logistic else strength * err
        loss += .5 * strength * err * err
        for d in range(p.shape[1]):
            gp[a, d] += der * w[b, d]
            gw[b, d] += der * p[a, d]
    return loss, gp, gw


@njit(cache=True, nogil=True)
def pair_penalty(u, v, weights, p, strength):
    grad = np.zeros_like(p)
    loss = 0.
    for k in range(len(u)):
        a, b = u[k], v[k]
        for d in range(p.shape[1]):
            diff = p[a, d] - p[b, d]
            val = strength * weights[k] * diff
            loss += .5 * diff * val
            grad[a, d] += val
            grad[b, d] -= val
    return loss, grad


@njit(cache=True, nogil=True)
def pcc_weights(tu, tv, indptr, indices, values):
    """PCC on common TRAINING items; missing/undefined PCC gives weight 0.

    Defined PCC is mapped from [-1, 1] to [0, 1], as in Ma et al. 2011.
    """
    result = np.zeros(len(tu))
    for k in range(len(tu)):
        u, v = tu[k], tv[k]
        a, b = indptr[u], indptr[v]
        na, nb = indptr[u+1] - a, indptr[v+1] - b
        if na == 0 or nb == 0:
            continue
        mu = values[indptr[u]:indptr[u+1]].mean()
        mv = values[indptr[v]:indptr[v+1]].mean()
        xy, xx, yy, common = 0., 0., 0., 0
        while a < indptr[u+1] and b < indptr[v+1]:
            if indices[a] == indices[b]:
                x, y = values[a] - mu, values[b] - mv
                xy += x*y
                xx += x*x
                yy += y*y
                common += 1
                a += 1
                b += 1
            elif indices[a] < indices[b]:
                a += 1
            else:
                b += 1
        if common > 0 and xx > 0 and yy > 0:
            result[k] = .5 * (1. + xy / np.sqrt(xx*yy))
    return result


MODELS = ['UserAvg', 'ItemAvg', 'PMF', 'RSTE', 'SoRec', 'SoReg', 'SocialMF', 'TrustMF', 'SVD++', 'TrustSVD']


class Objective:
    def __init__(self, data, train, model, dim, reg, social, alpha=1., role='truster'):
        self.data, self.model, self.dim = data, model, dim
        self.reg, self.social, self.alpha, self.role = reg, social, alpha, role
        self.u, self.i, self.r = data.u[train], data.i[train], data.r[train]
        self.mean = float(self.r.mean())
        nu, ni = data.n_users, data.n_items
        self.A = adjacency(self.u, self.i, (nu, ni))
        self.T = csr_matrix((data.t, (data.tu, data.tv)), shape=(nu, nu))
        self.T.sum_duplicates()
        self.rc = np.asarray(self.A.sum(axis=1)).ravel()
        self.ic = np.asarray(self.A.sum(axis=0)).ravel()
        self.tc = np.asarray((self.T != 0).sum(axis=1)).ravel()
        self.tin = np.asarray((self.T != 0).sum(axis=0)).ravel()
        self.Hr = diags(invsqrt(self.rc)) @ self.A
        self.Ht = diags(invsqrt(self.tc)) @ (self.T != 0).astype(float)
        row_sums = np.asarray(self.T.sum(axis=1)).ravel()
        self.Tnorm = diags(np.divide(1., row_sums, out=np.zeros(nu), where=row_sums > 0)) @ self.T
        # Salakhutdinov & Mnih, section 2, Eq.(5): their experiments use the
        # logistic observation model and (r-min)/(max-min), not raw-score PMF.
        self.logistic = model in ('PMF', 'RSTE', 'SoRec', 'SocialMF', 'TrustMF')
        # Source papers use different normalizations; no test-data statistics.
        self.offset = data.minimum if model in ('PMF', 'SoRec', 'SocialMF') else 0.
        self.scale = data.maximum - self.offset
        self.target = (self.r - self.offset) / self.scale if self.logistic else self.r
        self.fields = [('p', (nu, dim)), ('q', (ni, dim))]
        if model in ('SVD++', 'TrustSVD'):
            self.fields += [('y', (ni, dim))]
        if model in ('TrustSVD', 'SoRec', 'TrustMF'):
            self.fields += [('w', (nu, dim))]
        if model in ('SVD++', 'TrustSVD'):
            self.fields += [('bu', (nu,)), ('bi', (ni,))]
        self.slices, start = {}, 0
        for name, shape in self.fields:
            size = int(np.prod(shape))
            self.slices[name] = (slice(start, start + size), shape)
            start += size
        self.size = start
        self.zero_bu, self.zero_bi = np.zeros(nu), np.zeros(ni)
        if model == 'SoReg':
            R = csr_matrix((self.r, (self.u, self.i)), shape=(nu, ni))
            multiplicity = csr_matrix((np.ones(len(self.r)), (self.u, self.i)), shape=(nu, ni))
            # A rating matrix must not sum repeated observations into scores
            # outside the scale. Average duplicates only for PCC, while the
            # original observations remain intact in the prediction loss.
            R.data /= multiplicity.data
            R.sort_indices()
            self.sim = pcc_weights(data.tu, data.tv, R.indptr, R.indices, R.data)
        if model == 'RSTE':
            # No outgoing neighbors -> user's own preference, not alpha*preference.
            alpha_u = np.where(self.tc > 0, alpha, 1.)
            self.ensemble = diags(alpha_u) + diags(1. - alpha_u) @ self.Tnorm
        if model == 'SoRec':
            # SoRec Eq. (2): in-degree confidence on each observed trust edge.
            self.trust_target = data.t * np.sqrt(self.tin[data.tv] / (self.tc[data.tu] + self.tin[data.tv]))
        else:
            self.trust_target = data.t
        self.penalties = self._penalties()

    def _penalties(self):
        nu, ni = self.data.n_users, self.data.n_items
        if self.model == 'TrustSVD':
            return dict(p=self.reg*invsqrt(self.rc) + self.social*invsqrt(self.tc),
                        q=self.reg*invsqrt(self.ic), y=self.reg*invsqrt(self.ic),
                        w=self.reg*invsqrt(self.tin), bu=self.reg*invsqrt(self.rc),
                        bi=self.reg*invsqrt(self.ic))
        if self.model == 'SVD++':
            # Standard per-observation L2 regularization represented as a global sum.
            return dict(p=self.reg*self.rc, q=self.reg*self.ic,
                        y=self.reg*np.asarray(self.A.T @ self.rc).ravel(),
                        bu=self.reg*self.rc, bi=self.reg*self.ic)
        if self.model == 'TrustMF':
            degree = self.tc if self.role == 'truster' else self.tin
            other = self.tin if self.role == 'truster' else self.tc
            return dict(p=self.reg*(self.rc + degree), q=self.reg*self.ic, w=self.reg*other)
        return {n: np.full(shape[0], self.reg) for n, shape in self.fields}

    def unpack(self, x):
        return {name: x[s].reshape(shape) for name, (s, shape) in self.slices.items()}

    def pack(self, arrays):
        return np.concatenate([np.asarray(arrays[n]).ravel() for n, _ in self.fields])

    def initial(self, seed):
        rng = np.random.default_rng(seed)
        parts = {}
        for name, shape in self.fields:
            parts[name] = np.zeros(shape) if name in ('bu', 'bi') else rng.normal(0., .05, shape)
        # Unobserved parameters must not produce arbitrary cold-start predictions.
        parts['p'][self.rc + self.tc + self.tin == 0] = 0.
        parts['q'][self.ic == 0] = 0.
        if 'y' in parts:
            parts['y'][self.ic == 0] = 0.
        if 'w' in parts:
            parts['w'][self.tin == 0 if self.role == 'truster' else self.tc == 0] = 0.
        return self.pack(parts)

    def effective(self, z):
        h = z['p'].copy()
        if self.model == 'RSTE':
            h = self.ensemble @ h
        if 'y' in z:
            h += self.Hr @ z['y']
        if self.model == 'TrustSVD':
            h += self.Ht @ z['w']
        return h

    def value_grad(self, x):
        z = self.unpack(x)
        h = self.effective(z)
        loss, gh, gq, gbu, gbi = rating_loss_grad(
            self.u, self.i, self.target, h, z['q'], z.get('bu', self.zero_bu),
            z.get('bi', self.zero_bi), self.mean if 'bu' in z else 0., self.logistic)
        g = {n: np.zeros_like(v) for n, v in z.items()}
        g['p'] = self.ensemble.T @ gh if self.model == 'RSTE' else gh
        g['q'] = gq
        if 'bu' in z:
            g['bu'], g['bi'] = gbu, gbi
        if 'y' in z:
            g['y'] = self.Hr.T @ gh
        if self.model == 'TrustSVD':
            g['w'] = self.Ht.T @ gh
        if self.model in ('TrustSVD', 'SoRec', 'TrustMF'):
            tu, tv = self.data.tu, self.data.tv
            if self.model == 'TrustMF' and self.role == 'trustee':
                tu, tv = tv, tu
            tl, gp, gw = edge_loss_grad(tu, tv, self.trust_target, z['p'], z['w'],
                                      self.social, self.model != 'TrustSVD')
            loss += tl
            g['p'] += gp
            g['w'] += gw
        elif self.model == 'SocialMF':
            diff = z['p'] - self.Tnorm @ z['p']
            diff[self.tc == 0] = 0.
            loss += .5*self.social*np.sum(diff*diff)
            g['p'] += self.social*(diff - self.Tnorm.T @ diff)
        elif self.model == 'SoReg':
            tl, gp = pair_penalty(self.data.tu, self.data.tv, self.sim, z['p'], self.social)
            loss += tl
            g['p'] += gp
        for name, value in z.items():
            weight = self.penalties[name]
            if value.ndim == 2:
                weight = weight[:, None]
            loss += .5*np.sum(weight*value*value)
            g[name] += weight*value
        # Scale whole objective, preserving its minimizers and gradient identity.
        norm = len(self.r)
        return float(loss/norm), self.pack(g)/norm

    def predict(self, x, u, i):
        z = self.unpack(x)
        h = self.effective(z)
        raw = np.einsum('ij,ij->i', h[u], z['q'][i])
        if self.logistic:
            return self.offset + self.scale*expit(raw)
        if 'bu' in z:
            raw += self.mean + z['bu'][u] + z['bi'][i]
        return raw

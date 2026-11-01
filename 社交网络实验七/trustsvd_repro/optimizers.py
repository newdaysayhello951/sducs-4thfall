"""A small independent full-gradient descent solver for the paper's Eq.(2).

Armijo backtracking ensures descent; a Barzilai-Borwein scalar step avoids
requiring an undocumented learning rate. The main run uses this solver;
separately disclosed supplemental runs use SciPy L-BFGS-B.
"""
from types import SimpleNamespace
import numpy as np


def gradient_descent(fun, x0, maxiter, callback=None, gtol=1e-7):
    x = x0.copy()
    value, grad = fun(x)
    step = 1. / max(float(np.linalg.norm(grad)), 1e-8)
    message, nit = 'maximum iterations reached', 0
    for iteration in range(maxiter):
        if np.max(np.abs(grad)) <= gtol:
            message = 'gradient tolerance reached'
            break
        norm2 = float(grad@grad)
        accepted = False
        for _ in range(35):
            proposal = x-step*grad
            new_value, new_grad = fun(proposal)
            if np.isfinite(new_value) and new_value <= value-1e-4*step*norm2:
                accepted = True
                break
            step *= .5
        if not accepted:
            message = 'backtracking could not find a descent step'
            break
        s, y = proposal-x, new_grad-grad
        sy = float(s@y)
        step = np.clip(float(s@s)/sy, 1e-8, 1e8) if sy > 1e-20 else min(step*1.5,1e8)
        x, value, grad = proposal, new_value, new_grad
        nit = iteration+1
        if callback is not None:
            callback(x)
    return SimpleNamespace(x=x, fun=value, jac=grad, nit=nit, message=message)

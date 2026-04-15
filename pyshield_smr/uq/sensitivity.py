"""Morris elementary-effects screening.

The Morris method is a cheap global sensitivity analysis that ranks input
variables by how much they move an output across a grid of trajectories. It is
a screening step: cheap enough to run early, informative enough to tell you
which inputs deserve a full variance-based sensitivity study.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Sequence

import numpy as np


def morris_screen(
    f: Callable[[Dict[str, float]], float],
    bounds: Dict[str, tuple[float, float]],
    *,
    n_trajectories: int = 20,
    grid_levels: int = 4,
    seed: int = 7,
) -> Dict[str, Dict[str, float]]:
    """Return per-parameter mean absolute elementary effect ``mu_star`` and sigma.

    Parameters
    ----------
    f
        Callable taking ``{name: value}``.
    bounds
        ``{name: (low, high)}``.
    n_trajectories
        Number of Morris trajectories (``r``).
    grid_levels
        Levels per axis (``p``); the step ``delta = p / (2*(p-1))``.

    Returns
    -------
    dict
        ``{name: {mu_star: ..., sigma: ...}}`` — Morris summary.
    """
    rng = np.random.default_rng(seed)
    names = list(bounds.keys())
    k = len(names)
    p = grid_levels
    delta = p / (2.0 * (p - 1))
    effects: Dict[str, List[float]] = {n: [] for n in names}
    for _ in range(n_trajectories):
        base = rng.integers(0, p, size=k) / (p - 1)
        order = rng.permutation(k)
        current = base.copy()
        y_prev = _eval(f, current, bounds, names)
        for i in order:
            new = current.copy()
            new[i] = min(new[i] + delta, 1.0) if new[i] + delta <= 1.0 else new[i] - delta
            y_new = _eval(f, new, bounds, names)
            effects[names[i]].append((y_new - y_prev) / delta)
            current = new
            y_prev = y_new
    out: Dict[str, Dict[str, float]] = {}
    for n in names:
        arr = np.array(effects[n])
        out[n] = {
            "mu_star": float(np.mean(np.abs(arr))),
            "sigma": float(np.std(arr, ddof=1)),
        }
    return out


def _eval(
    f: Callable[[Dict[str, float]], float],
    x_unit: np.ndarray,
    bounds: Dict[str, tuple[float, float]],
    names: Sequence[str],
) -> float:
    x = {n: bounds[n][0] + (bounds[n][1] - bounds[n][0]) * float(x_unit[i]) for i, n in enumerate(names)}
    return float(f(x))

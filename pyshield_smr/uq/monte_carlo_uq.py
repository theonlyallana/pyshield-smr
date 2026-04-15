"""Latin-hypercube Monte Carlo uncertainty propagation.

Supports lognormal, normal, and uniform marginals. Correlations are ignored in
this pedagogical implementation (a production UQ layer would use the
Iman–Conover rank transform or a Gaussian copula).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence

import numpy as np


@dataclass(frozen=True)
class Marginal:
    """A single marginal distribution."""

    name: str
    distribution: str  # "lognormal", "normal", "uniform"
    parameters: Dict[str, float]


def lhs_samples(
    marginals: Sequence[Marginal],
    n_samples: int,
    *,
    seed: int = 42,
) -> Dict[str, np.ndarray]:
    """Draw ``n_samples`` Latin-hypercube samples for each marginal.

    Returns a dict ``{name: array of shape (n_samples,)}``.
    """
    rng = np.random.default_rng(seed)
    out: Dict[str, np.ndarray] = {}
    for m in marginals:
        # Stratified uniform samples (one per stratum), then permute.
        strata_edges = np.linspace(0.0, 1.0, n_samples + 1)
        u = rng.uniform(strata_edges[:-1], strata_edges[1:])
        rng.shuffle(u)
        out[m.name] = _icdf(m, u)
    return out


def _icdf(m: Marginal, u: np.ndarray) -> np.ndarray:
    if m.distribution == "normal":
        mu = float(m.parameters["mean"])
        sigma = float(m.parameters["std"])
        from scipy.stats import norm
        return norm.ppf(u, loc=mu, scale=sigma)
    if m.distribution == "lognormal":
        mu = float(m.parameters["mean_log"])
        sigma = float(m.parameters["std_log"])
        from scipy.stats import norm
        return np.exp(norm.ppf(u, loc=mu, scale=sigma))
    if m.distribution == "uniform":
        lo = float(m.parameters["low"])
        hi = float(m.parameters["high"])
        return lo + (hi - lo) * u
    raise ValueError(f"unknown distribution: {m.distribution!r}")


def propagate_scalar(
    f: Callable[[Dict[str, float]], float],
    samples: Dict[str, np.ndarray],
) -> Dict[str, float]:
    """Apply ``f`` to each sample and return summary statistics.

    Returns
    -------
    dict
        ``{mean, std, median, p5, p95, n}``.
    """
    n = len(next(iter(samples.values())))
    results = np.empty(n)
    for i in range(n):
        args = {k: float(v[i]) for k, v in samples.items()}
        results[i] = float(f(args))
    return {
        "mean": float(np.mean(results)),
        "std": float(np.std(results, ddof=1)),
        "median": float(np.median(results)),
        "p5": float(np.percentile(results, 5)),
        "p95": float(np.percentile(results, 95)),
        "n": int(n),
    }

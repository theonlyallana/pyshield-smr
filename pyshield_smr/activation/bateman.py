"""Bateman decay-chain solver.

For a set of ``n`` nuclides with decay constants ``lambda_i`` linked by branching
ratios ``b_{ij}`` (parent ``j`` → daughter ``i``), the inventory evolves as::

    dN/dt = A * N,    A_ii = -lambda_i,
                      A_ij = b_{ij} * lambda_j  (j → i, j != i).

The closed-form solution is ``N(t) = expm(A * t) * N(0)``. SciPy's
``scipy.linalg.expm`` handles this robustly for short chains; long chains used in
production would use a specialised solver (CRAM — Chebyshev Rational
Approximation Method — is the canonical choice in codes like FISPACT / ORIGEN).

This module exposes:

- :func:`decay_matrix` — build the generator matrix from a nuclide set, decay
  constants, and branching ratios,
- :func:`decay_inventory` — evaluate ``N(t)`` at one or many times.
"""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Sequence

import numpy as np
from scipy.linalg import expm


def decay_matrix(
    nuclides: Sequence[str],
    decay_constants_per_s: Mapping[str, float],
    branching: Mapping[tuple[str, str], float] | None = None,
) -> np.ndarray:
    """Build the Bateman generator matrix.

    Parameters
    ----------
    nuclides
        Ordered list of nuclide names. ``branching`` keys reference these names.
    decay_constants_per_s
        Decay constants by nuclide. Missing entries are treated as zero (stable).
    branching
        Mapping ``(parent, daughter) -> branching ratio``.

    Returns
    -------
    numpy.ndarray
        ``(n, n)`` matrix suitable for ``N(t) = expm(A * t) N(0)``.
    """
    n = len(nuclides)
    index = {name: i for i, name in enumerate(nuclides)}
    A = np.zeros((n, n), dtype=float)
    for i, name in enumerate(nuclides):
        A[i, i] = -float(decay_constants_per_s.get(name, 0.0))
    if branching:
        for (parent, daughter), b in branching.items():
            if parent not in index or daughter not in index:
                continue
            if parent == daughter:
                continue
            j = index[parent]
            i = index[daughter]
            lam = float(decay_constants_per_s.get(parent, 0.0))
            A[i, j] += b * lam
    return A


def decay_inventory(
    nuclides: Sequence[str],
    initial_atoms: Mapping[str, float],
    decay_constants_per_s: Mapping[str, float],
    times_s: Iterable[float],
    branching: Mapping[tuple[str, str], float] | None = None,
) -> Dict[float, Dict[str, float]]:
    """Evolve an initial inventory over ``times_s``.

    Parameters
    ----------
    nuclides
        Ordered list of tracked nuclides.
    initial_atoms
        Initial inventory, atoms per nuclide (use ``activity / decay_constant``).
    decay_constants_per_s
        Decay constants.
    times_s
        Elapsed times, seconds.
    branching
        Optional branching.

    Returns
    -------
    dict
        ``{time: {nuclide: atoms}}``.
    """
    A = decay_matrix(nuclides, decay_constants_per_s, branching)
    N0 = np.array([float(initial_atoms.get(name, 0.0)) for name in nuclides])
    out: Dict[float, Dict[str, float]] = {}
    for t in times_s:
        Nt = expm(A * float(t)) @ N0
        out[float(t)] = {name: float(n) for name, n in zip(nuclides, Nt, strict=True)}
    return out

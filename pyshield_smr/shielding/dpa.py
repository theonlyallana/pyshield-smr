"""Atomic displacements per atom (DPA) estimator.

DPA is commonly estimated via the Norgett-Robinson-Torrens (NRT) model:

    N_d(T) = (0.8 * T_dam) / (2 * E_d)

where ``T_dam`` is the damage energy (the portion of recoil kinetic energy that
goes into atomic displacements, not electronic excitation) and ``E_d`` is the
threshold displacement energy. For a neutron flux ``phi(E)`` in ``n/(cm^2 s)``
with displacement cross section ``sigma_d(E)`` in barns,

    DPA_rate = integral_E phi(E) * sigma_d(E) dE  [displacements/atom/s]

This module exposes a convenience wrapper that accepts tabulated ``(E, phi,
sigma_d)`` arrays and integrates via the trapezoidal rule. It is deliberately
pedagogical — a production workflow would consume multi-group neutron fluxes
from a transport solution.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

from ..physics.constants import BARN_TO_CM2


def dpa_rate(
    energies_MeV: Iterable[float] | np.ndarray,
    neutron_flux_n_per_cm2_per_s: Iterable[float] | np.ndarray,
    displacement_xs_barn: Iterable[float] | np.ndarray,
) -> float:
    """Return the DPA rate in displacements per atom per second.

    Parameters
    ----------
    energies_MeV
        Energy grid (MeV).
    neutron_flux_n_per_cm2_per_s
        Neutron flux per unit energy at each grid point (``n / (cm^2 s MeV)``).
        For a flux given per bin, divide by bin width before calling.
    displacement_xs_barn
        Displacement cross section at each energy, in barns.

    Returns
    -------
    float
        DPA rate.
    """
    E = np.asarray(energies_MeV, dtype=float)
    phi = np.asarray(neutron_flux_n_per_cm2_per_s, dtype=float)
    sig = np.asarray(displacement_xs_barn, dtype=float) * BARN_TO_CM2  # cm^2
    if not (E.shape == phi.shape == sig.shape):
        raise ValueError("all inputs must have the same shape")
    integrand = phi * sig
    return float(np.trapezoid(integrand, E))

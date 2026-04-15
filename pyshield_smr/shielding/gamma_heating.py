"""Volumetric gamma heating estimator.

Gamma heating is the volumetric energy deposition by photons in a material, usually
reported in ``W / cm^3`` or ``W / g``. For a spectral fluence rate ``phi(E)`` in
``photons / (cm^2 s)`` the mass energy-absorption rate is

    H_mass(r) = integral_E phi(E) * E * mu_en/rho(E) dE   [MeV / (g s)]

and the volumetric heating rate is ``H_vol = H_mass * rho``. This module uses the
total mass-attenuation coefficient as an overestimate for ``mu_en/rho`` (the two
differ mainly by the energy carried away by scattered photons). Good enough for
teaching; a production run needs proper ``mu_en/rho`` data.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

from ..physics.attenuation import interpolate_mass_attenuation
from ..physics.constants import MEV_TO_J
from ..physics.materials import Material


def gamma_heating_rate(
    *,
    material: Material,
    energies_MeV: Iterable[float] | np.ndarray,
    fluence_per_cm2_per_s: Iterable[float] | np.ndarray,
) -> dict[str, float]:
    """Return the gamma-heating rate in a material.

    Parameters
    ----------
    material
        Material of interest.
    energies_MeV, fluence_per_cm2_per_s
        Spectral fluence rate arrays at each energy.

    Returns
    -------
    dict
        ``{"W_per_g": ..., "W_per_cm3": ...}``.
    """
    e = np.asarray(energies_MeV, dtype=float)
    phi = np.asarray(fluence_per_cm2_per_s, dtype=float)
    if e.shape != phi.shape:
        raise ValueError("energies and fluence arrays must have the same shape")
    mu_over_rho = interpolate_mass_attenuation(material, e)  # cm^2/g
    # MeV deposited per gram per second per photon per cm^2/s:
    mev_per_g_s = np.trapezoid(phi * e * mu_over_rho, e)  # MeV / (g s)
    w_per_g = float(mev_per_g_s * MEV_TO_J)
    w_per_cm3 = float(w_per_g * material.density_g_per_cm3)
    return {"W_per_g": w_per_g, "W_per_cm3": w_per_cm3}

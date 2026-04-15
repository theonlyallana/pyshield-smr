"""Mass and linear attenuation helpers.

These helpers provide:

- :func:`interpolate_mass_attenuation` — log-log interpolation of $\\mu/\\rho$ versus energy,
- :func:`linear_attenuation_coefficient` — convert a mass attenuation coefficient at a
  given energy and density into the usual ``1/m`` (or ``1/cm``) linear attenuation
  coefficient.

We perform interpolation in ``log`` space on both axes because mass attenuation
coefficients vary smoothly on a log-log scale away from absorption edges; this is a
well-known numerical convenience and is what most production shielding codes do for
fast lookup.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

from .materials import Material


def interpolate_mass_attenuation(
    material: Material,
    energies_MeV: float | Iterable[float] | np.ndarray,
) -> np.ndarray:
    """Log-log interpolate the mass attenuation coefficient of ``material``.

    Parameters
    ----------
    material
        :class:`Material` with tabulated ``energies_MeV`` and ``mu_over_rho_cm2_per_g``.
    energies_MeV
        Scalar or array of energies in MeV at which to evaluate. Energies outside the
        tabulated range are clamped.

    Returns
    -------
    numpy.ndarray
        Mass attenuation coefficients in ``cm^2 / g``, same shape as ``energies_MeV``.
    """
    e = np.atleast_1d(np.asarray(energies_MeV, dtype=float))
    e = np.clip(e, material.energies_MeV.min(), material.energies_MeV.max())
    log_e_tab = np.log(material.energies_MeV)
    log_mu_tab = np.log(material.mu_over_rho_cm2_per_g)
    log_e = np.log(e)
    log_mu = np.interp(log_e, log_e_tab, log_mu_tab)
    return np.exp(log_mu)


def linear_attenuation_coefficient(
    material: Material,
    energies_MeV: float | Iterable[float] | np.ndarray,
    *,
    in_units: str = "per_cm",
) -> np.ndarray:
    """Return the linear attenuation coefficient for ``material``.

    Parameters
    ----------
    material
        :class:`Material` used to look up the mass attenuation coefficient.
    energies_MeV
        Scalar or array of energies in MeV.
    in_units
        Either ``"per_cm"`` (default) or ``"per_m"``.

    Returns
    -------
    numpy.ndarray
        Linear attenuation coefficient (``1/cm`` by default).

    Notes
    -----
    By definition ``mu = (mu/rho) * rho``. The result is returned per the requested
    length unit.
    """
    mu_over_rho = interpolate_mass_attenuation(material, energies_MeV)
    mu_per_cm = mu_over_rho * material.density_g_per_cm3
    if in_units == "per_cm":
        return mu_per_cm
    if in_units == "per_m":
        return mu_per_cm * 100.0
    raise ValueError(f"unknown units: {in_units!r}; expected 'per_cm' or 'per_m'")

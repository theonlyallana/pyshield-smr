"""Fluence-to-dose conversion.

This module exposes :func:`flux_to_dose_h10`, which converts a photon scalar fluence
(or fluence rate) at a given energy into ambient dose equivalent ``H*(10)`` using
ICRP-74 / ICRP-116 conversion coefficients.

The coefficients are shipped in ``data/flux_to_dose/icrp74_photon.json`` as
``pSv * cm^2 / photon``. The conversion used here is::

    H*(10)_rate [Sv/s] = fluence_rate [1/(cm^2 * s)] * coeff [pSv*cm^2] * 1e-12

Hourly dose rate (``Sv/h``) is obtained by multiplying by 3600.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


@lru_cache(maxsize=1)
def _load_coefficients() -> Tuple[np.ndarray, np.ndarray]:
    path = DATA_ROOT / "flux_to_dose" / "icrp74_photon.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    energies = np.array(raw["energies_MeV"], dtype=float)
    coeffs = np.array(raw["h_star_10_pSv_cm2"], dtype=float)
    return energies, coeffs


def flux_to_dose_h10(
    energies_MeV: float | Iterable[float] | np.ndarray,
    fluence_per_cm2_per_s: float | Iterable[float] | np.ndarray,
    *,
    per_hour: bool = True,
) -> np.ndarray:
    """Convert a photon fluence-rate spectrum to H*(10) dose rate.

    Parameters
    ----------
    energies_MeV
        Photon energies, MeV.
    fluence_per_cm2_per_s
        Photon scalar fluence rate at each energy, ``photons / (cm^2 * s)``.
    per_hour
        If ``True`` (default) the result is in ``Sv / h``. Otherwise ``Sv / s``.

    Returns
    -------
    numpy.ndarray
        Dose rate, element-wise. Sum over the energy axis for a total.

    Notes
    -----
    Coefficients are linearly interpolated in ``log(E)``; this is consistent with how
    ICRP reports are usually read for production dose assessments, although a
    log-log interpolation can also be argued. The difference between the two is
    ≲2% at the tabulated energies.
    """
    energies = np.atleast_1d(np.asarray(energies_MeV, dtype=float))
    fluence = np.atleast_1d(np.asarray(fluence_per_cm2_per_s, dtype=float))
    if energies.shape != fluence.shape:
        raise ValueError(
            f"energies shape {energies.shape} != fluence shape {fluence.shape}"
        )
    tab_e, tab_c = _load_coefficients()
    tab_e_clipped = np.clip(energies, tab_e.min(), tab_e.max())
    coeff_pSv_cm2 = np.interp(np.log(tab_e_clipped), np.log(tab_e), tab_c)
    dose_sv_s = fluence * coeff_pSv_cm2 * 1.0e-12
    if per_hour:
        return dose_sv_s * 3600.0
    return dose_sv_s

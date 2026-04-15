"""Simple detector-response model.

Given a spectral fluence and an energy-dependent detector response function
``R(E)`` (counts per unit fluence), return the integrated count rate.

Real detectors need a full Monte Carlo simulation or MCA calibration; this
module shows the pattern and provides an analytical "ideal" response used by
tests.
"""

from __future__ import annotations

from typing import Callable, Iterable

import numpy as np


def detector_response(
    energies_MeV: Iterable[float] | np.ndarray,
    fluence_per_cm2_per_s: Iterable[float] | np.ndarray,
    response: Callable[[np.ndarray], np.ndarray],
    *,
    area_cm2: float = 1.0,
) -> float:
    """Integrate ``R(E) * phi(E)`` across energy.

    Parameters
    ----------
    energies_MeV, fluence_per_cm2_per_s
        Spectral fluence rate.
    response
        Callable taking an energy array (MeV) and returning counts per photon.
    area_cm2
        Detector active area, ``cm^2``.

    Returns
    -------
    float
        Count rate in counts per second.
    """
    e = np.asarray(energies_MeV, dtype=float)
    phi = np.asarray(fluence_per_cm2_per_s, dtype=float)
    R = response(e)
    return float(np.trapezoid(R * phi * area_cm2, e))

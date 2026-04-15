"""Convert a tabulated photon fluence spectrum to ambient dose rate."""

from __future__ import annotations

import numpy as np

from ..physics.dose import flux_to_dose_h10


def spectrum_to_dose_rate(
    energies_MeV: np.ndarray,
    fluence_per_cm2_per_s: np.ndarray,
    *,
    per_hour: bool = True,
) -> float:
    """Integrate a fluence-rate spectrum against H*(10) to give a scalar dose rate.

    Parameters
    ----------
    energies_MeV
        Photon energies, MeV.
    fluence_per_cm2_per_s
        Fluence rate at each energy.
    per_hour
        ``True`` for Sv/h, ``False`` for Sv/s.

    Returns
    -------
    float
        Scalar dose rate.
    """
    dose_per_energy = flux_to_dose_h10(
        energies_MeV, fluence_per_cm2_per_s, per_hour=per_hour
    )
    return float(np.sum(dose_per_energy))

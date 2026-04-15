"""Lightweight unit registry.

We deliberately do not take a dependency on ``pint`` — the goal is to enforce
*explicit* units in function signatures and docstrings, not to carry a
runtime unit system through every NumPy array. This module therefore provides
a very small set of named multipliers and conversion helpers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class _UnitRegistry:
    """Unit multipliers used across the code base.

    Access pattern::

        from pyshield_smr.physics.units import ureg
        length_cm = length_m * ureg.cm_per_m
    """

    cm_per_m: float = 100.0
    m_per_cm: float = 0.01
    mm_per_m: float = 1000.0
    m_per_mm: float = 1e-3
    seconds_per_hour: float = 3600.0
    hours_per_second: float = 1.0 / 3600.0
    sv_per_psv: float = 1.0e-12  # 1 pSv
    psv_per_sv: float = 1.0e12

    # Dose-rate conversions used in reports
    sv_per_h_to_usv_per_h: float = 1.0e6
    usv_per_h_to_sv_per_h: float = 1.0e-6


ureg = _UnitRegistry()


def mev_to_kev(energy_mev: float) -> float:
    """Convert MeV to keV.

    Parameters
    ----------
    energy_mev
        Energy in MeV.

    Returns
    -------
    float
        Energy in keV.
    """
    return energy_mev * 1000.0


def kev_to_mev(energy_kev: float) -> float:
    """Convert keV to MeV."""
    return energy_kev * 1e-3

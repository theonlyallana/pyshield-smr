"""Photon buildup factors.

The point-kernel dose formulation separates the uncollided contribution from the
scattered (built-up) contribution:

    D(r) = (S / 4*pi*r^2) * exp(-mu*x) * B(mu*x, E, material) * K(E)

where ``B`` is the buildup factor. This module implements the *two-term Taylor form*::

    B(mu_x) = A * exp(-a1 * mu_x) + (1 - A) * exp(-a2 * mu_x)

with parameters tabulated versus material and energy in
``data/buildup_factors/taylor_two_term.json``. The form is widely used in teaching and
early design sizing; the ANS-6.4.3 Geometric-Progression (GP) form is generally
preferred for production work but is intentionally out of scope here (see
``docs/theory/02_point_kernel.md`` for the trade-off).

The implementation interpolates *parameters* log-linearly in energy and then
evaluates ``B(mu_x)`` directly. It supports vector ``mu_x`` inputs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict

import numpy as np


DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class TaylorParams:
    """Two-term Taylor buildup parameters at a single energy."""

    A: float
    alpha1: float
    alpha2: float


@lru_cache(maxsize=1)
def _load_table() -> Dict[str, Dict[float, TaylorParams]]:
    path = DATA_ROOT / "buildup_factors" / "taylor_two_term.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    table: Dict[str, Dict[float, TaylorParams]] = {}
    for material, entries in raw["materials"].items():
        by_energy: Dict[float, TaylorParams] = {}
        for key, v in entries.items():
            # key is "x.y_MeV"
            energy = float(key.split("_")[0])
            by_energy[energy] = TaylorParams(
                A=float(v["A"]),
                alpha1=float(v["alpha1"]),
                alpha2=float(v["alpha2"]),
            )
        table[material] = by_energy
    return table


def _interpolate_params(material: str, energy_MeV: float) -> TaylorParams:
    """Log-linear interpolation of Taylor parameters in energy."""
    table = _load_table()
    if material not in table:
        raise KeyError(
            f"no Taylor buildup parameters for material {material!r}; "
            f"available: {sorted(table)}"
        )
    entries = sorted(table[material].items())
    energies = np.array([e for e, _ in entries])
    energy_MeV_c = float(np.clip(energy_MeV, energies.min(), energies.max()))
    le = np.log(energies)
    le_c = np.log(energy_MeV_c)
    A_arr = np.array([p.A for _, p in entries])
    a1_arr = np.array([p.alpha1 for _, p in entries])
    a2_arr = np.array([p.alpha2 for _, p in entries])
    return TaylorParams(
        A=float(np.interp(le_c, le, A_arr)),
        alpha1=float(np.interp(le_c, le, a1_arr)),
        alpha2=float(np.interp(le_c, le, a2_arr)),
    )


def taylor_buildup(
    material: str,
    energy_MeV: float,
    mu_x: np.ndarray | float,
) -> np.ndarray:
    """Evaluate the two-term Taylor buildup factor.

    Parameters
    ----------
    material
        One of the materials in ``data/buildup_factors/taylor_two_term.json``.
    energy_MeV
        Photon energy in MeV. Clamped to the tabulated range.
    mu_x
        Optical depth ``mu * x`` (dimensionless; number of mean free paths).

    Returns
    -------
    numpy.ndarray
        Buildup factor ``B >= 1`` for physical inputs; shape matches ``mu_x``.

    Notes
    -----
    The form is ``B = A * exp(+alpha1 * mu_x) + (1 - A) * exp(-alpha2 * mu_x)``.
    ``alpha1`` drives the growth term (small positive value); ``alpha2`` drives the
    complementary decay term (larger positive value). At ``mu_x = 0`` this yields
    ``A + (1 - A) = 1`` by construction. Valid for ``mu_x ≤ 20`` mean free paths.

    Sign convention: the stored ``alpha1`` parameter enters the exponent with a
    **positive** sign. This matches the parameterisation in the bundled
    ``data/buildup_factors/taylor_two_term.json`` dataset.
    """
    scalar_input = np.ndim(mu_x) == 0
    mu_x_arr = np.atleast_1d(np.asarray(mu_x, dtype=float))
    mu_x_arr = np.clip(mu_x_arr, 0.0, 20.0)  # validity ceiling per the dataset meta
    params = _interpolate_params(material, energy_MeV)
    # alpha1: positive exponent (buildup grows with optical depth).
    # alpha2: negative exponent (complementary damping term).
    B = params.A * np.exp(params.alpha1 * mu_x_arr) + (1.0 - params.A) * np.exp(
        -params.alpha2 * mu_x_arr
    )
    # Physicality guard: B must be >= 1.  In practice this only triggers at the
    # tails of the interpolated parameter range.
    result = np.maximum(B, 1.0)
    # Return scalar if input was scalar (avoids deprecation on float() conversion).
    return float(result[0]) if scalar_input else result

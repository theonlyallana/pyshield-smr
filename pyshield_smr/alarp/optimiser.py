"""ALARP shielding optimisation.

ALARP ("As Low As Reasonably Practicable") is a legal duty in UK nuclear
regulation, not an optimisation algorithm. What an *engineering* ALARP study
can do computationally is frame the trade-off explicitly: at what point does
an additional increment of shielding stop buying a proportionate reduction in
detriment?

Here we implement a simple gradient-based optimiser (SLSQP) that minimises an
objective of the form::

    J(t) = w_dose * annual_collective_dose(t) + w_mass * mass(t)

subject to
    dose_rate(t) <= dose_rate_limit
    t_i >= t_min
    t_i <= t_max

where ``t`` is a vector of slab thicknesses in metres. The user supplies
callables ``dose_rate(t)``, ``annual_collective_dose(t)`` and material densities.
This is the *shape* of an ALARP calculation, not a substitute for the broader
regulatory justification; see ``docs/theory/07_alarp.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Sequence

import numpy as np
from scipy.optimize import minimize


@dataclass(frozen=True)
class OptimisationResult:
    """Result of :func:`optimise_shielding`."""

    thicknesses_m: np.ndarray
    dose_rate_sv_per_h: float
    collective_dose_msv: float
    mass_tonnes: float
    success: bool
    message: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "thicknesses_m": self.thicknesses_m.tolist(),
            "dose_rate_sv_per_h": self.dose_rate_sv_per_h,
            "collective_dose_msv": self.collective_dose_msv,
            "mass_tonnes": self.mass_tonnes,
            "success": self.success,
            "message": self.message,
        }


def optimise_shielding(
    *,
    initial_thicknesses_m: Sequence[float],
    dose_rate_sv_per_h_of: Callable[[np.ndarray], float],
    annual_collective_dose_msv_of: Callable[[np.ndarray], float],
    mass_tonnes_of: Callable[[np.ndarray], float],
    dose_rate_limit_sv_per_h: float,
    thickness_bounds_m: Sequence[tuple[float, float]],
    weights: tuple[float, float] = (1.0, 0.01),
) -> OptimisationResult:
    """Run a simple ALARP-shaped shielding optimisation.

    Returns
    -------
    OptimisationResult
    """
    x0 = np.asarray(initial_thicknesses_m, dtype=float)
    w_dose, w_mass = weights

    def objective(t: np.ndarray) -> float:
        return w_dose * float(annual_collective_dose_msv_of(t)) + w_mass * float(
            mass_tonnes_of(t)
        )

    constraints = [
        {
            "type": "ineq",
            "fun": lambda t: dose_rate_limit_sv_per_h - float(dose_rate_sv_per_h_of(t)),
        }
    ]
    res = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=list(thickness_bounds_m),
        constraints=constraints,
        options={"maxiter": 200, "ftol": 1e-8},
    )
    t_star = np.asarray(res.x, dtype=float)
    return OptimisationResult(
        thicknesses_m=t_star,
        dose_rate_sv_per_h=float(dose_rate_sv_per_h_of(t_star)),
        collective_dose_msv=float(annual_collective_dose_msv_of(t_star)),
        mass_tonnes=float(mass_tonnes_of(t_star)),
        success=bool(res.success),
        message=str(res.message),
    )

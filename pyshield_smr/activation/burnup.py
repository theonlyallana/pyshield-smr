"""Simplified buildup / burn-up model.

For a single activation channel ``Target --sigma*phi--> Product --lambda-->`` the
standard result is::

    N_product(t) = N_target * sigma * phi / lambda * (1 - exp(-lambda * t))

This module gives that closed-form expression, and a cooldown decay afterward.
It is a deliberate stand-in for a full ORIGEN / FISPACT depletion calculation.
"""

from __future__ import annotations

import numpy as np


def simple_burnup_buildup(
    *,
    target_atoms: float,
    activation_xs_barn: float,
    flux_n_per_cm2_per_s: float,
    product_decay_constant_per_s: float,
    irradiation_time_s: float,
    cooldown_time_s: float = 0.0,
) -> dict[str, float]:
    """Return the product atom count at end of irradiation and after cooldown.

    Returns
    -------
    dict
        ``{"end_of_irradiation_atoms": ..., "after_cooldown_atoms": ...,
           "end_of_irradiation_bq": ..., "after_cooldown_bq": ...}``.
    """
    sigma_cm2 = activation_xs_barn * 1e-24
    R = target_atoms * sigma_cm2 * flux_n_per_cm2_per_s  # reactions/s
    lam = float(product_decay_constant_per_s)
    if lam <= 0.0:
        # Stable product: purely linear buildup, ignores cooldown decay.
        end_atoms = R * irradiation_time_s
        return {
            "end_of_irradiation_atoms": end_atoms,
            "after_cooldown_atoms": end_atoms,
            "end_of_irradiation_bq": 0.0,
            "after_cooldown_bq": 0.0,
        }
    end_atoms = (R / lam) * (1.0 - np.exp(-lam * irradiation_time_s))
    after_atoms = end_atoms * np.exp(-lam * cooldown_time_s)
    return {
        "end_of_irradiation_atoms": float(end_atoms),
        "after_cooldown_atoms": float(after_atoms),
        "end_of_irradiation_bq": float(lam * end_atoms),
        "after_cooldown_bq": float(lam * after_atoms),
    }

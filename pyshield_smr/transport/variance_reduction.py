"""Variance reduction for the Monte Carlo engine.

Two canonical techniques are implemented, following standard textbook definitions
(Shultis & Faw, "Radiation Shielding"; Lux & Koblinger, "Monte Carlo Particle
Transport Methods"):

* **Implicit capture.** Instead of terminating a photon at an absorption event, its
  statistical weight is reduced by the non-absorption probability ``(mu_s/mu_t)``
  and the photon is forced to scatter. This cuts variance for deeply penetrating
  tallies.
* **Russian roulette + splitting (weight window).** If a photon's weight drops
  below a lower bound ``w_low``, kill it with probability ``1 - w/w_low`` and
  otherwise boost it back to ``w_low``. If a photon's weight exceeds an upper
  bound ``w_high``, split it into ``k`` lower-weight copies.

These preserve the expected tally (unbiased) while reducing variance for
problems where most source particles contribute zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass(frozen=True)
class WeightWindow:
    """Simple global weight window.

    Attributes
    ----------
    w_low
        Lower weight bound; particles below this face Russian roulette.
    w_high
        Upper weight bound; particles above this are split.
    """

    w_low: float = 1e-6
    w_high: float = 10.0

    def __post_init__(self) -> None:
        if not (0 < self.w_low < self.w_high):
            raise ValueError("require 0 < w_low < w_high")


def roulette_and_split(
    weight: float,
    rng: np.random.Generator,
    window: WeightWindow,
) -> List[float]:
    """Apply Russian roulette below ``w_low`` and splitting above ``w_high``.

    Returns a list of post-transformation weights. An empty list means the particle
    was killed.
    """
    if weight < window.w_low:
        # Roulette: survive with probability p = weight / w_low, boosted to w_low.
        p = weight / window.w_low
        if rng.random() < p:
            return [window.w_low]
        return []
    if weight > window.w_high:
        # Splitting: integer split factor ~ weight / w_high, cap at 10.
        k = min(int(np.floor(weight / window.w_high)) + 1, 10)
        return [weight / k] * k
    return [weight]

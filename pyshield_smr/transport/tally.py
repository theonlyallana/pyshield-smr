"""Monte Carlo tallies.

A tally is an accumulator that records contributions from transported particles. We
provide two simple tallies:

- :class:`EnergyTally` bins contributions into an energy grid (e.g. a fluence
  spectrum).
- :class:`SurfaceTally` records the weight crossing a plane (e.g. the transmitted
  beam on the shielded side of a slab stack).

Both accumulate both a first and second moment so that the standard deviation of
the mean can be reported, giving the usual ``1/sqrt(N)`` scaling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np


@dataclass
class EnergyTally:
    """Histogram fluence / current versus energy, with per-bin variance estimate."""

    energy_edges_MeV: np.ndarray
    _sum: np.ndarray = field(init=False)
    _sum_sq: np.ndarray = field(init=False)
    _n_histories: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        n = len(self.energy_edges_MeV) - 1
        if n <= 0:
            raise ValueError("energy_edges_MeV must have at least two entries")
        self._sum = np.zeros(n, dtype=float)
        self._sum_sq = np.zeros(n, dtype=float)

    def add(self, energy_MeV: float, weight: float) -> None:
        """Score a single contribution at ``energy_MeV`` with statistical weight
        ``weight``.
        """
        if energy_MeV < self.energy_edges_MeV[0] or energy_MeV > self.energy_edges_MeV[-1]:
            return
        idx = int(np.searchsorted(self.energy_edges_MeV, energy_MeV, side="right") - 1)
        idx = min(max(idx, 0), len(self._sum) - 1)
        self._sum[idx] += weight
        self._sum_sq[idx] += weight * weight

    def end_history(self) -> None:
        """Mark the end of a source particle; used for variance estimation."""
        self._n_histories += 1

    def mean(self) -> np.ndarray:
        """Per-bin mean score per source particle."""
        n = max(self._n_histories, 1)
        return self._sum / n

    def relative_error(self) -> np.ndarray:
        """Per-bin relative standard error of the mean.

        Uses the standard Monte Carlo estimator
        ``sigma_mean / mean = sqrt( (<x^2> - <x>^2) / N ) / <x>``.
        Bins with zero mean return ``inf``.
        """
        n = max(self._n_histories, 1)
        mean = self._sum / n
        mean_sq = self._sum_sq / n
        var_mean = np.maximum(mean_sq - mean * mean, 0.0) / n
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = np.where(mean > 0.0, np.sqrt(var_mean) / mean, np.inf)
        return rel

    def to_dict(self) -> Dict[str, list]:
        """Serialisable summary."""
        return {
            "energy_edges_MeV": self.energy_edges_MeV.tolist(),
            "mean": self.mean().tolist(),
            "relative_error": self.relative_error().tolist(),
            "n_histories": self._n_histories,
        }


@dataclass
class SurfaceTally:
    """Accumulates total statistical weight crossing a surface."""

    _sum: float = 0.0
    _sum_sq: float = 0.0
    _n_histories: int = 0
    _per_history: float = 0.0  # accumulated in the current history

    def add(self, weight: float) -> None:
        self._per_history += weight

    def end_history(self) -> None:
        self._sum += self._per_history
        self._sum_sq += self._per_history * self._per_history
        self._per_history = 0.0
        self._n_histories += 1

    def mean(self) -> float:
        n = max(self._n_histories, 1)
        return self._sum / n

    def relative_error(self) -> float:
        n = max(self._n_histories, 1)
        mean = self._sum / n
        mean_sq = self._sum_sq / n
        var_mean = max(mean_sq - mean * mean, 0.0) / n
        if mean <= 0.0:
            return float("inf")
        return float(np.sqrt(var_mean) / mean)

    def to_dict(self) -> Dict[str, float | int]:
        return {
            "mean": self.mean(),
            "relative_error": self.relative_error(),
            "n_histories": self._n_histories,
        }

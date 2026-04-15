"""Spectrum utilities."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Tuple

import numpy as np

from .source_term import LineSource


def aggregate_lines(
    lines: Iterable[LineSource],
    *,
    bin_width_MeV: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """Group nearby lines into bins of width ``bin_width_MeV`` and sum intensities.

    Returns
    -------
    (energies, intensities)
        One-dimensional arrays sorted by energy.
    """
    if bin_width_MeV <= 0:
        raise ValueError("bin_width_MeV must be positive")
    bucket: dict[float, float] = defaultdict(float)
    for line in lines:
        key = round(line.energy_MeV / bin_width_MeV) * bin_width_MeV
        bucket[key] += line.intensity_per_s
    energies = np.array(sorted(bucket.keys()))
    intensities = np.array([bucket[k] for k in energies])
    return energies, intensities

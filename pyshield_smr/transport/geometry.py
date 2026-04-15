"""Minimal analytic geometry primitives.

Two shapes are enough to express most pedagogical shielding problems:

- :class:`SlabStack`: 1-D stack of plane-parallel slabs along +x, each slab described
  by material name and thickness (metres). The first slab begins at ``x = 0``.
- :class:`Sphere`: spherical shell with inner radius ``r_in`` and outer radius ``r_out``.

Real analyses will use CAD / SpaceClaim geometry; this module shows how to ray-trace
the simple cases cleanly. Extending to voxel grids or constructive solid geometry
would subclass a common ``Geometry`` protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np


@dataclass
class SlabStack:
    """Plane-parallel 1-D slab stack along the +x axis.

    Attributes
    ----------
    materials
        Material names, in geometric order along +x.
    thicknesses_m
        Matching slab thicknesses, metres.
    """

    materials: List[str]
    thicknesses_m: List[float]

    def __post_init__(self) -> None:
        if len(self.materials) != len(self.thicknesses_m):
            raise ValueError("materials and thicknesses_m must have the same length")
        if any(t <= 0 for t in self.thicknesses_m):
            raise ValueError("slab thicknesses must be positive")

    @property
    def boundaries_m(self) -> np.ndarray:
        """Slab boundaries in metres, including the starting boundary at 0."""
        return np.concatenate([[0.0], np.cumsum(self.thicknesses_m)])

    @property
    def total_thickness_m(self) -> float:
        return float(np.sum(self.thicknesses_m))

    def material_at(self, x_m: float) -> str | None:
        """Return the material at depth ``x_m`` from the source side, or ``None``
        if ``x_m`` is outside the stack."""
        if x_m < 0.0 or x_m >= self.total_thickness_m:
            return None
        bounds = self.boundaries_m
        idx = int(np.searchsorted(bounds, x_m, side="right") - 1)
        return self.materials[idx]

    def traverse(self, x_m: float, mu: float) -> List[Tuple[str, float]]:
        """Return the sequence of (material, path-length in m) segments from ``x_m``
        in the direction ``mu = cos(theta)`` until the particle exits the stack.

        ``mu`` must be non-zero; positive goes towards +x, negative towards -x.
        """
        if mu == 0.0:
            raise ValueError("grazing trajectories (mu=0) are not supported")
        segments: List[Tuple[str, float]] = []
        bounds = self.boundaries_m
        total = self.total_thickness_m
        x = float(x_m)
        while 0.0 <= x < total:
            if mu > 0:
                idx = int(np.searchsorted(bounds, x, side="right") - 1)
                next_boundary = bounds[idx + 1]
            else:
                idx = int(np.searchsorted(bounds, x, side="right") - 1)
                # If we're exactly on a boundary going left, step into previous slab.
                if np.isclose(x, bounds[idx]) and idx > 0:
                    idx -= 1
                next_boundary = bounds[idx]
            dx = abs(next_boundary - x)
            if dx <= 0.0:
                break
            segments.append((self.materials[idx], dx / abs(mu)))
            x = next_boundary + (1e-15 if mu > 0 else -1e-15)
        return segments


@dataclass
class Sphere:
    """Spherical shell ``r_in <= r <= r_out``, single material."""

    material: str
    r_in_m: float
    r_out_m: float

    def __post_init__(self) -> None:
        if self.r_in_m < 0.0 or self.r_out_m <= self.r_in_m:
            raise ValueError("require 0 <= r_in < r_out")

    @property
    def thickness_m(self) -> float:
        return self.r_out_m - self.r_in_m

"""Point-kernel shielding engine.

Given a set of point sources (position, energy, intensity) and a set of receptor
positions, compute the scalar fluence and ambient dose rate at each receptor
with material-aware attenuation and buildup. The engine is intentionally restricted
to **1-D slab geometry along +x** for pedagogical clarity; extensions to 3-D ray
tracing follow the same pattern but require a richer geometry layer.

Theory (see ``docs/theory/02_point_kernel.md``):

    phi(r) = (S / 4*pi*r^2) * exp(- sum_i mu_i * x_i ) * B( sum_i mu_i*x_i, E, material_max )

where ``mu_i`` and ``x_i`` are the linear attenuation coefficient and path length
in slab ``i``. In this implementation the buildup factor is evaluated in the slab
that contributes the largest optical depth, which is the customary simplification
when a single material dominates the shield.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

import numpy as np

from ..physics.attenuation import linear_attenuation_coefficient
from ..physics.buildup import taylor_buildup
from ..physics.dose import flux_to_dose_h10
from ..physics.materials import Material, load_material_library
from ..transport.geometry import SlabStack


@dataclass(frozen=True)
class PointKernelResult:
    """Result of a point-kernel evaluation at one or more receptors."""

    receptor_positions_m: np.ndarray
    energies_MeV: np.ndarray
    uncollided_fluence: np.ndarray  # shape (n_receptor, n_energy) per source photon
    buildup_fluence: np.ndarray  # same shape, after buildup
    dose_rate_sv_per_h: np.ndarray  # shape (n_receptor,)
    buildup_material: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "receptor_positions_m": self.receptor_positions_m.tolist(),
            "energies_MeV": self.energies_MeV.tolist(),
            "uncollided_fluence": self.uncollided_fluence.tolist(),
            "buildup_fluence": self.buildup_fluence.tolist(),
            "dose_rate_sv_per_h": self.dose_rate_sv_per_h.tolist(),
            "buildup_material": self.buildup_material,
        }


def point_kernel_dose_rate(
    *,
    source_position_m: float,
    source_energies_MeV: Sequence[float],
    source_intensities_per_s: Sequence[float],
    geometry: SlabStack,
    receptor_positions_m: Sequence[float],
    buildup_material: str,
    material_library: Dict[str, Material] | None = None,
) -> PointKernelResult:
    """Point-kernel fluence and dose-rate evaluation.

    Parameters
    ----------
    source_position_m
        Position of the point source along +x, in metres. Must be at or before the
        near side of the slab stack.
    source_energies_MeV, source_intensities_per_s
        Monoenergetic lines (energy in MeV, emission rate in photons/s).
    geometry
        Slab stack describing the shield. The positive-x direction goes from source
        to receptor.
    receptor_positions_m
        Receptor positions along +x, in metres (must be strictly greater than
        ``source_position_m`` and at or past the far side of the stack).
    buildup_material
        Material used to evaluate the buildup factor. Usually the material with the
        dominant optical depth.

    Returns
    -------
    PointKernelResult
    """
    mats = material_library or load_material_library()
    energies = np.asarray(source_energies_MeV, dtype=float)
    intensities = np.asarray(source_intensities_per_s, dtype=float)
    rec_positions = np.asarray(receptor_positions_m, dtype=float)

    if energies.shape != intensities.shape:
        raise ValueError("energies and intensities must have the same shape")
    if np.any(rec_positions <= source_position_m):
        raise ValueError("all receptor positions must be downstream of the source")

    n_rec = rec_positions.size
    n_e = energies.size
    uncollided = np.zeros((n_rec, n_e), dtype=float)
    with_buildup = np.zeros((n_rec, n_e), dtype=float)

    # Pre-compute mu per slab per energy (1/m).
    mu_slabs_per_m = np.zeros((len(geometry.materials), n_e), dtype=float)
    for i, mat_name in enumerate(geometry.materials):
        mu_slabs_per_m[i, :] = linear_attenuation_coefficient(
            mats[mat_name], energies, in_units="per_m"
        )

    thicknesses = np.asarray(geometry.thicknesses_m, dtype=float)

    for r_idx, r_pos in enumerate(rec_positions):
        # Compute optical depth along line from source to receptor.
        # Integrate only the portion of each slab between source and receptor.
        # For 1-D, source_position < first boundary and receptor > last boundary in
        # the common case; we just cap integration to [source_position, r_pos].
        bounds = geometry.boundaries_m
        x0 = max(source_position_m, bounds[0])
        x1 = min(r_pos, bounds[-1])
        # Optical depth per slab, per energy.
        per_slab_depth_m = np.zeros(len(geometry.materials), dtype=float)
        if x1 > x0:
            left = np.maximum(bounds[:-1], x0)
            right = np.minimum(bounds[1:], x1)
            per_slab_depth_m = np.clip(right - left, 0.0, thicknesses)
        optical_depth = (mu_slabs_per_m * per_slab_depth_m[:, None]).sum(axis=0)

        r = r_pos - source_position_m  # source-to-receptor distance, m
        r_cm = r * 100.0
        # Fluence per photon emitted: 1 / (4*pi*r^2 [cm^2]) * exp(-tau)
        geom = 1.0 / (4.0 * np.pi * r_cm * r_cm)
        uncollided[r_idx, :] = intensities * geom * np.exp(-optical_depth)
        # taylor_buildup returns a scalar when given a scalar optical depth.
        B = np.array(
            [float(taylor_buildup(buildup_material, float(energies[e]), float(optical_depth[e]))) for e in range(n_e)]
        )
        with_buildup[r_idx, :] = uncollided[r_idx, :] * B

    # Sum over energy for total dose rate.
    dose_per_energy = np.zeros_like(with_buildup)
    for e in range(n_e):
        dose_per_energy[:, e] = flux_to_dose_h10(
            np.full(n_rec, energies[e]),
            with_buildup[:, e],
            per_hour=True,
        )
    total_dose = dose_per_energy.sum(axis=1)

    return PointKernelResult(
        receptor_positions_m=rec_positions,
        energies_MeV=energies,
        uncollided_fluence=uncollided,
        buildup_fluence=with_buildup,
        dose_rate_sv_per_h=total_dose,
        buildup_material=buildup_material,
    )

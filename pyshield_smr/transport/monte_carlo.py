"""Analog + non-analog photon Monte Carlo transport through a 1-D slab stack.

Scope
-----
This is a pedagogical solver. It transports mono-energetic photons through a
:class:`~pyshield_smr.transport.geometry.SlabStack`, scattering via
Klein–Nishina incoherent scattering and terminating on absorption (analog) or on
roulette kill (non-analog). It tracks transmitted, reflected, and absorbed weight
and spectral fluence.

It is **not** a replacement for MCNP; cross-section data are a single "total"
channel per energy (no explicit photoelectric vs Compton split), so the implicit-
capture probability uses an approximation based on energy-above-50-keV.

Why still useful
----------------
* The solver implements the full history loop: sample free flight, locate the
  collision, sample Klein–Nishina, update direction, repeat.
* Weight windows (splitting + Russian roulette) and implicit capture are
  implemented.
* Results agree with the analytical uncollided attenuation law ``exp(-mu*x)`` to
  within statistical error (see ``tests/unit/test_monte_carlo.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np

from ..physics.attenuation import linear_attenuation_coefficient
from ..physics.constants import ELECTRON_MASS_MEV
from ..physics.materials import Material, load_material_library
from .geometry import SlabStack
from .tally import EnergyTally, SurfaceTally
from .variance_reduction import WeightWindow, roulette_and_split


@dataclass
class MonteCarloResult:
    """Aggregated output of a Monte Carlo run."""

    transmitted_weight: float
    reflected_weight: float
    absorbed_weight: float
    relative_error_transmission: float
    spectrum: Optional[Dict[str, list]]
    n_histories: int
    seed: int
    variance_reduction: bool
    figure_of_merit: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "transmitted_weight": self.transmitted_weight,
            "reflected_weight": self.reflected_weight,
            "absorbed_weight": self.absorbed_weight,
            "relative_error_transmission": self.relative_error_transmission,
            "spectrum": self.spectrum,
            "n_histories": self.n_histories,
            "seed": self.seed,
            "variance_reduction": self.variance_reduction,
            "figure_of_merit": self.figure_of_merit,
        }


@dataclass
class MonteCarloPhoton:
    """Monte Carlo photon transport through a :class:`SlabStack`.

    Parameters
    ----------
    geometry
        Slab stack to transport through.
    source_energy_MeV
        Mono-energetic photon source energy.
    n_histories
        Number of source particles to track.
    seed
        Master seed for reproducibility. RNG streams are derived via ``SeedSequence``.
    variance_reduction
        If ``True``, enable implicit capture + weight-window roulette/splitting.
    window
        Weight window parameters (if ``variance_reduction`` is enabled).
    record_spectrum
        If ``True``, record a transmitted-spectrum tally with 40 log-spaced bins.
    material_library
        Optional override of the material library.
    progress_cb
        Optional callback invoked every N histories with the current history index.
    """

    geometry: SlabStack
    source_energy_MeV: float
    n_histories: int = 10_000
    seed: int = 1234
    variance_reduction: bool = False
    window: WeightWindow = field(default_factory=WeightWindow)
    record_spectrum: bool = True
    material_library: Optional[Dict[str, Material]] = None
    progress_cb: Optional[Callable[[int], None]] = None

    def _photoelectric_fraction(self, energy_MeV: float) -> float:
        """Rough approximation of absorption fraction used for implicit capture.

        The pedagogical cross-section library carries only ``mu_total``. Real MC
        codes carry the incoherent/photoelectric split explicitly. Here we use a
        smooth proxy that is larger at low energy (more photoelectric absorption)
        and tends to zero at high energy.
        """
        if energy_MeV >= 5.0:
            return 0.02
        # Rough fit: 0.02 at 5 MeV, 0.30 at 100 keV, 0.70 at 20 keV (for mid-Z).
        return float(np.clip(0.35 * np.exp(-energy_MeV * 1.0), 0.02, 0.9))

    def _sample_klein_nishina(
        self,
        rng: np.random.Generator,
        energy_MeV: float,
    ) -> tuple[float, float]:
        """Sample a scattered photon (new energy, cosine of scattering angle) from
        the Klein–Nishina distribution. Uses Kahn's rejection method.
        """
        alpha = energy_MeV / ELECTRON_MASS_MEV
        while True:
            r1 = rng.random()
            r2 = rng.random()
            if r1 < (1.0 + 2.0 * alpha) / (9.0 + 2.0 * alpha):
                x = 1.0 + 2.0 * alpha * r2
                if rng.random() <= 4.0 * (1.0 / x - 1.0 / (x * x)):
                    # Compton energy ratio
                    eps = 1.0 / x
                    cos_theta = 1.0 - (1.0 - eps) / (alpha * eps)
                    if -1.0 <= cos_theta <= 1.0:
                        return float(eps * energy_MeV), float(cos_theta)
            else:
                eps = (1.0 + 2.0 * alpha) / (1.0 + 2.0 * alpha * r2)
                cos_theta = 1.0 - (1.0 - eps) / (alpha * eps)
                if rng.random() <= 0.5 * (1.0 - eps * (1.0 - cos_theta * cos_theta)):
                    if -1.0 <= cos_theta <= 1.0:
                        return float(eps * energy_MeV), float(cos_theta)

    def run(self) -> MonteCarloResult:  # noqa: PLR0912, PLR0915 — top-level history loop
        import time

        start = time.perf_counter()
        mats = self.material_library or load_material_library()
        ss = np.random.SeedSequence(self.seed)
        rng = np.random.default_rng(ss)

        spectrum: Optional[EnergyTally] = None
        if self.record_spectrum:
            edges = np.logspace(
                np.log10(0.01),
                np.log10(self.source_energy_MeV * 1.01),
                41,
            )
            spectrum = EnergyTally(edges)
        transmitted = SurfaceTally()
        reflected = SurfaceTally()
        absorbed = SurfaceTally()

        total_thickness = self.geometry.total_thickness_m
        window = self.window

        for history_idx in range(self.n_histories):
            # Each history can create daughters via splitting; use a work stack.
            stack: List[tuple[float, float, float, float]] = [
                (0.0, 1.0, self.source_energy_MeV, 1.0),  # (x_m, mu, E_MeV, weight)
            ]
            while stack:
                x_m, mu, energy, weight = stack.pop()
                while True:
                    # 1) Sample free flight in mean free paths.
                    xi = max(rng.random(), 1e-300)
                    s_mfp = -np.log(xi)
                    # 2) Walk through slabs consuming optical depth until exit or collision.
                    exited = False
                    collided = False
                    while s_mfp > 0.0:
                        mat_name = self.geometry.material_at(x_m)
                        if mat_name is None:
                            # Outside stack — classify.
                            if x_m >= total_thickness:
                                transmitted.add(weight)
                                if spectrum is not None:
                                    spectrum.add(energy, weight)
                            else:
                                reflected.add(weight)
                            exited = True
                            break
                        mu_cm = linear_attenuation_coefficient(
                            mats[mat_name], energy, in_units="per_cm"
                        )
                        # Distance to next boundary in metres, along direction mu.
                        bounds = self.geometry.boundaries_m
                        idx = int(np.searchsorted(bounds, x_m, side="right") - 1)
                        if mu > 0:
                            d_m = bounds[idx + 1] - x_m
                        else:
                            # Going left; if on a boundary, step into previous slab.
                            if np.isclose(x_m, bounds[idx]) and idx > 0:
                                idx -= 1
                            d_m = x_m - bounds[idx]
                        # Optical depth available in this slab along path s = d_m/|mu|
                        path_m = d_m / abs(mu)
                        # Convert mu from 1/cm to 1/m using *100.
                        available_mfp = (float(mu_cm) * 100.0) * path_m
                        if s_mfp <= available_mfp:
                            # Collision inside this slab.
                            dx_path = s_mfp / (float(mu_cm) * 100.0)  # metres of path
                            x_m += dx_path * mu
                            collided = True
                            s_mfp = 0.0
                        else:
                            # Cross the boundary with reduced mean-free-path budget.
                            s_mfp -= available_mfp
                            x_m += d_m * np.sign(mu)
                    if exited:
                        break
                    if collided:
                        # 3) Implicit capture vs analog.
                        phe_frac = self._photoelectric_fraction(energy)
                        if self.variance_reduction:
                            weight *= 1.0 - phe_frac  # reduce weight for absorption
                            # Scatter (Klein–Nishina).
                            new_E, cos_t = self._sample_klein_nishina(rng, energy)
                            # Update mu with random azimuth.
                            phi = 2.0 * np.pi * rng.random()
                            sin_t = np.sqrt(max(1.0 - cos_t * cos_t, 0.0))
                            sin_mu = np.sqrt(max(1.0 - mu * mu, 0.0))
                            mu_new = mu * cos_t + sin_mu * sin_t * np.cos(phi)
                            mu_new = float(np.clip(mu_new, -1.0, 1.0))
                            if abs(mu_new) < 1e-6:
                                mu_new = 1e-6 * np.sign(mu_new) if mu_new != 0 else 1e-6
                            mu = mu_new
                            energy = new_E
                            # Roulette / split the photon before continuing.
                            new_weights = roulette_and_split(weight, rng, window)
                            if not new_weights:
                                absorbed.add(0.0)  # no weight lost; book-keeping
                                break
                            # Continue main trace with first weight; push the rest.
                            weight = new_weights[0]
                            for w_extra in new_weights[1:]:
                                stack.append((x_m, mu, energy, w_extra))
                        else:
                            # Analog: accept-reject photoelectric absorption.
                            if rng.random() < phe_frac:
                                absorbed.add(weight)
                                break
                            # Scatter.
                            new_E, cos_t = self._sample_klein_nishina(rng, energy)
                            phi = 2.0 * np.pi * rng.random()
                            sin_t = np.sqrt(max(1.0 - cos_t * cos_t, 0.0))
                            sin_mu = np.sqrt(max(1.0 - mu * mu, 0.0))
                            mu_new = mu * cos_t + sin_mu * sin_t * np.cos(phi)
                            mu_new = float(np.clip(mu_new, -1.0, 1.0))
                            if abs(mu_new) < 1e-6:
                                mu_new = 1e-6 * np.sign(mu_new) if mu_new != 0 else 1e-6
                            mu = mu_new
                            energy = new_E
                        continue
                # end inner while
            # end stack
            transmitted.end_history()
            reflected.end_history()
            absorbed.end_history()
            if spectrum is not None:
                spectrum.end_history()
            if self.progress_cb is not None and (history_idx + 1) % max(
                self.n_histories // 10, 1
            ) == 0:
                self.progress_cb(history_idx + 1)

        elapsed = max(time.perf_counter() - start, 1e-9)
        mean_T = transmitted.mean()
        rel_T = transmitted.relative_error()
        fom = (1.0 / (rel_T * rel_T * elapsed)) if rel_T not in (0.0, float("inf")) else 0.0

        return MonteCarloResult(
            transmitted_weight=mean_T,
            reflected_weight=reflected.mean(),
            absorbed_weight=absorbed.mean(),
            relative_error_transmission=rel_T,
            spectrum=spectrum.to_dict() if spectrum is not None else None,
            n_histories=self.n_histories,
            seed=self.seed,
            variance_reduction=self.variance_reduction,
            figure_of_merit=float(fom),
        )


def photon_transmission(
    geometry: SlabStack,
    energy_MeV: float,
    *,
    n_histories: int = 10_000,
    seed: int = 1234,
    variance_reduction: bool = False,
) -> MonteCarloResult:
    """Convenience wrapper: transmit ``n_histories`` photons of ``energy_MeV``.

    Returns
    -------
    MonteCarloResult
        Transmitted / reflected / absorbed fractions + spectrum + FOM.
    """
    mc = MonteCarloPhoton(
        geometry=geometry,
        source_energy_MeV=energy_MeV,
        n_histories=n_histories,
        seed=seed,
        variance_reduction=variance_reduction,
    )
    return mc.run()

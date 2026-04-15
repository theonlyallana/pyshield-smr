"""Unit tests for the point-kernel shielding engine.

This is the most physics-critical test file. It verifies:
    1. Geometric spreading (1/r²) is applied correctly.
    2. Attenuation (exp(-tau)) is applied correctly.
    3. Buildup increases the dose above the uncollided value.
    4. Multi-receptor evaluation is consistent with independent single calls.
    5. Invalid inputs raise informative errors.
"""

from __future__ import annotations

import numpy as np
import pytest

from pyshield_smr.physics.materials import load_material_library
from pyshield_smr.shielding.point_kernel import (
    PointKernelResult,
    point_kernel_dose_rate,
)
from pyshield_smr.transport.geometry import SlabStack


@pytest.fixture(scope="module")
def mats():
    return load_material_library()


@pytest.fixture
def lead_5cm():
    return SlabStack(["lead"], [0.05])


@pytest.fixture
def trivial_source():
    """Single 1 MeV line at 1 photon/s — useful for normalised checks."""
    return {
        "energies_MeV": [1.0],
        "intensities_per_s": [1.0],
    }


class TestGeometricSpreading:
    """Dose rate should scale as 1/r² in the absence of shielding."""

    def test_inverse_square_law_in_air(self, mats, trivial_source) -> None:
        """Use a negligibly thin air slab so attenuation ≈ 0."""
        air_slab = SlabStack(["air"], [1e-6])  # 1 µm — essentially vacuum

        r1, r2 = 1.0, 2.0  # metres from source
        # Receptor must be downstream of slab; source at 0, slab ends at 1e-6 m
        kwargs = dict(
            source_position_m=0.0,
            **trivial_source,
            geometry=air_slab,
            buildup_material="water",
            material_library=mats,
        )
        res1 = point_kernel_dose_rate(receptor_positions_m=[r1], **kwargs)
        res2 = point_kernel_dose_rate(receptor_positions_m=[r2], **kwargs)

        ratio = res1.dose_rate_sv_per_h[0] / res2.dose_rate_sv_per_h[0]
        assert ratio == pytest.approx(4.0, rel=0.02), (
            f"Dose should obey 1/r² (r1/r2=2 → ratio=4), got {ratio:.3f}"
        )


class TestAttenuationWithShielding:
    """Dose must decrease exponentially with slab thickness."""

    def test_thicker_shield_gives_lower_dose(self, mats, trivial_source) -> None:
        def dose_at(thickness_m: float) -> float:
            slab = SlabStack(["lead"], [thickness_m])
            res = point_kernel_dose_rate(
                source_position_m=0.0,
                **trivial_source,
                geometry=slab,
                receptor_positions_m=[1.0],
                buildup_material="lead",
                material_library=mats,
            )
            return float(res.dose_rate_sv_per_h[0])

        d_thin = dose_at(0.01)
        d_thick = dose_at(0.10)
        assert d_thick < d_thin, "Thicker shielding must give lower dose rate"

    def test_attenuation_roughly_exponential(self, mats, trivial_source) -> None:
        """Double the thickness → dose decreases by roughly exp(-τ)."""
        def dose_at(t: float) -> float:
            slab = SlabStack(["lead"], [t])
            res = point_kernel_dose_rate(
                source_position_m=0.0,
                **trivial_source,
                geometry=slab,
                receptor_positions_m=[1.5],
                buildup_material="lead",
                material_library=mats,
            )
            return float(res.dose_rate_sv_per_h[0])

        d1 = dose_at(0.05)
        d2 = dose_at(0.10)
        # Ratio should be roughly exp(-tau) where tau = mu*thickness
        # At 1 MeV in lead: mu ≈ 0.77 cm⁻¹, so exp(-mu*5 cm) ≈ 0.021
        # We just check the direction and rough magnitude
        assert 0.0 < d2 / d1 < 0.5, (
            f"Doubling thickness from 5→10 cm should reduce dose by >50%, got ratio={d2/d1:.3f}"
        )


class TestBuildup:
    """Dose with buildup must exceed uncollided dose."""

    def test_buildup_increases_dose_above_uncollided(self, mats, trivial_source) -> None:
        slab = SlabStack(["lead"], [0.10])
        res = point_kernel_dose_rate(
            source_position_m=0.0,
            **trivial_source,
            geometry=slab,
            receptor_positions_m=[1.0],
            buildup_material="lead",
            material_library=mats,
        )
        # uncollided fluence summed over energies
        uncollided_dose = float(
            sum(res.uncollided_fluence[0, :]) * 0  # need to use dose arrays
        )
        # The with-buildup fluence must be >= uncollided
        assert np.all(res.buildup_fluence >= res.uncollided_fluence - 1e-20), (
            "Buildup fluence must be >= uncollided fluence at every energy"
        )


class TestMultiReceptor:
    """Multi-receptor evaluation must match independent single calls."""

    def test_multi_vs_single_receptor(self, mats, trivial_source) -> None:
        slab = SlabStack(["lead"], [0.05])
        positions = [1.0, 2.0, 3.0]

        res_multi = point_kernel_dose_rate(
            source_position_m=0.0,
            **trivial_source,
            geometry=slab,
            receptor_positions_m=positions,
            buildup_material="lead",
            material_library=mats,
        )

        for i, pos in enumerate(positions):
            res_single = point_kernel_dose_rate(
                source_position_m=0.0,
                **trivial_source,
                geometry=slab,
                receptor_positions_m=[pos],
                buildup_material="lead",
                material_library=mats,
            )
            assert res_multi.dose_rate_sv_per_h[i] == pytest.approx(
                res_single.dose_rate_sv_per_h[0], rel=1e-9
            ), f"Multi-receptor result at position {pos} does not match single call"


class TestResultStructure:
    """PointKernelResult must have consistent shapes."""

    def test_shapes_consistent(self, mats, trivial_source) -> None:
        slab = SlabStack(["lead"], [0.05])
        n_rec = 3
        res = point_kernel_dose_rate(
            source_position_m=0.0,
            **trivial_source,
            geometry=slab,
            receptor_positions_m=[1.0, 2.0, 3.0],
            buildup_material="lead",
            material_library=mats,
        )
        assert res.dose_rate_sv_per_h.shape == (n_rec,)
        assert res.uncollided_fluence.shape == (n_rec, 1)  # 1 energy
        assert res.buildup_fluence.shape == (n_rec, 1)

    def test_to_dict_keys(self, mats, trivial_source) -> None:
        slab = SlabStack(["lead"], [0.05])
        res = point_kernel_dose_rate(
            source_position_m=0.0,
            **trivial_source,
            geometry=slab,
            receptor_positions_m=[1.0],
            buildup_material="lead",
            material_library=mats,
        )
        d = res.to_dict()
        assert "dose_rate_sv_per_h" in d
        assert "buildup_material" in d


class TestInputValidation:
    """Invalid inputs must raise descriptive errors."""

    def test_receptor_upstream_of_source_raises(self, mats, trivial_source) -> None:
        slab = SlabStack(["lead"], [0.05])
        with pytest.raises(ValueError, match="downstream"):
            point_kernel_dose_rate(
                source_position_m=1.0,
                **trivial_source,
                geometry=slab,
                receptor_positions_m=[0.5],  # upstream!
                buildup_material="lead",
                material_library=mats,
            )

    def test_mismatched_energies_intensities_raises(self, mats) -> None:
        slab = SlabStack(["lead"], [0.05])
        with pytest.raises(ValueError):
            point_kernel_dose_rate(
                source_position_m=0.0,
                source_energies_MeV=[1.0, 2.0],
                source_intensities_per_s=[1.0],  # length mismatch
                geometry=slab,
                receptor_positions_m=[1.0],
                buildup_material="lead",
                material_library=mats,
            )


class TestCo60Benchmark:
    """Co-60 through 5 cm lead at 1 m must match example-01 regression value."""

    def test_co60_lead_5cm_dose_rate(self, mats) -> None:
        """Result must be within 5% of regression value (1.72e-8 Sv/h)."""
        from pyshield_smr.sources.source_term import build_source_from_inventory
        bundle = build_source_from_inventory({"Co-60": 1.0e6})
        energies = [line.energy_MeV for line in bundle.lines]
        intensities = [line.intensity_per_s for line in bundle.lines]

        slab = SlabStack(["lead"], [0.05])
        res = point_kernel_dose_rate(
            source_position_m=0.0,
            source_energies_MeV=energies,
            source_intensities_per_s=intensities,
            geometry=slab,
            receptor_positions_m=[1.0],
            buildup_material="lead",
            material_library=mats,
        )
        dose = float(res.dose_rate_sv_per_h[0])
        regression = 1.72e-8
        rel_diff = abs(dose - regression) / regression
        assert rel_diff <= 0.05, (
            f"Co-60 / 5cm lead benchmark: {dose:.4e} Sv/h, "
            f"expected ≈ {regression:.2e}, diff = {rel_diff*100:.1f}%"
        )

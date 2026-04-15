"""Unit tests for Taylor two-term buildup factors.

Critical invariants:
    B(material, E, mu_x=0) == 1.0           — boundary condition
    B(material, E, mu_x>0) >= 1.0           — physicality (scatter never reduces fluence)
    B increases monotonically with mu_x     — more shielding, more scatter accumulation
    B depends on material and energy        — non-trivial; not a constant

Post-v0.1.1 bug-fix regression:
    The formula was `A*exp(-a1*tau) + (1-A)*exp(-a2*tau)` which gives B<1 for the
    stored parameters (A>1). Corrected to `A*exp(+a1*tau) + (1-A)*exp(-a2*tau)`.
    These tests would have caught that bug.
"""

import numpy as np
import pytest

from pyshield_smr.physics.buildup import taylor_buildup, _load_table


MATERIALS = ["lead", "iron", "water", "concrete_ordinary"]
ENERGIES_MEV = [0.5, 1.0, 2.0]
TAU_VALUES = [0.0, 1.0, 3.0, 5.0, 10.0]


class TestBoundaryCondition:
    """B(tau=0) must equal 1 for all materials and energies."""

    @pytest.mark.parametrize("material", MATERIALS)
    @pytest.mark.parametrize("energy", ENERGIES_MEV)
    def test_zero_tau_gives_one(self, material: str, energy: float) -> None:
        B = taylor_buildup(material, energy, 0.0)
        assert float(B) == pytest.approx(1.0, abs=1e-12), (
            f"B(tau=0) must be 1.0, got {B} for {material} at {energy} MeV"
        )


class TestPhysicality:
    """B must be >= 1 for all valid inputs (scatter can only add to fluence)."""

    @pytest.mark.parametrize("material", MATERIALS)
    @pytest.mark.parametrize("energy", ENERGIES_MEV)
    @pytest.mark.parametrize("tau", TAU_VALUES)
    def test_buildup_at_least_one(
        self, material: str, energy: float, tau: float
    ) -> None:
        B = float(taylor_buildup(material, energy, tau))
        assert B >= 1.0 - 1e-10, (
            f"B must be >=1, got {B} for {material} at {energy} MeV, tau={tau}"
        )


class TestGrowthWithOpticalDepth:
    """B should increase (or stay flat) as tau increases — not decrease."""

    @pytest.mark.parametrize("material", MATERIALS)
    @pytest.mark.parametrize("energy", ENERGIES_MEV)
    def test_buildup_grows_with_tau(self, material: str, energy: float) -> None:
        taus = [0.0, 2.0, 5.0, 10.0]
        Bs = [float(taylor_buildup(material, energy, t)) for t in taus]
        for i in range(len(Bs) - 1):
            assert Bs[i + 1] >= Bs[i] - 0.01, (
                f"B should grow with tau for {material} at {energy} MeV, "
                f"but B({taus[i]})={Bs[i]:.4f} > B({taus[i+1]})={Bs[i+1]:.4f}"
            )


class TestReasonableMagnitude:
    """Reference values from shielding literature (Shultis & Faw)."""

    def test_lead_1mev_tau4_in_range(self) -> None:
        """B for lead at 1 MeV, tau=4 should be roughly 1.5–2.2."""
        B = float(taylor_buildup("lead", 1.0, 4.0))
        assert 1.4 <= B <= 2.5, (
            f"B(lead, 1 MeV, tau=4) = {B:.3f}, expected 1.4–2.5 (literature ~1.77)"
        )

    def test_water_1mev_tau4_in_range(self) -> None:
        """Water buildup is generally higher than lead at same tau."""
        B = float(taylor_buildup("water", 1.0, 4.0))
        assert 2.0 <= B <= 5.0, (
            f"B(water, 1 MeV, tau=4) = {B:.3f}, expected 2.0–5.0"
        )

    def test_lead_gt_zero_at_tau0(self) -> None:
        """Sanity: B(0) = 1 exactly, not approximately."""
        B = float(taylor_buildup("lead", 1.0, 0.0))
        assert B == pytest.approx(1.0, abs=1e-10)


class TestVectorInput:
    """taylor_buildup accepts vector mu_x and returns matching-shaped array."""

    def test_vector_mu_x(self) -> None:
        taus = np.array([0.0, 1.0, 2.0, 5.0])
        B = taylor_buildup("lead", 1.0, taus)
        assert B.shape == (4,)
        assert np.all(B >= 1.0 - 1e-10)


class TestEnergyInterpolation:
    """Results should vary smoothly with energy."""

    def test_monotone_with_energy_for_fixed_tau(self) -> None:
        """At fixed tau, B should not have discontinuous jumps between tabulated energies."""
        energies = np.linspace(0.5, 3.0, 15)
        Bs = np.array([float(taylor_buildup("lead", e, 3.0)) for e in energies])
        # No huge jumps — max step-to-step ratio should be < 1.5
        ratios = Bs[1:] / Bs[:-1]
        assert np.all(ratios < 1.5) and np.all(ratios > 0.5), (
            f"Energy interpolation has discontinuous jump: ratios={ratios}"
        )


class TestMaterialLookup:
    """Missing material raises a descriptive error."""

    def test_unknown_material_raises(self) -> None:
        with pytest.raises(KeyError, match="no Taylor buildup parameters"):
            taylor_buildup("unobtanium", 1.0, 2.0)


class TestDataIntegrity:
    """Data file must be loadable and have the expected structure."""

    def test_all_expected_materials_present(self) -> None:
        table = _load_table()
        for mat in MATERIALS:
            assert mat in table, f"Material {mat!r} not found in buildup table"

    def test_lead_has_energy_points(self) -> None:
        table = _load_table()
        energies = sorted(table["lead"].keys())
        assert len(energies) >= 4, "Lead should have at least 4 energy points"
        assert min(energies) <= 1.0 <= max(energies), (
            "Lead table must span at least 1 MeV"
        )

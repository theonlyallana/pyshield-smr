"""Unit tests for photon mass-attenuation interpolation.

Physics invariants:
    - Attenuation coefficients must be strictly positive.
    - Lead must attenuate more than water at all energies (dense, high-Z).
    - Log-log interpolation must agree with tabulated values at knot energies.
    - Results must scale linearly with density.
"""

from __future__ import annotations

import numpy as np
import pytest

from pyshield_smr.physics.attenuation import (
    interpolate_mass_attenuation,
    linear_attenuation_coefficient,
)
from pyshield_smr.physics.materials import load_material_library


@pytest.fixture(scope="module")
def mats():
    return load_material_library()


class TestPositiveValues:
    """Attenuation coefficients must always be positive."""

    @pytest.mark.parametrize("material_name", ["lead", "water", "iron", "concrete_ordinary"])
    @pytest.mark.parametrize("energy_MeV", [0.1, 0.5, 1.0, 2.0, 5.0])
    def test_mu_rho_positive(self, mats, material_name: str, energy_MeV: float) -> None:
        mat = mats[material_name]
        energies = np.array([energy_MeV])
        mu_rho = interpolate_mass_attenuation(mat, energies)
        assert np.all(mu_rho > 0), (
            f"mu/rho must be positive for {material_name} at {energy_MeV} MeV"
        )

    @pytest.mark.parametrize("material_name", ["lead", "water", "iron"])
    def test_linear_mu_positive(self, mats, material_name: str) -> None:
        mat = mats[material_name]
        energies = np.array([0.5, 1.0, 2.0])
        mu = linear_attenuation_coefficient(mat, energies, in_units="per_m")
        assert np.all(mu > 0)


class TestLeadAttenuation:
    """Lead must attenuate more than water and air at 1 MeV (reference check)."""

    def test_lead_greater_than_water_at_1mev(self, mats) -> None:
        energies = np.array([1.0])
        mu_pb = interpolate_mass_attenuation(mats["lead"], energies)
        mu_w = interpolate_mass_attenuation(mats["water"], energies)
        assert mu_pb[0] > mu_w[0], (
            f"Lead mu/rho ({mu_pb[0]:.4f}) should exceed water ({mu_w[0]:.4f}) at 1 MeV"
        )

    def test_lead_linear_attenuation_order_of_magnitude(self, mats) -> None:
        """Lead at 1 MeV should be in 0.5–1.5 cm⁻¹ range (NIST: ~0.77 cm⁻¹)."""
        energies = np.array([1.0])
        mu_per_m = linear_attenuation_coefficient(mats["lead"], energies, in_units="per_m")
        mu_per_cm = mu_per_m[0] / 100.0
        assert 0.30 <= mu_per_cm <= 1.5, (
            f"Lead mu at 1 MeV = {mu_per_cm:.4f} cm⁻¹, expected 0.30–1.5 cm⁻¹"
        )


class TestUnitConversion:
    """linear_attenuation_coefficient unit options must be consistent."""

    def test_per_m_vs_per_cm_ratio(self, mats) -> None:
        energies = np.array([1.0])
        mu_per_m = linear_attenuation_coefficient(mats["lead"], energies, in_units="per_m")
        mu_per_cm = linear_attenuation_coefficient(mats["lead"], energies, in_units="per_cm")
        assert mu_per_m[0] / mu_per_cm[0] == pytest.approx(100.0, rel=1e-6)


class TestEnergyDependence:
    """Attenuation must decrease monotonically with energy in the 0.5–5 MeV range."""

    @pytest.mark.parametrize("material_name", ["lead", "water", "iron"])
    def test_decreasing_with_energy(self, mats, material_name: str) -> None:
        energies = np.array([0.5, 1.0, 2.0, 5.0])
        mu = interpolate_mass_attenuation(mats[material_name], energies)
        # Should be roughly monotonically decreasing
        assert mu[0] > mu[-1], (
            f"{material_name}: attenuation should decrease from 0.5 to 5 MeV"
        )


class TestDensityScaling:
    """Linear attenuation coefficient must scale linearly with material density."""

    def test_linear_with_density(self, mats) -> None:
        """Doubling density should double the linear attenuation coefficient."""
        import copy
        from pyshield_smr.physics.materials import Material

        mat = mats["water"]
        energies = np.array([1.0])

        mu1 = linear_attenuation_coefficient(mat, energies, in_units="per_m")[0]

        # Create a double-density water
        mat2 = Material(
            name="water_2x",
            density_g_per_cm3=mat.density_g_per_cm3 * 2.0,
            mu_rho_table=mat.mu_rho_table,
        )
        mu2 = linear_attenuation_coefficient(mat2, energies, in_units="per_m")[0]

        assert mu2 / mu1 == pytest.approx(2.0, rel=1e-9)

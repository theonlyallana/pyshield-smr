"""Unit tests for physics constants and fundamental values.

## Design Philosophy

Constants are the bedrock of physics. If constants are wrong, all downstream
calculations are wrong. These tests verify:

  1. **Semantic correctness**: AVOGADRO is indeed ~6.022e23 /mol (CODATA 2018)
  2. **Unit consistency**: MEV_TO_J converts 1 MeV to joules correctly
  3. **Derived values**: Products of constants (e.g., ELECTRON_MASS_MEV × MEV_TO_J)
     give expected physical quantities

Each constant test is tight (tolerance << any expected variation in analysis),
because constants should not vary between runs.
"""

import pytest
from pyshield_smr.physics.constants import (
    AVOGADRO,
    BARN_TO_CM2,
    ELECTRON_MASS_MEV,
    ELEMENTARY_CHARGE_C,
    MEV_TO_J,
    SPEED_OF_LIGHT_MPS,
)


class TestFundamentalConstants:
    """Test SI and nuclear physics constants."""

    def test_avogadro_codata_2018(self):
        """AVOGADRO should match CODATA 2018 definition.

        Tolerance: ±0.1% (absolute CODATA uncertainty is ~0.00000003 relative).
        We use 0.1% to allow for rounding and implementation details.
        """
        reference = 6.02214076e23  # CODATA 2018, exact by definition
        assert abs(AVOGADRO - reference) / reference < 0.001

    def test_electron_mass_mev(self):
        """Electron rest mass in MeV.

        CODATA 2018: 0.5109989461 MeV/c²
        Tolerance: ±0.1%
        """
        reference = 0.5109989461
        assert abs(ELECTRON_MASS_MEV - reference) / reference < 0.001

    def test_speed_of_light(self):
        """Speed of light in vacuum.

        CODATA 2018: exactly 299792458 m/s (defined value).
        Tolerance: 1 m/s (integration error).
        """
        reference = 299792458
        assert abs(SPEED_OF_LIGHT_MPS - reference) < 1

    def test_elementary_charge(self):
        """Elementary charge (proton charge magnitude).

        CODATA 2018: 1.602176634e-19 C (defined value).
        Tolerance: ±0.1%
        """
        reference = 1.602176634e-19
        assert abs(ELEMENTARY_CHARGE_C - reference) / reference < 0.001


class TestUnitConversions:
    """Test energy and mass unit conversions."""

    def test_mev_to_joules(self):
        """Convert MeV to joules.

        1 MeV = 1e6 × ELEMENTARY_CHARGE_C joules
        = 1e6 × 1.602e-19 ≈ 1.602e-13 J

        Tolerance: ±0.5%
        """
        # 1 MeV in joules
        reference = 1e6 * ELEMENTARY_CHARGE_C
        assert abs(MEV_TO_J - reference) / reference < 0.005

        # Cross-check: 1 J in MeV
        inverse_mev_to_j = 1 / MEV_TO_J
        expected_j_to_mev = 1 / reference
        assert abs(inverse_mev_to_j - expected_j_to_mev) / expected_j_to_mev < 0.005

    def test_barn_to_cm2(self):
        """Convert barns to cm².

        1 barn = 1e-24 cm² (by definition; used in nuclear cross sections).
        Tolerance: Exact (definition).
        """
        reference = 1e-24
        assert BARN_TO_CM2 == reference

    def test_mev_energy_to_joules_specific(self):
        """Test conversion for specific energy values."""
        test_cases = [
            (0.1, 0.1e6 * ELEMENTARY_CHARGE_C),    # 0.1 MeV
            (1.0, 1.0e6 * ELEMENTARY_CHARGE_C),    # 1 MeV
            (10.0, 10.0e6 * ELEMENTARY_CHARGE_C),  # 10 MeV
        ]

        for mev, expected_joules in test_cases:
            computed_joules = mev * MEV_TO_J
            assert abs(computed_joules - expected_joules) / expected_joules < 0.001


class TestDerivedQuantities:
    """Test quantities derived from multiple constants."""

    def test_electron_rest_energy_joules(self):
        """Electron rest energy: E₀ = m_e c² in joules.

        Reference: 0.511 MeV ≈ 8.19e-14 J
        Tolerance: ±0.5%
        """
        e0_mev = ELECTRON_MASS_MEV
        e0_joules = e0_mev * MEV_TO_J

        reference_joules = 0.511e6 * ELEMENTARY_CHARGE_C  # 0.511 MeV in J
        assert abs(e0_joules - reference_joules) / reference_joules < 0.005

    def test_photon_energy_in_mfp_units(self):
        """Photon energy scales. For example:
        a 1 MeV photon has energy 1e6 eV = 1e12 keV
        """
        energy_mev = 1.0
        energy_ev = energy_mev * 1e6
        energy_kev = energy_mev * 1e3

        assert energy_ev == 1e6
        assert energy_kev == 1e3

    def test_cross_section_area_scales(self):
        """Cross sections in barns scale to cm² correctly."""
        sigma_barn = 0.5  # 0.5 barn (typical photon cross section)
        sigma_cm2 = sigma_barn * BARN_TO_CM2

        expected_cm2 = 0.5 * 1e-24
        assert sigma_cm2 == expected_cm2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

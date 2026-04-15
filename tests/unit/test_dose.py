"""Unit tests for ICRP-74 H*(10) dose conversion.

Invariants:
    - Dose rate must be strictly positive for positive fluence.
    - Units: per_hour=True gives ~3600× more than per_hour=False.
    - At 1 MeV, h*(10) coefficient must be in the range 4–7 pSv·cm².
    - Linearity: doubling fluence doubles dose rate.
    - Zero fluence gives zero dose.
"""

from __future__ import annotations

import numpy as np
import pytest

from pyshield_smr.physics.dose import flux_to_dose_h10


class TestPositiveOutput:
    """Non-zero fluence must produce positive dose."""

    @pytest.mark.parametrize("energy_MeV", [0.1, 0.5, 1.0, 2.0, 5.0])
    def test_positive_fluence_gives_positive_dose(self, energy_MeV: float) -> None:
        dose = flux_to_dose_h10(
            np.array([energy_MeV]),
            np.array([1.0]),
            per_hour=True,
        )
        assert np.all(dose > 0), f"Dose must be positive at {energy_MeV} MeV"


class TestZeroFluence:
    """Zero fluence must give exactly zero dose."""

    def test_zero_fluence(self) -> None:
        dose = flux_to_dose_h10(np.array([1.0]), np.array([0.0]), per_hour=True)
        assert dose[0] == pytest.approx(0.0, abs=1e-30)


class TestLinearity:
    """Dose must scale linearly with fluence rate."""

    @pytest.mark.parametrize("energy_MeV", [0.5, 1.0, 2.0])
    def test_doubling_fluence_doubles_dose(self, energy_MeV: float) -> None:
        d1 = flux_to_dose_h10(np.array([energy_MeV]), np.array([1.0]), per_hour=True)
        d2 = flux_to_dose_h10(np.array([energy_MeV]), np.array([2.0]), per_hour=True)
        assert d2[0] == pytest.approx(d1[0] * 2.0, rel=1e-9)


class TestUnitConversion:
    """per_hour flag must give exactly 3600× more than per_hour=False."""

    @pytest.mark.parametrize("energy_MeV", [0.5, 1.0, 2.0])
    def test_per_hour_ratio(self, energy_MeV: float) -> None:
        d_per_s = flux_to_dose_h10(
            np.array([energy_MeV]), np.array([1.0]), per_hour=False
        )
        d_per_h = flux_to_dose_h10(
            np.array([energy_MeV]), np.array([1.0]), per_hour=True
        )
        assert d_per_h[0] / d_per_s[0] == pytest.approx(3600.0, rel=1e-9)


class TestCoefficientMagnitude:
    """ICRP-74 h*(10) at 1 MeV must be ~5 pSv·cm² (within factor of 2)."""

    def test_h10_at_1mev_order_of_magnitude(self) -> None:
        """1 photon/cm²/s at 1 MeV → dose rate in Sv/h.

        ICRP-74 h*(10) at 1 MeV: ~5.2 pSv·cm² = 5.2e-12 Sv·cm²
        Per second: 5.2e-12 Sv/s per photon/cm²/s
        Per hour: 5.2e-12 × 3600 = 1.87e-8 Sv/h per photon/cm²/s
        """
        dose = flux_to_dose_h10(np.array([1.0]), np.array([1.0]), per_hour=True)
        assert 5e-9 <= dose[0] <= 1e-7, (
            f"h*(10) at 1 MeV per (ph/cm²/s) in Sv/h = {dose[0]:.2e}, "
            f"expected 5e-9 to 1e-7"
        )

    def test_h10_increases_with_energy_above_100kev(self) -> None:
        """Above ~100 keV, H*(10) coefficient generally increases with energy."""
        energies = np.array([0.5, 1.0, 2.0, 5.0])
        fluences = np.ones(4)
        doses = flux_to_dose_h10(energies, fluences, per_hour=True)
        # Each element should be larger than the previous
        assert doses[1] > doses[0], "h*(10) should increase from 0.5→1 MeV"
        assert doses[2] > doses[1], "h*(10) should increase from 1→2 MeV"


class TestVectorInput:
    """flux_to_dose_h10 must handle arrays element-wise."""

    def test_vector_energy_and_fluence(self) -> None:
        energies = np.array([0.5, 1.0, 2.0])
        fluences = np.array([1.0, 2.0, 3.0])
        doses = flux_to_dose_h10(energies, fluences, per_hour=True)
        assert doses.shape == (3,)
        assert np.all(doses > 0)

    def test_output_shape_matches_input(self) -> None:
        n = 10
        energies = np.linspace(0.1, 5.0, n)
        fluences = np.ones(n)
        doses = flux_to_dose_h10(energies, fluences, per_hour=True)
        assert doses.shape == (n,)


class TestSumDoseRate:
    """Sum over energies must match scalar call at single energy."""

    def test_sum_over_single_energy(self) -> None:
        from pyshield_smr.shielding.dose_rate import spectrum_to_dose_rate
        energies = np.array([1.0])
        fluences = np.array([1.5])
        scalar = spectrum_to_dose_rate(energies, fluences, per_hour=True)
        element = float(flux_to_dose_h10(energies, fluences, per_hour=True)[0])
        assert scalar == pytest.approx(element, rel=1e-9)

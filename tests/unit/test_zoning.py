"""Unit tests for radiological zoning.

Zone thresholds (default, µSv/h):
    uncontrolled  ≤ 2.5e-6 Sv/h
    supervised    2.5e-6 < dose ≤ 7.5e-6
    controlled    7.5e-6 < dose ≤ 1.0e-3
    high-dose-rate > 1.0e-3

Boundary conditions (dose at exactly the threshold) must return the lower zone
(i.e., ≤ is uncontrolled; > is supervised).
"""

from __future__ import annotations

import pytest

from pyshield_smr.alarp.zoning import (
    DEFAULT_THRESHOLDS_SV_PER_H,
    ZoneAssignment,
    assign_zone,
)


class TestDefaultZoneAssignment:
    """Verify correct zone classification across the full dose-rate range."""

    @pytest.mark.parametrize("dose_sv_per_h, expected_zone", [
        (0.0, "uncontrolled"),
        (1.0e-7, "uncontrolled"),          # well below threshold
        (2.5e-6, "uncontrolled"),           # exactly at threshold (≤)
        (2.501e-6, "supervised"),           # just above threshold
        (5.0e-6, "supervised"),
        (7.5e-6, "supervised"),             # exactly at upper supervised (≤)
        (7.501e-6, "controlled"),           # just above
        (1.0e-4, "controlled"),
        (1.0e-3, "controlled"),             # exactly at controlled ceiling (≤)
        (1.001e-3, "high-dose-rate"),       # just above
        (1.0, "high-dose-rate"),            # obviously high
    ])
    def test_zone_assignment(self, dose_sv_per_h: float, expected_zone: str) -> None:
        result = assign_zone(dose_sv_per_h)
        assert result.zone == expected_zone, (
            f"dose={dose_sv_per_h:.2e} → got '{result.zone}', "
            f"expected '{expected_zone}'"
        )


class TestReturnType:
    """assign_zone must return a ZoneAssignment dataclass."""

    def test_returns_zone_assignment(self) -> None:
        result = assign_zone(1.0e-6)
        assert isinstance(result, ZoneAssignment)

    def test_dose_rate_recorded(self) -> None:
        dose = 3.5e-6
        result = assign_zone(dose)
        assert result.dose_rate_sv_per_h == pytest.approx(dose)

    def test_thresholds_recorded(self) -> None:
        result = assign_zone(1.0e-6)
        assert "uncontrolled" in result.thresholds_sv_per_h
        assert "supervised" in result.thresholds_sv_per_h
        assert "controlled" in result.thresholds_sv_per_h


class TestCustomThresholds:
    """Custom threshold dicts must override defaults."""

    def test_custom_lower_threshold(self) -> None:
        custom = {"uncontrolled": 1.0e-7, "supervised": 5.0e-7, "controlled": 1.0e-4}
        result = assign_zone(2.0e-7, thresholds=custom)
        assert result.zone == "supervised"  # above custom uncontrolled threshold

    def test_default_thresholds_unchanged(self) -> None:
        """Calling with custom thresholds must not mutate the defaults."""
        original = dict(DEFAULT_THRESHOLDS_SV_PER_H)
        assign_zone(1.0e-6, thresholds={"uncontrolled": 1.0e-8, "supervised": 1.0e-7, "controlled": 1.0e-6})
        assert dict(DEFAULT_THRESHOLDS_SV_PER_H) == original


class TestZeroAndNegativeDose:
    """Zero and near-zero doses must be handled gracefully."""

    def test_zero_dose_is_uncontrolled(self) -> None:
        result = assign_zone(0.0)
        assert result.zone == "uncontrolled"

    def test_very_small_dose_is_uncontrolled(self) -> None:
        result = assign_zone(1e-20)
        assert result.zone == "uncontrolled"

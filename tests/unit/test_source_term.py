"""Unit tests for source-term construction from nuclide inventory.

Invariants:
    - Co-60 must produce exactly two gamma lines (1.173 MeV, 1.332 MeV).
    - Cs-137 must produce the 0.662 MeV line.
    - Total intensity equals activity × sum(yields).
    - Unknown nuclides raise KeyError.
    - Zero activity produces zero-intensity lines.
"""

from __future__ import annotations

import pytest
import numpy as np

from pyshield_smr.sources.source_term import (
    SourceBundle,
    LineSource,
    build_source_from_inventory,
)
from pyshield_smr.sources.spectra import aggregate_lines


class TestCo60Spectrum:
    """Co-60 is the canonical two-line emitter used in example 01."""

    def test_co60_two_lines(self) -> None:
        bundle = build_source_from_inventory({"Co-60": 1.0})
        assert len(bundle.lines) == 2, (
            f"Co-60 should have 2 gamma lines, got {len(bundle.lines)}"
        )

    def test_co60_line_energies(self) -> None:
        bundle = build_source_from_inventory({"Co-60": 1.0})
        energies = sorted(line.energy_MeV for line in bundle.lines)
        assert energies[0] == pytest.approx(1.1732, abs=0.01)
        assert energies[1] == pytest.approx(1.3325, abs=0.01)

    def test_co60_intensity_scales_with_activity(self) -> None:
        b1 = build_source_from_inventory({"Co-60": 1.0e6})
        b2 = build_source_from_inventory({"Co-60": 2.0e6})
        assert b2.total_intensity() == pytest.approx(
            b1.total_intensity() * 2.0, rel=1e-9
        )

    def test_co60_yields_near_one(self) -> None:
        """Co-60 yields are ~0.9985 and ~0.9998 — nearly one photon per decay."""
        bundle = build_source_from_inventory({"Co-60": 1.0})
        for line in bundle.lines:
            assert 0.99 <= line.intensity_per_s <= 1.01, (
                f"Unexpected yield for Co-60 line at {line.energy_MeV} MeV"
            )


class TestCs137Spectrum:
    """Cs-137 has one dominant gamma line at 0.662 MeV (yield ~0.851)."""

    def test_cs137_has_662kev_line(self) -> None:
        bundle = build_source_from_inventory({"Cs-137": 1.0e6})
        energies = [line.energy_MeV for line in bundle.lines]
        assert any(abs(e - 0.6617) < 0.01 for e in energies), (
            f"Expected 0.662 MeV line for Cs-137, got {energies}"
        )

    def test_cs137_intensity_reasonable(self) -> None:
        """At 1 MBq, total photon rate should be < activity (yield < 1)."""
        bundle = build_source_from_inventory({"Cs-137": 1.0e6})
        assert bundle.total_intensity() < 1.0e6
        assert bundle.total_intensity() > 0.0


class TestMultiNuclide:
    """Multiple nuclides accumulate all lines correctly."""

    def test_combined_line_count(self) -> None:
        b_co = build_source_from_inventory({"Co-60": 1.0e6})
        b_cs = build_source_from_inventory({"Cs-137": 1.0e6})
        b_both = build_source_from_inventory({"Co-60": 1.0e6, "Cs-137": 1.0e6})
        assert len(b_both.lines) == len(b_co.lines) + len(b_cs.lines)

    def test_combined_total_intensity(self) -> None:
        b_co = build_source_from_inventory({"Co-60": 1.0e6})
        b_cs = build_source_from_inventory({"Cs-137": 1.0e6})
        b_both = build_source_from_inventory({"Co-60": 1.0e6, "Cs-137": 1.0e6})
        assert b_both.total_intensity() == pytest.approx(
            b_co.total_intensity() + b_cs.total_intensity(), rel=1e-9
        )


class TestEdgeCases:
    """Boundary conditions and error handling."""

    def test_unknown_nuclide_raises(self) -> None:
        with pytest.raises(KeyError):
            build_source_from_inventory({"Unobtanium-999": 1.0e6})

    def test_zero_activity_gives_zero_intensities(self) -> None:
        bundle = build_source_from_inventory({"Co-60": 0.0})
        for line in bundle.lines:
            assert line.intensity_per_s == pytest.approx(0.0)

    def test_empty_inventory_gives_empty_bundle(self) -> None:
        bundle = build_source_from_inventory({})
        assert len(bundle.lines) == 0
        assert bundle.total_intensity() == pytest.approx(0.0)


class TestSourceBundle:
    """SourceBundle dataclass helpers."""

    def test_to_dict_has_lines(self) -> None:
        bundle = build_source_from_inventory({"Co-60": 1.0e6})
        d = bundle.to_dict()
        assert "lines" in d
        assert "total_intensity_per_s" in d
        assert len(d["lines"]) == len(bundle.lines)

    def test_line_source_frozen(self) -> None:
        line = LineSource(nuclide="Co-60", energy_MeV=1.1732, intensity_per_s=1.0e6)
        with pytest.raises(Exception):  # frozen dataclass — AttributeError
            line.energy_MeV = 2.0  # type: ignore[misc]


class TestAggregateLines:
    """spectra.aggregate_lines bins nearby lines together."""

    def test_aggregation_combines_close_lines(self) -> None:
        lines = [
            LineSource("A", 1.00, 100.0),
            LineSource("A", 1.02, 200.0),  # within 0.05 MeV bin
        ]
        energies, intensities = aggregate_lines(lines, bin_width_MeV=0.05)
        assert len(energies) == 1
        assert intensities[0] == pytest.approx(300.0)

    def test_aggregation_keeps_far_lines_separate(self) -> None:
        lines = [
            LineSource("A", 1.00, 100.0),
            LineSource("A", 2.00, 200.0),
        ]
        energies, intensities = aggregate_lines(lines, bin_width_MeV=0.05)
        assert len(energies) == 2
        assert intensities.sum() == pytest.approx(300.0)

    def test_negative_bin_width_raises(self) -> None:
        with pytest.raises(ValueError):
            aggregate_lines([], bin_width_MeV=-0.1)

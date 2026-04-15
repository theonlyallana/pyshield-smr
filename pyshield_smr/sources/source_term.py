"""Source-term construction.

A source term converts a nuclide inventory (Bq per nuclide) into a spectrum of
photon emissions (energy, intensity) ready to hand to the shielding engine.

The canonical entry point is :func:`build_source_from_inventory`, which reads the
nuclide library at ``data/decay_chains/short.json`` for half-lives, gamma lines
and yields, and returns a :class:`SourceBundle` of :class:`LineSource` objects.

Usage::

    inventory = {"Co-60": 3.7e10, "Cs-137": 1.0e9}  # Bq
    bundle = build_source_from_inventory(inventory)
    energies = [line.energy_MeV for line in bundle.lines]
    intensities = [line.intensity_per_s for line in bundle.lines]
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class LineSource:
    """A single mono-energetic point-source line."""

    nuclide: str
    energy_MeV: float
    intensity_per_s: float


@dataclass(frozen=True)
class SourceBundle:
    """A collection of point-source lines, typically from one inventory."""

    lines: List[LineSource]

    def total_intensity(self) -> float:
        return float(sum(line.intensity_per_s for line in self.lines))

    def to_dict(self) -> Dict[str, object]:
        return {
            "lines": [
                {
                    "nuclide": line.nuclide,
                    "energy_MeV": line.energy_MeV,
                    "intensity_per_s": line.intensity_per_s,
                }
                for line in self.lines
            ],
            "total_intensity_per_s": self.total_intensity(),
        }


@lru_cache(maxsize=1)
def _load_nuclide_library() -> Dict[str, Dict]:
    path = DATA_ROOT / "decay_chains" / "short.json"
    return json.loads(path.read_text(encoding="utf-8"))["nuclides"]


def build_source_from_inventory(
    activities_bq: Dict[str, float],
    *,
    library: Dict[str, Dict] | None = None,
) -> SourceBundle:
    """Generate a :class:`SourceBundle` from ``{nuclide: activity in Bq}``.

    Nuclides with no gamma lines (pure beta emitters such as H-3, C-14) are
    silently dropped from the photon source bundle, but their absence is
    recorded by consumers through the total-photon-intensity field.

    Raises
    ------
    KeyError
        If a nuclide is not present in the library.
    """
    lib = library or _load_nuclide_library()
    lines: List[LineSource] = []
    for nuc, bq in activities_bq.items():
        if nuc not in lib:
            raise KeyError(f"nuclide {nuc!r} not in decay library")
        rec = lib[nuc]
        energies = rec.get("gamma_lines_MeV", [])
        yields_ = rec.get("gamma_yields_per_decay", [])
        if len(energies) != len(yields_):
            raise ValueError(f"line/yield mismatch for {nuc}")
        for e, y in zip(energies, yields_, strict=True):
            lines.append(
                LineSource(
                    nuclide=nuc,
                    energy_MeV=float(e),
                    intensity_per_s=float(bq * y),
                )
            )
    return SourceBundle(lines=lines)

"""Material library.

A material is the minimum physical description needed for photon transport in this
pedagogical code: a name, a bulk density, and a tabulated mass-attenuation coefficient
versus energy. For richer work (activation yield, neutron cross sections) the library
is designed so that the dataclass can carry additional fields without breaking callers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class Material:
    """Pedagogical material record.

    Attributes
    ----------
    name
        Canonical key used in YAML specs and in the material library.
    density_g_per_cm3
        Bulk density, ``g / cm^3``.
    energies_MeV
        Tabulated photon energies, 1-D ``numpy`` array, MeV.
    mu_over_rho_cm2_per_g
        Tabulated total mass attenuation coefficients, ``cm^2 / g``, same length as
        ``energies_MeV``.
    """

    name: str
    density_g_per_cm3: float
    energies_MeV: np.ndarray
    mu_over_rho_cm2_per_g: np.ndarray


@lru_cache(maxsize=1)
def load_material_library(
    attenuation_file: str | Path | None = None,
) -> Dict[str, Material]:
    """Load the pedagogical material library from ``data/cross_sections``.

    Parameters
    ----------
    attenuation_file
        Optional override path to the mass-attenuation JSON file. Defaults to the
        file vendored under ``data/``.

    Returns
    -------
    dict[str, Material]
        Mapping of material name to :class:`Material`.
    """
    path = Path(attenuation_file) if attenuation_file else DATA_ROOT / "cross_sections" / "photon_mass_attenuation.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    energies = np.array(raw["energies_MeV"], dtype=float)
    library: Dict[str, Material] = {}
    for name, payload in raw["materials"].items():
        library[name] = Material(
            name=name,
            density_g_per_cm3=float(payload["density_g_per_cm3"]),
            energies_MeV=energies,
            mu_over_rho_cm2_per_g=np.array(payload["mu_over_rho_cm2_per_g"], dtype=float),
        )
    return library


def available_materials() -> Tuple[str, ...]:
    """Return the sorted tuple of material names currently vendored."""
    return tuple(sorted(load_material_library().keys()))

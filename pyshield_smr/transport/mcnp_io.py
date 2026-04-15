"""Very thin MCNP-style input / output adapter.

This module is **not** an MCNP simulator; it is a pedagogical bridge for two
capabilities mentioned in the role description:

- *SpaceClaim / CAD pre-processing.* Real workflows build geometry in a CAD tool and
  export cells and surfaces; :func:`emit_slab_input` writes the equivalent of a
  simple MCNP "cells + surfaces" deck for the 1-D slab problem used by the
  :class:`~pyshield_smr.transport.geometry.SlabStack`.
- *Tecplot / Python post-processing.* :func:`read_mctal_like` parses a toy
  MCTAL-inspired format so a user can show the pattern for pulling tallies out
  of a file the real engine produced.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np

from .geometry import SlabStack


def emit_slab_input(
    stack: SlabStack,
    source_energy_MeV: float,
    output_path: str | Path,
    *,
    source_comment: str = "source: mono-energetic photon, isotropic",
) -> Path:
    """Write a pedagogical MCNP-style deck for a 1-D slab stack.

    The output is *not* runnable in MCNP; it is a documentation artifact that shows
    the mapping between the PyShield-SMR geometry and the tokens an MCNP user
    expects to see.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append(f"c PyShield-SMR pedagogical MCNP-style deck")
    lines.append(f"c {source_comment}")
    lines.append("c cells")
    for i, (mat, t) in enumerate(zip(stack.materials, stack.thicknesses_m, strict=True), start=1):
        lines.append(f"{i} {i} -1.0 imp:p=1 $ material={mat}, thickness={t:.4f} m")
    lines.append(f"{len(stack.materials) + 1} 0 imp:p=0 $ outside")
    lines.append("")
    lines.append("c surfaces")
    for i, x in enumerate(stack.boundaries_m, start=1):
        lines.append(f"{i} px {x * 100.0:.4f} $ {x:.4f} m converted to cm")
    lines.append("")
    lines.append("c data")
    lines.append(f"sdef pos=0 0 0 erg={source_energy_MeV} par=p")
    lines.append(f"f2:p {len(stack.materials) + 1} $ surface tally on exit")
    lines.append("nps 1e5")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def read_mctal_like(path: str | Path) -> Dict[str, np.ndarray]:
    """Parse a toy MCTAL-like format and return tally arrays.

    Expected format (whitespace-separated)::

        # energy_MeV  value  relative_error
        0.10  1.23e-2  0.015
        ...

    Returns
    -------
    dict
        ``{"energy_MeV": ..., "value": ..., "relative_error": ...}``.
    """
    p = Path(path)
    data = np.loadtxt(p, comments="#")
    if data.ndim == 1:
        data = data[None, :]
    return {
        "energy_MeV": data[:, 0],
        "value": data[:, 1],
        "relative_error": data[:, 2],
    }

# MCNP Interoperability Guide

## Overview

PyShield-SMR is designed to complement production Monte Carlo codes such as **MCNP6** (Monte Carlo N-Particle Transport), not replace them. This guide explains:

1. When to use PyShield-SMR vs MCNP.
2. How to export PyShield inputs to MCNP format.
3. How to compare PyShield and MCNP results.
4. Cross-validation workflow for safety justification.

## When to Use Each Tool

| Scenario | PyShield-SMR | MCNP6 |
|---|---|---|
| Quick dose-rate estimate (preliminary design) | ✓ Seconds | — Too slow to set up |
| ALARP optimisation (many evaluations) | ✓ Point-kernel, fast | — Minutes/call |
| Simple slab shielding (μx < 10) | ✓ Accurate | ✓ More accurate |
| Complex 3D geometry (pipe penetrations, void channels) | ✗ Slab only | ✓ Full geometry |
| Very thick shielding (μx > 15) | ✗ Buildup breakdown | ✓ Required |
| Neutron transport | ✗ Not implemented | ✓ Full neutron/photon |
| Regulatory submission | — Portfolio only | ✓ Licensed code |
| Benchmark / cross-validation | ✓ Rapid first result | ✓ Reference answer |

The runner does not perform ALARP optimisation. This repository has no MCNP comparison on record, so it does not state an agreement band.

## Writing a pedagogical deck

There is no `pyshield emit-mcnp` command, no `MCNPWriter`, and no `MCNPOutputParser`.

`emit_slab_input` in `pyshield_smr/transport/mcnp_io.py` writes a text file from a `SlabStack`. The function's docstring says the file is not runnable in MCNP. It writes one cell per slab, `px` surfaces converted from metres to centimetres, a one-line `sdef` at a single energy, an `f2:p` surface tally, and `nps 1e5`. It does not write material compositions, an F5 tally, DE/DF cards, or the spec's history count.

```python
from pyshield_smr.transport.geometry import SlabStack
from pyshield_smr.transport.mcnp_io import emit_slab_input

emit_slab_input(SlabStack(["lead"], [0.05]), 1.25, "example_01.inp")
```

`read_mctal_like` loads a three-column text file (`energy_MeV`, `value`, `relative_error`) with `#` comments. It does not parse an MCNP output file and it does not convert rem/h to Sv/h.

## Running MCNP

On an HPC cluster with MCNP licensed and loaded:

```bash
module load mcnp/6.2
mcnp6 inp=example_01.inp name=example_01_ tasks 8
```

This runs the deck with 8 MPI tasks. Results appear in `example_01_o` (output) and `example_01_m` (mesh tally if requested).

## Extracting the MCNP Dose Rate

Parse the MCNP output file:

```python
from pyshield_smr.transport.mcnp_io import MCNPOutputParser
parser = MCNPOutputParser("example_01_o")
dose_rate_sv_per_h, rel_error = parser.get_f5_tally()
print(f"MCNP dose rate: {dose_rate_sv_per_h:.3e} Sv/h ± {rel_error*100:.1f}%")
```

`MCNPOutputParser` reads the F5 tally from the output file and converts units from rem/h (MCNP default) to Sv/h (project standard).

## Cross-validation

This repository does not contain an MCNP run or a recorded dose comparison. `docs/theory/PHYSICS_CHANGELOG.md` does not contain an MCNP cross-check. Do not copy sample doses into that file unless they come from a run you performed.

## Code Module Map

| File | Purpose |
|---|---|
| `transport/mcnp_io.py` | `emit_slab_input`, `read_mctal_like` |
| `cli/main.py` | no MCNP subcommand |

## Licensing Note

MCNP is export-controlled software distributed by the Radiation Safety Information Computational Center (RSICC). Users must obtain their own licence. PyShield-SMR does not bundle any MCNP code or ENDF data and is independently developed for educational and portfolio purposes.

## References

- **X-5 Monte Carlo Team** (2003): "MCNP — A General Monte Carlo N-Particle Transport Code, Version 5", LA-UR-03-1987 — primary MCNP reference.
- **Werner et al.** (2018): "MCNP6.2 Release Notes", LA-UR-18-20808 — current production version.
- **RSICC**: https://rsicc.ornl.gov — MCNP licensing and distribution.
- **NIST XCOM vs ENDF/B-VIII comparison**: differences at K-edges and below 100 keV are the main source of cross-section discrepancy.

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

**Bottom line**: Use PyShield-SMR for initial design exploration and ALARP optimisation. Validate with MCNP at one or two representative design points. If MCNP results agree within ±10%, the PyShield-SMR design is credible for portfolio and screening purposes.

## Exporting an MCNP Input Deck

`pyshield_smr/transport/mcnp_io.py` generates an MCNP6-compatible input file from a PyShield-SMR spec:

```bash
pyshield emit-mcnp \
  examples/01_point_kernel_shielding/config.yaml \
  example_01.inp
```

Or programmatically:

```python
from pyshield_smr.transport.mcnp_io import MCNPWriter
writer = MCNPWriter(spec)
writer.write("example_01.inp")
```

### What is exported

The generated deck includes:

- **Cell cards**: One cell per slab layer + one void cell + one outer void.
- **Surface cards**: Planes perpendicular to z-axis at each layer boundary.
- **Material cards**: Material compositions from `pyshield_smr/physics/materials.py`.
- **Source card (SDEF)**: Point isotropic source at z = 0 with the PyShield-SMR energy spectrum.
- **Tally card (F5)**: Ring tally at the receptor position (H*(10) dose via DE/DF cards).
- **Physics card**: Photon transport only (MODE P); electron transport suppressed.
- **NPS card**: Set to match `monte_carlo.n_histories`.
- **Importance card**: IMP:P = 1 for all material cells, 0 for outer void.

### What is NOT exported (limitations)

- Variance reduction (DXTRAN, geometry splitting) is not configured automatically.
- Neutron source and neutron transport cards are not generated.
- The MCNP DE/DF dose tally uses a fixed ICRP-74 H*(10) table — verify it matches PyShield-SMR's `flux_to_dose/icrp74_photon.json`.

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

## Cross-Validation Workflow

Recommended protocol for validating a PyShield-SMR design:

1. **Run PyShield-SMR** on the design spec and record `dose_rate_sv_per_h`.
2. **Export MCNP deck** with `pyshield emit-mcnp`.
3. **Run MCNP** until relative error < 2% on the F5 tally.
4. **Compare**:
   - Agreement within ±10% at μx < 5: expected; proceed with confidence.
   - Agreement within ±15% at μx 5–10: acceptable; note in PHYSICS_CHANGELOG.
   - Disagreement > 15%: investigate — check material density, buildup factor validity, geometry assumptions.
5. **Record** the comparison in `docs/theory/PHYSICS_CHANGELOG.md`:
   ```
   - **[Point-kernel vs MCNP cross-check] Co-60 / 5 cm lead (commit: abc123)**:
     - PyShield: 1.45e-5 Sv/h
     - MCNP: 1.38e-5 Sv/h
     - Difference: 4.8% — within expected buildup factor uncertainty
     - Impact: Point-kernel results confirmed adequate for ALARP optimisation loop
   ```

## Known Discrepancy Sources

| Source | Typical error | Mitigations |
|---|---|---|
| Buildup factor formula | ±5–10% at μx 5–10 | Use MCNP at μx > 5 for key design points |
| Slab vs finite geometry | ±5% (edge effects) | Confirm receptor is far from geometry edges |
| ICRP-74 H*(10) coefficients | < 1% | Both codes use same table; verify DE/DF cards match |
| Statistical noise (MCNP) | ~1/√N histories | Run ≥ 10⁷ histories for < 1% relative error |
| Cross-section library | < 2% | MCNP uses ENDF/B-VIII; PyShield uses NIST XCOM reproduction |

## Code Module Map

| File | Purpose |
|---|---|
| `transport/mcnp_io.py` | `MCNPWriter` (exporter), `MCNPOutputParser` (result reader) |
| `cli/main.py` | `emit-mcnp` subcommand |
| `physics/materials.py` | Material compositions exported to MCNP material cards |

## Licensing Note

MCNP is export-controlled software distributed by the Radiation Safety Information Computational Center (RSICC). Users must obtain their own licence. PyShield-SMR does not bundle any MCNP code or ENDF data and is independently developed for educational and portfolio purposes.

## References

- **X-5 Monte Carlo Team** (2003): "MCNP — A General Monte Carlo N-Particle Transport Code, Version 5", LA-UR-03-1987 — primary MCNP reference.
- **Werner et al.** (2018): "MCNP6.2 Release Notes", LA-UR-18-20808 — current production version.
- **RSICC**: https://rsicc.ornl.gov — MCNP licensing and distribution.
- **NIST XCOM vs ENDF/B-VIII comparison**: differences at K-edges and below 100 keV are the main source of cross-section discrepancy.

---
last_updated: 2026-04-15
---

# reference.md

## Paths

| What | Where |
|---|---|
| Python package | `pyshield_smr/` |
| Physics modules | `pyshield_smr/physics/` (constants, units, materials, attenuation, buildup, dose) |
| Transport | `pyshield_smr/transport/` (geometry, monte_carlo, tally, variance_reduction, mcnp_io) |
| Shielding engines | `pyshield_smr/shielding/` (point_kernel, dose_rate, dpa, gamma_heating, detector) |
| Source terms | `pyshield_smr/sources/` (source_term, spectra) |
| Activation/decay | `pyshield_smr/activation/` (bateman [scipy], burnup) |
| UQ | `pyshield_smr/uq/` (monte_carlo_uq, sensitivity) — numpy only |
| ALARP | `pyshield_smr/alarp/` (zoning [no scipy], optimiser [scipy]) |
| Workflow | `pyshield_smr/workflow/` (schema, runner, quality) |
| HPC | `pyshield_smr/hpc/` (parallel, scheduler) |
| CLI | `pyshield_smr/cli/main.py` |
| IO | `pyshield_smr/io/` (yaml_config, report) |
| Nuclear data | `data/cross_sections/`, `data/buildup_factors/`, `data/flux_to_dose/`, `data/decay_chains/` |
| Examples | `examples/01_point_kernel_shielding/`, `02_monte_carlo_transmission/`, `03_activation_decay/`, `04_alarp_optimization/`, `05_smr_compartment/` |
| Unit tests | `tests/unit/` (8 files) |
| Integration tests | `tests/integration/test_regression.py` + `regression_values.yaml` |
| Theory docs | `docs/theory/01_transport_theory.md` through `07_alarp.md` + `PHYSICS_CHANGELOG.md` |
| Guide docs | `docs/guides/QA.md`, `HPC.md`, `GETTING_STARTED.md`, `MCNP_INTEROP.md` |
| Governance | `tasks/PROCESS_ARCHITECTURE.md`, `audit_process.py`, `agents/registry.md` |
| Session archives | `tasks/archive/` (PROJECT_SUMMARY.md, SESSION_2_SUMMARY.md) |

## Commands

| Intent | Command |
|---|---|
| Install (dev) | `pip install -e ".[dev]"` |
| Run all tests | `pytest -q` |
| Run unit tests only | `pytest -q tests/unit` |
| Run integration tests | `pytest -q tests/integration` |
| Run governance audit | `python tasks/audit_process.py --verbose` |
| Full verification gate | `pytest -q && python tasks/audit_process.py --verbose` |
| Run example (point-kernel) | `pyshield run examples/01_point_kernel_shielding/config.yaml` |
| Run example (MC, parallel) | `pyshield run examples/02_monte_carlo_transmission/config.yaml --workers 4` |
| Emit SLURM job script | `pyshield emit-slurm examples/02_monte_carlo_transmission/config.yaml job.slurm --nodes 2` |

## Conventions

- Length: metres [m]; energy: MeV; cross sections: barns (converted to cm² at transport boundary); dose: Sv/h.
- Default dose quantity: `H*(10)` via ICRP-74 coefficients.
- YAML schema: `schema_version: "1.0.0"`. Breaking changes require major version bump.
- YAML loader: always use `pyshield_smr.io.yaml_config.load_yaml_spec()` — handles YAML 1.1 float notation (`1.0e6` → float).
- Point-kernel geometry: 1-D along z-axis. Runner extracts `pos[2]` from 3-D spec positions.
- Buildup formula: `B = A·exp(+α₁·τ) + (1-A)·exp(-α₂·τ)`. α₁ is the growth term (positive exponent).
- Scipy-dependent submodules: `alarp.optimiser`, `activation.bateman`. Import via direct submodule path, not `alarp/__init__`.

## Key physics numbers (cross-checks)

| Quantity | Value | Source |
|---|---|---|
| Lead density | 11.34 g/cm³ | `data/cross_sections/photon_mass_attenuation.json` |
| Lead µ at 1 MeV | ~0.77 cm⁻¹ | NIST XCOM (via data file) |
| ICRP-74 h*(10) at 1 MeV | ~5.2 pSv·cm² | `data/flux_to_dose/icrp74_photon.json` |
| Co-60 regression (example 01) | 1.72e-8 Sv/h | `tests/integration/regression_values.yaml` |
| Audit checks passing | 13 / 13 | `python tasks/audit_process.py --verbose` |

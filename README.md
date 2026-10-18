# PyShield-SMR

**Radiation physics and shielding analysis framework for Small Modular Reactors — built from first principles in Python.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![tests](https://github.com/theonlyallana/pyshield-smr/actions/workflows/tests.yml/badge.svg)](https://github.com/theonlyallana/pyshield-smr/actions/workflows/tests.yml)

> **Portfolio / demonstrator project.** Implements real physics, real numerical methods, and real QA practices. Not a licensed safety-case tool — see [disclaimer](#disclaimer).

---

## What this demonstrates

PyShield-SMR is structured around the full competency profile of a Radiation Physics & Shielding (RP&S) engineer. Every module maps to a real deliverable:

| Engineering deliverable | Code |
|---|---|
| Dose-rate shielding assessments | `pyshield_smr/shielding/point_kernel.py` |
| Monte Carlo photon transport | `pyshield_smr/transport/monte_carlo.py` |
| Source-term generation | `pyshield_smr/sources/source_term.py` |
| Bateman decay-chain solver | `pyshield_smr/activation/bateman.py` (`decay_matrix`, `decay_inventory`) |
| DPA, gamma heating, detector response | `pyshield_smr/shielding/dpa.py`, `gamma_heating.py`, `detector.py` |
| ALARP shielding optimisation | `pyshield_smr/alarp/optimiser.py` (`optimise_shielding`) |
| Latin-hypercube uncertainty quantification | `pyshield_smr/uq/monte_carlo_uq.py` (`lhs_samples`) |
| YAML-driven workflow engine | `pyshield_smr/workflow/runner.py` |
| QA manifest (data hashes, version, platform) | `pyshield_smr/workflow/quality.py` |
| Structured technical report (Markdown + HTML) | `reports/templates/` |
| SLURM/PBS script helpers | `pyshield_smr/hpc/scheduler.py` (`emit_slurm_script`, `emit_pbs_script`) |

The workflow runner calls the point-kernel dose calculation, zone assignment, the QA manifest, and the report templates. Monte Carlo, uncertainty quantification, and ALARP optimisation are libraries only. See [Roadmap](#roadmap).

---

## Quick start (Windows / PowerShell)

```powershell
git clone https://github.com/theonlyallana/pyshield-smr.git
cd pyshield-smr

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"

# Governance audit (12 checks)
python tasks/audit_process.py --verbose

# Test suite
pytest -q

# Example 1 — Co-60 behind 5 cm lead, point-kernel dose assessment
pyshield run examples/01_point_kernel_shielding/config.yaml

# Open the generated report
start reports\  # then open the timestamped folder
```

**Expected output from Example 1** (log lines are `timestamp | LEVEL | logger | message`; dose checked on Python 3.12):
```
... | INFO | pyshield_smr.workflow.runner | Starting analysis: Co-60 Behind 5cm Lead
... | INFO | pyshield_smr.workflow.runner |   Resolving Co-60 at 1.00e+06 Bq
... | INFO | pyshield_smr.workflow.runner |   Resolved 2 photon lines
... | INFO | pyshield_smr.workflow.runner |   Building slab: lead 5.0 cm
... | INFO | pyshield_smr.workflow.runner |   Engine: point-kernel
... | INFO | pyshield_smr.workflow.runner |     Dose rate at receptor: 1.721e-08 Sv/h
... | INFO | pyshield_smr.workflow.runner |   Zone assigned: uncontrolled
... | INFO | pyshield_smr.workflow.runner | All outputs written to reports/<timestamp>_Co-60_Behind_5cm_Lead
```

Results written to `reports/<timestamp>_<case>/`:

```
report.md          ← human-readable analysis report
report.html        ← styled HTML (open in browser)
qa_manifest.json   ← QA record: package version, data hashes, runtime
spec_used.yaml     ← exact input spec that produced this result
```

---

## Five worked examples

Run a spec with `pyshield run examples/<folder>/config.yaml`. What the runner actually executes:

| # | Example | What `pyshield run` does |
|---|---|---|
| 01 | `01_point_kernel_shielding/` | Point-kernel dose for Co-60 through 5 cm lead, then zone assignment |
| 02 | `02_monte_carlo_transmission/` | Logs that Monte Carlo is not integrated and does not report a dose. The spec's `monte_carlo` block is not read by the runner |
| 03 | `03_activation_decay/` | Point-kernel dose from the Co-60 activity written in the spec. `decay_inventory` and `simple_burnup_buildup` are not called |
| 04 | `04_alarp_optimization/` | Point-kernel dose for the starting geometry. `optimise_shielding` is not called |
| 05 | `05_smr_compartment/` | Point-kernel dose for the first receptor. Uncertainty and ALARP sections are not executed |

---

## Roadmap

These exist as importable libraries. They are not called by `pyshield run`, and this change does not add a CLI command for them.

| Item | Where it lives | Not done |
|---|---|---|
| Monte Carlo photon transport | `MonteCarloPhoton` in `pyshield_smr/transport/monte_carlo.py`; `run_histories_parallel` in `pyshield_smr/hpc/parallel.py` | The runner does not call either. Example 02 logs that Monte Carlo is not integrated and does not report a dose |
| Uncertainty quantification | `lhs_samples` and `morris_screen` in `pyshield_smr/uq/` | The runner does not call them. A spec `uncertainty` block is skipped |
| ALARP optimisation | `optimise_shielding` in `pyshield_smr/alarp/optimiser.py` | The runner does not call it. Example 04 reports the starting-geometry point-kernel dose |
| Scheduler CLI | `emit_slurm_script` and `emit_pbs_script` in `pyshield_smr/hpc/scheduler.py` | `pyshield emit-slurm` writes a short placeholder and does not call `emit_slurm_script`. There is no `emit-pbs` command and no `--workers` flag |

---

## Physics covered

### Transport methods

**Point-kernel** — analytical integration of the Boltzmann transport equation along a 1-D ray path through a slab stack:

```
Ḋ(r) = Σ_E [ S(E) / (4πr²) ] × exp(−τ(E)) × B(τ, E) × h*(10, E)
```

where `τ` is optical depth, `B` is the Taylor two-term buildup factor, and `h*` is the ICRP-74 flux-to-dose coefficient.

**Monte Carlo** — individual photon histories sampled stochastically with Kahn rejection for Compton Klein-Nishina kinematics, optional implicit-capture and Russian-roulette/splitting variance reduction.

### Nuclear data (all vendored, SHA-256 hashed)

| Dataset | File | Source |
|---|---|---|
| Photon mass attenuation | `data/cross_sections/photon_mass_attenuation.json` | NIST XCOM |
| Taylor two-term buildup factors | `data/buildup_factors/taylor_two_term.json` | ANS-6.4.3-style |
| Flux-to-dose (H*(10)) | `data/flux_to_dose/icrp74_photon.json` | ICRP-74 |
| Gamma-line library | `data/decay_chains/short.json` | NUBASE2020 / ENSDF |

---

## Quality & governance

The project implements a four-layer governance model (see [`tasks/PROCESS_ARCHITECTURE.md`](tasks/PROCESS_ARCHITECTURE.md)):

```
python tasks/audit_process.py --verbose
```

On Python 3.12, `python tasks/audit_process.py --verbose` reported `audit: PASS (12 checks)`.

`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and `docs/guides/QA.md` are not required. The specialist-routing check that read `AGENTS.md` is not run. `tasks/memory/MEMORY.md` stays dated 2026-04-14 and `tasks/memory/feedback.md` stays dated 2026-04-15; the audit locks those dates. Other memory files still have to be dated within 180 days. `tasks/process_state.md` stays at `last_reviewed: 2026-04-14` and `next_review_due: 2026-07-14`. The audit reports that the review date is overdue and does not fail for it.

`.github/workflows/tests.yml` runs `pytest` on Python 3.12. The badge at the top points at that workflow. It was added after [run 39164454656](https://github.com/theonlyallana/pyshield-smr/actions/runs/39164454656) completed with success on commit `855fb97`.

Every analysis produces a **QA manifest** — a JSON record of the code version, all nuclear-data file SHA-256 hashes, platform, runtime, and warnings — ensuring full reproducibility.

### Test coverage

On Python 3.12, `pytest -q` reported **254 passed**. `pytest -q tests/integration` reported **12 passed**. The integration file compares four point-kernel cases with the tolerances in `tests/integration/regression_values.yaml` (5% or 10%). The iron case expected dose is 1.65e-7 Sv/h after the buildup correction; the tolerance is still 5%. Example 02 is not one of those cases.

Unit modules and what they cover:

```
tests/unit/
  test_physics_constants.py   CODATA 2018 constants
  test_buildup.py             B(τ=0)=1, growth with τ, lead and water magnitude
  test_attenuation.py         Interpolation, unit conversion, density scaling
  test_dose.py                h*(10) linearity, 3600× unit ratio, ICRP-74 range
  test_geometry.py            SlabStack boundaries, traverse(), Sphere validation
  test_source_term.py         Co-60 two-line spectrum, Cs-137, multi-nuclide
  test_point_kernel.py        1/r², attenuation, buildup, multi-receptor, Co-60/lead benchmark
  test_zoning.py              Zone thresholds, boundary conditions, custom thresholds
  test_yaml_config.py         YAML 1.1 float parsing (1.0e6 → float, not string)
  test_runner_smoke.py        Import paths and a point-kernel execute cycle
```

There are no unit tests for `activation/`, `uq/`, `alarp/optimiser.py`, `transport/monte_carlo.py`, `hpc/`, or the DPA, gamma-heating, and detector modules.

---

## Project structure

```
pyshield-smr/
├── pyshield_smr/              # Main package
│   ├── physics/               # Constants, materials, attenuation, buildup, dose conversion
│   ├── transport/             # Slab geometry, Monte Carlo solver, tallies, MCNP I/O
│   ├── shielding/             # Point-kernel, dose rate, DPA, gamma heating, detector
│   ├── sources/               # Source-term builder, gamma-line spectra
│   ├── activation/            # Bateman solver (scipy), simplified burnup
│   ├── uq/                    # Latin-hypercube sampler, Morris sensitivity screening
│   ├── alarp/                 # SLSQP optimiser, radiological zoning
│   ├── workflow/              # YAML schema, runner, QA manifest, report renderer
│   ├── hpc/                   # Multiprocessing runner, SLURM/PBS script emitter
│   ├── cli/                   # `pyshield` command-line interface
│   └── io/                    # YAML config loader, Jinja2 report renderer
│
├── data/                      # Vendored nuclear data (hashed into every QA manifest)
│   ├── cross_sections/        # NIST XCOM photon mass attenuation coefficients
│   ├── buildup_factors/       # Taylor two-term parameters (4 materials)
│   ├── flux_to_dose/          # ICRP-74 H*(10) conversion coefficients
│   └── decay_chains/          # Nuclide half-lives, gamma lines, yields
│
├── examples/                  # Five end-to-end worked analyses
├── tests/                     # pytest unit + integration suite
├── docs/theory/               # Physics derivations (7 documents + PHYSICS_CHANGELOG.md)
├── docs/guides/               # GETTING_STARTED.md, HPC.md, MCNP_INTEROP.md
├── reports/templates/         # Jinja2 report templates (Markdown + HTML)
├── tasks/                     # Governance notes, audit script, memory, agent files
│
├── requirements-dev.txt       # Pip requirements matching pyproject; does not install the package
└── pyproject.toml             # Package metadata, runtime deps, [dev] extra, tool config
```

---

## Documentation

| Document | What it covers |
|---|---|
| [`docs/theory/01_transport_theory.md`](docs/theory/01_transport_theory.md) | Boltzmann equation, photon interactions, dose quantities, unit conventions |
| [`docs/theory/02_point_kernel.md`](docs/theory/02_point_kernel.md) | Point-kernel derivation, buildup factors, validation against MC |
| [`docs/theory/03_monte_carlo.md`](docs/theory/03_monte_carlo.md) | Analog MC, Kahn sampling, implicit capture, FOM, convergence |
| [`docs/theory/04_source_terms.md`](docs/theory/04_source_terms.md) | Fission products, activation gammas, combined spectrum |
| [`docs/theory/05_activation_and_decay.md`](docs/theory/05_activation_and_decay.md) | Bateman equations, matrix exponential, burnup simplifications |
| [`docs/theory/06_uq.md`](docs/theory/06_uq.md) | LHS, Morris screening, uncertainty sources, reporting |
| [`docs/theory/07_alarp.md`](docs/theory/07_alarp.md) | ALARP regulatory basis, optimisation formulation, IRR17 |
| [`docs/guides/GETTING_STARTED.md`](docs/guides/GETTING_STARTED.md) | Setup and walkthrough (Windows + Linux/macOS) |
| [`docs/guides/HPC.md`](docs/guides/HPC.md) | What the HPC helpers do, and which CLI flags are absent |
| [`docs/guides/MCNP_INTEROP.md`](docs/guides/MCNP_INTEROP.md) | Exporting to MCNP, cross-validation protocol |

---

## Disclaimer

PyShield-SMR is an educational and portfolio project. It implements real physics and real numerical methods, but:

- It is **not** a licensed safety-case tool.
- It must **not** be used for regulatory submissions or actual facility safety justification.
- Nuclear data is a pedagogical reproduction — production analyses require official ENDF/B or JEF libraries.
- Where MCNP, SCALE, FISPACT, ORIGEN, or Attila4MC are referenced it is for pedagogical comparison only.

---

## License

[MIT](LICENSE) — © Andrew Allan, 2026.

If you reference this work in a thesis, portfolio, or presentation:

> A. Allan, *PyShield-SMR: an open-source radiation physics and shielding analysis framework for SMRs*, 2026. https://github.com/theonlyallana/pyshield-smr

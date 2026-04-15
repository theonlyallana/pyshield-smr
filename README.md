# PyShield-SMR

**Radiation physics and shielding analysis framework for Small Modular Reactors — built from first principles in Python.**

[![CI](https://github.com/YOUR_GITHUB_USERNAME/pyshield-smr/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/pyshield-smr/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Governance](https://img.shields.io/badge/audit-13%2F13%20checks-brightgreen)](#quality--governance)

> **Portfolio / demonstrator project.** Implements real physics, real numerical methods, and real QA practices. Not a licensed safety-case tool — see [disclaimer](#disclaimer).

---

## What this demonstrates

PyShield-SMR is structured around the full competency profile of a Radiation Physics & Shielding (RP&S) engineer. Every module maps to a real deliverable:

| Engineering deliverable | Code |
|---|---|
| Dose-rate shielding assessments | `pyshield_smr/shielding/point_kernel.py` |
| Monte Carlo photon transport | `pyshield_smr/transport/monte_carlo.py` |
| Source-term generation (fission products, activation) | `pyshield_smr/sources/source_term.py` |
| Bateman decay-chain solver | `pyshield_smr/activation/bateman.py` |
| DPA, gamma heating, detector response | `pyshield_smr/shielding/dpa.py`, `gamma_heating.py`, `detector.py` |
| ALARP shielding optimisation | `pyshield_smr/alarp/optimiser.py` |
| Latin-hypercube uncertainty quantification | `pyshield_smr/uq/monte_carlo_uq.py` |
| Reproducible YAML-driven workflow engine | `pyshield_smr/workflow/runner.py` |
| QA manifest (data hashes, version, platform) | `pyshield_smr/workflow/quality.py` |
| Structured technical report (Markdown + HTML) | `reports/templates/` |
| HPC job-script generation (SLURM/PBS) | `pyshield_smr/hpc/scheduler.py` |

---

## Quick start (Windows / PowerShell)

```powershell
git clone https://github.com/YOUR_GITHUB_USERNAME/pyshield-smr.git
cd pyshield-smr

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements-dev.txt
pip install -e .

# Run the governance audit (all 13 checks)
python tasks/audit_process.py --verbose

# Run the test suite
pytest -q

# Run Example 1 — Co-60 behind 5 cm lead, point-kernel dose assessment
pyshield run examples/01_point_kernel_shielding/config.yaml

# Open the generated report
start reports\  # then open the timestamped folder
```

**Expected output from Example 1:**
```
INFO | Starting analysis: Co-60 Behind 5cm Lead
INFO | Resolving Co-60 at 1.00e+06 Bq
INFO | Resolved 2 photon lines
INFO | Building slab: lead 5.0 cm
INFO | Engine: point-kernel
INFO | Dose rate at receptor: 1.721e-08 Sv/h
INFO | Zone assigned: uncontrolled
INFO | All outputs written to reports\..._Co-60_Behind_5cm_Lead\
```

Results written to `reports/<timestamp>_<case>/`:

```
report.md          ← human-readable analysis report
report.html        ← styled HTML (open in browser)
qa_manifest.json   ← QA record: code version, data hashes, runtime
spec_used.yaml     ← exact input spec that produced this result
```

---

## Five worked examples

Each example builds complexity. Run any with `pyshield run examples/<folder>/config.yaml`.

| # | Example | Physics demonstrated |
|---|---|---|
| 01 | `01_point_kernel_shielding/` | Point-kernel method, buildup factors, zone assignment |
| 02 | `02_monte_carlo_transmission/` | Analog MC transport, statistical convergence, variance reduction |
| 03 | `03_activation_decay/` | Activation source term, gamma-line library, iron shielding |
| 04 | `04_alarp_optimization/` | SLSQP-constrained shielding optimisation, ALARP trade-off |
| 05 | `05_smr_compartment/` | Multi-layer composite shield, multi-receptor, UQ + ALARP |

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

```
✓ required-files-present
✓ architecture-links
✓ specialist-routing-doctrine
✓ agent-files-present
✓ memory-freshness
✓ process-state-review-date
✓ todo-review-present
✓ physics-changelog-nonempty
✓ yaml-schema-version
✓ data-directory-populated
✓ tests-discoverable
✓ qa-manifest-hashing
✓ examples-consistency
audit: PASS (13 checks)
```

Every analysis produces a **QA manifest** — a JSON record of the code version, all nuclear-data file SHA-256 hashes, platform, runtime, and warnings — ensuring full reproducibility.

### Test coverage

```
tests/unit/
  test_physics_constants.py   CODATA 2018 constants
  test_buildup.py             Buildup formula: B(τ=0)=1, B grows with τ, physical range
  test_attenuation.py         Log-log interpolation, unit conversion, lead > water
  test_dose.py                h*(10) linearity, 3600× unit ratio, ICRP-74 range
  test_geometry.py            SlabStack boundaries, traverse(), Sphere validation
  test_source_term.py         Co-60 two-line spectrum, Cs-137, multi-nuclide, binning
  test_point_kernel.py        1/r² law, exp(-τ), buildup > uncollided, Co-60 benchmark
  test_zoning.py              Zone thresholds, boundary conditions, custom thresholds
  test_yaml_config.py         YAML 1.1 float parsing (1.0e6 → float, not string)
  test_runner_smoke.py        Import paths, full execute cycle, QA manifest, no errors

tests/integration/
  test_regression.py          Four example cases within ±5–10% of regression_values.yaml
```

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
├── docs/theory/               # Physics derivations (7 documents)
├── docs/guides/               # How-to guides (QA, HPC, MCNP interop, getting started)
├── reports/templates/         # Jinja2 report templates (Markdown + HTML)
├── tasks/                     # Governance: process architecture, audit, memory, agents
│
├── requirements.txt           # Runtime dependencies
├── requirements-dev.txt       # + test and lint tools
└── pyproject.toml             # Package metadata and tool config
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
| [`docs/guides/GETTING_STARTED.md`](docs/guides/GETTING_STARTED.md) | Full setup and walkthrough (Windows + Linux/macOS) |
| [`docs/guides/QA.md`](docs/guides/QA.md) | Reproducibility, QA manifest, regression testing, physics changelog |
| [`docs/guides/HPC.md`](docs/guides/HPC.md) | Parallel execution, SLURM/PBS job scripts |
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

[MIT](LICENSE) — © Andrew Allana, 2026.

If you reference this work in a thesis, portfolio, or presentation:

> A. Allana, *PyShield-SMR: an open-source radiation physics and shielding analysis framework for SMRs*, 2026. https://github.com/YOUR_GITHUB_USERNAME/pyshield-smr

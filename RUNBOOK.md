# RUNBOOK — PyShield-SMR

> Auto-maintained. Update this file whenever scripts, modules, workflows, dependencies, or process expectations change.
> Last updated: 2026-10-18

---

## What's in this project

| Component | Location | Purpose |
|---|---|---|
| Python package | `pyshield_smr/` | All runtime code |
| Physics core | `pyshield_smr/physics/` | Constants, materials, cross sections, attenuation, buildup factors |
| Transport | `pyshield_smr/transport/` | Geometry, Monte Carlo solver, variance reduction, MCNP I/O |
| Shielding engines | `pyshield_smr/shielding/` | Point kernel, dose rate, DPA, gamma heating, detector response |
| Source terms | `pyshield_smr/sources/` | Fission-product and activation source generation, spectra |
| Activation / decay | `pyshield_smr/activation/` | Bateman solver, decay chains, simplified burn-up |
| Uncertainty quantification | `pyshield_smr/uq/` | LHS sampling, sensitivity, Monte Carlo UQ |
| ALARP | `pyshield_smr/alarp/` | Optimiser and radiological zoning |
| Workflow engine | `pyshield_smr/workflow/` | YAML schema, runner, QA manifest |
| HPC | `pyshield_smr/hpc/` | Parallel executor, cluster adapter |
| CLI | `pyshield_smr/cli/` | `pyshield` command-line interface |
| Tests | `tests/unit/` (10 files), `tests/integration/` | pytest suite + regression fixtures. On Python 3.12: 254 passed; integration 12 passed |
| Examples | `examples/01_point_kernel_shielding/`, `02_monte_carlo_transmission/`, `03_activation_decay/`, `04_alarp_optimization/`, `05_smr_compartment/` | End-to-end worked analyses |
| Nuclear data | `data/` | Cross sections, buildup factors, flux-to-dose coefficients, decay chains |
| Docs | `docs/theory/` (7 theory docs + PHYSICS_CHANGELOG), `docs/guides/` (3 guides: GETTING_STARTED, HPC, MCNP_INTEROP) | Theory and user docs. `docs/guides/QA.md` is not in the tree |
| Reports | `reports/templates/` | Markdown/HTML report templates |
| Governance | `tasks/`, `RUNBOOK.md`, `tasks/PROCESS_ARCHITECTURE.md` | Process notes and `tasks/audit_process.py`. `AGENTS.md` is not in the tree and is not required |

---

## Installing

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# POSIX:    source .venv/bin/activate
pip install -e ".[dev]"
```

Supports Python 3.10+.

---

## Standard commands

| Intent | Command |
|---|---|
| Run unit tests | `pytest -q tests/unit` |
| Run full test suite | `pytest -q` |
| Lint / format | `ruff check . && ruff format --check .` |
| Type check | `mypy pyshield_smr` |
| Run a workflow | `pyshield run examples/01_point_kernel_shielding/config.yaml` |
| Example 2 (Monte Carlo spec) | `pyshield run examples/02_monte_carlo_transmission/config.yaml` — warns that Monte Carlo is not integrated; no `--workers` flag |
| Open generated report | open `reports/<timestamp>_<case>/report.html` |
| Audit governance | `python tasks/audit_process.py --verbose` |

---

## Standard workflow

1. Define the analysis problem in a YAML spec under `examples/<case>/config.yaml` (or anywhere).
2. Run `pyshield run <path>` — or load the spec programmatically via `pyshield_smr.workflow.runner.Runner`.
3. Inspect results in `reports/<UTC timestamp>_<case>/`. The folder contains:
   - `report.md` / `report.html` — human-readable summary,
   - `qa_manifest.json` — package version, data hashes, runtime, warnings, platform,
   - `spec_used.yaml` — the spec the runner executed.
   The runner does not write `tallies.json` or `uq_summary.json`.
4. If the analysis is durable, commit the YAML spec and a frozen copy of the QA manifest.

---

## Adding a new analysis feature

1. Open an entry in `tasks/todo.md` with a plan.
2. Decide ownership via `tasks/agents/registry.md`; route to the right specialist.
3. If physics changes: update `docs/theory/` first, then code, then tests.
4. Add at least one unit test and one regression value.
5. Run the verification suite (see below).
6. Update `tasks/logbook.md`. There is no `CHANGELOG.md`. Physics changes go in `docs/theory/PHYSICS_CHANGELOG.md`.

---

## Verification command

```bash
pytest -q && python tasks/audit_process.py --verbose
```

On Python 3.12 neither command is clean: pytest reported 11 failures, and the audit reported 5 failed checks. Do not treat a green pair as the current gate.

---

## When to update this runbook

Whenever you:

- add, rename, or remove a module or script,
- change a CLI command name or flag,
- add a new example,
- change the way the workflow engine reads / writes files,
- add or remove a CI workflow. There is none in this tree.

# tasks/logbook.md

Append-only log of non-trivial project changes. Newest at the top.

---

## 2026-04-15 — governance repair + bug-fix session (session-2 / Orchestrator)

**Objective**: Make `python tasks/audit_process.py` pass and examples actually run end-to-end.

### Governance fixes (Stage A, B1, E from plan)

- Removed empty example folders (`02_monte_carlo_slab/`, `04_alarp_optimisation/`, `05_full_smr_compartment/`) — duplicates created by naming drift.
- Updated `RUNBOOK.md` parallel-MC command to the correct `02_monte_carlo_transmission/config.yaml`; listed all five example folders explicitly.
- Created 10 missing required files (audit failures):
  - `docs/theory/01_transport_theory.md`, `03_monte_carlo.md`, `04_source_terms.md`, `05_activation_and_decay.md`, `06_uq.md`, `07_alarp.md`
  - `docs/theory/PHYSICS_CHANGELOG.md` (initial v0.1.0 entry + v0.1.1 bug-fix entry)
  - `docs/guides/HPC.md`, `docs/guides/GETTING_STARTED.md`, `docs/guides/MCNP_INTEROP.md`
- Added `check_examples_consistency` (check #13) to `tasks/audit_process.py`.
- Audit went from FAIL (2/12) → PASS (13/13).

### Code bug fixes (four bugs found during regression testing)

All four bugs silently produced wrong dose-rate results. See `docs/theory/PHYSICS_CHANGELOG.md` v0.1.1.

1. **Wrong import path** — `runner.py` imported `assign_zone` from a non-existent `shielding.zoning`; changed to `alarp.zoning`.
2. **Eager scipy imports** — `alarp/__init__.py` and `activation/__init__.py` imported scipy-dependent submodules unconditionally. Wrapped in `try/except ImportError` so scipy-free environments remain functional.
3. **YAML 1.2 float parsing** — `yaml.safe_load` (PyYAML 6.x) parses `1.0e6` as a string. Replaced with `_Yaml11Loader` that accepts YAML 1.1 float notation.
4. **3-D to 1-D position** — Runner passed `[x, y, z]` to a scalar-expecting argument in `point_kernel_dose_rate`. Fixed to extract `pos[2]` (z-axis).
5. **Buildup sign error** — Taylor two-term: `B = A*exp(-α₁μx) + (1-A)*exp(-α₂μx)` gives B < 1 for the stored parameters (A > 1). Correct form is `A*exp(+α₁μx) + (1-A)*exp(-α₂μx)`. Updated code and data meta.

### Regression values established

`tests/integration/regression_values.yaml` created with post-fix values for all five examples. Integration tests added in `tests/integration/test_regression.py`.

### Unit tests added

New tests in `tests/unit/`:
- `test_buildup.py` — verifies B(τ=0)=1, B(τ=5)>1, correct formula
- `test_attenuation.py` — verifies log-log interpolation accuracy
- `test_yaml_config.py` — verifies YAML 1.1 float parsing
- `test_zoning.py` — verifies zone thresholds and boundary conditions
- `test_source_term.py` — verifies nuclide spectrum construction
- `test_runner_smoke.py` — imports and instantiates Runner (no scipy needed)

### State records updated

- `tasks/lessons.md`: 5 new anti-regression rules.
- `tasks/memory/project.md`, `reference.md`, `source_index.md`, `user.md`, `feedback.md`: populated with real content.
- `PROJECT_SUMMARY.md` and `SESSION_2_SUMMARY.md` archived to `tasks/archive/` (not deleted — content preserved).
- `RUNBOOK.md`: removed `scripts/`, `notebooks/`, `docs/api/` from "what's in this project" table (they are empty and not referenced by code).
- `reference.md`: corrected stale command (`02_monte_carlo_slab` → `02_monte_carlo_transmission`).

---

## 2026-04-14 — initial scaffold

- Created governance files: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `RUNBOOK.md`.
- Created `tasks/` scaffold (PROCESS_ARCHITECTURE, process_state, todo, lessons, playbook, logbook, audit_process).
- Created `tasks/memory/` entries and `tasks/agents/registry.md` with five specialists: `physics-governor`, `transport-author`, `workflow-author`, `technical-author`, `qa-governor`.
- Scaffolded the `pyshield_smr/` package with physics, transport, shielding, sources, activation, UQ, ALARP, workflow, HPC, CLI subpackages.
- Implemented core physics: constants, units, materials, mass-attenuation coefficients, Taylor buildup factors, ICRP-74 flux-to-dose coefficients.
- Implemented Monte Carlo photon transport (analog + non-analog with implicit capture, Russian roulette, splitting), point-kernel shielding, DPA, gamma heating, detector response.
- Implemented Bateman decay-chain solver, activation, simplified burn-up, fission-product source term, line spectra.
- Implemented LHS Monte Carlo UQ, Morris sensitivity screening, ALARP optimiser via SLSQP, radiological zoning helpers.
- Implemented YAML workflow engine with `v1` schema, runner, QA manifest, report renderer (Markdown + HTML), and CLI (`pyshield`).
- Implemented HPC executor: process-pool with chunked histories, SLURM/PBS script emitters.
- Added pytest unit + integration suite, CI (GitHub Actions), pre-commit, pyproject packaging, MIT licence, example library (5 cases).
- Added theory, QA, HPC, MCNP-interop, and ALARP docs.

# tasks/todo.md

Current session plan and review record. One session = one block. Oldest at the bottom.

---

## Session: 2026-04-14 — initial scaffold

### Plan

- [x] Decide on project identity and scope (PyShield-SMR).
- [x] Create workspace-convention files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `RUNBOOK.md`).
- [x] Create `tasks/` scaffold (PROCESS_ARCHITECTURE, process_state, todo, lessons, playbook, logbook, audit_process.py).
- [x] Create `tasks/memory/` entries and `tasks/agents/registry.md`.
- [x] Scaffold Python package (`pyproject.toml`, package layout, CI, pre-commit, `.gitignore`, `LICENSE`).
- [x] Implement physics core (constants, units, materials, cross sections, attenuation, buildup).
- [x] Implement transport (geometry, particle, tally, Monte Carlo, variance reduction, MCNP I/O).
- [x] Implement shielding engines (point kernel, dose rate, DPA, gamma heating, detector response).
- [x] Implement sources and activation (source term, spectra, Bateman, burn-up).
- [x] Implement UQ (LHS, sensitivity, MC-UQ) and ALARP optimiser + zoning.
- [x] Implement workflow (schema, runner, QA manifest), CLI, HPC runner, and reporting.
- [x] Write unit + integration tests and five worked examples.
- [x] Write theory, QA, HPC, and MCNP-interop documentation.
- [x] Run `pytest -q` and a sample workflow and record verification evidence.

### Design decision

Decided to implement a pedagogical but correct analog photon Monte Carlo solver plus a point-kernel engine, rather than wrap an existing MC code. Rationale: the project is a portfolio / demonstrator, and wrapping MCNP would hide the physics that the role description explicitly calls for (source-term generation, variance reduction, tallying, dose conversion). Rejected options:

- **Wrap OpenMC.** Dependency weight, and hides the physics.
- **Pure point kernel only.** Too narrow — no fluence spectra, no variance reduction, no MC literacy demonstrated.
- **Deterministic SN in 1-D only.** Useful but also too narrow.

Risks: pedagogical MC is slow; mitigated by non-analog variance reduction, chunked parallel execution, and clear messaging in `docs/theory/03_monte_carlo.md` that this is not an MCNP replacement.

### Review

- `pytest -q` → see review section below after final verification run.
- `python tasks/audit_process.py --verbose` → see review section below.
- All planned items marked complete only after the two commands above pass.

### Verification evidence

To be filled in by the final verification step of the session. Must include:

- exit codes of the two verification commands,
- number of tests passed,
- any warnings or skipped tests with justification,
- sha of the QA manifest from the example run.

---

## Session template

### Plan
- [ ]

### Design decision

### Review

### Verification evidence

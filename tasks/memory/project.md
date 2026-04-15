---
last_updated: 2026-04-15
---

# project.md

## Current state

v0.1.1 — governance repair and bug-fix session complete (2026-04-15).

All governance checks pass (13/13 in `audit_process.py`). Four code bugs found and fixed during first real execution of the examples. Regression values established. Full unit test suite written (8 test files covering physics, geometry, source terms, dose conversion, zoning, YAML loading, runner, and integration regressions).

## What is working end-to-end

- Point-kernel analysis for all five examples: YAML spec → source term → geometry → transport → dose rate → zone → QA manifest → reports.
- Governance audit: all 13 checks pass including the new `check_examples_consistency` check.
- Unit tests: 8 files, coverage across all major modules.
- Integration regression tests: 4 cases against `regression_values.yaml`.

## What is NOT yet wired into the runner

- Monte Carlo transport (`_run_monte_carlo` logs a warning; MC engine itself is implemented in `transport/monte_carlo.py`).
- UQ sampling (`_run_uq` logs a warning; LHS and Morris implementations exist in `uq/`).
- ALARP optimisation (`_run_alarp` logs a warning; SLSQP optimiser exists in `alarp/optimiser.py` and requires scipy).

## Decisions

- Own analog photon MC (not wrapping an external code) for pedagogy and portfolio evidence.
- YAML-spec-as-code workflow at schema `v1.0.0`.
- `H*(10)` default dose quantity; ICRP-74 coefficients.
- Pedagogical cross-section and buildup datasets vendored; hashed into QA manifest.
- Taylor two-term buildup: `B = A·exp(+α₁τ) + (1-A)·exp(-α₂τ)` — α₁ is the growth term (positive sign).
- YAML loader uses YAML 1.1 float resolver so `1.0e6` parses as float.
- 1-D point-kernel uses z-axis only; runner extracts `pos[2]` from 3-D spec positions.
- scipy-dependent modules (`alarp.optimiser`, `activation.bateman`) wrapped in conditional imports so scipy-free environments remain functional.

## Blockers / followups (priority order)

1. Wire MC engine into runner `_run_monte_carlo()` — physics is ready, runner stub is not.
2. Wire UQ sampler into runner `_run_uq()`.
3. Wire ALARP optimiser into runner `_run_alarp()` — requires scipy at runtime.
4. Add Monte Carlo integration test (blocked by item 1).
5. Add Sphinx docs site (currently standalone Markdown).
6. OpenMC backend cross-verification (out of scope for v1).

## Active work

Verification pass complete. No open tasks. Next session should wire the MC/UQ/ALARP runner stubs.

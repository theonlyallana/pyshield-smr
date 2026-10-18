---
last_updated: 2026-10-18
---

# project.md

## Current state

v0.1.1. Checked on 2026-10-18 with Python 3.12.

`python tasks/audit_process.py --verbose` fails 5 of 13 checks. Missing files: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `docs/guides/QA.md`. `tasks/memory/MEMORY.md` and `tasks/memory/feedback.md` are still dated April 2026, so `memory-freshness` still fails. `tasks/process_state.md` has `next_review_due: 2026-07-14`.

`pytest -q` reported 11 failed, 243 passed. `pytest -q tests/integration` reported 12 passed. Unit tests are 10 files, not 8. There is no coverage of activation, Monte Carlo, UQ, the ALARP optimiser, or HPC.

## What is working end-to-end

- Point-kernel path for examples 01, 03, 04, and 05: YAML spec → prescribed source → slab → point-kernel dose → zone → QA manifest → `report.md`, `report.html`, `qa_manifest.json`, `spec_used.yaml`.
- Example 01 dose rate printed by the runner: 1.721e-08 Sv/h, zone uncontrolled.
- Example 02 does not produce a dose. The runner warns that Monte Carlo is not integrated.

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

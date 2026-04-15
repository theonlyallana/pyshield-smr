---
status: active
last_reviewed: 2026-04-14
---

# PyShield-SMR — Project Agent Instructions

Canonical startup file for LLM agents working inside `pyshield-smr/`. Root workspace rules in `../AGENTS.md` still apply; this file owns project-specific detail.

## Session Start Checklist

1. Read this file.
2. Read `RUNBOOK.md` for project structure and commands.
3. Read `tasks/PROCESS_ARCHITECTURE.md` to place new rules in the right layer.
4. Read `tasks/lessons.md` and `tasks/todo.md` before editing durable files.
5. Read `tasks/agents/registry.md` to identify active specialists.
6. Read `tasks/memory/MEMORY.md` and load the relevant memory files for the task.
7. Before finishing, update `tasks/todo.md` with the plan + review outcome, and `tasks/logbook.md` with any non-trivial change.
8. Run `python tasks/audit_process.py --verbose` before marking non-trivial work complete.

## What PyShield-SMR is

A Python framework that performs radiation physics and shielding analysis for an SMR-class PWR. It implements:

- photon/neutron transport (point-kernel + Monte Carlo, with variance reduction),
- source-term generation, neutron activation, and Bateman decay chains,
- dose-rate, DPA, gamma-heating, and detector-response post-processing,
- ALARP optimisation over shielding thickness / layout,
- uncertainty quantification by Latin-hypercube sampling,
- an analysis-spec-as-code YAML workflow engine with QA manifest and report generator.

It is a **portfolio / demonstrator** code — not a licensed safety-case tool.

## Rule Hierarchy

1. Safety / quality rules from the root `AGENTS.md` always apply.
2. Project-local rules in this file own project-specific behaviour.
3. Module-level docstrings and `docs/theory/*.md` own the physics conventions.
4. `tasks/lessons.md` records anti-regression rules from past corrections.

## Automatic Specialist Routing

- Physics / numerics changes → route to `physics-governor` (owns invariants, cross-section sources, and `physics_changelog.md`).
- Shielding engine / point-kernel / MC changes → route to `transport-author`.
- Workflow, CLI, HPC scheduler changes → route to `workflow-author`.
- Anything that touches reports, dose tables, or external-facing language → route to `technical-author` for clarity + correctness pass.
- QA / audit / CI changes → route to `qa-governor`.

If no specialist exists for a recurring need (≥3 anticipated uses), spawn a new one and register it in `tasks/agents/registry.md`.

## Decentralised Handoff

A specialist may hand off directly to another registered specialist when the next step has a clearer owner. The handoff must (a) name the receiver, (b) state reason + context + evidence, (c) assign verification responsibility, (d) define the return point to the Orchestrator. Return to the Orchestrator for user-facing synthesis, permission-sensitive actions, or conflicts.

## Verification Before Done

- Run `pytest -q` — must pass.
- Run `python tasks/audit_process.py --verbose` — must pass.
- For physics changes: re-run the relevant examples in `examples/` and confirm results agree with the regression values in `tests/integration/regression_values.yaml` to within tolerance.
- Record verification evidence in `tasks/todo.md` → review section.

## Elegance Gate

Before non-trivial changes, ask whether a simpler route exists. If a fix feels hacky, go back to the physics or the interface. Prefer named functions over clever one-liners; prefer explicit units and type hints over "everything is a float".

## Core Principles

- Physics correctness over code cleverness.
- Traceability: every number in a report must be reproducible from the YAML spec + code version.
- Units are never implicit (use `pyshield_smr.physics.units`).
- All uncertainties are declared; no "point estimates as truth".
- No network calls at analysis time — nuclear data is vendored under `data/` and hashed into the QA manifest.
- Reports state assumptions, limits of validity, and what would falsify the result.

## Pointers

- `tasks/PROCESS_ARCHITECTURE.md` — four-layer process model.
- `tasks/audit_process.py` — executable governance audit.
- `docs/theory/` — physics derivations and conventions.
- `docs/guides/QA.md` — quality-management process.
- `docs/guides/HPC.md` — running on clusters.

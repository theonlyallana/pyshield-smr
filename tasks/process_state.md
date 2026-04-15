---
last_reviewed: 2026-04-14
next_review_due: 2026-07-14
review_cadence_days: 90
owner: orchestrator
---

# Process State

## Current baseline

Initial project scaffold complete. Governance layer (AGENTS, RUNBOOK, PROCESS_ARCHITECTURE, audit_process) and analysis code (physics, transport, shielding, sources, activation, UQ, ALARP, workflow, HPC, CLI) are in place. Tests and one end-to-end example run under `pytest -q` and `pyshield run`.

## What is stable

- Unit policy: all distances in metres, energies in MeV, cross sections in barns (internally converted to cm² at the transport boundary), dose in sieverts/hour unless stated otherwise.
- Fluence direction convention: scalar fluence, 4π unless a direction cosine is tracked.
- Default dose quantity: H*(10) — ambient dose equivalent — via ICRP-74 coefficients.
- YAML schema versioned at `v1`; breaking changes require a major bump.

## Pending decisions

- Whether to ship an optional `openmc` backend for cross-verification (currently out of scope; pedagogical MC is analog photon transport only).
- Whether to vendor a subset of ENDF/B-VIII cross sections or to stay with the embedded educational library.

## Last review notes

Scaffold established on 2026-04-14. No corrections yet. Next review: re-check stable assumptions after the first external code review.

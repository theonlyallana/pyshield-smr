---
last_updated: 2026-04-15
---

# user.md

## Goal

Portfolio project demonstrating the full competency profile of a Radiation Physics & Shielding engineer at Rolls-Royce SMR. Deliverable is a self-contained GitHub repo that (a) reads well, (b) runs end-to-end on a clean laptop, (c) shows real physics, not stubs.

## Audience

- Hiring manager / interviewer — will skim README, clone, run an example.
- Technical reviewer — will open the theory docs and the tests.
- Future employers — the repo must be re-usable as evidence of craft.

## Preferences

- Prose over bullet-point dumps in docs.
- Explicit units, no magic numbers.
- Tests that show the physics, not just that a function returns a number.
- Keep licensed codes (MCNP / Attila / SCALE / FISPACT / ORIGEN) as references, not dependencies.
- After finding bugs or making changes, always record learnings in the md files (PHYSICS_CHANGELOG, lessons.md, logbook.md, memory/).
- Use agents / subagents to check md files and record learnings at session end.

## Current status (2026-04-15)

The repo is in a state where `python tasks/audit_process.py --verbose` passes 13/13 checks and all five point-kernel examples run end-to-end without errors. Four silent physics/runtime bugs were discovered and fixed. The repo is now ready for review or interview demonstration on the point-kernel + governance stack. MC/UQ/ALARP runner integration is the next major milestone.

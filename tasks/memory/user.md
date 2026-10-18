---
last_updated: 2026-10-18
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

## Current status (2026-10-18)

The audit does not pass (5 of 13 checks failed). Example 01 runs and prints 1.721e-08 Sv/h. Examples 03–05 run a point-kernel dose from the activity in the YAML. Example 02 does not. The test suite is not green (11 failed, 243 passed on Python 3.12). MC, UQ, and ALARP are still not called by the runner.

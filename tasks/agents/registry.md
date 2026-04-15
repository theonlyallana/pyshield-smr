# tasks/agents/registry.md

Single source of truth for active specialists in the PyShield-SMR project.

| name | status | role | scope | spawned | last_used |
|---|---|---|---|---|---|
| physics-governor | Active | Physics invariants owner | Cross sections, buildup factors, dose coefficients, unit conventions, `PHYSICS_CHANGELOG.md` | 2026-04-14 | 2026-04-14 |
| transport-author | Active | Transport / shielding engineering | Monte Carlo solver, point kernel, variance reduction, DPA, gamma heating, detector response | 2026-04-14 | 2026-04-14 |
| workflow-author | Active | Workflow engineering | YAML schema, runner, CLI, HPC executor, reporting | 2026-04-14 | 2026-04-14 |
| technical-author | Active | External-facing communication | Reports, README, docs/guides/, release notes | 2026-04-14 | 2026-04-14 |
| qa-governor | Active | QA and audits | `audit_process.py`, tests, CI, pre-commit, QA manifest | 2026-04-14 | 2026-04-14 |

## Activation rules

- When a task clearly matches one specialist, the Orchestrator activates that specialist automatically.
- When multiple specialists contribute, the Orchestrator routes in parallel and synthesises.
- When a recurring gap is seen (≥3 anticipated uses), spawn a new specialist; add a row here plus `config.md`, `playbook.md`, `logbook.md` in `tasks/agents/<name>/`.

## Retirement rules

- Dormant: no use in 30+ days → flag.
- Underperforming: avg score < 7.0 over 5+ tasks → flag for retirement.

## Proof of delegation

Non-trivial delegated work must leave an entry in the owning agent's `logbook.md` with the session date, inputs, outputs, and verification.

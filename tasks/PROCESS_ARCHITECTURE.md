---
status: active
last_reviewed: 2026-04-14
---

# PyShield-SMR — Process Architecture

Four layers. Every durable rule must fit into exactly one of them.

## 1. Stable rules (rarely change)

These are the invariants that define the project's identity.

- **`AGENTS.md`** — agent startup, rule hierarchy, specialist routing, handoff protocol.
- **`RUNBOOK.md`** — what the project is, how to install and run, standard workflow.
- **`docs/theory/`** — physics conventions (units, direction of fluence, dose quantity, cross-section library).
- **`LICENSE`** — legal boundary.

Stable rules change through a reviewed edit to the file, with an entry in `tasks/logbook.md`.

## 2. Operating playbooks (per-role how-to)

- **`tasks/playbook.md`** — default Orchestrator playbook.
- **`tasks/agents/<name>/playbook.md`** — per-specialist heuristics and output templates.
- **`docs/guides/QA.md`** — how we review and verify analyses.
- **`docs/guides/HPC.md`** — how to run at scale.

Playbooks change whenever a specialist learns a new reusable pattern.

## 3. Executable audits (the single source of compliance truth)

- **`tasks/audit_process.py`** — governance audit: required files, cross-links, registry consistency, memory freshness, review dates, regression-value drift.
- **`tests/`** — physics and code correctness audits.
- **`.github/workflows/ci.yml`** — CI runs both of the above on every push.

If a rule is not encoded in an executable audit, it is not enforced. When adding a new rule, add (or extend) an audit at the same time.

## 4. State records (change every session)

- **`tasks/todo.md`** — current plan + review section.
- **`tasks/logbook.md`** — append-only log of non-trivial changes.
- **`tasks/process_state.md`** — review-cadence state with YAML frontmatter.
- **`tasks/lessons.md`** — anti-regression rules from user corrections.
- **`tasks/memory/`** — durable memory for the project.
- **`CHANGELOG.md`** — user-facing change log.

State records change constantly and do not require a review.

## Cross-cutting rules

- **Automatic specialist routing**: recognised in `AGENTS.md`, encoded by entries in `tasks/agents/registry.md`, enforced by a section of `audit_process.py` that checks every Active agent has a `config.md`, `playbook.md`, and `logbook.md`.
- **Decentralised handoff**: recognised in `AGENTS.md`, enforced by logbook entries that include `handoff_from` / `handoff_to` / `return_point` fields.
- **Verification before done**: recognised in `AGENTS.md`, enforced by the CI pipeline and by `audit_process.py` checking that `todo.md` review sections include a verification block for non-trivial work.
- **Physics changelog**: any change that could move a dose result records an entry in `docs/theory/PHYSICS_CHANGELOG.md` with physics reason, affected results, and regression impact.

## When architecture changes

Update this file, update `audit_process.py` in the same commit, and record the change in `tasks/logbook.md`. Do not leave dangling rules that no audit can see.

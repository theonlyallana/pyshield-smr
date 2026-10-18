---
status: active
last_reviewed: 2026-04-14
---

# PyShield-SMR — Process Architecture

Four layers. Every durable rule must fit into exactly one of them.

## 1. Stable rules (rarely change)

These are the invariants that define the project's identity.

- **`AGENTS.md`** — was the agent startup file. It is not in the tree. `tasks/audit_process.py` still requires it, so `required-files-present`, `check_architecture_links`, and `check_specialist_routing` fail.
- **`RUNBOOK.md`** — what the project is, how to install and run, standard workflow.
- **`docs/theory/`** — physics conventions (units, direction of fluence, dose quantity, cross-section library).
- **`LICENSE`** — legal boundary.

Stable rules change through a reviewed edit to the file, with an entry in `tasks/logbook.md`.

## 2. Operating playbooks (per-role how-to)

- **`tasks/playbook.md`** — default Orchestrator playbook.
- **`tasks/agents/<name>/playbook.md`** — per-specialist heuristics and output templates.
- **`docs/guides/QA.md`** — not in the tree. The audit still lists it as required. Review notes that remain are `docs/theory/PHYSICS_CHANGELOG.md` and `tasks/audit_process.py`.
- **`docs/guides/HPC.md`** — how to run at scale.

Playbooks change whenever a specialist learns a new reusable pattern.

## 3. Executable audits (the single source of compliance truth)

- **`tasks/audit_process.py`** — governance audit: required files, cross-links, registry consistency, memory freshness, review dates, regression-value drift.
- **`tests/`** — physics and code correctness audits.
- **`.github/workflows/ci.yml`** — not in the tree. Nothing runs the audit or the tests on push.

If a rule is not encoded in an executable audit, it is not enforced. When adding a new rule, add (or extend) an audit at the same time.

## 4. State records (change every session)

- **`tasks/todo.md`** — current plan + review section.
- **`tasks/logbook.md`** — append-only log of non-trivial changes.
- **`tasks/process_state.md`** — review-cadence state with YAML frontmatter.
- **`tasks/lessons.md`** — anti-regression rules from user corrections.
- **`tasks/memory/`** — durable memory for the project.
- **`CHANGELOG.md`** — not in the tree. Physics changes are recorded in `docs/theory/PHYSICS_CHANGELOG.md`.

State records change constantly and do not require a review.

## Cross-cutting rules

- **Agent files**: `tasks/agents/registry.md` lists Active agents. `audit_process.py` checks that each Active agent has `config.md`, `playbook.md`, and `logbook.md`. That check currently passes. The doctrine text it also looks for lived in `AGENTS.md`, which is gone.
- **Verification before done**: `audit_process.py` checks that `tasks/todo.md` has review and verification headings. There is no CI pipeline enforcing that.
- **Physics changelog**: any change that could move a dose result records an entry in `docs/theory/PHYSICS_CHANGELOG.md` with physics reason, affected results, and regression impact.

## When architecture changes

Update this file, update `audit_process.py` in the same commit, and record the change in `tasks/logbook.md`. Do not leave dangling rules that no audit can see.

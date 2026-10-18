---
status: active
last_reviewed: 2026-04-14
---

# PyShield-SMR — Process Architecture

Four layers. Every durable rule must fit into exactly one of them.

## 1. Stable rules (rarely change)

These are the invariants that define the project's identity.

- **`AGENTS.md`**, **`CLAUDE.md`**, and **`GEMINI.md`** — not in the tree and not required by `tasks/audit_process.py`. They are not recreated.
- **`RUNBOOK.md`** — what the project is, how to install and run, standard workflow.
- **`docs/theory/`** — physics conventions (units, direction of fluence, dose quantity, cross-section library).
- **`LICENSE`** — legal boundary.

Stable rules change through a reviewed edit to the file, with an entry in `tasks/logbook.md`.

## 2. Operating playbooks (per-role how-to)

- **`tasks/playbook.md`** — default Orchestrator playbook.
- **`tasks/agents/<name>/playbook.md`** — per-specialist heuristics and output templates.
- **`docs/guides/QA.md`** — not in the tree and not required by the audit. Review notes that remain are `docs/theory/PHYSICS_CHANGELOG.md` and `tasks/audit_process.py`.
- **`docs/guides/HPC.md`** — how to run at scale.

Playbooks change whenever a specialist learns a new reusable pattern.

## 3. Executable audits (the single source of compliance truth)

- **`tasks/audit_process.py`** — governance audit: required files, cross-links between `RUNBOOK.md` and this file, registry consistency, memory dates, the frozen process-state record, and the other checks in that script. It does not require `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or `docs/guides/QA.md`. `MEMORY.md`, `feedback.md`, and `tasks/process_state.md` keep their original dates; the audit locks those dates instead of asking for them to be rewritten.
- **`tests/`** — physics and code correctness audits.
- **`.github/workflows/tests.yml`** — runs `pytest` on Python 3.12. It does not run the governance audit.

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

- **Agent files**: `tasks/agents/registry.md` lists Active agents. `audit_process.py` checks that each Active agent has `config.md`, `playbook.md`, and `logbook.md`. Specialist-routing phrases that used to be read from `AGENTS.md` are not checked.
- **Verification before done**: `audit_process.py` checks that `tasks/todo.md` has review and verification headings. There is no CI pipeline enforcing that.
- **Physics changelog**: any change that could move a dose result records an entry in `docs/theory/PHYSICS_CHANGELOG.md` with physics reason, affected results, and regression impact.

## When architecture changes

Update this file, update `audit_process.py` in the same commit, and record the change in `tasks/logbook.md`. Do not leave dangling rules that no audit can see.

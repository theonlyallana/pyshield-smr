# qa-governor — logbook

## 2026-04-14 — audit + CI landed

- `tasks/audit_process.py` with twelve checks, including required-files, architecture links, specialist doctrine, registry consistency, memory freshness, review date, todo review section, physics changelog presence, YAML schema version, data directory populated, tests discoverable, QA manifest hashing.
- `.github/workflows/ci.yml` runs `ruff`, `mypy`, `pytest`, and `audit_process.py` on Python 3.10–3.12.
- `.pre-commit-config.yaml` runs the same locally.
- Regression values file `tests/integration/regression_values.yaml` seeded for point-kernel cases. It has no Monte Carlo case.

## 2026-10-18 — CI file is gone

- `.github/workflows/ci.yml` was deleted. The April note above describes a file that is not in the tree.
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `docs/guides/QA.md`, `CHANGELOG.md`, and `requirements.txt` were also deleted. `tasks/audit_process.py` still requires the first four, so the audit fails.

## 2026-10-18 — audit requirements match the tree

- `tasks/audit_process.py` no longer requires `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or `docs/guides/QA.md`, and it no longer reads `AGENTS.md`.
- `MEMORY.md` (2026-04-14), `feedback.md` (2026-04-15), and `tasks/process_state.md` (`next_review_due: 2026-07-14`) are locked. Their dates were not moved.
- `.github/workflows/tests.yml` runs pytest on Python 3.12. It is not the deleted `ci.yml`.

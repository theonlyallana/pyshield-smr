# Contributing

Thanks for looking at PyShield-SMR.

This repository follows a workspace-wide convention (see `AGENTS.md`). In short:

1. Read `AGENTS.md`, `RUNBOOK.md`, and `tasks/PROCESS_ARCHITECTURE.md` before editing durable files.
2. Open an entry in `tasks/todo.md` with a plan + design decision.
3. Route the work to the right specialist via `tasks/agents/registry.md`.
4. Add or update the right audit or test: a rule that is not in an executable audit is not enforced.
5. Run:
   ```bash
   pytest -q
   python tasks/audit_process.py --verbose
   ```
   Both must pass before opening a PR.
6. Update `CHANGELOG.md` and `tasks/logbook.md`.

## Physics changes

Any change that could move a dose number:

- add a `docs/theory/PHYSICS_CHANGELOG.md` entry **in the same commit**,
- update or justify the affected entries in `tests/integration/regression_values.yaml`,
- cite the primary source (ICRP / ENDF / NIST / peer-reviewed paper).

## Style

- `ruff` formatter and linter are authoritative.
- Public functions carry NumPy-style docstrings that state units in parameter descriptions.
- No magic numbers: use `pyshield_smr.physics.units` or module-level named constants with a citation.

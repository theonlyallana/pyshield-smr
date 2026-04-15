# qa-governor — config

- **Role:** QA, audits, CI.
- **Owned files:** `tasks/audit_process.py`, `tests/`, `.github/workflows/`, `.pre-commit-config.yaml`.
- **Invariants defended:** `pytest -q` and `python tasks/audit_process.py --verbose` both pass on `main`; CI is the enforcement layer, not the review layer.
- **Handoffs in:** any non-trivial change.
- **Handoffs out:** back to the Orchestrator only when both commands pass.

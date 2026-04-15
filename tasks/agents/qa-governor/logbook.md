# qa-governor — logbook

## 2026-04-14 — audit + CI landed

- `tasks/audit_process.py` with twelve checks, including required-files, architecture links, specialist doctrine, registry consistency, memory freshness, review date, todo review section, physics changelog presence, YAML schema version, data directory populated, tests discoverable, QA manifest hashing.
- `.github/workflows/ci.yml` runs `ruff`, `mypy`, `pytest`, and `audit_process.py` on Python 3.10–3.12.
- `.pre-commit-config.yaml` runs the same locally.
- Regression values file `tests/integration/regression_values.yaml` seeded for point-kernel and MC slab examples.

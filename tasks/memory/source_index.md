---
last_updated: 2026-04-15
---

# source_index.md — best starting points by task type

| If the task is… | Start here |
|---|---|
| Changing a cross section or buildup factor | `docs/theory/02_point_kernel.md` → `data/` → `pyshield_smr/physics/` → `docs/theory/PHYSICS_CHANGELOG.md` |
| Adding a new Monte Carlo feature | `docs/theory/03_monte_carlo.md` → `pyshield_smr/transport/monte_carlo.py` → `tests/unit/test_point_kernel.py` |
| Wiring MC into the runner | `pyshield_smr/workflow/runner.py → _run_monte_carlo()` stub → `transport/monte_carlo.py → run_monte_carlo()` |
| Wiring UQ into the runner | `pyshield_smr/workflow/runner.py → _run_uq()` stub → `uq/monte_carlo_uq.py → LatinHypercubeSampler` |
| Wiring ALARP into the runner | `pyshield_smr/workflow/runner.py → _run_alarp()` stub → `alarp/optimiser.py` (requires scipy) |
| Adding a new dose quantity | `docs/theory/01_transport_theory.md` → `pyshield_smr/physics/dose.py` → `pyshield_smr/shielding/dose_rate.py` |
| Adding a new source type to the runner | `runner.py → resolve_sources()` → `sources/source_term.py` → `examples/` |
| Adding a new workflow step | `pyshield_smr/workflow/schema.py` → `runner.py` → new example config |
| Adding a new CLI subcommand | `pyshield_smr/cli/main.py` → update `RUNBOOK.md` commands table |
| Adding a new specialist | `tasks/agents/registry.md` → `tasks/agents/<name>/` (config.md, playbook.md, logbook.md) |
| Investigating a regression | `tests/integration/regression_values.yaml` → `docs/theory/PHYSICS_CHANGELOG.md` → audit trail |
| YAML spec parsing fails silently | `pyshield_smr/io/yaml_config.py → _Yaml11Loader` → check all numeric values are float not str |
| Buildup factor gives B=1 (no buildup) | `pyshield_smr/physics/buildup.py` → verify sign convention: `+α₁` in first exponent |
| Runner fails at import | Check `from pyshield_smr.alarp.zoning import assign_zone` — NOT `shielding.zoning` |
| Writing / regenerating a report | `pyshield_smr/io/report.py` → `reports/templates/` |
| Governance audit fails | `python tasks/audit_process.py --verbose` → fix the specific check → update `tasks/logbook.md` |

# tasks/lessons.md

Anti-regression rules. Each entry is written as a rule to prevent a category of mistake, not a narrative.

Format:

```
## <short-rule-title>
- Rule: <imperative>
- Why: <failure this prevents>
- Enforcement: <audit / test / review step>
- Date: YYYY-MM-DD
```

---

## buildup-sign-convention-must-match-data

- Rule: When implementing a tabulated buildup-factor formula, record the exact sign convention in both the code docstring AND the data `.meta.json` file. Before committing, verify that `B(τ=0) = 1` exactly and `B(τ=5) > 1` for a known material.
- Why: the Taylor two-term form has two legitimate conventions (both negative exponents, or mixed signs). Storing data for one convention and coding the other silently produces B=1 (no buildup), which under-estimates dose by 50–100% for moderate shielding depths.
- Enforcement: `tests/unit/test_buildup.py` checks `B(lead, 1.0 MeV, tau=4) > 1.2` and `B(lead, 1.0 MeV, tau=0) == 1.0`.
- Date: 2026-04-15

## yaml-loader-must-handle-1-1-floats

- Rule: All YAML spec loading must use a YAML 1.1-compatible loader (or document that YAML 1.2 notation `1.0e+6` is required). Never use bare `yaml.safe_load` on user-facing files that may contain scientific notation without explicit signs.
- Why: PyYAML ≥ 6.0 follows YAML 1.2 where `1.0e6` (no sign) is a string, not a float. This silently breaks every calculation that relies on the number.
- Enforcement: `tests/unit/test_yaml_config.py` checks that `load_yaml_spec` parses `1.0e6`, `5e13`, and `3.156e7` as `float`.
- Date: 2026-04-15

## position-projection-for-1d-engines

- Rule: When the workflow runner passes positions from a 3-D YAML spec (`position_m: [x, y, z]`) to a 1-D physics engine, it must explicitly extract the relevant axis component (e.g., `pos[2]` for the z-axis). Never pass the full 3-D vector.
- Why: passing a list to a scalar-expecting argument causes a silent NumPy broadcasting error — the geometry check `rec > src` evaluates element-wise, and incorrect receptor positions are used.
- Enforcement: `tests/integration/test_regression.py` exercises the full runner stack end-to-end and would catch this category of error.
- Date: 2026-04-15

## scipy-imports-must-be-conditional

- Rule: Any module that imports scipy at module-level must be wrapped in a `try/except ImportError` in its `__init__.py`. Non-scipy modules (e.g., `alarp.zoning`) must remain importable without scipy.
- Why: the CI linting environment, sandbox runners, and lightweight deployments may not have scipy. An eager import cascades through `__init__.py` and makes the entire package un-importable.
- Enforcement: `tests/unit/test_import_without_scipy.py` (can be skipped in envs with scipy); also verified by the sandbox runner that has only numpy.
- Date: 2026-04-15

## runner-import-path-must-match-module-location

- Rule: When importing a symbol in the runner, always import from the actual defining module path, not from a re-export path that might not exist. Specifically: `from pyshield_smr.alarp.zoning import assign_zone`, not `from pyshield_smr.shielding.zoning import assign_zone`.
- Why: a wrong import path raises `ModuleNotFoundError` at runner startup and makes the entire workflow unusable.
- Enforcement: `python -c "from pyshield_smr.workflow.runner import Runner"` is run in CI as a smoke test.
- Date: 2026-04-15

---

## physics-changelog-required

- Rule: Any change that could move a dose result — cross-section data, buildup factors, dose conversion, geometry conventions, default parameters — must add an entry to `docs/theory/PHYSICS_CHANGELOG.md` in the same commit, stating the physics reason and the regression impact.
- Why: prevents silent physics drift between report versions.
- Enforcement: `tasks/audit_process.py` checks that commits touching `pyshield_smr/physics/` or `pyshield_smr/shielding/` also touch the changelog.
- Date: 2026-04-14

## units-are-explicit

- Rule: No numeric literal with physical meaning may appear in code without a unit comment or a constant from `pyshield_smr.physics.units`. Public function signatures must state units in the docstring.
- Why: unit errors are the most common source of wrong answers in shielding analysis.
- Enforcement: review-gate. A linter rule is planned (see `ruff` config) but not yet strict.
- Date: 2026-04-14

## uq-never-optional-for-reports

- Rule: A workflow that emits a `report.html` / `report.md` must either include a UQ block or explicitly opt out with a `uq.skip_reason` string in the YAML spec. Opt-outs are recorded in the QA manifest.
- Why: point-estimate dose numbers are misleading in a safety case.
- Enforcement: `pyshield_smr.workflow.schema` enforces the rule; tests cover both paths.
- Date: 2026-04-14

## data-hashes-in-manifest

- Rule: Every nuclear-data file consumed during an analysis must be hashed and recorded in the QA manifest.
- Why: regulator- and reviewer-traceability; protects against silent data swaps.
- Enforcement: `pyshield_smr.workflow.quality.build_qa_manifest` + unit test.
- Date: 2026-04-14

## copy-user-spec-into-qa

- Rule: The exact YAML spec that produced a report is copied into the report folder, not just referenced by path.
- Why: the spec on disk can change after the run; reports must be self-contained.
- Enforcement: `Runner.execute` unit test checks the copy.
- Date: 2026-04-14

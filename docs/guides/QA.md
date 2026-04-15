# Quality Assurance, Governance & Reproducibility

## Overview

PyShield-SMR implements comprehensive QA practices to ensure **reproducibility, traceability, and auditability** of radiation analyses. This document explains:

1. **What is governed**: Physics, data, code, processes
2. **How governance works**: Multi-agent specialist system with automated checks
3. **How to verify analyses**: QA manifest, regression testing, audit trail
4. **How to extend safely**: Handoff protocols, change documentation

## The Multi-Agent Specialist System

PyShield-SMR uses a **decentralized, multi-agent** governance model inspired by real-world nuclear engineering teams:

| Role | Owns | Verifies | Handoff To |
|------|------|----------|-----------|
| **Physics Governor** | Physics constants, cross sections, decay data, PHYSICS_CHANGELOG | Numerical tolerances, unit consistency, nuclear data accuracy | Transport Author (for regression validation) |
| **Transport Author** | Monte Carlo and point-kernel engines, tallies, variance reduction | Algorithm correctness, variance reduction effectiveness, numerical stability | QA Governor (for test coverage) |
| **Workflow Author** | YAML schema, runner orchestration, CLI | Schema stability, spec validation, user input handling | QA Governor (for integration tests) |
| **Technical Author** | Reports, documentation, external communication | Clarity, accuracy, completeness of explanations | QA Governor (doc review) |
| **QA Governor** | Tests, audit_process.py, CI/CD, pre-commit hooks | Code quality (ruff, mypy), test coverage, governance compliance | Team (final sign-off) |

**Key principle**: Each specialist owns a domain and certifies correctness within that domain. Handoffs include explicit "return points" (how the next specialist signals issues back).

See `tasks/agents/registry.md` for current agent assignment, operating playbooks, and logbooks.

## Automated Governance Checks

Every commit and analysis run is validated by `tasks/audit_process.py`:

```bash
python tasks/audit_process.py --verbose
```

**12 governance checks** (fail = exit code 1, all pass = exit code 0):

1. **Required files present**: AGENTS.md, RUNBOOK.md, docs/theory/, data/
2. **Architecture links**: AGENTS.md → PROCESS_ARCHITECTURE.md, RUNBOOK.md → audit_process.py
3. **Specialist routing doctrine**: Agents table matches registry
4. **Agent registry consistency**: All agents have config.md, playbook.md, logbook.md
5. **Memory freshness**: tasks/memory/MEMORY.md updated within 180 days
6. **Process state review dates**: Check todos not overdue
7. **Todo review sections**: Each todo item has review date and justification
8. **Physics changelog non-empty**: PHYSICS_CHANGELOG entries document all physics changes
9. **YAML schema version present**: In pyshield_smr/workflow/schema.py
10. **Data directory populated**: All required data files hashed and present
11. **Tests discoverable**: test_*.py files in tests/unit/ and tests/integration/
12. **QA manifest hashing**: All data files have SHA-256 digests recorded

**Pre-commit integration**: `git commit` will not proceed until `audit_process.py` passes.

## QA Manifest: The Analysis Record

Every completed analysis generates a **QA manifest** (JSON file):

```json
{
  "timestamp": "2026-04-14T14:32:15.123456Z",
  "runtime_seconds": 42.56,
  "pyshield_version": "0.1.0",
  "code_version": "commit abc123def",
  "platform": {
    "python_version": "3.11.2",
    "os": "Linux",
    "os_version": "5.15.0",
    "machine": "x86_64"
  },
  "data_files": {
    "data/cross_sections/photon_mass_attenuation.json": "a1b2c3d4e5f6...",
    "data/decay_chains/short.json": "f6g7h8i9j0k1...",
    "data/buildup_factors/taylor_two_term.json": "l2m3n4o5p6q7..."
  },
  "warnings": [
    "Monte Carlo relative error 0.023 exceeds target 0.01"
  ],
  "analysis_metadata": {
    "case_name": "Lead-lined container 100mm",
    "analyst": "John Doe",
    "engine": "point_kernel",
    "dose_rate_sv_per_h": 1.234e-6,
    "zone": "supervised"
  }
}
```

### Why SHA-256 Hashing?

Data file hashes prevent **silent data corruption**:

- **Scenario 1**: Analyst updates `photon_mass_attenuation.json` from NIST XCOM
- **Manifest check**: If hash changes, audit system flags it
- **Traceability**: Months later, we can verify the exact data file used

This is the nuclear engineering **gold standard** for data provenance.

### Reading the Manifest

```bash
# View manifest from latest analysis
cat reports/*/qa_manifest.json | jq .

# Extract dose rate
cat reports/*/qa_manifest.json | jq '.analysis_metadata.dose_rate_sv_per_h'

# Check if warnings present
cat reports/*/qa_manifest.json | jq '.warnings | length'
```

### Manifest Integration with Reports

The manifest is automatically appended to the end of each HTML report:

```html
<!-- ... analysis results ... -->

<hr>
<h2>QA Manifest</h2>
<pre id="qa-manifest">
{JSON manifest here}
</pre>
```

This ensures the manifest travels with the report (no separate files to lose).

## Regression Testing

Regression tests validate that code changes don't silently break physics:

```bash
# Run integration tests (includes regression checks)
pytest tests/integration/ -v

# View regression values (expected results)
cat tests/integration/regression_values.yaml
```

**Regression values** (YAML) codify expected results for benchmark cases:

```yaml
point_kernel_lead_slab_5cm:
  case: examples/01_point_kernel_shielding/config.yaml
  expected_dose_rate_sv_per_h: 1.45e-5
  tolerance_percent: 5.0  # Allow ±5% variation
  notes: "Co-60 1 MBq behind 5 cm lead at 1 m"

monte_carlo_transmission_1mev:
  case: examples/02_monte_carlo_transmission/config.yaml
  expected_transmission: 0.0032
  tolerance_percent: 10.0  # MC has ±√N statistical error
  n_histories_min: 1e6  # Require >1M histories for this precision
```

**When regression fails**:

1. **Magnitude ±5% or less**: OK (expected variation, likely numerical precision)
2. **Magnitude ±5–10%**: Investigate
   - Did physics change? (e.g., buildup factor formula)
   - Did data change? (e.g., updated NIST XCOM)
   - Did infrastructure change? (e.g., Python version floating-point rounding)
3. **Magnitude > 10%**: **STOP** — This is a regression
   - Something broke the physics
   - Revert commit, debug, re-test

**Workflow** (for developers):

```bash
# Make physics change (e.g., fix Klein-Nishina sampling)
# Run tests
pytest tests/integration/ -v

# If regression test fails:
# 1. Run affected example manually
#    python -m pyshield_smr.cli.main run examples/02_monte_carlo_transmission/config.yaml
# 2. Compare dose rate to regression_values.yaml
# 3. If correct but different: update regression value with justification
#    (e.g., "Fixed Klein-Nishina sampling; results now match literature to ±0.5%")
# 4. Re-run tests; should pass
# 5. Commit with message: "Update Klein-Nishina sampling regression values (…)"
```

## Testing Strategy

### Unit Tests (tests/unit/)

Fast, isolated tests of individual modules:

```bash
pytest tests/unit/ -v  # Should complete in <10 seconds
```

**Coverage**:
- Physics correctness (constants match CODATA 2018 to ±0.1%)
- Interpolation (log-log mass attenuation within ±1%)
- Dose conversion (ICRP-74 flux-to-dose within ±2%)
- Transport geometry (ray tracing, mean free paths)
- Tally variance estimation (relative error estimates match theory)
- ALARP convergence (optimizer finds minimum within tolerance)

**Example** (test_physics_constants.py):
```python
def test_avogadro_codata_2018(self):
    """AVOGADRO should match CODATA 2018."""
    reference = 6.02214076e23
    assert abs(AVOGADRO - reference) / reference < 0.001  # ±0.1%
```

### Integration Tests (tests/integration/)

End-to-end workflows exercising multiple components:

```bash
pytest tests/integration/ -v  # Should complete in <1 minute
```

**Coverage**:
- Full point-kernel analysis (spec → dose rate)
- Monte Carlo transmission (convergence, FOM)
- Activation decay chain (Bateman solver)
- UQ sampling (Latin hypercube, Morris effects)
- ALARP optimization (converges to expected solution)
- Regression validation (dose rates within tolerance)

**Example** (test_point_kernel_lead.py):
```python
def test_point_kernel_co60_lead_regression(self):
    """Point-kernel Co-60 through 5 cm lead matches regression value."""
    spec = load_yaml("examples/01_point_kernel_shielding/config.yaml")
    runner = Runner(spec)
    state = runner.execute()
    
    expected = 1.45e-5  # From regression_values.yaml
    tolerance = 0.05   # ±5%
    
    assert abs(state.dose_rate_sv_per_h - expected) < tolerance * expected
```

## Data Provenance

All nuclear data files include `.meta.json` siblings:

```json
// data/cross_sections/photon_mass_attenuation.meta.json
{
  "source": "NIST XCOM online database",
  "url": "https://physics.nist.gov/PhysRefData/Xcom/",
  "retrieval_date": "2026-04-01",
  "accuracy_target": "Within ~2% of NIST tabulated values",
  "materials": ["water", "concrete", "iron", "lead", "borated_polyethylene", "air"],
  "energy_range_MeV": [0.1, 10.0],
  "notes": "Pedagogical reproduction for portfolio; production analyses should use official ENDF/B data"
}
```

**QA check**: If analyst updates a data file, they must:
1. Update `.meta.json` with new retrieval date and source
2. Re-hash the file (SHA-256 updates automatically in manifest)
3. Include change in CHANGELOG.md with justification

## Physics Changelog

All physics changes are documented in `PHYSICS_CHANGELOG.md`:

```markdown
## v0.1.0 (2026-04-14)

### Physics Changes

- **Klein-Nishina sampling (commit abc123)**: Fixed scattering angle distribution
  - Previous: Used incorrect Kahn rejection method rejection probability
  - New: Corrected per Evans (1955) eq. 2.14
  - Impact: MC transmission results now within 0.5% of point-kernel
  - Regression: Updated tests/integration/regression_values.yaml
  
- **Buildup factor interpolation (commit def456)**: Changed from linear to log-linear
  - Previous: Linear interpolation in energy space
  - New: Log-linear interpolation (physics more accurate on log-log scale)
  - Impact: Point-kernel dose rates change by ±2% depending on energy
  - Regression: Updated expected values for examples/01, 02
```

**Mandatory practice**: Physics Governor must write a changelog entry *before* coding any change.

Format:
```
- **[Component] [What changed] (commit [hash])**:
  - Previous: [How it was]
  - New: [How it is now]
  - Impact: [What users observe]
  - Regression: [Which tests updated, why]
```

## Regulatory Compliance (ALARP)

For safety-critical analyses, the framework must demonstrate **ALARP** (As Low As Reasonably Practicable):

1. **Optimization**: Shielding design minimizes collective dose subject to cost
2. **Justification**: Why this thickness? Why not more/less?
3. **Uncertainty**: How sensitive is design to parameter changes?
4. **Documentation**: Every decision recorded with rationale

**QA checklist for ALARP analyses**:
- [ ] Optimizer converged (exit flag = success)
- [ ] Constraint satisfied (dose_rate ≤ threshold)
- [ ] Sensitivity analysis included (±10% thickness variation)
- [ ] UQ performed (source term uncertainty propagated)
- [ ] Assumptions stated (geometry, material properties)
- [ ] Alternatives considered (why not different shielding material?)

## Audit Trail

Every analysis leaves a complete audit trail:

```
reports/2026-04-14_14-32-15_Lead_lined_container/
├── report.md                # Human-readable summary
├── report.html              # Styled HTML with embedded manifest
├── qa_manifest.json         # Machine-readable QA record
└── spec_used.yaml           # Input spec (for audit)
```

**Full traceability**:
1. **Spec** (spec_used.yaml) → What did user ask for?
2. **Code** (git commit) → What version ran this?
3. **Data** (qa_manifest.json hashes) → What nuclear data was used?
4. **Results** (report.md/.html) → What did we get?
5. **Metadata** (qa_manifest.json) → When, where, by whom?

**Audit verification**:
```bash
# Check if analysis is reproducible
# 1. Get analysis folder
REPORT_DIR="reports/2026-04-14_14-32-15_Lead_lined_container"

# 2. Extract spec
SPEC="$REPORT_DIR/spec_used.yaml"

# 3. Re-run analysis
python -m pyshield_smr.cli.main run "$SPEC" --output-dir /tmp/rerun

# 4. Compare QA manifests
diff "$REPORT_DIR/qa_manifest.json" /tmp/rerun/qa_manifest.json
# → Should match exactly (same timestamps should differ, but data hashes identical)
```

## Continuous Integration (CI)

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every commit:

```yaml
- Matrix: Python 3.10, 3.11, 3.12
- Lint: ruff check + ruff format --check
- Type check: mypy (non-strict)
- Tests: pytest unit + integration
- Governance: audit_process.py --verbose
```

**All must pass** before merge to main:
- If any lint error: fix + recommit
- If any test fails: debug + recommit
- If any governance check fails: investigate + fix + recommit

**CI failure example**:
```
❌ FAILED tests/integration/test_point_kernel.py::test_regression_lead_slab
Expected: 1.45e-5 Sv/h
Got: 1.52e-5 Sv/h (4.8% difference, within 5% tolerance) → PASS

✗ FAILED tests/integration/test_monte_carlo.py::test_transmission_convergence
Relative error: 0.034 (3.4%), target: 0.01 (1%) → FAIL
→ Need more histories (1e6 → 1e7) or accept lower precision
```

## Best Practices for Analysts

### When Running an Analysis

1. **Validate spec first**:
   ```bash
   python -m pyshield_smr.cli.main validate my_spec.yaml
   ```

2. **Note any warnings in QA manifest**:
   ```bash
   cat reports/*/qa_manifest.json | jq '.warnings'
   ```

3. **Keep original spec with results**:
   ```bash
   cp my_spec.yaml reports/*/spec_original.yaml
   ```

4. **Document assumptions**:
   - Edit spec.yaml with comments explaining choices
   - Include in report_format (rendered in output)

### When Changing Code

1. **Physics change?** → Write PHYSICS_CHANGELOG entry first
2. **Data change?** → Update .meta.json, re-hash data file
3. **Schema change?** → Update SCHEMA_VERSION, document migration path
4. **New test?** → Add to tests/unit/ or tests/integration/
5. **Regression expected?** → Update regression_values.yaml with justification

### When Reviewing Results

1. **Check QA manifest**:
   - Timestamp reasonable? (not 2 years old)
   - Data files intact? (hashes match data/ folder)
   - Platform compatible? (Python 3.10+, Linux/macOS/Windows)
   - Warnings present? (investigate any warnings)

2. **Check assumptions**:
   - Is geometry realistic? (not simplified beyond acceptability)
   - Are uncertainties quantified? (single point-estimate is risky)
   - Is ALARP considered? (or is design suboptimal?)

3. **Cross-check with literature**:
   - Run same case with MCNP6, SCALE, or published examples
   - Expect ±5–10% agreement (buildup factor uncertainty, geometry differences)

## Summary

PyShield-SMR implements **enterprise-grade governance** for radiation analyses:

- **Reproducibility**: SHA-256 data hashing, spec archival, full audit trail
- **Traceability**: QA manifest, physics changelog, regression testing
- **Auditability**: Automated governance checks, multi-agent specialist system, pre-commit hooks
- **Transparency**: Comprehensive documentation, theory papers, code comments

This approach demonstrates the **nuclear engineering mindset**: not just "does it work?" but "can I prove it works, and can someone else reproduce it in 5 years?"

---

**For questions**: See AGENTS.md (specialist contacts), RUNBOOK.md (standard workflows), or theory docs (physics explanations).

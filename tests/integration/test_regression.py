"""Integration regression tests for PyShield-SMR.

These tests run the complete analysis workflow (YAML spec → transport → dose rate)
for each documented example and compare results against the values in
``tests/integration/regression_values.yaml``.

Regression policy (see AGENTS.md §"Verification Before Done"):
- Difference ≤ 5%: PASS — numerical precision variation.
- Difference 5–10%: INVESTIGATE — check whether a physics change was intended.
- Difference > 10%: FAIL — physics regression or data corruption.

Running:
    pytest tests/integration/ -v

Note: ALARP and UQ are disabled for determinism. Only point-kernel examples are
tested here because Monte Carlo integration into the runner is pending (v0.2).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

# Silence runner's operational logging during tests
logging.disable(logging.WARNING)

ROOT = Path(__file__).resolve().parents[2]
REG_FILE = Path(__file__).parent / "regression_values.yaml"


def _load_regression_values() -> Dict[str, Any]:
    return yaml.safe_load(REG_FILE.read_text(encoding="utf-8"))["cases"]


def _run_spec(spec_path: Path, disable_alarp: bool = True, disable_uq: bool = True) -> Any:
    """Load a YAML spec and run it; return RunnerState."""
    from pyshield_smr.io.yaml_config import load_yaml_spec
    from pyshield_smr.workflow.runner import Runner

    spec = load_yaml_spec(spec_path)

    # Disable optional post-processors for determinism
    if disable_alarp:
        spec.pop("alarp", None)
    if disable_uq:
        spec.pop("uncertainty", None)

    # Point-kernel is 1-D; collapse multi-receptor specs to first receptor
    if isinstance(spec.get("receptor"), list):
        spec["receptor"] = spec["receptor"][0]

    runner = Runner(spec)
    return runner.execute()


# ---------------------------------------------------------------------------
# Parametrised regression test
# ---------------------------------------------------------------------------

_REG = _load_regression_values()


@pytest.mark.parametrize("case_name,case", list(_REG.items()))
def test_regression(case_name: str, case: Dict[str, Any]) -> None:
    """Run the spec and compare dose rate to the regression value."""
    spec_path = ROOT / case["spec"]

    # Skip if spec doesn't exist (guards against future removal)
    if not spec_path.exists():
        pytest.skip(f"Spec file not found: {spec_path}")

    state = _run_spec(spec_path)

    # Runner must complete without fatal errors
    assert state.errors == [], (
        f"[{case_name}] Runner reported errors: {state.errors}"
    )

    dose = state.dose_rate_sv_per_h
    assert dose is not None, f"[{case_name}] dose_rate_sv_per_h is None"
    assert dose > 0.0, f"[{case_name}] dose rate must be positive, got {dose}"

    expected = float(case["expected_dose_rate_sv_per_h"])
    tol = float(case["tolerance_percent"]) / 100.0

    rel_diff = abs(dose - expected) / expected
    assert rel_diff <= tol, (
        f"[{case_name}] dose rate regression failure:\n"
        f"  computed : {dose:.6e} Sv/h\n"
        f"  expected : {expected:.6e} Sv/h\n"
        f"  |diff|   : {rel_diff * 100:.2f}%  (tolerance: {tol * 100:.1f}%)"
    )


@pytest.mark.parametrize("case_name,case", list(_REG.items()))
def test_zone_assignment(case_name: str, case: Dict[str, Any]) -> None:
    """Zone must match the expected zone from the regression file."""
    spec_path = ROOT / case["spec"]
    if not spec_path.exists():
        pytest.skip(f"Spec file not found: {spec_path}")

    state = _run_spec(spec_path)

    expected_zone = case["zone"]
    assert state.zone == expected_zone, (
        f"[{case_name}] zone mismatch: got {state.zone!r}, expected {expected_zone!r}"
    )


# ---------------------------------------------------------------------------
# Smoke tests for runner infrastructure
# ---------------------------------------------------------------------------

def test_runner_import_smoke() -> None:
    """Runner must be importable without scipy (alarp.zoning bypass check)."""
    from pyshield_smr.workflow.runner import Runner  # noqa: F401 — import is the test
    assert Runner is not None


def test_runner_produces_qa_manifest() -> None:
    """Completed runner must attach a populated QA manifest."""
    spec_path = ROOT / "examples/01_point_kernel_shielding/config.yaml"
    if not spec_path.exists():
        pytest.skip("Example 01 not found")

    state = _run_spec(spec_path)
    assert state.qa_manifest is not None, "QA manifest is None"
    assert len(state.qa_manifest.data_files) > 0, "QA manifest has no data file hashes"


def test_runner_runtime_recorded() -> None:
    """Runner must record non-zero runtime."""
    spec_path = ROOT / "examples/01_point_kernel_shielding/config.yaml"
    if not spec_path.exists():
        pytest.skip("Example 01 not found")

    state = _run_spec(spec_path)
    assert state.runtime_seconds > 0.0


def test_regression_values_file_exists() -> None:
    """Regression values file must be present and non-empty."""
    assert REG_FILE.exists(), f"Regression values file missing: {REG_FILE}"
    cases = _load_regression_values()
    assert len(cases) >= 1, "Regression values file has no cases"

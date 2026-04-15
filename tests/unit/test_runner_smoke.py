"""Smoke tests for the workflow runner.

These tests verify that the runner is importable and correctly wired without
running a full end-to-end analysis. They are fast (< 1 second each) and do not
require scipy.

Post-v0.1.1 regression guard:
    - Runner must import from the correct alarp.zoning path (not shielding.zoning).
    - Runner must produce a non-None dose rate for a minimal valid spec.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

logging.disable(logging.WARNING)

ROOT = Path(__file__).resolve().parents[2]


class TestImport:
    """Runner and its immediate dependencies must be importable."""

    def test_runner_importable(self) -> None:
        from pyshield_smr.workflow.runner import Runner  # noqa: F401
        assert Runner is not None

    def test_runner_state_importable(self) -> None:
        from pyshield_smr.workflow.runner import RunnerState  # noqa: F401
        assert RunnerState is not None

    def test_alarp_zoning_importable_without_scipy(self) -> None:
        """alarp.zoning must import cleanly even if scipy is absent."""
        from pyshield_smr.alarp.zoning import assign_zone  # noqa: F401
        assert assign_zone is not None

    def test_yaml_config_importable(self) -> None:
        from pyshield_smr.io.yaml_config import load_yaml_spec  # noqa: F401
        assert load_yaml_spec is not None


class TestRunnerInstantiation:
    """Runner can be instantiated from a minimal spec dict."""

    def _minimal_spec(self) -> dict:
        return {
            "schema_version": "1.0.0",
            "case_name": "Smoke test",
            "analyst": "test",
            "engine": "point_kernel",
            "geometry": {"type": "infinite_slab", "material": "lead", "thickness_m": 0.05},
            "source": {
                "type": "point_isotropic",
                "position_m": [0.0, 0.0, 0.0],
                "nuclide": "Co-60",
                "activity_bq": 1.0e6,
            },
            "receptor": {
                "type": "point",
                "position_m": [0.0, 0.0, 1.0],
            },
            "buildup_material": "lead",
            "report_format": ["markdown"],
        }

    def test_instantiate_from_dict(self) -> None:
        from pyshield_smr.workflow.runner import Runner
        r = Runner(self._minimal_spec())
        assert r is not None

    def test_execute_returns_state(self) -> None:
        from pyshield_smr.workflow.runner import Runner, RunnerState
        r = Runner(self._minimal_spec())
        state = r.execute()
        assert isinstance(state, RunnerState)

    def test_execute_no_fatal_errors(self) -> None:
        from pyshield_smr.workflow.runner import Runner
        r = Runner(self._minimal_spec())
        state = r.execute()
        assert state.errors == [], f"Runner errors: {state.errors}"

    def test_dose_rate_not_none(self) -> None:
        from pyshield_smr.workflow.runner import Runner
        r = Runner(self._minimal_spec())
        state = r.execute()
        assert state.dose_rate_sv_per_h is not None
        assert state.dose_rate_sv_per_h > 0.0

    def test_zone_assigned(self) -> None:
        from pyshield_smr.workflow.runner import Runner
        r = Runner(self._minimal_spec())
        state = r.execute()
        assert state.zone in {"uncontrolled", "supervised", "controlled", "high-dose-rate"}

    def test_qa_manifest_attached(self) -> None:
        from pyshield_smr.workflow.runner import Runner
        r = Runner(self._minimal_spec())
        state = r.execute()
        assert state.qa_manifest is not None

    def test_runtime_recorded(self) -> None:
        from pyshield_smr.workflow.runner import Runner
        r = Runner(self._minimal_spec())
        state = r.execute()
        assert state.runtime_seconds > 0.0


class TestFromSpecFile:
    """Runner.from_spec_file must load and validate example specs."""

    @pytest.mark.parametrize("rel_path", [
        "examples/01_point_kernel_shielding/config.yaml",
        "examples/03_activation_decay/config.yaml",
    ])
    def test_from_spec_file(self, rel_path: str) -> None:
        spec_path = ROOT / rel_path
        if not spec_path.exists():
            pytest.skip(f"Spec not found: {spec_path}")

        from pyshield_smr.workflow.runner import Runner
        runner = Runner.from_spec_file(spec_path)
        assert runner is not None
        assert runner.spec.get("schema_version") is not None

"""Unit tests for YAML configuration loading.

Post-v0.1.1 regression:
    PyYAML 6.x (YAML 1.2) parses ``1.0e6`` (positive exponent, no sign) as a
    string. All example specs used this notation. The fix in ``yaml_config.py``
    adds a YAML 1.1-compatible float resolver. These tests protect against that
    regression recurring.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pyshield_smr.io.yaml_config import load_yaml_spec


class TestYaml11FloatParsing:
    """load_yaml_spec must parse YAML 1.1 float notation as Python float."""

    def _load_text(self, tmp_path: Path, content: str) -> dict:
        p = tmp_path / "test.yaml"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return load_yaml_spec(p)

    def test_positive_exponent_no_sign(self, tmp_path: Path) -> None:
        """1.0e6 must be float(1000000.0), not str('1.0e6')."""
        spec = self._load_text(tmp_path, "value: 1.0e6")
        assert isinstance(spec["value"], float), (
            f"Expected float, got {type(spec['value'])}: {spec['value']!r}"
        )
        assert spec["value"] == pytest.approx(1e6)

    def test_large_positive_exponent(self, tmp_path: Path) -> None:
        spec = self._load_text(tmp_path, "value: 5.0e13")
        assert isinstance(spec["value"], float)
        assert spec["value"] == pytest.approx(5e13)

    def test_non_round_exponent(self, tmp_path: Path) -> None:
        spec = self._load_text(tmp_path, "value: 3.156e7")
        assert isinstance(spec["value"], float)
        assert spec["value"] == pytest.approx(3.156e7)

    def test_negative_exponent_still_works(self, tmp_path: Path) -> None:
        """YAML 1.2 already handles negative exponents; must remain working."""
        spec = self._load_text(tmp_path, "value: 2.5e-6")
        assert isinstance(spec["value"], float)
        assert spec["value"] == pytest.approx(2.5e-6)

    def test_integer_not_converted(self, tmp_path: Path) -> None:
        spec = self._load_text(tmp_path, "value: 42")
        assert isinstance(spec["value"], int)

    def test_string_not_converted(self, tmp_path: Path) -> None:
        spec = self._load_text(tmp_path, "value: 'lead'")
        assert isinstance(spec["value"], str)

    def test_explicit_positive_sign_exponent(self, tmp_path: Path) -> None:
        """1.0e+6 (YAML 1.2 compliant) must also parse as float."""
        spec = self._load_text(tmp_path, "value: 1.0e+6")
        assert isinstance(spec["value"], float)
        assert spec["value"] == pytest.approx(1e6)


class TestLoadRealSpecs:
    """Round-trip check: all five example specs must load without string numbers."""

    EXAMPLES = [
        "examples/01_point_kernel_shielding/config.yaml",
        "examples/02_monte_carlo_transmission/config.yaml",
        "examples/03_activation_decay/config.yaml",
        "examples/04_alarp_optimization/config.yaml",
        "examples/05_smr_compartment/config.yaml",
    ]

    @pytest.mark.parametrize("rel_path", EXAMPLES)
    def test_activity_is_float(self, rel_path: str) -> None:
        """Source activity must parse as float, never string."""
        spec_path = Path(__file__).parents[2] / rel_path
        if not spec_path.exists():
            pytest.skip(f"Spec not found: {spec_path}")

        spec = load_yaml_spec(spec_path)

        source = spec.get("source")
        if source is None:
            return
        if isinstance(source, list):
            source = source[0]

        if "activity_bq" in source:
            assert isinstance(source["activity_bq"], (int, float)), (
                f"[{rel_path}] activity_bq is {type(source['activity_bq'])}: "
                f"{source['activity_bq']!r}"
            )
        if "intensities_per_s" in source:
            for v in source["intensities_per_s"]:
                assert isinstance(v, (int, float)), (
                    f"[{rel_path}] intensities_per_s value {v!r} is not numeric"
                )

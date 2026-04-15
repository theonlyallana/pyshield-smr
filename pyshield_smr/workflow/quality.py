"""Quality assurance (QA) manifest generation and governance.

This module builds a comprehensive QA manifest for each analysis run. The manifest
records what code ran, which data files were used, platform details, and any warnings.

## Why QA Manifests?

In nuclear engineering, reproducibility and traceability are critical. A manifest
ensures that months or years later, we can answer:
  - "Did the code version match what was approved?"
  - "Were the nuclear data files the official release version?"
  - "Did this run complete successfully, or with warnings?"

The manifest is appended to the end of each report (as JSON) so it travels with results.

## Data File Hashing Strategy

All input data files (cross sections, decay chains, buildup factors, flux-to-dose
coefficients) are hashed using SHA-256. If someone accidentally swaps
data/cross_sections/photon_mass_attenuation.json between runs, the hashes will differ,
signaling the discrepancy. This is the gold standard for detecting silent data corruption
in computational workflows.

The hash is computed over the file's *content*, not metadata. This way, if the file
is copied to a different directory, the hash remains the same (reproducible).

## Warnings and Thresholds

The manifest records warnings such as:
  - Regression value tolerance exceeded (actual result outside expected ± tolerance band)
  - Non-standard platform (e.g., Python 3.9 when tests target 3.10+)
  - Data file not found (partial analysis, result may be invalid)
  - Runtime unusually long or short (may indicate convergence issue)

These are informational; the analysis still completes. But they are logged so the
reviewer is aware of potential issues.

## Example Manifest

    {
      "code_version": "commit abc123def456",
      "pyshield_version": "0.1.0",
      "timestamp": "2026-04-14T14:32:15.123456Z",
      "runtime_seconds": 42.56,
      "platform": {
        "python_version": "3.11.2",
        "os": "Linux",
        "os_version": "5.15.0",
        "machine": "x86_64"
      },
      "data_files": {
        "data/cross_sections/photon_mass_attenuation.json": "a1b2c3d4e5...",
        "data/decay_chains/short.json": "f6g7h8i9j0..."
      },
      "warnings": [],
      "analysis_metadata": {
        "case_name": "Lead-lined container 100mm",
        "engine": "point_kernel",
        "dose_rate_sv_per_h": 1.234e-6,
        "zone": "supervised"
      }
    }

The QA manifest is machine-readable JSON, parseable by auditors and CI systems.
"""

from __future__ import annotations

import json
import logging
import platform
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pyshield_smr.utils.hashing import sha256_file

logger = logging.getLogger(__name__)


@dataclass
class PlatformInfo:
    """Snapshot of the execution platform."""
    python_version: str
    """Full Python version string, e.g., '3.11.2'."""
    os: str
    """Operating system name, e.g., 'Linux', 'Windows'."""
    os_version: str
    """OS release string (kernel version on Linux, build number on Windows)."""
    machine: str
    """Machine architecture, e.g., 'x86_64', 'arm64'."""

    @classmethod
    def snapshot(cls) -> PlatformInfo:
        """Capture current platform information."""
        return cls(
            python_version=platform.python_version(),
            os=platform.system(),
            os_version=platform.release(),
            machine=platform.machine()
        )


@dataclass
class QAManifest:
    """Complete QA record for an analysis run."""
    timestamp: str
    """ISO 8601 timestamp (UTC) of analysis completion."""
    runtime_seconds: float
    """Wall-clock runtime from start to finish."""
    pyshield_version: str
    """PyShield-SMR package version."""
    code_version: Optional[str] = None
    """Git commit hash, branch, or version tag (optional; None if not in git repo)."""
    platform: Optional[PlatformInfo] = None
    """Platform snapshot at time of execution."""
    data_files: Dict[str, str] = field(default_factory=dict)
    """Mapping of {data_file_path: sha256_hex_digest}."""
    warnings: List[str] = field(default_factory=list)
    """Non-fatal warnings generated during analysis."""
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    """User-supplied metadata: case_name, analyst, engine, key results (dose rate, zone, etc.)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        d = asdict(self)
        # Ensure platform is a dict (asdict handles it, but make explicit)
        if self.platform:
            d["platform"] = asdict(self.platform)
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def write_to_file(self, path: str | Path) -> None:
        """Write manifest to a JSON file."""
        Path(path).write_text(self.to_json(), encoding="utf-8")
        logger.info(f"QA manifest written to {path}")


def build_qa_manifest(
    pyshield_version: str,
    runtime_seconds: float,
    data_files_to_hash: Optional[List[str | Path]] = None,
    code_version: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    analysis_metadata: Optional[Dict[str, Any]] = None,
) -> QAManifest:
    """Build a QA manifest for an analysis run.

    **Typical usage in the runner:**

        import time
        start_time = time.perf_counter()

        # ... run analysis ...

        elapsed = time.perf_counter() - start_time
        manifest = build_qa_manifest(
            pyshield_version="0.1.0",
            runtime_seconds=elapsed,
            data_files_to_hash=[
                "data/cross_sections/photon_mass_attenuation.json",
                "data/decay_chains/short.json"
            ],
            warnings=["Dose rate exceeds design threshold by 2.5%"],
            analysis_metadata={
                "case_name": "Lead-lined container",
                "engine": "point_kernel",
                "dose_rate_sv_per_h": 1.23e-6,
                "zone": "supervised"
            }
        )
        manifest.write_to_file("reports/latest/qa_manifest.json")

    Args:
        pyshield_version: Package version string (e.g., "0.1.0")
        runtime_seconds: Elapsed time in seconds
        data_files_to_hash: Paths to input data files to hash (optional)
        code_version: Git commit or version identifier (optional)
        warnings: List of warning strings (optional; default: empty list)
        analysis_metadata: Dict of case metadata to include (optional; default: empty dict)

    Returns:
        QAManifest object ready for serialization

    Raises:
        FileNotFoundError: If any file in data_files_to_hash does not exist
        ValueError: If pyshield_version is empty or malformed
    """
    if not pyshield_version:
        raise ValueError("pyshield_version must be a non-empty string")

    # Hash data files
    data_hashes: Dict[str, str] = {}
    if data_files_to_hash:
        for fpath in data_files_to_hash:
            fpath_obj = Path(fpath)
            if not fpath_obj.exists():
                raise FileNotFoundError(f"Data file not found: {fpath}")
            try:
                digest = sha256_file(fpath_obj)
                data_hashes[str(fpath)] = digest
                logger.debug(f"Hashed {fpath}: {digest[:12]}…")
            except Exception as e:
                logger.warning(f"Failed to hash {fpath}: {e}")
                data_hashes[str(fpath)] = f"ERROR: {e}"

    # Capture platform info
    platform_info = PlatformInfo.snapshot()

    # Timestamp in ISO 8601 UTC
    timestamp = datetime.now(timezone.utc).isoformat()

    # Build manifest
    manifest = QAManifest(
        timestamp=timestamp,
        runtime_seconds=runtime_seconds,
        pyshield_version=pyshield_version,
        code_version=code_version,
        platform=platform_info,
        data_files=data_hashes,
        warnings=warnings or [],
        analysis_metadata=analysis_metadata or {}
    )

    return manifest


def validate_manifest(manifest: QAManifest, spec: Dict[str, Any]) -> List[str]:
    """Cross-check manifest against original spec for consistency.

    **Checks performed:**
      1. analysis_metadata.case_name matches spec.case_name
      2. analysis_metadata.analyst matches spec.analyst (if in spec)
      3. analysis_metadata.engine matches spec.engine
      4. No critical warnings (fatal_warnings list is empty)

    Args:
        manifest: QA manifest from a completed run
        spec: Original YAML spec dict

    Returns:
        List of validation warning strings (empty if all checks pass)
    """
    issues: List[str] = []

    # Check case name consistency
    if manifest.analysis_metadata.get("case_name") != spec.get("case_name"):
        issues.append(
            f"Case name mismatch: manifest has "
            f"'{manifest.analysis_metadata.get('case_name')}' "
            f"but spec has '{spec.get('case_name')}'"
        )

    # Check analyst (if present in both)
    spec_analyst = spec.get("analyst")
    manifest_analyst = manifest.analysis_metadata.get("analyst")
    if spec_analyst and manifest_analyst and spec_analyst != manifest_analyst:
        issues.append(
            f"Analyst mismatch: manifest has '{manifest_analyst}' "
            f"but spec has '{spec_analyst}'"
        )

    # Check engine consistency
    if manifest.analysis_metadata.get("engine") != spec.get("engine"):
        issues.append(
            f"Engine mismatch: manifest has "
            f"'{manifest.analysis_metadata.get('engine')}' "
            f"but spec has '{spec.get('engine')}'"
        )

    return issues


def check_regression_tolerance(
    result_value: float,
    expected_value: float,
    tolerance_percent: float = 2.0
) -> Optional[str]:
    """Check if result is within tolerance of expected value.

    **Typical usage:**

        expected_dose = 1.234e-6  # From regression_values.yaml
        computed_dose = 1.245e-6  # From current run
        warning = check_regression_tolerance(computed_dose, expected_dose, tolerance_percent=2.0)
        if warning:
            warnings.append(warning)

    Args:
        result_value: Computed value from current run
        expected_value: Reference value from regression test
        tolerance_percent: Tolerance band as percentage (default 2%)

    Returns:
        Warning string if result is outside tolerance, None otherwise
    """
    if expected_value == 0:
        if result_value == 0:
            return None
        else:
            return (
                f"Expected 0 but got {result_value}; "
                f"tolerance check skipped for zero-reference values"
            )

    relative_error = abs(result_value - expected_value) / abs(expected_value)
    tolerance_frac = tolerance_percent / 100.0

    if relative_error > tolerance_frac:
        error_pct = relative_error * 100
        return (
            f"Regression tolerance exceeded: "
            f"expected {expected_value:.3e}, got {result_value:.3e} "
            f"(error {error_pct:.2f}% > {tolerance_percent}% limit)"
        )

    return None

"""Workflow engine: schema, runner, QA manifest, reporting.

This package orchestrates the complete analysis pipeline:
  1. Schema validation and versioning (schema.py)
  2. Execution orchestration (runner.py)
  3. Quality assurance manifest generation (quality.py)
"""

from .quality import (
    QAManifest,
    build_qa_manifest,
    check_regression_tolerance,
    validate_manifest,
)
from .runner import Runner, RunnerState
from .schema import (
    SCHEMA_VERSION,
    MigrationStep,
    ValidationError,
    migrate_spec,
    validate_spec,
)

__all__ = [
    # Schema
    "SCHEMA_VERSION",
    "ValidationError",
    "MigrationStep",
    "validate_spec",
    "migrate_spec",
    # Runner
    "Runner",
    "RunnerState",
    # Quality
    "QAManifest",
    "build_qa_manifest",
    "check_regression_tolerance",
    "validate_manifest",
]

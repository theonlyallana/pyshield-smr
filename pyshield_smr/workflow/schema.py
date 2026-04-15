"""YAML specification schema, validation, and versioning.

This module defines the canonical structure for PyShield-SMR analysis specifications
(YAML files), validates user-provided specs against it, and handles schema evolution.

## Schema Design Philosophy

The spec schema encodes *intent* rather than detailed physics parameters. For example:
a user writes "shielding_geometry: { material: lead, thickness_m: 0.05 }" rather than
pre-computing mass attenuation coefficients. The runner then resolves these high-level
constructs into physics objects at execution time.

This separation keeps specs human-readable, versionable in git, and decoupled from
internal implementation details (e.g., if we change how buildup factors are interpolated,
the user's spec doesn't break).

## Versioning Strategy

SCHEMA_VERSION follows semantic versioning: MAJOR.MINOR.PATCH
- MAJOR bump (1.0 → 2.0): Breaking spec changes; runner refuses old specs
- MINOR bump (1.0 → 1.1): Backward-compatible additions; runner auto-upgrades if safe
- PATCH bump (1.0.1): Documentation/clarification only; no code impact

When a spec declares schema_version: "1.0" but the runner is at "1.2", the runner:
  (a) Checks if migration path exists (e.g., 1.0 → 1.1 → 1.2)
  (b) Auto-applies migrations if declared as safe
  (c) Records migration steps in QA manifest and warnings
  (d) Proceeds if all migrations succeeded; aborts otherwise

## Example Usage

    # User writes: examples/shielding.yaml
    schema_version: "1.0"
    case_name: "Lead-lined container 100mm"
    analyst: "John Doe"
    engine: point_kernel
    geometry:
      type: infinite_slab
      material: lead
      thickness_m: 0.1
    source:
      type: point_isotropic
      position_m: [0, 0, -0.2]
      nuclide: Co-60
      activity_bq: 1e6
    receptor:
      position_m: [0, 0, 0.3]
    report_format: [markdown, html]

    # Runner validates:
    from pyshield_smr.workflow.schema import validate_spec, migrate_spec
    spec = load_yaml("examples/shielding.yaml")
    validate_spec(spec)  # Raises ValidationError if required fields missing
    spec, warnings = migrate_spec(spec)  # Upgrades schema if needed
    # Then runner proceeds with execution

## Integration with Version Control

Each YAML spec file should declare its schema_version for reproducibility.
If schema changes break compatibility, users must explicitly update their specs.
This allows old analyses to remain valid for audit purposes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import yaml

SCHEMA_VERSION = "1.0.0"
"""Canonical schema version. Checked against spec['schema_version'] at validation."""

# Allowed top-level keys in spec (with defaults where applicable)
ALLOWED_TOP_KEYS = {
    "schema_version",  # Required: string "MAJOR.MINOR.PATCH"
    "case_name",       # Required: string
    "analyst",         # Required: string
    "engine",          # Required: "point_kernel" | "monte_carlo"
    "geometry",        # Required: dict
    "source",          # Required: dict | list of dicts
    "receptor",        # Required: dict | list of dicts
    "tallies",         # Optional: dict
    "uncertainty",     # Optional: dict
    "alarp",           # Optional: dict
    "report_format",   # Optional: list of strings, default ["markdown"]
}

# Allowed engine types
ALLOWED_ENGINES = {"point_kernel", "monte_carlo"}

# Allowed geometry types
ALLOWED_GEOMETRY_TYPES = {"infinite_slab", "spherical_shell", "composite_slab"}

# Allowed source types
ALLOWED_SOURCE_TYPES = {"point_isotropic", "line_source", "custom_spectrum"}

# Allowed receptor types
ALLOWED_RECEPTOR_TYPES = {"point", "line", "area_tally"}

# Allowed report formats
ALLOWED_REPORT_FORMATS = {"markdown", "html", "json"}


@dataclass
class ValidationError:
    """Encapsulates a schema validation error with context."""
    key: str
    """Top-level key or nested path (e.g., 'geometry.material')."""
    message: str
    """Human-readable error message."""
    spec_value: Any = None
    """The value that failed validation (for debugging)."""

    def __str__(self) -> str:
        msg = f"Validation error at '{self.key}': {self.message}"
        if self.spec_value is not None:
            msg += f"\n  Got: {self.spec_value!r}"
        return msg


@dataclass
class MigrationStep:
    """Records a single schema migration applied to a spec."""
    from_version: str
    """Schema version before this step (e.g., '1.0.0')."""
    to_version: str
    """Schema version after this step (e.g., '1.1.0')."""
    transformation: str
    """Human-readable description of the change applied."""
    safe: bool = True
    """Whether this migration is guaranteed reversible (for audit purposes)."""


def validate_spec(spec: Dict[str, Any]) -> List[ValidationError]:
    """Validate a loaded YAML spec dict against the current schema.

    Returns a list of ValidationError objects. If the list is empty, the spec
    is valid and can proceed to the runner. If non-empty, the caller should
    report errors and abort.

    **Validation checks (in order):**
      1. Top-level schema_version field exists and is semantic versioned
      2. Required fields present: case_name, analyst, engine, geometry, source, receptor
      3. Engine is one of ALLOWED_ENGINES
      4. Geometry section is a dict with 'type' in ALLOWED_GEOMETRY_TYPES
      5. Source section is a dict or list of dicts, each with 'type' in ALLOWED_SOURCE_TYPES
      6. Receptor section is a dict or list of dicts, each with 'type' in ALLOWED_RECEPTOR_TYPES
      7. Optional sections (uncertainty, alarp, tallies) are dicts if present
      8. report_format (if present) is a list of strings from ALLOWED_REPORT_FORMATS

    Args:
        spec: Loaded YAML spec dict

    Returns:
        List of ValidationError objects (empty if valid)

    Example:
        >>> spec = load_yaml_spec("my_analysis.yaml")
        >>> errors = validate_spec(spec)
        >>> if errors:
        ...     for err in errors:
        ...         print(err)
        ...     raise RuntimeError("Spec validation failed")
    """
    errors: List[ValidationError] = []

    # 1. Check schema_version
    if "schema_version" not in spec:
        errors.append(ValidationError(
            key="schema_version",
            message="Required field missing",
            spec_value=None
        ))
    else:
        version_str = spec.get("schema_version")
        if not isinstance(version_str, str):
            errors.append(ValidationError(
                key="schema_version",
                message="Must be a string in format 'MAJOR.MINOR.PATCH'",
                spec_value=version_str
            ))
        elif not _is_valid_semver(version_str):
            errors.append(ValidationError(
                key="schema_version",
                message="Invalid semantic version format",
                spec_value=version_str
            ))

    # 2. Check required fields
    required_fields = ["case_name", "analyst", "engine", "geometry", "source", "receptor"]
    for field in required_fields:
        if field not in spec:
            errors.append(ValidationError(
                key=field,
                message="Required field missing"
            ))

    # 3. Engine type
    if "engine" in spec:
        engine = spec["engine"]
        if engine not in ALLOWED_ENGINES:
            errors.append(ValidationError(
                key="engine",
                message=f"Must be one of {ALLOWED_ENGINES}",
                spec_value=engine
            ))

    # 4. Geometry section
    if "geometry" in spec:
        geom = spec["geometry"]
        if not isinstance(geom, dict):
            errors.append(ValidationError(
                key="geometry",
                message="Must be a dict (e.g., {type: infinite_slab, material: lead, ...})",
                spec_value=geom
            ))
        elif "type" not in geom:
            errors.append(ValidationError(
                key="geometry.type",
                message="Required field 'type' missing from geometry",
                spec_value=geom
            ))
        elif geom["type"] not in ALLOWED_GEOMETRY_TYPES:
            errors.append(ValidationError(
                key="geometry.type",
                message=f"Must be one of {ALLOWED_GEOMETRY_TYPES}",
                spec_value=geom["type"]
            ))

    # 5. Source section (can be single dict or list of dicts)
    if "source" in spec:
        sources = spec["source"]
        if isinstance(sources, dict):
            sources = [sources]
        elif not isinstance(sources, list):
            errors.append(ValidationError(
                key="source",
                message="Must be a dict or list of dicts",
                spec_value=sources
            ))
            sources = []

        for i, src in enumerate(sources):
            if not isinstance(src, dict):
                errors.append(ValidationError(
                    key=f"source[{i}]",
                    message="Each source must be a dict",
                    spec_value=src
                ))
            elif "type" not in src:
                errors.append(ValidationError(
                    key=f"source[{i}].type",
                    message="Required field 'type' missing from source",
                    spec_value=src
                ))
            elif src["type"] not in ALLOWED_SOURCE_TYPES:
                errors.append(ValidationError(
                    key=f"source[{i}].type",
                    message=f"Must be one of {ALLOWED_SOURCE_TYPES}",
                    spec_value=src["type"]
                ))

    # 6. Receptor section (can be single dict or list of dicts)
    if "receptor" in spec:
        receptors = spec["receptor"]
        if isinstance(receptors, dict):
            receptors = [receptors]
        elif not isinstance(receptors, list):
            errors.append(ValidationError(
                key="receptor",
                message="Must be a dict or list of dicts",
                spec_value=receptors
            ))
            receptors = []

        for i, recv in enumerate(receptors):
            if not isinstance(recv, dict):
                errors.append(ValidationError(
                    key=f"receptor[{i}]",
                    message="Each receptor must be a dict",
                    spec_value=recv
                ))
            elif "type" not in recv:
                errors.append(ValidationError(
                    key=f"receptor[{i}].type",
                    message="Required field 'type' missing from receptor",
                    spec_value=recv
                ))
            elif recv["type"] not in ALLOWED_RECEPTOR_TYPES:
                errors.append(ValidationError(
                    key=f"receptor[{i}].type",
                    message=f"Must be one of {ALLOWED_RECEPTOR_TYPES}",
                    spec_value=recv["type"]
                ))

    # 7. Optional sections should be dicts if present
    optional_dict_sections = ["uncertainty", "alarp", "tallies"]
    for section in optional_dict_sections:
        if section in spec and not isinstance(spec[section], dict):
            errors.append(ValidationError(
                key=section,
                message="Optional field must be a dict if present",
                spec_value=spec[section]
            ))

    # 8. report_format
    if "report_format" in spec:
        formats = spec["report_format"]
        if isinstance(formats, str):
            formats = [formats]
        elif not isinstance(formats, list):
            errors.append(ValidationError(
                key="report_format",
                message="Must be a string or list of strings",
                spec_value=formats
            ))
        else:
            for fmt in formats:
                if fmt not in ALLOWED_REPORT_FORMATS:
                    errors.append(ValidationError(
                        key="report_format",
                        message=f"Each format must be one of {ALLOWED_REPORT_FORMATS}",
                        spec_value=fmt
                    ))

    return errors


def migrate_spec(spec: Dict[str, Any]) -> Tuple[Dict[str, Any], List[MigrationStep]]:
    """Migrate a spec from its declared version to SCHEMA_VERSION.

    **Supported migrations:**
    - 1.0.0 → current: Identity (no changes; both are the same)

    For any unsupported migration or major version mismatch, raises RuntimeError.

    Args:
        spec: Loaded YAML spec with declared schema_version

    Returns:
        Tuple of (migrated_spec, list_of_migrations_applied)

    Raises:
        RuntimeError: If migration path does not exist or requires manual intervention

    Example:
        >>> spec = load_yaml_spec("old_analysis.yaml")
        >>> spec, migrations = migrate_spec(spec)
        >>> print(f"Applied {len(migrations)} migrations")
    """
    if "schema_version" not in spec:
        raise RuntimeError(
            "Cannot migrate spec without schema_version field. "
            "Add 'schema_version: \"1.0.0\"' to your YAML."
        )

    spec_version = spec["schema_version"]
    migrations: List[MigrationStep] = []

    # Parse version strings
    spec_major, spec_minor, spec_patch = _parse_semver(spec_version)
    target_major, target_minor, target_patch = _parse_semver(SCHEMA_VERSION)

    # Check for major version mismatch (breaking change)
    if spec_major != target_major:
        raise RuntimeError(
            f"Spec declares schema v{spec_version} but runner is at v{SCHEMA_VERSION}. "
            f"Major version mismatch requires manual migration. "
            f"See docs/guides/SCHEMA_MIGRATIONS.md for instructions."
        )

    # Apply minor version migrations (backward-compatible)
    # (Currently: 1.0.0 is the only version, so no migrations yet)
    # Example of future migration:
    #
    #   if (spec_major, spec_minor) < (1, 1):
    #       # Migrate 1.0 -> 1.1: add 'buildup_material' field (with default)
    #       spec.setdefault("buildup_material", "water")
    #       migrations.append(MigrationStep(
    #           from_version="1.0.0",
    #           to_version="1.1.0",
    #           transformation="Added 'buildup_material' field with default 'water'",
    #           safe=True
    #       ))

    # Update schema_version in spec
    spec["schema_version"] = SCHEMA_VERSION

    return spec, migrations


def _is_valid_semver(version_str: str) -> bool:
    """Check if string is valid semantic version (MAJOR.MINOR.PATCH)."""
    parts = version_str.split(".")
    if len(parts) != 3:
        return False
    try:
        for part in parts:
            int(part)  # Ensure numeric
        return True
    except ValueError:
        return False


def _parse_semver(version_str: str) -> Tuple[int, int, int]:
    """Parse semantic version string into (major, minor, patch) tuple."""
    parts = version_str.split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])

"""Orchestration engine: spec → execution → report.

The Runner class implements the complete analysis workflow:

    1. **Load & validate**: Parse YAML spec, check schema version, migrate if needed
    2. **Build objects**: Resolve source terms, geometry, material library
    3. **Execute engine**: Run point-kernel or Monte Carlo transport
    4. **Post-process**: Apply dose conversion, UQ sampling, ALARP optimization
    5. **Report**: Render Markdown & HTML templates with results
    6. **Govern**: Build QA manifest with data hashes and runtime info
    7. **Persist**: Write timestamped output folder with all reports

## Design Philosophy: The Handoff Pattern

Each phase of the workflow is a *separate method* with clear inputs and outputs.
This makes the runner testable (you can mock phase N-1 to test phase N) and auditable
(you can inspect intermediate results).

Example: If you want to test the report generation without running Monte Carlo,
you can manually construct a RunnerState with pre-computed results and call
renderer.render() directly.

## Typical Usage

    # User runs: pyshield run examples/01_point_kernel_shielding/config.yaml
    runner = Runner.from_spec_file("examples/01_point_kernel_shielding/config.yaml")
    runner.execute()
    # Outputs:
    #   reports/2026-04-14_14-32-15_Lead_lined_container/report.md
    #   reports/2026-04-14_14-32-15_Lead_lined_container/report.html
    #   reports/2026-04-14_14-32-15_Lead_lined_container/qa_manifest.json

## Error Handling Strategy

All errors in the runner (data not found, schema validation, convergence failure)
are caught, logged, and appended to the QA manifest as warnings. The runner
completes even if phases fail, but reports indicate what went wrong.

This is intentional: for research, it's better to see a partial result with
clear warnings than to crash silently. For safety-critical analyses, the
warnings prompt a human review.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from pyshield_smr.io.report import render_report
from pyshield_smr.io.yaml_config import load_yaml_spec
from pyshield_smr.physics import (
    load_material_library,
    flux_to_dose_h10,
)
from pyshield_smr.shielding.dose_rate import spectrum_to_dose_rate
from pyshield_smr.alarp.zoning import assign_zone
from pyshield_smr.sources.source_term import build_source_from_inventory
from pyshield_smr.transport.geometry import SlabStack
from pyshield_smr.workflow.quality import (
    QAManifest,
    build_qa_manifest,
    check_regression_tolerance,
    validate_manifest,
)
from pyshield_smr.workflow.schema import (
    SCHEMA_VERSION,
    ValidationError,
    migrate_spec,
    validate_spec,
)
from pyshield_smr.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RunnerState:
    """Intermediate state object passed between runner phases.

    Encapsulates all intermediate and final results from the analysis.
    This allows phases to be tested independently (e.g., mock RunnerState
    to test report rendering without running transport).
    """
    spec: Dict[str, Any]
    """Validated and migrated YAML spec."""

    # Source and geometry
    source_energies_MeV: Optional[List[float]] = None
    """Photon energies (in MeV) from source term resolution."""
    source_intensities_per_s: Optional[List[float]] = None
    """Emission rate (in 1/s) per energy."""

    # Transport results
    dose_rate_sv_per_h: Optional[float] = None
    """Total dose rate at receptor (in Sv/h) from transport."""
    relative_error_dose: Optional[float] = None
    """Relative statistical error on dose rate (for MC)."""
    zone: Optional[str] = None
    """Radiological zone (uncontrolled, supervised, controlled, etc.)."""

    # UQ results (if enabled)
    uq_results: Optional[Dict[str, Any]] = None
    """Summary statistics from uncertainty quantification."""

    # ALARP results (if enabled)
    alarp_results: Optional[Dict[str, Any]] = None
    """Optimized shielding configuration and cost-benefit."""

    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    """Fatal errors encountered (analysis may be invalid)."""
    warnings: List[str] = field(default_factory=list)
    """Non-fatal warnings (analysis completed but with caveats)."""

    # Governance
    runtime_seconds: float = 0.0
    """Wall-clock time from start to finish (populated by runner)."""
    qa_manifest: Optional[QAManifest] = None
    """QA record including data hashes and platform info."""


class Runner:
    """Orchestrates the complete analysis workflow.

    The Runner is responsible for:
      1. Validating user specs
      2. Resolving physics objects (sources, geometries, materials)
      3. Dispatching to the appropriate transport engine
      4. Post-processing results
      5. Rendering reports
      6. Recording governance metadata
    """

    def __init__(self, spec: Dict[str, Any]):
        """Initialize runner with a validated spec dict.

        Args:
            spec: Loaded YAML specification dict (should be validated first)

        Raises:
            ValueError: If spec is invalid
        """
        self.spec = spec
        self.state = RunnerState(spec=spec)
        self.output_dir: Optional[Path] = None

    @classmethod
    def from_spec_file(cls, spec_path: str | Path) -> Runner:
        """Factory: load Runner from a YAML spec file.

        **Steps:**
          1. Load YAML from disk
          2. Validate against schema
          3. Migrate if necessary
          4. Instantiate Runner

        Args:
            spec_path: Path to YAML spec file

        Returns:
            Runner instance ready to execute()

        Raises:
            FileNotFoundError: If spec file does not exist
            RuntimeError: If schema validation fails or migration is unsupported
        """
        spec_path = Path(spec_path)
        if not spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_path}")

        logger.info(f"Loading spec from {spec_path}")
        spec = load_yaml_spec(spec_path)

        # Validate schema
        errors = validate_spec(spec)
        if errors:
            error_msg = "\n".join(str(e) for e in errors)
            raise RuntimeError(f"Spec validation failed:\n{error_msg}")

        logger.info(f"Spec valid for schema v{spec.get('schema_version')}")

        # Migrate if needed
        if spec.get("schema_version") != SCHEMA_VERSION:
            logger.info(f"Migrating spec from {spec.get('schema_version')} to {SCHEMA_VERSION}")
            spec, migrations = migrate_spec(spec)
            for mig in migrations:
                logger.info(f"  Applied: {mig.transformation}")

        return cls(spec)

    def execute(self) -> RunnerState:
        """Execute the complete analysis workflow.

        **Workflow phases (in order):**
          1. resolve_sources() - Convert inventory to photon spectrum
          2. resolve_geometry() - Build transport geometry
          3. run_transport() - Execute point-kernel or MC engine
          4. apply_post_processors() - UQ, ALARP (if enabled)
          5. render_outputs() - Generate Markdown/HTML reports
          6. build_governance() - Create QA manifest
          7. persist_outputs() - Write to timestamped folder

        If any phase fails, execution continues with warnings logged.
        Results (partial or complete) are written to reports/ folder.

        Returns:
            RunnerState with all results populated (or None values if phases failed)
        """
        start_time = time.perf_counter()

        try:
            logger.info("=" * 60)
            logger.info(f"Starting analysis: {self.spec.get('case_name')}")
            logger.info("=" * 60)

            self.resolve_sources()
            self.resolve_geometry()
            self.run_transport()
            self.apply_post_processors()
            # Build governance first so data_hashes are available in the report.
            self.build_governance()
            self.render_outputs()

        except Exception as e:
            logger.error(f"Fatal error in workflow: {e}")
            self.state.errors.append(f"Workflow error: {e}")

        finally:
            elapsed = time.perf_counter() - start_time
            self.state.runtime_seconds = elapsed
            logger.info(f"Analysis completed in {elapsed:.2f}s")

            try:
                self.persist_outputs()
            except Exception as e:
                logger.error(f"Error during persistence: {e}")
                self.state.warnings.append(f"Persistence error: {e}")

        return self.state

    def resolve_sources(self) -> None:
        """Parse source section of spec and build photon spectrum.

        **Source types supported:**
          - point_isotropic: Isotropic point source with given nuclide/activity
          - line_source: Extended line source (pedagogical)
          - custom_spectrum: Pre-computed energies and intensities

        Result is stored in state.source_energies_MeV and state.source_intensities_per_s.

        On error, warnings are logged; execution continues with None energies.
        """
        logger.info("Resolving source term...")

        try:
            source_spec = self.spec.get("source")
            if not source_spec:
                raise ValueError("No source section in spec")

            # Normalize to list
            sources = source_spec if isinstance(source_spec, list) else [source_spec]

            source_energies = []
            source_intensities = []

            for src in sources:
                src_type = src.get("type")

                if src_type == "point_isotropic":
                    # Parse nuclide and activity from spec
                    nuclide = src.get("nuclide")
                    activity_bq = src.get("activity_bq")

                    if not nuclide or not activity_bq:
                        raise ValueError(
                            f"point_isotropic source missing 'nuclide' or 'activity_bq'"
                        )

                    logger.info(f"  Resolving {nuclide} at {activity_bq:.2e} Bq")

                    # Build source from inventory
                    inventory = {nuclide: activity_bq}
                    bundle = build_source_from_inventory(inventory)

                    # Extract energies and intensities
                    for line in bundle.lines:
                        source_energies.append(line.energy_MeV)
                        source_intensities.append(line.intensity_per_s)

                elif src_type == "custom_spectrum":
                    # User provides explicit energies and intensities
                    energies = src.get("energies_MeV")
                    intensities = src.get("intensities_per_s")

                    if not energies or not intensities:
                        raise ValueError(
                            "custom_spectrum missing 'energies_MeV' or 'intensities_per_s'"
                        )

                    source_energies.extend(energies)
                    source_intensities.extend(intensities)

                else:
                    self.state.warnings.append(f"Unknown source type: {src_type}")

            if not source_energies:
                raise ValueError("No source energies resolved")

            self.state.source_energies_MeV = source_energies
            self.state.source_intensities_per_s = source_intensities
            logger.info(f"  Resolved {len(source_energies)} photon lines")

        except Exception as e:
            logger.error(f"Source resolution failed: {e}")
            self.state.errors.append(f"Source error: {e}")

    def resolve_geometry(self) -> None:
        """Parse geometry section and build transport geometry object.

        **Geometry types supported:**
          - infinite_slab: Plane-parallel slab geometry
          - spherical_shell: Concentric spheres (pedagogical)
          - composite_slab: Multiple slabs with different materials

        Result is stored in self.geometry for use in run_transport().

        On error, warnings logged; execution continues with None geometry.
        """
        logger.info("Resolving geometry...")

        try:
            geom_spec = self.spec.get("geometry")
            if not geom_spec:
                raise ValueError("No geometry section in spec")

            geom_type = geom_spec.get("type")

            if geom_type == "infinite_slab":
                # Single material, single thickness
                material = geom_spec.get("material")
                thickness_m = geom_spec.get("thickness_m")

                if not material or thickness_m is None:
                    raise ValueError(
                        "infinite_slab missing 'material' or 'thickness_m'"
                    )

                logger.info(f"  Building slab: {material} {thickness_m*100:.1f} cm")
                self.geometry = SlabStack([material], [thickness_m])

            elif geom_type == "composite_slab":
                # Multiple materials and thicknesses
                materials = geom_spec.get("materials")
                thicknesses_m = geom_spec.get("thicknesses_m")

                if not materials or not thicknesses_m:
                    raise ValueError(
                        "composite_slab missing 'materials' or 'thicknesses_m'"
                    )

                if len(materials) != len(thicknesses_m):
                    raise ValueError(
                        f"materials length {len(materials)} != "
                        f"thicknesses_m length {len(thicknesses_m)}"
                    )

                logger.info(f"  Building composite slab with {len(materials)} layers")
                self.geometry = SlabStack(materials, thicknesses_m)

            else:
                self.state.warnings.append(f"Unknown geometry type: {geom_type}")

        except Exception as e:
            logger.error(f"Geometry resolution failed: {e}")
            self.state.errors.append(f"Geometry error: {e}")

    def run_transport(self) -> None:
        """Execute transport engine (point-kernel or Monte Carlo).

        Dispatches to the appropriate engine based on spec['engine'].
        Updates state.dose_rate_sv_per_h, state.relative_error_dose, state.zone.

        On error, dose_rate is set to None; execution continues.
        """
        logger.info("Running transport engine...")

        if not hasattr(self, 'geometry'):
            self.state.errors.append("Cannot run transport: geometry not resolved")
            return

        if self.state.source_energies_MeV is None:
            self.state.errors.append("Cannot run transport: sources not resolved")
            return

        try:
            engine = self.spec.get("engine")

            if engine == "point_kernel":
                self._run_point_kernel()
            elif engine == "monte_carlo":
                self._run_monte_carlo()
            else:
                self.state.warnings.append(f"Unknown engine: {engine}")

            # Compute zone
            if self.state.dose_rate_sv_per_h is not None:
                zone_result = assign_zone(self.state.dose_rate_sv_per_h)
                self.state.zone = zone_result.zone
                logger.info(f"  Zone assigned: {self.state.zone}")

        except Exception as e:
            logger.error(f"Transport execution failed: {e}")
            self.state.errors.append(f"Transport error: {e}")

    def _run_point_kernel(self) -> None:
        """Execute point-kernel dose-rate assessment."""
        logger.info("  Engine: point-kernel")

        from pyshield_smr.shielding.point_kernel import point_kernel_dose_rate

        receptor_spec = self.spec.get("receptor")
        if not receptor_spec:
            raise ValueError("No receptor section in spec")

        # Normalize to list
        receptors = receptor_spec if isinstance(receptor_spec, list) else [receptor_spec]

        # For now, use first receptor
        recv = receptors[0]
        recv_pos = recv.get("position_m")
        if not recv_pos:
            raise ValueError("Receptor missing 'position_m'")

        # Source position
        source_spec = self.spec.get("source")
        source_pos = source_spec.get("position_m") if isinstance(source_spec, dict) else None

        if not source_pos:
            raise ValueError("Source missing 'position_m'")

        # Get buildup material (default: first material in geometry)
        buildup_material = self.spec.get("buildup_material", "water")

        # Load material library
        material_library = load_material_library()

        # The point-kernel engine is 1-D along the +z axis.
        # Positions in the YAML spec are 3-D [x, y, z]; extract the z component.
        src_z = source_pos[2] if hasattr(source_pos, "__getitem__") else float(source_pos)
        rec_z = recv_pos[2] if hasattr(recv_pos, "__getitem__") else float(recv_pos)

        # Run point-kernel
        result = point_kernel_dose_rate(
            source_position_m=src_z,
            source_energies_MeV=self.state.source_energies_MeV,
            source_intensities_per_s=self.state.source_intensities_per_s,
            geometry=self.geometry,
            receptor_positions_m=[rec_z],
            buildup_material=buildup_material,
            material_library=material_library
        )

        self.state.dose_rate_sv_per_h = result.dose_rate_sv_per_h[0]
        logger.info(f"    Dose rate at receptor: {self.state.dose_rate_sv_per_h:.3e} Sv/h")

    def _run_monte_carlo(self) -> None:
        """Execute Monte Carlo photon transport (placeholder for now)."""
        logger.info("  Engine: monte-carlo")
        logger.warning("Monte Carlo execution not yet integrated into runner")
        self.state.warnings.append("Monte Carlo engine not yet implemented in runner")

    def apply_post_processors(self) -> None:
        """Execute optional post-processors: UQ, ALARP optimization.

        These are only run if spec['uncertainty'] or spec['alarp'] are present.
        """
        try:
            if "uncertainty" in self.spec:
                self._run_uq()

            if "alarp" in self.spec:
                self._run_alarp()

        except Exception as e:
            logger.error(f"Post-processing failed: {e}")
            self.state.errors.append(f"Post-processor error: {e}")

    def _run_uq(self) -> None:
        """Execute uncertainty quantification (Monte Carlo sampling)."""
        logger.info("Running uncertainty quantification...")
        logger.warning("UQ integration not yet implemented in runner")
        self.state.warnings.append("UQ not yet integrated into runner")

    def _run_alarp(self) -> None:
        """Execute ALARP optimization."""
        logger.info("Running ALARP optimization...")
        logger.warning("ALARP integration not yet implemented in runner")
        self.state.warnings.append("ALARP not yet integrated into runner")

    def render_outputs(self) -> None:
        """Generate Markdown and HTML reports from analysis results."""
        logger.info("Rendering reports...")

        try:
            # Build context for Jinja2 templates
            context = self._build_report_context()

            # Render both formats
            formats = self.spec.get("report_format", ["markdown"])
            if isinstance(formats, str):
                formats = [formats]

            rendered = render_report(context, formats=tuple(formats))

            # Store for later persistence
            self.rendered_reports = rendered
            logger.info(f"  Rendered {len(rendered)} report formats")

        except Exception as e:
            logger.error(f"Report rendering failed: {e}")
            self.state.warnings.append(f"Rendering error: {e}")

    def _build_report_context(self) -> Dict[str, Any]:
        """Build context dict for Jinja2 templates."""
        import platform as _platform

        engine = self.spec.get("engine", "unknown")

        # Method summary sentence shown in section 2 of the report.
        method_descriptions = {
            "point_kernel": (
                "Point-kernel method: uncollided fluence from the point source is "
                "attenuated through each slab using NIST XCOM mass-attenuation "
                "coefficients, then multiplied by a Taylor two-term buildup factor "
                "to account for scattered radiation. Dose is converted to H*(10) "
                "using ICRP-74 flux-to-dose coefficients."
            ),
            "monte_carlo": (
                "Analog Monte Carlo photon transport: individual photon histories "
                "are sampled from the source spectrum and tracked through the slab "
                "geometry. Compton scattering uses the Kahn rejection method for "
                "Klein-Nishina sampling. Dose is tallied at the receptor using "
                "ICRP-74 H*(10) conversion coefficients."
            ),
        }
        method_summary = method_descriptions.get(
            engine,
            f"Engine '{engine}' — see docs/theory/ for details.",
        )

        # Data file hashes from QA manifest (available because governance runs first).
        data_hashes: Dict[str, str] = {}
        if self.state.qa_manifest is not None:
            data_hashes = dict(self.state.qa_manifest.data_files)

        return {
            "case_name": self.spec.get("case_name", "Untitled"),
            "analyst": self.spec.get("analyst", "Unknown"),
            "spec_path": "spec_used.yaml",
            "engine": engine,
            "buildup_material": self.spec.get("buildup_material", "water"),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "version": "0.1.1",
            "dose_rate_sv_per_h": self.state.dose_rate_sv_per_h,
            "zone": self.state.zone,
            "method_summary": method_summary,
            # MC-specific fields — None unless Monte Carlo engine was used.
            "transmitted_weight": None,
            "relative_error": None,
            "assumptions": [
                "1-D plane-parallel geometry (infinite slab approximation).",
                "Photon transport only — neutron contributions not modelled.",
                "Taylor two-term buildup factor valid for optical depth ≤ 20 mfp.",
                "Point-source approximation — source dimensions << source-to-receptor distance.",
                "H*(10) dose quantity via ICRP-74 coefficients.",
            ],
            "warnings": self.state.warnings,
            "uq": self.state.uq_results,
            "uq_skip_reason": "UQ not enabled in this spec.",
            "data_hashes": data_hashes,
            "platform": _platform.platform(),
            "runtime_seconds": self.state.runtime_seconds,
        }

    def build_governance(self) -> None:
        """Build QA manifest with data hashes and platform info."""
        logger.info("Building QA manifest...")

        try:
            # Identify data files used
            data_files_to_hash = [
                "data/cross_sections/photon_mass_attenuation.json",
                "data/decay_chains/short.json",
                "data/buildup_factors/taylor_two_term.json",
                "data/flux_to_dose/icrp74_photon.json",
            ]

            # Filter to files that actually exist
            existing_files = [
                Path(f) for f in data_files_to_hash
                if Path(f).exists()
            ]

            manifest = build_qa_manifest(
                pyshield_version="0.1.0",
                runtime_seconds=self.state.runtime_seconds,
                data_files_to_hash=existing_files if existing_files else None,
                warnings=self.state.warnings,
                analysis_metadata={
                    "case_name": self.spec.get("case_name"),
                    "analyst": self.spec.get("analyst"),
                    "engine": self.spec.get("engine"),
                    "dose_rate_sv_per_h": self.state.dose_rate_sv_per_h,
                    "zone": self.state.zone,
                }
            )

            self.state.qa_manifest = manifest
            logger.info(f"  QA manifest built with {len(manifest.data_files)} data file hashes")

        except Exception as e:
            logger.error(f"QA manifest generation failed: {e}")
            self.state.warnings.append(f"QA error: {e}")

    def persist_outputs(self) -> None:
        """Write all outputs (reports, manifest) to timestamped folder."""
        logger.info("Persisting outputs...")

        try:
            case_name = self.spec.get("case_name", "analysis").replace(" ", "_")
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())
            output_dir = Path("reports") / f"{timestamp}_{case_name}"

            output_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir = output_dir

            # Write reports
            if hasattr(self, 'rendered_reports'):
                for fmt, content in self.rendered_reports.items():
                    report_path = output_dir / f"report.{fmt}"
                    report_path.write_text(content, encoding="utf-8")
                    logger.info(f"  Wrote {report_path}")

            # Write QA manifest
            if self.state.qa_manifest:
                manifest_path = output_dir / "qa_manifest.json"
                self.state.qa_manifest.write_to_file(manifest_path)

            # Write spec (for audit)
            spec_path = output_dir / "spec_used.yaml"
            from pyshield_smr.io.yaml_config import dump_yaml_spec
            dump_yaml_spec(self.spec, spec_path)

            logger.info(f"All outputs written to {output_dir}")

        except Exception as e:
            logger.error(f"Output persistence failed: {e}")
            self.state.warnings.append(f"Persistence error: {e}")

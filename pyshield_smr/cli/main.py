"""Command-line interface: entry point for pyshield commands.

## User-Facing Commands

    pyshield run <spec.yaml>
        Execute analysis from YAML spec. Outputs reports to reports/TIMESTAMP_CASENAME/.

    pyshield validate <spec.yaml>
        Check YAML against schema. Exit 0 if valid, 1 if errors found.

    pyshield hash-data <file>
        Compute and display SHA-256 hash of a data file (for QA verification).

    pyshield emit-slurm <spec.yaml> <output.slurm>
        Generate a SLURM job script for parallel execution on HPC clusters.

## Design Philosophy

The CLI is a thin wrapper around the Runner. No physics logic lives in the CLI;
all computation is delegated to runner.py, which is importable and testable
independently of argparse.

This keeps the CLI simple and the core logic reusable (e.g., for programmatic
invocation, batch workflows, or embedding in Jupyter notebooks).

## Typical Usage

    $ cd /path/to/pyshield-smr
    $ python -m pyshield_smr.cli.main run examples/01_point_kernel_shielding/config.yaml
    ... Analysis runs ...
    $ ls reports/
    2026-04-14_14-32-15_Lead_lined_container/
    $ cat reports/2026-04-14_14-32-15_Lead_lined_container/report.md
    ... Results ...
"""

import argparse
import logging
import sys
from pathlib import Path

from pyshield_smr.utils.hashing import sha256_file
from pyshield_smr.utils.logging import get_logger
from pyshield_smr.workflow.runner import Runner
from pyshield_smr.workflow.schema import validate_spec
from pyshield_smr.io.yaml_config import load_yaml_spec

logger = get_logger(__name__, level="INFO")


def main(argv: list[str] | None = None) -> int:
    """Main entry point for CLI.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code: 0 for success, 1 for error
    """
    parser = argparse.ArgumentParser(
        description="PyShield-SMR: Radiation shielding analysis framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Run analysis from YAML spec
  pyshield run examples/01_point_kernel_shielding/config.yaml

  # Validate spec before running
  pyshield validate examples/01_point_kernel_shielding/config.yaml

  # Compute hash of data file for audit
  pyshield hash-data data/cross_sections/photon_mass_attenuation.json

  # Generate SLURM job script for cluster execution
  pyshield emit-slurm examples/01_point_kernel_shielding/config.yaml job.slurm
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # ============================================================================
    # run command
    # ============================================================================
    run_parser = subparsers.add_parser(
        "run",
        help="Execute analysis from YAML spec"
    )
    run_parser.add_argument(
        "spec",
        type=str,
        help="Path to YAML specification file"
    )
    run_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging"
    )

    # ============================================================================
    # validate command
    # ============================================================================
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate YAML spec against schema"
    )
    validate_parser.add_argument(
        "spec",
        type=str,
        help="Path to YAML specification file"
    )

    # ============================================================================
    # hash-data command
    # ============================================================================
    hash_parser = subparsers.add_parser(
        "hash-data",
        help="Compute SHA-256 hash of a data file"
    )
    hash_parser.add_argument(
        "file",
        type=str,
        help="Path to data file"
    )

    # ============================================================================
    # emit-slurm command
    # ============================================================================
    slurm_parser = subparsers.add_parser(
        "emit-slurm",
        help="Generate SLURM job script for HPC execution"
    )
    slurm_parser.add_argument(
        "spec",
        type=str,
        help="Path to YAML specification file"
    )
    slurm_parser.add_argument(
        "output",
        type=str,
        help="Path to write SLURM script to"
    )
    slurm_parser.add_argument(
        "--nodes",
        type=int,
        default=1,
        help="Number of compute nodes (default: 1)"
    )
    slurm_parser.add_argument(
        "--tasks-per-node",
        type=int,
        default=8,
        help="Tasks per node (default: 8)"
    )
    slurm_parser.add_argument(
        "--time",
        type=str,
        default="00:30:00",
        help="Wall-clock time (default: 00:30:00)"
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    # Dispatch to subcommand handler
    try:
        if args.command == "run":
            return cmd_run(args)
        elif args.command == "validate":
            return cmd_validate(args)
        elif args.command == "hash-data":
            return cmd_hash_data(args)
        elif args.command == "emit-slurm":
            return cmd_emit_slurm(args)
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Execute 'pyshield run' subcommand."""
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    spec_path = Path(args.spec)

    if not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        return 1

    try:
        runner = Runner.from_spec_file(spec_path)
        state = runner.execute()

        # Report summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("ANALYSIS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Case: {state.spec.get('case_name')}")
        logger.info(f"Engine: {state.spec.get('engine')}")
        logger.info(f"Dose rate: {state.dose_rate_sv_per_h or 'N/A'}")
        logger.info(f"Zone: {state.zone or 'N/A'}")
        logger.info(f"Runtime: {state.runtime_seconds:.2f}s")
        logger.info(f"Warnings: {len(state.warnings)}")
        logger.info(f"Errors: {len(state.errors)}")

        if state.errors:
            logger.error("Analysis completed with errors:")
            for err in state.errors:
                logger.error(f"  - {err}")
            logger.info(f"Output: {runner.output_dir}")
            return 1

        if state.warnings:
            logger.warning("Analysis completed with warnings:")
            for warn in state.warnings:
                logger.warning(f"  - {warn}")

        logger.info(f"Output: {runner.output_dir}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Run failed: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute 'pyshield validate' subcommand."""
    spec_path = Path(args.spec)

    if not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        return 1

    try:
        spec = load_yaml_spec(spec_path)
        errors = validate_spec(spec)

        if errors:
            logger.error(f"Validation failed: {len(errors)} error(s)")
            for err in errors:
                logger.error(f"  {err}")
            return 1
        else:
            logger.info(f"Spec valid: {spec_path}")
            return 0

    except Exception as e:
        logger.error(f"Validation error: {e}")
        return 1


def cmd_hash_data(args: argparse.Namespace) -> int:
    """Execute 'pyshield hash-data' subcommand."""
    file_path = Path(args.file)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 1

    try:
        digest = sha256_file(file_path)
        logger.info(f"{file_path}: {digest}")
        return 0

    except Exception as e:
        logger.error(f"Hash failed: {e}")
        return 1


def cmd_emit_slurm(args: argparse.Namespace) -> int:
    """Execute 'pyshield emit-slurm' subcommand (placeholder)."""
    spec_path = Path(args.spec)
    output_path = Path(args.output)

    if not spec_path.exists():
        logger.error(f"Spec file not found: {spec_path}")
        return 1

    try:
        # TODO: Implement SLURM script generation in hpc/scheduler.py
        logger.warning("SLURM script generation not yet implemented")

        # Placeholder: generate a basic SLURM script
        script = f"""\
#!/bin/bash
#SBATCH --nodes={args.nodes}
#SBATCH --ntasks-per-node={args.tasks_per_node}
#SBATCH --time={args.time}
#SBATCH --job-name=pyshield

module load python/3.11  # Adjust for your cluster

cd $SLURM_SUBMIT_DIR

# Run analysis with parallel MPI-style execution
python -m pyshield_smr.cli.main run {spec_path}
"""

        output_path.write_text(script)
        logger.info(f"SLURM script written to {output_path}")
        logger.info(f"Submit with: sbatch {output_path}")

        return 0

    except Exception as e:
        logger.error(f"SLURM generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

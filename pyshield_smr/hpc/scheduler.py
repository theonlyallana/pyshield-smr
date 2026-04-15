"""SLURM/PBS job script generation for cluster submission.

This module generates job scripts for popular HPC schedulers:
  - SLURM (Simple Linux Utility for Resource Management)
  - PBS (Portable Batch System, via OpenPBS or Torque)

A generated script can be submitted directly to the cluster:
    sbatch script.slurm
    qsub script.pbs

## Design Philosophy

The module emits *pedagogical* scripts, not production-optimized ones. Key points:
  1. Scripts are human-readable (clear comments, sensible defaults)
  2. They demonstrate best practices (module loading, environment setup, error checking)
  3. They can be manually tuned for specific clusters (wall time, queue selection, etc.)

## Example Usage

    from pyshield_smr.hpc.scheduler import emit_slurm_script

    config = SlurmConfig(
        nodes=4,
        ntasks_per_node=8,
        time="01:00:00",
        memory_per_task_gb=4,
        job_name="pyshield_analysis",
        email="user@example.com"
    )

    script = emit_slurm_script(
        config=config,
        spec_path="examples/01_point_kernel_shielding/config.yaml",
        output_dir="results"
    )

    Path("job.slurm").write_text(script)
    # Then: sbatch job.slurm
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pyshield_smr.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SlurmConfig:
    """Configuration for SLURM job script generation."""
    nodes: int = 1
    """Number of compute nodes."""
    ntasks_per_node: int = 8
    """Number of parallel tasks per node."""
    time: str = "00:30:00"
    """Wall-clock time in HH:MM:SS format."""
    memory_per_task_gb: Optional[float] = None
    """Memory per task in GB (e.g., 4 for 4GB). If None, not specified."""
    job_name: str = "pyshield"
    """SLURM job name."""
    partition: Optional[str] = None
    """Partition/queue name (e.g., 'gpu', 'compute'). If None, use default."""
    email: Optional[str] = None
    """Email address for completion notifications."""
    email_type: str = "END"
    """When to email: START, END, FAIL, ALL (default: END)."""
    modules: list[str] = field(default_factory=lambda: ["python/3.11"])
    """Environment modules to load (site-specific)."""


@dataclass
class PBSConfig:
    """Configuration for PBS job script generation."""
    nodes: int = 1
    """Number of compute nodes."""
    ppn: int = 8
    """Processors per node."""
    walltime: str = "00:30:00"
    """Wall-clock time in HH:MM:SS format."""
    memory: Optional[str] = None
    """Memory request (e.g., '32gb'). If None, not specified."""
    job_name: str = "pyshield"
    """PBS job name."""
    queue: Optional[str] = None
    """Queue name. If None, use default."""
    email: Optional[str] = None
    """Email address for notifications."""
    modules: list[str] = field(default_factory=lambda: ["python/3.11"])
    """Environment modules to load."""


def emit_slurm_script(
    config: SlurmConfig,
    spec_path: str | Path,
    output_dir: str | Path = "results",
) -> str:
    """Generate a SLURM job script for parallel analysis execution.

    Args:
        config: SlurmConfig with job parameters
        spec_path: Path to analysis spec file (relative or absolute)
        output_dir: Where to write results

    Returns:
        Complete SLURM script as a string

    Example:
        >>> config = SlurmConfig(nodes=2, ntasks_per_node=8, time="02:00:00")
        >>> script = emit_slurm_script(config, "specs/analysis.yaml")
        >>> Path("job.slurm").write_text(script)
    """
    spec_path = Path(spec_path)
    output_dir = Path(output_dir)

    script_lines = [
        "#!/bin/bash",
        "",
        "# PyShield-SMR SLURM Job Script",
        "# This script runs a parallel radiation shielding analysis on an HPC cluster",
        "",
    ]

    # SLURM directives
    script_lines.append(f"#SBATCH --nodes={config.nodes}")
    script_lines.append(f"#SBATCH --ntasks-per-node={config.ntasks_per_node}")
    script_lines.append(f"#SBATCH --time={config.time}")

    if config.memory_per_task_gb:
        script_lines.append(f"#SBATCH --mem-per-cpu={config.memory_per_task_gb}G")

    script_lines.append(f"#SBATCH --job-name={config.job_name}")

    if config.partition:
        script_lines.append(f"#SBATCH --partition={config.partition}")

    if config.email:
        script_lines.append(f"#SBATCH --mail-user={config.email}")
        script_lines.append(f"#SBATCH --mail-type={config.email_type}")

    script_lines.extend([
        "",
        "# Print job info for debugging",
        "echo \"SLURM_JOB_ID: $SLURM_JOB_ID\"",
        "echo \"SLURM_NODELIST: $SLURM_NODELIST\"",
        "echo \"SLURM_NTASKS: $SLURM_NTASKS\"",
        "",
        "# Set up environment",
        "set -e  # Exit on any error",
        f"cd $SLURM_SUBMIT_DIR || exit 1",
        "",
    ])

    # Module loads
    for mod in config.modules:
        script_lines.append(f"module load {mod}")

    script_lines.extend([
        "",
        "# Create output directory",
        f"mkdir -p {output_dir}",
        "",
        "# Run analysis with automatic parallelization",
        "echo 'Starting analysis...'",
        f"python -m pyshield_smr.cli.main run {spec_path} \\",
        f"  --output-dir {output_dir}",
        "",
        "if [ $? -eq 0 ]; then",
        "  echo 'Analysis completed successfully'",
        "else",
        "  echo 'Analysis failed with exit code $?'",
        "  exit 1",
        "fi",
        "",
        "echo \"Results written to {output_dir}\"",
    ])

    return "\n".join(script_lines)


def emit_pbs_script(
    config: PBSConfig,
    spec_path: str | Path,
    output_dir: str | Path = "results",
) -> str:
    """Generate a PBS job script for parallel analysis execution.

    Args:
        config: PBSConfig with job parameters
        spec_path: Path to analysis spec file
        output_dir: Where to write results

    Returns:
        Complete PBS script as a string

    Example:
        >>> config = PBSConfig(nodes=2, ppn=8, walltime="02:00:00")
        >>> script = emit_pbs_script(config, "specs/analysis.yaml")
        >>> Path("job.pbs").write_text(script)
    """
    spec_path = Path(spec_path)
    output_dir = Path(output_dir)

    script_lines = [
        "#!/bin/bash",
        "",
        "# PyShield-SMR PBS Job Script",
        "# This script runs a parallel radiation shielding analysis via PBS",
        "",
    ]

    # PBS directives
    select_clause = f"select={config.nodes}:ppn={config.ppn}"
    if config.memory:
        select_clause += f":mem={config.memory}"

    script_lines.append(f"#PBS -l {select_clause}")
    script_lines.append(f"#PBS -l walltime={config.walltime}")
    script_lines.append(f"#PBS -N {config.job_name}")

    if config.queue:
        script_lines.append(f"#PBS -q {config.queue}")

    if config.email:
        script_lines.append(f"#PBS -M {config.email}")
        script_lines.append("#PBS -m e")

    script_lines.extend([
        "",
        "# PBS environment setup",
        "set -e",
        "cd $PBS_O_WORKDIR || exit 1",
        "",
    ])

    # Module loads
    for mod in config.modules:
        script_lines.append(f"module load {mod}")

    script_lines.extend([
        "",
        "# Create output directory",
        f"mkdir -p {output_dir}",
        "",
        "# Print job info",
        "echo \"PBS_JOBID: $PBS_JOBID\"",
        "echo \"PBS_NODEFILE: $PBS_NODEFILE\"",
        "echo \"PBS_NUM_PPN: $PBS_NUM_PPN\"",
        "",
        "# Run analysis",
        "echo 'Starting analysis...'",
        f"python -m pyshield_smr.cli.main run {spec_path} \\",
        f"  --output-dir {output_dir}",
        "",
        "echo \"Results written to {output_dir}\"",
    ])

    return "\n".join(script_lines)


def estimate_cluster_runtime(
    n_histories: int,
    histories_per_second: float = 1e5,
    n_nodes: int = 1,
    ntasks_per_node: int = 8,
    overhead_factor: float = 1.1,
) -> float:
    """Estimate wall-clock time needed for analysis on cluster.

    **Model:** Runtime ≈ (N_histories / throughput) × overhead

    where throughput (histories/s) scales with parallelism.

    Args:
        n_histories: Total histories to run
        histories_per_second: Single-core throughput (typical: 1e5 - 1e6)
        n_nodes: Number of nodes
        ntasks_per_node: Tasks per node
        overhead_factor: Multiplicative overhead (e.g., 1.1 = 10% overhead)

    Returns:
        Estimated runtime in seconds

    Example:
        >>> # 100M histories, typical single-core 1e5 hist/s, 4 nodes × 8 cores
        >>> runtime_s = estimate_cluster_runtime(
        ...     n_histories=int(1e8),
        ...     histories_per_second=1e5,
        ...     n_nodes=4,
        ...     ntasks_per_node=8
        ... )
        >>> minutes = runtime_s / 60
        >>> print(f"Estimated: {minutes:.1f} minutes")
        Estimated: 13.2 minutes
    """
    n_cores = n_nodes * ntasks_per_node
    parallel_throughput = histories_per_second * n_cores
    base_runtime = n_histories / parallel_throughput
    return base_runtime * overhead_factor


def format_walltime(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format for job schedulers.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string HH:MM:SS
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

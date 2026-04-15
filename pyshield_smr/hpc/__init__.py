"""HPC (High-Performance Computing) support: parallel execution and cluster integration.

This package provides:
  - parallel.py: Multiprocessing-based history parallelization for Monte Carlo
  - scheduler.py: SLURM/PBS script generation for cluster job submission
"""

from . import parallel, scheduler

__all__ = ["parallel", "scheduler"]

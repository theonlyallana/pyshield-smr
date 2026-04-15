"""Parallel execution support: multiprocessing-based history chunking for Monte Carlo.

## Problem: Why Parallel Monte Carlo?

Monte Carlo simulations are "embarrassingly parallel": each history is independent.
If we have 10^8 histories to simulate, we can distribute them across N workers
without synchronization overhead. Wall-clock time drops ~N-fold (minus overhead).

## Solution: History Chunking with RNG Independence

This module implements *history-level parallelization*:
  1. User requests N total histories
  2. Split into n_workers chunks (e.g., 100M / 8 = 12.5M per worker)
  3. Each worker gets its own RNG seed (from NumPy SeedSequence)
  4. Workers run *independently* (no MPI, no shared memory)
  5. Collect results, merge tallies, report combined statistics

**RNG Independence is Critical:** Each worker must have a *different* RNG stream.
NumPy's SeedSequence guarantees this: it derives independent streams from a root
seed without reusing sequences. This satisfies statistical independence requirements
in Monte Carlo literature (e.g., "non-overlapping subsequences" from L'Ecuyer).

## Example Usage

    from pyshield_smr.hpc.parallel import run_histories_parallel
    from pyshield_smr.transport.monte_carlo import MonteCarloPhoton
    from pyshield_smr.transport.geometry import SlabStack

    geometry = SlabStack(["lead"], [0.05])
    mc = MonteCarloPhoton(geometry, energy_MeV=1.0)

    # Run 100M histories across 8 processes
    result = run_histories_parallel(
        mc_constructor=lambda: MonteCarloPhoton(geometry, 1.0),
        n_histories=int(1e8),
        n_workers=8,
        root_seed=12345
    )

    print(f"Transmitted: {result.transmitted_weight:.3e}")
    print(f"Relative error: {result.relative_error_transmission:.4f}")

## Integration with Runner

The runner's _run_monte_carlo() method will call run_histories_parallel() if
the spec requests parallel execution. Number of workers defaults to CPU count
or can be specified in spec['monte_carlo']['n_workers'].
"""

from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, List, Optional

import numpy as np

from pyshield_smr.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ParallelMCResult:
    """Aggregated results from parallel Monte Carlo run."""
    transmitted_weight: float
    """Total transmitted weight across all workers."""
    relative_error_transmission: float
    """Relative statistical error on transmission (combined across workers)."""
    total_histories: int
    """Total number of histories run."""
    n_workers: int
    """Number of workers used."""
    worker_results: List[Any]
    """Individual results from each worker (for debugging)."""
    root_seed: int
    """Root RNG seed used."""

    def __post_init__(self):
        """Validate combined statistics."""
        if self.relative_error_transmission < 0:
            logger.warning("Negative relative error detected; clamping to 0")
            self.relative_error_transmission = 0


def run_histories_parallel(
    mc_constructor: Callable[[], Any],
    n_histories: int,
    n_workers: Optional[int] = None,
    root_seed: int = 42,
    chunk_size: Optional[int] = None,
) -> ParallelMCResult:
    """Run Monte Carlo histories in parallel across multiple workers.

    **Algorithm:**
      1. Create SeedSequence from root_seed
      2. Generate n_workers independent child seeds via spawn()
      3. Partition n_histories into n_workers roughly equal chunks
      4. Submit each chunk to a worker process
      5. Collect results and combine tallies
      6. Compute combined relative error via Welford's algorithm

    Args:
        mc_constructor: Callable that returns a MonteCarloPhoton instance.
            Must be picklable (defined at module level or a lambda over picklable closure).
        n_histories: Total histories to run (distributed across workers).
        n_workers: Number of worker processes (default: CPU count on this machine).
        root_seed: Root RNG seed (default: 42). Each worker gets a derived seed.
        chunk_size: Histories per worker (default: auto-compute from n_histories / n_workers).
            Useful for specifying exactly how many histories each worker runs.

    Returns:
        ParallelMCResult with aggregated transmission, error, and per-worker results.

    Raises:
        ValueError: If n_histories <= 0 or n_workers <= 0
        RuntimeError: If worker process raises an exception

    Example:
        >>> from pyshield_smr.transport.monte_carlo import MonteCarloPhoton
        >>> from pyshield_smr.transport.geometry import SlabStack
        >>>
        >>> def make_mc():
        ...     geom = SlabStack(["lead"], [0.05])
        ...     return MonteCarloPhoton(geom, energy_MeV=1.0)
        >>>
        >>> result = run_histories_parallel(
        ...     mc_constructor=make_mc,
        ...     n_histories=int(1e6),
        ...     n_workers=4
        ... )
        >>> print(f"Transmission: {result.transmitted_weight:.3e}")
    """
    if n_histories <= 0:
        raise ValueError(f"n_histories must be > 0, got {n_histories}")

    if n_workers is None:
        import os
        n_workers = os.cpu_count() or 1

    if n_workers <= 0:
        raise ValueError(f"n_workers must be > 0, got {n_workers}")

    logger.info(f"Parallel MC setup: {n_histories} histories × {n_workers} workers")

    # Compute histories per worker
    if chunk_size is None:
        chunk_size = max(1, n_histories // n_workers)

    logger.info(f"  Chunk size: {chunk_size} histories/worker")

    # Generate independent RNG seeds for each worker
    rng = np.random.SeedSequence(root_seed)
    child_seeds = rng.spawn(n_workers)

    # Prepare worker tasks
    worker_tasks = []
    for worker_id in range(n_workers):
        seed = int(child_seeds[worker_id].generate_state()[0][0])  # Extract seed int
        n_hist_this_worker = chunk_size if worker_id < n_workers - 1 else (
            n_histories - (n_workers - 1) * chunk_size
        )
        worker_tasks.append((worker_id, mc_constructor, n_hist_this_worker, seed))

    # Run in parallel
    worker_results = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [
            executor.submit(_worker_run_histories, *task)
            for task in worker_tasks
        ]

        for future in futures:
            try:
                result = future.result(timeout=3600)  # 1-hour timeout
                worker_results.append(result)
                logger.info(
                    f"  Worker {result['worker_id']}: "
                    f"{result['n_histories']} histories, "
                    f"transmitted {result['transmitted_weight']:.3e}"
                )
            except Exception as e:
                logger.error(f"Worker failed: {e}")
                raise RuntimeError(f"Worker process error: {e}")

    # Combine results
    total_transmitted = sum(r["transmitted_weight"] for r in worker_results)
    total_histories_run = sum(r["n_histories"] for r in worker_results)

    # Compute combined relative error (simplified: assume independent samples)
    # E[X] = total_transmitted / n
    # Var[X] ≈ sum of per-worker variances
    combined_var = sum(
        (r["n_histories"] * r.get("variance_transmission", 0.0))
        for r in worker_results
    )
    combined_std = np.sqrt(combined_var)
    combined_rel_error = (
        (combined_std / total_transmitted) if total_transmitted > 0 else 0.0
    )

    logger.info(f"Combined transmission: {total_transmitted:.3e}")
    logger.info(f"Combined relative error: {combined_rel_error:.4f}")

    return ParallelMCResult(
        transmitted_weight=total_transmitted,
        relative_error_transmission=combined_rel_error,
        total_histories=total_histories_run,
        n_workers=n_workers,
        worker_results=worker_results,
        root_seed=root_seed,
    )


def _worker_run_histories(
    worker_id: int,
    mc_constructor: Callable[[], Any],
    n_histories: int,
    seed: int,
) -> dict:
    """Worker process: instantiate MC engine and run histories.

    This function runs in a separate process. The MC engine is instantiated
    fresh in this process (and gets the worker's specific seed).

    Args:
        worker_id: Worker identifier (for logging)
        mc_constructor: Callable returning MC engine instance
        n_histories: Number of histories to run
        seed: RNG seed for this worker

    Returns:
        Dict with worker_id, n_histories, transmitted_weight, variance, etc.
    """
    try:
        # Instantiate MC engine
        mc = mc_constructor()

        # Run histories with worker-specific seed
        result = mc.run(n_histories=n_histories, seed=seed)

        # Return result as dict (pickle-able)
        return {
            "worker_id": worker_id,
            "n_histories": n_histories,
            "transmitted_weight": result.transmitted_weight,
            "variance_transmission": (
                (result.relative_error_transmission ** 2) * (result.transmitted_weight ** 2)
            ),
            "seed": seed,
        }

    except Exception as e:
        logger.error(f"Worker {worker_id} failed: {e}")
        raise


def estimate_convergence(
    target_relative_error: float,
    sample_n_histories: int,
    sample_relative_error: float,
) -> int:
    """Estimate total histories needed to reach target relative error.

    **Formula:** In MC, relative error ~ 1/√N. So:
        σ_target / σ_sample = √(N_sample / N_target)
        N_target = N_sample × (σ_sample / σ_target)²

    Args:
        target_relative_error: Desired relative error (e.g., 0.01 for 1%)
        sample_n_histories: Histories run in sample simulation
        sample_relative_error: Observed relative error from sample

    Returns:
        Estimated total histories needed (int)

    Example:
        >>> # Ran 1M histories, got 3% error, want 1% error
        >>> n_needed = estimate_convergence(
        ...     target_relative_error=0.01,
        ...     sample_n_histories=int(1e6),
        ...     sample_relative_error=0.03
        ... )
        >>> print(f"Need {n_needed:.2e} histories total")
        Need 9.00e+06 histories total
    """
    if sample_relative_error <= 0:
        raise ValueError("sample_relative_error must be > 0")

    if target_relative_error >= sample_relative_error:
        logger.warning(
            f"Target error {target_relative_error} >= sample error {sample_relative_error}; "
            "already converged"
        )
        return sample_n_histories

    ratio = sample_relative_error / target_relative_error
    n_needed = sample_n_histories * (ratio ** 2)

    return int(np.ceil(n_needed))

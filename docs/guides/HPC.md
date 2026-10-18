# HPC Cluster Execution

## Overview

`pyshield_smr/hpc/` has two separate pieces. Neither is wired to `pyshield run`.

- `parallel.py` exposes `run_histories_parallel`. It is not named `ParallelMCRunner`. The CLI has no `--workers` flag, and `Runner._run_monte_carlo` does not call this function.
- `scheduler.py` exposes `emit_slurm_script` and `emit_pbs_script`. They return a shell script as a string. `pyshield emit-slurm` does not call `emit_slurm_script`; it writes a shorter placeholder and logs that SLURM generation is not implemented. There is no `pyshield emit-pbs` command.

## Local parallel execution

Call the function directly. `mc_constructor` must return a `MonteCarloPhoton`:

```python
from pyshield_smr.hpc.parallel import run_histories_parallel
from pyshield_smr.transport.monte_carlo import MonteCarloPhoton

result = run_histories_parallel(
    mc_constructor=lambda: MonteCarloPhoton(...),
    n_histories=1000,
    n_workers=2,
    root_seed=42,
)
```

`run_histories_parallel` splits histories across processes and seeds them with `numpy.random.SeedSequence.spawn`. This guide does not quote a wall-clock time for that call.

## SLURM Cluster Execution

### 1. Generate the SLURM job script

```python
from pathlib import Path
from pyshield_smr.hpc.scheduler import SlurmConfig, emit_slurm_script

script = emit_slurm_script(
    SlurmConfig(nodes=2, ntasks_per_node=8, time="02:00:00"),
    "examples/01_point_kernel_shielding/config.yaml",
)
Path("job.slurm").write_text(script)
```

The generated script calls `python -m pyshield_smr.cli.main run <spec>`. That command has no `--output-dir` flag. For a point-kernel spec it runs the dose calculation. For `examples/02_monte_carlo_transmission/config.yaml` the runner warns and does not transport photons. The script does not call `srun` or `run_histories_parallel`.

`pyshield emit-slurm` accepts `spec`, `output`, `--nodes`, `--tasks-per-node`, and `--time`. It does not accept `--partition` or `--account`, and it does not use `emit_slurm_script`.

### 2. Review and customise

```bash
cat job.slurm
```

Generated script structure:

Read the file `emit_slurm_script` returned. Do not assume it contains `srun`, `--workers`, or `--account`. Those strings are not in `scheduler.py`.

### 3. Submit

```bash
sbatch job.slurm
```

### 4. Collect results

The generated script does not set an SBATCH output path and does not pass `--output-dir`. `pyshield run` writes `reports/<timestamp>_<case>/` in the job's working directory.

## PBS/Torque Cluster Execution

There is no `pyshield emit-pbs` subcommand. Build the script in Python:

```python
from pathlib import Path
from pyshield_smr.hpc.scheduler import PBSConfig, emit_pbs_script

script = emit_pbs_script(
    PBSConfig(nodes=1, ppn=4, walltime="00:30:00"),
    "examples/01_point_kernel_shielding/config.yaml",
)
Path("job.pbs").write_text(script)
```

Submit with `qsub` only after you have read the script. It runs the same `pyshield run` command as the SLURM helper.

## Parallelism Strategy

`run_histories_parallel` splits `n_histories` across workers and returns a `ParallelMCResult`. It does not return a `TallyResult`. The workflow runner does not call it.

**RNG independence**: Each worker is seeded with a child of a root `numpy.random.SeedSequence`:

```python
root_seed = np.random.SeedSequence(entropy=12345)
child_seeds = root_seed.spawn(n_workers)
```

This guarantees that child streams are statistically independent and reproducible from the root seed.

## Scaling

No wall-clock times or relative errors for parallel runs were measured in this repository.

`qa_manifest.json` does not record `n_workers`, an RNG seed, or per-worker wall time. It records the package version, platform, data-file SHA-256 hashes, warnings, and the analysis metadata the runner stored.

## Memory Considerations

This repository has no measured memory profile for `run_histories_parallel`, and it has no streaming-tally mode. `AGENTS.md` is not in the tree.

## Code Module Map

| File | Purpose |
|---|---|
| `hpc/parallel.py` | `run_histories_parallel`, `ParallelMCResult` |
| `hpc/scheduler.py` | `emit_slurm_script`, `emit_pbs_script`, `SlurmConfig`, `PBSConfig` |
| `cli/main.py` | `emit-slurm` writes a placeholder script. No `emit-pbs` subcommand |

## Troubleshooting

**Workers hang / no output**: Check that the compute nodes can see the data directory (NFS mount or pre-copied). All data files are read at worker startup.

**Different results run-to-run**: `run_histories_parallel` takes `root_seed` as a Python argument (default 42). The runner does not read `rng_seed` from the YAML spec, because it does not run Monte Carlo.

**SLURM script rejected**: Ensure Python 3.10+ and `pyshield_smr` are available on compute nodes. Pre-create `.venv` on the shared filesystem before job submission.

## References

- **numpy SeedSequence**: https://numpy.org/doc/stable/reference/random/parallel.html — authoritative guide to parallel RNG seeding.
- **SLURM documentation**: https://slurm.schedmd.com/documentation.html
- **PBS/Torque user guide**: Available from your HPC centre.

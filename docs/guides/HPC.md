# HPC Cluster Execution

## Overview

For large Monte Carlo runs (N > 10⁷ histories) or parameter sweeps, PyShield-SMR supports parallel execution on HPC clusters via SLURM and PBS/Torque schedulers. The `pyshield_smr/hpc/` module handles job script generation, worker coordination, and result collection.

## Architecture

```
┌─────────────────────────────────────────────┐
│  User: pyshield run config.yaml --workers N │
└──────────────────────┬──────────────────────┘
                       │
           ┌───────────▼───────────┐
           │  ParallelMCRunner     │  (pyshield_smr/hpc/parallel.py)
           │  Split N_total into   │
           │  N_total/workers each │
           └──┬──────────┬────────┘
         Worker 1      Worker 2  ...  Worker N
         seed = s1     seed = s2      seed = sN
         (numpy SeedSequence.spawn)
              │              │
           Tally 1        Tally 2
              └──────┬───────┘
                     │ merge
               Combined tally
```

Workers share no state; each receives an independent RNG seed via `numpy.random.SeedSequence.spawn(n_workers)`, guaranteeing statistically independent histories.

## Local Parallel Execution

For multi-core workstations:

```bash
# Run with 8 workers (uses multiprocessing)
pyshield run examples/02_monte_carlo_transmission/config.yaml --workers 8

# Or programmatically:
from pyshield_smr.hpc.parallel import ParallelMCRunner
runner = ParallelMCRunner(spec, n_workers=8)
result = runner.run()
```

No cluster scheduler is needed; `multiprocessing.Pool` distributes histories across CPU cores.

## SLURM Cluster Execution

### 1. Generate the SLURM job script

```bash
pyshield emit-slurm \
  examples/02_monte_carlo_transmission/config.yaml \
  job.slurm \
  --nodes 4 \
  --tasks-per-node 8 \
  --time 02:00:00 \
  --partition compute \
  --account my_project
```

This generates `job.slurm` with the correct MPI/multiprocessing layout for the target cluster.

### 2. Review and customise

```bash
cat job.slurm
```

Generated script structure:

```bash
#!/bin/bash
#SBATCH --job-name=pyshield_mc
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=8
#SBATCH --time=02:00:00
#SBATCH --partition=compute
#SBATCH --account=my_project
#SBATCH --output=logs/slurm_%j.out

module load python/3.11
source .venv/bin/activate

srun python -m pyshield_smr.hpc.scheduler \
  --spec examples/02_monte_carlo_transmission/config.yaml \
  --workers 32 \
  --output-dir reports/cluster_run
```

### 3. Submit

```bash
sbatch job.slurm
```

### 4. Monitor

```bash
squeue -u $USER
tail -f logs/slurm_<job_id>.out
```

### 5. Collect results

Results are written to the `--output-dir` on the cluster filesystem. Copy to local machine with:

```bash
rsync -avz cluster_user@hpc.example.ac.uk:~/pyshield-smr/reports/cluster_run/ ./reports/
```

## PBS/Torque Cluster Execution

```bash
pyshield emit-pbs \
  examples/02_monte_carlo_transmission/config.yaml \
  job.pbs \
  --ncpus 64 \
  --walltime 02:00:00
qsub job.pbs
```

PBS job script generation follows the same pattern as SLURM; see `pyshield_smr/hpc/scheduler.py → emit_pbs_script()`.

## Parallelism Strategy

PyShield-SMR uses **embarrassingly parallel** decomposition: the total history count `N` is divided equally across all workers. Each worker runs `N/workers` histories, then sends its `TallyResult` back to the controller for merging.

**RNG independence**: Each worker is seeded with a child of a root `numpy.random.SeedSequence`:

```python
root_seed = np.random.SeedSequence(entropy=12345)
child_seeds = root_seed.spawn(n_workers)
```

This guarantees that child streams are statistically independent and reproducible from the root seed.

## Scaling

| Workers | N histories | Wall time (est.) | Relative error |
|---|---|---|---|
| 1 | 10⁶ | ~30 s | ~1.0% |
| 8 | 10⁷ | ~40 s | ~0.3% |
| 32 | 10⁸ | ~50 s | ~0.1% |

(Times are illustrative for a simple slab geometry on modern hardware.)

The `qa_manifest.json` records:
- `n_workers` used
- `rng_root_seed` (for reproducibility)
- Wall-clock time per worker

## Memory Considerations

Each worker holds at most `n_histories_per_worker × sizeof(photon_state)` in memory (~few hundred bytes per photon). For 10⁷/worker, this is ~4 GB peak; ensure nodes have ≥ 8 GB RAM per task.

For very large problems (N > 10⁹), use streaming tallies rather than storing full histories — contact the project maintainer (see `AGENTS.md`).

## Code Module Map

| File | Purpose |
|---|---|
| `hpc/parallel.py` | `ParallelMCRunner` — local multiprocessing runner |
| `hpc/scheduler.py` | `emit_slurm_script()`, `emit_pbs_script()` |
| `cli/main.py` | `emit-slurm` and `emit-pbs` CLI subcommands |

## Troubleshooting

**Workers hang / no output**: Check that the compute nodes can see the data directory (NFS mount or pre-copied). All data files are read at worker startup.

**Different results run-to-run**: If `rng_root_seed` is not fixed in the YAML spec, a new random seed is chosen each run. Fix the seed for reproducibility:

```yaml
monte_carlo:
  n_histories: 1000000
  rng_seed: 42
```

**SLURM script rejected**: Ensure Python 3.10+ and `pyshield_smr` are available on compute nodes. Pre-create `.venv` on the shared filesystem before job submission.

## References

- **numpy SeedSequence**: https://numpy.org/doc/stable/reference/random/parallel.html — authoritative guide to parallel RNG seeding.
- **SLURM documentation**: https://slurm.schedmd.com/documentation.html
- **PBS/Torque user guide**: Available from your HPC centre.

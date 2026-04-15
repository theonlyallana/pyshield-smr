# workflow-author — logbook

## 2026-04-14 — v1 schema shipped

- Defined `SCHEMA_VERSION = "1.0.0"`.
- Implemented `Runner.execute(spec_path)` that validates the spec, resolves data hashes, orchestrates sources → transport → post-processing → UQ → ALARP → report, and writes a QA manifest.
- Implemented CLI: `pyshield run`, `pyshield validate`, `pyshield hash-data`, `pyshield emit-slurm`.
- Implemented HPC executor `pyshield_smr.hpc.parallel.ProcessPoolExecutor` that chunks histories, and a thin SLURM / PBS script emitter.

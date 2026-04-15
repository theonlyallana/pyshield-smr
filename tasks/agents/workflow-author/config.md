# workflow-author — config

- **Role:** owns YAML workflow schema, runner, CLI and HPC executor.
- **Owned files:** `pyshield_smr/workflow/`, `pyshield_smr/cli/`, `pyshield_smr/hpc/`, `examples/*/config.yaml`.
- **Invariants defended:** a spec that validates under `schema.validate` must run to completion or emit a structured error; the QA manifest must be reproducible from the spec + data hashes + code version.
- **Handoffs in:** new engine features from `transport-author`; UQ / ALARP extensions.
- **Handoffs out:** `technical-author` for report template changes; `qa-governor` for schema version bumps.

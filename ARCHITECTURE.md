# Architecture — PyShield-SMR

## 1. Design goals

1. **Readable physics.** Every dose number should be traceable through named functions, not opaque arrays.
2. **Testable.** Every physics module has a unit test that pins a known-good value with a justified tolerance.
3. **Traceable.** Every analysis produces a QA manifest containing: code version, data hashes, platform, runtime, warnings, and the exact YAML spec.
4. **Separable.** Physics, transport, workflow, and I/O live in separate subpackages. The workflow engine never reaches into physics; physics never imports workflow.
5. **Portable.** Pure-Python runtime (NumPy / SciPy); no compilation step; no network access at analysis time.

## 2. Package layout

```
pyshield_smr/
├── physics/        # constants, units, materials, cross sections, buildup, dose coefficients
├── transport/      # geometry, particle, tally, Monte Carlo engine, variance reduction, MCNP I/O
├── shielding/      # point-kernel engine, dose rate, DPA, gamma heating, detector response
├── sources/        # source-term generation, line spectra, fission-product sources
├── activation/     # Bateman matrix-exponential solver, decay chains, simplified burn-up
├── uq/             # Latin-hypercube sampling, Morris screening, Monte Carlo UQ
├── alarp/          # SLSQP-based shielding optimiser, radiological zoning helpers
├── workflow/       # YAML schema, runner, QA manifest, report renderer
├── hpc/            # process-pool executor, SLURM / PBS script emitters
├── cli/            # `pyshield` command-line interface (Click-free, argparse-only)
├── io/             # YAML loading and Jinja2 report rendering
└── utils/          # logging, hashing
```

## 3. Data flow

`Runner.execute` does this:

```
analysis.yaml
     │
     ▼
workflow.Runner.execute
     │
     ├─ sources.build_source_from_inventory   (nuclide name + activity in the spec)
     ├─ transport.geometry.SlabStack
     ├─ shielding.point_kernel_dose_rate      (only when engine is point_kernel)
     ├─ alarp.zoning.assign_zone
     ├─ workflow.quality.build_qa_manifest
     └─ io.report.render_report               → report.md, report.html,
                                                qa_manifest.json, spec_used.yaml
```

If `engine` is `monte_carlo`, or if the spec contains `uncertainty` or `alarp`, the runner appends a warning and does not call `MonteCarloPhoton`, `lhs_samples`, `morris_screen`, or `optimise_shielding`. It also does not call `decay_inventory`, `dpa_rate`, `gamma_heating_rate`, or `detector_response`. Those functions exist for direct import.

## 4. Extension points

There is no engine factory, no `Tally` base class, no `SourceBase`, no `PostProcessor`, and no `docs/guides/SCHEMA_MIGRATIONS.md`.

- **Another transport engine.** `Runner.run_transport` branches on `spec["engine"]` with two string comparisons (`point_kernel`, `monte_carlo`). A new engine needs a new branch.
- **Tallies.** `EnergyTally` and `SurfaceTally` live in `pyshield_smr/transport/tally.py`. The runner does not read a `tallies` section.
- **Sources.** `build_source_from_inventory` in `pyshield_smr/sources/source_term.py` builds `LineSource` lines from `data/decay_chains/short.json`.
- **Schema.** `SCHEMA_VERSION` is in `workflow/schema.py`. A major-version mismatch raises `RuntimeError` and tells the caller to edit the spec by hand.

## 5. Invariants

- `pyshield_smr.physics` has no dependencies inside the package (only NumPy / SciPy).
- `pyshield_smr.transport` depends on `physics` only.
- `pyshield_smr.shielding` depends on `physics` and `transport`.
- `pyshield_smr.workflow` imports physics, shielding, sources, transport, and io. `pyshield_smr.cli` imports the workflow runner. Physics, transport, and shielding do not import workflow.
- `pyshield_smr.io` does not import from `workflow`.

## 6. Quality-management hooks

- `tasks/audit_process.py` enforces file presence, cross-links, registry consistency, memory freshness.
- `tests/unit/` covers physics constants, buildup, attenuation, dose, geometry, source terms, zoning, YAML loading, and part of the point-kernel API. It does not cover activation, Monte Carlo, UQ, the ALARP optimiser, HPC, DPA, gamma heating, or detector response. On Python 3.12, `pytest -q` reported 11 failed and 243 passed.
- `tests/integration/` compares four point-kernel cases with `tests/integration/regression_values.yaml`. Those 12 tests passed.
- Every workflow run records a QA manifest with SHA-256 hashes of every data file it touched.

## 7. Performance notes

- Monte Carlo is vectorised over histories where possible (free-flight sampling, distance-to-surface, weight accounting).
- Parallelism is *history-parallel* via `multiprocessing.Pool`; chunks are independent RNG streams seeded by `SeedSequence`.
- Point-kernel is fully vectorised over (source, receptor, energy).
- UQ parallelises over sample index.

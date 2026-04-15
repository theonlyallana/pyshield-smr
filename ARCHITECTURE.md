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
├── io/             # report rendering, data loading, VTK-lite fluence export
└── utils/          # logging, hashing
```

## 3. Data flow

```
analysis.yaml
     │
     ▼
workflow.Runner.execute
     │
     ├─ sources.SourceBuilder  ──► ordered list of (energy, intensity) emissions
     │
     ├─ activation.Bateman     ──► time-dependent inventory if decay requested
     │
     ├─ transport.MonteCarlo   ──► tallies: fluence, uncollided current, surface crossings
     │       OR
     │   shielding.PointKernel ──► tallies: uncollided + build-up corrected dose
     │
     ├─ shielding.DoseRate     ──► H*(10) from spectral fluence
     │   shielding.DPA         ──► atomic-displacement damage rate
     │   shielding.GammaHeating──► volumetric energy deposition
     │
     ├─ uq                     ──► propagated uncertainty bands (optional)
     │
     ├─ alarp                  ──► optimised thicknesses (optional)
     │
     └─ io.report              ──► report.md / report.html + qa_manifest.json
```

## 4. Extension points

- **New engine.** Implement a class in `pyshield_smr/transport/` or `pyshield_smr/shielding/` that returns a `Tally` object. Add a factory entry in `workflow.runner._resolve_engine`.
- **New tally.** Subclass `pyshield_smr.transport.tally.Tally`; the runner will pick it up if listed in the YAML spec under `tallies`.
- **New source.** Subclass `pyshield_smr.sources.source_term.SourceBase`.
- **New post-processor.** Subclass `pyshield_smr.shielding.PostProcessor`.
- **New schema version.** Bump `SCHEMA_VERSION` in `workflow/schema.py` and document the migration in `docs/guides/SCHEMA_MIGRATIONS.md`.

## 5. Invariants

- `pyshield_smr.physics` has no dependencies inside the package (only NumPy / SciPy).
- `pyshield_smr.transport` depends on `physics` only.
- `pyshield_smr.shielding` depends on `physics` and `transport`.
- `pyshield_smr.workflow` depends on everything; nothing depends on `workflow`.
- `pyshield_smr.io` does not import from `workflow`.

## 6. Quality-management hooks

- `tasks/audit_process.py` enforces file presence, cross-links, registry consistency, memory freshness.
- `tests/unit/` pins physics.
- `tests/integration/` pins end-to-end behaviour with regression values in `tests/integration/regression_values.yaml`.
- Every workflow run records a QA manifest with SHA-256 hashes of every data file it touched.

## 7. Performance notes

- Monte Carlo is vectorised over histories where possible (free-flight sampling, distance-to-surface, weight accounting).
- Parallelism is *history-parallel* via `multiprocessing.Pool`; chunks are independent RNG streams seeded by `SeedSequence`.
- Point-kernel is fully vectorised over (source, receptor, energy).
- UQ parallelises over sample index.

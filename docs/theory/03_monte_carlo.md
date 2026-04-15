# Monte Carlo Photon Transport

## Overview

The Monte Carlo (MC) method solves the linear Boltzmann transport equation by simulating individual photon histories. Each history follows a sequence of random free-flight distances, interaction sites, and scattering events. The dose rate estimate converges to the true value as the number of histories N → ∞, with statistical uncertainty ~ 1/√N.

PyShield-SMR implements **analog and non-analog (variance-reduced) photon transport** in `pyshield_smr/transport/monte_carlo.py`.

## Analog Transport Algorithm

A single photon history:

```
1. Sample birth position and direction from source distribution.
2. Sample free-flight distance:  d = -ln(ξ) / μ_t(E)   where ξ ~ Uniform(0,1)
3. Transport to collision site; check geometry boundary.
   - If particle escapes geometry: record tally, terminate history.
4. Sample interaction type (photoelectric / Compton / pair) with probability
   proportional to partial cross-section fraction.
5. Photoelectric / pair production: absorb photon (weight → 0), terminate.
6. Compton scatter:
   a. Sample scattering angle θ from Klein-Nishina distribution (Kahn method).
   b. Update photon direction using rotation matrix.
   c. Update energy: E' = E / (1 + (E / 0.511)(1 - cos θ))
7. Return to step 2.
```

### Kahn Rejection Method for Klein-Nishina Sampling

The differential cross section is bounded by an envelope and sampled by rejection:

1. Choose with equal probability between two sampling strategies based on the Kahn (1954) decomposition.
2. Sample a candidate scatter energy $E'$.
3. Accept/reject with probability proportional to the exact Klein-Nishina value at $(E, E')$.

Typical acceptance rate is 50–80% at 1 MeV in lead. See `monte_carlo.py → _sample_compton_scatter()`.

## Non-Analog (Variance Reduction) Techniques

Standard analog transport can be extremely inefficient when the detector subtends a small solid angle or when shielding is thick. Two variance reduction techniques are implemented:

### 1. Implicit Capture

Instead of terminating the photon upon absorption, we reduce its **statistical weight** $w$ by the non-absorption probability at each collision:

$$w_\text{new} = w_\text{old} \times \frac{\sigma_s}{\sigma_t}$$

The photon continues after every collision (as Compton scatter), carrying a fractional weight. This eliminates the high variance from rare transmission events.

**Effect**: Reduces relative error by ~√(σ_t/σ_s) compared to analog; most effective for high-Z materials where σ_a >> σ_s.

### 2. Russian Roulette and Splitting

Particles with weight below a threshold $w_\text{low}$ are either killed (with probability $1 - w/w_\text{low}$) or boosted (weight → $w_\text{low}$). Particles above $w_\text{high}$ are split into $n = \lfloor w/w_\text{ref} \rfloor$ copies.

This keeps the population of active particles roughly constant and prevents wasting CPU on particles that will contribute negligibly to the tally.

Both techniques are configured via the YAML spec:

```yaml
monte_carlo:
  variance_reduction:
    implicit_capture: true
    roulette_split:
      w_low: 0.01
      w_high: 10.0
```

See `pyshield_smr/transport/variance_reduction.py`.

## Tallying and Uncertainty Estimation

A **tally** accumulates contributions from each history into an estimator of the dose rate:

$$\hat{D} = \frac{1}{N} \sum_{i=1}^{N} x_i$$

where $x_i$ is the score from history $i$ (zero if history does not reach the detector).

**Relative statistical error** (coefficient of variation):

$$\hat{\sigma}_r = \frac{1}{\hat{D}\sqrt{N}} \sqrt{\frac{\sum x_i^2}{N} - \hat{D}^2}$$

The MC simulation terminates when either:
- `n_histories` is reached, or
- `target_relative_error` is achieved (if specified).

Tally implementation: `pyshield_smr/transport/tally.py`.

## Figure of Merit

The **Figure of Merit (FOM)** measures transport efficiency independent of runtime investment:

$$\text{FOM} = \frac{1}{\hat{\sigma}_r^2 \cdot T}$$

where $T$ is wall-clock time. An efficient variance reduction configuration maximises FOM. FOM is recorded in `qa_manifest.json` for every MC run.

## Statistical Convergence Checks

The framework warns when:

- Relative error > `target_relative_error` (default 0.05 = 5%)
- Fewer than 10 non-zero scores were tallied (estimate unreliable regardless of σ)
- FOM degrades by > 30% compared to analog baseline (variance reduction is hurting)

See `pyshield_smr/transport/tally.py → TallyResult.check_convergence()`.

## Geometry

PyShield-SMR uses a **one-dimensional slab stack** geometry (`pyshield_smr/transport/geometry.py`):

```
Source       Layer 1   Layer 2  ...  Layer N      Receptor
  •  --------|---------|---------|---|---------|-----  •
             x₀        x₁       ...  x_{N-1}  x_N
```

Particles travel along the z-axis (1D) with isotropic source sampling. Ray tracing is performed by `SlabStack.traverse(position, direction)`, returning a list of `(material, path_length)` tuples.

**Extension to 3D**: The geometry module exports a `GeometryInterface` ABC; a 3D voxel or CAD geometry can be plugged in without changing the transport loop. Currently only `SlabStack` is implemented.

## Parallel Execution

For large histories counts, the transport loop is parallelised using `multiprocessing`:

```python
runner = ParallelMCRunner(spec, n_workers=8)
tallies = runner.run()   # distributes N/8 histories per worker
```

Independent RNG streams are seeded using `numpy.random.SeedSequence` with spawn, ensuring statistical independence between workers. See `pyshield_smr/hpc/parallel.py`.

## Comparison with Point-Kernel

See `docs/theory/02_point_kernel.md` §"Validation & Comparison with Monte Carlo" for the benchmark protocol. Short rule of thumb:

- μx < 5: point-kernel and MC agree within ±5%; use point-kernel for speed.
- μx 5–15: MC is the reference; point-kernel deviates due to buildup factor breakdown.
- μx > 15: Monte Carlo only; statistical noise is the limiting factor.

## Code Module Map

| File | Key functions |
|---|---|
| `transport/monte_carlo.py` | `run_monte_carlo()`, `_simulate_history()`, `_sample_compton_scatter()` |
| `transport/variance_reduction.py` | `implicit_capture_weight()`, `russian_roulette()`, `split_particle()` |
| `transport/tally.py` | `Tally`, `TallyResult`, `TallyResult.check_convergence()` |
| `transport/geometry.py` | `SlabStack`, `traverse()` |
| `transport/mcnp_io.py` | MCNP input deck I/O for cross-verification |
| `hpc/parallel.py` | `ParallelMCRunner` |

## References

- **Kahn, H.** (1954): "Use of Different Monte Carlo Sampling Techniques", RAND Corporation — original description of the Kahn rejection method for Klein-Nishina sampling.
- **Lux & Koblinger** (1991): "Monte Carlo Particle Transport Methods" — comprehensive reference on analog and non-analog techniques.
- **X-5 Monte Carlo Team** (2003): "MCNP — A General Monte Carlo N-Particle Transport Code, Version 5" — production code for comparison.
- **Shultis & Faw** (2000): "Radiation Shielding" — Chapter 4 covers MC shielding calculations.

## TBD: Topics for Expansion

- Neutron transport, (n,γ) secondary photon generation.
- Geometry-splitting variance reduction along the primary shielding axis.
- Point detector (next-event) estimators for better efficiency at deep-penetration tally points.
- Electron/positron secondary particle tracking.

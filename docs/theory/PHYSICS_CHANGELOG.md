# Physics Changelog

Record of all changes that could alter a dose result, a regression value, or a physics constant. Every entry must follow the format below. Written by the **Physics Governor** before coding the change.

Format:

```
## vX.Y.Z (YYYY-MM-DD)
- **[Component] [What changed] (commit <hash or "initial">)**:
  - Previous: [How it was]
  - New: [How it is now]
  - Impact: [What users observe]
  - Regression: [Which tests updated, why, or "no regression impact"]
```

---

## v0.1.1 (2026-04-15)

Bug-fix release. No new physics; corrects implementation errors that produced wrong dose-rate numbers in all point-kernel analyses.

- **[Buildup] Taylor two-term formula sign convention fixed (commit: session-2026-04-15)**:
  - Previous: `B = A * exp(-α₁ μx) + (1-A) * exp(-α₂ μx)` — both exponents negative. With A > 1 this makes B < 1 for all τ > 0, which is then clamped to 1. Net effect: buildup was silently disabled; all point-kernel doses computed without scatter contribution.
  - New: `B = A * exp(+α₁ μx) + (1-A) * exp(-α₂ μx)` — α₁ drives growth (positive), α₂ drives the complementary decay (negative). B(0) = 1 exactly; B grows correctly with optical depth.
  - Impact: Point-kernel dose rates increase by 30–60% for typical shielding depths (1–8 mfp in lead). Example 01 (Co-60, 5 cm lead): 1.08e-8 → 1.72e-8 Sv/h.
  - Regression: All five `examples/*/` regression values updated. See `tests/integration/regression_values.yaml`.

- **[Runner] Wrong import path for `assign_zone` (commit: session-2026-04-15)**:
  - Previous: `from pyshield_smr.shielding.zoning import assign_zone` — module does not exist; runner failed at import.
  - New: `from pyshield_smr.alarp.zoning import assign_zone` — correct location.
  - Impact: Runner was completely broken; no analysis could run.
  - Regression: No numerical change; import smoke test added to CI.

- **[Runner] 3-D position vector passed to 1-D point-kernel (commit: session-2026-04-15)**:
  - Previous: Runner passed `source_pos = [x, y, z]` as `source_position_m` directly to `point_kernel_dose_rate()`, which expects a scalar z-coordinate.
  - New: Runner extracts `source_pos[2]` and `recv_pos[2]` before passing to the engine.
  - Impact: Previously raised `ValueError: all receptor positions must be downstream of the source` because NumPy evaluated `[0,0,1] > [0,0,0]` element-wise.
  - Regression: No numerical change to correct physics; geometry error is now resolved.

- **[IO] YAML loader silently parsed `1.0e6` as string (commit: session-2026-04-15)**:
  - Previous: `yaml.safe_load()` (PyYAML 6.x / YAML 1.2) parses `1.0e6` as a string, not a float. All positive-exponent scientific notation in YAML specs silently became strings.
  - New: `_Yaml11Loader` extends `yaml.SafeLoader` with a YAML 1.1-style float resolver that accepts exponents without explicit sign.
  - Impact: Was silently corrupting source activities, neutron fluxes, irradiation durations in all specs. Format error appeared only at runner log level (format string on string instead of float).
  - Regression: All example values now load as `float`. Tests added in `tests/unit/test_yaml_config.py`.

## v0.1.0 (2026-04-14)

Initial scaffold. All physics components established from first principles. No prior version to compare against.

- **[Point-kernel] Taylor two-term buildup factors (commit: initial)**:
  - Previous: N/A (new code)
  - New: Taylor two-term form $B(τ, E) = A \exp(-α_1 τ) + (1-A)\exp(-α_2 τ)$, parameters from ANS-6.1.1 tables, interpolated from `data/buildup_factors/taylor_two_term.json`.
  - Impact: All point-kernel dose rates use this buildup model. Valid for μx ≤ 15.
  - Regression: No prior values; `examples/01_point_kernel_shielding` establishes Co-60/lead baseline.

- **[Attenuation] NIST XCOM log-log interpolation (commit: initial)**:
  - Previous: N/A
  - New: Mass attenuation coefficients from `data/cross_sections/photon_mass_attenuation.json` (NIST XCOM, educational reproduction). Interpolated on log(E)–log(μ/ρ) axes for accuracy between absorption edges.
  - Impact: Interpolation error < 1% over 0.1–10 MeV for all implemented materials.
  - Regression: No prior values.

- **[Dose conversion] ICRP-74 H*(10) coefficients (commit: initial)**:
  - Previous: N/A
  - New: H*(10) coefficients from `data/flux_to_dose/icrp74_photon.json`. Applied as $\dot{D} = \phi \cdot h_{10}(E)$ per energy bin.
  - Impact: Dose quantity is ambient dose equivalent. Results are directly comparable to IRR17 dose-rate thresholds.
  - Regression: No prior values.

- **[Monte Carlo] Kahn rejection sampling for Klein-Nishina (commit: initial)**:
  - Previous: N/A
  - New: Analog photon transport with Kahn (1954) rejection method for Compton scattering angle. Energy update via Compton kinematic relation.
  - Impact: MC results are statistically exact (converge to true value as N → ∞). Validated against point-kernel for thin-shield cases (μx < 2).
  - Regression: `examples/02_monte_carlo_transmission` establishes 1 MeV slab transmission baseline.

- **[Activation] Matrix-exponential Bateman solver (commit: initial)**:
  - Previous: N/A
  - New: `scipy.linalg.expm` for decay phase; single-step saturation formula for irradiation phase. Validated against analytic single-nuclide and two-nuclide chain solutions.
  - Impact: Activation source terms are correct to float64 precision for decay; irradiation uses simplified single-step model (see `docs/theory/05_activation_and_decay.md` limits).
  - Regression: `examples/03_activation_decay` establishes Co-60 irradiation+decay baseline.

- **[ALARP] SLSQP optimiser with point-kernel objective (commit: initial)**:
  - Previous: N/A
  - New: `scipy.optimize.minimize(method="SLSQP")` with dose-rate constraint. Objective is weighted sum of dose rate and shielding mass.
  - Impact: Optimised designs minimise dose subject to regulatory threshold. Convergence tolerance `ftol=1e-9`.
  - Regression: `examples/04_alarp_optimization` establishes lead optimisation baseline.

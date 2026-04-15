# Point-Kernel Method for Shielding Design

## Overview

The **point-kernel method** is a fast, analytical approach for computing dose rates from a radiation source through shielding. It's widely used in preliminary design and operational dose assessment because it requires only seconds of computation (vs. hours for Monte Carlo).

**Physics principle**: The dose rate at a receptor is determined by:
1. **Uncollided fluence** from the source (direct path through shielding)
2. **Scattered radiation** (photons scattered en route, which contribute to dose)

The point-kernel method approximates the total fluence as:

$$\Phi(r, E) = \Phi_0(r, E) \times B(τ, E)$$

where:
- $\Phi_0$ = uncollided fluence (source emission / 4πr² × exp(-τ))
- $B$ = buildup factor (accounts for scattered photons)
- $τ$ = optical depth (integral of attenuation coefficient along ray path)

## Mathematical Foundation

### Uncollided Fluence

For a point source emitting isotropically:

$$\Phi_0(r, E) = \frac{I(E)}{4\pi r^2} \exp(-\tau(r, E))$$

where:
- $I(E)$ = source intensity at energy E [photons/s]
- $r$ = distance from source to receptor [m]
- $τ$ = optical depth = $\int_0^r \mu_t(E) \, dx$ [dimensionless]
- $\mu_t$ = linear attenuation coefficient [m⁻¹]

**Physical interpretation**: 
- The 1/(4πr²) term accounts for geometric spreading (solid angle)
- The exp(-τ) term accounts for absorption and scattering out of the direct beam
- By definition, $\Phi_0$ includes only photons that never interacted

### Buildup Factor

The buildup factor $B(τ, E)$ empirically accounts for scattered photons that reach the receptor:

$$B(τ, E) = \frac{\text{Total fluence at receptor}}{\text{Uncollided fluence at receptor}} ≥ 1$$

For shielding problems, we use the **Taylor two-term form**:

$$B(τ, E) = A \exp(-α_1 τ) + (1 - A) \exp(-α_2 τ)$$

where:
- $A$ = fractional amplitude of first exponential (typically 0.1–0.4)
- $α_1, α_2$ = attenuation constants (typically 0.5–2.0 m⁻¹ equivalent)
- Parameters depend on energy E and shielding material

**Interpretation**:
- At small optical depths (thin shielding, τ << 1): B ≈ 1 + (...)τ (linear growth)
- At large optical depths (τ >> 1): B ≈ A exp(-α₁τ) (exponential decay)

### Dose Rate Calculation

Total dose rate is computed by integrating over energy:

$$\dot{D}(r) = \int_0^{\infty} \Phi(r, E) × B(τ, E) × h(E) \, dE$$

where:
- $h(E)$ = dose conversion factor [Sv·m²/photon] from ICRP-74 flux-to-dose coefficients

**Practical implementation**:
1. Discretize energy into N bins (e.g., 25 bins from 10 keV to 10 MeV)
2. For each energy bin: compute τ, B, and h
3. Sum: $\dot{D} ≈ Σ \Phi_0(E_i) × B(τ, E_i) × h(E_i) × ΔE_i$

## Implementation Details

### Optical Depth Computation

Given a ray path from source to receptor through a composite slab:

$$τ = \sum_{j=1}^{N} \mu(E, \text{material}_j) × x_j$$

where $x_j$ is thickness of layer j.

**Example** (from example/01_point_kernel_shielding):
- Source at z = 0, receptor at z = 1 m
- Lead slab: 0 < z < 0.05 m
- Air: 0.05 < z < 1 m

Optical depths:
- τ(lead) = μ_Pb(E) × 0.05
- τ(air) = μ_air(E) × 0.95 ≈ 0 (air is transparent)
- Total: τ ≈ μ_Pb(E) × 0.05

### Mass Attenuation Coefficient Interpolation

Mass attenuation coefficients μ/ρ (in cm²/g) are tabulated in NIST XCOM. We interpolate:

$$\log(μ/ρ) = \text{linear interpolation in } \log(E)$$

**Why log-log?** Attenuation is a smooth exponential function. On log-log scales, it becomes nearly linear between absorption edges, allowing simple linear interpolation with <1% error.

**Code example** (pyshield_smr/physics/attenuation.py):
```python
def interpolate_mass_attenuation(material, energies_MeV):
    """Log-log interpolation of μ/ρ from tabulated values."""
    log_e = np.log(energies_MeV)
    log_mu = np.interp(log_e, material.energies_log, material.mu_log)
    return np.exp(log_mu)
```

### Buildup Factor Selection

This framework uses **Taylor two-term** buildup factors (ANS-6.1.1 standard):

$$B = A \exp(-α_1 μx) + (1 - A) \exp(-α_2 μx)$$

**Alternative forms** (not implemented, but documented):
1. **Geometric Progression** (ANS-6.4.3): $B = (K-1) b^{μx} / (K - b^{μx})$
   - More accurate for very thick shielding (μx > 10)
   - More complex parameters
   - Preferred in production MCNP6/SCALE codes

2. **Exponential** (simple): $B = e^{μx(1/λ - 1)}$
   - Very simple but less accurate
   - Good for order-of-magnitude estimates

### Buildup Factor Limitations

The buildup factor approach has known limitations:

1. **Valid for 0 < μx < 20 mean free paths**: Beyond this, exponential formulas break down
2. **Single-material assumption**: Assumes most scattering happens in first (thickest) layer
3. **Photon-only**: Doesn't account for neutron-induced gamma rays or charged particles
4. **Isotropic point source assumption**: Real sources (fuel rods, activated components) have structure
5. **No spatial correlations**: Buildup at one energy assumed independent of other energies

**Best practices**:
- For μx < 5: Trust Taylor two-term to within ±5%
- For 5 < μx < 10: Expect ±10% uncertainty; use UQ to quantify
- For μx > 10: Consider Monte Carlo validation; add design margin (e.g., ×1.5 on dose)

## Code Architecture

Point-kernel dose-rate calculation is split into:

1. **Geometry**: `pyshield_smr/transport/geometry.py`
   - `SlabStack`: Stores material layers and thicknesses
   - `traverse()`: Traces ray path and returns list of (material, path_length) tuples

2. **Physics**: `pyshield_smr/physics/`
   - `interpolate_mass_attenuation()`: log-log interpolation of μ/ρ
   - `linear_attenuation_coefficient()`: converts μ/ρ to linear μ accounting for density
   - `taylor_buildup()`: Evaluates B(μx, E, material)
   - `flux_to_dose_h10()`: ICRP-74 dose conversion

3. **Integration**: `pyshield_smr/shielding/point_kernel.py`
   - `point_kernel_dose_rate()`: Main orchestration function
   - Loops over source energies, receptors
   - For each (energy, receptor): computes τ, B, h, accumulates dose

4. **Workflow**: `pyshield_smr/workflow/runner.py`
   - `_run_point_kernel()`: Resolves spec parameters and calls point_kernel_dose_rate()

## Validation & Comparison with Monte Carlo

When is point-kernel valid?

| Scenario | Point-Kernel | Monte Carlo |
|----------|---------|-----------|
| Thin shielding (μx < 2) | ✓ Excellent (B ≈ 1) | ✓ Slower, noisier |
| Medium shielding (2 < μx < 10) | ✓ Good (±10%) | ✓ Gold standard, slower |
| Thick shielding (μx > 10) | ✗ Poor (buildup formula breaks down) | ✓ Only reliable method |
| Complex geometry | ✗ Limited to slabs | ✓ Handles arbitrary geometry |
| Multi-nuclide sources | ✓ Fast | ✓ More complex code |
| Design optimization | ✓ Fast (100s of designs/second) | ✗ Too slow for optimization loop |

**Validation strategy** (from example/02):
1. Run point-kernel on a simple slab geometry
2. Run Monte Carlo on the same geometry with 10⁶–10⁸ histories
3. Compare dose rates: should agree within ±10%
4. If disagreement > 10%: investigate buildup factor validity

**Expected agreement sources of error**:
- MC statistical error: ±√(1/N_histories)
- Buildup factor accuracy: ±5–10% depending on μx
- Geometry differences: point-kernel assumes infinite slab; MC enforces boundaries

## Example Walkthrough: example/01

**Problem**: Co-60 point source (1 MBq) at z=0; 5 cm lead slab (0–5 cm); receptor at z=100 cm. Compute dose rate.

**Solution**:

1. **Parse source**: Co-60 → gamma-line library → [1.17 MeV: 0.996/2, 1.33 MeV: 1.000/2]

2. **Parse geometry**: lead, 0.05 m → SlabStack([lead], [0.05])

3. **For each photon line** (e.g., 1.17 MeV):
   - Get intensity: 0.5 × 1e6 = 5e5 /s
   - Compute distance: r = 1.0 m
   - Uncollided fluence: Φ₀ = 5e5 / (4π×1²) × exp(-μ_Pb(1.17)×0.05)
     - μ_Pb(1.17 MeV) ≈ 0.039 cm⁻¹ (NIST XCOM)
     - τ = 0.039 × 5 = 0.195 mean free paths
     - exp(-0.195) ≈ 0.823
   - Buildup: B(0.195, 1.17 MeV, lead) ≈ 1.08 (interpolated from data)
   - Total fluence: Φ = 0.823 × 1.08 ≈ 0.889 of uncollided value
   - Dose conversion: h(1.17 MeV) ≈ 20 pSv·cm² (ICRP-74)
   - Contribution: 5e5/(4π) × 0.889 × 20e-12 ≈ 7.1e-6 Sv/h

4. **Repeat for 1.33 MeV** (similar calculation)

5. **Total dose rate**: ~1.4e-5 Sv/h = 14 µSv/h

6. **Zone assignment**: 14 µSv/h is in "controlled area" (> 2.5 µSv/h threshold)

## Extensions & Future Work

### Potential Improvements

1. **Geometric Progression buildup**: Better accuracy for μx > 10
2. **Multi-layer buildup**: Different buildup for each layer (not just first)
3. **Anisotropic point sources**: Account for fuel rod geometry (line source, area source)
4. **Neutron attenuation**: Extend to (n,γ) reactions and fast neutron dose
5. **Directional dose**: H*(10) conversion factor depends on photon direction; account for this

### When to Use Monte Carlo Instead

If any of these apply, Monte Carlo is required:
- μx > 15 (buildup formula unreliable)
- Geometry is complex (not a slab)
- Source is extended (not point-like)
- Need variance reduction (optimize shielding → expensive repeated evaluations)

## References

- **ANS-6.1.1**: "Gamma-Ray Attenuation Coefficients and Buildup Factors for Engineering Materials" (American Nuclear Society)
- **ICRP-74**: "Conversion Coefficients for Use in Radiological Protection Against External Radiation" (International Commission on Radiological Protection)
- **NIST XCOM**: Photon mass attenuation coefficients tabulated online
- **Evans, R.D.** (1955): "The Atomic Nucleus" — classic reference on photon interactions
- **Knoll, G.F.** (2000): "Radiation Detection and Measurement" — modern comprehensive text

## Summary

The point-kernel method is a **fast, analytical approach** suitable for:
- Initial shielding design (μx < 10)
- Dose-rate operational assessments
- ALARP optimization (requires many evaluations)
- Parametric studies (how does dose vary with thickness?)

Its **limitations** are well-understood and documented. Analysts should:
1. Validate against Monte Carlo on simple benchmark cases
2. Quantify buildup factor uncertainty via UQ
3. Add design margins (×1.2–1.5) for regulatory robustness
4. Consider Monte Carlo if μx > 10

---

**PyShield-SMR** implements the point-kernel method with full traceability: every constant, every interpolation, every buildup factor is documented with references. This enables both **learning** (understand the physics) and **reproducibility** (audit the calculation).

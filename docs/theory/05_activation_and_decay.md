# Activation and Radioactive Decay

## Overview

Neutron activation converts stable structural materials into radionuclides, which then decay by γ emission and contribute to the post-shutdown dose field. This document covers:

1. **The Bateman equations** — the ODE system governing nuclide population evolution.
2. **Matrix exponential method** — the numerical approach used in `activation/bateman.py`.
3. **Simplified burn-up model** — how neutron flux and irradiation time are combined.

## The Bateman Equations

For a linear decay chain $A_1 \to A_2 \to \cdots \to A_N$ (with possible branching fractions $b_{ij}$):

$$\frac{dN_i}{dt} = -(\lambda_i + \phi \sigma_i) N_i + \sum_{j < i} b_{ji} \lambda_j N_j + \sum_{j < i} \phi \sigma_{ji} N_j$$

where:
- $N_i(t)$ = number density of nuclide $i$ [atoms/cm³]
- $\lambda_i = \ln 2 / t_{1/2,i}$ = radioactive decay constant [s⁻¹]
- $\phi$ = scalar neutron flux [n/cm²/s]
- $\sigma_i$ = one-group neutron capture cross section [cm²]
- $b_{ji}$ = branching fraction from nuclide $j$ to $i$ by decay
- $\sigma_{ji}$ = capture cross section of $j$ producing $i$

In matrix form:

$$\frac{d\mathbf{N}}{dt} = \mathbf{A} \mathbf{N}(t)$$

where $\mathbf{A}$ is the **transition matrix**, with diagonal entries $-(\lambda_i + \phi \sigma_i)$ and off-diagonal entries $b_{ji}\lambda_j + \phi \sigma_{ji}$.

## Matrix Exponential Solution

The exact solution is:

$$\mathbf{N}(t) = \exp(\mathbf{A} t) \, \mathbf{N}(0)$$

PyShield-SMR computes $\exp(\mathbf{A} t)$ using `scipy.linalg.expm` for the decay step (where $\phi = 0$, so $\mathbf{A}$ is purely from radioactive decay). The irradiation step can alternatively use eigenvalue decomposition when the chain is short.

See `decay_matrix` and `decay_inventory` in `pyshield_smr/activation/bateman.py`. There is no `BatemanSolver` class.

### Two-Step Approach

The workflow decomposes each analysis into:

1. **Irradiation phase** (duration $t_\text{irr}$, flux $\phi$): Build up activation products.
   $$\mathbf{N}(t_\text{irr}) = \exp(\mathbf{A}_\text{irr} t_\text{irr}) \, \mathbf{N}(0)$$
2. **Decay phase** (cooling time $t_c$ after shutdown, $\phi = 0$): Activity decreases.
   $$\mathbf{N}(t_\text{irr} + t_c) = \exp(\mathbf{A}_\text{decay} \, t_c) \, \mathbf{N}(t_\text{irr})$$

Activity of nuclide $i$ at any time:

$$A_i(t) = \lambda_i N_i(t) \quad [\text{Bq/cm}^3]$$

Gamma source intensity from nuclide $i$ at energy $E_j$:

$$I_{ij}(t) = A_i(t) \cdot Y_{ij} \quad [\text{photons/s/cm}^3]$$

where $Y_{ij}$ is the gamma yield at line $j$ (photons per disintegration).

## Simplified Burn-up Model

Full burnup (changing fuel composition, varying spectrum) is out of scope. PyShield-SMR uses a **single-irradiation-step approximation**:

1. User specifies $\phi$, $t_\text{irr}$, target material composition (element fractions).
2. For each element, look up dominant (n,γ) reactions from `data/decay_chains/short.json`.
3. Compute equilibrium activity for each activation product.
4. Pass resulting activity to the source-term builder.

**Saturation activity** for a single nuclide (steady state, $t_\text{irr} \gg t_{1/2}$):

$$A_\text{sat} = \phi \sigma N_0$$

For $t_\text{irr} < 5 t_{1/2}$ (build-up not saturated):

$$A(t_\text{irr}) = A_\text{sat} \left(1 - e^{-\lambda t_\text{irr}}\right)$$

The single-channel form is `simple_burnup_buildup` in `activation/burnup.py`. There is no `compute_activation`.

## YAML Spec: Activation Input

```yaml
activation:
  enabled: true
  neutron_flux_n_cm2_s: 5.0e13
  irradiation_duration_s: 3.156e7     # 1 year
  cooling_time_s: 3600                 # 1 hour post-shutdown
  materials:
    - name: stainless_steel_316
      mass_kg: 5000
      composition:
        Fe: 0.65
        Cr: 0.17
        Ni: 0.12
        Mo: 0.025
```

The workflow runner does not read an `activation` block and does not merge a Bateman inventory into the source. `build_source_from_inventory` turns a `{nuclide: becquerels}` dict into photon lines. Example 03 puts a Co-60 activity in the YAML and runs the point kernel on that activity.

## Numerical Considerations

- **Short-lived nuclides** ($t_{1/2}$ < 1 s) produce stiff ODEs; `scipy.linalg.expm` handles this correctly (unlike explicit Euler methods which would require very small time steps).
- **Sparse chains**: Most nuclides connect to only one or two daughters. The $\mathbf{A}$ matrix is sparse; `scipy.sparse.linalg.expm_multiply` can be used for large chains (not yet implemented).
- **Numerical zero threshold**: Activities below $10^{-12}$ × peak activity are considered zero and suppressed from the source term to avoid floating-point noise accumulating in spectra.

## Code Module Map

| File | Key class / function |
|---|---|
| `activation/bateman.py` | `decay_matrix`, `decay_inventory` |
| `activation/burnup.py` | `simple_burnup_buildup` |
| `sources/source_term.py` | `build_source_from_inventory` |
| `data/decay_chains/short.json` | Gamma lines, half-lives, branching fractions |

## Validation

Nothing in `tests/` imports `decay_inventory` or `simple_burnup_buildup`. `tests/unit/test_physics_constants.py` checks physical constants, not a Bateman benchmark. `docs/guides/QA.md` is not in the repository. This file does not quote an error for the solver.

## References

- **Bateman, H.** (1910): "The solution of a system of differential equations occurring in the theory of radioactive transformations", Proc. Cambridge Phil. Soc. 15, 423–427 — original derivation.
- **Moler & Van Loan** (2003): "Nineteen dubious ways to compute the exponential of a matrix, twenty-five years later", SIAM Review — comprehensive guide to matrix exponential algorithms.
- **Lamarsh & Baratta** (2001): "Introduction to Nuclear Engineering", Chapter 4 — radioactive decay and activation.
- **IAEA-TECDOC-1234**: Neutron activation cross sections relevant to reactor structural materials.

## TBD: Topics for Expansion

- Multi-cycle burnup: alternating flux-on/flux-off with spectral hardening.
- Full ORIGEN-S or FISPACT integration for production inventory calculations.
- Branching ratio uncertainty propagation via UQ module.
- Photonuclear reactions (γ, n) for very high-energy source fields.

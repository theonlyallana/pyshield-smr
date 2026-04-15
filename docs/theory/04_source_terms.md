# Source Terms: Fission Products and Activation Gamma Spectra

## Overview

A radiation shielding analysis begins with a **source term** — the energy spectrum and intensity of photons emitted by the radioactive inventory inside the SMR. PyShield-SMR builds source terms from two independent inventories:

1. **Fission-product photons** — from the fission fragment decay chain in the fuel.
2. **Activation gammas** — from neutron activation of structural materials (steel, zircaloy cladding, coolant).

Both inventories are computed by `pyshield_smr/sources/source_term.py` and exposed to the workflow engine via the `SourceTerm` dataclass.

## Fission-Product Source Term

### Physical Origin

When a heavy nucleus (⁲³⁵U, ²³⁹Pu) undergoes fission, it produces two fission fragments with mass numbers roughly 90–100 (light fragment) and 130–145 (heavy fragment). These fragments are highly neutron-rich and undergo a chain of β⁻ decays, each accompanied by gamma emission:

```
Fission fragment → β⁻ + ν̄_e → daughter nucleus* → γ + daughter nucleus (ground state)
```

Key contributors (CRUD and primary fission products):

| Nuclide | Half-life | Main γ energy [MeV] | Yield per fission |
|---|---|---|---|
| ⁹⁰Kr | 32.3 s | 1.118, 1.531 | 0.019 |
| ¹³⁷Cs | 30.1 yr | 0.662 | 0.061 |
| ¹³⁴Cs | 2.06 yr | 0.605, 0.796 | burnup-dependent |
| ¹³¹I | 8.02 d | 0.364 | 0.029 |
| ¹³³Xe | 5.24 d | 0.081 | 0.068 |

### Implementation

`pyshield_smr/sources/source_term.py → build_fission_product_source()`:

1. Look up the YAML spec `source.nuclides` list and activities [Bq].
2. For each nuclide, fetch the gamma-line library from `data/decay_chains/short.json`.
3. Construct the discrete energy spectrum:
   $$I(E_j) = A \cdot Y_j \quad [\text{photons/s per energy bin } j]$$
   where $A$ = activity [Bq], $Y_j$ = gamma yield at energy $E_j$ [photons/disintegration].

The result is a `Spectrum` object: a list of `(energy_MeV, intensity_ph_per_s)` pairs. See `pyshield_smr/sources/spectra.py`.

## Activation Source Term

### Physical Origin

Structural materials exposed to the neutron flux in the reactor core undergo **(n,γ)** reactions, producing radioactive isotopes that decay by gamma emission after shutdown. Major contributors:

| Parent material | Activation product | Half-life | Main γ [MeV] |
|---|---|---|---|
| ⁵⁸Ni (steel) | ⁵⁸Co | 70.9 d | 0.811 |
| ⁵⁴Fe (steel) | ⁵⁴Mn | 312 d | 0.835 |
| ⁶⁰Co (trace) | ⁶⁰Co | 5.27 yr | 1.173, 1.332 |
| ²⁷Al (cladding) | ²⁸Al | 2.24 min | 1.779 |

### Activation Calculation

Activation is computed by `pyshield_smr/activation/`:

$$\frac{dN_i}{dt} = \phi \sigma_i N_{i-1} - \lambda_i N_i$$

where:
- $N_i$ = number density of nuclide $i$ [cm⁻³]
- $\phi$ = neutron flux [n/cm²/s]
- $\sigma_i$ = neutron capture cross section [barn]
- $\lambda_i = \ln 2 / t_{1/2}$ = decay constant [s⁻¹]

After a shutdown at time $t_s$, the activity of each nuclide decays as:

$$A_i(t) = A_i(t_s) \cdot e^{-\lambda_i (t - t_s)}$$

The full decay chain (Bateman equations) is solved by `pyshield_smr/activation/bateman.py`. See `docs/theory/05_activation_and_decay.md` for the Bateman solver.

## Combined Source Spectrum

The workflow engine (`pyshield_smr/workflow/runner.py → _build_source_term()`) merges fission-product and activation contributions into a single `Spectrum`, binned on a common energy grid.

Energy grid: 25 log-spaced bins from 0.1 MeV to 10 MeV (configurable via YAML `source.energy_grid`).

```yaml
source:
  type: mixed
  nuclides:
    - name: Co-60
      activity_bq: 1.0e9
    - name: Cs-137
      activity_bq: 5.0e11
  energy_grid:
    n_bins: 25
    e_min_mev: 0.1
    e_max_mev: 10.0
```

## Source Geometry

The source term currently models a **point isotropic source**. The YAML spec positions it via `source.position_m: [x, y, z]`.

For distributed sources (fuel assemblies, activated piping runs), the analyst splits the source into multiple point sources at different positions and sums contributions — or uses the MC geometry directly. This is the principal limitation of the current implementation.

## Data: Decay Chain Library

Gamma-line data is vendored in `data/decay_chains/short.json`. The file stores:

```json
{
  "Co-60": {
    "half_life_s": 1.6634e8,
    "gamma_lines": [
      {"energy_mev": 1.1732, "yield": 0.9985},
      {"energy_mev": 1.3325, "yield": 0.9998}
    ]
  },
  ...
}
```

Provenance is recorded in `data/decay_chains/short.meta.json` (source: NUBASE2020 / ENSDF, retrieval date, accuracy).

## Code Module Map

| File | Purpose |
|---|---|
| `sources/source_term.py` | Top-level `build_source_term()`, `SourceTerm` dataclass |
| `sources/spectra.py` | `Spectrum` type, `merge_spectra()`, `discretise()` |
| `activation/bateman.py` | Bateman solver for decay chains |
| `activation/burnup.py` | Simplified burn-up model (neutron flux × time → activation) |
| `data/decay_chains/short.json` | Vendored gamma-line library |

## Limits of Validity

- **Point-source approximation**: Valid when source-to-receptor distance >> source dimensions. For compact SMR components, this may hold reasonably well; for fuel assemblies, a line-source or distributed-source model should be used.
- **Simplified nuclear data**: The vendored library covers ~30 key nuclides relevant to LWR/SMR operation. Production analyses should use ORIGEN-S (SCALE) or FISPACT for full inventory calculations.
- **No burnup history**: Current activation model uses a single-step irradiation followed by decay. Multi-cycle burnup (varying flux, varying composition) is not modelled. See `activation/burnup.py` for the current simplification.

## References

- **ICRP-107** (2008): "Nuclear Decay Data for Dosimetric Calculations" — authoritative decay data.
- **NUBASE2020**: Wang et al. (2021), Chinese Physics C 45(3) — half-lives, mass excesses.
- **Lamarsh & Baratta** (2001): "Introduction to Nuclear Engineering" — Chapter 10 covers fission product inventories.
- **IAEA-TECDOC-1234**: "Nuclear data for neutron activation calculations" — activation cross sections.

## TBD: Topics for Expansion

- Line and volume source geometry (fuel assembly, coolant loop piping).
- Full ORIGEN-S / FISPACT integration for production-quality inventory calculations.
- Multi-cycle burnup with variable flux and spectrum.
- Neutron source term (for shielding against fast and thermal neutrons).

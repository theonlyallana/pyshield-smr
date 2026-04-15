# Radiation Transport Theory

## Overview

Radiation transport describes how particles (photons, neutrons) move through matter, losing energy and changing direction through scattering and absorption. The governing equation is the **linear Boltzmann transport equation** (BTE), which tracks the angular flux of particles as a function of position, direction, and energy.

PyShield-SMR implements photon transport via two complementary methods:

1. **Point-kernel (analytical)** — integrates the BTE analytically along a ray, using empirical buildup factors to account for scattered radiation. Fast, limited to slab geometries. See `docs/theory/02_point_kernel.md`.
2. **Photon Monte Carlo** — samples the BTE stochastically, tracking individual photon histories through geometry. Exact for the physics implemented; slower but geometry-general. See `docs/theory/03_monte_carlo.md`.

## The Linear Boltzmann Transport Equation

For a steady-state mono-energetic photon field in 3D:

$$\hat{\Omega} \cdot \nabla \Psi(\mathbf{r}, \hat{\Omega}, E) + \Sigma_t(\mathbf{r}, E) \Psi = \int \Sigma_s(\mathbf{r}, E' \to E, \hat{\Omega}' \to \hat{\Omega}) \Psi \, d\hat{\Omega}' \, dE' + S(\mathbf{r}, \hat{\Omega}, E)$$

where:
- $\Psi(\mathbf{r}, \hat{\Omega}, E)$ = angular flux [photons / (cm² s sr MeV)]
- $\hat{\Omega}$ = unit direction vector
- $\Sigma_t$ = total macroscopic cross section (absorption + scatter) [cm⁻¹]
- $\Sigma_s$ = differential scattering cross section [cm⁻¹ sr⁻¹ MeV⁻¹]
- $S$ = external source term [photons / (cm³ s sr MeV)]

**Scalar fluence rate** (what dose coefficients are applied to):

$$\phi(\mathbf{r}, E) = \int_{4\pi} \Psi(\mathbf{r}, \hat{\Omega}, E) \, d\hat{\Omega}$$

## Photon Interactions with Matter

For photon energies 0.1–10 MeV (the range of interest for fission products and activation gammas):

| Interaction | Cross section symbol | Energy range dominant | Effect |
|---|---|---|---|
| Photoelectric effect | $\sigma_{pe}$ | < 0.5 MeV (high-Z) | Photon absorbed; electron ejected |
| Compton scatter | $\sigma_C$ | 0.1–10 MeV | Photon scattered, loses energy |
| Pair production | $\sigma_{pp}$ | > 1.022 MeV | Photon converts to e⁺e⁻ pair |

Total linear attenuation coefficient:

$$\mu(E) = \rho \left(\frac{\mu}{\rho}\right)_\text{total}(E) = \rho \left[\left(\frac{\mu}{\rho}\right)_{pe} + \left(\frac{\mu}{\rho}\right)_C + \left(\frac{\mu}{\rho}\right)_{pp}\right]$$

Mass attenuation coefficients are tabulated in `data/cross_sections/photon_mass_attenuation.json` from NIST XCOM. See `pyshield_smr/physics/attenuation.py` for interpolation details.

## Compton Scattering (Klein-Nishina Formula)

The dominant interaction in the 0.5–5 MeV range. The differential cross section per electron:

$$\frac{d\sigma_C}{d\Omega} = \frac{r_e^2}{2} \left(\frac{E'}{E}\right)^2 \left(\frac{E'}{E} + \frac{E}{E'} - \sin^2\theta\right)$$

where:
- $r_e = 2.818 \times 10^{-13}$ cm = classical electron radius
- $E$ = incident photon energy [MeV]
- $E'$ = scattered photon energy [MeV]
- $\theta$ = scattering angle

Energy-angle relationship (Compton kinematics):

$$E' = \frac{E}{1 + \frac{E}{m_e c^2}(1 - \cos\theta)}, \quad m_e c^2 = 0.511 \text{ MeV}$$

Monte Carlo sampling of the scattering angle uses the Kahn rejection method. See `pyshield_smr/transport/monte_carlo.py`.

## Mean Free Path and Optical Depth

The **mean free path** is the average distance a photon travels before interaction:

$$\lambda = \frac{1}{\mu_t(E)} \quad [\text{cm}]$$

**Optical depth** along a ray path from source to receptor:

$$\tau = \int_0^L \mu_t(E, \mathbf{r}) \, dl$$

For a slab stack of $N$ layers:

$$\tau = \sum_{j=1}^{N} \mu_j(E) \cdot x_j$$

The probability of **no interaction** over path length $L$ is $e^{-\tau}$ (Beer-Lambert law). This is the uncollided fraction used by the point-kernel method.

## Dose Quantity Convention

This framework computes **H\*(10) — ambient dose equivalent** — as the primary dose quantity, following ICRP-74 recommendations. H\*(10) is the dose equivalent at 10 mm depth in the ICRU sphere for a field aligned with the reference direction.

$$H^*(10)(E) = \phi(E) \cdot h_{10}(E)$$

where $h_{10}(E)$ [pSv·cm²/photon] is the ICRP-74 conversion coefficient. Tabulated values are in `data/flux_to_dose/icrp74_photon.json`.

**Zone thresholds** (conventional for occupational use):

| Dose rate | Zone |
|---|---|
| < 1 µSv/h | Public / unrestricted |
| 1–7.5 µSv/h | Supervised area |
| > 7.5 µSv/h | Controlled area |

## Units Policy

All internal quantities follow the unit policy stated in `tasks/process_state.md`:

- Distances: metres [m]
- Energies: MeV
- Cross sections: barns internally; converted to cm² at the transport boundary
- Dose: sieverts per hour [Sv/h]
- Fluence: photons / cm²

See `pyshield_smr/physics/units.py` for the unit conversion helpers. **Quantities are never passed bare** — always use the helpers or annotate with comments.

## Code Architecture

| Physics concept | Implementation |
|---|---|
| Mass attenuation coefficients | `pyshield_smr/physics/attenuation.py` |
| Linear attenuation, optical depth | `pyshield_smr/physics/attenuation.py` |
| Buildup factors (Taylor two-term) | `pyshield_smr/physics/buildup.py` |
| Dose conversion (ICRP-74) | `pyshield_smr/physics/dose.py` |
| Physical constants (CODATA 2018) | `pyshield_smr/physics/constants.py` |
| Material definitions | `pyshield_smr/physics/materials.py` |
| Slab geometry, ray tracing | `pyshield_smr/transport/geometry.py` |
| Photon MC solver | `pyshield_smr/transport/monte_carlo.py` |
| Tally / detector response | `pyshield_smr/transport/tally.py` |

## References

- **Lewis & Miller** (1984): "Computational Methods of Neutron Transport" — rigorous BTE derivation.
- **Shultis & Faw** (2000): "Radiation Shielding" — photon transport for engineering applications.
- **ICRP-74** (1996): "Conversion Coefficients for Use in Radiological Protection Against External Radiation" — H\*(10) dose coefficients.
- **NIST XCOM**: Online database of photon cross sections, https://physics.nist.gov/PhysRefData/Xcom/
- **CODATA 2018**: Fundamental physical constants used in `constants.py`.

## TBD: Topics for Expansion

- Neutron transport (currently out of scope; analog photon-only MC is implemented).
- Secondary electron transport and charged-particle equilibrium assumptions.
- Energy-group multigroup transport as an alternative to continuous-energy MC.
- Kerma approximation and its validity regime.

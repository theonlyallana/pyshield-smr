# physics-governor — logbook

## 2026-04-14 — initial physics baseline

- Seeded `data/flux_to_dose/icrp74_photon.json` with 25-point ICRP-74 H*(10) conversion coefficients for photons (40 keV–10 MeV).
- Seeded `data/cross_sections/photon_mass_attenuation.json` with NIST XCOM-style total mass attenuation coefficients for: water, concrete (ordinary), Fe, Pb, borated polyethylene (5% B), air (at 8 standard energies).
- Seeded `data/buildup_factors/taylor_two_term.json` with two-term Taylor buildup parameters for water, concrete, iron and lead at 0.5–10 MeV.
- Seeded `data/decay_chains/short.json` with ten common activation nuclides (e.g. Co-60, Co-58, Mn-54, Fe-59, Cs-137, I-131, H-3, C-14, Ar-41, N-16).
- Stated unit convention: length m, energy MeV, cross section barns (converted to cm² at transport boundary), density g/cm³, dose Sv/h.
- Declared `H*(10)` as default dose quantity.
- Verification: unit tests `tests/unit/test_physics_core.py` assert interpolation of coefficients, round-trip of units, and buildup monotonicity.

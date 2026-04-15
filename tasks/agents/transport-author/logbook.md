# transport-author — logbook

## 2026-04-14 — engines landed

- Implemented 3-D ray-tracing geometry for axis-aligned slab stacks and spheres.
- Implemented analog photon MC with Klein–Nishina scattering sampling and exponential free-flight.
- Added non-analog MC: implicit capture, Russian roulette below a weight threshold, particle splitting at weight-window boundaries.
- Implemented point-kernel shielding with Taylor two-term buildup.
- Added DPA, gamma-heating, and flux-to-dose post-processors.
- Seeded pinned-seed regression tests for both engines against analytical attenuation.

# ALARP Optimisation

## Overview

**ALARP (As Low As Reasonably Practicable)** is the legal and regulatory requirement in nuclear industries that radiation doses to workers and the public be reduced as far as is reasonably practicable. This document covers:

1. The regulatory basis for ALARP in SMR design.
2. The optimisation problem formulation used in PyShield-SMR.
3. The numerical implementation in `pyshield_smr/alarp/`.

## Regulatory Context

ALARP is mandated in UK and many international jurisdictions:

- **IRR17** (UK Ionising Radiation Regulations 2017) — employers must reduce dose to ALARP.
- **ONR Safety Assessment Principles** (SAPs 2014) — explicit ALARP demonstration required for nuclear facilities.
- **ICRP Publication 103** (2007) — dose limits and optimisation principles.

Key dose limits (occupational, per year):

| Limit | Dose [mSv/yr] | Equivalent dose rate [µSv/h] (2000 h/yr) |
|---|---|---|
| Legal limit (UK IRR17) | 20 | 10 |
| Investigation level | 6 | 3 |
| ALARP target (design goal) | 1 | 0.5 |

For design purposes, we convert occupational dose limits to dose-rate thresholds assuming 2000 working hours per year.

## ALARP Optimisation Formulation

PyShield-SMR formulates ALARP shielding design as a **scalar constrained optimisation**:

$$\min_{\mathbf{x}} \; J(\mathbf{x}) = w_1 \cdot \dot{D}(\mathbf{x}) + w_2 \cdot C(\mathbf{x})$$

subject to:

$$\dot{D}(\mathbf{x}) \leq \dot{D}_\text{max}$$
$$x_i^\text{lo} \leq x_i \leq x_i^\text{hi} \quad \forall i$$

where:
- $\mathbf{x}$ = shielding design variables (thicknesses, material choices) [m]
- $\dot{D}(\mathbf{x})$ = dose rate at the design receptor [Sv/h]
- $C(\mathbf{x})$ = cost proxy (shielding mass, installation cost) [kg or £]
- $w_1, w_2$ = weights (analyst-specified to balance dose reduction against cost)
- $\dot{D}_\text{max}$ = hard dose-rate constraint [Sv/h]

**Interpretation**: The objective minimises a weighted sum of collective dose and cost. Increasing $w_1/w_2$ pushes towards lower dose at higher cost; decreasing it accepts more dose if the cost saving is large enough. The analyst justifies the chosen weights as part of the ALARP demonstration.

## Why a Trade-off Surface, Not a Binary Answer

For a given budget, there exists a **Pareto front** of designs that are not dominated (lowering dose further requires more cost). The regulator asks: "Is the remaining dose justified by the cost of further reduction?" This is the ALARP judgment.

PyShield-SMR makes this concrete by:
1. Solving the optimisation at several $w_1/w_2$ ratios to trace the Pareto front.
2. Reporting dose and cost at each point.
3. Letting the analyst annotate which point is the ALARP choice and justify it.

## Numerical Implementation

### Solver

`pyshield_smr/alarp/optimiser.py → ALARPOptimiser` uses `scipy.optimize.minimize` with:
- Method: `SLSQP` (Sequential Least-Squares Programming) — handles nonlinear constraints and bounds.
- Gradient: finite-difference approximation (central difference).
- Constraint: `dose_rate(x) ≤ dose_rate_max` enforced as inequality constraint.

```python
result = scipy.optimize.minimize(
    fun=objective,
    x0=x_initial,
    method="SLSQP",
    bounds=bounds,
    constraints=[{"type": "ineq", "fun": lambda x: dose_rate_max - dose_rate(x)}],
    options={"ftol": 1e-9, "maxiter": 200},
)
```

The dose-rate function $\dot{D}(\mathbf{x})$ calls the point-kernel solver (fast, ~milliseconds per evaluation), making the full optimisation tractable in seconds.

### Radiological Zoning

After solving, `pyshield_smr/alarp/zoning.py → assign_zone()` maps the optimised dose rate to a radiological zone:

| Zone | Dose rate threshold | Regulatory basis |
|---|---|---|
| Unrestricted | < 1 µSv/h | Public area |
| Supervised | 1–7.5 µSv/h | IRR17 Supervised Area |
| Controlled | > 7.5 µSv/h | IRR17 Controlled Area |

Zone assignment is included in the report and QA manifest.

## YAML Spec

```yaml
alarp:
  enabled: true
  objective:
    health_weight: 1.0            # dimensionless
    cost_weight: 0.01             # per kg of shielding mass
  constraints:
    dose_rate_sv_per_h_max: 7.5e-6  # Controlled area threshold
  variables:
    - name: thickness_m
      material: lead
      lower_bound: 0.01           # 1 cm minimum
      upper_bound: 0.50           # 50 cm maximum
      initial_guess: 0.05
  pareto_scan:
    enabled: true
    n_points: 10                  # Trace 10-point Pareto front
    weight_ratios: [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
```

## Sensitivity Analysis Post-Optimisation

After finding the optimal design $\mathbf{x}^*$, a ±10% parametric sweep around $x^*_i$ quantifies how sensitive the dose rate is to manufacturing tolerances. This is reported as a **sensitivity table** in the HTML report:

| Parameter | Nominal | +10% | −10% | Δdose rate |
|---|---|---|---|---|
| Pb thickness | 50 mm | 55 mm | 45 mm | ±8% |
| Pb density | 11300 kg/m³ | 12430 | 10170 | ±1.5% |
| Activity | 1 GBq | 1.1 GBq | 0.9 GBq | ±10% |

This demonstrates that the design remains within zone constraints across the range of expected manufacturing variability — a key part of the ALARP justification.

## Code Module Map

| File | Key class / function |
|---|---|
| `alarp/optimiser.py` | `ALARPOptimiser`, `ALARPResult` |
| `alarp/zoning.py` | `assign_zone()`, `ZONE_THRESHOLDS` |
| `workflow/runner.py` | `Runner._run_alarp()` |
| `examples/04_alarp_optimization/config.yaml` | Worked example |

## Limits and Assumptions

- **Point-kernel transport**: ALARP uses the fast point-kernel solver in the inner optimisation loop. Monte Carlo is too slow for repeated evaluations (~10³ calls needed). This limits validity to μx < 10.
- **Single receptor**: The optimisation minimises dose at one representative receptor. A full ALARP would consider multiple receptors (workers at different distances, members of the public).
- **Cost proxy**: The framework uses shielding mass [kg] as a cost proxy. A real ALARP uses full lifecycle costs (material, installation, maintenance, ALARA programme costs).
- **Deterministic**: Optimisation uses nominal values; UQ is post-hoc. A full robust optimisation would treat uncertainty explicitly.

## References

- **IRR17**: UK Ionising Radiation Regulations 2017, HSE — statutory ALARP requirement.
- **ONR SAPs** (2014): "Safety Assessment Principles for Nuclear Facilities" — regulator guidance on ALARP demonstration.
- **ICRP-103** (2007): "The 2007 Recommendations of the International Commission on Radiological Protection" — dose limits and optimisation philosophy.
- **Hájek et al.** (2017): "Multi-objective optimisation in radiation shielding design" — academic treatment of Pareto-front shielding problems.

## TBD: Topics for Expansion

- Multi-receptor ALARP (optimise for collective dose across a zone map).
- Robust optimisation (optimise worst-case dose over the uncertainty distribution).
- Material choice as a combinatorial variable (lead vs. borated polyethylene vs. concrete).
- Full lifecycle cost model (replaces mass proxy with £ estimate).

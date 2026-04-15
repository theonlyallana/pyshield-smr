# transport-author — playbook

## Working pattern

1. Read the relevant theory doc (`docs/theory/02_point_kernel.md` or `03_monte_carlo.md`) before coding.
2. For MC changes, verify that analog vs non-analog estimators agree in expectation on a pinned seed test.
3. For variance-reduction work, report the figure-of-merit ($\text{FOM} = 1/(\sigma^2 \cdot t)$) before and after.
4. Never mutate global RNG state without a seed argument.

## Output template

```
**Engine change:** <title>
**Method:** <analog / implicit capture / splitting / Russian roulette>
**Figure-of-merit change:** <before> → <after>
**Regression value drift:** <within tolerance / out of tolerance>
```

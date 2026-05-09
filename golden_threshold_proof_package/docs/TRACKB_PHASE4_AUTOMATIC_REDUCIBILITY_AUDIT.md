# Track B Phase 4: automatic-reducibility and radii-proxy audit

This overlay audits the Phase 1 golden embedding seeds using a double-precision automatic-reducibility diagnostic.
It computes the standard-map derivative cocycle in the tangent/symplectic-normal frame and reports how close the reduced cocycle is to the upper-triangular form

```text
[[1, S(theta)], [0, 1]]
```

It also reports diagnostic weighted-norm quantities and a deliberately conservative radii-polynomial proxy. These outputs are **not theorem-facing** and must not be consumed by the final replay. The next theorem-grade phase must replace these estimates with outward-rounded interval Fourier arithmetic, exact/interval golden small-divisor bounds, and rigorous nonlinear/reducibility constants.

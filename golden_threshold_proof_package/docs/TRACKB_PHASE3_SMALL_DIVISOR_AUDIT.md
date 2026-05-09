# Track B Phase 3: Small-divisor and cohomology audit

This overlay adds a diagnostic small-divisor/cohomology audit for the Track B Theorem III lower-anchor route.

It reads the Phase 1 numerical seed embeddings selected/ranked by Phase 2 and computes:

- finite resolved small divisors for the golden rotation;
- worst modes and inverse multiplier sizes;
- zero-mode residual size;
- diagnostic cohomology corrections for residual coefficients;
- weighted \(\ell^1_\nu\) norms of the residual and cohomology correction;
- correction tail ratios.

All outputs are explicitly diagnostic:

```json
{
  "diagnostic_only": true,
  "theorem_facing": false,
  "promotion_allowed": false
}
```

This phase does **not** prove the lower-anchor theorem. It is meant to choose the seed and analytic weight for the next phase: automatic reducibility plus radii-polynomial constants. The theorem-facing version must replace the double-precision small-divisor calculations with exact/interval continued-fraction bounds and outward-rounded arithmetic.

Suggested working weights after Phase 2 are conservative values such as \(\nu=1.003\), with \(\nu=1.005\) used as a stress-test value near the final anchor.

# Track B Phase 2: Fourier-tail audit

This overlay adds a diagnostic Fourier-tail audit for the Phase 1 Track B numerical seed embeddings.
It is intentionally **not theorem-facing**. Its job is to decide which saved embedding is the best seed
for the later interval/radii-polynomial lower-anchor validator.

The audit reads Phase 1 `.npz` files and computes:

- normalized Fourier coefficients for `u` and the residual;
- weighted `l1_nu` norms on a configurable `nu` grid;
- plain and weighted tail fractions after selected mode fractions;
- exponential decay fits for coefficient envelopes;
- diagnostic geometric tail envelopes;
- shell-by-shell coefficient summaries;
- candidate rankings for Phase 3/4.

The best proof seed should usually be a high-resolution final-anchor embedding, not necessarily the
row with the smallest low-resolution floating residual.

All outputs include:

```json
{
  "diagnostic_only": true,
  "theorem_facing": false,
  "promotion_allowed": false
}
```

These diagnostics must be replaced by outward-rounded interval bounds before Theorem III can be closed.

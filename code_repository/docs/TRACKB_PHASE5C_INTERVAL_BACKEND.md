# Track B Phase 5C — Outward-Rounded Interval Backend Scaffold

Phase 5C is the first proof-backend-shaped stage after the Phase 5B component audit.
It reads the selected H1 seed and produces outward-rounded, interval-shaped bounds for
residual, small divisors, cohomology correction, reducibility defect, nonlinear proxy,
and a candidate radii inequality.

## Status

This stage is still **not theorem-facing**. It uses IEEE-754 `nextafter` outward rounding
and conservative component inflations. It is intended to catch scale/radius problems before
we implement the final formal interval arithmetic backend.

## Recommended starting configuration

- `K = 0.971635`
- selected seed: `phase4i_selected_seed/K0p9716350000_M8192_H1_SELECTED.npz`
- `nu = 1.001`
- `cutoff = frac:0.95`
- `tail-start = 0.90`
- `grid-factor = 4`
- `radius = 3e-5`

## Output

Primary summary:

```text
phase5c_interval_backend_summary.json
phase5c_interval_backend_results.csv
phase5c_ranked_candidates.json
records/*.phase5c_interval_backend.json
```

Key fields:

- `Y_interval_upper`
- `Z_interval_upper`
- `Q_interval_upper`
- `radii_lhs_interval_upper`
- `radii_margin_interval_lower`
- `radii_relative_margin_interval_lower`
- `small_divisor_min_denominator_lower`
- `cohomology_inverse_linf_resolved_upper`
- `recommendation_label`

## Next step

If Phase 5C remains positive under conservative inflation, proceed to Phase 5D: certificate
assembly scaffold, with explicit assumptions/open hypotheses and a path toward replacing
this backend by a formal interval implementation.

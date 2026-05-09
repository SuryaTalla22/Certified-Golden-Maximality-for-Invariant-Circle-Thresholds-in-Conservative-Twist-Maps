# Track B Phase 4g: Tangent Consistency Audit

Diagnostic only. This audit compares the scalar graph residual, the derivative of that residual, and the full 2D tangent/cocycle residual for the saved Track-B embeddings. It is intended to decide whether the current Phase 4 bottleneck is a true high-frequency aliasing problem or a formula/frame/sign mismatch.

Key outputs:

- `best_sign`: selected standard-map sine sign convention by smallest scalar residual.
- `max_derivative_vs_tangent_x_linf_best_sign`: should be near roundoff; if not, the tangent formula is inconsistent.
- `max_scalar_residual_linf_over_grids_best_sign`: scalar residual across native and oversampled grids.
- `max_tangent_residual_linf_over_grids_best_sign`: tangent/cocycle residual across grids.
- `recommendation_label`: diagnostic interpretation.

No output from this phase is theorem-facing.

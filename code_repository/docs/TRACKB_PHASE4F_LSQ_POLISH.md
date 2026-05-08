# Track B Phase 4f: Oversampled least-squares polish

This diagnostic overlay is a corrective follow-up to Phase 4e. Phase 4e drove the *projected* residual down but left the oversampled/core residual and Phase 4d automatic-reducibility diagnostics worse. Phase 4f instead solves an overdetermined oversampled residual by LSMR/Gauss--Newton.

It is not theorem-facing. It is intended only to decide whether the current final-anchor seed can be dealiased/polished enough before intervalization.

Key outputs:

- `oversampled_residual_linf`
- `projected_residual_linf`
- `core_residual_linf`
- `output_npz`

The resulting `output_npz` files should be audited with the Phase 4d target-frame audit before any further decision.

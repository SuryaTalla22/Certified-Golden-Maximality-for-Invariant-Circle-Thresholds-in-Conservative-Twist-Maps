# Track B Phase 5B: Interval-Component Audit Scaffold

Phase 5B is a diagnostic-but-proof-shaped audit around the selected H1 seed for
Theorem III.  It computes conservative component-inflated bounds for residual,
small divisors, cohomology correction, frame geometry, reducibility defect, and a
radii-polynomial proxy.

This phase is **not theorem-facing**.  It does not yet use a formal interval
arithmetic backend.  Its purpose is to choose the exact numerical configuration
for the first real outward-rounded validator.

Recommended first theorem-prep configuration:

- selected seed: `phase4i_selected_seed/K0p9716350000_M8192_H1_SELECTED.npz`
- `nu = 1.001`
- cutoff: `frac:0.95` and `full` comparator
- grid factor: `4`
- radius: `1e-5`

The main fields to inspect are:

- `Y_component_bound`
- `Z_component_bound`
- `Q_component_bound`
- `tail_residual_component_bound`
- `radii_margin_component`
- `dominant_component_term`
- `recommendation_label`

A positive component margin is only a signal to proceed to a formal interval
backend; it is not itself a proof.

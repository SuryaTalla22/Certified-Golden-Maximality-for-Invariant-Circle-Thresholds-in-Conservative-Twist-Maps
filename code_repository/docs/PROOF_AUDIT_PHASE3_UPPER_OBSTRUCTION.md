# Phase 3 Proof-Audit Layer: Upper Obstruction and Analytic-Incompatibility Margin

Phase 3 adds a proof-carrying audit for the Theorem-IV upper obstruction layer.  The goal is to stop treating the upper theorem as a compact status field and instead expose the raw interval/symbolic payload and the recomputed inequalities that make the analytic-incompatibility claim checkable.

## New files

- `kam_theorem_suite/audit/upper_obstruction_margin.py`
- `scripts/audit/audit_upper_obstruction.py`
- `tests/test_upper_obstruction_audit.py`
- `artifacts/proof_audit/upper_obstruction/upper_obstruction_audit.json`
- `artifacts/proof_audit/upper_obstruction/upper_obstruction_audit.bundle.json`
- `tables/proof_audit/upper_obstruction/upper_obstruction_margin_ledger.csv`
- `tables/proof_audit/upper_obstruction/upper_obstruction_margin_ledger.tex`
- `figures/proof_audit/upper_obstruction/upper_obstruction_intervals.pdf`
- `figures/proof_audit/upper_obstruction/upper_obstruction_margin_ledger.pdf`
- `figures/proof_audit/upper_obstruction/upper_tail_support.pdf`

## Source artifact

The Phase-3 audit reads:

```text
artifacts/final_discharge/stage_cache/theorem_iv_upper_bridge_promotion.json
```

This source is a cached Theorem-IV bridge-promotion artifact.  Phase 3 is not a heavy re-run of the Theorem-IV solver.  It is a Level-A artifact-derived audit: it recomputes the theorem-facing inequalities from the cached promotion fields and fails closed if those fields do not support the upper obstruction.

## Recomputed inequalities

The audit recomputes the following key margins:

- the certified upper window is ordered;
- the analytic obstruction barrier window is ordered;
- the upper window is strictly below the barrier;
- the exported incompatibility gap matches `barrier_lo - upper_hi`;
- the exported window widths match the interval endpoints;
- the incompatibility gap dominates the upper localization width;
- the exported gap/localization ratio matches the recomputed ratio;
- support fraction, entry coverage, supporting entry count, candidate count, promoted-entry count, and strongest-candidate support count are positive;
- the denominator tail is nonempty and strictly ordered;
- the bridge status and tail-coherence status are strong;
- the family label is `standard-sine` and the stored rotation is the golden representative;
- the missing-hypothesis list is empty.

For the current snapshot the central interval inequality is:

```text
upper_hi = 0.9717820875185549
barrier_lo = 1.0366258097576748
barrier_lo - upper_hi = 0.06484372223911994 > 0
```

The gap also dominates the upper localization width:

```text
upper_width = 0.0015091815185549473
gap - upper_width = 0.06333454072056499 > 0
```

The recomputed ratio is:

```text
gap / upper_width = 42.9661518126781
```

## Derived Booleans

The following theorem-facing Booleans are derived from the margin ledger rather than trusted as inputs:

- `upper_obstruction_margin_ledger_complete`
- `supercritical_obstruction_locked`
- `support_geometry_certified`
- `tail_coherence_certified`
- `tail_stability_certified`
- `analytic_incompatibility_certified`

Each of these Booleans has a dependency list and a positive margin.  The fail-closed validator rejects the bundle if any theorem-facing Boolean is marked `trusted_as_input`, if any required margin is nonpositive, if raw/source dependencies are missing, or if any active assumptions, open hypotheses, or failure fields remain.

## Artifact-derived Theorem-IV shell

`build_theorem_iv_shell_from_audit(...)` now records:

- `upper_obstruction_interval`
- `analytic_barrier_interval`
- `analytic_incompatibility_margin`
- `upper_obstruction_gap_minus_width`
- `upper_obstruction_tail_qs`
- `proof_audit_derived_booleans`
- `proof_audit_margin_ledger`

This makes the replay shell visibly derived from the Phase-3 audit bundle.

## Negative controls

`tests/test_upper_obstruction_audit.py` checks that the validator rejects:

- an upper endpoint moved above the barrier;
- a false tail-suffix field;
- an exported gap that no longer matches the recomputed interval gap;
- a theorem-facing Boolean switched to `trusted_as_input`.

The positive test also verifies that the current promotion artifact passes the proof-audit validator and can build a Theorem-IV shell from the audit bundle.

## Current Phase-3 result

The current audit passes:

```text
status: passed
analytic_incompatibility_margin: 0.06484372223911994
gap_minus_upper_width: 0.06333454072056499
gap_to_localization_ratio: 42.9661518126781
failure_fields: []
```

This closes the Phase-3 artifact-derived upper-obstruction audit.  It does not replace a future heavy Theorem-IV regeneration protocol; it gives the final theorem path a fail-closed, proof-carrying margin ledger for the current cached upper bridge.

# Phase 4 proof audit: decomposed transport budget

Phase 4 adds a proof-carrying audit for the compressed Theorem-V transport contract.  It does **not** store a cached Theorem-V theorem artifact.  Instead, it exposes the small downstream budget ledger that the compressed contract must provide before later theorem consumers are allowed to treat `preserves_golden_gap=True` as mathematical input.

## Files added

- `kam_theorem_suite/audit/transport_budget.py`
- `scripts/audit/audit_transport_budget.py`
- `scripts/study_transport_margin_amplification.py`
- `tests/test_transport_budget_audit.py`

Generated outputs are written under:

- `artifacts/proof_audit/transport_budget/`
- `tables/proof_audit/transport_budget/`
- `figures/proof_audit/transport_budget/`

These are lightweight audit outputs, not stored Theorem-V-or-above stage-cache artifacts.

## Checked inequality

The budget ledger verifies

```text
total_charged = delta_rat + delta_branch + delta_tail + delta_round
remaining_margin = available_gap - total_charged > 0
margin_ratio = available_gap / total_charged > 1.
```

The default component formulas are deliberately transparent:

```text
delta_rat    = 0.35 * target_width
delta_branch = 0.25 * target_width
delta_tail   = 0.30 * target_width
delta_round  = max(1e-12, 8 * ulp(target_hi))
```

For the compact replay target interval `[0.9716350, 0.9716370]`, the target width is `2e-6`, while the replay top-gap scale is `1e-5`.  The baseline charged budget is therefore roughly `1.800001e-6`, leaving a positive margin of roughly `8.199999e-6`.

## Fail-closed behavior

The validator rejects the audit if:

- the target interval is unordered;
- the exported target width does not match the endpoints;
- any budget component is nonpositive or nonfinite;
- the stored total does not equal the component sum;
- the stored remaining margin does not equal `available_gap - total_charged`;
- the margin ratio is not recomputed correctly;
- the total charged budget exceeds the available gap;
- branch/chart labels are missing;
- the shell reports raw-shell consumption;
- the theorem-facing Boolean is marked as trusted input.

## Margin-amplification study

`scripts/study_transport_margin_amplification.py` runs a diagnostic, non-theorem-facing scenario study.  It asks which future refinements would improve the margin most: deeper denominator rows, increased precision, sharper tail modulus, refined recurrence-rate control, narrowed target interval, and alternate branch-window choices.

The study is intentionally marked diagnostic.  It guides Phase-4 follow-up work without pretending to be a regenerated transport theorem.

# Phase 2O: Tail/Radius Closure for Theorem III

Phase 2N showed that the collar-000 residual is no longer the active obstruction.  The best Phase-2N rows have residuals near `1e-9`, but the strict Phase-2E inequality

```text
Y + Z r + T < r
```

still fails because the tail term `T` is about three times larger than the allowable tail budget.  Phase 2O therefore stops running larger Newton solves and instead audits the tail/radius proof budget directly.

## What Phase 2O does

The main script is:

```text
scripts/audit/run_lower_anchor_phase2o_radius_tail_scan.py
```

It consumes one of the following:

1. a Phase-2N batch summary JSON with a `best.path` field;
2. a Phase-2N single-N attempt JSON; or
3. a Phase-2N best single-segment candidate JSON.

It writes:

```text
artifacts/proof_audit/lower_corridor/phase2o_tail_radius/*.json
tables/proof_audit/lower_corridor/phase2o_tail_radius/*.csv
```

## Rows produced

Phase 2O produces three families of rows.

### 1. Strict source-tail radius scans

These rows keep the source Phase-2E tail bound fixed and scan proof-radius multipliers.  They are theorem-eligible, but they also check the finite-dimensional contraction condition.  If the radius needed to beat the tail violates `q < 1`, this conclusively shows that radius inflation cannot close the current tail model.

### 2. True working-sigma override rows

These rows recompute the modewise inverse-applied residual and Cauchy tail bound at explicit working-strip widths.  They are theorem-eligible when the sigma is positive, the Cauchy tail is usable, the finite radius polynomial remains valid, and the outward-rounded margin is positive.

This is the most important Phase-2O theorem-facing rescue mechanism because the older lower-anchor path had a hard `1e-4` sigma floor.  Phase 2O tests whether a smaller but still positive working sigma reduces the tail enough to close the proof.

### 3. Diagnostic high-mode envelope rows

These rows estimate what would happen if the tail envelope were fitted only from high resolved modes.  They are **not theorem-eligible**.  They are included only to diagnose whether a sharper tail lemma is worth implementing.

## Promotion policy

A Phase-2O candidate is theorem-facing only if a row has:

```text
theorem_eligible = true
theorem_ready = true
radii_margin > 0
failure_reasons = []
```

Diagnostic rows are never promoted automatically.  If a diagnostic row closes while all theorem-eligible rows fail, the next mathematical task is to write and validate the corresponding sharper tail lemma.

## Interpretation

If the report says `radius_inflation_blocked_by_finite_contraction=true`, then increasing `r` is not a viable closure mechanism under the current finite-dimensional Krawczyk ball.

If the best theorem-eligible sigma override still fails with a large tail, then the only credible next move is to replace the global Cauchy tail envelope with a sharper theorem-facing tail estimate.

If a theorem-eligible row closes, merge the emitted Phase-2O candidate into the collar chain and run the existing two-regime verifier.

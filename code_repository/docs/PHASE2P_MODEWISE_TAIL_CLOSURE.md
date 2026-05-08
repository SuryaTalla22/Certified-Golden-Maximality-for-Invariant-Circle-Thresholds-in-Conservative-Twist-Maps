# Phase 2P: Modewise Tail-Response Closure for Theorem III

Phase 2O showed that the lower-anchor obstruction is no longer the residual,
K-width, or radius inflation.  The remaining blocker is the scalar worst-case
strict tail response.  Phase 2P is a proof-audit patch that replaces the scalar
bound

```text
max_k inverse_multiplier(k) * tail_l1
```

with a modewise geometric tail response

```text
sum_{m >= tail_start} inverse_multiplier(m) * tail_envelope(m)
```

plus an infinite-remainder bound using the golden small-divisor inequality

```text
|exp(2*pi*i*m*rho_G) - 1| >= (4/sqrt(5)) / m.
```

A Phase 2P row is theorem-facing only if all of the following hold:

1. the input row is the golden lower-anchor row within tolerance;
2. the analytic tail envelope is theorem-usable;
3. the finite contraction bound remains below one;
4. the finite radius-polynomial margin is positive;
5. the modewise tail ledger includes the finite exact sum and the infinite
   golden Diophantine remainder;
6. the recomputed inequality `Y + Z*r + T < r` has a positive outward-rounded
   margin.

The script does **not** rerun the heavy Newton solve.  It consumes the best
Phase 2O candidate/report or the underlying Phase 2N attempt, recomputes the
tail response, writes a JSON report, writes a CSV table, and exports a
single-segment candidate compatible with the existing `anchor_segments` schema.

## Main entry point

```bash
python scripts/audit/run_lower_anchor_phase2p_modewise_tail_scan.py \
  --input artifacts/proof_audit/lower_corridor/phase2o_tail_radius/phase2o_collar_000_tail_radius_candidate.json \
  --out artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_collar_000_modewise_tail_scan.json \
  --csv tables/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_collar_000_modewise_tail_scan.csv \
  --candidate-out artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_collar_000_modewise_tail_candidate.json \
  --sigma-values 0.0001,0.000075,0.00005,0.000025,0.00001,0.000005,0.0000025,0.000001 \
  --tail-cutoffs 1024,2048,4096,8192,16384 \
  --oversample-factors 16
```

## Output paths

The default outputs are:

```text
artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_modewise_tail_scan.json
tables/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_modewise_tail_scan.csv
artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_modewise_tail_candidate.json
```

When `theorem_ready_count > 0`, the candidate JSON has:

```text
theorem_facing = true
promotion_allowed = true
failure_fields = []
closure_level = phase2p_modewise_tail_closure
```

This closes the single collar-000 segment only.  It still must be merged into a
contiguous collar chain with overlap checks before the full Theorem III lower
anchor is discharged.

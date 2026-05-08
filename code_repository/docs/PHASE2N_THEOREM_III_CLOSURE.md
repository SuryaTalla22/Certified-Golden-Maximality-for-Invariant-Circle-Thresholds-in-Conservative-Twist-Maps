# Phase 2N Theorem III Closure Rescue

Phase 2N replaces the Phase-2M brute-force near-critical collar sweep with a
memory-safe and margin-aware workflow.  The previous collar command died because
large dense spectral solves were attempted inside one process.  Phase 2N runs
one numerical resolution at a time and scores attempts by the actual theorem
ledger

```text
Y + Z r + T < r
```

instead of by the older compact `analytic_theorem_margin` proxy.

## Files added

- `kam_theorem_suite/audit/lower_anchor_phase2n.py`
  - single-N attempt runner
  - Fourier seed resampling
  - strict Phase-2E ledger scoring
  - diagnostic tail variants
  - best-attempt summary and one-segment candidate generation
- `scripts/audit/run_lower_anchor_phase2n_single_N_probe.py`
  - one K/N/oversample/sigma subprocess-safe attempt
- `scripts/audit/run_lower_anchor_phase2n_batch.py`
  - memory-safe grid runner; one subprocess per attempt
- `scripts/audit/run_lower_anchor_phase2n_seeded_continuation.py`
  - short seeded continuation ladder in K
- `scripts/audit/run_lower_anchor_phase2n_endpoint_probe.py`
  - final-anchor endpoint probe wrapper
- `scripts/audit/summarize_lower_anchor_phase2n_probes.py`
  - rebuilds summary/csv/candidate from existing Phase-2N attempts

## File edited

- `kam_theorem_suite/audit/lower_anchor_heavy_certificate.py`
  - candidate rows now export the ledger sigma instead of hard-coding
    `sigma: 0.0`.

## The intended workflow

1. Probe collar-000 with small, safe grids only.
2. Read the Phase-2E margin table.
3. If one attempt closes, generate a one-segment candidate.
4. If no attempt closes, inspect which term dominates: `residual_Y`, `Z*r`, or
   `tail_T`.
5. Run seeded continuation only after a positive or near-positive row is found.
6. Try the endpoint theorem route after the collar-000 numerics are understood.

## Theorem-facing caution

The `strict_phase2e_source_tail` variant is the only theorem-eligible tail
variant by default.  The high-mode envelope tail is intentionally diagnostic; it
is meant to tell whether a sharper tail lemma would close the margin, not to
replace the current theorem gate.

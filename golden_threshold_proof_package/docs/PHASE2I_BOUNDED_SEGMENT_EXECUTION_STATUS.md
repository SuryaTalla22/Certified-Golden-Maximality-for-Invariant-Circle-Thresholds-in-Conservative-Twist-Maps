# Phase 2I bounded segment execution status

Phase 2I adds a subprocess-level executor for the remaining lower-anchor
segments.  The previous Phase 2H shell script is correct for a long-running HPC
session, but in bounded environments a single near-critical segment can consume
the entire wall-time budget before producing a candidate file.  Phase 2I turns
that situation into an auditable per-segment execution report.

The new entry point is:

```bash
python -S scripts/audit/run_lower_anchor_phase2i_segment_executor.py \
  --segment-timeout-seconds 900 \
  --n-values 64,96,128,192,256,384,512 \
  --oversample-factor 16
```

The executor:

1. preflights the numerical lower stack;
2. inventories the current Phase 2H status;
3. runs missing/failing segment commands one subprocess at a time;
4. kills any segment that exceeds its per-segment wall-clock budget;
5. writes stdout/stderr logs for every attempted segment;
6. refreshes the Phase 2H inventory after execution; and
7. refuses promotion unless the refreshed strict pathway succeeds.

In minimal environments without `mpmath`, the repository now has a small
float-based fallback so non-interval lower-collocation diagnostics can import.
This fallback is explicitly non-theorem-grade for interval arithmetic.  Final
promotion should be run in an environment with the real `mpmath` dependency or
with an independent interval backend accepted by the validator.

The expected final HPC command is still to execute all missing segments with a
large enough timeout, merge them, and run strict Phase 2B ingestion.  Phase 2I
only makes that execution robust and diagnosable.

## Sandbox Phase 2I execution result

In the bounded sandbox run, the executor succeeded in converting the remaining
missing work into explicit segment artifacts and a merged strict-ingestion
attempt.  The important outcome is not promotion; it is diagnosis.

Current results:

- all 10 full-grid segment artifacts are now present;
- segments 000--001 remain theorem-ready;
- segments 002--009 are present but fail the Phase-2E analytic radii ledger;
- the merged candidate covers the final anchor interval `[0.971635, 0.971636]`;
- the merged candidate is not promotable because eight segment margins are
  negative;
- strict Phase-2B ingestion correctly fails.

The summary artifact is:

```text
artifacts/proof_audit/lower_corridor/lower_anchor_phase2i_execution_merge_summary.json
```

The merged candidate and strict-ingestion report are:

```text
artifacts/proof_audit/lower_corridor/lower_anchor_phase2i_merged_candidate.json
artifacts/proof_audit/lower_corridor/lower_anchor_phase2i_strict_ingestion_check.json
```

This is a useful Phase 2I endpoint because the lower-chain problem is no longer
"missing segment execution."  It is now a sharper analytic-bound problem:
segments 002--009 have finite-dimensional candidates, but their recomputed
Phase-2E radii margins are negative.  The next stage should therefore be a
Phase 2J targeted analytic rescue, not another inventory/controller pass.

Phase 2J should work segment-by-segment, beginning with segment 002, and try:

1. real `mpmath` rather than the local float fallback;
2. larger `N` and oversampling;
3. smaller K-subsegments;
4. adaptive validation radius selection rather than the current small fixed
   radius inherited from the source finite validator;
5. sharper tail and nonlinear majorants; and
6. modewise inverse-applied residual and small-divisor diagnostics for each
   failed candidate.

The strict rule remains unchanged: no promotion unless every segment has
positive recomputed `r - (Y + Zr + T)` margin and strict Phase-2B ingestion
passes.

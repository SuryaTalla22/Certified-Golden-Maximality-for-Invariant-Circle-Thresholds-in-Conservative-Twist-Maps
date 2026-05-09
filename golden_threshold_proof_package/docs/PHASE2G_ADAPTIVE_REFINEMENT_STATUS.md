# Phase 2G adaptive lower-anchor refinement status

Phase 2G adds the targeted repair layer after a Phase 2E/2F lower-anchor run fails strict promotion.  It is intentionally not a promotion mechanism.  Its purpose is to make the next expensive run local and interpretable: identify the first blocker, classify whether it is a finite solve failure, analytic-margin failure, overlap failure, or incomplete final-anchor coverage, and emit a concrete rerun plan.

## Added code

- `kam_theorem_suite/audit/lower_anchor_phase2g_refinement.py`
  - recomputes Phase-2B radii margins from raw fields;
  - classifies failing rows;
  - detects nonpositive overlap links;
  - proposes bisection / near-critical subdivision / overlap-bridge / final-anchor continuation segments;
  - emits JSON, CSV, and shell rerun commands.
- `scripts/audit/run_lower_anchor_phase2g_refinement.py`
  - CLI for diagnosing a chunk or merged candidate.
- `scripts/audit/run_lower_anchor_phase2g_segment.py`
  - CLI for running one explicit refined segment.
- `kam_theorem_suite/audit/lower_anchor_heavy_certificate.py`
  - now exposes `run_heavy_lower_anchor_certificate_on_segments(...)` for arbitrary Phase-2G local intervals;
  - lazily imports the Phase-2E analytic Krawczyk module so refinement planning and dry-run tests do not import the numerical stack unnecessarily.
- `tests/test_lower_anchor_phase2g_refinement.py`
  - pure unit tests for margin recomputation, failure classification, near-critical subdivision, overlap repair, final-anchor continuation, and shell-output generation.

## Generated artifacts

- `artifacts/proof_audit/lower_corridor/lower_anchor_phase2g_refinement_plan.json`
- `tables/proof_audit/lower_corridor/lower_anchor_phase2g_refinement_segments.csv`
- `scripts/audit/run_phase2g_refinement_segments.sh`
- `artifacts/proof_audit/lower_corridor/phase2g_refinements/phase2g_smoke_candidate.json`

The generated plan diagnoses the current bounded Phase-2F chunk as incomplete rather than mathematically failed: it covers roughly `[0.265, 0.7000001]` and therefore does not reach the final anchor `[0.971635, 0.971636]`.  The actionable refinement plan emits all eight remaining full-grid segments, each with higher-resolution Phase-2G settings (`N=64,96,128,192,256,384,512`, oversampling at least 16).

## How to use next

Run the generated command file on a machine with enough runtime:

```bash
bash scripts/audit/run_phase2g_refinement_segments.sh
```

Then merge the new Phase-2G candidate chunks with the earlier theorem-ready chunks:

```bash
python scripts/audit/run_lower_anchor_phase2e_full_grid.py \
  --merge-candidates \
  artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_000_candidate.json \
  artifacts/proof_audit/lower_corridor/phase2g_refinements/*.json \
  --merged-candidate-name lower_anchor_phase2g_merged_candidate.json \
  --check-strict-ingestion
```

If strict ingestion still fails, rerun the Phase-2G planner on the merged candidate.  The correct loop is:

1. diagnose the first blocker;
2. run only the proposed refined segment(s);
3. merge;
4. run strict Phase-2B ingestion;
5. repeat until either promotion succeeds or a genuine irreducible analytic obstruction is isolated.

Do not weaken Phase-2B.  Nonpositive analytic margins, finite-dimensional-only rows, missing raw terms, and overlap failures must remain hard failures.

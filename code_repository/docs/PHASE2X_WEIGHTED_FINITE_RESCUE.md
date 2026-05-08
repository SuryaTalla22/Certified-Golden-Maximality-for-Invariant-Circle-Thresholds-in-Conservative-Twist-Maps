# Phase 2X — Weighted finite rescue and anchor-openness fallback

Phase 2X replaces broad subdivision as the default response to the stubborn
Theorem-III lower-collar gap.  The previous phases showed that the hard pieces
miss by tiny margins, typically `1e-8` to `3e-8`, even after 64- and 256-piece
subdivision.  This indicates that the limiting artifact is the finite/norm
ledger, not the existence of the invariant object.

Phase 2X is conservative: it does **not** promote a candidate from heuristic
post-processing.  The new scripts rank failed pieces and rerun the existing
fail-closed `2N -> 2O -> 2P` validators on only the most promising pieces using
narrow, evidence-driven profiles.

## Files

- `kam_theorem_suite/audit/lower_anchor_phase2x_weighted_finite.py`
- `scripts/audit/run_lower_anchor_phase2x_failure_autopsy.py`
- `scripts/audit/run_lower_anchor_phase2x_weighted_rescue.py`
- `scripts/audit/run_lower_anchor_phase2x_anchor_openness.py`
- `tests/test_lower_anchor_phase2x_weighted_finite.py`

## Workflow

1. Run failure autopsy on the latest Phase 2V/2U run summary.
2. Run weighted rescue on the top failed pieces.
3. If the weighted run does not close enough pieces, run the N-lift profile on
the same top pieces.
4. If fixed interval validation remains brittle, run anchor-openness fallback.

The scripts are resumable and write all artifacts under:

- `artifacts/proof_audit/lower_corridor/phase2x_weighted/`
- `tables/proof_audit/lower_corridor/phase2x_weighted/`
- `artifacts/proof_audit/lower_corridor/phase2x_anchor/`
- `tables/proof_audit/lower_corridor/phase2x_anchor/`

## CPU-node safety

Always set BLAS/OpenMP limits before parallel runs:

```bash
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export BLIS_NUM_THREADS=1
```

## Autopsy command

```bash
python scripts/audit/run_lower_anchor_phase2x_failure_autopsy.py \
  --summary artifacts/proof_audit/lower_corridor/phase2v_micro/collar_012b1_v256/phase2v_collar_012b1_v256_run_summary.json \
  --out artifacts/proof_audit/lower_corridor/phase2x_weighted/phase2x_collar_012b1_autopsy.json \
  --csv tables/proof_audit/lower_corridor/phase2x_weighted/phase2x_collar_012b1_autopsy.csv
```

## Weighted rescue command

```bash
python scripts/audit/run_lower_anchor_phase2x_weighted_rescue.py \
  --summary artifacts/proof_audit/lower_corridor/phase2v_micro/collar_012b1_v256/phase2v_collar_012b1_v256_run_summary.json \
  --label collar_012b1_phase2x_weighted \
  --seed-json artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_collar_012a_N1024_os16_sg0p0001.json \
  --top-k 20 \
  --workers 12 \
  --profile weighted
```

## Targeted N-lift command

```bash
python scripts/audit/run_lower_anchor_phase2x_weighted_rescue.py \
  --summary artifacts/proof_audit/lower_corridor/phase2v_micro/collar_012b1_v256/phase2v_collar_012b1_v256_run_summary.json \
  --label collar_012b1_phase2x_nlift1536 \
  --seed-json artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_collar_012a_N1024_os16_sg0p0001.json \
  --top-k 12 \
  --workers 6 \
  --profile nlift1536
```

## Anchor-openness fallback

```bash
python scripts/audit/run_lower_anchor_phase2x_anchor_openness.py \
  --label collar_012b1_anchor \
  --K-lo 0.9662501 \
  --K-hi 0.9663752 \
  --seed-json artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_collar_012a_N1024_os16_sg0p0001.json \
  --anchor-count 128 \
  --half-width 0.00000055 \
  --workers 24 \
  --profile anchor1536
```


# Phase 2U: Fast fixed-depth microsegment closer

Phase 2U is a replacement for the recursive Phase 2T gap closer.  It is intended for CPU-node use when a collar/sub-collar is very close to theorem closure but the full segment sits on the finite-contraction boundary.

## Purpose

Phase 2U closes a hard interval by fixed micro-subdivision:

1. Split `[K_lo,K_hi]` into many small overlapping microsegments.
2. Run the existing `Phase 2N -> Phase 2O -> Phase 2P` pipeline on each microsegment.
3. Promote only theorem-ready Phase 2P candidates.
4. Checkpoint after every completed piece.
5. Optionally assemble all closed pieces using Phase 2Q.

Unlike Phase 2T, Phase 2U does not recursively explode.  This makes it safer for 2--6 hour CPU allocations.

## Thread safety on NERSC CPU nodes

Always set thread limits before running many Python subprocesses:

```bash
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export BLIS_NUM_THREADS=1
```

## Recommended first run for collar_012b1

```bash
python scripts/audit/run_lower_anchor_phase2u_fast_micro_closer.py \
  --label collar_012b1 \
  --K-lo 0.9662501 \
  --K-hi 0.9663752 \
  --seed-json artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_collar_012a_N1024_os16_sg0p0001.json \
  --pieces 64 \
  --workers 32 \
  --profile fast \
  2>&1 | tee artifacts/proof_audit/replay/phase2u_collar_012b1_fast.log
```

If all pieces do not close, inspect the summary:

```bash
python - <<'PY'
import json
p='artifacts/proof_audit/lower_corridor/phase2u_micro/collar_012b1/phase2u_collar_012b1_run_summary.json'
d=json.load(open(p))
print(json.dumps({
  'status': d.get('status'),
  'closed_count': d.get('closed_count'),
  'pending_count': d.get('pending_count'),
  'best_failed_rows': d.get('best_failed_rows', [])[:10],
  'assemble_report': d.get('assemble_report'),
}, indent=2))
PY
```

Then rerun only missing pieces with a stronger profile if needed.  The script is resumable and skips theorem-ready pieces unless `--force` is used.

## Profiles

`fast` is designed for many microsegments:

- radius multipliers: `1.0,1.08,1.12,1.16,1.2,1.25,1.3`
- sigma values: `1e-6, 5e-7, 1e-7`
- tail cutoffs: `1536,2048`

`standard` and `aggressive` broaden the search but cost much more.

## Chunked runs

For short allocations, split the 64 pieces into ranges:

```bash
python scripts/audit/run_lower_anchor_phase2u_fast_micro_closer.py \
  --label collar_012b1 \
  --K-lo 0.9662501 \
  --K-hi 0.9663752 \
  --seed-json artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_collar_012a_N1024_os16_sg0p0001.json \
  --pieces 64 \
  --piece-start 0 \
  --piece-stop 32 \
  --workers 32 \
  --profile fast
```

Then run `--piece-start 32 --piece-stop 64`.  After all pieces are closed:

```bash
python scripts/audit/run_lower_anchor_phase2u_fast_micro_closer.py \
  --label collar_012b1 \
  --K-lo 0.9662501 \
  --K-hi 0.9663752 \
  --pieces 64 \
  --assemble-only
```

## Output locations

- Run summary: `artifacts/proof_audit/lower_corridor/phase2u_micro/<label>/phase2u_<label>_run_summary.json`
- Piece CSV: `tables/proof_audit/lower_corridor/phase2u_micro/<label>/phase2u_<label>_pieces.csv`
- Per-piece logs: `artifacts/proof_audit/replay/phase2u_<label>/<segment_id>.log`
- Ready candidates: `artifacts/proof_audit/lower_corridor/phase2u_micro/<label>/ready/*THEOREM_READY_candidate.json`
- Split-chain candidate: `artifacts/proof_audit/lower_corridor/phase2u_micro/<label>/phase2u_<label>_split_chain_candidate.json`

## Exit codes

- `0`: selected pieces closed, and full-run assembly succeeded if requested.
- `2`: one or more pieces remain unclosed.
- `3`: all pieces closed but Phase 2Q split-chain assembly failed.

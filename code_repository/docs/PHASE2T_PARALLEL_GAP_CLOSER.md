# Phase 2T Parallel Adaptive Gap Closer

Phase 2T automates the proof closure strategy for narrow near-critical gaps that fail by a small analytic margin. It is designed for a multi-core CPU node and runs many independent sub-collar certificates in parallel.

The script orchestrates the existing theorem-facing pipeline:

1. Phase 2N: solve/export a single lower-anchor certificate for a subsegment.
2. Phase 2O: scan the radius/tail ledger.
3. Phase 2P: apply the strict modewise inverse tail lemma.
4. Phase 2Q: assemble all theorem-ready split pieces into a chain.

It does not relax proof criteria. A subpiece is promoted only if Phase 2P writes a candidate with:

```text
theorem_facing = true
promotion_allowed = true
failure_fields = []
selected_phase2p_row.theorem_ready = true
selected_phase2p_row.failure_reasons = []
```

## Recommended use on a CPU node

Before running many workers, prevent BLAS/OpenMP oversubscription:

```bash
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
```

Start with 32 or 64 workers even if the node has 256 CPUs, because the pipeline writes many JSON/CSV/log artifacts. Increase only if the filesystem remains responsive.

## Current target example

For the difficult interval `012b1 = [0.9662501, 0.9663752]`:

```bash
python scripts/audit/run_lower_anchor_phase2t_parallel_gap_closer.py \
  --label collar_012b1 \
  --K-lo 0.9662501 \
  --K-hi 0.9663752 \
  --seed-json artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_collar_012a_N1024_os16_sg0p0001.json \
  --initial-pieces 16 \
  --split-factor 2 \
  --max-depth 3 \
  --workers 64
```

The script is resumable. If it stops midway, rerun the same command; theorem-ready piece candidates are reused by default.

## Outputs

Main summary:

```text
artifacts/proof_audit/lower_corridor/phase2t_parallel/phase2t_<label>_run_summary.json
```

Piece CSV:

```text
tables/proof_audit/lower_corridor/phase2t_parallel/phase2t_<label>_pieces.csv
```

Theorem-ready piece candidates:

```text
artifacts/proof_audit/lower_corridor/phase2p_modewise_tail/phase2p_<piece_label>_THEOREM_READY_candidate.json
```

Split-chain candidate for the target interval:

```text
artifacts/proof_audit/lower_corridor/phase2t_parallel/phase2t_<label>_split_chain_candidate.json
```

## Integration after a successful split gap

Once Phase 2T closes the gap, include the piece candidates in a mixed Phase 2Q chain with the already-closed collar candidates. For example, the chain around collar 012 may become:

```text
000–011, 012a, <012b1 split pieces>, <012b2 split pieces>, 013–...
```

Phase 2T assembles the split gap itself. A later split-aware Phase 2R/2Q pass can automate the full mixed chain.

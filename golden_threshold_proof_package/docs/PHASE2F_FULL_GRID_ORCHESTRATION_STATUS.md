# Phase 2F status: full-grid lower-anchor orchestration

This update does **not** claim that the lower near-critical anchor has been
proved.  It adds the missing orchestration layer needed to finish Phase 2E on a
larger machine or in multiple resumable chunks.

## What was added

- `kam_theorem_suite/audit/lower_anchor_phase2e_full_grid.py`
  - writes the complete adaptive Phase-2E grid plan;
  - runs bounded Phase-2E chunks;
  - merges theorem-ready chunk candidates;
  - checks strict Phase-2B ingestion in-process.

- `scripts/audit/run_lower_anchor_phase2e_full_grid.py`
  - `--plan-only` writes the full grid plan;
  - `--chunk-index` / `--chunk-size` runs one resumable chunk;
  - `--segment-start` / `--segment-stop` runs an arbitrary slice;
  - `--merge-candidates` merges completed chunks;
  - `--check-strict-ingestion` immediately tests the merged candidate against the Phase-2B gate.

- `kam_theorem_suite/audit/lower_anchor_heavy_certificate.py`
  - now supports segment slicing via `segment_start`/`segment_stop`;
  - now supports wall-time bounded runs via `max_wall_seconds`;
  - marks every partial-grid run as diagnostic and non-promotable.

## Generated local artifacts

- `artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_full_grid_plan.json`
- `artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_000_candidate.json`
- `artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_000_strict_ingestion_check.json`
- `artifacts/proof_audit/replay/phase2f_targeted_tests.txt`

The bounded local chunk produced two theorem-ready local rows, but the candidate
is intentionally diagnostic because it does not reach the final anchor.  The
strict Phase-2B check therefore fails closed, as intended.

## How to run the full grid in chunks

Example 2-segment chunks:

```bash
python scripts/audit/run_lower_anchor_phase2e_full_grid.py \
  --chunk-index 0 --chunk-size 2 \
  --candidate-name lower_anchor_phase2f_chunk_000_candidate.json

python scripts/audit/run_lower_anchor_phase2e_full_grid.py \
  --chunk-index 1 --chunk-size 2 \
  --candidate-name lower_anchor_phase2f_chunk_001_candidate.json
```

After all chunks complete, merge:

```bash
python scripts/audit/run_lower_anchor_phase2e_full_grid.py \
  --merge-candidates \
    artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_000_candidate.json \
    artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_001_candidate.json \
    artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_002_candidate.json \
    artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_003_candidate.json \
    artifacts/proof_audit/lower_corridor/lower_anchor_phase2f_chunk_004_candidate.json \
  --check-strict-ingestion \
  --strict
```

The merge becomes theorem-facing only if every row is analytic-theorem-closed,
all adjacent rows overlap, and the merged coverage reaches
`[0.9716350, 0.9716360]`.

## Current mathematical status

Still fail-closed.  The local Phase-2E rows are encouraging, but the repository
must not promote the lower anchor until the full merged grid passes strict
Phase-2B ingestion.

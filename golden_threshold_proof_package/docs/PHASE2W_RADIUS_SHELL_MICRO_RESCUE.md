# Phase 2W: Radius-Shell Micro Rescue

Phase 2W is a targeted rescue layer for near-miss Phase 2V/2U microsegments. It is designed for cases where subdivision has produced very small intervals, but Phase 2P still misses by only `1e-8` to `1e-7` and the best rows are near the finite contraction boundary.

## Motivation

The Phase 2V `needle` profile intentionally used a narrow radius grid. In the collar `012b1` results, many pieces failed only narrowly. Several best rows used radius multipliers near the upper edge of the profile, for example `x1.25` with finite contraction safely below one. Those rows may close if Phase 2O/2P are rerun with a radius shell extending past the previous cap while keeping the sigma and tail-cutoff grids narrow enough to avoid the Phase 2P timeout.

Phase 2W therefore does **not** run broad grids. It runs a focused radius shell and small tail cutoff set.

## What it does

For each selected piece, Phase 2W runs:

1. Phase 2N using the same low-cost N=1024, oversample=16 solve.
2. Phase 2O using a focused radius shell, typically `1.20` through `1.60`.
3. Phase 2P using a narrow modewise tail grid around `sigma=1e-7` and cutoff around `1536`.
4. Candidate inspection and promotion if theorem-ready.
5. Checkpointed JSON and CSV summaries.

## Recommended use

First test one known best piece:

```bash
python scripts/audit/run_lower_anchor_phase2w_radius_shell_rescue.py \
  --label collar_012b1_v256 \
  --K-lo 0.9662501 \
  --K-hi 0.9663752 \
  --seed-json artifacts/proof_audit/lower_corridor/phase2n_probes/phase2n_collar_012a_N1024_os16_sg0p0001.json \
  --pieces 256 \
  --piece-indices 5 \
  --workers 1 \
  --profile shell
```

If that closes, use `--from-summary` and `--top-k` to target the best failed pieces from an existing Phase 2V summary.


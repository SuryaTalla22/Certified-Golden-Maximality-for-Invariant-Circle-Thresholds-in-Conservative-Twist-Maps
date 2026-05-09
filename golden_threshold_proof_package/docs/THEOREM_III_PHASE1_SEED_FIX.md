# Theorem III Track-B Phase-1 seed filename fix

This overlay updates `scripts/regenerate_theorem_iii_trackb_from_scratch.py` so the Track-B pipeline does not fail when the Phase-1 seed filename differs from the stale hard-coded value.

## What was wrong

The parent pipeline expected the Phase-1 seed at:

```text
artifacts/proof_audit/theorem_iii_trackb/phase1_seed/embeddings/K0p9716350000_M1024_steps44.npz
```

but the Phase-1 runner was invoked without an explicit continuation-step count in some runs. In that case it could create a file such as:

```text
artifacts/proof_audit/theorem_iii_trackb/phase1_seed/embeddings/K0p9716350000_M1024_steps40.npz
```

Phase 4f then failed with `FileNotFoundError` when it tried to load the stale hard-coded `steps44` path.

## What this overlay changes

The updated script:

1. makes the Phase-1 continuation-step count explicit, defaulting to `44`;
2. resolves the Phase-1 seed from `phase1_seed_summary.json` and the actual `embeddings/` directory after Phase 1 completes;
3. prefers the canonical `steps44` seed when present, but can continue from a valid produced seed instead of failing on a filename mismatch;
4. resolves the Phase-4f output from the Phase-4f summary before Phase 4i consumes it.

## How to apply

From the repository root:

```bash
unzip -o theorem_iii_phase1_seed_fix_overlay.zip -d /tmp/theorem_iii_phase1_seed_fix_overlay
rsync -av /tmp/theorem_iii_phase1_seed_fix_overlay/ ./
```

Then restart Theorem III cleanly:

```bash
rm -rf artifacts/proof_audit/theorem_iii_trackb

python scripts/regenerate_all_theorems_from_scratch.py \
  --use-cache \
  --workers "${SLURM_CPUS_ON_NODE:-64}" \
  --run-focused-tests \
  --fail-on-acceptance
```

If you want to test only Theorem III first:

```bash
python scripts/regenerate_theorem_iii_trackb_from_scratch.py \
  --from-scratch \
  --force \
  --workers "${SLURM_CPUS_ON_NODE:-64}" \
  --copy-to-stage-cache \
  --theorem-i-artifact artifacts/final_discharge/stage_cache/theorem_i_ii.json \
  --theorem-ii-artifact artifacts/final_discharge/stage_cache/theorem_i_ii.json \
  --theorem-iv-artifact artifacts/final_discharge/stage_cache/theorem_iv.json
```

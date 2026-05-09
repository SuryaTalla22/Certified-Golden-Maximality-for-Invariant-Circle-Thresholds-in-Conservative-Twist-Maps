# Stage-D verification resume note

This overlay adjusts `scripts/regenerate_all_theorems_from_scratch.py` so that fresh reconstruction does not compare regenerated stage-cache JSON bytes against the frozen `HASHES.sha256` ledger during downstream replay. By default Stage D now runs:

```bash
python scripts/replay_downstream_from_cache.py --no-hash-check
```

The stage-cache files are still required and the downstream theorem-facing replay still validates the proof chain. A fresh run writes a regenerated hash ledger at:

```text
artifacts/full_regeneration/<stamp>/REGENERATED_HASHES.sha256
```

Use the old frozen-ledger behavior only when intentionally validating the archived distribution:

```bash
python scripts/regenerate_all_theorems_from_scratch.py ... --strict-frozen-hash-check
```

The overlay also adds a Stage-B resume behavior: when `--use-cache` is passed and `artifacts/final_discharge/stage_cache/theorem_iii.json` already exists, the top-level script reuses it rather than rerunning the heavy Track-B Theorem III child. To force a rerun, use `--force` or `--from-scratch`.

For a verification-only resume after Theorem III has already completed, run:

```bash
python scripts/regenerate_all_theorems_from_scratch.py \
  --use-cache \
  --workers "${SLURM_CPUS_ON_NODE:-64}" \
  --run-focused-tests \
  --fail-on-acceptance
```

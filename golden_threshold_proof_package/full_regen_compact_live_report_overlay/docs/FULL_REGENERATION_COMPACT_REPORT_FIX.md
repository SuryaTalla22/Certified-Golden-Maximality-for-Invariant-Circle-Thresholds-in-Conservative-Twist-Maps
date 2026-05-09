# Full-regeneration compact live-report fix

This overlay updates `scripts/regenerate_all_theorems_from_scratch.py` so that the final live theorem-program report is written as a compact acceptance/status summary instead of embedding the full downstream theorem subreports.

The full Theorem VIII base/discharge artifacts can be multi-GB JSON files.  A fresh regeneration should keep those full theorem objects in `artifacts/final_discharge/stage_cache/`, but the final run manifest only needs the acceptance-facing fields, paths, sizes, and hashes.  The compact report avoids duplicating the Theorem VIII payload during `live_theorem_program_discharge_report_cache`, which can otherwise be killed by memory pressure.

## Resume command

After applying the overlay, resume with the cached objects:

```bash
python scripts/regenerate_all_theorems_from_scratch.py \
  --use-cache \
  --skip-theorem-iii \
  --workers "${SLURM_CPUS_ON_NODE:-64}" \
  --run-focused-tests \
  --fail-on-acceptance
```

`--skip-theorem-iii` is appropriate if `artifacts/final_discharge/stage_cache/theorem_iii.json` already exists and was produced successfully in the previous run.

## Optional cleanup

Remove only the failed live-report cache if it exists:

```bash
rm -f artifacts/final_discharge/stage_cache/live_theorem_program_discharge_report_cache.json
rm -f artifacts/final_discharge/stage_cache/live_theorem_program_discharge_report_summary_cache.json
```

Do not delete Theorem VIII stage-cache artifacts unless you intend to rebuild them.

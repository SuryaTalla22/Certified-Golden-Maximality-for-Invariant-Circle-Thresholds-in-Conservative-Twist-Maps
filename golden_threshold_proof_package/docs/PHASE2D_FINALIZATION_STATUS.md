# Phase 2D Finalization Status

This note records the code-side work completed after the Phase 2C repository review.

## What was added

1. `kam_theorem_suite/audit/lower_anchor_heavy_certificate.py`
   - Adds a conservative heavy lower-anchor certificate driver.
   - Builds an adaptive near-critical grid from the current lower endpoint to the final lower anchor.
   - Records modewise golden small-divisor summaries.
   - Converts analytic certificate outputs into Phase-2B-compatible `Y + Z r + T < r` rows.
   - Refuses theorem-facing promotion unless every segment has a safely positive analytic margin and positive recomputed Phase-2B margin.

2. `scripts/audit/generate_lower_anchor_heavy_candidate.py`
   - CLI for producing `lower_anchor_heavy_candidate.json`, `lower_anchor_heavy_report.json`, and table outputs.
   - Supports dry-run planning and actual heavy validator execution.
   - The default failure mode is diagnostic-only, not theorem-facing.

3. `kam_theorem_suite/audit/theorem_iv_cache_inventory.py`
   - Adds manifest-based Theorem-IV cache inventory and restoration helpers.
   - Audits which Theorem-IV manifest entries are present, missing, hash-checked, and available from older source roots.
   - Copies only real available files; it never fabricates missing cache entries.

4. `scripts/audit/restore_theorem_iv_cache.py`
   - CLI for copying old Theorem-IV cache files into the local stage cache.
   - Intended command:
     ```bash
     PYTHONPATH=. python -S scripts/audit/restore_theorem_iv_cache.py \
       --source-root /path/to/old/code_repository \
       --copy
     ```

5. New tests:
   - `tests/test_lower_anchor_heavy_certificate.py`
   - `tests/test_theorem_iv_cache_inventory.py`

## Local Theorem-IV restoration attempt

The old repository uploaded in this session contained only three heavy Theorem-IV cache files:

- `theorem_iv.json`
- `theorem_iv_lower_neighborhood.json`
- `theorem_iv_upper_bridge.json`

Those were copied into the local working tree for inspection and inventory. They are intentionally **not bundled** in the updated zip, because they are large archived cache artifacts and the handoff request specified that Theorem-IV files do not need to be returned.

The current manifest lists 39 Theorem-IV entries. With the current promotion artifact and the three old files locally copied, 4 entries were present and 35 were still missing from the local cache. This is a repository-completeness issue for Theorem IV, not a Phase-2 lower-anchor proof closure.

## Heavy lower-anchor status

A dry-run heavy lower-anchor candidate was generated:

- `artifacts/proof_audit/lower_corridor/lower_anchor_heavy_candidate.json`
- `artifacts/proof_audit/lower_corridor/lower_anchor_heavy_report.json`
- `tables/proof_audit/lower_corridor/lower_anchor_heavy_records.csv`
- `tables/proof_audit/lower_corridor/lower_anchor_heavy_records.tex`

The dry-run is intentionally diagnostic-only:

- `promotion_allowed = false`
- `failure_fields = ["some_heavy_segments_not_attempted", "analytic_theorem_closure_not_established_for_all_segments"]`

This preserves the fail-closed boundary: the final theorem-facing lower chain is still not promoted until a real heavy analytic run produces positive margins on every segment.

## Tests run

The following targeted smoke suite passed:

- `tests.test_lower_anchor_heavy_certificate`
- `tests.test_theorem_iv_cache_inventory`
- `tests.test_lower_anchor_regeneration_phase2c`
- `tests.test_upper_obstruction_audit`

The test log is stored at:

- `artifacts/proof_audit/replay/phase2d_new_tests.txt`

The existing Phase-2B lower closure and upper audit tests were also run individually during development and passed in visible output. Some broader shell-based runs in this container hung after printing successful test output because the environment spawned lingering normal-Python file-check processes; for this reason, the reproducible test path used `python -S` and explicit `PYTHONPATH=.`.

## Next command sequence for the full local run

After manually adding the full old Theorem-IV cache files on your end, the intended sequence is:

```bash
PYTHONPATH=. python -S scripts/audit/restore_theorem_iv_cache.py \
  --source-root /path/to/old/code_repository \
  --copy

PYTHONPATH=. python -S scripts/audit/generate_lower_anchor_heavy_candidate.py \
  --N-values 64,96,128,192,256 \
  --oversample-factor 8 \
  --candidate-name lower_anchor_heavy_candidate.json

PYTHONPATH=. python -S scripts/audit/regenerate_lower_anchor_chain.py \
  --candidate artifacts/proof_audit/lower_corridor/lower_anchor_heavy_candidate.json \
  --strict
```

The last command should continue to fail until the heavy candidate is genuinely theorem-facing.

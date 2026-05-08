# Phase 2K: Rescue Execution, Merge, and Strict-Ingestion Controller

Phase 2K is the execution boundary after the Phase 2J adaptive rescue plan.  It does **not** weaken the lower-anchor theorem gate.  It only runs or inventories rescue variants, selects rows whose raw radii-polynomial fields recompute a positive margin, merges those rows with the already theorem-ready prefix, and reruns strict Phase-2B ingestion.

## Added code

- `kam_theorem_suite/audit/lower_anchor_phase2k_rescue_execution.py`
- `scripts/audit/run_lower_anchor_phase2k_rescue_execution.py`
- `tests/test_lower_anchor_phase2k_rescue_execution.py`

## Intended full-environment command

```bash
python scripts/audit/run_lower_anchor_phase2k_rescue_execution.py \
  --execute \
  --site \
  --timeout-seconds 7200 \
  --strict
```

Use `--site` when the local theorem environment has real `mpmath` installed through the normal Python site path.  The generated Phase-2J shell script uses `-S`, which can accidentally hide site-packages on some machines; Phase 2K records this as an environment warning rather than silently treating fallback execution as theorem-grade.

## Current bundled status

The bundled run inventories the existing Phase-2J rescue candidates and merges only theorem-ready rows.  In the current artifact state, no Phase-2J rescue candidate is theorem-ready, so the merged Phase-2K candidate remains diagnostic-only and strict ingestion remains false.  This is the correct fail-closed result.

## Success condition

The lower-anchor blocker is closed only when:

```text
successful_parent_count = 8
failed_parent_count = 0
merged_promotion_allowed = true
strict_ingestion_passed = true
```

After that, run the Phase-2B promotion command on `lower_anchor_phase2k_merged_rescued_candidate.json`.

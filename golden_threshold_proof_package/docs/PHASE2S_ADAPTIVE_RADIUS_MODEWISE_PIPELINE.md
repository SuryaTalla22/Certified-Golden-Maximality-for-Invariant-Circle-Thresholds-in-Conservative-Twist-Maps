# Phase 2S: Adaptive Radius + Modewise Tail Automation Hotfix

## Purpose

Phase 2R successfully automated the collar workflow through Phase 2Q, but collar 011 exposed a coupling that the first automation pass did not exercise:

- Phase 2O's scalar-tail score may prefer a small radius row.
- Phase 2P's modewise-tail lemma may need to combine the modewise tail response with a larger theorem-eligible Phase 2O radius row.

The previous Phase 2P scanner consumed only the single selected Phase 2O candidate row.  This was sufficient for collars 000--010, but not for collar 011, where the wide-radius Phase 2O CSV contained radius rows with much larger allowable tail budgets.

## What changed

This patch changes Phase 2P and Phase 2R in two ways.

1. **Phase 2P now expands Phase 2O inputs.**
   - If the input is a Phase 2O scan report, Phase 2P scans every theorem-eligible Phase 2O row.
   - If the input is a Phase 2O candidate, Phase 2P follows the candidate's `source_artifact` back to the Phase 2O scan and scans every theorem-eligible row from that scan.
   - If the scan cannot be found, Phase 2P falls back to the selected candidate row.

2. **Phase 2R now uses a broader default Phase 2O radius grid and refreshes stale Phase 2O candidates.**
   - Default radius multipliers now include values up to `6.0`.
   - When resuming, Phase 2R checks whether an existing Phase 2O candidate came from a scan broad enough for the requested radius grid. If not, it regenerates Phase 2O.

## Expected effect

For collar 011, Phase 2P should now test combinations such as:

```text
Phase 2O radius row: strict_source_tail_radius_x6
Phase 2P tail model: strict_modewise_geometric_tail_response
```

instead of only reusing the radius multiplier 1.0 row.

## Theorem-facing rule

No diagnostic rows are promoted. Phase 2P scans only theorem-eligible Phase 2O rows by default. A candidate is promoted only if:

```text
theorem_facing = true
promotion_allowed = true
selected_phase2p_row.theorem_ready = true
failure_fields = []
```

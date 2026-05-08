# Track B Phase 5J: Branch/Chart Compatibility and Final Graph Consumption

Phase 5J appends the next two formal-component flags to the hash-bound lower-anchor attachment:

- `branch_chart_compatibility_proof = true`
- `final_graph_consumption_proof = true`

The phase is still fail-closed. It deliberately keeps these global flags false:

- `formal_interval_backend = false`
- `independent_replay_passed = false`

This means Phase 5E should still return `REJECT_FAIL_CLOSED` after Phase 5J, but the only remaining failures should be the global backend and independent replay flags.

The branch/chart component checks that the lower-anchor constants match the selected branch and chart contract:

- family: `standard_sine_twist_map`
- omega: `golden`
- lower anchor: `K >= 0.971635`
- norm/validation configuration: `nu = 1.001`, `radius = 3e-5`, `cutoff = full`, `tail_start = 0.90`
- local margin and Z thresholds remain satisfied
- all prior local component flags are already true
- the attachment is bound to the exact Phase 5D certificate SHA256

The final graph-consumption component states that the object may be consumed only as a direct lower-anchor certificate. It does not claim a full parameter interval or a mesh corridor.

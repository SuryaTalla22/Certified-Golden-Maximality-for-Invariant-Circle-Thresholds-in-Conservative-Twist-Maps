# Track B Phase 5G: Residual and Small-Divisor Formal Component Candidates

Phase 5G creates the first two independently replayable formal-component objects for the Theorem III Track B lower-anchor scaffold:

1. an outward-rounded scalar residual component, and
2. a finite golden small-divisor component.

The phase remains fail-closed. It may set only these two component evidence flags:

```text
outward_rounded_residual_proof = true
small_divisor_proof = true
```

It must not set:

```text
formal_interval_backend = true
independent_replay_passed = true
theorem_facing = true
promotion_allowed = true
```

The Phase 5E promotion gate is expected to continue rejecting the attachment until the remaining proof components are supplied and independently replayed.

## Primary selected configuration

```text
K = 0.971635
M = 8192
nu = 1.001
cutoff = full
tail_start = 0.90
radius = 3e-5
grid_factor = 4
```

## Outputs

```text
phase5g_formal_interval_attachment_COMPONENTS.json
phase5g_component_summary.json
phase5g_compact_report.json
phase5g_component_replay_summary.json
phase5g_replay_compact_report.json
```

## Notes

This phase uses IEEE-754 nextafter guards and deterministic replay. It is an incremental formalization step, not the final theorem-facing certificate.

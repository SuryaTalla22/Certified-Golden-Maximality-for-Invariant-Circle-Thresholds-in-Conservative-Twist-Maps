# Track B Phase 5D: Certificate Assembly Scaffold

Phase 5D assembles the best Phase 5C interval-backend candidate into a stable,
replayable **diagnostic-only** certificate scaffold for Theorem III. It does not
promote the result to a theorem-facing certificate.

## Inputs

Primary input is a Phase 5C backend summary or a single Phase 5C backend record.
The expected winning configuration is usually:

- `K = 0.971635`
- `M = 8192`
- `nu = 1.001`
- `radius = 3e-5`
- `grid_factor = 4`
- `cutoff = full` as primary, `frac:0.95` as comparator
- `tail_start = 0.90`

## Outputs

The assembly script writes:

- `theorem_iii_trackb_phase5d_certificate_scaffold.json`
- `phase5d_replay_summary.json`
- `phase5d_assembly_summary.json`

The scaffold includes:

- lower-anchor claim scaffold;
- seed path and validation parameters;
- Y/Z/Q interval-backend upper bounds;
- recomputed radii inequality;
- residual, small-divisor, frame, twist, and reducibility quantities;
- active assumptions and open hypotheses;
- negative-control replay results.

## Important limitations

Phase 5D is still not theorem-facing. It freezes the candidate and replay logic so
that Phase 5E can add fail-closed theorem replay and formal promotion checks.

The scaffold must remain:

```json
{
  "diagnostic_only": true,
  "theorem_facing": false,
  "promotion_allowed": false
}
```

until a later phase attaches independent formal interval verification and final
proof-graph compatibility checks.

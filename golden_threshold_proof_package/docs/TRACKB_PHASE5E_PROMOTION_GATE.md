# Track B Phase 5E: Fail-Closed Promotion Gate

Phase 5E is a theorem-facing replay **gate**, not a proof promotion by itself.
Its purpose is to make accidental promotion impossible.

Input:

- a Phase 5D diagnostic certificate scaffold;
- optionally, a separate formal interval attachment.

Expected result without formal attachment:

- scaffold replay checks pass;
- negative controls pass;
- theorem replay is rejected;
- `theorem_facing=false` and `promotion_allowed=false`.

Promotion requires a separate JSON attachment with schema
`theorem_iii_trackb_phase5e_formal_interval_attachment_v1` and all required
formal evidence flags set to true.  The attachment must also reference the
SHA-256 hash of the exact Phase 5D scaffold it promotes.

Required formal evidence keys:

- `formal_interval_backend`
- `independent_replay_passed`
- `outward_rounded_residual_proof`
- `small_divisor_proof`
- `cohomology_inverse_proof`
- `frame_reducibility_proof`
- `nonlinear_bound_proof`
- `tail_bound_proof`
- `branch_chart_compatibility_proof`
- `final_graph_consumption_proof`

This overlay intentionally emits a template attachment whose proof flags are
false.  It is a to-do list, not evidence.

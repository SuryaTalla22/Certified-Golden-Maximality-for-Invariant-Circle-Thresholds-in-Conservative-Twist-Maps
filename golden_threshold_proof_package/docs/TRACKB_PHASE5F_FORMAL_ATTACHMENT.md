# Track B Phase 5F — Formal Attachment Candidate

Phase 5F is a fail-closed bridge between the Phase 5D certificate scaffold and a future theorem-facing formal interval certificate.

It **does not** promote the certificate. Instead, it assembles a formal-attachment candidate using the Phase 5C interval-backend record, replays the radii inequality in high-precision decimal arithmetic, records file hashes and selected constants, and emits the exact formal evidence keys that remain false.

## Inputs

- Phase 5D certificate scaffold JSON.
- Phase 5C interval backend summary JSON, preferably the conservative stress summary.

## Outputs

- `phase5f_formal_interval_attachment_CANDIDATE.json`
- `phase5f_attachment_candidate_summary.json`
- `phase5f_attachment_candidate_replay_summary.json`
- `phase5f_compact_report.json`

## Fail-closed policy

The generated candidate uses schema:

```text
theorem_iii_trackb_phase5e_formal_interval_attachment_v1
```

but leaves all required formal evidence flags set to `false`:

```text
formal_interval_backend
independent_replay_passed
outward_rounded_residual_proof
small_divisor_proof
cohomology_inverse_proof
frame_reducibility_proof
nonlinear_bound_proof
tail_bound_proof
branch_chart_compatibility_proof
final_graph_consumption_proof
```

This means Phase 5E should still reject it. That is intentional. Phase 5F is the audit ledger for the missing proof obligations, not a proof.

## Success criterion

Phase 5F succeeds when:

- the attachment candidate is generated;
- the decimal replay verifies positive margin and threshold compatibility;
- all required formal evidence keys are present and false;
- the candidate is expected to be rejected by Phase 5E until genuine formal evidence is attached.

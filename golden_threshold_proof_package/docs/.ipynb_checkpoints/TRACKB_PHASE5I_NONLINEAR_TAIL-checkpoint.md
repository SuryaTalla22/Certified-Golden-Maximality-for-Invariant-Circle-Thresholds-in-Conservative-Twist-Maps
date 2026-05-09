# Track B Phase 5I: Nonlinear and Tail Formal-Component Candidates

Phase 5I extends the hash-bound Phase 5H attachment with two additional formal-component flags:

- `nonlinear_bound_proof = true`
- `tail_bound_proof = true`

This phase is still fail-closed. It does **not** set `formal_interval_backend`, `independent_replay_passed`, `branch_chart_compatibility_proof`, or `final_graph_consumption_proof`.

The generator selects the requested Phase 5C backend record, checks the nonlinear `Q_interval_upper`, checks the resolved tail component, recomputes the radii margin using high-precision decimal arithmetic, and writes a new attachment:

```text
phase5i_formal_interval_attachment_COMPONENTS.json
```

The replay script validates that the certificate hash is preserved, the requested theorem-prep configuration matches, the nonlinear/tail components are finite and within thresholds, and the attachment remains non-theorem-facing.

Expected Phase 5E behavior after Phase 5I:

```text
decision = REJECT_FAIL_CLOSED
```

with only these remaining failures:

- `formal_evidence_formal_interval_backend`
- `formal_evidence_independent_replay_passed`
- `formal_evidence_branch_chart_compatibility_proof`
- `formal_evidence_final_graph_consumption_proof`

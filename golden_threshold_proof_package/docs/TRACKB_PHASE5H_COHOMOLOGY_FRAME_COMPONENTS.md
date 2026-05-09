# Track B Phase 5H: Cohomology-Inverse and Frame/Reducibility Components

Phase 5H adds two more fail-closed formal-component candidates to the Theorem III Track B lower-anchor attachment:

```text
cohomology_inverse_proof = true
frame_reducibility_proof = true
```

It assumes Phase 5G-c has already completed the residual and small-divisor components. Phase 5H does **not** set the global formal backend flags and does **not** promote the certificate:

```text
formal_interval_backend = false
independent_replay_passed = false
theorem_facing = false
promotion_allowed = false
```

The expected Phase 5E outcome after Phase 5H is still `REJECT_FAIL_CLOSED`, but the remaining failures should be narrowed to:

```text
formal_evidence_formal_interval_backend
formal_evidence_independent_replay_passed
formal_evidence_nonlinear_bound_proof
formal_evidence_tail_bound_proof
formal_evidence_branch_chart_compatibility_proof
formal_evidence_final_graph_consumption_proof
```

The component objects are replayable and tied to the exact Phase 5D certificate hash. They carry forward the selected Phase 5C/5D constants:

```text
K = 0.971635
M = 8192
nu = 1.001
cutoff = full
radius = 3e-5
tail_start = 0.90
```

This phase is still not a final theorem-facing proof; it only adds the Z-block component evidence in a fail-closed way.

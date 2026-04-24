# Validator specification for the paper-facing proof ledger

This document records the deterministic validator invariants that are cited by
the manuscript and exercised by the replay scripts and negative-control tests.
The guiding rule is fail-closed validation: a theorem-facing object is accepted
only when required status, interval, symbolic, provenance, and scope fields are
present and mutually compatible.

## Scope rule

The final theorem is scoped to the certified universe named in
`CERTIFIED_UNIVERSE.json`.  The map family, arithmetic domain, threshold branch,
normalization convention, and artifact manifest must match the final replay
ledger.  A scope mismatch is a validation failure, not a warning.

## Replay levels

| Replay | Script | Validator expectation |
|---|---|---|
| Minimal | `scripts/replay_minimal.py` | compact theorem-facing shells pass all logical and interval checks; no cache provenance is required |
| Downstream from cache | `scripts/replay_downstream_from_cache.py` | cached I--II/III/IV artifacts exist, their hashes match `HASHES.sha256`, and V-and-beyond replay verifies |
| Full archival | `scripts/replay_full.py` | fail-closed stub until the heavy Theorem-IV regeneration command is wired |

## Theorem-facing versus diagnostic objects

A theorem-facing object may be consumed by the final replay only if it exposes:

1. a `theorem_status` or `status` field accepted by the consuming layer;
2. empty `active_assumptions` and `open_hypotheses`, unless the consuming layer
   explicitly discharges them;
3. the finite interval, symbolic, or provenance fields required by the layer;
4. upstream artifact/provenance compatibility in the manifest and hash ledger.

Diagnostic objects may remain in the repository, but they must not be consumed by
identification, VI, VII, VIII, or the final replay unless wrapped in a
theorem-facing contract.  In particular, the raw Theorem-V transport shell is not
the theorem object; the compressed Theorem-V contract is the theorem-facing
object.

## Core pass conditions

| Layer | Pass condition |
|---|---|
| I--II | workstream package is paper-facing/final and has no active/open burdens |
| III | lower interval is present and ordered; small-divisor, invariance-defect, tail, and lower-interval closure are represented by the accepted lower-corridor artifact |
| IV | upper obstruction status is final; support-core stability, tail coherence/stability, and analytic incompatibility are true |
| V | compressed contract is strong; target interval exists; raw shell is not consumed; transport lock and gap preservation are certified |
| Identification | branch labels, chart labels, overlap window, and native-tail witness are compatible; the witness is strictly inside the overlap window |
| VI | screened one-variable envelope/top-gap object is strong; most dangerous challenger upper lies strictly below the golden lower anchor; global obligations are handed to VII |
| VII | all six global-exhaustion failure lists are empty; pending near-top count is zero; near-top upper bound is strictly below the golden lower anchor |
| VIII | final implication, `GL(2,Z)` normalization, and universe matching are closed |
| Final replay | all support/readiness/upstream flags are true; failed-check list is empty; active assumptions, open hypotheses, and remaining true mathematical burden are empty |

## Required cached artifacts for downstream replay

The downstream replay requires, by default:

```text
artifacts/final_discharge/stage_cache/theorem_i_ii.json
artifacts/final_discharge/stage_cache/theorem_iii.json
artifacts/final_discharge/stage_cache/theorem_iv.json
```

If `HASHES.sha256` is available, the script verifies those artifacts against the
ledger.  Missing files, missing hash entries, or hash mismatches cause the replay
to fail closed unless the user explicitly passes `--allow-synthetic-upstream`.
That fallback is for smoke testing only and must not be used as publication
evidence.

## Negative-control philosophy

A validator that only accepts the happy path is not enough.  The publication test
suite therefore checks rejection of:

- raw/diagnostic Theorem-V shells;
- nonfinal Theorem-VII status;
- nonempty VII failure fields, including uncontrolled omitted labels;
- branch-label or chart-label mismatch at identification;
- witness intervals outside the overlap window;
- eroded/nonpositive final comparison margins;
- final-reduction scope mismatch;
- missing cached upstream artifacts;
- required artifact hash mismatches.

These failures are expected and desirable: they demonstrate that the validator is
not merely accepting status strings.

# Phase 2B: Lower-Anchor Closure Audit

Phase 2B is the strict Theorem-III completion boundary.  Phase 2 already turns the currently cached lower-side evidence into a proof-carrying segment ledger, but the present cached ledger stops at the local/neighborhood lower corridor rather than the near-critical golden lower anchor.  Phase 2B therefore adds a fail-closed ingestion and validation path for a regenerated or manually supplied heavy lower-anchor candidate.

The Phase-2B code does **not** fabricate a near-critical lower KAM certificate.  It accepts a candidate only when the candidate exposes raw segment rows with

```text
K_lo, K_hi, residual_Y, linear_defect_Z, tail_bound_T, radius_r
```

and every row recomputes the lower validation inequality

```text
Y + Z*r + T < r.
```

A candidate is promoted only if all of the following are true:

1. every candidate row has a strictly positive recomputed radii margin;
2. every row is theorem-facing, non-diagnostic, and source-attributed;
3. candidate rows overlap each other in the parameter coordinate;
4. the first candidate row overlaps the existing Phase-2 covered corridor;
5. the combined chain reaches the final near-critical anchor `[0.9716350, 0.9716360]`;
6. the hardened Phase-8 lower payload validator returns no failures.

## New files

```text
kam_theorem_suite/audit/lower_anchor_closure.py
scripts/audit/regenerate_lower_anchor_chain.py
scripts/regenerate_lower_anchor_chain.py
tests/test_lower_anchor_closure_phase2b.py
```

## Important commands

Write a diagnostic template for a future heavy artifact:

```bash
python -S scripts/audit/regenerate_lower_anchor_chain.py \
  --write-template artifacts/proof_audit/lower_corridor/lower_anchor_candidate_TEMPLATE.json
```

Run the Phase-2B boundary without a candidate.  This is expected to fail closed and record that the lower-anchor candidate is missing:

```bash
python -S scripts/audit/regenerate_lower_anchor_chain.py --no-figures
```

Ingest a regenerated heavy candidate:

```bash
python -S scripts/audit/regenerate_lower_anchor_chain.py \
  --candidate artifacts/proof_audit/lower_corridor/my_heavy_lower_anchor_candidate.json \
  --promote
```

`--promote` overwrites the canonical `lower_corridor_audit.bundle.json` only if the candidate passes strict validation.  Without `--promote`, the strict closure bundle is still written as:

```text
artifacts/proof_audit/lower_corridor/lower_anchor_closure_audit.bundle.json
```

The Phase-7 replay protocol now prefers a valid Phase-2B closure bundle when it exists; otherwise it falls back to the Phase-2 lower-corridor audit and reports the known lower gap.

## Current repository status

The returned bundle includes the Phase-2B machinery and a fail-closed Phase-2B report.  It does not include a regenerated heavy near-critical lower-anchor candidate.  Therefore the strict theorem status remains blocked by the same honest condition:

```text
strict_final_ready = false
known_lower_gap = true
```

This is the desired behavior until an actual heavy lower-anchor artifact is supplied or regenerated.

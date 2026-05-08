# Phase 2E Lower-Anchor Analytic Krawczyk Upgrade

This repository update adds the Phase-2E analytic lower-corridor machinery.  The
goal is to replace the Phase-2D aggregate diagnostic lower-anchor probe with a
proof-payload generator that exposes the raw analytic radii-polynomial terms

\[
Y + Zr + T < r.
\]

## New code path

Phase 2E adds `kam_theorem_suite/analytic_lower_krawczyk.py`.  This module:

- builds a modewise small-divisor ledger for the golden rotation class;
- recomputes the invariance residual from source collocation samples when they
  are present in the upstream analytic invariant-circle certificate;
- applies the cohomological inverse mode-by-mode instead of multiplying the
  aggregate weighted residual by a single pessimistic inverse bound;
- separates `Y`, `Z`, `T`, `r`, raw recomputable margin, and outward-rounded
  theorem-readiness margin;
- fails closed when source samples are missing, when only compact status fields
  are present, or when the outward-rounded margin is not safely positive.

The heavy lower-anchor driver in
`kam_theorem_suite/audit/lower_anchor_heavy_certificate.py` now consumes this
Phase-2E direct ledger by default.  It still supports the legacy Phase-2D
aggregate fallback for archival/synthetic shells, but such fallback records are
not silently promoted unless the legacy strict conditions also hold.

## Script interface

`python scripts/audit/generate_lower_anchor_heavy_candidate.py` now generates a
Phase-2E candidate by default.  The new relevant switches are:

```bash
--disable-phase2e-direct-radii-ledger
--phase2e-nonlinear-margin-fraction 0.25
```

The direct ledger is enabled unless explicitly disabled.

## Current generated artifact status

A bounded sandbox run was executed with:

```bash
python scripts/audit/generate_lower_anchor_heavy_candidate.py \
  --max-segments 2 \
  --N-values 16,32 \
  --oversample-factor 4 \
  --candidate-name lower_anchor_heavy_candidate.json
```

The resulting first two segments are theorem-ready under the Phase-2E local
ledger, with positive Phase-2B-shaped raw margins.  The generated candidate is
still not globally promotable because only two segments were run in the bounded
sandbox pass and the grid therefore does not reach the final near-critical anchor
`[0.9716350, 0.9716360]`.

This is expected and desirable: Phase-2B strict ingestion still rejects the
candidate with `final_anchor_not_reached` and diagnostic/theorem-facing flags
left false at the candidate level.

## Tests added

- `tests/test_analytic_lower_krawczyk_phase2e.py`
- `tests/test_lower_anchor_heavy_phase2e.py`

The tests verify that:

1. golden small-divisor gaps are positive over the tested mode range;
2. a modewise divisor ledger is generated and serialized;
3. a perfect zero-forcing source certificate closes the direct Phase-2E
   radii-polynomial inequality;
4. missing source samples fail closed rather than silently promoting an aggregate
   shell;
5. the heavy lower-anchor driver can promote a synthetic Phase-2E direct ledger
   even when the old compact theorem-status string would not be sufficient;
6. disabling the Phase-2E direct ledger restores fail-closed behavior for a
   negative legacy theorem margin.

## What remains

The next heavy run should use the full adaptive near-anchor grid and a larger
resolution ladder, for example:

```bash
python scripts/audit/generate_lower_anchor_heavy_candidate.py \
  --N-values 32,64,96,128,192 \
  --oversample-factor 8 \
  --candidate-name lower_anchor_heavy_candidate.json
```

If that run produces every segment with positive Phase-2E direct margins and
coverage through the final anchor, then run:

```bash
python scripts/audit/regenerate_lower_anchor_chain.py \
  --candidate artifacts/proof_audit/lower_corridor/lower_anchor_heavy_candidate.json \
  --strict
```

Only after that passes should the same command be run with `--promote`.

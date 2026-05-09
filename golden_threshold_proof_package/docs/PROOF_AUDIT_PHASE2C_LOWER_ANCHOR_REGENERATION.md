# Phase 2C — Lower-Anchor Regeneration Attempt

Phase 2B created the strict ingestion boundary for a heavy Theorem-III lower-anchor candidate. Phase 2C performs the next honest computational step: it drives the existing finite-dimensional invariant-circle validation stack across the missing interval from the cached lower-corridor endpoint to the near-critical anchor.

## What Phase 2C generates

The new generator writes:

- `artifacts/proof_audit/lower_corridor/lower_anchor_finite_dimensional_candidate.json`
- `artifacts/proof_audit/lower_corridor/lower_anchor_regeneration_report.json`
- `artifacts/proof_audit/lower_corridor/lower_anchor_phase2c_ingestion_summary.json`
- `tables/proof_audit/lower_corridor/lower_anchor_regeneration_records.csv`
- `tables/proof_audit/lower_corridor/lower_anchor_regeneration_records.tex`
- `figures/proof_audit/lower_corridor/lower_anchor_regeneration_finite_margins.pdf`
- `figures/proof_audit/lower_corridor/lower_anchor_regeneration_analytic_probe.pdf`

The generated candidate is shaped so that Phase 2B can ingest it, but it remains diagnostic-only unless every segment also has a positive analytic theorem-closure margin.

## Current result

The finite-dimensional validations succeed across the generated chain and reach the final anchor. The minimum finite-dimensional radii margin in the generated run is positive. However, the analytic closure probe is still negative at the near-critical end, so the candidate is not theorem-facing and is not promotable.

This is the desired fail-closed behavior: the repository now distinguishes a useful finite-dimensional lower-anchor regeneration attempt from a theorem-grade lower KAM certificate.

## How to run

```bash
python scripts/audit/generate_lower_anchor_candidate.py \
  --segments 6 \
  --N 32 \
  --oversample-factor 2 \
  --analytic-N-values 32,64 \
  --analytic-probe-at last
```

To test the strict boundary, feed the generated file back into Phase 2B:

```bash
python scripts/audit/regenerate_lower_anchor_chain.py \
  --candidate artifacts/proof_audit/lower_corridor/lower_anchor_finite_dimensional_candidate.json \
  --strict
```

The strict command should fail until the candidate is replaced by a genuinely theorem-facing analytic-closure payload.

## Why this is not promoted

A finite-dimensional collocation Newton/radii inequality has the form

```text
eta + 0.5 * B * L(r) * r^2 < r
```

For Phase 2B compatibility, this is encoded as

```text
Y + Z*r + T < r,
Y = eta,
Z = 0.5 * B * L(r) * r,
T = 0.
```

That is a valid record of the finite-dimensional calculation, but it does not close the infinite-dimensional analytic-tail, small-divisor, and invariance-defect obligations needed for Theorem III. The Phase 2C output therefore remains `diagnostic_only: true` unless analytic theorem closure is explicitly positive for every segment.

## Next technical target

The next numerical target is to make the analytic theorem margin positive near the final anchor. The likely tuning knobs are:

1. increase Fourier resolution beyond the lightweight Phase-2C run,
2. use adaptive smaller segments near the final anchor,
3. improve the analytic defect/tail majorants,
4. improve the cohomological inverse/small-divisor bound used by the analytic closure,
5. rerun Phase 2C with analytic probes on all late segments,
6. only then promote through Phase 2B.

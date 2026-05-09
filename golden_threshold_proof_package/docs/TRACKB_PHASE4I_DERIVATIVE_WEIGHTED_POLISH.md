# Track B Phase 4i: Spectral Forensics and Derivative-Weighted Polish

This overlay is diagnostic-only. It is not a theorem-facing validator and it does not
produce interval or outward-rounded proof constants.

## Purpose

Prior Track B diagnostics showed that the final-anchor seeds solve the scalar
invariance equation well, but the derivative/cocycle residual needed for automatic
reducibility remains too large. Phase 4g verified that this is not a sign or frame
formula mismatch. Phase 4i therefore changes the numerical objective: instead of
polishing only the scalar residual, it inspects and then penalizes the derivative of
the scalar residual.

## Components

- `phase4i_spectral_forensics.py`: audits Fourier residual spectra, derivative-weighted residual spectra, shell summaries, and top modes.
- `phase4i_h1_polish.py`: runs a diagnostic H1/analytic-derivative weighted Gauss-Newton/LSMR polish.

## Acceptance logic

A candidate should still be audited afterward with the existing Phase 4d target-frame
audit and Phase 4g tangent-consistency audit. Do not promote any Phase 4i output to a
proof artifact directly.

Working numerical targets:

- scalar/grid-tested residual <= 1e-8
- tangent residual <= 5e-5 to 7e-5
- upper-triangular/a21 defect <= 1e-4 to 2e-4
- source/target frame determinant defects at machine scale

## Notes

The H1 polish objective stacks scalar residual rows and derivative-residual rows,
with optional high-mode damping. It is intentionally a pilot-level diagnostic to
determine whether derivative-weighted polishing is promising before moving to a
high-precision or true FHL-frame Newton implementation.

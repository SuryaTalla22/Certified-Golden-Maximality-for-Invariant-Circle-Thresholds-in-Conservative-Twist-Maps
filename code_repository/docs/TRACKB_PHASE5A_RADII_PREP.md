# Track B Phase 5A — Radii-Prep / Intervalization Scaffold

This overlay is diagnostic only. It reads one or more selected Track B seeds and computes proof-shaped, double-precision proxies for quantities needed by a later theorem-facing radii-polynomial validator.

It estimates:

- scalar residual and derivative residual;
- weighted Fourier residual norms for a grid of analytic weights `nu`;
- observed core/tail splits for several cutoff choices;
- resolved golden small-divisor statistics;
- cohomology correction norm proxies;
- target-frame/automatic-reducibility geometry proxies;
- candidate `Y`, `Z`, and `Q` radii-polynomial proxy terms;
- candidate radius margins over a user-provided radius grid.

These numbers are not outward-rounded and must not be promoted to theorem-facing claims. The purpose is to choose a plausible `nu`, core cutoff, tail model, and dominant-error strategy before implementing interval arithmetic.

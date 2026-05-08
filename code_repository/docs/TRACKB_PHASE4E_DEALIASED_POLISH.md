# Track B Phase 4e: Dealiased Newton Seed Polish

This diagnostic phase polishes a saved Track-B embedding by evaluating the nonlinear standard-sine invariance residual on an oversampled grid, projecting the residual back to the core Fourier modes, and applying damped Newton/GMRES to the projected residual.

Purpose: reduce aliasing-driven tangent and automatic-reducibility defects before intervalization.

This is **not** theorem-facing. Outputs remain diagnostic-only and must not be consumed by the final replay.

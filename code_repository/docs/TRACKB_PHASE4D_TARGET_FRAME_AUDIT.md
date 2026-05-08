# Track B Phase 4d: Target-frame automatic-reducibility audit

Phase 4b fixed the lift residual but still shifted the nonlinear symplectic normal vector to assemble the target frame.  This is diagnostic-fragile because the normal is a nonlinear function of the tangent and its tail is not represented exactly.

This overlay recomputes the target normal directly from the shifted tangent:

```text
n(theta+omega) = (-r'(theta+omega), x'(theta+omega)) / |W'(theta+omega)|^2
```

instead of using a Fourier shift of `n(theta)`.  The output is still diagnostic only and must not be promoted to Theorem III.  Its purpose is to decide whether the Phase 4 failure was mostly a frame-normalization artifact or whether the seed still needs dealiased/high-precision refinement.

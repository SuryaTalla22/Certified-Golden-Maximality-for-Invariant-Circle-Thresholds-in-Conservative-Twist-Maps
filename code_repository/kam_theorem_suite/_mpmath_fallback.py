from __future__ import annotations

"""Tiny fallback subset of mpmath used only when the real dependency is absent.

This module is intentionally modest and float-based.  It exists so lightweight
and lower-collocation audit paths can run in minimal environments that lack
mpmath.  It is *not* a replacement for rigorous interval arithmetic.  Code that
needs theorem-grade interval enclosure should still use a real mpmath install;
outputs generated with this fallback remain diagnostic unless the surrounding
validator explicitly certifies every required margin.
"""

import contextlib
import math
from typing import Any, Iterable

pi = math.pi
inf = math.inf

class _MPContext:
    dps: int = 53

mp = _MPContext()


def mpf(value: Any = 0.0) -> float:
    if isinstance(value, _Interval):
        return 0.5 * (value.a + value.b)
    if isinstance(value, (list, tuple)):
        if len(value) == 0:
            return 0.0
        return float(value[0])
    return float(value)


def sqrt(x: Any) -> float:
    return math.sqrt(float(x))


def sin(x: Any) -> float:
    return math.sin(float(x))


def cos(x: Any) -> float:
    return math.cos(float(x))


def exp(x: Any) -> float:
    return math.exp(float(x))


def fabs(x: Any) -> float:
    return abs(float(x))


@contextlib.contextmanager
def workdps(dps: int):
    old = mp.dps
    mp.dps = int(dps)
    try:
        yield
    finally:
        mp.dps = old


class _Interval:
    __slots__ = ("a", "b")
    def __init__(self, value: Any = 0.0, hi: Any | None = None):
        if hi is not None:
            lo_f = float(value); hi_f = float(hi)
        elif isinstance(value, _Interval):
            lo_f, hi_f = value.a, value.b
        elif isinstance(value, (list, tuple)) and len(value) >= 2:
            lo_f, hi_f = float(value[0]), float(value[1])
        else:
            lo_f = hi_f = float(value)
        if lo_f <= hi_f:
            self.a, self.b = lo_f, hi_f
        else:
            self.a, self.b = hi_f, lo_f
    def __float__(self) -> float:
        return 0.5 * (self.a + self.b)
    def __repr__(self) -> str:
        return f"iv.mpf([{self.a!r}, {self.b!r}])"
    def _coerce(self, other: Any) -> "_Interval":
        return other if isinstance(other, _Interval) else _Interval(other)
    def __add__(self, other: Any):
        o = self._coerce(other); return _Interval(self.a + o.a, self.b + o.b)
    __radd__ = __add__
    def __sub__(self, other: Any):
        o = self._coerce(other); return _Interval(self.a - o.b, self.b - o.a)
    def __rsub__(self, other: Any):
        o = self._coerce(other); return _Interval(o.a - self.b, o.b - self.a)
    def __neg__(self):
        return _Interval(-self.b, -self.a)
    def __mul__(self, other: Any):
        o = self._coerce(other)
        vals = [self.a*o.a, self.a*o.b, self.b*o.a, self.b*o.b]
        return _Interval(min(vals), max(vals))
    __rmul__ = __mul__
    def __truediv__(self, other: Any):
        o = self._coerce(other)
        if o.a <= 0.0 <= o.b:
            return _Interval(-math.inf, math.inf)
        vals = [self.a/o.a, self.a/o.b, self.b/o.a, self.b/o.b]
        return _Interval(min(vals), max(vals))
    def __rtruediv__(self, other: Any):
        return self._coerce(other).__truediv__(self)
    def __abs__(self):
        if self.a <= 0.0 <= self.b:
            return _Interval(0.0, max(abs(self.a), abs(self.b)))
        return _Interval(min(abs(self.a), abs(self.b)), max(abs(self.a), abs(self.b)))
    def __lt__(self, other: Any): return float(self) < float(other)
    def __le__(self, other: Any): return float(self) <= float(other)
    def __gt__(self, other: Any): return float(self) > float(other)
    def __ge__(self, other: Any): return float(self) >= float(other)


class _IntervalContext:
    @staticmethod
    def mpf(value: Any = 0.0):
        return _Interval(value)
    @staticmethod
    def sin(x: Any):
        x = x if isinstance(x, _Interval) else _Interval(x)
        # crude enclosure by endpoint plus global extrema check over intervals
        lo, hi = x.a, x.b
        if not (math.isfinite(lo) and math.isfinite(hi)) or hi - lo >= 2*math.pi:
            return _Interval(-1.0, 1.0)
        vals = [math.sin(lo), math.sin(hi)]
        # include extrema pi/2 + k*pi within range
        k0 = math.floor((lo - math.pi/2)/math.pi) - 1
        k1 = math.ceil((hi - math.pi/2)/math.pi) + 1
        for k in range(int(k0), int(k1)+1):
            t = math.pi/2 + k*math.pi
            if lo <= t <= hi:
                vals.append(math.sin(t))
        return _Interval(min(vals), max(vals))
    @staticmethod
    def cos(x: Any):
        x = x if isinstance(x, _Interval) else _Interval(x)
        return _IntervalContext.sin(_Interval(x.a + math.pi/2, x.b + math.pi/2))

iv = _IntervalContext()

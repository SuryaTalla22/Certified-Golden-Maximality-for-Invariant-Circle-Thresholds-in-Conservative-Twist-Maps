#!/usr/bin/env python3
from __future__ import annotations

"""Compatibility wrapper for scripts/audit/audit_transport_budget.py."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.audit_transport_budget import main

if __name__ == "__main__":
    raise SystemExit(main())

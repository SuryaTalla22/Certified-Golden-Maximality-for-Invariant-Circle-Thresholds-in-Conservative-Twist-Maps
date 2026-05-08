#!/usr/bin/env python3
from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "audit" / "audit_arithmetic_domain.py"), run_name="__main__")

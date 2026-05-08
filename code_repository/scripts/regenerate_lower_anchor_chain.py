#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "scripts" / "audit" / "regenerate_lower_anchor_chain.py"), run_name="__main__")

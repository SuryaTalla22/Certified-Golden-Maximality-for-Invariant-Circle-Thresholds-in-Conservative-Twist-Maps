#!/usr/bin/env python3
from pathlib import Path
import os
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kam_theorem_suite.audit.manuscript_audit_outputs import cli_tables
if __name__ == "__main__":
    code = cli_tables()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(code)

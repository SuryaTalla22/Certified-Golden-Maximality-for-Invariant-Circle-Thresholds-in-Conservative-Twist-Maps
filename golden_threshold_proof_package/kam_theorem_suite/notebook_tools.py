from __future__ import annotations

"""Helpers for notebook execution and bootstrap.

The main practical issue observed in user notebook runs was environment drift:
notebooks were launched from the ``notebooks/`` directory, so the project root
was not automatically importable.  This module provides a tiny, explicit helper
that notebook cells can use without relying on global environment state.
"""

from pathlib import Path
import sys


def bootstrap_project_root(start: str | Path | None = None) -> str:
    """Insert the nearest project root containing ``kam_theorem_suite``.

    Returns the detected root as a string so notebooks can print/log it.
    """
    here = Path(start or Path.cwd()).resolve()
    candidates = [here, *here.parents]
    for cand in candidates:
        if (cand / 'kam_theorem_suite').exists() or (cand / 'pyproject.toml').exists():
            root = str(cand)
            if root not in sys.path:
                sys.path.insert(0, root)
            return root
    raise RuntimeError(f'Could not find project root from {here}')


__all__ = ['bootstrap_project_root']

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


def _sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {str(k): _sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]

    if isinstance(obj, np.ndarray):
        return _sanitize_for_json(obj.tolist())

    if isinstance(obj, (np.integer,)):
        return int(obj)

    if isinstance(obj, (np.floating, float)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return None
        return val

    if isinstance(obj, (np.bool_,)):
        return bool(obj)

    return obj

def save_progress(rows):
    clean_rows = _sanitize_for_json(rows)
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(clean_rows, f, indent=2)


@dataclass
class ExperimentPaths:
    root: Path

    def __post_init__(self):
        self.root = Path(self.root)
        self.data = self.root / "data"
        self.figures = self.root / "figures"
        self.tables = self.root / "tables"
        self.cache = self.root / "cache"
        for p in (self.root, self.data, self.figures, self.tables, self.cache):
            p.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path: str | Path, text: str, *, encoding: str = "utf-8") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding=encoding) as f:
        f.write(text)
    os.replace(tmp, path)
    return path


def save_json(obj: Any, path: str | Path, *, indent: int = 2) -> Path:
    path = Path(path)
    clean_obj = _sanitize_for_json(obj)
    payload = json.dumps(clean_obj, indent=indent, allow_nan=False)
    return atomic_write_text(path, payload + "\n")


def load_json(path: str | Path):
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

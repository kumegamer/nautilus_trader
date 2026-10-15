"""Experiment paths, immutable hashes, and predeclared candidates."""

import hashlib
import itertools
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def config():
    return json.loads((ROOT / "config.json").read_text())


def ns(date):
    return int(pd.Timestamp(date, tz="UTC").value)


def candidates():
    result = []
    for family, grid in config()["grids"].items():
        keys = list(grid)
        for values in itertools.product(*(grid[k] for k in keys)):
            p = dict(zip(keys, values, strict=True))
            suffix = "_".join(f"{k}{v}" for k, v in p.items())
            result.append({"id": f"{family}_{suffix}", "family": family, **p})
    return result


def source_hashes():
    paths = [ROOT / "config.json", ROOT / "PROTOCOL.md"]
    paths += sorted((ROOT / "edge_discovery").glob("*.py"))
    paths += sorted((ROOT / "tests").glob("*.py"))
    paths += [ROOT / "README.md", ROOT / "runtime-requirements.txt"]
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def assert_frozen():
    path = ROOT / "results" / "freeze.json"
    if not path.exists():
        raise RuntimeError("Holdout is sealed: freeze decisions before opening")
    frozen = json.loads(path.read_text())
    if source_hashes() != frozen["source_hashes"]:
        raise RuntimeError("Frozen source/config/protocol hashes changed")
    for name, expected in frozen["evidence_hashes"].items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(f"Frozen evidence changed: {name}")
    return frozen

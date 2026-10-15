"""Experiment paths, atomic artifacts, and tamper-evident sealed protocol."""

import hashlib
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DAY = 86400 * 10**9
HOUR = 3600 * 10**9
PRIOR = "3c669f91dd195266107a2f5b77c5c991565840a8"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    temporary.replace(path)


def config():
    return json.loads((ROOT / "config.json").read_text())


def ns(date):
    value = pd.Timestamp(date)
    return int(value.tz_localize("UTC").value if value.tz is None else value.value)


def source_hashes():
    paths = [ROOT / "config.json", ROOT / "PROTOCOL.md"]
    paths += sorted((ROOT / "adaptive").glob("*.py"))
    paths += sorted((ROOT / "tests").glob("*.py"))
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def assert_frozen():
    path = ROOT / "results" / "freeze.json"
    if not path.exists():
        raise RuntimeError("Holdout sealed: freeze protocol, policy and evidence first")
    frozen = json.loads(path.read_text())
    if source_hashes() != frozen["source_hashes"]:
        raise RuntimeError(
            "Frozen source/config/protocol changed; do not retune after holdout"
        )
    for name, expected in frozen["evidence_hashes"].items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(f"Frozen evidence changed: {name}")
    return frozen

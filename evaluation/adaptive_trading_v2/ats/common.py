"""Local experiment configuration and atomic, deterministic artifacts."""

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DAY = 86400 * 10**9
HOUR = 3600 * 10**9


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


@lru_cache(maxsize=1)
def config():
    return json.loads((ROOT / "config.json").read_text())


def ns(date):
    value = pd.Timestamp(date)
    return int(
        value.as_unit("ns").tz_localize("UTC").value
        if value.tz is None
        else value.as_unit("ns").value
    )


def specification_hashes():
    paths = [ROOT / "config.json", ROOT / "PROTOCOL.md", ROOT / "GATES.md"]
    return {p.name: digest(p) for p in paths}


def assert_specification():
    frozen = json.loads((ROOT / "results" / "predeclaration.json").read_text())
    if frozen["specification_hashes"] != specification_hashes():
        raise RuntimeError(
            "Predeclared specification changed; create a new experiment version"
        )

"""Finite, fingerprinted historical experiments; proposals never mutate candidates."""

import argparse
import concurrent.futures
import gzip
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone

import pandas as pd

from .common import ROOT, config, digest, write_json
from .profiles import library


def source_hashes():
    paths = [
        *sorted((ROOT / "alpha").glob("*.py")),
        ROOT / "config.json",
        ROOT / "PROTOCOL.md",
        ROOT / "GATES.md",
        ROOT / "FEATURES.md",
    ]
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def freeze():
    path = ROOT / "results/predeclaration.json"
    if path.exists():
        verify_freeze()
        return
    files = source_hashes()
    write_json(
        path,
        {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "files": files,
            "profiles": [p.definition() for p in library().values()],
            "budget": config()["research_budget"],
            "evidence_class": "RETROSPECTIVE_EVIDENCE",
        },
    )


def verify_freeze():
    frozen = json.loads((ROOT / "results/predeclaration.json").read_text())
    if frozen["files"] != source_hashes():
        raise RuntimeError("Frozen research source changed; no scoring permitted")


def prepare():
    from .data import load
    from .features import build
    from .ml import attach

    raw, rates = {}, {}
    for s in config()["symbols"]:
        raw[s], rates[s] = load(s, "retrospective", 5)
    frames, models = attach(build(raw, rates))
    records = []
    for s, f in frames.items():
        for kind, frame in (("features", f), ("bars", raw[s]), ("rates", rates[s])):
            path = ROOT / f"data/cache/{s}_{kind}.parquet"
            path.parent.mkdir(parents=True, exist_ok=True)
            frame.to_parquet(path, index=False)
            records.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "sha256": digest(path),
                    "rows": len(frame),
                }
            )
    write_json(ROOT / "data/feature_cache_manifest.json", records)
    write_json(ROOT / "results/ml_training.json", models)
    write_json(
        ROOT / "results/runtime_snapshot.json",
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "baseline_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "native_binary_sha256": digest(
                __import__(
                    "nautilus_trader._libnautilus", fromlist=["__file__"]
                ).__file__
            ),
            "packages": {
                p: importlib.metadata.version(p)
                for p in ("numpy", "pandas", "pyarrow", "pytest", "ruff")
            },
        },
    )
    print("Prepared audited features and chronological ML fits", flush=True)


def fingerprint():
    return hashlib.sha256(
        json.dumps(
            {
                "source": source_hashes(),
                "data": digest(ROOT / "data/feature_cache_manifest.json"),
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()


def group_run(job):
    from .features import aggregate
    from .native import run
    from .strategy import factory

    symbol, scenario = job
    verify_freeze()
    for record in json.loads((ROOT / "data/feature_cache_manifest.json").read_text()):
        if (
            record["path"].startswith(f"data/cache/{symbol}_")
            and digest(ROOT / record["path"]) != record["sha256"]
        ):
            raise RuntimeError("Feature cache changed")
    f = pd.read_parquet(ROOT / f"data/cache/{symbol}_features.parquet")
    raw = pd.read_parquet(ROOT / f"data/cache/{symbol}_bars.parquet")
    bars = aggregate(raw, 15)
    rates = pd.read_parquet(ROOT / f"data/cache/{symbol}_rates.parquet")
    features = {int(row["available_ns"]): row for row in f.to_dict("records")}
    stamp = fingerprint()
    count = 0
    for p in library().values():
        path = ROOT / f"results/runs/{p.id}_{symbol}_{scenario}.json.gz"
        if path.exists():
            with gzip.open(path, "rt") as stream:
                old = json.load(stream)
            if old["fingerprint"] != stamp:
                raise RuntimeError("Stale run; archive it before explicit rerun")
            continue
        candidate = {**p.definition(), "liquidate": True}
        result = run(
            candidate,
            symbol,
            "retrospective",
            bars,
            rates,
            scenario,
            strategy_factory=factory(features),
        )
        from .research import local_observation

        result["research_observation"] = local_observation(result)
        result["fingerprint"] = stamp
        result["hypothesis"] = p.definition()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        with gzip.open(temporary, "wt") as stream:
            json.dump(result, stream, allow_nan=False)
        temporary.replace(path)
        count += 1
        print(f"{symbol} {scenario} {p.id}: {len(result['trades'])} trades", flush=True)
    return count


def execute(workers):
    verify_freeze()
    budget = config()["research_budget"]
    jobs = [(s, c) for s in config()["symbols"] for c in config()["scenarios"]]
    assert len(library()) == budget["total_paths"]
    assert len(jobs) * len(library()) <= budget["maximum_native_runs"]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        for count in pool.map(group_run, jobs):
            print(f"Completed group: {count} new native runs", flush=True)


def load_runs():
    runs = {}
    for path in sorted((ROOT / "results/runs").glob("*.json.gz")):
        with gzip.open(path, "rt") as stream:
            r = json.load(stream)
        runs[(r["candidate"], r["symbol"], r["scenario"])] = r
    return runs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=("prepare", "freeze", "run", "report", "verify")
    )
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "freeze":
        freeze()
    elif args.action == "run":
        execute(args.workers)
    elif args.action == "report":
        from .report import generate

        generate()
    else:
        from .audit import verify

        verify()


if __name__ == "__main__":
    main()

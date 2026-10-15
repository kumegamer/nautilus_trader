"""Restore publisher-verified inputs and replay one exact frozen native experiment."""

import argparse
import gzip
import importlib.metadata
import json
import subprocess

from .common import ROOT, assert_frozen, digest, source_hashes, write_json
from .data import download_one, fetch
from .evidence import EvidenceProvider
from .native import run
from .runtime import factory, native_candidate
from .workflow import PRE, BuyHold, inputs, read_runs, run_path


def restore():
    assert_frozen()
    for manifest in sorted((ROOT / "data").glob("*manifest.json")):
        for row in json.loads(manifest.read_text()):
            downloaded = download_one((row["symbol"], row["month"], row["kind"]))
            if downloaded["sha256"] != row["publisher_sha256"]:
                raise RuntimeError("Publisher archive no longer matches frozen bytes")
    for manifest in sorted((ROOT / "data").glob("*repairs.json")):
        for row in json.loads(manifest.read_text()):
            path = ROOT / row["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_bytes(fetch(row["url"]))
            if digest(path) != row["publisher_sha256"]:
                raise RuntimeError("Repair archive no longer matches frozen bytes")
            path.with_suffix(".zip.CHECKSUM").write_text(
                row["publisher_sha256"] + "  " + path.name + "\n"
            )
    print("All frozen publisher bytes restored and verified")


def replay(profile, period, scenario, symbol):
    assert_frozen()
    bars, rates, features = inputs(period)[symbol]
    if profile == "ADAPTIVE":
        previous_state = None
        from .common import config

        periods = list(config()["periods"])
        index = periods.index(period)
        if index:
            with gzip.open(
                run_path(profile, symbol, periods[index - 1], scenario), "rt"
            ) as f:
                previous_state = json.load(f)["adaptive_state"]
        sf = factory(
            features,
            evidence_provider=EvidenceProvider(read_runs(PRE)),
            resume_state=previous_state,
        )
        candidate = native_candidate("TB48")
    elif profile == "BUY_HOLD":
        sf, candidate = BuyHold, native_candidate("TB48")
    else:
        sf, candidate = factory(features, fixed=profile), native_candidate(profile)
    candidate["id"] = profile
    actual = run(candidate, symbol, period, bars, rates, scenario, strategy_factory=sf)
    with gzip.open(run_path(profile, symbol, period, scenario), "rt") as f:
        expected = json.load(f)
    keys = [
        "trades",
        "fills",
        "daily",
        "native_balance",
        "reconciliation_difference",
        "signals",
        "size_skips",
    ]
    if profile == "ADAPTIVE":
        keys += ["decisions", "switches", "degradation", "research", "promotions"]
    differing = [key for key in keys if actual[key] != expected[key]]
    if differing:
        raise RuntimeError(f"Replay mismatch in {differing}")
    print(
        json.dumps(
            {
                "replayed": [profile, period, scenario, symbol],
                "exact_fields": keys,
                "status": "PASS",
            }
        )
    )


def provenance():
    import nautilus_trader._libnautilus as native

    from .common import config

    repo = ROOT.parents[1]
    lock_hashes = {
        str(p.relative_to(repo)): digest(p)
        for p in (
            repo / "Cargo.lock",
            repo / "rust-toolchain.toml",
            repo / "python/uv.lock",
        )
        if p.exists()
    }
    packages = {
        d.metadata["Name"]: d.version
        for d in importlib.metadata.distributions()
        if d.metadata.get("Name")
    }
    write_json(
        ROOT / "results" / "environment.json",
        {
            "packages": dict(sorted(packages.items())),
            "extension_sha256": digest(native.__file__),
            "upstream_locks": lock_hashes,
            "baseline_commit": config()["baseline_commit"],
            "research_commit": config()["prior_commit"],
            "source_hashes": source_hashes(),
        },
    )
    lines = [
        "# Runtime dependency snapshot; build Nautilus from the pinned repository baseline"
    ]
    for name in ("numpy", "pandas", "pyarrow", "pytest"):
        lines.append(f"{name}=={importlib.metadata.version(name)}")
    (ROOT / "runtime-requirements.txt").write_text("\n".join(lines) + "\n")
    destination = ROOT / "upstream_locks"
    destination.mkdir(exist_ok=True)
    for relative in lock_hashes:
        source = repo / relative
        (destination / source.name).write_bytes(source.read_bytes())
    # Read only; never updates the prior research or develop references
    checks = {}
    for ref in ("HEAD", "origin/develop", "origin/evaluation/edge-discovery-v1"):
        result = subprocess.run(
            ["git", "rev-parse", ref],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
        checks[ref] = result.stdout.strip()
    write_json(ROOT / "results/repository_refs.json", checks)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["restore", "replay", "provenance"])
    parser.add_argument("--profile", default="TB48_SHORT")
    parser.add_argument("--period", default="validation")
    parser.add_argument("--scenario", default="base")
    parser.add_argument("--symbol", default="BTCUSDT")
    args = parser.parse_args()
    if args.action == "restore":
        restore()
    elif args.action == "provenance":
        provenance()
    else:
        replay(args.profile, args.period, args.scenario, args.symbol)


if __name__ == "__main__":
    main()

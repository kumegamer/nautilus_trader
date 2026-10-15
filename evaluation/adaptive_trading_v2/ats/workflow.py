"""Bounded simulations and reproducible rolling validation, entirely under V2."""

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import multiprocessing
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from .common import ROOT, assert_specification, config, digest, ns, write_json
from .data import load
from .evidence import build_records
from .features import aggregate, build_features
from .native import run
from .profiles import BASE, POLICIES, library
from .regime import attach_regimes
from .runtime import candidate, factory

FEATURES = {}
BARS = {}
RATES = {}
EVIDENCE = []


def execution_hash():
    names = (
        "common",
        "data",
        "features",
        "regime",
        "profiles",
        "native",
        "runtime",
        "controller",
        "evidence",
        "metrics",
    )
    return hashlib.sha256(
        json.dumps(
            {n: digest(ROOT / "ats" / (n + ".py")) for n in names}, sort_keys=True
        ).encode()
        + (ROOT / "config.json").read_bytes()
    ).hexdigest()


def prepare():
    assert_specification()
    raw, rates = {}, {}
    for symbol in config()["symbols"]:
        raw[symbol], rates[symbol] = load(symbol, "retrospective", 5)
    frames = build_features(raw, rates)
    for symbol, frame in frames.items():
        frame, transitions = attach_regimes(frame)
        b = raw[symbol].set_index(pd.to_datetime(raw[symbol].t, unit="ns", utc=True))
        closes = b.close.resample("1D").last()
        volatility = closes.pct_change().rolling(30).std() * np.sqrt(365)
        weights = (
            (config()["passive"]["annual_volatility_target"] / volatility)
            .clip(upper=config()["passive"]["maximum_notional_fraction"])
            .fillna(0)
        )
        daily = pd.DataFrame(
            {
                "available_ns": (
                    weights.index.as_unit("ns").asi8 + 86400 * 10**9 - 10**6
                ),
                "passive_weight": weights.to_numpy(),
            }
        )
        frame = pd.merge_asof(frame, daily, on="available_ns", direction="backward")
        prefix_features = (
            "_close",
            "_atr",
            "_trend",
            "_high_prev",
            "_low_prev",
            "_exit_high",
            "_exit_low",
            "_compressed_recent",
            "_width_expanding",
        )
        columns = [
            c
            for c in frame
            if c
            in (
                "available_ns",
                "ready",
                "new_hour",
                "close",
                "vol_ratio_60",
                "passive_weight",
                "regime",
                "confidence",
                "transition_confidence",
                "candidate",
                "persistence_hours",
                "dwell_ns",
                "raw_regime",
                "raw_confidence",
            )
            or c[0].isdigit()
            and c.endswith(prefix_features)
        ]
        path = ROOT / "data" / "cache"
        path.mkdir(parents=True, exist_ok=True)
        frame[columns].to_parquet(path / f"{symbol}_features.parquet", index=False)
        aggregate(raw[symbol], 15).to_parquet(
            path / f"{symbol}_bars.parquet", index=False
        )
        rates[symbol].to_parquet(path / f"{symbol}_rates.parquet", index=False)
        write_json(ROOT / "results" / f"{symbol}_regime_transitions.json", transitions)
        print(
            f"Prepared {symbol}: {len(frame)} causal feature rows, {len(transitions)} stable transitions",
            flush=True,
        )
    write_json(
        ROOT / "data" / "feature_cache_manifest.json",
        {p.name: digest(p) for p in sorted((ROOT / "data/cache").glob("*.parquet"))},
    )


def initialize(symbol):
    frame = pd.read_parquet(ROOT / "data/cache" / f"{symbol}_features.parquet")
    FEATURES[symbol] = {int(f["available_ns"]): f for f in frame.to_dict("records")}
    BARS[symbol] = pd.read_parquet(ROOT / "data/cache" / f"{symbol}_bars.parquet")
    RATES[symbol] = pd.read_parquet(ROOT / "data/cache" / f"{symbol}_rates.parquet")


def run_path(profile, policy, scenario, symbol):
    return ROOT / "results/runs" / f"{profile}__{policy}__{scenario}__{symbol}.json.gz"


def read_run(profile, policy, scenario, symbol):
    return json.loads(
        gzip.decompress(run_path(profile, policy, scenario, symbol).read_bytes())
    )


def simulate(job):
    profile, policy, scenario, symbol = job
    if symbol not in FEATURES:
        initialize(symbol)
    fingerprint = execution_hash()
    path = run_path(*job)
    if path.exists():
        saved = read_run(*job)
        if saved.get("execution_hash") == fingerprint:
            return [*job, len(saved["trades"]), "CACHED"]
    result = run(
        candidate(profile, policy),
        symbol,
        "retrospective",
        BARS[symbol],
        RATES[symbol],
        scenario,
        factory(FEATURES[symbol], EVIDENCE),
    )
    result["execution_hash"] = fingerprint
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        gzip.compress(
            json.dumps(result, sort_keys=True, allow_nan=False).encode(), mtime=0
        )
    )
    return [*job, len(result["trades"]), result["native_balance"]]


def jobs_static():
    for profile in library():
        if profile == "NO_TRADE":
            continue
        policies = POLICIES if profile in {p.id for p in BASE} else ("ENTRY_ONLY",)
        for policy in policies:
            for scenario in config()["scenarios"]:
                for symbol in config()["symbols"]:
                    yield profile, policy, scenario, symbol


def execute(jobs, workers):
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=workers, mp_context=multiprocessing.get_context("fork")
    ) as pool:
        for value in pool.map(simulate, jobs, chunksize=1):
            print(json.dumps(value), flush=True)


def evidence():
    store = {}
    for profile in library():
        if profile == "NO_TRADE":
            continue
        for scenario in config()["scenarios"]:
            store[(profile, "ENTRY_ONLY", scenario)] = [
                read_run(profile, "ENTRY_ONLY", scenario, s)
                for s in config()["symbols"]
            ]
    timestamps = [
        ns(t) for t in pd.date_range("2025-01-01", "2026-10-01", freq="MS", tz="UTC")
    ]
    records = build_records(store, timestamps)
    write_json(ROOT / "results/eligibility.json", records)
    print(
        f"Rolling gate records: {len(records)}; passes: {sum(r['eligible'] for r in records)}",
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare", "static", "evidence", "adaptive"))
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    assert_specification()
    if args.stage == "prepare":
        prepare()
    elif args.stage == "static":
        write_json(
            ROOT / "results/scoring_started.json",
            {
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "execution_hash": execution_hash(),
                "trials": 36,
                "scenarios": 3,
            },
        )
        execute(list(jobs_static()), args.workers)
    elif args.stage == "evidence":
        evidence()
    else:
        EVIDENCE[:] = json.loads((ROOT / "results/eligibility.json").read_text())
        execute(
            [
                (p, "ENTRY_ONLY", scenario, s)
                for p in ("ADAPTIVE", "PASSIVE", "NO_TRADE")
                for scenario in config()["scenarios"]
                for s in config()["symbols"]
            ],
            args.workers,
        )


if __name__ == "__main__":
    main()

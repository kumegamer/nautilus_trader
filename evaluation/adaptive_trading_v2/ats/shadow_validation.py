"""Monthly revalidation of frozen profiles from matured recorded market data.

Run separately from the minute collector. Completion time, rather than historical
month boundary, controls when its gate records become available to the controller.
"""

import json
import time

import pandas as pd

from .common import DAY, ROOT, config, digest, ns
from .data import read_klines
from .evidence import evaluate
from .features import aggregate, build_features
from .native import run
from .profiles import BASE, library
from .regime import attach_regimes
from .runtime import candidate, factory
from .shadow import assert_freeze


def validate_month(journal, boundary=None):
    assert_freeze()
    for record in json.loads((ROOT / "data/historical_manifest.json").read_text()):
        if digest(ROOT / record["path"]) != record["sha256"]:
            raise RuntimeError("Consumed archive differs from frozen expected input")
    cache_manifest = json.loads((ROOT / "data/feature_cache_manifest.json").read_text())
    for symbol in config()["symbols"]:
        name = f"{symbol}_rates.parquet"
        if digest(ROOT / "data/cache" / name) != cache_manifest[name]:
            raise RuntimeError(
                "Historical native funding cache differs from frozen input"
            )
    now = time.time_ns()
    month = pd.Timestamp(now, unit="ns", tz="UTC").normalize().replace(day=1)
    if boundary is not None:
        month = pd.Timestamp(boundary, tz="UTC")
    timestamp = int(month.value)
    if timestamp > now:
        raise ValueError("Cannot validate future monthly boundary")
    if journal.get("prospective_start_ns") is None:
        raise ValueError("Collect public market data before validation")
    execution_start = ns(config()["periods"]["retrospective"][0])
    consumed_end = ns(config()["periods"]["retrospective"][1])
    if timestamp < consumed_end:
        raise ValueError("Cannot replace frozen historical monthly evidence")
    end = timestamp - config()["validation"]["embargo_days"] * DAY
    # Reproduce the original continuous path; evaluate() purges to the rolling
    # window. Restarting flat at that window would change occupancy and trades.
    warm = execution_start - config()["warmup_days"] * DAY
    store = {}
    hashes = {}
    for symbol in config()["symbols"]:
        prior = []
        last_historical = pd.Timestamp("2026-09-01", tz="UTC")
        for m in pd.date_range(
            pd.Timestamp(warm, unit="ns", tz="UTC").normalize().replace(day=1),
            min(last_historical, pd.Timestamp(end, unit="ns", tz="UTC")),
            freq="MS",
        ):
            frame = read_klines(symbol, m.strftime("%Y-%m")).iloc[:, :6].copy()
            frame.columns = ["t", "open", "high", "low", "close", "volume"]
            frame = frame.astype(float)
            frame["t"] = frame.t.astype("int64") * 10**6
            prior.append(frame)
        events = journal.events("bar5m", symbol)
        forward = pd.DataFrame(
            [
                [e["event_ns"], *map(float, e["payload"][1:6])]
                for e in events
                if e["event_ns"] >= consumed_end
            ],
            columns=["t", "open", "high", "low", "close", "volume"],
        )
        raw = pd.concat([*prior, forward], ignore_index=True)
        raw = (
            raw[(raw.t >= warm) & (raw.t < end)].sort_values("t").reset_index(drop=True)
        )
        raw = raw.astype(float)
        raw["t"] = raw.t.astype("int64")
        if (
            len(raw) != (end - warm) // (300 * 10**9)
            or raw.t.duplicated().any()
            or (raw.t.diff().dropna() != 300 * 10**9).any()
        ):
            raise RuntimeError(
                "Complete matured training bars are required before monthly validation"
            )
        old_rates = pd.read_parquet(ROOT / "data/cache" / f"{symbol}_rates.parquet")
        new_rates = pd.DataFrame(
            [
                {
                    "t": e["event_ns"],
                    "original_ms": e["event_ns"] // 10**6,
                    "rate": float(e["payload"]["fundingRate"]),
                    "mark": float(e["payload"]["markPrice"]),
                    "interval": 8,
                }
                for e in journal.events("funding", symbol)
                if e["event_ns"] >= consumed_end
            ]
        )
        rates = pd.concat([old_rates, new_rates], ignore_index=True)
        rates = rates[(rates.t >= execution_start) & (rates.t < end)].sort_values("t")
        if (
            rates.t.duplicated().any()
            or (rates.t.diff().dropna() > 8 * 3600 * 10**9).any()
            or len(rates) < (end - execution_start) / DAY * 2.9
        ):
            raise RuntimeError(
                "Complete matured funding coverage required before monthly validation"
            )
        features = build_features({symbol: raw}, {symbol: rates})[symbol]
        features, _ = attach_regimes(features)
        mapping = {int(f["available_ns"]): f for f in features.to_dict("records")}
        bars = aggregate(raw, 15)
        hashes[symbol] = {
            "bars_sha256": __import__("hashlib")
            .sha256(raw.to_json().encode())
            .hexdigest(),
            "rates_sha256": __import__("hashlib")
            .sha256(rates.to_json().encode())
            .hexdigest(),
        }
        for profile in library():
            if profile == "NO_TRADE":
                continue
            for scenario in config()["scenarios"]:
                result = run(
                    candidate(profile, liquidate=False),
                    symbol,
                    "retrospective",
                    bars,
                    rates,
                    scenario,
                    factory(mapping),
                    start_ns=execution_start,
                    end_ns=end,
                )
                store.setdefault((profile, "ENTRY_ONLY", scenario), []).append(result)
                print(f"Validated path {symbol} {profile} {scenario}", flush=True)
    records = [evaluate(p.id, timestamp, store) for p in BASE]
    completed = time.time_ns()
    for record in records:
        record["requested_boundary_ns"] = record["timestamp"]
        record["timestamp"] = completed
        record["market_input_hashes"] = hashes
        record["freeze_sha256"] = digest(ROOT / "prospective_freeze.json")
        journal.append(
            "eligibility",
            record["profile"],
            completed,
            completed,
            record,
            "PROSPECTIVE_EVIDENCE_WITH_CONSUMED_TRAINING",
        )
    print(
        json.dumps(
            {
                "completed_ns": completed,
                "eligible": [r["profile"] for r in records if r["eligible"]],
            }
        )
    )
    return records

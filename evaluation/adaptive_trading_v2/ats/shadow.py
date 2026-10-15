"""Public GET-only Binance collector with immutable journal and deterministic native replay.

No trading client or key is imported. Persistence uses SQLite transactions and replay
rather than serializing native engine internals. Each poll can run from a scheduler.
"""

import argparse
import hashlib
import itertools
import json
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

from .common import DAY, ROOT, config, digest, ns, write_json
from .features import aggregate, build_features
from .native import run
from .regime import attach_regimes
from .runtime import AdaptiveStrategy, candidate

BASE = "https://fapi.binance.com"
ENDPOINTS = {
    "/fapi/v1/time",
    "/fapi/v1/klines",
    "/fapi/v1/ticker/bookTicker",
    "/fapi/v1/fundingRate",
    "/fapi/v1/premiumIndex",
}


class ShadowStrategy(AdaptiveStrategy):
    """Recheck entry permission at observed execution after a public-data outage."""

    def submit_order(self, order, **kwargs):
        self.hypothetical_orders.append(
            {
                "timestamp": self.clock.timestamp_ns(),
                "client_order_id": str(order.client_order_id),
                "instrument_id": str(order.instrument_id),
                "side": order.side.name,
                "type": order.order_type.name,
                "quantity": str(order.quantity),
                "reduce_only": order.is_reduce_only,
            }
        )
        super().submit_order(order, **kwargs)

    def on_bar(self, bar):
        self.latest_features = self.features[bar.ts_event]
        super().on_bar(bar)

    def on_quote(self, quote):
        if self.pending and self.pending["action"] == "entry":
            p = self.profiles[self.pending["profile"]]
            f = self.latest_features
            record = self.controller.provider.at(quote.ts_event).get(p.id)
            allowed = (
                record is not None
                and record["eligible"]
                and f["regime"] in p.compatible_regimes
                and f["confidence"] >= config()["regime"]["entry_confidence"]
                and quote.ts_event >= self.controller.disabled_until
            )
            if not allowed:
                self.pending = None
        super().on_quote(quote)


def shadow_factory(features, evidence, orders):
    def create(inst, parameters, start, end, references):
        strategy = ShadowStrategy(
            inst, parameters, start, end, references, features, evidence
        )
        strategy.hypothetical_orders = orders
        return strategy

    return create


def public_get(endpoint, params=None):
    if endpoint not in ENDPOINTS:
        raise ValueError(
            "Only explicitly allowed public market-data endpoints are supported"
        )
    query = urllib.parse.urlencode(params or {})
    request = urllib.request.Request(
        BASE + endpoint + ("?" + query if query else ""), method="GET"
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def assert_freeze():
    freeze = json.loads((ROOT / "prospective_freeze.json").read_text())
    for name, expected in freeze["files"].items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(
                f"Frozen V2 bundle changed: {name}; create a new version"
            )
    return freeze


class Journal:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / "market.sqlite", timeout=30)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                kind TEXT NOT NULL, symbol TEXT NOT NULL, event_ns INTEGER NOT NULL,
                observed_ns INTEGER NOT NULL, payload TEXT NOT NULL, sha256 TEXT NOT NULL,
                evidence_class TEXT NOT NULL,
                PRIMARY KEY(kind, symbol, event_ns)
            );
        """)

    def get(self, key):
        row = self.db.execute(
            "SELECT value FROM metadata WHERE key=?", (key,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def set_once(self, key, value):
        encoded = json.dumps(value, sort_keys=True)
        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO metadata VALUES (?,?)", (key, encoded)
            )
        if self.get(key) != value:
            raise RuntimeError(f"Immutable journal metadata mismatch: {key}")

    def append(self, kind, symbol, event_ns, observed_ns, payload, evidence_class):
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        checksum = hashlib.sha256(encoded.encode()).hexdigest()
        old = self.db.execute(
            "SELECT sha256 FROM events WHERE kind=? AND symbol=? AND event_ns=?",
            (kind, symbol, event_ns),
        ).fetchone()
        if old:
            if old[0] != checksum:
                raise RuntimeError(
                    "Previously recorded market event revised; original preserved"
                )
            return False
        with self.db:
            self.db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?)",
                (
                    kind,
                    symbol,
                    event_ns,
                    observed_ns,
                    encoded,
                    checksum,
                    evidence_class,
                ),
            )
        return True

    def events(self, kind, symbol):
        rows = self.db.execute(
            "SELECT event_ns,observed_ns,payload,sha256,evidence_class FROM events WHERE kind=? AND symbol=? ORDER BY event_ns",
            (kind, symbol),
        ).fetchall()
        result = []
        for t, observed, payload, checksum, label in rows:
            if hashlib.sha256(payload.encode()).hexdigest() != checksum:
                raise RuntimeError("Market journal payload checksum mismatch")
            result.append(
                {
                    "event_ns": t,
                    "observed_ns": observed,
                    "payload": json.loads(payload),
                    "evidence_class": label,
                }
            )
        return result

    def close(self):
        self.db.close()


def collect(journal):
    freeze = assert_freeze()
    freeze_hash = digest(ROOT / "prospective_freeze.json")
    journal.set_once("freeze_sha256", freeze_hash)
    server_ms = int(public_get("/fapi/v1/time")["serverTime"])
    if journal.get("prospective_start_ns") is None:
        journal.set_once("prospective_start_ns", max(time.time_ns(), server_ms * 10**6))
        journal.set_once("created_utc", datetime.now(timezone.utc).isoformat())
    start = journal.get("prospective_start_ns")
    consumed_end = ns(
        config().get("periods", {}).get("retrospective", [None, "2026-10-01"])[1]
    )
    bootstrap_ms = min(
        (server_ms - config()["warmup_days"] * 86400000) // 300000 * 300000,
        consumed_end // 10**6,
    )
    for symbol in config()["symbols"]:
        existing = journal.events("bar5m", symbol)
        cursor = (
            existing[-1]["event_ns"] // 10**6 + 300000 if existing else bootstrap_ms
        )
        for previous, current in itertools.pairwise(existing):
            if current["event_ns"] - previous["event_ns"] != 300 * 10**9:
                cursor = previous["event_ns"] // 10**6 + 300000
                break
        while cursor + 300000 <= server_ms:
            rows = public_get(
                "/fapi/v1/klines",
                {
                    "symbol": symbol,
                    "interval": "5m",
                    "startTime": cursor,
                    "endTime": server_ms - 1,
                    "limit": 1500,
                },
            )
            observed = time.time_ns()
            closed = [r for r in rows if int(r[6]) < server_ms]
            if not closed:
                raise RuntimeError(
                    "Expected closed public bars are unavailable; retry collection"
                )
            expected = cursor
            for r in closed:
                if int(r[0]) != expected:
                    raise RuntimeError(
                        "Public kline gap blocks execution; retry missing interval"
                    )
                expected += 300000
                t = int(r[0]) * 10**6
                label = (
                    "WARMUP_ONLY"
                    if (int(r[6]) + 1) * 10**6 <= start
                    else "PROSPECTIVE_EVIDENCE"
                )
                journal.append("bar5m", symbol, t, observed, r[:7], label)
            next_cursor = int(closed[-1][0]) + 300000
            if next_cursor <= cursor:
                raise RuntimeError("Public market cursor failed to advance")
            cursor = next_cursor
        quote = public_get("/fapi/v1/ticker/bookTicker", {"symbol": symbol})
        bid, ask = Decimal(quote["bidPrice"]), Decimal(quote["askPrice"])
        if (
            quote["symbol"] != symbol
            or not bid.is_finite()
            or not ask.is_finite()
            or bid <= 0
            or ask < bid
            or Decimal(quote["bidQty"]) <= 0
            or Decimal(quote["askQty"]) <= 0
        ):
            raise RuntimeError("Invalid public quote blocks hypothetical execution")
        observed = time.time_ns()
        journal.append(
            "quote",
            symbol,
            observed,
            observed,
            {
                "bid": quote["bidPrice"],
                "ask": quote["askPrice"],
                "bid_qty": quote["bidQty"],
                "ask_qty": quote["askQty"],
                "venue_ms": quote.get("time"),
            },
            "PROSPECTIVE_EVIDENCE",
        )
        funding_events = journal.events("funding", symbol)
        cursor = (
            funding_events[-1]["event_ns"] // 10**6 + 1
            if funding_events
            else bootstrap_ms
        )
        while cursor <= server_ms:
            rates = public_get(
                "/fapi/v1/fundingRate",
                {
                    "symbol": symbol,
                    "startTime": cursor,
                    "endTime": server_ms,
                    "limit": 1000,
                },
            )
            observed = time.time_ns()
            for r in rates:
                journal.append(
                    "funding",
                    symbol,
                    int(r["fundingTime"]) * 10**6,
                    observed,
                    r,
                    "WARMUP_ONLY"
                    if int(r["fundingTime"]) * 10**6 < start
                    else "PROSPECTIVE_EVIDENCE",
                )
            if not rates:
                break
            next_cursor = int(rates[-1]["fundingTime"]) + 1
            if next_cursor <= cursor:
                raise RuntimeError("Public funding cursor failed to advance")
            cursor = next_cursor
            if len(rates) < 1000:
                break
    return freeze


def replay(journal):
    assert_freeze()
    if journal.get("freeze_sha256") != digest(ROOT / "prospective_freeze.json"):
        raise RuntimeError("Journal belongs to a different frozen version")
    start = journal.get("prospective_start_ns")
    if start is None:
        raise RuntimeError("Collect public market data first")
    evidence = json.loads((ROOT / "results/eligibility.json").read_text())
    from .profiles import BASE

    for p in BASE:
        for event in journal.events("eligibility", p.id):
            record = event["payload"]
            if (
                record["freeze_sha256"] != journal.get("freeze_sha256")
                or record["timestamp"] != event["observed_ns"]
                or record["end_ns"] >= record["timestamp"]
            ):
                raise RuntimeError("Invalid monthly eligibility provenance")
            evidence.append(record)
    results = {}
    for symbol in config()["symbols"]:
        warm_start = (
            (start - config()["warmup_days"] * DAY) // (300 * 10**9) * (300 * 10**9)
        )
        events = [
            e for e in journal.events("bar5m", symbol) if e["event_ns"] >= warm_start
        ]
        if not events:
            continue
        raw = pd.DataFrame(
            [[e["event_ns"], *map(float, e["payload"][1:6])] for e in events],
            columns=["t", "open", "high", "low", "close", "volume"],
        )
        if (raw.t.diff().dropna() != 300 * 10**9).any():
            raise RuntimeError(
                "Public-data gap blocks shadow replay; collect missing bars first"
            )
        if (
            not np.isfinite(raw.to_numpy()).all()
            or (raw.iloc[:, 1:5] <= 0).any().any()
            or (raw.volume < 0).any()
            or (raw.high < raw[["open", "close", "low"]].max(axis=1)).any()
            or (raw.low > raw[["open", "close", "high"]].min(axis=1)).any()
        ):
            raise RuntimeError("Invalid observed OHLCV blocks shadow execution")
        funding = [
            e for e in journal.events("funding", symbol) if e["event_ns"] >= start
        ]
        feature_rates = pd.DataFrame(
            {"original_ms": [int(raw.t.iloc[0] // 10**6)], "rate": [0.0]}
        )
        frame = build_features({symbol: raw}, {symbol: feature_rates})[symbol]
        bars = aggregate(raw, 15)
        observations = {e["event_ns"]: e for e in events}
        availability = []
        last = 0
        for t in bars.t:
            end = int(t + 900 * 10**9 - 10**6)
            source = observations[int(t + 600 * 10**9)]
            observed = (
                end
                if source["evidence_class"] == "WARMUP_ONLY"
                else max(end, source["observed_ns"])
            )
            observed = max(observed, last + 1)
            availability.append(observed)
            last = observed
        frame["day_end"] = (frame.available_ns + 10**6) % DAY == 0
        frame["available_ns"] = availability
        bars["available_ns"] = availability
        frame, transitions = attach_regimes(frame)
        features = {int(f["available_ns"]): f for f in frame.to_dict("records")}
        quotes = [
            {
                "observed_ns": e["observed_ns"],
                "bid": e["payload"]["bid"],
                "ask": e["payload"]["ask"],
                "bid_qty": 1000000,
                "ask_qty": 1000000,
            }
            for e in journal.events("quote", symbol)
        ]
        rates = pd.DataFrame(
            [
                {
                    "t": e["observed_ns"],
                    "mark": float(e["payload"]["markPrice"]),
                    "rate": float(e["payload"]["fundingRate"]),
                    "interval": 8,
                }
                for e in funding
            ],
            columns=["t", "mark", "rate", "interval"],
        )
        end = max([*availability, *[q["observed_ns"] for q in quotes]]) + 1
        orders = []
        result = run(
            candidate("ADAPTIVE", liquidate=False),
            symbol,
            "retrospective",
            bars,
            rates,
            strategy_factory=shadow_factory(features, evidence, orders),
            start_ns=start,
            end_ns=end,
            public_quotes=quotes,
        )
        result["hypothetical_orders"] = orders
        result["regime_transitions"] = [
            t for t in transitions if t["timestamp"] >= start
        ]
        result["evidence_class"] = "PROSPECTIVE_EVIDENCE"
        result["funding_timing"] = (
            "Applied when observed; settlement latency explicitly retained in journal"
        )
        write_json(journal.directory / f"{symbol}_shadow.json", result)
        results[symbol] = result
    write_json(
        journal.directory / "checkpoint.json",
        {
            "freeze_sha256": journal.get("freeze_sha256"),
            "prospective_start_ns": start,
            "replay_sha256": hashlib.sha256(
                json.dumps(results, sort_keys=True).encode()
            ).hexdigest(),
            "symbols": sorted(results),
            "resume": "replay immutable journal; positions never forcibly liquidated on restart",
        },
    )
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("poll", "replay", "verify", "validate"))
    parser.add_argument("--state", type=Path, default=ROOT / "shadow_state")
    args = parser.parse_args()
    assert_freeze()
    if args.action == "verify":
        print("Frozen V2 checksums verified; no execution adapter exists")
        return
    journal = Journal(args.state)
    try:
        if args.action == "validate":
            from .shadow_validation import validate_month

            validate_month(journal)
            return
        if args.action == "poll":
            collect(journal)
        result = replay(journal)
        print(
            json.dumps(
                {
                    s: {
                        "trades": len(r["trades"]),
                        "open_position": bool(r["open_position"]),
                        "hypothetical_fills": len(r["fills"]),
                    }
                    for s, r in result.items()
                },
                sort_keys=True,
            )
        )
    finally:
        journal.close()


if __name__ == "__main__":
    main()

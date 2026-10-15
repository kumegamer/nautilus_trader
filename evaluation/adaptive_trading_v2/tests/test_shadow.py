"""Restart, immutable journal and public-endpoint boundary checks."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ats.shadow import Journal, public_get


def test_journal_restart_deduplication_and_revision_rejection(tmp_path):
    journal = Journal(tmp_path)
    journal.set_once("version", "v2")
    assert journal.append(
        "quote", "BTCUSDT", 100, 101, {"bid": "10"}, "PROSPECTIVE_EVIDENCE"
    )
    journal.close()
    resumed = Journal(tmp_path)
    assert resumed.get("version") == "v2"
    assert not resumed.append(
        "quote", "BTCUSDT", 100, 200, {"bid": "10"}, "PROSPECTIVE_EVIDENCE"
    )
    with pytest.raises(RuntimeError, match="revised"):
        resumed.append(
            "quote", "BTCUSDT", 100, 201, {"bid": "11"}, "PROSPECTIVE_EVIDENCE"
        )
    assert resumed.events("quote", "BTCUSDT")[0]["payload"] == {"bid": "10"}
    resumed.db.execute("UPDATE events SET payload=?", (json.dumps({"bid": "12"}),))
    resumed.db.commit()
    with pytest.raises(RuntimeError, match="checksum"):
        resumed.events("quote", "BTCUSDT")
    resumed.close()


def test_order_endpoints_cannot_be_requested():
    with pytest.raises(ValueError, match="public"):
        public_get("/fapi/v1/order", {"symbol": "BTCUSDT"})


def test_monthly_eligibility_expiry_blocks_stale_admissions():
    from ats.evidence import EvidenceProvider

    provider = EvidenceProvider(
        [
            {
                "profile": "TB_SHORT",
                "timestamp": 100,
                "end_ns": 90,
                "valid_until_ns": 200,
                "eligible": True,
            }
        ]
    )
    assert provider.at(199)
    assert not provider.at(200)


def test_native_shadow_replay_preserves_open_position_and_prior_fills(
    tmp_path, monkeypatch
):
    import hashlib

    from ats import shadow
    from ats.common import ns

    root = tmp_path / "bundle"
    (root / "results").mkdir(parents=True)
    (root / "prospective_freeze.json").write_text("{}")
    freeze_hash = hashlib.sha256(b"{}").hexdigest()
    start = ns("2025-01-01")
    record = {
        "profile": "TB_LONG",
        "timestamp": start,
        "end_ns": start - 86400 * 10**9,
        "valid_until_ns": ns("2025-02-01"),
        "eligible": True,
    }
    (root / "results/eligibility.json").write_text(json.dumps([record]))
    monkeypatch.setattr(shadow, "ROOT", root)
    monkeypatch.setattr(shadow, "assert_freeze", dict)
    directory = tmp_path / "state"
    journal = Journal(directory)
    journal.set_once("freeze_sha256", freeze_hash)
    journal.set_once("prospective_start_ns", start)
    initial = start - 42 * 86400 * 10**9

    def append_bars(a, b):
        for i in range(a, b):
            t = initial + i * 300 * 10**9
            price = 100 + i * 0.01
            close = t + 300 * 10**9 - 10**6
            observed = close + 2 * 10**6
            label = "WARMUP_ONLY" if close < start else "PROSPECTIVE_EVIDENCE"
            journal.append(
                "bar5m",
                "BTCUSDT",
                t,
                observed,
                [
                    t // 10**6,
                    str(price),
                    str(price + 0.02),
                    str(price - 0.02),
                    str(price + 0.015),
                    "100000",
                    close // 10**6,
                ],
                label,
            )
            if close >= start and (i + 1) % 3 == 0:
                quote_t = observed + 10**6
                journal.append(
                    "quote",
                    "BTCUSDT",
                    quote_t,
                    quote_t,
                    {
                        "bid": str(price),
                        "ask": str(price + 0.1),
                        "bid_qty": "1000",
                        "ask_qty": "1000",
                    },
                    "PROSPECTIVE_EVIDENCE",
                )

    append_bars(0, 12120)
    first = shadow.replay(journal)["BTCUSDT"]
    assert first["open_position"] is not None
    assert first["fills"]
    assert len(first["hypothetical_orders"]) == len(first["fills"])
    assert first["hypothetical_orders"][0]["type"] == "MARKET"
    assert not first["hypothetical_orders"][0]["reduce_only"]
    assert all(f["signal_ns"] < f["ts_ns"] for f in first["fills"])
    journal.close()
    journal = Journal(directory)
    repeated = shadow.replay(journal)["BTCUSDT"]
    assert repeated == first
    append_bars(12120, 12144)
    extended = shadow.replay(journal)["BTCUSDT"]
    cutoff = first["fills"][-1]["ts_ns"]
    assert [f for f in extended["fills"] if f["ts_ns"] <= cutoff] == first["fills"]
    assert extended["open_position"]["entry_ns"] == first["open_position"]["entry_ns"]
    journal.close()


def test_prospective_freeze_detects_source_tampering_on_copy(tmp_path, monkeypatch):
    import hashlib

    from ats import shadow

    script = tmp_path / "rules.py"
    script.write_text("threshold = 1\n")
    (tmp_path / "prospective_freeze.json").write_text(
        json.dumps(
            {"files": {"rules.py": hashlib.sha256(script.read_bytes()).hexdigest()}}
        )
    )
    monkeypatch.setattr(shadow, "ROOT", tmp_path)
    assert shadow.assert_freeze()
    script.write_text("threshold = 2\n")
    with pytest.raises(RuntimeError, match="Frozen V2 bundle changed"):
        shadow.assert_freeze()


@pytest.mark.parametrize("publisher_gap", [False, True])
def test_collector_retries_earliest_gap_and_never_executes_past_missing_bars(
    tmp_path, monkeypatch, publisher_gap
):
    import hashlib

    from ats import shadow

    root = tmp_path / "bundle"
    root.mkdir()
    (root / "prospective_freeze.json").write_text("{}")
    monkeypatch.setattr(shadow, "ROOT", root)
    monkeypatch.setattr(shadow, "assert_freeze", dict)
    monkeypatch.setattr(
        shadow, "config", lambda: {"symbols": ["BTCUSDT"], "warmup_days": 1}
    )
    initial = 1704067200000
    now = (initial + 900000) * 10**6 + 1000000000
    monkeypatch.setattr(shadow.time, "time_ns", lambda: now)
    journal = Journal(tmp_path / "state")
    journal.set_once("freeze_sha256", hashlib.sha256(b"{}").hexdigest())
    journal.set_once("prospective_start_ns", initial * 10**6)

    def bar(t):
        return [t, "100", "101", "99", "100", "1000", t + 299999]

    for t in (initial, initial + 600000):
        journal.append(
            "bar5m", "BTCUSDT", t * 10**6, now - 1, bar(t), "PROSPECTIVE_EVIDENCE"
        )
    requested = []

    def response(endpoint, params=None):
        if endpoint == "/fapi/v1/time":
            return {"serverTime": initial + 900000}
        if endpoint == "/fapi/v1/klines":
            requested.append(params["startTime"])
            return (
                [bar(initial + 600000)]
                if publisher_gap
                else [bar(initial + 300000), bar(initial + 600000)]
            )
        if endpoint == "/fapi/v1/ticker/bookTicker":
            return {
                "symbol": "BTCUSDT",
                "bidPrice": "100",
                "askPrice": "101",
                "bidQty": "1",
                "askQty": "1",
            }
        return []

    monkeypatch.setattr(shadow, "public_get", response)
    if publisher_gap:
        with pytest.raises(RuntimeError, match="kline gap"):
            shadow.collect(journal)
        assert journal.events("quote", "BTCUSDT") == []
    else:
        shadow.collect(journal)
        assert len(journal.events("bar5m", "BTCUSDT")) == 3
    assert requested[0] == initial + 300000
    journal.close()


def test_late_deployment_bootstraps_consumed_gap_and_paginates_funding(
    tmp_path, monkeypatch
):
    from ats import shadow
    from ats.common import ns

    root = tmp_path / "bundle"
    root.mkdir()
    (root / "prospective_freeze.json").write_text("{}")
    monkeypatch.setattr(shadow, "ROOT", root)
    monkeypatch.setattr(shadow, "assert_freeze", dict)
    boundary = ns("2026-10-01")
    server_ms = ns("2027-12-01") // 10**6
    observed = server_ms * 10**6 + 1
    monkeypatch.setattr(shadow.time, "time_ns", lambda: observed)
    journal = Journal(tmp_path / "state")
    requests = []

    def response(endpoint, params=None):
        if endpoint == "/fapi/v1/time":
            return {"serverTime": server_ms}
        if endpoint == "/fapi/v1/klines":
            requests.append((endpoint, params["startTime"]))
            # Stop after proving the first requested backfill interval.
            raise RuntimeError("fixture backfill boundary")
        if endpoint == "/fapi/v1/ticker/bookTicker":
            return {
                "symbol": params["symbol"],
                "bidPrice": "100",
                "askPrice": "101",
                "bidQty": "1",
                "askQty": "1",
            }
        if endpoint == "/fapi/v1/fundingRate":
            requests.append((endpoint, params["startTime"]))
            first = boundary // 10**6
            if params["startTime"] == first:
                return [{"fundingTime": first + i} for i in range(1000)]
            return [{"fundingTime": first + 1000}]
        raise AssertionError(endpoint)

    monkeypatch.setattr(shadow, "public_get", response)
    with pytest.raises(RuntimeError, match="fixture backfill"):
        shadow.collect(journal)
    assert requests[0] == ("/fapi/v1/klines", boundary // 10**6)
    # Existing complete candles allow the funding-pagination path to run.
    monkeypatch.setattr(
        shadow, "config", lambda: {"symbols": ["BTCUSDT"], "warmup_days": 40}
    )
    journal.append(
        "bar5m",
        "BTCUSDT",
        (server_ms - 300000) * 10**6,
        observed,
        [server_ms - 300000, "100", "101", "99", "100", "1", server_ms - 1],
        "WARMUP_ONLY",
    )
    shadow.collect(journal)
    funding = journal.events("funding", "BTCUSDT")
    assert len(funding) == 1001
    assert requests[-1] == ("/fapi/v1/fundingRate", boundary // 10**6 + 1000)
    assert all(e["evidence_class"] == "WARMUP_ONLY" for e in funding)
    journal.close()

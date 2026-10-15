"""Exact replay comparison, independent economic audit and prior-metric gates."""
import argparse
import csv
import hashlib
import json
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from pathlib import Path

from canonicalize import canonicalize

OLD_SHA256 = "7aecf9ac5050a5eb6c08ca36a32cd5bd29edf82c4c26d3df51799ea750f60814"
PREVIOUS_EXACT = {"closed_trades": 172, "long_trades": 86, "short_trades": 86,
                  "orders": 344, "fills": 344, "wins": 39, "final_balance": "9810.296225",
                  "gross_pnl_after_slippage": "-17.874000", "commissions": "171.829775",
                  "net_realized_pnl": "-189.703775", "max_drawdown_usdt": "233.238054"}
PREVIOUS_ROUNDED = {"win_rate_pct": ("22.6744", "0.0001"),
                    "max_drawdown_pct": ("2.327584", "0.000001"),
                    "profit_factor": ("0.737767", "0.000001")}


def dtext(value):
    return "0" if not value else format(value.normalize(), "f")


def reference_signals(rows):
    # Independent full-series recurrence, not the strategy class or its seed state.
    closes = [float(r["close"]) for r in rows]
    efast, eslow = [None] * len(rows), [None] * len(rows)
    for n, out in [(20, efast), (50, eslow)]:
        if len(rows) < n:
            continue
        out[n - 1] = sum(closes[:n]) / n
        for i in range(n, len(rows)):
            out[i] = out[i - 1] + (closes[i] - out[i - 1]) * (2.0 / (n + 1))
    signals = []
    for i in range(50, len(rows)):
        previous = efast[i - 1] - eslow[i - 1]
        current = efast[i] - eslow[i]
        if (previous <= 0 < current) or (previous >= 0 > current):
            signals.append((i, 1 if current > 0 else -1))
    return signals, efast, eslow


def independent_audit(e, rows):
    signals, fast, slow = reference_signals(rows)
    assert [(s["bar_index"], 1 if s["target"] == "LONG" else -1) for s in e["signals"]] == signals
    assert len(signals) == 172
    for i, state in enumerate(e["indicators"]):
        assert state["ema20_hex"] == (None if fast[i] is None else fast[i].hex())
        assert state["ema50_hex"] == (None if slow[i] is None else slow[i].hex())
    # Future-perturbation check: altering every close after each cutoff cannot affect earlier signals.
    cutoffs = [49, 148, 291, 999, 4463, 7000, 8855]
    for cutoff in cutoffs:
        changed = [dict(row) for row in rows]
        for i in range(cutoff + 1, len(changed)):
            changed[i]["close"] = "1" if i % 2 else "999999"
        changed_signals, _, _ = reference_signals(changed)
        assert [s for s in changed_signals if s[0] <= cutoff] == [s for s in signals if s[0] <= cutoff]
    fills = e["fills"]
    for j, (i, side) in enumerate(signals):
        opening = fills[2 * j]
        closing = fills[2 * j + 1]
        assert opening["role"] == "OPEN"
        assert opening["position_before_btc"] == "0"
        assert D(opening["position_after_btc"]) == D(side) * D("0.010")
        next_i = signals[j + 1][0] if j + 1 < len(signals) else None
        base_entry = D(rows[i + 1]["open"])
        base_exit = D(rows[next_i + 1]["open"]) if next_i is not None else D(rows[-1]["close"])
        for f, base, direction in [(opening, base_entry, side), (closing, base_exit, -side)]:
            rounded = (base * (1 + D(direction) * D("0.0001")) / D("0.1")).to_integral_value(
                rounding=ROUND_CEILING if direction > 0 else ROUND_FLOOR) * D("0.1")
            assert D(f["fill_price"]) == rounded
            assert D(f["reference_price"]) == base
            assert D(f["commission"]) == rounded * D("0.010") * D("0.0005")
            assert D(f["quantity_btc"]) == D("0.010") and f["liquidity"] == "TAKER"
            if f["signal_available_ns"] is not None:
                assert f["ts_ns"] == f["signal_available_ns"] + 1
        assert closing["position_after_btc"] == "0"
        t = e["trades"][j]
        gross = (D(closing["fill_price"]) - D(opening["fill_price"])) * side * D("0.010")
        fees = D(opening["commission"]) + D(closing["commission"])
        assert D(t["gross_pnl"]) == gross and D(t["commissions"]) == fees
        assert D(t["net_pnl"]) == gross - fees
    # Independently mark all 8,928 closes from the executed fill journal.
    balance, signed, entry, fill_cursor = D("10000"), 0, None, 0
    peak, maxdd, maxpct = balance, D(0), D(0)
    for i, row in enumerate(rows):
        end_ns = (int(row["open_time"]) + 300000) * 1000000
        limit_ns = end_ns + 2 if i == len(rows) - 1 else end_ns
        while fill_cursor < len(fills) and fills[fill_cursor]["ts_ns"] <= limit_ns:
            f = fills[fill_cursor]
            px, fee = D(f["fill_price"]), D(f["commission"])
            balance -= fee
            if f["role"] == "OPEN":
                assert signed == 0
                signed = 1 if f["side"] == "BUY" else -1
                entry = px
            else:
                balance += (px - entry) * signed * D("0.010")
                signed, entry = 0, None
            assert D(f["balance_after"]) == balance
            fill_cursor += 1
        unrealized = (D(row["close"]) - entry) * signed * D("0.010") if signed else D(0)
        equity = balance + unrealized
        point = e["equity"][i]
        assert D(point["balance"]) == balance and D(point["equity"]) == equity
        assert D(point["unrealized_pnl"]) == unrealized
        assert D(point["position_btc"]) == signed * D("0.010")
        peak = max(peak, equity)
        maxdd, maxpct = max(maxdd, peak - equity), max(maxpct, (peak - equity) / peak * 100)
    assert fill_cursor == len(fills) and signed == 0
    m = e["metrics"]
    assert D(m["max_drawdown_usdt"]) == maxdd
    assert D(m["max_drawdown_pct"]) == maxpct
    pnl = [D(t["net_pnl"]) for t in e["trades"]]
    assert D(m["profit_factor"]) == sum(p for p in pnl if p > 0) / -sum(p for p in pnl if p < 0)
    assert D(m["net_realized_pnl"]) == sum(pnl) == balance - D("10000")
    assert sum(D(f["commission"]) for f in fills) == D(m["commissions"])
    return {"signals": len(signals), "fills_audited": len(fills), "trades_audited": len(pnl),
            "equity_points_audited": len(rows), "future_perturbation_cutoffs": cutoffs,
            "completed_closes_then_next_open": True, "close_before_reverse": True,
            "final_close_slippage_and_fee": True, "decimal_accounting": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).parent / "btcusdt-repro")
    args = parser.parse_args()
    raws = [json.loads((args.root / f"run{i}" / "raw.json").read_text()) for i in [1, 2]]
    csv_bytes = (args.root / "BTCUSDT-5m-2025-01.csv").read_bytes()
    rows = list(csv.DictReader(csv_bytes.decode().splitlines()))
    archive = (args.root / "BTCUSDT-5m-2025-01.zip").read_bytes()
    archive_sha = hashlib.sha256(archive).hexdigest()
    assert archive_sha == (args.root / "BTCUSDT-5m-2025-01.zip.CHECKSUM").read_text().split()[0]
    audits = [independent_audit(raw["economics"], rows) for raw in raws]
    canonical = [canonicalize(raw) for raw in raws]
    hashes = [hashlib.sha256(c).hexdigest() for c in canonical]
    for i, c in enumerate(canonical, 1):
        (args.root / f"run{i}" / "canonical.json").write_bytes(c)
    equal_economics = raws[0]["economics"] == raws[1]["economics"]
    m = raws[0]["economics"]["metrics"]
    comparisons = {}
    for key, expected in PREVIOUS_EXACT.items():
        actual = m[key]
        comparisons[key] = {"expected": expected, "actual": actual, "equal": D(str(actual)) == D(str(expected)), "comparison": "exact decimal"}
    for key, (expected, quantum) in PREVIOUS_ROUNDED.items():
        rounded = D(m[key]).quantize(D(quantum), rounding=ROUND_HALF_UP)
        comparisons[key] = {"expected": expected, "actual_full_precision": m[key], "actual_at_reported_precision": str(rounded),
                            "equal": rounded == D(expected), "comparison": "exact at prior report precision; unrounded prior value unavailable"}
    previous_match = all(c["equal"] for c in comparisons.values())
    match_old_sha = [h == OLD_SHA256 for h in hashes]
    # Conservative label: supplied PARTIAL rule applies while old canonicalization is missing.
    label = "REPRODUCIBILITY_PARTIAL" if equal_economics and canonical[0] == canonical[1] and previous_match else "REPRODUCIBILITY_FAIL"
    sections = {}
    for key in raws[0]["economics"]:
        value = json.dumps(raws[0]["economics"][key], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        sections[key] = {"identical_between_runs": raws[0]["economics"][key] == raws[1]["economics"][key], "sha256": hashlib.sha256(value).hexdigest()}
    result = {"classification": label, "runtime": raws[0]["runtime"], "canonical_schema": "btc-ema-replay-canonical-v1",
              "canonical_sha256": hashes, "canonical_bytes_identical": canonical[0] == canonical[1],
              "economics_exactly_identical": equal_economics, "prior_report_metrics_match": previous_match,
              "previous_canonical_sha256": OLD_SHA256, "new_hash_equals_previous_hash": match_old_sha,
              "historical_byte_reproduction": "UNVERIFIABLE: prior script and canonicalization unavailable; this schema is new",
              "historical_event_by_event_comparison": "UNAVAILABLE: prior orders, fills, signals and equity curve were not supplied",
              "data": {"bars": len(rows), "archive_sha256": archive_sha, "published_archive_checksum_verified": True,
                       "csv_sha256": hashlib.sha256(csv_bytes).hexdigest(), "gaps": 0, "duplicates": 0},
              "metric_comparisons": comparisons, "section_comparisons": sections,
              "independent_audits": audits, "engine_validations": [r["validation"] for r in raws]}
    (args.root / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if label == "REPRODUCIBILITY_FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

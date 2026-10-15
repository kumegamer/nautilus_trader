"""Timestamp-filtered rolling validation; proposals have no access to this evaluator."""

import pandas as pd

from .common import DAY, config
from .metrics import (
    block_bootstrap,
    portfolio_daily,
    risk_metrics,
    selected_trades,
    trade_metrics,
)
from .profiles import BASE


def evaluate(profile, timestamp, store):
    cfg = config()["validation"]
    end = timestamp - cfg["embargo_days"] * DAY
    begin = end - cfg["training_days"] * DAY
    runs = store[(profile, "ENTRY_ONLY", "base")]
    trades = selected_trades(runs, begin, end, purge_blocks=True)
    m = trade_metrics(trades)
    blocks = [0.0, 0.0, 0.0]
    counts = {}
    for t in trades:
        blocks[min(2, int(3 * (t["exit_ns"] - begin) / (end - begin)))] += t["net_pnl"]
        counts[t["symbol"]] = counts.get(t["symbol"], 0) + 1
    costs = {
        scenario: trade_metrics(
            selected_trades(store[(profile, "ENTRY_ONLY", scenario)], begin, end, True)
        )["net_pnl"]
        for scenario in ("cost1.5x", "cost2x")
    }
    neighbors = {
        suffix: trade_metrics(
            selected_trades(
                store[(profile + suffix, "ENTRY_ONLY", "base")], begin, end, True
            )
        )["net_pnl"]
        for suffix in ("_STOP", "_WINDOW")
    }
    bootstrap = block_bootstrap(trades, begin, end)
    risk = risk_metrics(portfolio_daily(runs, begin, end), 30000)
    concentration = (
        m["top1_share"] is not None
        and m["top1_share"] <= cfg["maximum_top1_share"]
        and m["largest_month_share"] is not None
        and m["largest_month_share"] <= cfg["maximum_month_share"]
        and m["largest_symbol_share"] is not None
        and m["largest_symbol_share"] <= cfg["maximum_symbol_share"]
    )
    gates = {
        "integrity": all(
            r["reconciliation_difference"] == "0.00000000"
            or abs(float(r["reconciliation_difference"])) <= 0.00001
            for r in runs
        ),
        "sample": m["trades"] >= cfg["minimum_trades"],
        "economics": m["net_pnl"] > 0
        and (m["profit_factor"] or 0) >= cfg["minimum_profit_factor"],
        "chronology": sum(x > 0 for x in blocks) >= cfg["minimum_positive_blocks"]
        and blocks[-1] > 0,
        "cost": all(x > 0 for x in costs.values()),
        "risk": risk["maximum_drawdown"] <= cfg["maximum_drawdown"],
        "transfer": sum(
            net > 0 and counts.get(s, 0) >= cfg["minimum_symbol_trades"]
            for s, net in m["symbols"].items()
        )
        >= cfg["minimum_positive_symbols"],
        "stability": sum(x > 0 for x in neighbors.values())
        >= cfg["minimum_positive_neighbors"],
        "resampling": bootstrap["probability_positive"]
        >= cfg["bootstrap_probability_positive"],
        "concentration": concentration,
    }
    return {
        "profile": profile,
        "timestamp": timestamp,
        "valid_until_ns": int(
            (
                pd.Timestamp(timestamp, unit="ns", tz="UTC") + pd.offsets.MonthBegin(1)
            ).value
        ),
        "begin_ns": begin,
        "end_ns": end,
        "eligible": all(gates.values()),
        "gates": gates,
        "metrics": m,
        "risk": risk,
        "blocks": blocks,
        "costs": costs,
        "neighbors": neighbors,
        "bootstrap": bootstrap,
    }


class EvidenceProvider:
    def __init__(self, records):
        self.records = records

    def at(self, timestamp):
        available = [
            r
            for r in self.records
            if r["timestamp"] <= timestamp
            and r["end_ns"] < timestamp < r.get("valid_until_ns", 10**30)
        ]
        latest = {}
        for r in sorted(available, key=lambda r: r["timestamp"]):
            latest[r["profile"]] = r
        return latest


def build_records(store, timestamps):
    return [evaluate(p.id, t, store) for t in timestamps for p in BASE]

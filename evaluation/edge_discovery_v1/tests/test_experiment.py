"""Critical safeguards and independent execution-accounting expectations."""

import json
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from edge_discovery import common, engine
from edge_discovery.common import candidates, ns
from edge_discovery.engine import EdgeStrategy, quantize
from edge_discovery.metrics import metrics


def synthetic():
    start = ns("2022-01-01")
    t = start - 400 * 300 * 10**9 + np.arange(1000, dtype="int64") * 300 * 10**9
    price = 100 + np.arange(1000) * 0.02
    bars = pd.DataFrame(
        {
            "t": t,
            "open": price,
            "high": price + 0.05,
            "low": price - 0.05,
            "close": price + 0.01,
            "volume": 100000.0,
        }
    )
    rates = pd.DataFrame(
        {"t": [start + 8 * 3600 * 10**9], "rate": [0.001], "interval": [8], "mark": [110.0]}
    )
    return bars, rates


class Scheduled(EdgeStrategy):
    def on_bar(self, bar):
        self.previous_volume = Decimal(100000)
        if bar.ts_event == ns("2022-01-01") + 300 * 10**9 - 10**6:
            self.pending = {
                "action": "entry",
                "side": self.p.get("test_side", 1),
                "distance": 1,
                "signal_ns": bar.ts_event,
                "regime": "trend",
            }
        if bar.ts_event == ns("2022-01-01") + 10 * 3600 * 10**9 - 10**6:
            self.pending = {"action": "exit", "signal_ns": bar.ts_event, "regime": "trend"}
        if bar.ts_event >= self.start and (bar.ts_event + 10**6) % engine.DAY == 0:
            balance = (
                self.cache.account_for_venue(engine.VENUE).balance_total(engine.USDT).as_decimal()
            )
            unrealized = (
                self.signed_qty * (bar.close.as_decimal() - self.active["entry_price"])
                if self.active
                else 0
            )
            self.daily[bar.ts_event + 10**6] = float(balance + unrealized)


@pytest.mark.parametrize("side", [1, -1])
def test_native_fills_funding_and_cost_stress(monkeypatch, side):
    monkeypatch.setattr(engine, "EdgeStrategy", Scheduled)
    bars, rates = synthetic()
    c = {
        "id": "scheduled",
        "family": "trend_breakout",
        "minutes": 5,
        "lookback": 24,
        "stop_atr": 2.0,
        "test_side": side,
    }
    a = engine.run(c, "SOLUSDT", "research", bars, rates)
    b = engine.run(c, "SOLUSDT", "research", bars, rates, "cost2x")
    assert len(a["trades"]) == 1
    trade = a["trades"][0]
    assert trade["quantity"] == 25
    assert trade["funding"] == pytest.approx(-side * 25 * 110 * 0.001, abs=1e-7)
    assert trade["gross_pnl"] == pytest.approx(side * 25 * (110.4 - 108.02))
    assert trade["slippage"] > 0
    assert b["trades"][0]["net_pnl"] < trade["net_pnl"]
    assert abs(float(a["reconciliation_difference"])) < 1e-8
    assert all(f["ts_ns"] - f["signal_ns"] == 2 * 10**6 for f in a["fills"])
    for f in a["fills"]:
        notional = float(f["price"]) * float(f["quantity"])
        assert float(f["fee"]) == pytest.approx(notional * 0.0005, abs=1e-7)


def test_predeclared_small_grid_and_neighbors():
    assert len(candidates()) == 32
    assert len({c["id"] for c in candidates()}) == 32
    from edge_discovery.workflow import neighbors

    assert len(neighbors(candidates()[0])) == 2


@pytest.mark.parametrize("minutes", [5, 15, 60])
def test_all_declared_timeframes_use_valid_native_aggregation(minutes):
    inst = engine.instrument("BTCUSDT")
    bar_type = engine.native_bar_type(inst, minutes)
    assert str(bar_type).endswith(
        "1-HOUR-LAST-EXTERNAL" if minutes == 60 else f"{minutes}-MINUTE-LAST-EXTERNAL"
    )


def test_precision_rounds_adversely_and_sizes_down():
    assert quantize("123.456", "0.1") == Decimal("123.4")
    assert quantize("123.456", "0.1", True) == Decimal("123.5")
    assert quantize("0.1239", "0.001") == Decimal("0.123")


def test_holdout_requires_freeze_and_detects_source_change(monkeypatch, tmp_path):
    monkeypatch.setattr(common, "ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="sealed"):
        common.assert_frozen()
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "freeze.json").write_text(
        json.dumps({"source_hashes": {"bad": "hash"}})
    )
    monkeypatch.setattr(common, "source_hashes", lambda: {})
    with pytest.raises(RuntimeError, match="changed"):
        common.assert_frozen()


def test_equity_drawdown_includes_initial_loss():
    start, end = ns("2024-01-01"), ns("2025-01-01")
    trade = {
        "side": 1,
        "net_pnl": -100,
        "gross_pnl": -80,
        "fees": 10,
        "slippage": 10,
        "funding": 0,
        "exit_ns": start + engine.DAY,
        "duration_ns": engine.DAY,
        "regime": "trend",
    }
    run = {
        "trades": [trade],
        "symbol": "BTCUSDT",
        "period": "validation",
        "daily": [[start, 10000], [start + engine.DAY, 9900], [end, 9900]],
        "fills": [],
        "reconciliation_difference": "0",
    }
    result = metrics([run])
    assert result["maximum_drawdown"] == pytest.approx(0.01)
    assert result["return"] == pytest.approx(-0.01)


def test_period_resets_do_not_create_negative_wealth_or_false_sharpe():
    runs = []
    from edge_discovery.common import config

    for period in ["research", "validation", "wf1", "wf2"]:
        begin, finish = map(ns, config()["periods"][period])
        trade = {
            "side": 1,
            "net_pnl": -5000,
            "gross_pnl": -4980,
            "fees": 10,
            "slippage": 10,
            "funding": 0,
            "exit_ns": finish - 1,
            "duration_ns": engine.DAY,
            "regime": "trend",
        }
        runs.append(
            {
                "trades": [trade],
                "symbol": "BTCUSDT",
                "period": period,
                "daily": [[begin, 10000], [begin + engine.DAY, 7500], [finish, 5000]],
                "fills": [],
                "reconciliation_difference": "0",
            }
        )
    result = metrics(runs)
    assert result["net_pnl"] == -20000
    assert result["return"] == pytest.approx(0.5**4 - 1)
    assert min(e for _, e in result["daily_equity"]) > 0
    assert result["sharpe"] < 0
    assert result["maximum_drawdown"] == pytest.approx(1 - 0.5**4)

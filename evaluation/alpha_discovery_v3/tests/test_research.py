"""Financial and information-integrity tests; fixtures are not market evidence."""

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest
from alpha.common import DAY, ns
from alpha.features import aggregate, build
from alpha.ml import attach
from alpha.native import quantize, run
from alpha.profiles import library
from alpha.strategy import factory


@pytest.fixture(scope="module")
def fixture_data():
    t = np.arange(ns("2024-01-01"), ns("2024-02-16"), 300 * 10**9, dtype="int64")
    returns = 0.0003 + 0.00015 * np.sin(np.arange(len(t)) / 30)
    close = 100 * np.exp(np.cumsum(returns))
    frame = pd.DataFrame(
        {
            "t": t,
            "open": close / (1 + returns),
            "high": close * 1.00005,
            "low": close / (1 + returns) * 0.99995,
            "close": close,
            "volume": 100000.0,
            "quote_volume": close * 100000.0,
            "taker_buy": 55000.0,
        }
    )
    ft = np.arange(t[0], t[-1], 8 * 3600 * 10**9, dtype="int64")
    rates = pd.DataFrame(
        {
            "t": ft,
            "original_ms": ft // 10**6 + 1000,
            "interval": 8,
            "rate": 0.0001,
            "mark": np.interp(ft, t, close),
        }
    )
    return {s: frame.copy() for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT")}, {
        s: rates.copy() for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    }


def test_feature_prefix_and_future_mutation(fixture_data):
    raw, rates = fixture_data
    cut = ns("2024-02-10")
    full = build(raw, rates)
    prefix = build({s: f[f.t < cut].copy() for s, f in raw.items()}, rates)
    mutant = {s: f.copy() for s, f in raw.items()}
    for f in mutant.values():
        f.loc[f.t >= cut, ["open", "high", "low", "close"]] *= 7
        f.loc[f.t >= cut, "taker_buy"] = 1000
    changed = build(mutant, rates)
    for s in raw:
        pd.testing.assert_frame_equal(
            full[s][full[s].available_ns < cut].reset_index(drop=True),
            prefix[s],
            check_exact=True,
        )
        pd.testing.assert_frame_equal(
            full[s][full[s].available_ns < cut].reset_index(drop=True),
            changed[s][changed[s].available_ns < cut].reset_index(drop=True),
            check_exact=True,
        )


def test_funding_availability_and_no_partial_candles(fixture_data):
    raw, rates = fixture_data
    f = build(raw, rates)["BTCUSDT"]
    known = f.funding.notna()
    assert (f.loc[known, "funding_available_ns"] <= f.loc[known, "available_ns"]).all()
    assert len(aggregate(raw["BTCUSDT"].iloc[:5], 15)) == 1
    assert len(aggregate(raw["BTCUSDT"].iloc[:11], 60)) == 0


def test_budget_and_directional_neighbors():
    profiles = library()
    assert len(profiles) == 44
    for p in profiles.values():
        if p.role == "neighbor":
            parent = profiles[p.parent]
            assert p.side == parent.side and p.threshold != parent.threshold
            assert p.exit == parent.exit and p.stop_atr == parent.stop_atr


def test_exact_rounding():
    assert quantize("1.001", "0.01") == Decimal("1.00")
    assert quantize("1.001", "0.01", True) == Decimal("1.01")


def test_native_reconciliation_funding_cost_and_causal_fills(fixture_data):
    raw, rates = fixture_data
    f = build(raw, rates)["BTCUSDT"]
    features = {int(r["available_ns"]): r for r in f.to_dict("records")}
    p = library()["RAW_LONG"]
    kwargs = {
        "candidate": {**p.definition(), "liquidate": True},
        "symbol": "BTCUSDT",
        "period": "retrospective",
        "bars": aggregate(raw["BTCUSDT"], 15),
        "rates": rates["BTCUSDT"],
        "start_ns": ns("2024-02-05"),
        "end_ns": ns("2024-02-16"),
        "strategy_factory": factory(features),
    }
    base = run(**kwargs)
    stress = run(**kwargs, scenario="cost2x")
    assert len(base["trades"]) > 0
    assert Decimal(base["reconciliation_difference"]) == 0
    assert (
        base["funding_events"]
        and sum(float(x["amount"]) for x in base["funding_events"]) < 0
    )
    assert all(x["signal_ns"] < x["ts_ns"] for x in base["fills"])
    assert all(
        Decimal(x["fee"]) >= 0 and Decimal(x["slippage"]) >= 0 for x in base["fills"]
    )
    assert Decimal(stress["native_balance"]) < Decimal(base["native_balance"])
    for t in base["trades"]:
        e = t["exact_financials"]
        assert abs(
            Decimal(e["gross_pnl"])
            - Decimal(e["fees"])
            - Decimal(e["slippage"])
            + Decimal(e["funding"])
            - Decimal(e["net_pnl"])
        ) < Decimal("0.00000001")
    # Replay a shorter prefix without scheduled liquidation: earlier actual fills agree
    cutoff = ns("2024-02-12")
    kwargs["candidate"] = {**p.definition(), "liquidate": False}
    kwargs["bars"] = kwargs["bars"][kwargs["bars"].t < cutoff]
    kwargs["rates"] = kwargs["rates"][kwargs["rates"].t < cutoff]
    kwargs["end_ns"] = cutoff
    prefix = run(**kwargs)
    assert prefix["fills"] == [x for x in base["fills"] if x["ts_ns"] < cutoff]


def test_ml_training_embargo(fixture_data):
    raw, rates = fixture_data
    _, records = attach(build(raw, rates))
    for r in records:
        if r["latest_label_end_ns"] is not None:
            assert (
                r["latest_label_end_ns"]
                < r["training_cutoff_ns"]
                <= r["decision_ns"] - DAY
            )


def test_marked_boundary_pnl_is_not_deleted_trade_attribution():
    from alpha.analysis import bootstrap, summary
    from alpha.metrics import risk_metrics

    begin = ns("2025-01-01")
    end = begin + 3 * DAY
    run_record = {
        "symbol": "BTCUSDT",
        "trades": [
            {
                "entry_ns": begin - DAY,
                "exit_ns": begin + DAY,
                "net_pnl": 100.0,
                "fees": 1.0,
                "funding": 0.0,
                "slippage": 0.2,
                "symbol": "BTCUSDT",
            }
        ],
        "daily": [
            [begin, 10050.0],
            [begin + DAY, 10100.0],
            [begin + 2 * DAY, 10080.0],
            [end, 10090.0],
        ],
        "fills": [],
        "funding_events": [],
        "exposure_daily": [],
    }
    m = summary([run_record], begin, end)
    assert m["net_pnl"] == 40 and m["purged_trade_net"] == 0 and m["trades"] == 0
    assert abs(sum(m["months_marked"].values()) - m["net_pnl"]) < 1e-9
    cash = risk_metrics([[begin, 10000], [end, 10000]], 10000)
    assert cash["sharpe"] is None and cash["maximum_drawdown"] == 0
    a = bootstrap([run_record], begin, end)
    b = bootstrap([run_record], begin, end)
    assert a == b

"""Behavioral and causal safeguards for the experiment, separate from economic evidence."""

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ats.common import DAY, HOUR, assert_specification, ns
from ats.controller import Controller
from ats.evidence import EvidenceProvider
from ats.features import build_features
from ats.native import run
from ats.profiles import library
from ats.regime import RegimeEngine, invalidated
from ats.research import Proposal, save_proposals
from ats.runtime import candidate, factory


def features():
    return {
        "ready": True,
        "new_hour": True,
        "vol_ratio_60": 1.0,
        "efficiency_60": 0.5,
        "slope_60": 0.1,
        "momentum_15": 0.0,
    }


def test_hysteresis_suppresses_single_candidate_and_records_dwell():
    engine = RegimeEngine()
    f = features()
    for h in range(6):
        state = engine.update(h * HOUR, f)
    assert state["regime"] == "TREND_LOW_VOL"
    engine.update(6 * HOUR, {**f, "efficiency_60": 0.1})
    assert engine.regime == "TREND_LOW_VOL"
    engine.update(7 * HOUR, f)
    assert len(engine.transitions) == 1
    assert engine.transitions[0]["previous_duration_ns"] >= 4 * HOUR


@pytest.mark.parametrize(
    "policy, expected",
    [
        ("ENTRY_ONLY", False),
        ("PERSIST_4", True),
        ("CONFIDENT_80", True),
        ("V1_IMMEDIATE", True),
    ],
)
def test_position_invalidated_is_independent_of_entry(policy, expected):
    f = {
        "regime": "RANGE_LOW_VOL",
        "raw_regime": "RANGE_LOW_VOL",
        "transition_confidence": 0.85,
        "persistence_hours": 2,
    }
    assert invalidated(policy, library()["TB_SHORT"], f, 4) is expected


def test_evidence_provider_never_reads_future_score():
    provider = EvidenceProvider(
        [{"profile": "TB_SHORT", "timestamp": 100, "end_ns": 90, "eligible": True}]
    )
    assert provider.at(99) == {}
    assert provider.at(100)["TB_SHORT"]["eligible"]


def test_validated_controller_actually_switches_and_preserves_open_position():
    t = ns("2025-01-01")
    provider = EvidenceProvider(
        [
            {"profile": p, "timestamp": t, "end_ns": t - DAY, "eligible": True}
            for p in ("TB_SHORT", "VB_SHORT")
        ]
    )
    c = Controller("BTCUSDT", provider)
    f = {"regime": "TREND_LOW_VOL", "confidence": 0.8}
    selected, risk, allowed, safety = c.decide(t, f, [], {t: 10000}, None)
    assert (selected, risk, allowed, safety) == ("TB_SHORT", 1, True, False)
    f = {"regime": "VOLATILITY_EXPANSION", "confidence": 0.8}
    assert c.decide(t + 2 * DAY, f, [], {t: 10000}, "TB_SHORT")[0] == "TB_SHORT"
    assert not c.decide(t + 2 * DAY, f, [], {t: 10000}, "TB_SHORT")[2]
    assert c.decide(t + 3 * DAY, f, [], {t: 10000}, None)[0] == "VB_SHORT"
    assert c.switches[-1]["available_eligible_profiles"] == ["TB_SHORT", "VB_SHORT"]


def synthetic_bars(n=13000):
    t = ns("2023-11-20") + np.arange(n, dtype=np.int64) * 300 * 10**9
    prices = 100 + np.arange(n) * 0.001 + np.sin(np.arange(n) / 20)
    return pd.DataFrame(
        {
            "t": t,
            "open": prices,
            "high": prices + 1,
            "low": prices - 1,
            "close": prices + 0.1,
            "volume": 1000.0,
        }
    )


def test_features_future_mutation_leaves_prefix_unchanged():
    b = synthetic_bars()
    rates = pd.DataFrame({"original_ms": [int(b.t.iloc[0] // 10**6)], "rate": [0.0]})
    first = build_features({"BTCUSDT": b}, {"BTCUSDT": rates})["BTCUSDT"]
    changed = b.copy()
    changed.loc[12000:, ["open", "high", "low", "close"]] *= 2
    second = build_features({"BTCUSDT": changed}, {"BTCUSDT": rates})["BTCUSDT"]
    cutoff = int(b.t.iloc[12000])
    pd.testing.assert_frame_equal(
        first[first.available_ns < cutoff], second[second.available_ns < cutoff]
    )


def test_native_execution_costs_accounting_and_open_replay():
    start = ns("2025-01-01")
    times = start + np.arange(8, dtype=np.int64) * 900 * 10**9
    bars = pd.DataFrame(
        {
            "t": times,
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "volume": 100000.0,
        }
    )
    rows = {}
    for i, t in enumerate(times):
        rows[int(t + 900 * 10**9 - 10**6)] = {
            "ready": True,
            "new_hour": True,
            "regime": "TREND_LOW_VOL",
            "confidence": 0.9,
            "raw_regime": "TREND_LOW_VOL",
            "raw_confidence": 0.9,
            "transition_confidence": 0.9,
            "persistence_hours": 5,
            "vol_ratio_60": 1.0,
            "60_48_close": 101.0,
            "60_48_atr": 1.0,
            "60_48_high_prev": 100.0,
            "60_48_low_prev": 90.0,
            "60_48_exit_low": 90.0,
            "60_48_exit_high": 110.0,
        }
    rates = pd.DataFrame(columns=["t", "mark", "rate", "interval"])
    first = run(
        candidate("TB_LONG"),
        "ETHUSDT",
        "retrospective",
        bars,
        rates,
        strategy_factory=factory(rows),
        start_ns=start,
        end_ns=int(times[-1] + 900 * 10**9),
    )
    assert len(first["trades"]) == 1
    assert all(f["signal_ns"] < f["ts_ns"] for f in first["fills"])
    assert abs(float(first["reconciliation_difference"])) < 0.00001
    assert first["trades"][0]["fees"] > 0
    second = run(
        candidate("TB_LONG", liquidate=False),
        "ETHUSDT",
        "retrospective",
        bars,
        rates,
        strategy_factory=factory(rows),
        start_ns=start,
        end_ns=int(times[-1] + 900 * 10**9),
    )
    assert second["open_position"] is not None
    assert abs(float(second["reconciliation_difference"])) < 0.00001


def test_proposal_is_data_only_and_does_not_mutate_input(tmp_path):
    class Agent:
        def propose(self, evidence):
            evidence["activation"] = True
            return [
                Proposal(
                    "Test", "Diagnostic", "New experiment", ("ledger",), "Change window"
                )
            ]

    evidence = {"activation": False}
    original = copy.deepcopy(evidence)
    records = save_proposals(Agent(), evidence, tmp_path / "proposals.json")
    assert evidence == original
    assert records[0]["stage"] == "RESEARCH"
    assert records[0]["activation"] == "PROHIBITED"


def test_predeclared_specification_is_unchanged():
    assert_specification()


def test_negative_month_and_symbol_totals_fail_concentration_without_error():
    from ats.evidence import evaluate

    timestamp = ns("2025-01-01")
    end = timestamp - 7 * DAY
    begin = end - 365 * DAY
    runs = []
    for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        trades = []
        for i in range(90):
            t = begin + (i * 4 + 1) * DAY
            trades.append(
                {
                    "entry_ns": t,
                    "exit_ns": t + HOUR,
                    "symbol": symbol,
                    "net_pnl": 1.0 if i % 3 else -5.0,
                    "fees": 0.0,
                    "funding": 0.0,
                    "slippage": 0.0,
                }
            )
        runs.append(
            {
                "trades": trades,
                "daily": [[begin, 10000.0], [end, 10000.0]],
                "reconciliation_difference": "0",
            }
        )
    store = {
        ("TB_SHORT" + suffix, "ENTRY_ONLY", scenario): runs
        for suffix in ("", "_STOP", "_WINDOW")
        for scenario in ("base", "cost1.5x", "cost2x")
    }
    record = evaluate("TB_SHORT", timestamp, store)
    assert not record["eligible"]
    assert not record["gates"]["concentration"]


@pytest.mark.parametrize(
    "policy,exit_bar",
    [("ENTRY_ONLY", 23), ("V1_IMMEDIATE", 8), ("PERSIST_4", 20), ("CONFIDENT_80", 12)],
)
def test_native_exit_policy_counterfactuals_and_funding_boundary(policy, exit_bar):
    start = ns("2025-01-01")
    times = start + np.arange(24, dtype=np.int64) * 900 * 10**9
    bars = pd.DataFrame(
        {
            "t": times,
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "volume": 100000.0,
        }
    )
    rows = {}
    for i, t in enumerate(times):
        regime = "TREND_LOW_VOL" if i < 7 else "RANGE_LOW_VOL"
        confidence = 0.7 if i < 11 else 0.85
        rows[int(t + 900 * 10**9 - 10**6)] = {
            "ready": True,
            "new_hour": (i + 1) % 4 == 0,
            "regime": regime,
            "confidence": confidence,
            "raw_regime": regime,
            "raw_confidence": confidence,
            "transition_confidence": confidence,
            "persistence_hours": 2,
            "vol_ratio_60": 1.0,
            "60_48_close": 101.0,
            "60_48_atr": 1.0,
            "60_48_high_prev": 100.0,
            "60_48_low_prev": 90.0,
            "60_48_exit_low": 90.0,
            "60_48_exit_high": 110.0,
        }
    rates = pd.DataFrame(
        {"t": [start + 2 * HOUR], "mark": [100.0], "rate": [0.001], "interval": [8]}
    )
    result = run(
        candidate("TB_LONG", policy),
        "ETHUSDT",
        "retrospective",
        bars,
        rates,
        strategy_factory=factory(rows),
        start_ns=start,
        end_ns=start + 6 * HOUR,
    )
    assert len(result["trades"]) == 1
    trade = result["trades"][0]
    assert trade["exit_ns"] == int(times[exit_bar]) + 10**6
    assert trade["exit_reasons"] == (
        ["SCHEDULED_END"] if policy == "ENTRY_ONLY" else ["REGIME_INVALIDATED"]
    )
    assert trade["funding"] == pytest.approx(-1.25, abs=1e-8)
    assert trade["net_pnl"] == pytest.approx(-2.75, abs=1e-8)
    assert result["funding_events"][0]["timestamp"] == start + 2 * HOUR

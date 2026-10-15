"""Integrity, causal controller boundaries, and native execution regression tests."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest
from adaptive.common import DAY, HOUR, config, ns
from adaptive.controller import Controller
from adaptive.evidence import EvidenceProvider
from adaptive.features import RegimeEngine, aggregate, build_features
from adaptive.native import run
from adaptive.performance import DriftDetector, PerformanceMonitor
from adaptive.profiles import BASE, NO_TRADE, library
from adaptive.research import (
    Proposal,
    Registry,
    ResearchLoop,
    State,
    validate_proposals,
)
from adaptive.runtime import factory, native_candidate
from pandas.testing import assert_frame_equal


def raw_bars(count=12000):
    t = ns("2023-12-01") + np.arange(count, dtype=np.int64) * 300 * 10**9
    c = 40000 * np.exp(
        np.sin(np.arange(count) / 60) * 0.03 + np.arange(count) * 0.000002
    )
    return pd.DataFrame(
        {
            "t": t,
            "open": c,
            "high": c * 1.001,
            "low": c * 0.999,
            "close": c,
            "volume": 1000.0,
        }
    )


def rates_for(b):
    t = b.t.to_numpy()[::96]
    return pd.DataFrame(
        {
            "t": t,
            "rate": 0.0001,
            "interval": 8,
            "mark": 40000.0,
            "original_ms": t // 10**6 + 1234,
        }
    )


def passing(timestamp):
    return {
        "end_ns": timestamp - DAY,
        "gates": {
            k: True
            for k in (
                "sample",
                "validation_positive",
                "walk_forward",
                "sealed_oos",
                "cost_stress",
                "neighbors",
                "symbols",
                "drawdown",
                "concentration",
                "profit_factor",
                "regimes",
                "sides",
            )
        },
    }


def native_fixture():
    t = np.arange(ns("2023-12-31"), ns("2024-01-04"), 900 * 10**9, dtype=np.int64)
    c = 40000 + np.arange(len(t)) * 10
    bars = pd.DataFrame(
        {
            "t": t,
            "open": c,
            "high": c + 12,
            "low": c - 12,
            "close": c + 1,
            "volume": 10000.0,
        }
    )
    features = {}
    for row in bars.itertuples():
        available = int(row.t + 900 * 10**9 - 10**6)
        f = {
            "available_ns": available,
            "ready": True,
            "vol_ratio_60": 1,
            "efficiency_60": 0.5,
            "slope_60": 0.1,
            "momentum_15": 0.01,
            "new_hour": (available + 10**6) % HOUR == 0,
            "funding_rate": 0.0001,
        }
        for p in library().values():
            prefix = f"{p.minutes}_{p.lookback}_"
            f.update(
                {
                    prefix + "close": row.close,
                    prefix + "atr": 50,
                    prefix + "trend": row.close - 100,
                    prefix + "eq": row.close - 10,
                    prefix + "high_prev": row.close - 1,
                    prefix + "low_prev": row.close - 100,
                    prefix + "exit_high": row.close + 100,
                    prefix + "exit_low": row.close - 200,
                }
            )
        features[available] = f
    funding = pd.DataFrame(
        {
            "t": np.arange(ns("2024-01-01"), ns("2024-01-04"), 8 * HOUR),
            "rate": 0.0001,
            "interval": 8,
            "mark": 40000.0,
        }
    )
    return bars, funding, features


def test_prefix_invariance_future_prices_volume_and_funding():
    b = raw_bars()
    rates = rates_for(b)
    cutoff = int(b.t.iloc[10000])
    raw = {s: b.copy() for s in config()["symbols"]}
    rr = {s: rates.copy() for s in raw}
    original = build_features(raw, rr)
    for s, frame in raw.items():
        frame.loc[raw[s].t >= cutoff, ["open", "high", "low", "close"]] *= 2
        frame.loc[frame.t >= cutoff, "volume"] *= 10
        rr[s].loc[rr[s].t >= cutoff, "rate"] = -0.1
    changed = build_features(raw, rr)
    for s, frame in original.items():
        assert_frame_equal(
            frame[frame.available_ns < cutoff],
            changed[s][changed[s].available_ns < cutoff],
        )


def test_incomplete_higher_timeframe_never_available():
    b = raw_bars(11)
    hourly = aggregate(b, 60)
    assert hourly.empty
    b = raw_bars(12)
    hourly = aggregate(b, 60)
    assert len(hourly) == 1
    assert hourly.available_ns.iloc[0] > b.t.iloc[-1]


def test_funding_feature_uses_actual_publication_timestamp():
    b = raw_bars(400)
    rates = rates_for(b)
    first_close = int(b.t.iloc[0] + 15 * 60 * 10**9 - 10**6)
    rates.loc[0, "original_ms"] = (first_close + 1) // 10**6 + 1
    features = build_features({"BTCUSDT": b}, {"BTCUSDT": rates})["BTCUSDT"]
    assert pd.isna(features.funding_rate.iloc[0])
    assert features.funding_rate.iloc[1] == 0.0001


def test_regime_prefix_and_transition_duration():
    engine = RegimeEngine()
    f = {
        "ready": True,
        "vol_ratio_60": 1,
        "efficiency_60": 0.5,
        "slope_60": 0.1,
        "momentum_15": 0.01,
    }
    first = engine.update(100, f)
    second = engine.update(200, f)
    assert first["regime"] == "TREND_LOW_VOL"
    assert second["duration_ns"] == 100
    assert len(engine.transitions) == 1
    assert engine.update(300, {**f, "vol_ratio_60": 4})["regime"] == "MARKET_STRESS"
    assert engine.update(400, {"ready": False})["regime"] == "UNKNOWN"


def test_profiles_immutable_and_budget_bounded():
    assert len(library()) == 15
    with pytest.raises(FrozenInstanceError):
        BASE[0].stop_atr = 10
    assert NO_TRADE.risk_allocation == 0
    assert "MARKET_STRESS" in BASE[0].incompatible_regimes


def test_ai_unknown_parameters_and_direct_activation_rejected():
    with pytest.raises(ValueError):
        validate_proposals([Proposal("arbitrary", "NEW_PARAMETERS", 1, "AI says so")])
    registry = Registry()
    with pytest.raises(ValueError):
        registry.transition("TB48", State.SHADOW, 100, passing(100))
    with pytest.raises(ValueError):
        registry.transition("TB48", State.LIVE_ELIGIBLE, 100, passing(100))


def test_missing_future_or_failed_evidence_cannot_promote():
    registry = Registry()
    with pytest.raises(ValueError):
        registry.transition("TB48", State.CANDIDATE, 100, {"end_ns": 101})
    registry.transition("TB48", State.CANDIDATE, DAY * 2, passing(DAY * 2))
    with pytest.raises(ValueError):
        registry.transition(
            "TB48", State.VALIDATED, DAY * 2, {"end_ns": DAY, "gates": {"sample": True}}
        )
    assert registry.eligible(DAY * 3) == ["NO_TRADE"]


def test_promotion_strict_availability_and_canary_gate():
    registry = Registry()
    registry.consider("TB48", 2 * DAY, passing(2 * DAY))
    assert "TB48" not in registry.eligible(2 * DAY)
    assert "TB48" in registry.eligible(2 * DAY + 1)
    with pytest.raises(ValueError):
        registry.transition("TB48", State.CANARY_ELIGIBLE, 3 * DAY, {"end_ns": 2 * DAY})
    registry.transition("TB48", State.DISABLED, 3 * DAY, {"end_ns": 2 * DAY})
    assert "TB48" not in registry.eligible(4 * DAY)


def test_research_throttle_and_failed_experiments_persist():
    registry = Registry()
    loop = ResearchLoop(
        registry, lambda p, t: {**passing(t), "gates": {"sample": False}}
    )
    loop.request(100 * DAY, {"state": "EDGE_DEGRADING"})
    n = len(loop.events)
    assert n >= 4 and all(e["status"] == "REJECTED" for e in loop.events)
    loop.request(101 * DAY, {"state": "EDGE_DEGRADING"})
    assert len(loop.events) == n
    loop.request(131 * DAY, {"state": "EDGE_DEGRADING"})
    assert len(loop.events) == 2 * n


def trade(index, net=-25, profile="TB48"):
    return {
        "entry_ns": index * HOUR,
        "exit_ns": (index + 1) * HOUR,
        "net_pnl": net,
        "gross_pnl": net + 2,
        "fees": 1,
        "slippage": 1,
        "funding": 0,
        "initial_risk": 25,
        "profile": profile,
        "symbol": "BTCUSDT",
        "side": 1,
        "regime": "TREND_LOW_VOL",
        "turnover": 2000,
        "strategy": "trend_breakout",
    }


def test_small_sample_does_not_declare_statistical_failure():
    monitor = PerformanceMonitor()
    for i in range(7):
        monitor.add(trade(i))
    regime = {"regime": "TREND_LOW_VOL", "confidence": 0.8}
    event = DriftDetector().evaluate(100 * HOUR, regime, BASE[0], monitor)
    assert event["state"] == "INSUFFICIENT_DATA"


def test_decay_is_multi_signal_and_not_exactly_50_trades():
    monitor = PerformanceMonitor()
    for i in range(30):
        monitor.add(trade(i))
    event = DriftDetector().evaluate(
        100 * HOUR, {"regime": "TREND_LOW_VOL", "confidence": 0.8}, BASE[0], monitor
    )
    assert event["state"] == "EDGE_DEGRADING"
    assert "expectancy_deterioration" in event["triggers"]
    assert "profit_factor_deterioration" in event["triggers"]
    assert "50_new_closed_trades" not in event["triggers"]


def test_execution_decay_isolated_from_signal_decay():
    monitor = PerformanceMonitor()
    for i in range(12):
        t = trade(i, net=1)
        t["fees"] = 4
        monitor.add(t)
    event = DriftDetector().evaluate(
        100 * HOUR, {"regime": "TREND_LOW_VOL", "confidence": 0.8}, BASE[0], monitor
    )
    assert event["state"] == "EXECUTION_DEGRADATION"


def test_controller_no_eligible_no_trade_and_stress_exit():
    registry = Registry()
    loop = ResearchLoop(registry, lambda p, t: None)
    controller = Controller(registry, loop)
    regime = {"regime": "TREND_LOW_VOL", "confidence": 0.8, "duration_ns": 2 * HOUR}
    event = controller.decide(100 * DAY, regime, None, PerformanceMonitor())
    assert event["new_profile"] == "NO_TRADE"
    registry.consider("TB48", 100 * DAY, passing(100 * DAY))
    controller.decide(100 * DAY + 1, regime, None, PerformanceMonitor())
    assert controller.current.id == "TB48"
    event = controller.decide(
        100 * DAY + HOUR,
        {**regime, "regime": "MARKET_STRESS"},
        None,
        PerformanceMonitor(),
    )
    assert event["new_profile"] == "NO_TRADE" and event["risk"] == 0
    assert all(
        k in event
        for k in (
            "timestamp",
            "old_profile",
            "new_profile",
            "regime",
            "regime_confidence",
            "performance_state",
            "reason",
            "evidence",
        )
    )


def test_future_results_never_in_historical_promotion_evidence():
    runs = []
    for p in ("TB48", "TB48_STOP", "TB48_WINDOW"):
        trades = []
        for i in range(700):
            x = trade(i, net=10)
            x["entry_ns"] = ns("2024-01-01") + i * DAY
            x["exit_ns"] = x["entry_ns"] + HOUR
            trades.append(x)
        runs.append(
            {"candidate": p, "scenario": "base", "period": "research", "trades": trades}
        )
    when = ns("2025-07-01")
    before = EvidenceProvider(runs)("TB48", when)
    import copy

    changed = copy.deepcopy(runs)
    for r in changed:
        for t in r["trades"]:
            if t["exit_ns"] >= when - 7 * DAY:
                t["net_pnl"] = 1e9
    assert before == EvidenceProvider(changed)("TB48", when)
    assert before["end_ns"] < when


def test_native_fill_funding_mae_and_account_reconciliation():
    bars, rates, features = native_fixture()
    out = run(
        native_candidate("TB48"),
        "BTCUSDT",
        "research",
        bars,
        rates,
        strategy_factory=factory(features, fixed="TB48"),
    )
    assert len(out["trades"]) >= 1
    assert abs(Decimal(out["reconciliation_difference"])) < Decimal("0.00001")
    assert all(f["signal_ns"] < f["ts_ns"] for f in out["fills"])
    assert all(float(f["slippage"]) >= 0 for f in out["fills"])
    assert sum(t["funding"] for t in out["trades"]) < 0
    assert all(t["mae"] <= 0 and t["mfe"] >= 0 for t in out["trades"])


def test_native_adaptive_selects_only_after_matured_evidence():
    bars, rates, features = native_fixture()

    def provider(p, t):
        return passing(t) if p == "TB48" and t >= ns("2024-01-01") else None

    out = run(
        native_candidate("TB48"),
        "BTCUSDT",
        "research",
        bars,
        rates,
        strategy_factory=factory(features, evidence_provider=provider),
    )
    assert len(out["switches"]) > 0
    assert any(e["new_profile"] == "TB48" for e in out["switches"])
    assert all(e["evidence"]["end_ns"] <= e["timestamp"] for e in out["promotions"])
    for fill in out["fills"]:
        assert fill["signal_ns"] < fill["ts_ns"]


def test_adaptive_state_roundtrip_preserves_history_and_warmup_chronology():
    from types import SimpleNamespace

    from adaptive.native import instrument
    from adaptive.runtime import AdaptiveStrategy

    inst = instrument("BTCUSDT")
    args = (
        inst,
        native_candidate("TB48"),
        ns("2024-01-01"),
        ns("2025-01-01"),
        {1: Decimal(1)},
        {},
    )
    strategy = AdaptiveStrategy(*args)
    strategy.monitor.add(trade(1))
    strategy.research.last_request = ns("2024-01-01")
    strategy.regimes.regime = "TREND_LOW_VOL"
    strategy.regimes.started = ns("2024-01-01")
    strategy.controller.registry.consider(
        "TB48", ns("2024-01-01"), passing(ns("2024-01-01"))
    )
    state = strategy.adaptive_state()
    resumed = AdaptiveStrategy(*args, resume_state=state)
    assert resumed.adaptive_state() == state
    resumed.on_bar(SimpleNamespace(ts_event=ns("2023-12-31")))
    assert resumed.regimes.started == ns("2024-01-01")


def test_material_failure_requires_new_validation_after_quarantine():
    registry = Registry()
    registry.consider("TB48", 100 * DAY, passing(100 * DAY))
    loop = ResearchLoop(registry, lambda p, t: passing(t))
    controller = Controller(registry, loop)
    controller.current, controller.risk = BASE[0], 0.5
    regime = {"regime": "TREND_LOW_VOL", "confidence": 0.8, "duration_ns": 2 * HOUR}
    controller.decide(
        101 * DAY, regime, {"state": "POSSIBLE_EDGE_FAILURE"}, PerformanceMonitor()
    )
    assert controller.current == NO_TRADE
    assert registry.states["TB48"] == State.DISABLED
    assert "TB48" not in registry.eligible(102 * DAY)
    registry.consider("TB48", 102 * DAY, passing(102 * DAY))
    assert registry.states["TB48"] == State.DISABLED
    registry.consider("TB48", 132 * DAY, passing(132 * DAY))
    assert registry.states["TB48"] == State.SHADOW


def test_freeze_writes_separate_manifest_without_overwriting_native_run(
    tmp_path, monkeypatch
):
    import gzip
    import json

    from adaptive import workflow
    from adaptive.common import digest

    monkeypatch.setattr(workflow, "ROOT", tmp_path)
    monkeypatch.setattr(workflow, "source_hashes", lambda: {"source.py": "frozen"})
    root = tmp_path / "results"
    root.mkdir()
    (root / "static_selection.json").write_text(json.dumps({"selected": "TB48"}))
    (root / "preholdout_evidence.json").write_text("{}")
    (root / "tests.txt").write_text("19 passed")
    (root / "tests.json").write_text(
        json.dumps(
            {
                "exit_code": 0,
                "source_hashes": {"source.py": "frozen"},
                "output_sha256": digest(root / "tests.txt"),
            }
        )
    )
    last = None
    for period in workflow.PRE:
        for scenario in config()["scenarios"]:
            for symbol in config()["symbols"]:
                last = workflow.run_path("ADAPTIVE", symbol, period, scenario)
                last.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(last, "wt") as f:
                    json.dump({"adaptive_state": {"saved": True}}, f)
    workflow.freeze()
    assert (root / "freeze.json").exists()
    with gzip.open(last, "rt") as f:
        assert json.load(f)["adaptive_state"] == {"saved": True}


def test_periodic_timer_not_postponed_by_regime_events():
    detector = DriftDetector()
    monitor = PerformanceMonitor()
    regime = {"regime": "TREND_LOW_VOL", "confidence": 0.8}
    detector.evaluate(100 * DAY, regime, BASE[0], monitor)
    for h in (6, 12, 18):
        detector.evaluate(
            100 * DAY + h * HOUR,
            {**regime, "regime": "RANGE_LOW_VOL" if h == 12 else "TREND_HIGH_VOL"},
            BASE[0],
            monitor,
        )
    event = detector.evaluate(101 * DAY, regime, BASE[0], monitor)
    assert "elapsed_time" in event["triggers"]


def test_trade_checkpoint_survives_other_evaluation_triggers():
    detector = DriftDetector()
    monitor = PerformanceMonitor()
    regime = {"regime": "TREND_LOW_VOL", "confidence": 0.8}
    detector.evaluate(0, regime, BASE[0], monitor)
    events = []
    for i in range(50):
        monitor.add(trade(i, net=1))
        event = detector.evaluate((i + 1) * HOUR, regime, BASE[0], monitor)
        if event:
            events.append(event)
    assert any("50_new_closed_trades" in e["triggers"] for e in events)


def test_profile_selection_does_not_chase_recent_winner():

    registry = Registry()
    for p in ("TB48", "TB48_SHORT"):
        registry.consider(p, 100 * DAY, passing(100 * DAY))
    monitor = PerformanceMonitor()
    for i in range(10):
        monitor.add(trade(i, net=1000, profile="TB48_SHORT"))
    controller = Controller(registry, ResearchLoop(registry, lambda p, t: None))
    regime = {"regime": "TREND_LOW_VOL", "confidence": 0.8, "duration_ns": 2 * HOUR}
    event = controller.decide(100 * DAY + 1, regime, None, monitor)
    assert event["new_profile"] == "TB48"

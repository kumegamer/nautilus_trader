"""Adaptive strategy runtime above deterministic NautilusTrader order execution."""

from dataclasses import asdict
from decimal import Decimal as D

from .common import DAY, config
from .controller import Controller
from .features import RegimeEngine
from .native import USDT, VENUE, EdgeStrategy
from .performance import DriftDetector, PerformanceMonitor
from .profiles import NO_TRADE, library, signal
from .research import Registry, ResearchLoop


class AdaptiveStrategy(EdgeStrategy):
    def __init__(
        self,
        inst,
        candidate,
        start,
        end,
        references,
        features,
        fixed=None,
        evidence_provider=None,
        initial_registry=None,
        resume_state=None,
    ):
        super().__init__(inst, candidate, start, end, references)
        self.features = features
        self.fixed = fixed
        self.profiles = library()
        self.regimes = RegimeEngine()
        self.monitor = PerformanceMonitor()
        self.detector = DriftDetector()
        registry = initial_registry or Registry()
        self.research = ResearchLoop(registry, evidence_provider or (lambda p, t: None))
        self.controller = Controller(registry, self.research)
        self.degradation_events = []
        self.last_profile_bar = None
        self.last_context = None
        self.last_state = "INSUFFICIENT_DATA"
        self.cfg = {**config()}
        self.equity_carry = 0.0
        self.resumed = resume_state is not None
        if resume_state:
            self.restore_adaptive_state(resume_state)
            self.equity_carry = sum(
                float(t["net_pnl"])
                for t in self.monitor.trades
                if t["exit_ns"] < self.start
            )
        self.initial_eligibility = dict(self.controller.registry.available)

    @property
    def decision_events(self):
        return self.controller.decisions

    @property
    def switch_events(self):
        return [e for e in self.controller.switches if e["timestamp"] >= self.start]

    @property
    def research_events(self):
        return self.research.events

    @property
    def promotion_events(self):
        return self.controller.registry.events

    @property
    def regime_transitions(self):
        return self.regimes.transitions

    def adaptive_state(self):
        def clean(value):
            if isinstance(value, D):
                return float(value)
            if isinstance(value, dict):
                return {k: clean(v) for k, v in value.items()}
            if isinstance(value, list):
                return [clean(v) for v in value]
            return value

        c = self.controller
        return clean(
            {
                "monitor_trades": self.monitor.trades,
                "monitor_daily": list(self.monitor.daily.items()),
                "detector": {
                    "last_evaluation": self.detector.last_evaluation,
                    "last_count": self.detector.last_count,
                    "trade_checkpoint": self.detector.trade_checkpoint,
                    "last_periodic_evaluation": self.detector.last_periodic_evaluation,
                    "last_regime": self.detector.last_regime,
                    "active_triggers": sorted(self.detector.active_triggers),
                },
                "registry": {
                    "states": {p: s.value for p, s in c.registry.states.items()},
                    "available": c.registry.available,
                    "evidence": c.registry.evidence,
                    "quarantined_until": c.registry.quarantined_until,
                },
                "controller": {
                    "current": c.current.id,
                    "risk": c.risk,
                    "last_switch": c.last_switch,
                    "switches": c.switches,
                    "disabled_until": c.disabled_until,
                    "symbol_disabled_until": c.symbol_disabled_until,
                    "side_disabled": [
                        [p, side, end] for (p, side), end in c.side_disabled.items()
                    ],
                },
                "regime": {
                    "regime": self.regimes.regime,
                    "started": self.regimes.started,
                },
                "last_research_request": self.research.last_request,
                "last_state": self.last_state,
            }
        )

    def restore_adaptive_state(self, snapshot):
        from .research import State

        self.monitor.trades = snapshot["monitor_trades"]
        self.monitor.daily = {int(t): e for t, e in snapshot["monitor_daily"]}
        for key, value in snapshot["detector"].items():
            setattr(
                self.detector, key, set(value) if key == "active_triggers" else value
            )
        r = snapshot["registry"]
        self.controller.registry.states = {p: State(s) for p, s in r["states"].items()}
        self.controller.registry.available = r["available"]
        self.controller.registry.evidence = r["evidence"]
        self.controller.registry.quarantined_until = r.get("quarantined_until", {})
        c = snapshot["controller"]
        for key in (
            "risk",
            "last_switch",
            "switches",
            "disabled_until",
            "symbol_disabled_until",
        ):
            setattr(self.controller, key, c[key])
        self.controller.current = self.profiles[c["current"]]
        self.controller.side_disabled = {
            (p, side): end for p, side, end in c["side_disabled"]
        }
        self.regimes.regime = snapshot["regime"]["regime"]
        self.regimes.started = snapshot["regime"]["started"]
        self.research.last_request = snapshot["last_research_request"]
        self.last_state = snapshot["last_state"]

    def on_bar(self, bar):
        timestamp = bar.ts_event
        if self.resumed and timestamp < self.start:
            return
        f = self.features.get(timestamp)
        if f is None:
            raise ValueError("Missing causal feature row")
        if int(f["available_ns"]) != timestamp:
            raise ValueError("Feature timestamp mismatch")
        regime = self.regimes.update(timestamp, f)
        c = float(bar.close)
        self.previous_volume = bar.volume.as_decimal()
        if self.active:
            move_high = self.active["side"] * (
                float(bar.high) - float(self.active["entry_price"])
            )
            move_low = self.active["side"] * (
                float(bar.low) - float(self.active["entry_price"])
            )
            quantity = float(self.active["quantity"])
            self.active["mae"] = min(
                self.active.get("mae", 0), quantity * min(move_high, move_low)
            )
            self.active["mfe"] = max(
                self.active.get("mfe", 0), quantity * max(move_high, move_low)
            )
        if not self.start <= timestamp < self.end:
            return
        balance = self.cache.account_for_venue(VENUE).balance_total(USDT).as_decimal()
        unrealized = (
            self.signed_qty * (D(str(c)) - self.active["entry_price"])
            if self.active
            else D(0)
        )
        if (timestamp + 10**6) % DAY == 0:
            self.daily[timestamp + 10**6] = float(balance + unrealized)
            self.monitor.daily[timestamp + 10**6] = (
                float(balance + unrealized) + self.equity_carry
            )
        if self.fixed:
            profile, risk = self.profiles[self.fixed], 1.0
            decision = {"disabled_sides": []}
        else:
            current = self.controller.current
            expected = self.controller.registry.evidence.get(current.id, {}).get(
                "expected"
            )
            drift = self.detector.evaluate(
                timestamp, regime, current, self.monitor, expected
            )
            if drift:
                self.degradation_events.append(drift)
                self.last_state = drift["state"]
            decision = self.controller.decide(timestamp, regime, drift, self.monitor)
            profile, risk = self.controller.current, self.controller.risk
        self.cfg["risk_per_trade"] = profile.risk_allocation * risk
        if self.active:
            held = self.profiles[self.active["profile"]]
            prefix = f"{held.minutes}_{held.lookback}_"
            clock_bar = held.minutes == 15 or f["new_hour"]
            close_position = (
                profile.id != held.id
                or risk == 0
                or regime["regime"] not in held.compatible_regimes
                or risk < self.active["risk_multiplier"]
                or self.active["side"] in decision["disabled_sides"]
            )
            if clock_bar and f.get("ready", False):
                self.age += 1
                atr = f[prefix + "atr"]
                side = self.active["side"]
                if held.family in ("trend_breakout", "volatility_breakout"):
                    proposal = c - side * held.stop_atr * atr
                    self.stop = (
                        max(self.stop, proposal)
                        if side > 0
                        else min(self.stop, proposal)
                    )
                    close_position |= (
                        c < f[prefix + "exit_low"]
                        if side > 0
                        else c > f[prefix + "exit_high"]
                    )
                elif held.family == "trend_pullback":
                    eq, trend = f[prefix + "eq"], f[prefix + "trend"]
                    close_position |= (
                        (c >= eq or c <= trend) if side > 0 else (c <= eq or c >= trend)
                    )
                else:
                    close_position |= (
                        c >= f[prefix + "mean"] if side > 0 else c <= f[prefix + "mean"]
                    )
                    close_position |= f[prefix + "efficiency"] > 0.35
                close_position |= (
                    side * (c - self.stop) <= 0 or self.age >= held.maximum_age
                )
            if close_position:
                self.pending = {
                    "action": "exit",
                    "signal_ns": timestamp,
                    "regime": regime["regime"],
                    "reason": "profile_or_exit_policy",
                }
        elif (
            profile != NO_TRADE
            and risk > 0
            and regime["regime"] in profile.compatible_regimes
            and (profile.minutes == 15 or f["new_hour"])
        ):
            side = signal(profile, f)
            if side and side not in decision["disabled_sides"]:
                prefix = f"{profile.minutes}_{profile.lookback}_"
                self.pending = {
                    "action": "entry",
                    "side": side,
                    "distance": profile.stop_atr * f[prefix + "atr"],
                    "signal_ns": timestamp,
                    "regime": regime["regime"],
                    "profile": profile.id,
                    "strategy": profile.family,
                    "regime_confidence": regime["confidence"],
                    "risk_multiplier": risk,
                }
                self.signal_count += 1

    def on_order_filled(self, event):
        context = self.contexts[str(event.client_order_id)]
        super().on_order_filled(event)
        if context["action"] == "entry":
            for key in ("profile", "strategy", "regime_confidence", "risk_multiplier"):
                self.active[key] = context[key]
            self.active["symbol"] = str(self.inst.raw_symbol)
            self.active["mae"], self.active["mfe"] = 0.0, 0.0
            self.active["initial_risk"] = self.active["quantity"] * D(
                str(context["distance"])
            )
        else:
            trade = self.trades[-1]
            trade["turnover"] = trade["quantity"] * (
                trade["entry_price"] + trade["exit_price"]
            )

    def on_position_closed(self, event):
        position = self.cache.position(event.position_id)
        matches = [t for t in self.trades if t["entry_ns"] == position.ts_opened]
        if len(matches) != 1:
            raise RuntimeError("Closed native position lacks a single audit trade")
        trade = matches[0]
        trade["funding"] = sum(
            (a.pnl_change.as_decimal() for a in position.adjustments() if a.pnl_change),
            D(0),
        )
        trade["net_pnl"] = (
            trade["gross_pnl"] - trade["slippage"] - trade["fees"] + trade["funding"]
        )
        if abs(trade["net_pnl"] - position.realized_pnl.as_decimal()) > D("0.00001"):
            raise RuntimeError("Real-time monitor/native realized PnL mismatch")
        self.monitor.add(trade)


def factory(features, fixed=None, evidence_provider=None, resume_state=None):
    def create(inst, candidate, start, end, references):
        return AdaptiveStrategy(
            inst,
            candidate,
            start,
            end,
            references,
            features,
            fixed,
            evidence_provider,
            resume_state=resume_state,
        )

    return create


def native_candidate(profile_id):
    p = library()[profile_id]
    return {**asdict(p), "minutes": 15}

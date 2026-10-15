"""Finite profile selection and multi-input decay monitoring, without parameter mutation."""

from .common import DAY, HOUR, config
from .metrics import risk_metrics, trade_metrics
from .profiles import library


class Controller:
    def __init__(self, symbol, provider):
        self.symbol, self.provider = symbol, provider
        self.current, self.risk = "NO_TRADE", 0.0
        self.last_switch = -(10**30)
        self.disabled_until = 0
        self.required_validation_after = 0
        self.switches, self.decisions, self.degradation, self.research = [], [], [], []
        self.last_evaluation = 0
        self.last_regime = None
        self.trade_count = 0
        self.last_research = 0
        self.performance_state = "INSUFFICIENT_DATA"
        self.rolling = {}

    def decide(self, timestamp, f, trades, daily, active_profile):
        cfg = config()["controller"]
        changed = f["regime"] != self.last_regime
        trigger = []
        if timestamp - self.last_evaluation >= DAY:
            trigger.append("ELAPSED_TIME")
        if changed:
            trigger.append("REGIME_TRANSITION")
        if len(trades) != self.trade_count:
            trigger.append("TRADE_CLOSED")
        evidence = self.provider.at(timestamp)
        eligible = sorted(
            p
            for p, e in evidence.items()
            if e["eligible"] and e["timestamp"] >= self.required_validation_after
        )
        if trigger:
            begin = timestamp - cfg["rolling_days"] * DAY
            recent = [
                t
                for t in trades
                if t["exit_ns"] >= begin and t["profile"] == self.current
            ]
            m = trade_metrics(recent)
            marked = [(t, e) for t, e in daily.items() if t >= begin]
            dd = risk_metrics(marked, config()["capital_per_symbol"])[
                "maximum_drawdown"
            ]
            elapsed = (
                timestamp - min((t["entry_ns"] for t in recent), default=timestamp)
            ) / DAY
            cost_bps = (
                (m["fees"] + m["slippage"]) / m["turnover_notional"] * 10000
                if m["turnover_notional"]
                else 0
            )
            sufficient = (
                m["trades"] >= cfg["decay_minimum_trades"]
                and elapsed >= cfg["decay_minimum_days"]
            )
            execution = m["trades"] >= 10 and cost_bps > cfg["execution_cost_bps"]
            degraded = (
                sufficient and m["expectancy"] < 0 and (m["profit_factor"] or 0) < 1
            )
            if dd >= cfg["disable_drawdown"] or execution:
                state = "EXECUTION_DEGRADATION" if execution else "DRAWDOWN_FAILURE"
                self.disabled_until = max(
                    self.disabled_until, timestamp + cfg["quarantine_days"] * DAY
                )
                self.required_validation_after = timestamp
            elif dd >= cfg["reduce_drawdown"] or degraded:
                state = "EDGE_DEGRADING"
            else:
                state = "NORMAL" if sufficient else "INSUFFICIENT_DATA"
            group_metrics = {"sides": {}, "regimes": {}}
            for key, output in (("side", "sides"), ("regime", "regimes")):
                for value in sorted({str(t[key]) for t in recent}):
                    group_metrics[output][value] = trade_metrics(
                        [t for t in recent if str(t[key]) == value]
                    )
            self.rolling = {
                **m,
                "maximum_drawdown": dd,
                "elapsed_days": elapsed,
                "cost_bps": cost_bps,
                "sharpe": risk_metrics(marked, 10000)["sharpe"],
                **group_metrics,
            }
            self.performance_state = state
            self.degradation.append(
                {
                    "timestamp": timestamp,
                    "symbol": self.symbol,
                    "profile": self.current,
                    "triggers": trigger,
                    "state": state,
                    "metrics": self.rolling,
                }
            )
            if (
                state in ("EDGE_DEGRADING", "EXECUTION_DEGRADATION", "DRAWDOWN_FAILURE")
                or (changed and not eligible)
            ) and timestamp - self.last_research >= 30 * DAY:
                self.research.append(
                    {
                        "timestamp": timestamp,
                        "symbol": self.symbol,
                        "state": state,
                        "trigger": trigger,
                        "status": "PROPOSAL_ONLY",
                    }
                )
                self.last_research = timestamp
            self.last_evaluation, self.last_regime, self.trade_count = (
                timestamp,
                f["regime"],
                len(trades),
            )
        safety = timestamp < self.disabled_until
        compatible = [
            p
            for p in cfg["priority"]
            if p in eligible and f["regime"] in library(False)[p].compatible_regimes
        ]
        desired = (
            compatible[0]
            if compatible
            and f["confidence"] >= config()["regime"]["entry_confidence"]
            and not safety
            else "NO_TRADE"
        )
        reason = (
            "PRIOR_VALIDATION_AND_REGIME"
            if desired != "NO_TRADE"
            else "NO_ELIGIBLE_COMPATIBLE_PROFILE"
        )
        if active_profile and not safety:
            desired, reason = active_profile, "POSITION_MANAGEMENT_UNTIL_STRATEGY_EXIT"
        switches = sum(s["timestamp"] > timestamp - 30 * DAY for s in self.switches)
        if desired != self.current:
            permitted = (
                safety
                or desired == "NO_TRADE"
                or (
                    timestamp - self.last_switch >= cfg["minimum_switch_hours"] * HOUR
                    and switches < cfg["maximum_switches_30d"]
                )
            )
            if permitted:
                self.switches.append(
                    {
                        "timestamp": timestamp,
                        "symbol": self.symbol,
                        "old_profile": self.current,
                        "new_profile": desired,
                        "current_regime": f["regime"],
                        "regime_confidence": f["confidence"],
                        "performance_state": self.performance_state,
                        "reason": reason,
                        "available_eligible_profiles": eligible,
                    }
                )
                self.current, self.last_switch = desired, timestamp
        self.risk = (
            0 if safety else 0.5 if self.performance_state == "EDGE_DEGRADING" else 1
        )
        allowed = self.current in eligible and self.current in compatible and not safety
        if trigger or (self.switches and self.switches[-1]["timestamp"] == timestamp):
            self.decisions.append(
                {
                    "timestamp": timestamp,
                    "symbol": self.symbol,
                    "profile": self.current,
                    "risk": self.risk,
                    "entry_allowed": allowed,
                    "position_invalidated": safety,
                    "reason": reason,
                    "eligible": eligible,
                    "evidence_end_ns": max(
                        (e["end_ns"] for e in evidence.values()), default=None
                    ),
                }
            )
        return self.current, self.risk, allowed, safety

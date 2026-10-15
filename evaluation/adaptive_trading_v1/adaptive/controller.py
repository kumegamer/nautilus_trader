"""Finite-profile policy with hysteresis, risk caps and causal eligibility."""

from .common import DAY, HOUR, config
from .performance import trade_metrics
from .profiles import NO_TRADE, library
from .research import State


class Controller:
    def __init__(self, registry, research):
        self.registry, self.research = registry, research
        self.profiles = library()
        self.policy = config()["policy"]
        self.current = NO_TRADE
        self.risk = 0.0
        self.last_switch = None
        self.switches = []
        self.decisions = []
        self.disabled_until = {}
        self.side_disabled = {}
        self.symbol_disabled_until = 0

    def decide(self, timestamp, regime, drift, monitor):
        policy = self.policy
        state = drift["state"] if drift else "NORMAL_VARIANCE"
        evidence = drift or {"timestamp": timestamp, "state": state}
        reason = "retain_validated_profile"
        candidate, risk = self.current, self.risk
        hard = state in ("POSSIBLE_EDGE_FAILURE", "EXECUTION_DEGRADATION")
        if drift:
            if hard:
                self.symbol_disabled_until = timestamp + 30 * DAY
            if hard and self.current.id != "NO_TRADE":
                self.disabled_until[self.current.id] = timestamp + 30 * DAY
                self.registry.quarantined_until[self.current.id] = timestamp + 30 * DAY
                if self.registry.states[self.current.id] in (
                    State.SHADOW,
                    State.CANARY_ELIGIBLE,
                ):
                    self.registry.transition(
                        self.current.id,
                        State.DISABLED,
                        timestamp,
                        {"end_ns": timestamp, "reason": state},
                    )
            if (
                state
                in (
                    "EDGE_DEGRADING",
                    "POSSIBLE_EDGE_FAILURE",
                    "EXECUTION_DEGRADATION",
                    "REGIME_MISMATCH",
                )
                or self.current == NO_TRADE
            ):
                self.research.request(
                    timestamp,
                    {
                        "regime": regime,
                        **drift,
                        "recent_performance": drift.get("metrics", {}),
                        "historical_regime_performance": self.registry.evidence.get(
                            self.current.id, {}
                        ).get("by_regime", {}),
                        "long_short": {
                            str(side): trade_metrics(
                                monitor.select(
                                    timestamp, profile=self.current.id, side=side
                                )
                            )
                            for side in (1, -1)
                        },
                    },
                )
        eligible = [
            self.profiles[p]
            for p in self.registry.eligible(timestamp)
            if p != "NO_TRADE"
            and regime["regime"] in self.profiles[p].compatible_regimes
            and timestamp >= self.disabled_until.get(p, 0)
        ]
        stable = (
            regime["duration_ns"] >= policy["minimum_regime_bars"] * 15 * 60 * 10**9
            and regime["confidence"] >= policy["minimum_regime_confidence"]
        )
        if (
            hard
            or timestamp < self.symbol_disabled_until
            or regime["regime"] in ("MARKET_STRESS", "UNKNOWN")
        ):
            candidate, risk, reason = NO_TRADE, 0, "safety_disable:" + state
        elif (
            self.current != NO_TRADE
            and regime["regime"] not in self.current.compatible_regimes
        ):
            candidate, risk, reason = NO_TRADE, 0, "incompatible_regime"
        elif self.current.id not in self.registry.eligible(timestamp):
            candidate, risk, reason = NO_TRADE, 0, "profile_not_eligible_at_timestamp"
        elif self.current == NO_TRADE and eligible and stable:
            # Fixed preference by family/id; no ranking by recent winners
            candidate = min(eligible, key=lambda p: (p.family, p.id))
            risk, reason = 0.5, "enter_prevalidated_shadow_with_stable_regime"
        elif self.current != NO_TRADE:
            risk = (
                0.5 if state in ("EDGE_DEGRADING", "INSUFFICIENT_DATA") else self.risk
            )
            own = monitor.select(timestamp, profile=self.current.id)
            if (
                state == "NORMAL_VARIANCE"
                and len(own) >= 60
                and drift
                and drift["metrics"]["expectancy_r"] > 0.1
            ):
                risk, reason = 1.0, "restore_within_validated_risk_bound"
            for side in (1, -1):
                side_trades = monitor.select(
                    timestamp, profile=self.current.id, side=side
                )
                if len(side_trades) >= 30:
                    net = sum(float(t["net_pnl"]) for t in side_trades)
                    if net < -100:
                        self.side_disabled[(self.current.id, side)] = (
                            timestamp + 30 * DAY
                        )
        safety_exit = candidate == NO_TRADE
        recent = [s for s in self.switches if s["timestamp"] >= timestamp - 30 * DAY]
        if candidate.id != self.current.id and not safety_exit:
            if (
                self.last_switch is not None
                and timestamp - self.last_switch < policy["minimum_switch_hours"] * HOUR
            ):
                candidate, risk, reason = (
                    self.current,
                    self.risk,
                    "minimum_dwell_hysteresis",
                )
            elif len(recent) >= policy["maximum_switches_per_month"]:
                candidate, risk, reason = NO_TRADE, 0, "switch_budget_exhausted"
        if risk not in policy["risk_bounds"]:
            raise ValueError("Risk outside validated discrete bounds")
        event = {
            "timestamp": timestamp,
            "old_profile": self.current.id,
            "new_profile": candidate.id,
            "regime": regime["regime"],
            "regime_confidence": regime["confidence"],
            "regime_start_ns": regime.get("start_ns", timestamp),
            "regime_duration_ns": regime["duration_ns"],
            "features": regime.get("features", {}),
            "performance_state": state,
            "reason": reason,
            "evidence": evidence,
            "old_risk": self.risk,
            "risk": risk,
            "disabled_sides": [
                side
                for (p, side), end in self.side_disabled.items()
                if p == candidate.id and timestamp < end
            ],
        }
        changed = candidate.id != self.current.id
        if changed:
            self.last_switch = timestamp
            self.switches.append(event)
        if changed or risk != self.risk or drift:
            self.decisions.append(event)
        self.current, self.risk = candidate, risk
        return event

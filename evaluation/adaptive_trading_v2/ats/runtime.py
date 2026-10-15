"""One causal strategy implementation for historical and replayed public shadow events."""

from decimal import Decimal as D

import pandas as pd

from .common import DAY, config
from .controller import Controller
from .evidence import EvidenceProvider
from .native import USDT, VENUE, EdgeStrategy
from .profiles import library, signal
from .regime import invalidated


class AdaptiveStrategy(EdgeStrategy):
    def __init__(self, inst, candidate, start, end, references, features, evidence):
        super().__init__(inst, candidate, start, end, references)
        self.features = features
        self.fixed = candidate["id"]
        self.policy = candidate.get("exit_policy", "ENTRY_ONLY")
        self.profiles = library()
        self.cfg = dict(config())
        self.controller = Controller(str(inst.raw_symbol), EvidenceProvider(evidence))
        self.incompatible_hours = 0
        self.monitor_trades = []
        self.exposure_daily = []
        self.exposure_accumulator = [0.0, 0.0, 0.0, 0.0, 0]
        self.passive_month = None
        self.passive_weight = 0.0
        self.last_close = None
        if not candidate.get("liquidate", True):
            self.final_quote = -1

    def on_bar(self, bar):
        timestamp = bar.ts_event
        f = self.features[timestamp]
        c = float(bar.close)
        self.last_close = c
        self.previous_volume = bar.volume.as_decimal()
        if not self.start <= timestamp < self.end:
            return
        balance = self.cache.account_for_venue(VENUE).balance_total(USDT).as_decimal()
        unrealized = (
            self.signed_qty * (D(str(c)) - self.active["entry_price"])
            if self.active
            else D(0)
        )
        equity = float(balance + unrealized)
        if self.active:
            side = self.active["side"]
            qty = float(self.active["quantity"])
            moves = [
                side * (float(price) - float(self.active["entry_price"])) * qty
                for price in (bar.high, bar.low)
            ]
            self.active["mae"] = min(self.active["mae"], *moves)
            self.active["mfe"] = max(self.active["mfe"], *moves)
        active_profile = self.active["profile"] if self.active else None
        if self.fixed == "ADAPTIVE":
            profile_id, risk, allowed, safety = self.controller.decide(
                timestamp, f, self.monitor_trades, self.daily, active_profile
            )
        else:
            profile_id, risk, allowed, safety = (
                self.fixed,
                1.0,
                self.fixed != "NO_TRADE",
                False,
            )
        a = self.exposure_accumulator
        a[0] += abs(float(self.signed_qty)) * c
        a[1] += bool(self.active)
        a[2] += (
            float(self.active["quantity"] * self.active["entry_price"])
            if self.active
            else 0
        )
        a[3] += profile_id == "NO_TRADE"
        a[4] += 1
        if f.get("day_end", (timestamp + 10**6) % DAY == 0):
            self.daily[timestamp + 10**6] = equity
            self.exposure_daily.append([timestamp + 10**6, *[v / a[4] for v in a[:4]]])
            self.exposure_accumulator = [0.0, 0.0, 0.0, 0.0, 0]
        if self.fixed == "PASSIVE":
            self.passive(timestamp, f)
            return
        profile = self.profiles[profile_id]
        if self.active:
            held = self.profiles[active_profile]
            if f["new_hour"]:
                self.incompatible_hours = (
                    self.incompatible_hours + 1
                    if f["regime"] not in held.compatible_regimes
                    else 0
                )
            forced = invalidated(self.policy, held, f, self.incompatible_hours)
            reasons = ["SAFETY"] if safety else []
            if forced:
                reasons.append("REGIME_INVALIDATED")
            if (held.minutes == 15 or f["new_hour"]) and f["ready"]:
                self.age += 1
                prefix = f"{held.minutes}_{held.lookback}_"
                side = self.active["side"]
                proposal = c - side * held.stop_atr * f[prefix + "atr"]
                self.stop = (
                    max(self.stop, proposal) if side > 0 else min(self.stop, proposal)
                )
                if side * (c - self.stop) <= 0:
                    reasons.append("TRAILING_STOP")
                if (
                    c < f[prefix + "exit_low"]
                    if side > 0
                    else c > f[prefix + "exit_high"]
                ):
                    reasons.append("OPPOSITE_CHANNEL")
                if self.age >= held.maximum_age:
                    reasons.append("MAXIMUM_AGE")
            if reasons:
                self.pending = {
                    "action": "exit",
                    "signal_ns": timestamp,
                    "regime": f["regime"],
                    "exit_reasons": reasons,
                }
        elif (
            allowed
            and risk
            and profile_id != "NO_TRADE"
            and (profile.minutes == 15 or f["new_hour"])
        ):
            regime_key = "raw_regime" if self.policy == "V1_IMMEDIATE" else "regime"
            confidence_key = (
                "raw_confidence" if self.policy == "V1_IMMEDIATE" else "confidence"
            )
            if (
                f[regime_key] not in profile.compatible_regimes
                or f[confidence_key] < config()["regime"]["entry_confidence"]
            ):
                return
            side = signal(profile, f)
            if side:
                scale = (
                    min(1.0, 1.0 / f["vol_ratio_60"])
                    if profile.family == "volatility_scaled_trend"
                    else 1.0
                )
                self.cfg["risk_per_trade"] = config()["risk_per_trade"] * risk * scale
                prefix = f"{profile.minutes}_{profile.lookback}_"
                self.pending = {
                    "action": "entry",
                    "side": side,
                    "distance": profile.stop_atr * f[prefix + "atr"],
                    "signal_ns": timestamp,
                    "regime": f[regime_key],
                    "profile": profile_id,
                    "risk_multiplier": risk * scale,
                    "regime_confidence": f[confidence_key],
                }
                self.signal_count += 1

    def passive(self, timestamp, f):
        month = pd.Timestamp(timestamp, unit="ns", tz="UTC").strftime("%Y-%m")
        if month != self.passive_month:
            self.passive_month, self.passive_weight = month, f.get("passive_weight", 0)
            if self.active:
                self.pending = {
                    "action": "exit",
                    "signal_ns": timestamp,
                    "regime": "PASSIVE",
                    "exit_reasons": ["MONTHLY_REBALANCE"],
                }
                return
        if not self.active and self.passive_weight > 0:
            self.cfg["risk_per_trade"] = config()["risk_per_trade"]
            self.pending = {
                "action": "entry",
                "side": 1,
                "distance": config()["risk_per_trade"]
                * float(f["close"])
                / self.passive_weight,
                "signal_ns": timestamp,
                "regime": "PASSIVE",
                "profile": "PASSIVE",
                "risk_multiplier": 1.0,
                "regime_confidence": 1.0,
            }

    def on_order_filled(self, event):
        context = self.contexts[str(event.client_order_id)]
        super().on_order_filled(event)
        if context["action"] == "entry":
            for key in ("profile", "risk_multiplier", "regime_confidence"):
                self.active[key] = context[key]
            self.active.update(
                {
                    "symbol": str(self.inst.raw_symbol),
                    "mae": 0.0,
                    "mfe": 0.0,
                    "initial_risk": self.active["quantity"]
                    * D(str(context["distance"])),
                }
            )
            self.incompatible_hours = 0
        else:
            trade = self.trades[-1]
            trade["exit_reasons"] = context.get("exit_reasons", ["SCHEDULED_END"])
            trade["turnover"] = trade["quantity"] * (
                trade["entry_price"] + trade["exit_price"]
            )

    def on_position_closed(self, event):
        position = self.cache.position(event.position_id)
        trade = next(
            t for t in reversed(self.trades) if t["entry_ns"] == position.ts_opened
        )
        trade["funding"] = sum(
            (a.pnl_change.as_decimal() for a in position.adjustments() if a.pnl_change),
            D(0),
        )
        trade["net_pnl"] = (
            trade["gross_pnl"] - trade["slippage"] - trade["fees"] + trade["funding"]
        )
        if abs(trade["net_pnl"] - position.realized_pnl.as_decimal()) > D("0.00001"):
            raise RuntimeError("Monitor/native position accounting disagreement")
        self.monitor_trades.append(trade)


def factory(features, evidence=()):
    def create(inst, candidate, start, end, references):
        return AdaptiveStrategy(
            inst, candidate, start, end, references, features, evidence
        )

    return create


def candidate(profile, policy="ENTRY_ONLY", liquidate=True):
    return {
        "id": profile,
        "family": "v2",
        "minutes": 15,
        "lookback": 48,
        "exit_policy": policy,
        "liquidate": liquidate,
    }

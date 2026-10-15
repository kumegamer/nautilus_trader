"""Native historical research execution; no live clients or external order endpoints."""

from decimal import Decimal as D

from .common import DAY, config
from .native import USDT, VENUE, ExecutionStrategy
from .profiles import library, signal


class AlphaStrategy(ExecutionStrategy):
    def __init__(self, inst, candidate, start, end, references, features):
        super().__init__(inst, candidate, start, end, references)
        self.features = features
        self.profile = library()[candidate["id"]]
        self.cfg = dict(config())
        self.exposure_daily = []
        self.accumulator = [0.0, 0.0, 0.0, 0.0, 0]
        self.last_close = None
        if not candidate.get("liquidate", True):
            self.final_quote = -1

    def on_bar(self, bar):
        t = bar.ts_event
        f = self.features[t]
        c = float(bar.close)
        self.last_close = c
        self.previous_volume = bar.volume.as_decimal()
        if not self.start <= t < self.end:
            return
        balance = self.cache.account_for_venue(VENUE).balance_total(USDT).as_decimal()
        unrealized = (
            self.signed_qty * (D(str(c)) - self.active["entry_price"])
            if self.active
            else D(0)
        )
        equity = float(balance + unrealized)
        a = self.accumulator
        a[0] += abs(float(self.signed_qty)) * c
        a[1] += bool(self.active)
        a[2] += (
            float(self.active["quantity"] * self.active["entry_price"])
            if self.active
            else 0
        )
        a[4] += 1
        if (t + 10**6) % DAY == 0:
            self.daily[t + 10**6] = equity
            self.exposure_daily.append([t + 10**6, *[v / a[4] for v in a[:4]]])
            self.accumulator = [0.0, 0.0, 0.0, 0.0, 0]
        p = self.profile
        if self.active:
            self.age += 1
            s = p.side
            q = float(self.active["quantity"])
            moves = [
                s * (float(price) - float(self.active["entry_price"])) * q
                for price in (bar.high, bar.low)
            ]
            self.active["mae"] = min(self.active["mae"], *moves)
            self.active["mfe"] = max(self.active["mfe"], *moves)
            reasons = []
            if p.exit in ("trailing", "structure", "contraction"):
                proposal = c - s * p.stop_atr * f["atr"]
                self.stop = (
                    max(self.stop, proposal) if s > 0 else min(self.stop, proposal)
                )
            if s * (c - self.stop) <= 0:
                reasons.append("CLOSE_STOP")
            if self.age >= p.max_age:
                reasons.append("TIME_STOP")
            if p.exit == "equilibrium" and s * (c - f["equilibrium"]) >= 0:
                reasons.append("EQUILIBRIUM")
            if p.exit == "structure" and (
                c < f["exit_low"] if s > 0 else c > f["exit_high"]
            ):
                reasons.append("STRUCTURE_INVALIDATION")
            if p.exit == "contraction" and self.age >= 8 and f["vol_ratio"] < 0.7:
                reasons.append("VOLATILITY_CONTRACTION")
            if reasons:
                self.pending = {
                    "action": "exit",
                    "signal_ns": t,
                    "regime": f["regime"],
                    "exit_reasons": reasons,
                }
        elif signal(p, f, str(self.inst.raw_symbol)):
            scale = min(1.0, 0.40 / max(float(f["annual_vol"]), 1e-8))
            self.cfg["risk_per_trade"] = config()["risk_per_trade"] * scale
            self.pending = {
                "action": "entry",
                "side": p.side,
                "distance": p.stop_atr * f["atr"],
                "signal_ns": t,
                "regime": f["regime"],
                "risk_multiplier": scale,
            }
            self.signal_count += 1

    def on_order_filled(self, event):
        context = self.contexts[str(event.client_order_id)]
        super().on_order_filled(event)
        if context["action"] == "entry":
            self.active.update(
                profile=self.profile.id,
                symbol=str(self.inst.raw_symbol),
                mae=0.0,
                mfe=0.0,
                initial_risk=self.active["quantity"] * D(str(context["distance"])),
                risk_multiplier=context["risk_multiplier"],
            )
        else:
            self.trades[-1]["exit_reasons"] = context.get(
                "exit_reasons", ["SCHEDULED_END"]
            )
            self.trades[-1]["turnover"] = self.trades[-1]["quantity"] * (
                self.trades[-1]["entry_price"] + self.trades[-1]["exit_price"]
            )


def factory(features):
    def create(inst, candidate, start, end, references):
        return AlphaStrategy(inst, candidate, start, end, references, features)

    return create

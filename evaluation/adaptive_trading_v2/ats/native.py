"""Native next-open execution/accounting, reused from frozen Edge Discovery evidence.

Sources: adaptive v1 8acc5c4, edge discovery 3c669f9. V2 execution-local copy.
The source branch is never checked out or modified. Adaptive runtime is injected here.
"""

import hashlib
from collections import OrderedDict, deque
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from itertools import pairwise

import pandas as pd
from nautilus_trader.backtest import BacktestEngine
from nautilus_trader.common import LoggerConfig, LogLevel
from nautilus_trader.config import BacktestEngineConfig
from nautilus_trader.execution import MakerTakerFeeModel
from nautilus_trader.indicators import (
    AverageTrueRange,
    BollingerBands,
    ExponentialMovingAverage,
)
from nautilus_trader.model import (
    AccountType,
    Bar,
    BarType,
    CryptoPerpetual,
    Currency,
    FundingRateUpdate,
    InstrumentId,
    MarkPriceUpdate,
    Money,
    OmsType,
    OrderSide,
    PositionId,
    Price,
    Quantity,
    QuoteTick,
    Symbol,
    Venue,
)
from nautilus_trader.trading import Strategy

from .common import config, ns

D = Decimal
DAY = 86400 * 10**9
VENUE = Venue("BINANCE")
USDT = Currency.from_str("USDT")
_EVENT_CACHE = OrderedDict()


def quantize(value, step, upward=False):
    value, step = D(str(value)), D(str(step))
    rounding = ROUND_CEILING if upward else ROUND_FLOOR
    return (value / step).to_integral_value(rounding=rounding) * step


def instrument(symbol):
    spec = config()["instrument_specs"][symbol]
    tick, step = D(spec["tick"]), D(spec["step"])
    return CryptoPerpetual(
        instrument_id=InstrumentId.from_str(f"{symbol}-PERP.BINANCE"),
        raw_symbol=Symbol(symbol),
        base_currency=Currency.from_str(symbol.removesuffix("USDT")),
        quote_currency=USDT,
        settlement_currency=USDT,
        is_inverse=False,
        price_precision=-tick.as_tuple().exponent,
        size_precision=-step.as_tuple().exponent,
        price_increment=Price.from_str(str(tick)),
        size_increment=Quantity.from_str(str(step)),
        min_quantity=Quantity.from_str(str(step)),
        min_notional=Money(config()["minimum_notional"], USDT),
        margin_init=D("1"),
        margin_maint=D("0.05"),
        ts_event=0,
        ts_init=0,
    )


def native_bar_type(inst, minutes):
    aggregation = "1-HOUR" if minutes == 60 else f"{minutes}-MINUTE"
    return BarType.from_str(f"{inst.id}-{aggregation}-LAST-EXTERNAL")


class EdgeStrategy(Strategy):
    """Four fixed signal mechanisms; all orders are native Nautilus market orders."""

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, inst, candidate, start, end, references):
        super().__init__()
        self.inst, self.p, self.start, self.end = inst, candidate, start, end
        self.references = references
        self.final_quote = max(references, default=-1)
        self.cfg = config()
        self.minutes = candidate["minutes"]
        self.bar_type = native_bar_type(inst, self.minutes)
        self.atr = AverageTrueRange(14)
        self.trend = ExponentialMovingAverage(200)
        self.equilibrium = ExponentialMovingAverage(candidate["lookback"])
        self.bands = BollingerBands(candidate["lookback"], candidate.get("band_k", 2.0))
        self.closes, self.highs, self.lows = (
            deque(maxlen=201),
            deque(maxlen=100),
            deque(maxlen=100),
        )
        self.widths = deque(maxlen=96)
        self.armed = 0
        self.pending = None
        self.contexts = {}
        self.signed_qty = D(0)
        self.active = None
        self.stop = None
        self.age = 0
        self.previous_volume = D(0)
        self.trades, self.fills, self.errors = [], [], []
        self.daily = {start: float(self.cfg["capital_per_symbol"])}
        self.signal_count = 0
        self.skipped_size = 0
        self.last_bar_ts = None

    def on_start(self):
        self.subscribe_bars(self.bar_type)
        self.subscribe_quotes(self.inst.id)

    def on_bar(self, bar):
        c, h, low = float(bar.close), float(bar.high), float(bar.low)
        n = self.p["lookback"]
        previous_high = max(list(self.highs)[-n:]) if len(self.highs) >= n else None
        previous_low = min(list(self.lows)[-n:]) if len(self.lows) >= n else None
        exit_high = max(list(self.highs)[-(n // 2) :]) if len(self.highs) >= n else None
        exit_low = min(list(self.lows)[-(n // 2) :]) if len(self.lows) >= n else None
        old_width = self.widths[-1] if self.widths else 0.0
        mean_width = sum(self.widths) / len(self.widths) if self.widths else 0.0
        if (
            self.last_bar_ts is not None
            and bar.ts_event - self.last_bar_ts != self.minutes * 60 * 10**9
        ):
            raise ValueError("Unexpected bar gap")
        self.last_bar_ts = bar.ts_event
        for indicator in (self.atr, self.trend, self.equilibrium, self.bands):
            indicator.handle_bar(bar)
        self.closes.append(c)
        self.highs.append(h)
        self.lows.append(low)
        self.previous_volume = bar.volume.as_decimal()
        width = (self.bands.upper - self.bands.lower) / c
        self.widths.append(width)
        if not all(x.initialized for x in (self.atr, self.trend, self.bands)):
            return
        recent = list(self.closes)[-49:]
        movement = sum(abs(b - a) for a, b in pairwise(recent))
        efficiency = abs(recent[-1] - recent[0]) / movement if movement else 0.0
        regime = (
            "trend"
            if efficiency >= 0.35
            else "range"
            if efficiency <= 0.20
            else "transition"
        )
        atr, trend, eq = self.atr.value, self.trend.value, self.equilibrium.value
        if atr <= 0:
            return
        family = self.p["family"]
        stop_atr = self.p.get("stop_atr", 2.0 if family == "mean_reversion" else 2.5)
        side = 1 if self.signed_qty > 0 else -1 if self.signed_qty < 0 else 0
        close_position = False
        if side:
            self.age += 1
            if family in ("trend_breakout", "volatility_breakout"):
                proposal = c - side * stop_atr * atr
                self.stop = (
                    max(self.stop, proposal) if side > 0 else min(self.stop, proposal)
                )
                close_position = c < exit_low if side > 0 else c > exit_high
            elif family == "trend_pullback":
                close_position = (
                    (c >= eq or c <= trend) if side > 0 else (c <= eq or c >= trend)
                )
            else:
                close_position = (
                    c >= self.bands.middle if side > 0 else c <= self.bands.middle
                )
                close_position |= efficiency > 0.35
            close_position |= side * (c - self.stop) <= 0 or self.age >= 96
        entry_side = 0
        if family == "trend_breakout":
            entry_side = 1 if c > previous_high else -1 if c < previous_low else 0
        elif family == "trend_pullback":
            pullback = self.p["pullback_atr"] * atr
            if c > trend and eq > trend and c < eq - pullback:
                entry_side = 1
            elif c < trend and eq < trend and c > eq + pullback:
                entry_side = -1
        elif family == "mean_reversion":
            if efficiency <= 0.20 and abs(c - trend) <= 3 * atr:
                entry_side = (
                    1 if c < self.bands.lower else -1 if c > self.bands.upper else 0
                )
        else:
            if old_width and old_width <= self.p["compression"] * mean_width:
                self.armed = 6
            else:
                self.armed = max(0, self.armed - 1)
            if self.armed and width > old_width:
                entry_side = 1 if c > previous_high else -1 if c < previous_low else 0
        if self.start <= bar.ts_event < self.end:
            if close_position:
                self.pending = {
                    "action": "exit",
                    "signal_ns": bar.ts_event,
                    "regime": regime,
                }
            elif not side and entry_side:
                self.pending = {
                    "action": "entry",
                    "side": entry_side,
                    "distance": stop_atr * atr,
                    "signal_ns": bar.ts_event,
                    "regime": regime,
                }
                self.signal_count += 1
            if (bar.ts_event + 10**6) % DAY == 0:
                balance = (
                    self.cache.account_for_venue(VENUE).balance_total(USDT).as_decimal()
                )
                unrealized = D(0)
                if self.active:
                    unrealized = self.signed_qty * (
                        D(str(c)) - self.active["entry_price"]
                    )
                self.daily[bar.ts_event + 10**6] = float(balance + unrealized)

    def on_quote(self, quote):
        if quote.ts_event not in self.references:
            raise ValueError("Quote has no declared open reference")
        reference = self.references[quote.ts_event]
        if quote.ts_event == self.final_quote:
            self.pending = (
                {
                    "action": "exit",
                    "signal_ns": quote.ts_event - 2 * 10**6,
                    "regime": "scheduled_end",
                }
                if self.signed_qty
                else None
            )
        if self.pending is None:
            return
        context, self.pending = self.pending, None
        if not context["signal_ns"] < quote.ts_event:
            raise ValueError("Signal execution timestamp leakage")
        context["reference"] = reference
        if context["action"] == "exit":
            if not self.signed_qty:
                return
            quantity = abs(self.signed_qty)
            side = -1 if self.signed_qty > 0 else 1
        else:
            side = context["side"]
            executable = (
                quote.ask_price.as_decimal()
                if side > 0
                else quote.bid_price.as_decimal()
            )
            capital = D(str(self.cfg["capital_per_symbol"]))
            risk_qty = (
                capital
                * D(str(self.cfg["risk_per_trade"]))
                / D(str(context["distance"]))
            )
            cap_qty = capital * D(str(self.cfg["notional_cap_fraction"])) / executable
            volume_qty = self.previous_volume * D(str(self.cfg["participation_cap"]))
            quantity = quantize(
                min(risk_qty, cap_qty, volume_qty),
                self.inst.size_increment.as_decimal(),
            )
            balance = (
                self.cache.account_for_venue(VENUE).balance_free(USDT).as_decimal()
            )
            if (
                quantity <= 0
                or quantity * executable < self.cfg["minimum_notional"]
                or quantity * executable > balance * D("0.95")
            ):
                self.skipped_size += 1
                return
        order = self.order_factory.market(
            self.inst.id,
            OrderSide.BUY if side > 0 else OrderSide.SELL,
            Quantity.from_str(str(quantity)),
            reduce_only=context["action"] == "exit",
        )
        self.contexts[str(order.client_order_id)] = context
        position_id = (
            PositionId(self.active["position_id"])
            if context["action"] == "exit"
            else None
        )
        self.submit_order(order, position_id=position_id)

    def on_order_filled(self, event):
        context = self.contexts[str(event.client_order_id)]
        quantity, price = event.last_qty.as_decimal(), event.last_px.as_decimal()
        sign = 1 if event.order_side == OrderSide.BUY else -1
        fee = event.commission.as_decimal() if event.commission else D(0)
        slip = quantity * sign * (price - context["reference"])
        self.fills.append(
            {
                "ts_ns": event.ts_event,
                "signal_ns": context["signal_ns"],
                "side": sign,
                "quantity": str(quantity),
                "price": str(price),
                "reference": str(context["reference"]),
                "fee": str(fee),
                "slippage": str(slip),
                "action": context["action"],
                "position_id": str(event.position_id),
            }
        )
        if context["action"] == "entry":
            if self.active is not None:
                self.errors.append("Unexpected partial entry or overlapping position")
                return
            self.active = {
                "entry_ns": event.ts_event,
                "side": sign,
                "quantity": quantity,
                "entry_price": price,
                "entry_reference": context["reference"],
                "fees": fee,
                "slippage": slip,
                "regime": context["regime"],
                "position_id": str(event.position_id),
            }
            self.stop = float(price) - sign * context["distance"]
            self.age = 0
        else:
            if self.active is None or quantity != self.active["quantity"]:
                self.errors.append("Unexpected partial close")
                return
            trade = self.active
            trade["exit_ns"] = event.ts_event
            trade["exit_price"] = price
            trade["fees"] += fee
            trade["slippage"] += slip
            trade["gross_pnl"] = (
                quantity
                * trade["side"]
                * (context["reference"] - trade["entry_reference"])
            )
            self.trades.append(trade)
            self.active = None
        self.signed_qty += sign * quantity

    def on_order_rejected(self, event):
        self.errors.append(str(event))

    def on_order_denied(self, event):
        self.errors.append(str(event))


def run(
    candidate,
    symbol,
    period,
    bars,
    rates,
    scenario="base",
    strategy_factory=None,
    *,
    start_ns=None,
    end_ns=None,
    public_quotes=None,
):
    cfg = config()
    start, end = map(ns, cfg["periods"][period])
    start = start if start_ns is None else start_ns
    end = end if end_ns is None else end_ns
    inst = instrument(symbol)
    spec = cfg["scenarios"][scenario]
    slip = D(str(spec["slippage_bps"])) / 10000
    engine = BacktestEngine(
        BacktestEngineConfig(
            logging=LoggerConfig(stdout_level=LogLevel.ERROR, is_colored=False),
            run_analysis=False,
        )
    )
    engine.add_venue(
        VENUE,
        OmsType.HEDGING,
        AccountType.MARGIN,
        [Money(cfg["capital_per_symbol"], USDT)],
        base_currency=USDT,
        default_leverage=D(1),
        fee_model=MakerTakerFeeModel(
            maker_rate=D(0),
            taker_rate=D(cfg["taker_fee"]) * D(str(spec["fee_multiplier"])),
        ),
        bar_execution=False,
        trade_execution=False,
        use_random_ids=False,
        liquidity_consumption=True,
    )
    engine.add_instrument(inst)
    minutes = candidate["minutes"]
    bar_type = native_bar_type(inst, minutes)
    cache_key = None
    if public_quotes is None:
        fingerprint = hashlib.sha256(
            pd.util.hash_pandas_object(bars, index=False).to_numpy().tobytes()
            + pd.util.hash_pandas_object(rates, index=False).to_numpy().tobytes()
        ).hexdigest()
        cache_key = (symbol, scenario, start, end, minutes, fingerprint)
    if cache_key is not None and cache_key in _EVENT_CACHE:
        events, references = _EVENT_CACHE[cache_key]
        _EVENT_CACHE.move_to_end(cache_key)
    else:
        events, references = [], {}
        for row in bars.itertuples(index=False):
            t = int(row.t)
            close_t = int(
                getattr(row, "available_ns", t + minutes * 60 * 10**9 - 10**6)
            )
            events.append(
                Bar(
                    bar_type,
                    inst.make_price(row.open),
                    inst.make_price(row.high),
                    inst.make_price(row.low),
                    inst.make_price(row.close),
                    inst.make_qty(row.volume),
                    close_t,
                    close_t,
                )
            )
            if t >= start and public_quotes is None:
                quote_t = t + 10**6
                reference = D(str(row.open))
                references[quote_t] = reference
                bid = quantize(
                    reference * (1 - slip), inst.price_increment.as_decimal()
                )
                ask = quantize(
                    reference * (1 + slip),
                    inst.price_increment.as_decimal(),
                    upward=True,
                )
                depth = inst.make_qty(1000000)
                events.append(
                    QuoteTick(
                        inst.id,
                        Price.from_str(str(bid)),
                        Price.from_str(str(ask)),
                        depth,
                        depth,
                        quote_t,
                        quote_t,
                    )
                )
        if public_quotes is not None:
            for q in public_quotes:
                quote_t = int(q["observed_ns"])
                reference = (D(str(q["bid"])) + D(str(q["ask"]))) / 2
                references[quote_t] = reference
                bid = quantize(
                    D(str(q["bid"])) * (1 - slip), inst.price_increment.as_decimal()
                )
                ask = quantize(
                    D(str(q["ask"])) * (1 + slip),
                    inst.price_increment.as_decimal(),
                    upward=True,
                )
                events.append(
                    QuoteTick(
                        inst.id,
                        Price.from_str(str(bid)),
                        Price.from_str(str(ask)),
                        inst.make_qty(q["bid_qty"]),
                        inst.make_qty(q["ask_qty"]),
                        quote_t,
                        quote_t,
                    )
                )
        for row in rates.itertuples(index=False):
            t = int(row.t)
            events.append(MarkPriceUpdate(inst.id, inst.make_price(row.mark), t, t))
            events.append(
                FundingRateUpdate(
                    inst.id,
                    D(str(row.rate)),
                    t,
                    t,
                    interval=int(row.interval) * 60,
                    next_funding_ns=t,
                )
            )
        events.sort(key=lambda e: e.ts_init)
        if cache_key is not None:
            _EVENT_CACHE[cache_key] = (events, references)
            if len(_EVENT_CACHE) > 3:
                _EVENT_CACHE.popitem(last=False)
    strategy = (strategy_factory or EdgeStrategy)(
        inst, candidate, start, end, references
    )
    try:
        engine.add_data(events)
        engine.add_strategy(strategy)
        engine.run()
        all_positions = engine.cache.positions(instrument_id=inst.id)
        positions = [p for p in all_positions if not p.is_open]
        if (
            strategy.errors
            or candidate.get("liquidate", True)
            and (strategy.active or any(p.is_open for p in all_positions))
        ):
            raise RuntimeError(f"Native execution integrity failed: {strategy.errors}")
        by_entry = {p.ts_opened: p for p in positions}
        if len(by_entry) != len(strategy.trades):
            raise RuntimeError("Native position/trade count mismatch")
        for trade in strategy.trades:
            p = by_entry[trade["entry_ns"]]
            funding = sum(
                (a.pnl_change.as_decimal() for a in p.adjustments() if a.pnl_change),
                D(0),
            )
            trade["funding"] = funding
            trade["net_pnl"] = (
                trade["gross_pnl"] - trade["slippage"] - trade["fees"] + funding
            )
            trade["duration_ns"] = trade["exit_ns"] - trade["entry_ns"]
            if abs(trade["net_pnl"] - p.realized_pnl.as_decimal()) > D("0.00001"):
                raise RuntimeError(
                    f"Native position PnL mismatch: {trade}, {p.realized_pnl}"
                )
        net = sum((t["net_pnl"] for t in strategy.trades), D(0))
        account = engine.cache.account_for_venue(VENUE).balance_total(USDT).as_decimal()
        open_cost = sum(
            (p.realized_pnl.as_decimal() for p in all_positions if p.is_open), D(0)
        )
        discrepancy = account - D(cfg["capital_per_symbol"]) - net - open_cost
        if abs(discrepancy) > D("0.00001"):
            raise RuntimeError(f"Native account PnL mismatch: {discrepancy}")
        unrealized = (
            strategy.signed_qty
            * (D(str(strategy.last_close)) - strategy.active["entry_price"])
            if strategy.active
            else D(0)
        )
        strategy.daily[end] = float(account + unrealized)
        trades = [
            {k: float(v) if isinstance(v, D) else v for k, v in t.items()}
            for t in strategy.trades
        ]
        return {
            "candidate": candidate["id"],
            "family": candidate["family"],
            "symbol": symbol,
            "period": period,
            "scenario": scenario,
            "trades": trades,
            "fills": strategy.fills,
            "daily": [[t, e] for t, e in sorted(strategy.daily.items())],
            "native_balance": str(account),
            "funding_events": [
                {
                    "timestamp": a.ts_event,
                    "amount": str(a.pnl_change.as_decimal()),
                    "position_id": str(p.id),
                }
                for p in all_positions
                for a in p.adjustments()
                if a.pnl_change
            ],
            "reconciliation_difference": str(discrepancy),
            "signals": strategy.signal_count,
            "size_skips": strategy.skipped_size,
            "exposure_daily": strategy.exposure_daily,
            "open_position": {
                k: str(v) if isinstance(v, D) else v for k, v in strategy.active.items()
            }
            if strategy.active
            else None,
            "initial_eligibility": getattr(strategy, "initial_eligibility", {}),
            "decisions": strategy.controller.decisions,
            "switches": strategy.controller.switches,
            "degradation": strategy.controller.degradation,
            "research": strategy.controller.research,
            "promotions": getattr(strategy, "promotion_events", []),
            "regime_transitions": getattr(strategy, "regime_transitions", []),
            "adaptive_state": strategy.adaptive_state()
            if hasattr(strategy, "adaptive_state")
            else None,
        }
    finally:
        engine.dispose()

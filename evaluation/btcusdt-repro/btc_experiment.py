"""Reconstructed fixed BTCUSDT experiment; uses the delivered Nautilus runtime.

No installs, builds, live trading, or writes inside the NautilusTrader checkout.
Run with python/.venv/bin/python -B btc_experiment.py --output <directory>.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

from nautilus_trader.backtest import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig, StrategyConfig
from nautilus_trader.execution import FillModel, MakerTakerFeeModel
from nautilus_trader.model import (
    AccountType, Bar, BarType, BookOrder, BookType, CryptoPerpetual, Currency,
    InstrumentId, Money, OmsType, OrderBook, OrderSide, Price, Quantity,
    QuoteTick, Symbol, TraderId, Venue,
)
from nautilus_trader.trading import Strategy

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "btcusdt-repro" / "BTCUSDT-5m-2025-01.csv"
QTY, FEE, SLIP, TICK = D("0.010"), D("0.0005"), D("0.0001"), D("0.1")
USDT, BTC = Currency.from_str("USDT"), Currency.from_str("BTC")
VENUE = Venue("BINANCE")
IID = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")
BT = BarType.from_str(f"{IID}-5-MINUTE-LAST-EXTERNAL")


def dec(value):
    return value.as_decimal()


def events(value):
    attribute = value.events
    return attribute() if callable(attribute) else attribute


def text_decimal(value):
    value = D(value)
    return "0" if not value else format(value.normalize(), "f")


def modeled_price(base, sign):
    raw = base * (1 + D(sign) * SLIP)
    rounding = ROUND_CEILING if sign == 1 else ROUND_FLOOR
    return (raw / TICK).to_integral_value(rounding=rounding) * TICK


class SMASeededEMA:
    """Only consumed closes enter the seed and recursive state."""
    def __init__(self, period):
        self.period, self.seed, self.value = period, [], None

    def update(self, close):
        if self.value is None:
            self.seed.append(close)
            if len(self.seed) == self.period:
                self.value = sum(self.seed) / self.period
        else:
            self.value += (close - self.value) * (2.0 / (self.period + 1))


class AdverseBasisPointFill(FillModel):
    """Synthetic liquidity at exactly 1 bp adverse, rounded outward to tick."""
    def get_orderbook_for_fill_simulation(self, instrument, order, best_bid, best_ask):
        assert best_bid is not None and best_ask is not None
        assert dec(best_bid) == dec(best_ask), "Only zero-spread execution reference quotes"
        book = OrderBook(instrument.id, BookType.L2_MBP)
        for sign, side in [(1, OrderSide.SELL), (-1, OrderSide.BUY)]:
            px = Price.from_str(format(modeled_price(dec(best_bid), sign), ".1f"))
            book.add(BookOrder(side, px, Quantity.from_str("100.000"), sign + 2), 0, 0, 0)
        return book


class ExperimentStrategy(Strategy):
    def __init__(self, rows):
        super().__init__(StrategyConfig(log_events=False, log_commands=False))
        self.rows = rows
        self.fast, self.slow = SMASeededEMA(20), SMASeededEMA(50)
        self.previous = None
        self.pending = None
        self.reverse = None
        self.contexts = {}
        self.signals, self.orders, self.fills, self.trades, self.equity, self.indicators = [], [], [], [], [], []
        self.position, self.entry = 0, None
        self.balance, self.gross, self.commissions = D("10000"), D(0), D(0)
        self.quote_base, self.quote_ts = None, None
        self.bar_index = -1
        self.final_ts = (int(rows[-1]["open_time"]) + 300000) * 1000000 + 2
        self.max_engine_positions = 0
        self.account_checks = 0

    def on_start(self):
        self.subscribe_bars(BT)
        self.subscribe_quotes(IID)

    def check_account(self):
        positions = self.cache.positions_open(instrument_id=IID)
        self.max_engine_positions = max(self.max_engine_positions, len(positions))
        assert len(positions) <= 1
        assert len(positions) == bool(self.position)
        if positions:
            assert dec(positions[0].quantity) == QTY
            assert positions[0].is_long == (self.position == 1)
        actual = dec(self.cache.account_for_venue(VENUE).balance_total(USDT))
        assert actual == self.balance, ("engine balance", actual, self.balance)
        self.account_checks += 1

    def mark_equity(self, ts, close, final=False):
        unrealized = (close - self.entry["price"]) * self.position * QTY if self.position else D(0)
        point = {"bar_index": self.bar_index, "ts_ns": ts, "mark": text_decimal(close),
                 "balance": text_decimal(self.balance), "unrealized_pnl": text_decimal(unrealized),
                 "equity": text_decimal(self.balance + unrealized), "position_btc": text_decimal(self.position * QTY)}
        if final:
            point["ts_ns"] = self.equity[-1]["ts_ns"]
            point["after_final_liquidation"] = True
            self.equity[-1] = point
        else:
            self.equity.append(point)

    def on_bar(self, bar):
        self.bar_index += 1
        self.check_account()
        i = self.bar_index
        assert bar.ts_event == (int(self.rows[i]["open_time"]) + 300000) * 1000000
        close = dec(bar.close)
        self.fast.update(float(close))
        self.slow.update(float(close))
        f, s = self.fast.value, self.slow.value
        self.indicators.append({"bar_index": i, "available_ns": bar.ts_event,
                                "ema20_hex": None if f is None else f.hex(),
                                "ema50_hex": None if s is None else s.hex()})
        if i >= 49:
            sign = 1 if f > s else -1 if f < s else 0
            if self.previous is not None and sign and sign != self.previous:
                signal = {"index": len(self.signals) + 1, "bar_index": i,
                          "available_ns": bar.ts_event, "target": "LONG" if sign == 1 else "SHORT",
                          "close": text_decimal(close), "ema20_hex": f.hex(), "ema50_hex": s.hex()}
                self.signals.append(signal)
                assert self.pending is None
                self.pending = (sign, signal)
            self.previous = sign
        self.mark_equity(bar.ts_event, close)

    def send_order(self, sign, role, signal):
        if role == "OPEN":
            assert self.position == 0, "Close must fill before reversal opens"
            assert len(self.cache.positions_open(instrument_id=IID)) == 0
        else:
            assert self.position == -sign
        order = self.order_factory.market(IID, OrderSide.BUY if sign == 1 else OrderSide.SELL,
                                          Quantity.from_str("0.010"), reduce_only=role != "OPEN")
        economic = {"index": len(self.orders) + 1, "signal_index": signal["index"] if signal else None,
                    "signal_available_ns": signal["available_ns"] if signal else None,
                    "ts_ns": self.quote_ts, "side": "BUY" if sign == 1 else "SELL", "role": role,
                    "quantity_btc": "0.01", "reference_price": text_decimal(self.quote_base),
                    "reference": "LAST_COMPLETED_CLOSE" if role == "FINAL_CLOSE" else "NEXT_BAR_OPEN",
                    "expected_fill_price": text_decimal(modeled_price(self.quote_base, sign))}
        if signal:
            assert self.quote_ts > signal["available_ns"]
        self.orders.append(economic)
        self.contexts[str(order.client_order_id)] = (sign, economic, signal)
        self.submit_order(order)

    def on_quote(self, quote):
        self.quote_base, self.quote_ts = dec(quote.bid_price), quote.ts_event
        assert quote.bid_price == quote.ask_price
        if quote.ts_event == self.final_ts:
            assert self.pending is None
            if self.position:
                self.send_order(-self.position, "FINAL_CLOSE", None)
        elif self.pending:
            sign, signal = self.pending
            self.pending = None
            assert quote.ts_event == signal["available_ns"] + 1
            if self.position:
                assert self.position == -sign
                self.reverse = (sign, signal)
                self.send_order(sign, "CLOSE", signal)
            else:
                self.send_order(sign, "OPEN", signal)

    def on_order_filled(self, event):
        sign, order, signal = self.contexts[str(event.client_order_id)]
        price, qty, fee = dec(event.last_px), dec(event.last_qty), dec(event.commission)
        assert qty == QTY
        assert price == D(order["expected_fill_price"])
        assert fee == price * QTY * FEE
        assert str(event.liquidity_side).split(".")[-1] == "TAKER"
        assert event.ts_event == order["ts_ns"]
        before = self.position
        self.commissions += fee
        self.balance -= fee
        if order["role"] == "OPEN":
            assert not self.position
            self.position = sign
            self.entry = {"price": price, "fee": fee, "fill_index": len(self.fills) + 1,
                          "ts_ns": event.ts_event, "signal_index": signal["index"]}
        else:
            assert self.position == -sign
            gross = (price - self.entry["price"]) * self.position * QTY
            self.balance += gross
            self.gross += gross
            self.trades.append({"index": len(self.trades) + 1, "side": "LONG" if self.position == 1 else "SHORT",
                                "entry_ns": self.entry["ts_ns"], "exit_ns": event.ts_event,
                                "entry_fill_index": self.entry["fill_index"], "exit_fill_index": len(self.fills) + 1,
                                "quantity_btc": "0.01", "entry_price": text_decimal(self.entry["price"]),
                                "exit_price": text_decimal(price), "gross_pnl": text_decimal(gross),
                                "commissions": text_decimal(self.entry["fee"] + fee),
                                "net_pnl": text_decimal(gross - self.entry["fee"] - fee),
                                "forced_final_exit": order["role"] == "FINAL_CLOSE"})
            self.position, self.entry = 0, None
        self.fills.append({**order, "fill_price": text_decimal(price), "commission": text_decimal(fee),
                           "liquidity": "TAKER", "position_before_btc": text_decimal(before * QTY),
                           "position_after_btc": text_decimal(self.position * QTY), "balance_after": text_decimal(self.balance)})
        if order["role"] == "CLOSE" and self.reverse:
            sign, next_signal = self.reverse
            self.reverse = None
            self.send_order(sign, "OPEN", next_signal)
        elif order["role"] == "FINAL_CLOSE":
            self.mark_equity(event.ts_event, self.quote_base, final=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    raw_csv = DATA.read_bytes()
    rows = list(csv.DictReader(raw_csv.decode().splitlines()))
    assert len(rows) == 8928
    assert [int(r["open_time"]) for r in rows] == list(range(1735689600000, 1738368000000, 300000))
    assert all(int(r["close_time"]) == int(r["open_time"]) + 299999 for r in rows)
    assert all(D(r["low"]) <= min(D(r["open"]), D(r["close"])) <= max(D(r["open"]), D(r["close"])) <= D(r["high"]) and D(r["volume"]) >= 0 for r in rows)
    instrument = CryptoPerpetual(IID, Symbol("BTCUSDT"), BTC, USDT, USDT, False,
                                1, 3, Price.from_str("0.1"), Quantity.from_str("0.001"), 0, 0,
                                margin_init=D("0.1"), margin_maint=D("0.05"))
    engine = BacktestEngine(BacktestEngineConfig(trader_id=TraderId.from_str("BACKTESTER-001"), bypass_logging=True, run_analysis=False))
    engine.add_venue(VENUE, OmsType.NETTING, AccountType.MARGIN, [Money(D("10000"), USDT)],
                     base_currency=USDT, fill_model=AdverseBasisPointFill(),
                     fee_model=MakerTakerFeeModel(maker_rate=FEE, taker_rate=FEE),
                     bar_execution=False, trade_execution=False)
    engine.add_instrument(instrument)
    data = []
    for row in rows:
        # These are execution references synthesized from historical opens, not real bid/ask data.
        ts_open = int(row["open_time"]) * 1000000 + 1
        px = Price.from_str(format(D(row["open"]), ".1f"))
        data.append(QuoteTick(IID, px, px, Quantity.from_str("100.000"), Quantity.from_str("100.000"), ts_open, ts_open))
        ts_close = (int(row["open_time"]) + 300000) * 1000000
        data.append(Bar(BT, *[Price.from_str(format(D(row[k]), ".1f")) for k in ["open", "high", "low", "close"]],
                        Quantity.from_str(format(D(row["volume"]), ".3f")), ts_close, ts_close))
    ts_final = (int(rows[-1]["open_time"]) + 300000) * 1000000 + 2
    px_final = Price.from_str(format(D(rows[-1]["close"]), ".1f"))
    data.append(QuoteTick(IID, px_final, px_final, Quantity.from_str("100.000"), Quantity.from_str("100.000"), ts_final, ts_final))
    engine.add_data(data, sort=True)
    strategy = ExperimentStrategy(rows)
    engine.add_strategy(strategy)
    engine.run()
    strategy.check_account()
    assert strategy.bar_index + 1 == 8928
    assert not strategy.position and strategy.pending is None and strategy.reverse is None
    assert len(strategy.orders) == len(strategy.fills) == len(engine.cache.orders())
    assert all(str(o.status).split(".")[-1] == "FILLED" for o in engine.cache.orders())
    # NETTING reuses one position ID; prior closed cycles live in the archive.
    closed_positions = engine.cache.position_snapshots() + engine.cache.positions_closed()
    assert len(closed_positions) == len(strategy.trades)
    assert not engine.cache.positions_open()
    peak, max_dd, max_pct = D("10000"), D(0), D(0)
    for point in strategy.equity:
        equity = D(point["equity"])
        peak = max(peak, equity)
        dd = peak - equity
        max_dd, max_pct = max(max_dd, dd), max(max_pct, dd / peak * 100)
    pnls = [D(t["net_pnl"]) for t in strategy.trades]
    wins = sum(p > 0 for p in pnls)
    profit, loss = sum(p for p in pnls if p > 0), -sum(p for p in pnls if p < 0)
    metrics = {"closed_trades": len(pnls), "long_trades": sum(t["side"] == "LONG" for t in strategy.trades),
               "short_trades": sum(t["side"] == "SHORT" for t in strategy.trades),
               "orders": len(strategy.orders), "fills": len(strategy.fills), "wins": wins,
               "final_balance": text_decimal(strategy.balance), "gross_pnl_after_slippage": text_decimal(strategy.gross),
               "commissions": text_decimal(strategy.commissions), "net_realized_pnl": text_decimal(sum(pnls)),
               "win_rate_pct": text_decimal(D(wins) / len(pnls) * 100),
               "max_drawdown_usdt": text_decimal(max_dd), "max_drawdown_pct": text_decimal(max_pct),
               "profit_factor": text_decimal(profit / loss), "gross_net_winning_pnl": text_decimal(profit),
               "gross_net_losing_pnl": text_decimal(loss), "final_exposure_btc": "0"}
    assert sum(pnls) == strategy.gross - strategy.commissions == strategy.balance - D("10000")
    positions = sorted(closed_positions, key=lambda p: p.ts_opened)
    for position, trade in zip(positions, strategy.trades, strict=True):
        assert position.ts_opened == trade["entry_ns"] and position.ts_closed == trade["exit_ns"]
        assert dec(position.realized_pnl) == D(trade["net_pnl"])
    economics = {"schema": "btc-ema-replay-economic-v1", "data": {"csv_sha256": hashlib.sha256(raw_csv).hexdigest(),
                 "source": "https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/5m/BTCUSDT-5m-2025-01.zip",
                 "bars": len(rows), "first_open_ms": int(rows[0]["open_time"]), "last_close_ms": int(rows[-1]["close_time"])},
                 "rules": {"ema": [20, 50], "seed": "SMA of first N completed closes", "warmup_bars": 50,
                 "entry": "strict crossover, first possible after both EMAs initialized; fill next open",
                 "quantity_btc": "0.01", "initial_balance_usdt": "10000", "taker_fee": "0.0005",
                 "slippage": "0.0001 adverse; buy ceil/sell floor to 0.1 USDT", "tick_usdt": "0.1", "funding": "0",
                 "position": "one; wait for close fill before reverse opening", "final_close": "last completed close plus same slippage/fee",
                 "event_order": "completed bar at boundary, next open at boundary+1ns; final liquidation boundary+2ns",
                 "equity": "mark each completed close; replace final sample with post-liquidation equity; initial high-water mark 10000",
                 "profit_factor": "sum positive net closed-trade PnL / abs(sum negative net closed-trade PnL)"},
                 "indicators": strategy.indicators, "signals": strategy.signals, "orders": strategy.orders,
                 "fills": strategy.fills, "trades": strategy.trades, "equity": strategy.equity, "metrics": metrics}
    raw_orders = sorted(engine.cache.orders(), key=lambda o: (o.ts_init, str(o.client_order_id)))
    account = engine.cache.account_for_venue(VENUE)
    raw_engine = {"orders": [o.to_dict() for o in raw_orders],
                  "order_events": [[e.to_dict() for e in events(o)] for o in raw_orders],
                  "positions": [p.to_dict() for p in positions],
                  "account_events": [e.to_dict() for e in events(account)]}
    payload = {"economics": economics, "engine": raw_engine,
               "runtime": {"python": platform.python_version(), "nautilus_trader": importlib.metadata.version("nautilus-trader")},
               "validation": {"engine_account_checks": strategy.account_checks, "max_open_engine_positions": strategy.max_engine_positions,
                              "all_orders_filled": True, "engine_trade_pnl_matches_decimal_ledger": True,
                              "engine_balances_match_decimal_ledger": True}}
    (args.output / "raw.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps({"runtime": payload["runtime"], "metrics": metrics, "validation": payload["validation"]}, indent=2))
    engine.dispose()


if __name__ == "__main__":
    main()

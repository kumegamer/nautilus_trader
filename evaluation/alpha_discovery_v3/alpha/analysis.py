"""Marked economics, purged trade diagnostics and dependence-aware resampling."""

import itertools

import numpy as np
import pandas as pd

from .common import config
from .metrics import portfolio_daily, risk_metrics, selected_trades, trade_metrics


def summary(runs, begin, end):
    trades = selected_trades(runs, begin, end)
    daily = portfolio_daily(runs, begin, end)
    capital = config()["capital_per_symbol"] * len(runs)
    tm = trade_metrics(trades)
    marked = float(daily[-1][1] - daily[0][1]) if daily else 0.0
    obs = [o for r in runs for o in r.get("exposure_daily", []) if begin < o[0] <= end]
    fills = [f for r in runs for f in r["fills"] if begin <= f["ts_ns"] < end]
    funding = [
        f for r in runs for f in r["funding_events"] if begin <= f["timestamp"] < end
    ]
    monthly = {}
    for (ta, ea), (tb, eb) in itertools.pairwise(daily):
        month = pd.Timestamp(tb - 1, unit="ns", tz="UTC").strftime("%Y-%m")
        monthly[month] = monthly.get(month, 0.0) + eb - ea
    positive = [v for v in monthly.values() if v > 0]
    exposure = (
        sum(o[1] for o in obs) / (len(obs) * config()["capital_per_symbol"])
        if obs
        else 0.0
    )
    return {
        **tm,
        **risk_metrics(daily, capital),
        "net_pnl": marked,
        "purged_trade_net": tm["net_pnl"],
        "return_on_allocated_capital": marked / capital,
        "months_marked": monthly,
        "largest_marked_month_share": max(positive) / sum(positive)
        if positive
        else None,
        "period_fees": sum(float(f["fee"]) for f in fills),
        "period_slippage": sum(float(f["slippage"]) for f in fills),
        "period_funding": sum(float(f["amount"]) for f in funding),
        "period_turnover": sum(float(f["price"]) * float(f["quantity"]) for f in fills)
        / capital,
        "average_exposure": exposure,
        "time_in_market": sum(o[2] for o in obs) / len(obs) if obs else 0.0,
        "expectancy_R": float(
            np.mean([t["net_pnl"] / t["initial_risk"] for t in trades])
        )
        if trades
        else None,
    }


def bootstrap(runs, begin, end):
    daily = portfolio_daily(runs, begin, end)
    pnl = np.diff([v for _, v in daily])
    n = len(pnl)
    if not n or not np.any(pnl):
        return {
            "probability_positive": 0.0,
            "p05": 0.0,
            "p95": 0.0,
            "centered_p": 1.0,
            "blocks": 7,
        }
    rng = np.random.default_rng(config()["validation"]["seed"])
    count = config()["validation"]["bootstrap_repetitions"]
    starts = rng.integers(n, size=(count, (n + 6) // 7))
    indices = ((starts[..., None] + np.arange(7)) % n).reshape(count, -1)[:, :n]
    totals = pnl[indices].sum(axis=1)
    centered = totals - pnl.sum()
    return {
        "probability_positive": float((totals > 0).mean()),
        "p05": float(np.quantile(totals, 0.05)),
        "p95": float(np.quantile(totals, 0.95)),
        "centered_p": float((1 + (centered >= pnl.sum()).sum()) / (count + 1)),
        "blocks": 7,
        "repetitions": count,
        "method": "synchronized circular calendar-day marked-PnL blocks; centered empirical one-sided null",
    }


def concentration(m):
    return (
        m["top1_share"] is not None
        and m["top1_share"] <= 0.25
        and m["largest_marked_month_share"] is not None
        and m["largest_marked_month_share"] <= 0.60
        and m["net_ex_top1"] > 0
    )

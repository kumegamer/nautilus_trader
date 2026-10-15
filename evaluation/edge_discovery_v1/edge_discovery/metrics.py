"""Daily marked-equity statistics and net trade/cost decompositions."""

import math

import numpy as np
import pandas as pd

from .common import config, ns


def finite(value):
    return float(value) if value is not None and math.isfinite(value) else None


def trade_metrics(trades):
    pnls = [t["net_pnl"] for t in trades]
    wins, losses = [p for p in pnls if p > 0], [p for p in pnls if p < 0]
    best = max(pnls, default=0)
    monthly = {}
    for t in trades:
        month = pd.Timestamp(t["exit_ns"], tz="UTC").strftime("%Y-%m")
        monthly[month] = monthly.get(month, 0) + t["net_pnl"]
    positive_months = sum(v for v in monthly.values() if v > 0)
    best_month = max(monthly.values(), default=0)
    return {
        "total_trades": len(trades),
        "long_trades": sum(t["side"] == 1 for t in trades),
        "short_trades": sum(t["side"] == -1 for t in trades),
        "gross_pnl": sum(t["gross_pnl"] for t in trades),
        "fees": sum(t["fees"] for t in trades),
        "funding": sum(t["funding"] for t in trades),
        "slippage_impact": sum(t["slippage"] for t in trades),
        "net_pnl": sum(pnls),
        "profit_factor": finite(sum(wins) / -sum(losses)) if losses else None,
        "win_rate": len(wins) / len(pnls) if pnls else None,
        "average_win": finite(np.mean(wins)) if wins else None,
        "average_loss": finite(np.mean(losses)) if losses else None,
        "expectancy_per_trade": finite(np.mean(pnls)) if pnls else None,
        "expectancy_r": sum(pnls) / len(pnls) / 25 if pnls else None,
        "net_excluding_best_trade": sum(pnls) - best,
        "best_trade_positive_profit_share": best / sum(wins) if wins else None,
        "best_trade_net_profit_share": best / sum(pnls) if sum(pnls) > 0 else None,
        "net_excluding_best_month": sum(pnls) - best_month,
        "best_month_positive_profit_share": best_month / positive_months
        if positive_months
        else None,
        "monthly_net_pnl": monthly,
    }


def metrics(runs):
    cfg = config()
    trades = [t for r in runs for t in r["trades"]]
    result = trade_metrics(trades)
    symbols = sorted({r["symbol"] for r in runs})
    capital = cfg["capital_per_symbol"] * len(symbols)
    if not capital:
        raise ValueError("No runs to summarize")
    periods = sorted({r["period"] for r in runs}, key=lambda p: ns(cfg["periods"][p][0]))
    normalized = []
    wealth = float(capital)
    for period in periods:
        period_runs = [r for r in runs if r["period"] == period]
        if {r["symbol"] for r in period_runs} != set(symbols):
            raise ValueError("Inconsistent symbol sleeves across periods")
        changes = []
        for r in period_runs:
            series = pd.Series({int(t): float(e) for t, e in r["daily"]}).sort_index()
            changes.append(series.diff().fillna(0))
        pnl = pd.concat(changes).groupby(level=0).sum().sort_index()
        period_equity = capital + pnl.cumsum()
        expected = sum(t["net_pnl"] for r in period_runs for t in r["trades"])
        if abs(period_equity.iloc[-1] - capital - expected) > 0.001:
            raise ValueError("Daily equity and native trade PnL mismatch within period")
        if (period_equity <= 0).any():
            raise ValueError("Bankrupt period cannot supply valid return statistics")
        normalized.append(period_equity * (wealth / capital))
        wealth *= period_equity.iloc[-1] / capital
    equity = pd.concat(normalized)
    equity = equity[~equity.index.duplicated(keep="first")].sort_index()
    returns = equity.pct_change().fillna(0).iloc[1:]
    deviation = returns.std(ddof=1)
    downside = float(np.sqrt(np.mean(np.minimum(returns.to_numpy(), 0) ** 2)))
    drawdown = equity / equity.cummax() - 1
    max_drawdown = float(-drawdown.min())
    duration = sum(ns(cfg["periods"][p][1]) - ns(cfg["periods"][p][0]) for p in periods)
    years = duration / (365 * 86400 * 10**9)
    total_return = wealth / capital - 1
    cagr = (1 + total_return) ** (1 / years) - 1 if years and total_return > -1 else None
    result.update(
        {
            "return": total_return,
            "cagr": cagr,
            "maximum_drawdown": max_drawdown,
            "sharpe": finite(returns.mean() / deviation * math.sqrt(365))
            if deviation > 0
            else None,
            "sortino": finite(returns.mean() / downside * math.sqrt(365)) if downside > 0 else None,
            "calmar": finite(cagr / max_drawdown) if max_drawdown and cagr is not None else None,
            "exposure": sum(t["duration_ns"] for t in trades) / (duration * len(symbols)),
            "turnover": sum(
                float(f["quantity"]) * float(f["price"]) for r in runs for f in r["fills"]
            )
            / capital,
            "initial_capital": capital,
            "period_capital_resets": len(periods),
            "return_method": "chain-linked normalized period equity; PnL is nominal sum",
            "symbols": symbols,
            "periods": periods,
            "daily_equity": [[int(t), float(e)] for t, e in equity.items()],
            "by_symbol": {
                s: trade_metrics([t for r in runs if r["symbol"] == s for t in r["trades"]])
                for s in symbols
            },
            "by_side": {
                side: trade_metrics([t for t in trades if t["side"] == value])
                for side, value in (("long", 1), ("short", -1))
            },
            "by_regime": {
                regime: trade_metrics([t for t in trades if t["regime"] == regime])
                for regime in ("trend", "range", "transition")
            },
            "reconciled": all(abs(float(r["reconciliation_difference"])) < 0.00001 for r in runs),
        }
    )
    return result

"""Marked-equity risk metrics and explicit realized-outcome diagnostics."""

import numpy as np
import pandas as pd

from .common import DAY, config


def risk_metrics(daily, capital):
    values = np.asarray([e for _, e in daily], dtype=float)
    if not len(values):
        values = np.array([capital])
    returns = np.diff(values) / values[:-1]
    sd = np.std(returns, ddof=1) if len(returns) > 1 else 0.0
    downside = np.sqrt(np.mean(np.minimum(returns, 0) ** 2)) if len(returns) else 0.0
    drawdown = float(np.max(1 - values / np.maximum.accumulate(values)))
    days = (daily[-1][0] - daily[0][0]) / DAY if len(daily) > 1 else 0
    ret = float(values[-1] / values[0] - 1)
    annual = (1 + ret) ** (365 / days) - 1 if days > 0 and ret > -1 else None
    return {
        "return": ret,
        "annual_volatility": float(sd * np.sqrt(365)),
        "sharpe": float(np.mean(returns) / sd * np.sqrt(365)) if sd else None,
        "sortino": float(np.mean(returns) / downside * np.sqrt(365))
        if downside
        else None,
        "maximum_drawdown": drawdown,
        "return_drawdown": ret / drawdown if drawdown else None,
        "calmar": annual / drawdown if drawdown and annual is not None else None,
    }


def trade_metrics(trades):
    pnls = np.array([float(t["net_pnl"]) for t in trades])
    winners = np.sort(pnls[pnls > 0])[::-1]
    gross_positive = winners.sum()
    gross_negative = -pnls[pnls < 0].sum()
    months, symbols = {}, {}
    for t in trades:
        month = pd.Timestamp(t["exit_ns"], unit="ns", tz="UTC").strftime("%Y-%m")
        months[month] = months.get(month, 0) + float(t["net_pnl"])
        s = t.get("symbol", "UNKNOWN")
        symbols[s] = symbols.get(s, 0) + float(t["net_pnl"])

    def positive_share(values):
        pos = [v for v in values if v > 0]
        return max(pos) / sum(pos) if pos else None

    result = {
        "trades": len(trades),
        "net_pnl": float(pnls.sum()),
        "expectancy": float(pnls.mean()) if len(pnls) else None,
        "profit_factor": float(gross_positive / gross_negative)
        if gross_negative
        else None,
        "fees": sum(float(t["fees"]) for t in trades),
        "funding": sum(float(t["funding"]) for t in trades),
        "slippage": sum(float(t["slippage"]) for t in trades),
        "turnover_notional": sum(float(t.get("turnover", 0)) for t in trades),
        "largest_month_share": positive_share(months.values()),
        "largest_symbol_share": positive_share(symbols.values()),
        "mae": float(np.mean([float(t.get("mae", 0)) for t in trades]))
        if trades
        else None,
        "mfe": float(np.mean([float(t.get("mfe", 0)) for t in trades]))
        if trades
        else None,
        "win_rate": float((pnls > 0).mean()) if len(pnls) else None,
        "outcome_quantiles": np.quantile(
            pnls, [0, 0.05, 0.25, 0.5, 0.75, 0.95, 1]
        ).tolist()
        if len(pnls)
        else [],
        "skew": float(pd.Series(pnls).skew())
        if len(pnls) >= 3 and np.std(pnls)
        else None,
        "months": months,
        "symbols": symbols,
    }
    for n in (1, 5, 10):
        result[f"top{n}_share"] = (
            float(winners[:n].sum() / gross_positive) if gross_positive else None
        )
        result[f"net_ex_top{n}"] = float(pnls.sum() - winners[:n].sum())
    return result


def block_bootstrap(trades, begin, end):
    cfg = config()["validation"]
    count = max(1, int((end - begin) // DAY))
    daily = np.zeros(count)
    for t in trades:
        index = min(count - 1, int((t["exit_ns"] - begin) // DAY))
        if index >= 0:
            daily[index] += float(t["net_pnl"])
    rng = np.random.default_rng(cfg["seed"])
    starts = rng.integers(count, size=(cfg["bootstrap_repetitions"], (count + 6) // 7))
    indices = (starts[..., None] + np.arange(7)) % count
    samples = daily[indices.reshape(len(starts), -1)[:, :count]].sum(axis=1)
    return {
        "probability_positive": float((samples > 0).mean()),
        "p05": float(np.quantile(samples, 0.05)),
        "p95": float(np.quantile(samples, 0.95)),
        "method": "circular 7-calendar-day blocks; realized exit-day attribution",
    }


def selected_trades(runs, begin, end, purge_blocks=False):
    out = []
    for run in runs:
        for t in run["trades"]:
            if begin <= t["entry_ns"] and t["exit_ns"] < end:
                if purge_blocks:
                    a = int(3 * (t["entry_ns"] - begin) / (end - begin))
                    b = int(3 * (t["exit_ns"] - begin) / (end - begin))
                    if a != b:
                        continue
                out.append(t)
    return sorted(out, key=lambda t: (t["exit_ns"], t["symbol"]))


def portfolio_daily(runs, begin=None, end=None):
    series = [pd.Series({int(t): float(e) for t, e in r["daily"]}) for r in runs]
    total = pd.concat(series, axis=1).sort_index().ffill().sum(axis=1)
    if begin is not None:
        total = total[total.index >= begin]
    if end is not None:
        total = total[total.index <= end]
    return [[int(t), float(e)] for t, e in total.items()]


def summarize(runs, begin, end):
    trades = selected_trades(runs, begin, end)
    capital = config()["capital_per_symbol"] * len(runs)
    daily = portfolio_daily(runs, begin, end)
    result = {**trade_metrics(trades), **risk_metrics(daily, capital)}
    obs = [o for r in runs for o in r.get("exposure_daily", []) if begin < o[0] <= end]
    exposure = (
        sum(o[1] for o in obs) / (len(obs) * config()["capital_per_symbol"])
        if obs
        else 0
    )
    result.update(
        {
            "average_exposure": exposure,
            "average_entry_notional_exposure": sum(o[3] for o in obs)
            / (len(obs) * config()["capital_per_symbol"])
            if obs
            else 0,
            "time_in_market": sum(o[2] for o in obs) / len(obs) if obs else 0,
            "return_per_unit_exposure": result["return"] / exposure
            if exposure
            else None,
            "return_on_allocated_capital": result["return"],
            "turnover": result["turnover_notional"] / capital,
            "profile_switches": sum(
                begin <= x["timestamp"] < end
                for r in runs
                for x in r.get("switches", [])
            ),
            "time_no_trade": sum(o[4] for o in obs) / len(obs) if obs else 1,
        }
    )
    return result

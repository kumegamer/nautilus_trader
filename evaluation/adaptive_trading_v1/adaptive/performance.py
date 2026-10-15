"""Rolling multi-axis diagnostics; trade statistics are not annualized returns."""

import math

import numpy as np
import pandas as pd

from .common import DAY, HOUR, config

STATES = (
    "NORMAL_VARIANCE",
    "EDGE_DEGRADING",
    "REGIME_MISMATCH",
    "EXECUTION_DEGRADATION",
    "POSSIBLE_EDGE_FAILURE",
    "INSUFFICIENT_DATA",
)


def trade_metrics(trades, capital=10000):
    pnls = np.array([float(t["net_pnl"]) for t in trades])
    wins, losses = pnls[pnls > 0], pnls[pnls < 0]
    equity = np.r_[capital, capital + pnls.cumsum()]
    dd = 1 - equity / np.maximum.accumulate(equity)
    consecutive = 0
    for p in reversed(pnls):
        if p >= 0:
            break
        consecutive += 1
    monthly = {}
    for t in trades:
        m = pd.Timestamp(t["exit_ns"], tz="UTC").strftime("%Y-%m")
        monthly[m] = monthly.get(m, 0) + float(t["net_pnl"])
    return {
        "number_of_trades": len(trades),
        "gross_pnl": sum(float(t["gross_pnl"]) for t in trades),
        "net_pnl": float(pnls.sum()),
        "expectancy": float(pnls.mean()) if len(pnls) else None,
        "expectancy_r": float(
            np.mean(
                [float(t["net_pnl"]) / float(t.get("initial_risk", 25)) for t in trades]
            )
        )
        if trades
        else None,
        "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) else None,
        "maximum_drawdown": float(dd.max()),
        "average_win": float(wins.mean()) if len(wins) else None,
        "average_loss": float(losses.mean()) if len(losses) else None,
        "win_rate": float(len(wins) / len(pnls)) if len(pnls) else None,
        "mae": float(np.mean([float(t["mae"]) for t in trades if "mae" in t]))
        if any("mae" in t for t in trades)
        else None,
        "mfe": float(np.mean([float(t["mfe"]) for t in trades if "mfe" in t]))
        if any("mfe" in t for t in trades)
        else None,
        "turnover": sum(
            float(
                t.get(
                    "turnover",
                    float(t.get("quantity", 0))
                    * (float(t.get("entry_price", 0)) + float(t.get("exit_price", 0))),
                )
            )
            for t in trades
        )
        / capital,
        "fees": sum(float(t["fees"]) for t in trades),
        "slippage": sum(float(t["slippage"]) for t in trades),
        "funding": sum(float(t["funding"]) for t in trades),
        "consecutive_losses": consecutive,
        "monthly_net_pnl": monthly,
        "top10_positive_profit_share": float(np.sort(wins)[-10:].sum() / wins.sum())
        if len(wins)
        else None,
        "net_excluding_top10": float(pnls.sum() - np.sort(wins)[-10:].sum()),
    }


def daily_statistics(points, capital):
    series = pd.Series({int(t): float(e) for t, e in points}).sort_index()
    ret = series.pct_change().dropna()
    std = ret.std(ddof=1)
    downside = np.sqrt(np.mean(np.minimum(ret.to_numpy(), 0) ** 2)) if len(ret) else 0
    return {
        "sharpe": float(ret.mean() / std * math.sqrt(365)) if std > 0 else None,
        "sortino": float(ret.mean() / downside * math.sqrt(365))
        if downside > 0
        else None,
        "maximum_drawdown": float((1 - series / series.cummax()).max())
        if len(series)
        else 0,
        "return": float(series.iloc[-1] / capital - 1) if len(series) else 0,
    }


class PerformanceMonitor:
    def __init__(self):
        self.trades = []
        self.daily = {}

    def add(self, trade):
        if self.trades and trade["exit_ns"] < self.trades[-1]["exit_ns"]:
            raise ValueError("Nonchronological closed trade")
        self.trades.append(trade.copy())

    def select(self, timestamp, days=90, **axes):
        return [
            t
            for t in self.trades
            if timestamp - days * DAY <= t["exit_ns"] <= timestamp
            and all(t.get(k) == value for k, value in axes.items())
        ]

    def snapshot(self, timestamp, **axes):
        selected = self.select(timestamp, **axes)
        result = trade_metrics(selected)
        result.update(
            daily_statistics(
                [
                    (t, e)
                    for t, e in self.daily.items()
                    if timestamp - 90 * DAY <= t <= timestamp
                ],
                10000,
            )
        )
        result["return_metric_scope"] = (
            "symbol sleeve daily marked equity; filtered trade axes above"
        )
        return result


class DriftDetector:
    def __init__(self):
        self.last_evaluation = None
        self.policy = config()["policy"]
        self.last_count = 0
        self.trade_checkpoint = 0
        self.last_periodic_evaluation = None
        self.last_regime = None
        self.active_triggers = set()

    def evaluate(self, timestamp, regime, profile, monitor, expected=None):
        policy = self.policy
        periodic_due = (
            self.last_periodic_evaluation is None
            or timestamp - self.last_periodic_evaluation
            >= policy["evaluation_hours"] * HOUR
        )
        if (
            not periodic_due
            and len(monitor.trades) == self.last_count
            and regime["regime"] == self.last_regime
        ):
            return None
        trades = monitor.select(timestamp, profile=profile.id)
        m = trade_metrics(trades)
        triggers = []
        if periodic_due:
            triggers.append("elapsed_time")
        if len(monitor.trades) - self.trade_checkpoint >= 50:
            triggers.append("50_new_closed_trades")
        changed = self.last_regime is not None and regime["regime"] != self.last_regime
        if changed and regime["confidence"] >= 0.55:
            triggers.append("regime_transition")
        marked = daily_statistics(sorted(monitor.daily.items()), 10000)
        if max(m["maximum_drawdown"], marked["maximum_drawdown"]) > 0.08:
            triggers.append("drawdown_breach")
        if m["consecutive_losses"] >= 8:
            triggers.append("abnormal_loss_sequence")
        n = len(trades)
        sufficient = n >= policy["minimum_decay_trades"]
        if sufficient and m["expectancy_r"] < -0.1:
            triggers.append("expectancy_deterioration")
        if sufficient and m["profit_factor"] is not None and m["profit_factor"] < 0.85:
            triggers.append("profit_factor_deterioration")
        cost_per_turnover = sum(float(t["slippage"] + t["fees"]) for t in trades) / max(
            sum(
                float(
                    t.get(
                        "turnover",
                        float(t.get("quantity", 0))
                        * (
                            float(t.get("entry_price", 0))
                            + float(t.get("exit_price", 0))
                        ),
                    )
                )
                for t in trades
            ),
            1,
        )
        if n >= 10 and cost_per_turnover > 0.0015:
            triggers.append("execution_cost_deterioration")
        if expected and sufficient:
            r = np.array(
                [float(t["net_pnl"]) / float(t["initial_risk"]) for t in trades]
            )
            if (
                r.mean() + 1.96 * r.std(ddof=1) / math.sqrt(n)
                < expected["expectancy_lower"]
            ):
                triggers.append("outside_historical_confidence_band")
        new_triggers = set(triggers) - self.active_triggers
        self.active_triggers = set(triggers)
        if not triggers or (
            not new_triggers
            and "elapsed_time" not in triggers
            and "50_new_closed_trades" not in triggers
        ):
            return None
        if "drawdown_breach" in triggers:
            state = "POSSIBLE_EDGE_FAILURE"
        elif "execution_cost_deterioration" in triggers:
            state = "EXECUTION_DEGRADATION"
        elif (
            profile.id != "NO_TRADE"
            and regime["regime"] not in profile.compatible_regimes
        ):
            state = "REGIME_MISMATCH"
        elif not sufficient:
            state = "INSUFFICIENT_DATA"
        elif "outside_historical_confidence_band" in triggers or (
            "expectancy_deterioration" in triggers
            and "profit_factor_deterioration" in triggers
            and n >= 50
        ):
            state = "POSSIBLE_EDGE_FAILURE"
        elif any(
            t in triggers
            for t in (
                "expectancy_deterioration",
                "profit_factor_deterioration",
                "abnormal_loss_sequence",
            )
        ):
            state = "EDGE_DEGRADING"
        else:
            state = "NORMAL_VARIANCE"
        if "elapsed_time" in triggers:
            self.last_periodic_evaluation = timestamp
        if "50_new_closed_trades" in triggers:
            self.trade_checkpoint = len(monitor.trades)
        self.last_evaluation, self.last_count, self.last_regime = (
            timestamp,
            len(monitor.trades),
            regime["regime"],
        )
        return {
            "timestamp": timestamp,
            "state": state,
            "triggers": triggers,
            "metrics": m,
            "cost_per_turnover": cost_per_turnover,
            "expected": expected,
            "sample_sufficient": sufficient,
            "marked_equity": marked,
        }
